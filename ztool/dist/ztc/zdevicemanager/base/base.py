import click
import sys
import traceback
import time
import json
import hashlib
import re
from . import tabulate
from . import websocket as ws
from . import commentjson as commentjson

__all__ =['Critical','Error','Warning','Info','echo','cli','error','warning','debug','info','log','log_json','log_table','critical','fatal','add_init','init_all','sleep','set_output_filter','ws','commentjson',"md5","md5b","compare_versions","match_version","int32_version","version_int32"]


## GLOBAL OPTIONS
_options = {
    "colors": True,
    "traceback": True
}


## Styles
_styles = {
    "Critical":{"fg":"magenta","bold":True},
    "Error":{"fg":"red","bold":True},
    "Warning":{"fg":"yellow"},
    "Info":{"fg":"green"}
}


_init_fns = []

def add_init(init,prio=None):
    global _init_fns
    if prio is None or prio<0:
        _init_fns.append(init)
    else:
        _init_fns = [init]+_init_fns

def init_all():
    for ii in _init_fns:
        ii()

class Style():
    def __init__(self,val):
        self.val = val

    def __str__(self):
        if _options["colors"]:
            return click.style(str(self.val),**_styles[self.__class__.__name__])
        else:
            return str(self.val)

class Critical(Style):
    pass

class Error(Style):
    pass

class Warning(Style):
    pass

class Info(Style):
    pass

## The magical Echo

def echo(*args,**kwargs):
    sep = kwargs.get("sep"," ")
    end = kwargs.get("end","\n")
    kwargs.pop("sep",None)
    kwargs.pop("end",None)
    if args:
        click.echo(str(args[0]),nl=False,**kwargs)
        for i in range(1,len(args)):
            click.echo(str(sep),nl=False,**kwargs)
            click.echo(str(args[i]),nl=False,**kwargs)
    click.echo(str(end),nl=False,**kwargs)


def critical(*args,**kwargs):
    if "exc" in kwargs:
        exc = kwargs.pop("exc")
    else:
        exc = None
    if exc:
        if _options["traceback"]:
            echo(Critical("[fatal]>"),*args,err=True,**kwargs)
            traceback.print_exc()
        else:
            echo(Critical("[fatal]>"),str(exc),*args,err=True,**kwargs)
    else:
        echo(Critical("[fatal]>"),*args,err=True,**kwargs)
    sys.exit(2)
    

def fatal(*args,**kwargs):
    echo(Error("[error]>"),*args,err=True,**kwargs)
    sys.exit(1)

def error(*args,**kwargs):
    echo(Error("[error]>"),*args,err=True,**kwargs)

def warning(*args,**kwargs):
    echo(Warning("[warning]>"),*args,err=True,**kwargs)

def info(*args,**kwargs):
    if not output_filter: return
    echo(Info("[info]>"),*args,**kwargs)

def log(*args,**kwargs):
    if not output_filter: return
    echo(*args,**kwargs)

def debug(*args,**kwargs):
    if not output_filter or not _options["verbose"]: return
    echo(Info("[debug]>"),*args,**kwargs)


def log_json(js,*args,**kwargs):
    if not output_filter: return
    cls = kwargs.pop("cls",None)
    sort_keys = kwargs.pop("sort_keys",False)
    echo(json.dumps(js,indent=indent,cls=cls,sort_keys=sort_keys),*args,**kwargs)

def log_table(table,*args,**kwargs):
    if not output_filter: return
    headers = kwargs.pop("headers",[])
    echo(tabulate.tabulate(table,headers),*args,**kwargs)

def set_output_filter(enabled):
    global output_filter 
    output_filter = enabled

output_filter = True
indent = None

def sleep(n):
    time.sleep(n)

def md5(file_or_data):
    hh = hashlib.new("md5")
    if isinstance(file_or_data,str):
        hh.update(fs.readfile(file_or_data,"r"))
    else:
        hh.update(file_or_data)
    return hh.hexdigest()

def md5b(file_or_data):
    hh = hashlib.new("md5")
    if isinstance(file_or_data,str):
        hh.update(fs.readfile(file_or_data,"r"))
    else:
        hh.update(file_or_data)
    return hh.digest()

_re = re.compile("r([0-9][0-9]*)\.([0-9][0-9]*)\.([0-9][0-9]*)")
def compare_versions(v1,v2):
    mv1 = _re.match(v1)
    mv2 = _re.match(v2)

    iv1 = (int(mv1.group(1))<<32)+(int(mv1.group(2))<<16)+(int(mv1.group(3)))
    iv2 = (int(mv2.group(1))<<32)+(int(mv2.group(2))<<16)+(int(mv2.group(3)))
    return iv1-iv2

def match_version(v1):
    return _re.match(v1)

def int32_version(v):
    mv = _re.match(v)
    iv = (int(mv.group(1))<<24)+(int(mv.group(2))<<16)+(int(mv.group(3)))
    return iv

def version_int32(iv):
    x = iv>>24
    y = (iv>>16)&0xff
    z = iv&0xffff
    return "r"+str(x)+"."+str(y)+"."+str(z)

## Main entrypoint gathering 

class ZCliContext(object):
    def __init__(self):
        from zdevicemanager import ZdmClient
        from zdevicemanager.base.cfg import env
        self.zdm_client = ZdmClient(base_url=env.zdm)

    @property
    def zdm(self):
        return self.zdm_client


pass_zcli = click.make_pass_decorator(ZCliContext, ensure=True)

@click.group(help="Zerynth Device Manger (ZDM) command line interface")
@click.option("-v","verbose",flag_value=True,default=False,help="Verbose.")
@click.option("--colors/--no-colors","nocolors",default=True,help="To enable/disable colors.")
@click.option("--traceback/--no-traceback","notraceback",default=False,help="To enable/disable exception traceback printing on criticals.")
@click.option("--user_agent",default="zdmcli",help="To insert custom user agent.")
@click.option("--pretty","pretty",flag_value=True, default=False,help="To display pretty json output.")
@click.option("-J","__j",flag_value=True,default=False,help="To display the output in json format.")
@click.pass_context
def cli(ctx, verbose,nocolors,notraceback,user_agent,__j,pretty):
    ctx.obj = ZCliContext()
    _options["colors"]=nocolors
    _options["traceback"]=notraceback
    _options["verbose"]=verbose
    from zdevicemanager.base.cfg import env

    if verbose:
        info("You are using the ZDM endpoint: {}".format(env.zdm))

    env.user_agent = user_agent+"/"+env.var.version+"/"+env.platform
    env.human = not __j
    global indent 
    indent = 4 if pretty else None
