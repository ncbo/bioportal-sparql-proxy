#An standalone API for 4store


import sys
import urllib,urllib2
import traceback
import pdb
import time                                                
import json

PREFIXES = """
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dc:   <http://purl.org/dc/elements/1.1/>
PREFIX dct:  <http://purl.org/dc/terms/>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX bio:  <http://purl.org/vocab/bio/0.1/>
PREFIX meta: <http://bioportal.bioontology.org/metadata/def/> 
PREFIX graphs: <http://purl.bioontology.org/def/graphs/>
PREFIX omv: <http://omv.ontoware.org/2005/05/ontology#>
"""

class SPARQL:
    def __init__(self,epr):
        self.epr = epr
    def pq(self,q):
        print query(PREFIXES+q,self.epr,f='text/plain')
    def count(self):
        return int(self.query("select (count(?s) as ?c) where { GRAPH ?g { ?s ?p ?o }}")[0]["c"])
    def desc(self,x):
        self.pq("DESCRIBE <%s>"%x)
    def query(self,x):
        o=query(PREFIXES+x,self.epr,f='application/json')
        return parse_json_result(o)
    def count_in_graph(self,g):
        return int(self.query("select (count(?s) as ?c) where { GRAPH <%s> { ?s ?p ?o }}"%g)[0]["c"])
    def predicates_in_graph(self,g):
        return [x["p"] for x in self.query("select DISTINCT ?p where { GRAPH <%s> { ?s ?p ?o }}"%g)]
    def subjects_in_graph(self,g):
        return [x["s"] for x in self.query("select DISTINCT ?s where { GRAPH <%s> { ?s ?p ?o }}"%g)]
    def objects_in_graph(self,g):
        return [x["o"] for x in self.query("select DISTINCT ?o where { GRAPH <%s> { ?s ?p ?o }}"%g)]
    def types_in_graph(self,g):
        return [x["o"] for x in self.query("select DISTINCT ?o where { GRAPH <%s> { ?s a ?o }}"%g)]
    def get_stats_for_graph(self,g):
        return dict(count=self.count_in_graph(g),
        preds=len(self.predicates_in_graph(g)),
        subs=len(self.subjects_in_graph(g)),
        objs=len(self.objects_in_graph(g)),
        types=len(self.types_in_graph(g)))

        

ru = SPARQL("http://bmir-dev1:7070/sparql/")
prd = SPARQL("http://bmir-dev1:8080/sparql/")

def timeit(method):

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print '%r (%r, %r) %2.2f sec' % \
              (method.__name__, args, kw, te-ts)
        return result

    return timed

def sol2dict(sol):
    d=dict()
    for v in sol:
        d[v]=sol[v]["value"]
    return d

def parse_json_result(res):
    j=json.loads(res)
    sols = []
    for sol in j["results"]["bindings"]:
        sols.append(sol2dict(sol))
    return sols

def pquery(q,epr="http://localhost:8080/sparql/"):
    print query(q,epr,f='text/plain')

def query(q,epr,f='application/json'):
    try:
        params = {'query': q}
        params = urllib.urlencode(params)
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(epr+'?'+params)
        request.add_header('Accept', f)
        request.get_method = lambda: 'GET'
        url = opener.open(request)
        return url.read()
    except Exception, e:
        traceback.print_exc(file=sys.stdout)
        raise e 

def delete_graph(graph,epr):
    sq = "DELETE DATA WHERE { GRAPH <%s> { ?s ?p ?o } }"%graph
    return update4s(sq,epr)

def assert_file_in_graph(graph_uri,file_path,epr,content_format):
   f = file(file_path,"r")
   triples = f.read()
   f.close()
   try:
       return assert4s(triples,epr,graph_uri,content_format)
   except Exception, e:
       return str(e)

def assert4s(data,epr,graph,contenttype):
    try:
        params = urllib.urlencode({'graph': graph,'data': data,'mime-type' : contenttype })
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(epr,params)
        #request.add_header('Content-Type', contenttype)
        request.get_method = lambda: 'POST'
        url = opener.open(request)
        return url.read()
    except Exception, e:
        traceback.print_exc(file=sys.stdout)
        raise e

def update4s(update,epr):
    try:
        params = urllib.urlencode({'update': update.encode("utf-8")})
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(epr,params)
        request.get_method = lambda: 'POST'
        url = opener.open(request)
        return url.read()
    except Exception, e:
        traceback.print_exc(file=sys.stdout)
        raise e
