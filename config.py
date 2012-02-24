SPARQL_SERVER = "INTERNAL SPARQL CLUSTER EPR"
REST_URL = "http://rest.bioontology.org/bioportal/"

#USER bioportal_sparql
USER_ID = "SOME INTERNAL ID" # we handle ids "59cca101-3334-4aac-b45d-9668125b9893" #user bioportal_sparql
API_KEY_AUTH = "SOME API KEY"

PROXY_DOMAIN = "bmir-dev1.stanford.edu:8080"
PROXIED_SERVER = u"http://%s/sparql/" % PROXY_DOMAIN

USE_HTTPLIB2 = False
STREAM_BUFFER_SIZE = 128 * 1024
