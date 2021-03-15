from .aws import *
from .zdm import *


class Provisioner():

    @staticmethod
    def create(pmethod,config,ppath=None):
        if pmethod.startswith("aws"):
            aws_data = config.get("aws",{})
            return AWS(pmethod,aws_data)
        elif pmethod.startswith("gcp"):
            gcp_data = config.get("gcp",{})
            pass
        elif pmethod.startswith("azure"):
            azure_data = config.get("azure",{})
            pass
        elif pmethod.startswith("manual"):
            return Provisioner()
        elif pmethod.startswith("zdm"):
            return ZDM(pmethod,config.get("zdm",{}),ppath)



    def __init__(self):
        pass

    def generate_cacert(self,res):
        res.load_from_file()

    def generate_clicert(self,res,**kwargs):
        res.load_from_file()
    
    def generate_prvkey(self,res,**kwargs):
        res.load_from_file()

    def generate_pubkey(self,res,**kwargs):
        res.load_from_file()

    def generate_endpoint(self,res,**kwargs):
        res.load_from_file()


    def generate_devinfo(self,res,**kwargs):
        res.load_from_file()


    def dump(self):
        info("======= Manual Provisioner")


    def finalize(self, resources):
        pass
