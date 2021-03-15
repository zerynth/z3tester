from base import *
import json

class AWS():

    def __init__(self,pmethod,aws_data):
        import boto3
        self.pmethod = pmethod
        self.credentials = {}
        self.credentials["aws_access_key_id"] = aws_data["aws_access_key_id"]
        self.credentials["aws_secret_access_key"] = aws_data["aws_secret_access_key"]
        self.credentials["region_name"] = aws_data["region_name"]

        self.client = boto3.client("iot",**self.credentials)
        self.aws_data = aws_data
        self.cache = {}

    def _generate_endpoint(self):
        etype = self.aws_data.get("endpoint_type","verisign")
        if "endpoint" not in self.cache:
            endpointType = "iot:Data" if etype=="verisign" else "iot:Data-ATS"
            res = self.client.describe_endpoint(endpointType=endpointType)
            self.cache["endpoint"] = res["endpointAddress"]

    def _generate_clicert_and_key(self,cert_active=False):
        if "clicert"  not in self.cache:
            res = self.client.create_keys_and_certificate(setAsActive=cert_active)
            clicert_pem = res["certificatePem"]
            prvkey_pem = res["keyPair"]["PrivateKey"]
            pubkey_pem = res["keyPair"]["PublicKey"]
            clicert_bin = clicert_pem.encode("utf-8")+b'\x00'
            prvkey_bin = prvkey_pem.encode("utf-8")+b'\x00'
            pubkey_bin = pubkey_pem.encode("utf-8")+b'\x00'
            self.cache["clicert"]=clicert_bin
            self.cache["prvkey"]=prvkey_bin
            self.cache["pubkey"]=pubkey_bin
            self.cache["cert_arn"]=res["certificateArn"]


    def generate_cacert(self,res):
        # TODO: check pmethod here whne support for self signed CA will be ready
        self._generate_endpoint()
        etype = self.aws_data.get("endpoint_type","verisign")
        cacert_file = fs.path(fs.dirname(__file__),"cacert_"+etype+".pem")
        cacert_bin = fs.readfile(cacert_file,"b")
        cacert_bin = cacert_bin+b'\x00'  #terminate with zero for Zerynth compatibility
        res.load_from_buffer(cacert_bin)

    def generate_clicert(self,res,**kwargs):
        cert_active = self.aws_data.get("activate_cert",False)
        self._generate_endpoint()
        if self.pmethod=="aws_iot_key_cert":
            self._generate_clicert_and_key(cert_active)
            clicert_bin = self.cache["clicert"]
            res.load_from_buffer(clicert_bin)
        elif self.pmethod=="aws_iot_csr_cert":
            pass
    
    def generate_prvkey(self,res,**kwargs):
        cert_active = self.aws_data.get("activate_cert",False)
        self._generate_endpoint()
        if self.pmethod=="aws_iot_key_cert":
            self._generate_clicert_and_key(cert_active)
            prvkey_bin = self.cache["prvkey"]
            res.load_from_buffer(prvkey_bin)
        elif self.pmethod=="aws_iot_csr_cert":
            pass

    def generate_pubkey(self,res,**kwargs):
        cert_active = self.aws_data.get("activate_cert",False)
        self._generate_endpoint()
        if self.pmethod=="aws_iot_key_cert":
            self._generate_clicert_and_key(cert_active)
            pubkey_bin = self.cache["pubkey"]
            res.load_from_buffer(pubkey_bin)
        elif self.pmethod=="aws_iot_csr_cert":
            pass

    def generate_endpoint(self,res,**kwargs):
        self._generate_endpoint()
        endpoint = self.cache["endpoint"]
        if res.format == "str" or res.format=="bin":
            res.load_from_buffer(endpoint.encode("utf-8"))
        elif res.format == "json":
            res.load_from_buffer(json.dumps({"endpoint":endpoint}).encode("utf-8"))

    def generate_devinfo(self,res,**kwargs):
        # generate placeholder, will be filled by posthook
        pass

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
        info("======= AWS Provisioner")
        info("Endpoint:",self.cache.get("endpoint"))
        info("Thing Name:",self.cache.get("thingname"))
        info("Cert Arn:",self.cache.get("cert_arn"))


    def finalize(self, resources):
        self.generate_thing()
        for rname,res in resources.items():
            if res.type=="devinfo":
                # found devinfo, fill them
                if res.format=="bin" or res.format=="str":
                    devinfo = "%s;%s;%s"%(self.cache["thingname"],self.cache["thingid"],self.cache["cert_arn"])
                    devinfo = devinfo.encode("utf-8")
                elif res.format == "json":
                    devinfo = '{"thing_name":"%s","thing_id":"%s","cert_arn":"%s"}'%(self.cache["thingname"],self.cache["thingid"],self.cache["cert_arn"])
                    devinfo = devinfo.encode("utf-8")
                res.load_from_buffer(devinfo)
                break
        else:
            warning("Resource not found while finalizing provisioning")


