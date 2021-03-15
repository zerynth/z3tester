from base import *
import sys
import importlib
import json
import hashlib



__all__=['Discover']



class Discover():
    def __init__(self):
        self.round=0
        if env.is_linux():
            from . import linuxusb
            self.devsrc = linuxusb.LinuxUsb()
        elif env.is_mac():
            from . import macusb 
            self.devsrc = macusb.MacUsb()
        else:
            from . import winusb
            self.devsrc = winusb.WinUsb()
        self.devices = {}
        self.matched_devices = {}
        self.device_cls = {}
        self.targets = {}
        self.load_devices()

    def get_targets(self):
        return self.targets

    def get_target(self,target,options={}):
        tgt = self.targets.get(target)
        if not tgt:
            return None
        return tgt["cls"](tgt,options) 

    def load_devices(self):
        bdirs = fs.dirs(env.devices)
        for bj in tools.get_devices():
            for cls in bj["classes"]:
                try:
                    sys.path.append(bj["path"])
                    module,bcls = cls.split(".")
                    bc = importlib.import_module(module)
                    dcls = getattr(bc,bcls)
                    bjc = dict(bj)
                    bjc["cls"]=dcls
                    sys.path.pop()
                    self.device_cls[bj["path"]+"::"+bcls]=bjc
                    if "target" in bj:
                        if "jtag_class" in bj:
                            if bj["jtag_class"]==bcls:
                                self.targets[bj["target"]]=bjc
                        else:
                            self.targets[bj["target"]]=bjc
                except Exception as e:
                    warning(e)

    def wait_for_uid(self,uid,loop=5,matchdb=True):
        for l in range(loop):
            devs = self.run_one(matchdb)
            uids = self.matching_uids(devs,uid)
            if len(uids)>=1:
                return uids,devs
            sleep(1)
            info("attempt",l+1)
        return [],{}

    def wait_for_classname(self,classname,loop=5,matchdb=True):
        devs = {}
        uids = []
        for l in range(loop):
            devs = self.run_one(matchdb)
            uids = [uid for uid,dev in devs.items() if dev.classname==classname]
            if len(uids)>=1:
                tgt = devs[uids[0]]
                if tgt.port is not None:
                    return uids,devs
            sleep(1)
            info("attempt",l+1)
        if len(uids)>=1:
            return uids,devs
        return [],{}

    def parse(self):
        devices = self.devsrc.parse()
        newdevices = {}
        for dev in devices:
            dev["uid"]=self.make_uid(dev)
            dev["fingerprint"]=self.make_fingerprint(dev)
            if dev["uid"] not in newdevices:
                newdevices[dev["uid"]]={}
            newdevices[dev["uid"]][dev["fingerprint"]]=dev
        # fuse devices by uid
        ret={}
        for k,v in newdevices.items():
            fused = {}
            for fg,vv in v.items():
                for key,value in vv.items():
                    if (key not in fused) or not fused[key]:
                        fused[key]=value
            fused["fingerprint"]=self.make_fingerprint(fused)
            ret[k]=fused
        return ret

    def output_devices(self):
        if not self.devices:
            log(" ")
        else:
            table = []
            for k,v in self.devices.items():
                if env.human:
                    table.append([v["vid"],v["pid"],v["sid"],v["uid"],v["port"],v["disk"],v["desc"]])
                else:
                    log_json(v)
            if env.human:
                log_table(table,headers=["vid","pid","sid","uid","port","disk","desc"])
        log("")

    def output_matched_devices(self):
        if not self.matched_devices:
            log(" ")
        else:
            table = []
            for k,v in self.matched_devices.items():
                dd = v.to_dict()
                dd["hash"]=k
                log(v["port"])
                #if env.human:
                #    table.append([v["name"],v["alias"],v["target"],v["uid"],v["chipid"],v["remote_id"],v["classname"],v["port"],v["disk"]])
                #else:
                #    log_json(dd)
            #if env.human:
            #    table = sorted(table,key=lambda x:x[3])
            #    log_table(table,headers=["name","alias","target","uid","chipid","remote_id","classname","port","disk"])
        #log("")

    def compare_dbs(self, new_db, old_db):
        if new_db.keys()!=old_db.keys():
            return False
        else:
            for k,v in old_db.items():
                if new_db[k]["fingerprint"]!=v["fingerprint"]:
                    return False
        return True

    def match_devices(self):
        ndb = {}
        pdevs = []
        tuid= {}
        # augment devices with devdb info (alias and target and name)
        for uid,dev in self.devices.items():
            devs = env.get_dev(uid)
            if devs:
                for alias,d in devs.items():
                    x = dict(dev)
                    x["alias"] = d.alias
                    x["custom_name"] = d.name
                    x["target"] = d.target
                    x["chipid"] = d.chipid
                    x["remote_id"] = d.remote_id
                    x["classname"] =d.classname
                    pdevs.append(x)
                    if d.uid not in tuid:
                        tuid[d.uid]=[]
                    tuid[d.uid].append(x)
            else:
                dev["alias"]=None
                pdevs.append(dev)
        
        #print(tuid)
        # perform device - known device matching
        for dkey,dinfo in self.device_cls.items():
            cls = dinfo["cls"]
            for dev in pdevs:
                #print("Checking",dev["uid"],dev["uid"] in tuid,dev)
                if dev["uid"] in tuid:  # uid with alias and target
                    if dinfo.get("target")==dev.get("target","-") and cls.__name__==dev.get("classname","-"): #same target can have different device classes
                        obj = cls(dinfo,dev)
                        ndb[obj.hash()]=obj
                elif cls.match(dev):
                    obj = cls(dinfo,dev)
                    ndb[obj.hash()]=obj
        # augment no_sid/linked devices -_-
        ddevs={}
        for h,obj in ndb.items():
            if obj.has_double_dev and "ser" in obj.cls.__name__:
                ddevs[h]=obj
                for h2,obj2 in ndb.items():
                    if obj.target == obj2.target and "ser" not in obj2.cls.__name__:
                        ndb[h2].set("port",obj.port)
                        for h3, obj3 in ndb.items():
                            if obj.vid == obj3.vid and obj.pid == obj3.pid and "ser" not in obj3.cls.__name__:
                                ddevs[h3]=obj3
        for h,obj in ddevs.items():
            del ndb[h]
        for h,obj in ndb.items():
            if obj.sid == "no_sid" or obj.has_linked_devs:
                # get all registered linked devices
                devs = env.get_linked_devs(obj.target)
                if devs and obj.original_target and obj.customized:
                    for k,d in devs.items():
                        d.set("original_target", obj.original_target)
                        d.set("customized", obj.customized)
                obj.set("linked_devs",{k:d.to_dict() for k,d in devs.items()})
        return ndb

    def matching_uids(self,devs,a_uid):
        uids=[]
        for uid,dev in devs.items():
            u = dev.uid
            if u.startswith(a_uid):
                uids.append(u)
        return uids


    def matching_uids_or_alias(self,devs,a_uid):
        uids=[]
        for uid,dev in devs.items():
            if dev.uid.startswith(a_uid):
                uids.append(dev.uid)
            elif dev.alias and dev.alias.startswith(a_uid):
                uids.append(dev.alias)
        return uids

    def get_by_alias(self,devs,alias):
        for h,dev in devs.items():
            if dev.alias==alias:
                return dev
        return None

    def find_again(self,dev):
        uids,devs = self.wait_for_uid(dev.uid)
        if len(uids)!=1:
            return None
        return devs[dev.hash()]


    def search_for_device(self,alias):
        devs = self.run_one(True)
        res = []
        for h,dev in devs.items():
            if dev.alias==alias:
                return dev
            elif dev.alias and dev.alias.startswith(alias):
                res.append(dev)
        if len(res)==1:
            return res[0]
        return res

    def search_for_attached_device(self,target=None):
        devs = self.run_one(True)
        res = []
        for h,dev in devs.items():
            if target:
                if dev.target==target:
                    return dev
            else:
                res.append(dev)
        if len(res) > 0:
            return res[0]
        return res


    def run_one(self,matchdb):
        nd = self.parse()
        if matchdb:
            self.devices=nd
            return self.match_devices()
        else:
            return nd

    def run(self,loop,looptime,matchdb):
        while True:
            show=False

            # parse devices
            nd = self.parse()
            if not self.compare_dbs(nd,self.devices):
                self.devices=nd
                show=True

            if matchdb and show:
                self.matched_devices = self.match_devices()
                self.output_matched_devices()
            elif show:
                self.output_devices()

            if loop: 
                sleep(looptime/1000)
            else:
                break
        

    def make_uid(self,dev):
        h = hashlib.sha1()
        k = dev["vid"]+":"+dev["pid"]+":"+dev["sid"]
        h.update(bytes(k,"ascii"))
        return h.hexdigest()

    def make_fingerprint(self,dev):
        return (dev.get("port") or "")+":"+(dev.get("disk") or "")

