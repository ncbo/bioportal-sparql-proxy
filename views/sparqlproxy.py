import logging
import json
from urllib import urlencode
from urllib2 import HTTPError

from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponseNotAllowed
from django.shortcuts import render_to_response
from django.template import RequestContext, loader
from django.views.decorators.http import condition
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import requires_csrf_token

import httpclient
from services import Services
from config import PROXIED_SERVER, USER_ID, BY_PASS_KEYS

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
        token = query["csrfmiddlewaretoken"]\
                    if "csrfmiddlewaretoken" in query else None
        if token and len(token) > 10:
            return True
    except Exception, e:
        pass
    return False

def proxy(request,query, url):
    http_client = httpclient.new_http_client()
    if request.method == "GET":
        database = query["kboption"] if "kboption" in query else None
        path_info = request.path
        if not database:
            if path_info:
                database = "mappings" if "mappings" in path_info else None
        ui = is_web_frontend(query)
        params = dict([(k,query[k]) for k in query])
        if ui:
            params["apikey"] = USER_ID
        headers=dict()
        if 'HTTP_ACCEPT' in request.META:
           headers["Accept"] = request.META["HTTP_ACCEPT"]
           if ui and ("describe" in query["query"].lower() or\
                "construct" in query["query"].lower()):
                    headers["Accept"]="text/plain"
        outputformat = None
        if "outputformat" in query:
            outputformat = query["outputformat"]
            if  query["outputformat"]=="json":
                headers["Accept"]="application/sparql-results+json"
        header_resp,\
        code_resp,\
        content_resp = http_client.get(PROXIED_SERVER(database), params, headers)
        content_type = header_resp["content-type"]\
                            if "content-type" in header_resp else None
        respd = HttpResponse(content_resp, mimetype=content_type)
        respd['Access-Control-Allow-Origin'] = "*"
        if outputformat:
            respd['Content-Disposition'] = 'inline; filename="bioportal_sparql_results.%s"'%outputformat
        respd.status_code = code_resp
        return respd
    elif request.method == "POST":
        response = HttpResponse()
        response.status_code = 403
        response.write("403 FORBIDEN - POST Requests not allowed")
        return response

def error_api_key():
    response = HttpResponse()
    response.status_code = 403
    response.write("403 FORBIDEN - Apikey not provided")
    return response

def error_not_query_request():
    response = HttpResponse()
    msg = "ERROR 500 - SPARQL Protocol 'query' parameter not provided"
    response.status_code = 500
    response.write(msg)
    logger.info(msg)
    return response

def error_apikey_validation(user_api_key,auth_err=""):
    response = HttpResponse()
    msg = "403 FORBIDEN apikey [%s] not valid. Trace 1. %s"%\
          (user_api_key,auth_err)
    response.status_code = 403
    response.write(msg)
    logger.info(msg)
    logger.exception(auth_err)
    return response

####
# we should try to stream out the response:
# see:
# http://stackoverflow.com/questions/2922874/how-to-stream-an-httpresponse-with-django
####
@condition(etag_func=None)
def sparql_auth(request):
    query = None
    user_api_key = None
    by_pass = False
    try:
        query = get_parameter(request,"query")
        if not query:
           return error_not_query_request()

        user_api_key = None
        user_id = None
        query = request.GET.copy() \
                    if request.method == "GET"\
                    else request.POST.copy()

        if not is_web_frontend(query):
            user_api_key = get_parameter(request,"apikey")
            if not user_api_key:
                return error_api_key()
            by_pass = user_api_key in BY_PASS_KEYS
            if by_pass:
                query["soft-limit"]=-1
            services = Services(user_api_key)
            try:
                bool_auth = services.validate_api_key()
                if bool_auth =="OK":
                    #TODO: private access to graphs disable until
                    # until new backend RDF is rolled out
                    user_id = "9876500"
                    query["apikey"]=user_id
                else:
                    return error_apikey_validation(user_api_key,"")
            except HTTPError, auth_err:
                if auth_err.getcode() == 403:
                    return error_apikey_validation(user_api_key,auth_err)
                raise auth_err
            except Exception, auth_err:
                return error_apikey_validation(user_api_key,auth_err)

        response = proxy(request,query, "sparql/")
        return response
    except HTTPError, e:
        error_msg = "\n".join(filter(lambda x: len(x.strip()) > 0 \
                                        and "4store" not in x,\
                                        e.readlines()))
        response = HttpResponse()
        print error_msg
        response.write("Error with SPARQL query: %s"%(error_msg))
        response.status_code = e.code;
        return response
    except Exception, e:
        logger.exception("Error processing sparql %s\n%s"%(user_api_key,query))
        response = HttpResponse()
        response.write("Internal error %s"%(e))
        response.status_code = 500;
        return response

def examples(request):
    c = {}
    c.update(csrf(request))
    return render_to_response("examples.html",c)

def apikeys(request):
    return render_to_response("apikey.html")
