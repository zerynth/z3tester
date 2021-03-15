from base import *
import json
import base64


class ZDM():

    def __init__(self,pmethod,data,ppath):
        self.pmethod = pmethod
        self.ppath = ppath
        self.endpoint_mode = "production"
        self.auth_mode = "cloud_token"
        self.key_type = None
        self.pdata={}

    def _load_provisioner(self,res):
        pth = fs.path(self.ppath,res.args) if self.ppath else fs.path(res.args)
        try:
            self.pdata = fs.get_json(pth)
        except:
            raise Exception("Can't read file "+str(pth))

        if "devinfo" not in self.pdata:
            raise Exception("Missing 'devinfo' field in "+str(pth))
        else:
            self.auth_mode = self.pdata["devinfo"]["mode"]
            self.key_type = self.pdata["devinfo"].get("key_type","")

        if "endpoint" not in self.pdata:
            raise Exception("Missing 'endpoint' field in "+str(pth))
        else:
            endpoint = self.pdata["endpoint"]["host"]
            if "test" in endpoint:
                self.endpoint_mode = "test"
            elif "stage" in endpoint:
                self.endpoint_mode = "stage"
            else:
                self.endpoint_mode = "production"


        if "prvkey" not in self.pdata:
            raise Exception("Missing 'prvkey' field in "+str(pth))


        return self.pdata


    def generate_cacert(self,res):
        data = self._load_provisioner(res)
        cacert_file = fs.path(fs.dirname(__file__),self.endpoint_mode,"ca.pem")
        cacert_bin = fs.readfile(cacert_file,"b")
        cacert_bin = cacert_bin+b'\x00'  #terminate with zero for Zerynth compatibility
        res.load_from_buffer(cacert_bin)

    def generate_clicert(self,res,**kwargs):
        data = self._load_provisioner(res)
        if "clicert" in data:
            clicert_bin = data["clicert"].encode("utf-8")+b'\x00'
            res.load_from_buffer(clicert_bin)
        else:
            res.load_from_buffer(b'\x00'*16)

    
    def generate_prvkey(self,res,**kwargs):
        data = self._load_provisioner(res)
        prvkey_bin = data["prvkey"]
        if self.key_type=="sym" and self.auth_mode!="cloud_token":
            prvkey_bin = base64.standard_b64decode(prvkey_bin)
        elif self.auth_mode=="cloud_token":
            prvkey_bin = prvkey_bin.encode("utf-8")
        else:
            # it's pem
            prvkey_bin = prvkey_bin.encode("utf-8")+b'\x00'

        res.load_from_buffer(prvkey_bin)

    def generate_pubkey(self,res,**kwargs):
        data = self._load_provisioner(res)
        pubkey_bin = data["pubkey"]
        pubkey_bin = data["pubkey"].encode("utf-8")+b'\x00'
        res.load_from_buffer(pubkey_bin)

    def generate_endpoint(self,res,**kwargs):
        data = self._load_provisioner(res)
        endpoint = data["endpoint"]
        if res.format == "str" or res.format=="bin":
            res.load_from_buffer(endpoint.encode("utf-8"))
        elif res.format == "json":
            res.load_from_buffer(json.dumps(endpoint).encode("utf-8"))

    def generate_devinfo(self,res,**kwargs):
        data = self._load_provisioner(res)
        nfo = data["devinfo"]
        if res.format == "str" or res.format=="bin":
            res.load_from_buffer(nfo.encode("utf-8"))
        elif res.format == "json":
            res.load_from_buffer(json.dumps(nfo).encode("utf-8"))

    def generate_thing(self):
        thingname = self.aws_data.get("thing_prefix")
        thing_policy = self.aws_data.get("thing_policy")
        c_arn = self.cache["cert_arn"]
        if thingname:
            thingname = thingname + "-" +md5(c_arn.encode("utf-8"))
            tparams = { "thingName":thingname }
            if "thing_type" in self.aws_data:
                tparams["thingTypeName"]=self.aws_data["thing_type"]
            if "thing_attributes" in self.aws_data:
                tparams["attributePayload"] = {"attributes":self.aws_data["thing_attributes"]}
            # create thing
            thing = self.client.create_thing(**tparams)
            self.cache["thingname"] = thing["thingName"]
            self.cache["thingid"] = thing["thingId"]
            # attach thing to certificate
            self.client.attach_thing_principal(thingName=thingname,principal=c_arn)
            if thing_policy:
                # attach certificate to the device policy
                self.client.attach_principal_policy(policyName=thing_policy,principal=c_arn)

    def dump(self):
        info("======= ZDM Provisioner")
        info("Endpoint:",self.pdata.get("endpoint","UNKNOWN"))
        info("Device  :",self.pdata.get("devinfo","UNKNOWN"))


    def finalize(self, resources):
        pass
    #     for rname,res in resources.items():
    #         if res.type=="devinfo":
    #             # found devinfo, fill them
    #             if res.format=="bin" or res.format=="str":
    #                 devinfo = "%s;%s;%s"%(self.cache["thingname"],self.cache["thingid"],self.cache["cert_arn"])
    #                 devinfo = devinfo.encode("utf-8")
    #             elif res.format == "json":
    #                 devinfo = '{"thing_name":"%s","thing_id":"%s","cert_arn":"%s"}'%(self.cache["thingname"],self.cache["thingid"],self.cache["cert_arn"])
    #                 devinfo = devinfo.encode("utf-8")
    #             res.load_from_buffer(devinfo)
    #             break
    #     else:
    #         warning("Resource not found while finalizing provisioning")



