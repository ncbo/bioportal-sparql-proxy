import pdb
import traceback
import xml.parsers.expat
import csv
from itertools import groupby
import logging
import urllib,urllib2
import json, xml2json
import email_sender
from config import REST_URL, SPARQL_SERVER, API_KEY_AUTH   
    
def http_request(service,params,api_key):
    try:
        params["apikey"]=api_key
        params = urllib.urlencode(params)
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(service+'?'+params)
        request.get_method = lambda: 'GET'
        url = opener.open(request)
        return url.read()
    except Exception, e:
        raise e

def auth_call(rest_url,user_api_key):
   return xml2json.xml2json(http_request(rest_url+"auth",dict(userapikey=user_api_key),API_KEY_AUTH))

def parse_xml_ontologies(xml_content):
    in_bean = [False]
    element = [""]
    beans = [] 
    def start_element(name, attrs):
        if in_bean[0]:
            element[0] = name
        if name == "ontologyBean":
            in_bean[0] = True
            beans.append(dict())
    def end_element(name):
        if name == "ontologyBean":
            in_bean[0] = False
        element[0] = ""
    def char_data(data):
         if in_bean[0] and len(element[0]) > 0:
            try:
                beans[-1][element[0]]=str(data)
            except Exception,e:
                pass
        #print 'Character data:', repr(data)
    p = xml.parsers.expat.ParserCreate()
    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data
    p.Parse(xml_content)
    return beans

def get_api_onts(rest_epr):
    content = http_request(rest_epr+"ontologies",dict(),API_KEY_AUTH)
    onts = parse_xml_ontologies(content)
    onts = sorted(onts,key=lambda x: x["format"])
    return onts

def get_acl_ont(rest_epr,ont_id):
    content=http_request(rest_epr+ "virtual/ontology/"+ont_id,dict(),API_KEY_AUTH)
    ont = json.loads(xml2json.xml2json(content))
    try:
        return ont["success"]["data"]["ontologyBean"]["userAcl"]
    except KeyError, k:
        return None

class BioportalAPIClient:
    def __init__(self,rest_url,cache=None):
        self.cache = cache
        self.rest_url = rest_url
        self.onts = None

    def user_auth(self,user_api_key):
        cache_key = None
        if self.cache:
            cache_key = filter(lambda x: x.isalnum(),user_api_key)
            res = self.cache.get(cache_key)
            if res:
                return json.loads(res)

        res = auth_call(self.rest_url,user_api_key)

        if self.cache:
            self.cache.set(cache_key, res,2 * 60 * 60)
        return json.loads(res)

    def load_all_ontologies_info(self,load_acl=False):
        if self.cache:
            ont_s = self.cache.get("ontologies")
            if ont_s:
                self.onts = json.loads(ont_s)
                return self.onts
        self.onts = get_api_onts(self.rest_url) 
        if load_acl:
            for ont in self.onts:
                ont_graph = "http://bioportal.bioontology.org/ontologies/%s"% ont["ontologyId"]
                ont["userAcl"] = get_acl_ont(self.rest_url,ont["ontologyId"])
                if ont["userAcl"] and ont["userAcl"].has_key("userEntry"):
                    if type(ont["userAcl"]["userEntry"]) <> list:
                        ont["userAcl"]["userEntry"]=[ont["userAcl"]["userEntry"]]
                    for user in ont["userAcl"]["userEntry"]:
                        userId = user["userId"]
                    ont["acl_config"]="%s=%s"%(ont_graph,";".join(x["userId"] for x in ont["userAcl"]["userEntry"]))

        if self.cache:
            self.cache.set("ontologies",json.dumps(self.onts), 60 * 60)
        return self.onts

    def get_private_onts(self):
        return filter(lambda x: x["userAcl"],self.onts)

def get_data_graph(ont):
    return "http://bioportal.bioontology.org/ontologies/" + ont["ontologyId"]
