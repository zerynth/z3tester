from base import *
from .provisioner import *
import struct

class Resource():
    def __init__(self,res):
        flds = set(["type","name","mapping"]) - set(res.keys())
        if flds:
            raise DCZResourceMissingField("Missing required fields in resource "+str(flds))
        resname = res["name"]
        if len(resname)>16:
            raise DCZResourceNameTooLong("Resource name "+str(resname)+" is too long (max 16)")

        restype = res["type"]
        resargs = res.get("args",[])
        resmaps = res["mapping"]
        resmaps = [int(x,16) if isinstance(x,str) else x for x in resmaps]
        resfilter = res.get("filter","")
        resenc = res.get("encrypt",False)
        if not isinstance(resmaps,list):
            resmaps = [resmaps]
        resfrmt = res.get("format","bin")
        if len(resfrmt)>4:
            raise DCZResourceFormatTooLong("Resource format "+str(resname)+" is too long (max 4)")

        self._res = {
            "name":resname,
            "type":restype,
            "mapping":resmaps,
            "format":resfrmt,
            "args":resargs,
            "encrypt":resenc,
            "filter":resfilter
        }

    def load_from_file(self,ppath=None):
        fpath = fs.path(self.args)
        if not fs.exists(fpath):
            if ppath:
                fpath = fs.path(ppath,self.args)
                if not fs.exists(fpath):
                    raise DCZResourceFileNotExists("Can't find file "+str(fpath)+" for resource "+str(self.name))
            else:
                raise DCZResourceFileNotExists("Can't find file "+str(fpath)+" for resource "+str(self.name))
        rbin = fs.readfile(fpath,"b")
        self.bin=rbin
        self.chksum=fletcher32(rbin)
        self.dsc=self.name

    def load_from_buffer(self,rbin,offset=0):
        self.bin=rbin
        self.chksum=fletcher32(rbin[offset:])
        self.dsc=self.name


    def __getattr__(self,key):
        return self._res.get(key)

    def __setattr__(self,key,value):
        if key=="_res":
            super().__setattr__(key,value)
        self._res[key]=value

    def __repr__(self):
        return self._res

class Layout():
    def __init__(self,has_error=False):
        self.layout = {"bin":[],"loc":[],"dsc":[],"chk":[],"sz":[]}
        self.has_error = has_error

    def add(self,bin,loc,dsc):
        self.layout["bin"].append(bin)
        self.layout["loc"].append(loc)
        self.layout["dsc"].append(dsc)
        self.layout["chk"].append(fletcher32(bin))
        self.layout["sz"].append(len(bin))

    def add_resources(self,resources):
        for rname,rr in resources.items():
            for addr in rr.mapping:
                self.add(rr.bin,addr,rr.dsc+" @"+hex(addr))

    def validate(self):
        addrs, sizes = zip(*sorted(zip(self.layout["loc"],self.layout["sz"])))
        for i in range(len(addrs)-1):
            if addrs[i]+sizes[i]>addrs[i+1]:
                # ouch, overlapping segments
                _ , dscs = zip(*sorted(zip(self.layout["loc"],self.layout["dsc"])))
                raise DCZOverlapping("Resource "+str(dscs[i])+" overlaps with "+str(dscs[i+1]))

    def chunks(self):
        for i in range(len(self.layout["bin"])):
            yield {
                    "bin": self.layout["bin"][i],
                    "loc": self.layout["loc"][i],
                    "dsc": self.layout["dsc"][i]
                    }

    def __repr__(self):
        return self.layout

    def is_empty(self):
        return not bool(self.layout["bin"])

    def with_errors(self):
        return self.has_error

    def to_table(self):
        table = []
        for i in range(len(self.layout["bin"])):
            table.append([
                self.layout["dsc"][i],
                hex(self.layout["loc"][i]),
                self.layout["sz"][i],
                hex(self.layout["chk"][i])
                ])
        return table
        

def dcz_compile(dczmap,resources):
    dczaddr = dczmap.get("mapping",[])
    dczres = dczmap.get("resources",[])
   
    # remove duplicates and sort
    dczres = sorted(list(set(dczres)))
    mappings = sorted(list(set(dczaddr)))
    nmappings = len(mappings)
    if nmappings<1 or nmappings>8:
        raise DCZBadMapping("Device Configuration Zone needs one to eight mapping addresses, "+str(nmappings)+" given")

    for rname in dczres:
        if rname not in resources:
            raise DCZUnknownResource("Resource "+str(rname)+" referenced in DCZ is not defined")
        res = resources[rname]
        if len(res.mapping)<nmappings:
            raise DCZMappingMismatch("Resource "+str(rname)+" provides "+str(len(res.mapping))+" mappings while "+str(nmappings)+" are needed")
        


    dczentries = len(dczres)
    dczsize = HEADER_SIZE+ENTRY_SIZE*dczentries
    dczbin = bytearray(b'\x00'*dczsize)
    # crc + size + version + entries + cardinality
    dczhead = struct.pack("=I",0)+struct.pack("=I",dczsize)+struct.pack("=I",0)+struct.pack("=H",dczentries)+struct.pack("=H",nmappings)
    dczbin[0:HEADER_SIZE]=dczhead
    # build dcz
    dczindex = 0
    for rname,r in resources.items():
        if rname not in dczres:
            #skip resources not in dcz
            continue
        dczentry = bytearray(b'\x00'*ENTRY_SIZE)
        btag = rname.encode("utf-8")
        bfmt = r.format.encode("utf-8")
        dczentry[0:len(btag)]=btag
        for i in range(nmappings):
            dczentry[16+i*4:20+i*4] = struct.pack("=I",r.mapping[i])
        dczentry[48:52] = struct.pack("=I",len(r.bin))
        dczentry[52:52+len(bfmt)] = bfmt
        dczentry[56:60] = struct.pack("=I",r.chksum)
        dczentry[60:62] = struct.pack("=H",1 if r.encrypt else 0)
        dczentry[62:64] = struct.pack("=H",0)
        dczbin[HEADER_SIZE+ENTRY_SIZE*dczindex:HEADER_SIZE+ENTRY_SIZE*dczindex+ENTRY_SIZE]=dczentry
        dczindex+=1
    # calculate dcz 
    chk = fletcher32(dczbin[4:]) 
    dczbin[0:4]=struct.pack("=I",chk)
    # create dcz as a resource and return
    rr = Resource({
        "name":"dcz",
        "mapping":mappings,
        "format":"bin",
        "args":[],
        "type":"dcz"
        })
    rr.load_from_buffer(dczbin,4)
    return rr


