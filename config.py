SPARQL_SERVER = "INTERNAL SPARQL CLUSTER EPR"
REST_URL = "http://data.bioontology.org/"

#USER bioportal_sparql
USER_ID = "SOME INTERNAL ID"
API_KEY_AUTH = "SOME API KEY"

PROXY_DOMAIN = "ncboprod-fsmaster1"
KB_ONTOLOGIES = "8080"
KB_MAPPINGS = "8083"
def PROXIED_SERVER(kb=None):
    KB_PORT = KB_ONTOLOGIES
    if kb!=None and kb=="mappings":
        KB_PORT = KB_MAPPINGS
    return "http://%s:%s/sparql/" % (PROXY_DOMAIN, KB_PORT)

#a set of api keys that can bypass timeouts
BY_PASS_KEYS = set([])

USE_HTTPLIB2 = False
STREAM_BUFFER_SIZE = 128 * 1024
