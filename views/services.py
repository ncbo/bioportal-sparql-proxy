from api_calls import BioportalAPIClient, get_data_graph
from config import REST_URL, API_KEY_AUTH
import os,json
import pdb
import logging, json

logger = logging.getLogger(__name__)

CACHE_DJANGO = None
try:
    from django.core.cache import cache
    CACHE_DJANGO = True
except Exception, e:
    logger.exception("Not possible to import django.core.cache")
    CACHE_DJANGO = False

bioportalAPI = None
if CACHE_DJANGO:
    bioportalAPI = BioportalAPIClient(REST_URL,cache=cache)
else:
    bioportalAPI = BioportalAPIClient(REST_URL)

class Services:
    def __init__(self,user_api_key=None):
        self.user_api_key=user_api_key

    def validate_api_key(self):
        resp = bioportalAPI.user_auth(self.user_api_key)
        try:
            user_id = resp["success"]["data"]["session"]["attributes"]["entry"]["securityContext"]["userBean"]["id"]
            return int(user_id)
        except Exception, e:
            raise e
    
    def get_private_ontologies(self,force_reload=False):
        if CACHE_DJANGO and not force_reload:
            val = cache.get("security")
            if val:
                return json.loads(val)

        bioportalAPI.load_all_ontologies_info(load_acl=True)
        prv = bioportalAPI.get_private_onts()

        res = dict()
        to_view = ("id","contactName","userAcl","ontologyId")
        for p in prv:
            obj = dict()
            for x in to_view:
                if x in p:
                    obj[x]=p[x]
            res[p["abbreviation"]] = obj
        if CACHE_DJANGO:
             cache.set("security",json.dumps(res), 60 * 60)
        return res
