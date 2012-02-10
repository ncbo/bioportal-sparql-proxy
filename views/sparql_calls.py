from sparql import *
import urlparse

from config import REST_URL, SPARQL_SERVER, API_KEY_AUTH

def get_ns(iri):
    p=urlparse.urlparse(iri)
    if p.fragment:
        x = p.path
    x = '/'.join(p.path.split("/")[:-1])
    return p.netloc + x
    
    
class BioportalSPARQLClient(SPARQL):
    def __init__(self,epr,apikey):
        self.apikey = apikey
        SPARQL.__init__(self,epr)

    def get_namespaces_in_graph(self,graph):
        subjects = SPARQL.subjects_in_graph(self,graph)
        namespaces = set()
        for s in subjects:
            namespaces.add(get_ns(s))
        return namespaces

if __name__ == "__main__":
    bio=BioportalSPARQLClient(SPARQL_SERVER)
