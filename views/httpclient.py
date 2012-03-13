import urllib
import urllib2
import config

if config.USE_HTTPLIB2:
    import httplib2

def new_http_client():
    if config.USE_HTTPLIB2:
        return HTTP2Client()
    else:
        return HTTPStreamClient()
    
class HTTP2Client(object):
    def __init__(self):
        self.conn = httplib2.Http()
    def get(self, url, headers):
        resp, content = self.conn.request(url, "GET", headers=headers )
        return resp, content

class HTTPStreamClient(object):
    def __init__(self):
        pass
    def get(self, url, values, headers):
        data = urllib.urlencode(values)
        error_msg = None
        error = None
        req = urllib2.Request(url, data, headers=headers)
        response = urllib2.urlopen(req)
        def response_streamer():
            if error_msg:
                yield error_msg
            else:
                while True:
                    l=response.read(config.STREAM_BUFFER_SIZE)
                    if len(l)==0:
                        break
                    yield l
        if error_msg:
            return error.headers,error.code,response_streamer()
        return response.headers,\
               response.getcode(),\
               response_streamer()
