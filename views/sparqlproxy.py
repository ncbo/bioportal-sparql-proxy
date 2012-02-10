from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed
from django.shortcuts import render_to_response
from django.template import RequestContext, loader
from django.views.decorators.http import condition
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import requires_csrf_token

from services import Services
import logging, json
from urllib2 import HTTPError
import httplib2
from config import PROXY_FORMAT
from config import USER_ID
from urllib import urlencode

logger = logging.getLogger(__name__)

def get_parameter(request,key):
	parameters = request.GET if request.method == 'GET' else request.POST
	return parameters[key] if key in parameters else None
	
def main(request): 
    c = {}
    c.update(csrf(request))
    return render_to_response("main.html",c)

def is_web_frontend(query):
    try:
        #TODO better CSRF validation
        apikey = query["apikey"] if "apikey" in query else None
        if apikey and len(apikey) > 10:
            return False
        token = query["csrfmiddlewaretoken"] if "csrfmiddlewaretoken" in query else None
        if token and len(token) > 10:
            return True
    except Exception, e:
        pass
    return False 

def proxy(request,query, url):
    conn = httplib2.Http()
    if request.method == "GET":
        url_ending = "%s?%s" % (url, urlencode(query))
        ui = is_web_frontend(query)
        if ui:
            url_ending += "&apikey=" + USER_ID
        url = PROXY_FORMAT % url_ending
        headers=dict()
        if 'HTTP_ACCEPT' in request.META:
           headers={"Accept" : request.META["HTTP_ACCEPT"] } 
        resp, content = conn.request(url, "GET", headers=headers )
        content_type = resp["content-type"] if "content-type" in resp else None
        respd = HttpResponse(mimetype=content_type)
        respd['Access-Control-Allow-Origin'] = "*"
        respd.write(content)
        respd.status_code = resp.status
        return respd
    elif request.method == "POST":
        response = HttpResponse()
        response.status_code = 403
        response.write("403 FORBIDEN - POST Requests not allowed")
        return response

####
# we should try to stream out the response:
# see: 
# http://stackoverflow.com/questions/2922874/how-to-stream-an-httpresponse-with-django
####
@condition(etag_func=None)
def sparql_auth(request): 
    try:
        query = get_parameter(request,"query")
        if not query:
            response = HttpResponse()
            msg = "ERROR 500 - SPARQL Protocol 'query' parameter not provided"
            response.status_code = 500
            response.write(msg)
            logger.info(msg)
            return response  

        user_api_key = None
        user_id = None
        query = request.GET.copy() if request.method == "GET" else request.POST.copy()
        if not is_web_frontend(query):
            user_api_key = get_parameter(request,"apikey")
            if not user_api_key:
                    response = HttpResponse()
                    response.status_code = 403
                    response.write("403 FORBIDEN - Apikey not provided")
                    return response

            services = Services(user_api_key)
            try:
                user_id = services.validate_api_key()
                query["apikey"]=user_id
            except HTTPError, auth_err:
                if auth_err.getcode() == 403:
                    response = HttpResponse()
                    msg = "403 FORBIDEN apikey [%s] not valid. Trace 1."%user_api_key
                    response.status_code = 403
                    response.write(msg)
                    logger.info(msg)
                    return response  
                raise auth_err
            except Exception, auth_err:
                response = HttpResponse()
                msg = "403 FORBIDEN apikey [%s] not valid. Trace 2. %s"%(user_api_key,auth_err)
                response.status_code = 403
                response.write(msg)
                logger.info(msg)
                logger.exception(auth_err)
                return response  

        response = proxy(request,query, "sparql/")
        return response

    except Exception, e:
        logger.exception("Error processing sparql")
        response = HttpResponse(mimetype="application/json")
        response.write("Error calling sparql [%s] %s"%(user_api_key,e))
        response.status_code = 500;
        return response

def examples(request):
    c = {}
    c.update(csrf(request))
    return render_to_response("examples.html",c)

def apikeys(request):
    return render_to_response("apikey.html")