def parse_resources(mapping,ppath=None):
    resources = {}
    provisioning = mapping.get("provisioning",{})
    if provisioning:
        # info("===== Provisioning")
        # scan all resources and create instances
        pres = provisioning.get("resources",[])
        for res in pres:
            rr = Resource(res)
            if rr.name in resources:
                raise DCZResourceDuplicate("Resource "+str(rr.name)+" has duplicated definition")
            resources[rr.name]=rr
        pmethod = provisioning.get("method","manual")
        if pmethod in ["manual","aws_iot_key_cert","zdm"]:
            provisioner = Provisioner.create(pmethod,mapping,ppath)
            for resname,res in resources.items():
                if res.type=="file":
                    res.load_from_file(ppath)
                elif res.type=="cacert":
                    provisioner.generate_cacert(res)
                elif res.type=="clicert":
                    provisioner.generate_clicert(res)
                elif res.type=="pubkey":
                    provisioner.generate_pubkey(res)
                elif res.type=="prvkey":
                    provisioner.generate_prvkey(res)
                elif res.type=="endpoint":
                    provisioner.generate_endpoint(res)
                elif res.type=="devinfo":
                    provisioner.generate_devinfo(res)
                else:
                    raise DCZResourceTypeNotSupported("Unsupported resource type "+str(res.type)+" for resource "+str(res.name))
        else:
            raise DCZResourceMethodNotSupported("Unsupported provisioning type "+str(pmethod))

    return resources, provisioner


######## some commands

def get_layout_at(ppath,fail=False):
    if fail:
        logm = fatal
    else:
        logm = warning
    mapfile = fs.path(ppath,"dcz.yml")
    if not fs.exists(mapfile):
        return Layout()
    map = fs.get_yaml(mapfile)
    if not map.get("active",False):
        logm("Layout generation skipped, active flag not set")
        return Layout()
    dcz_map = map.get("dcz",{})
    layout = Layout()
    try:
        resources, provisioner = parse_resources(map,ppath)
    except Exception as e:
        warning("Resource parsing failed")
        logm(e)
        return Layout(has_error=e)
    if provisioner:
        try:
            provisioner.finalize(resources)
            provisioner.dump()
        except Exception as e:
            warning("Provisioner failed")
            logm(e)
            return Layout(has_error=e)
    try:
        if dcz_map:
            dczres = dcz_compile(dcz_map,resources)
            resources[dczres.name]=dczres
    except Exception as e:
        warning("DCZ parsing failed")
        logm(e)
        return Layout(has_error=e)

    layout.add_resources(resources)
    # table = layout.to_table()
    # log_table(table,headers=["Segment","Address","Size","Checksum"])
    try:
        layout.validate()
    except Exception as e:
        warning("Layout validation failed")
        logm(e)
        return Layout(has_error=e)

    return layout





######## exceptions, utils and constants

class DCZResourceNameTooLong(Exception):
    pass
class DCZResourceFormatTooLong(Exception):
    pass
class DCZResourceFileNotExists(Exception):
    pass
class DCZResourceTypeNotSupported(Exception):
    pass
class DCZResourceMethodNotSupported(Exception):
    pass
class DCZResourceMissingField(Exception):
    pass
class DCZResourceDuplicate(Exception):
    pass
class DCZBadMapping(Exception):
    pass
class DCZMappingMismatch(Exception):
    pass
class DCZUnknownResource(Exception):
    pass
class DCZOverlapping(Exception):
    pass

def fletcher32(buf):
    sum1 = 0
    sum2 = 0
    sz = len(buf)
    if sz%2!=0:
        sz=sz-1
    for i in range(0,sz,2):
        e = buf[i]|(buf[i+1]<<8)
        sum1 = (sum1+e)%0xffff
        sum2 = (sum1+sum2)%0xffff

    if sz!=len(buf):
        e = buf[-1]
        sum1=(sum1+e)%0xffff
        sum2=(sum1+sum2)%0xffff

    result = sum1|(sum2<<16)
    return result


ENTRY_SIZE = 64
HEADER_SIZE = 16


