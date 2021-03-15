import requests
import datetime
import json
from .base import *
from .cfg import *
from .fs import *
import time
import os

TimeoutException = requests.exceptions.Timeout
if int(os.environ.get("ZERYNTH_TESTMODE",0))!=0:
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    _ssl_verify = False
else:
    _ssl_verify = fs.path(fs.dirname(__file__),"certs.pem")

_default_timeout=5
_default_retries=3


################### json special type encoder
class ZjsonEncoder(json.JSONEncoder):
    def default(self,obj):
        if isinstance(obj, datetime.datetime):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

def zpost(url,data,headers={},auth=True,timeout=_default_timeout):
    hh = {"Content-Type": "application/json","User-agent":env.user_agent}
    if auth:
        token = get_token()
        hh.update({"Authorization": "Bearer "+token})
    hh.update(headers)
    for x in range(_default_retries):
        try:
            return requests.post(url=url, headers=hh, data=json.dumps(data, cls=ZjsonEncoder),timeout=timeout,verify=_ssl_verify,proxies=env.proxies)
        except TimeoutException:
            warning("Timeout! Retrying...")
            timeout=timeout*2
    raise TimeoutException

def zget(url,headers={},params={},auth=True,token=None,stream=False,timeout=_default_timeout):
    hh = {"Content-Type": "application/json","User-agent":env.user_agent}
    if auth:
        if auth=="conditional":
            token = get_token(True)
        else:
            if not token:
                token = get_token()
    if token: hh.update({"Authorization": "Bearer "+token})
    hh.update(headers)
    for x in range(_default_retries):
        try:
            return requests.get(url=url, headers=hh,timeout=timeout,params=params,verify=_ssl_verify,stream=stream,proxies=env.proxies)
        except TimeoutException:
            warning("Timeout! Retrying...")
            timeout=timeout*2
    raise TimeoutException

def zdelete(url,headers={},auth=True,timeout=_default_timeout):
    hh = {"Content-Type": "application/json","User-agent":env.user_agent}
    if auth:
        token = get_token()
        hh.update({"Authorization": "Bearer "+token})
    hh.update(headers)
    for x in range(_default_retries):
        try:
            return requests.delete(url=url, headers=hh,timeout=timeout,verify=_ssl_verify,proxies=env.proxies)
        except TimeoutException:
            warning("Timeout! Retrying...")
            timeout=timeout*2
    raise TimeoutException

def zput(url, data,headers={},auth=True,timeout=_default_timeout):
    hh = {"Content-Type": "application/json","User-agent":env.user_agent}
    if auth:
        token = get_token()
        hh.update({"Authorization": "Bearer "+token})
    hh.update(headers)
    for x in range(_default_retries):
        try:
            return requests.put(url=url, headers=hh, data=json.dumps(data, cls=ZjsonEncoder),timeout=timeout,verify=_ssl_verify,proxies=env.proxies)
        except TimeoutException:
            warning("Timeout! Retrying...")
            timeout=timeout*2
    raise TimeoutException

def zgetraw(url):
    r = requests.get(url,stream=True)
    return r.raw

def get_token(continue_if_none=False):
    tokdata = env.get_token()
    token = tokdata.token
    fn = warning if continue_if_none else critical
    if token:
        try:
            now = time.time()
            nowth = now-60*60*24*5 #5 days before expiration triggers renewal
            if tokdata.expires>nowth:
                return token
            elif tokdata.expires<nowth and tokdata.expires>now:
                #try to renew
                info("Token almost expired, trying to renew...")
                try:
                    res = zget(env.api.renew,token=token)
                    rj = res.json()
                    env.set_token(rj["token"])
                    return rj["token"]
                except Exception as e:
                    warning("Token renewal failed",exc=e)
            else:
                #force another login
                token = None
                fn("Token expired! Please run 'zdm login' to get a new one")
        except Exception as e:
            token=None
            fn("Critical error while retrieving authorization token:",exc=e)
    else:
        fn("No authorization token! Please run 'zdm login' to get one")
    return token

def get_token_headers(continue_if_none=False):
    hh = {"Content-Type": "application/json","User-agent":env.user_agent}
    token = get_token(continue_if_none)
    hh.update({"Authorization": "Bearer "+token})
    return hh

def get_token_data():
    token = get_token(True)
    if not token:
        return None
    tks = token.split(".")
    data = tks[1]
    data = decode_base64(data).decode("utf-8")
    data = json.loads(data)
    return data
