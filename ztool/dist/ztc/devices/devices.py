from base import *
import re
import base64
from jtag import *

__all__=["Device","Board"]

class Device():
    def __init__(self,info={},dev={}):
        self._info=info
        self._dev = dev
        self._info["classname"] = self.__class__.__name__

    def hash(self):
        return self._info.get("target","---")+":"+self._dev.get("uid","---")

    def to_dict(self):
        x = {}
        x.update(self._info)
        x.update(self._dev)
        if "class" in x:
            x["classes"]=x["class"]
            del x["class"]
        if "cls" in x:
            del x["cls"]
        return x

    def __getitem__(self,key):
        return self.__getattr__(key)


    def __getattr__(self,attr):
        if attr in self._info:
            return self._info[attr]
        if attr in self._dev:
            return self._dev[attr]
        return None
        #raise AttributeError ##TODO: check correctness

    def get(self,attr,default=None):
        x = self.__getattr__(attr)
        if x is None: return default
        return x

    def set(self,attr,value):
        self._dev[attr]=value

    def virtualize(self,bin):
        pass

    def burn_with_probe(self,bin,offset=0,reset=True):
        #TODO: add support for multifile vms
        offs = offset if isinstance(offset,str) else hex(offset)
        fname = fs.get_tempfile(bin)
        try:
            pb  = Probe()
            pb.connect()
            jcmd ="program "+fs.wpath(fname)+" verify "
            if reset:
                jcmd+="reset "
            jcmd+=offs
            pb.send(jcmd,info)
            now = time.time()
            wait_verification = False
            while time.time()-now<self.get("jtag_timeout",30):
                lines = pb.read_lines()
                for line in lines:
                    if line.startswith("wrote 0 "):
                        return False,"0 bytes written!"
                    if line.startswith("** Programming Started **"):
                        wait_verification=True
                    if wait_verification and line.startswith("** Verified OK"):
                        if self.get("jtag_burn_end"):
                            pb.send(self.get("jtag_burn_end"))
                        return True, ""
                    if wait_verification and line.startswith("** Verified Failed"):
                        return False, "Verification failed"
                    if "** Programming Finished **" in line:
                        # reset countdown
                        now = time.time()
                    if "** Programming Failed **" in line:
                        return False, "Programming failed"
                    if "** Programming Finished **" in line:
                        # restart timeout counter
                        now = time.time()
            return False,"timeout"
        except Exception as e:
            return False, str(e)
        finally:
            fs.del_tempfile(fname)

    def get_chipid(self):
        try:
            pb = Probe()
            pb.connect()
            cmds = self.jtag_chipid_command.split(";")
            for cmd in cmds:
                warning(cmd)
                pb.send(cmd)
            # pb.send("halt; mdw 0x1fff7a10; mdw 0x1fff7a14; mdw 0x1fff7a18")
            lines = pb.read_lines(timeout=1)
            ids = []
            for line in lines:
                # if ":" not in line or not line.startswith("0x1fff7"):
                if ":" not in line or not line.startswith(self.jtag_chipid_prefix):
                    continue
                fld = line.split(":")
                ids.append(fld[1].strip())
            # if len(ids)!=3:
            if len(ids)<self.jtag_chipid_len:
                warning("Probe result too short!")
                return None
            ids = ids[:self.jtag_chipid_len]
            chipid = "".join([id[::-1] for id in ids])
            return chipid
        except Exception as e:
            warning(e)
            return None

    def get_vmuid(self):
        pb = Probe()
        pb.connect()
        cmd="reset halt;"
        addr = self.vmstore_offset
        cmd+="; ".join(["mdw "+hex(int(addr,16)+i) for i in range(0,32,4)])
        cmds = cmd.split(";")
        for cmd in cmds:
            warning(cmd)
            pb.send(cmd)
        # halt and read 8 words
        pb.send(cmd)
        lines = pb.read_lines(timeout=1)
        ids = []
        for line in lines:
            if ":" not in line or not line.startswith("0x"):
                continue
            fld = line.split(":")
            ids.append(fld[1].strip())
        if len(ids)<8:
            warning("Probe result too short!",len(ids),ids)
            return None
        # first word is length
        vmlen = int(ids[0],16)
        # recover all the other bytes
        bt = bytearray()
        for id in ids[1:]:
            bp = bytearray()
            for i in range(0,8,2):
                bb = int(id[i:i+2],16)
                # temporary append
                bp.append(bb)
            # extend reversed
            bt.extend(bp[::-1])
        vmuid = bt[0:vmlen].decode("utf-8")
        return vmuid

    def do_burn_vm(self,vm,options={},outfn=None):
        if not self.jtag_capable and options.get("probe"):
            return False, "Target does not support probes!"
        portbin = None
        what_to_burn="bin" if not self.burn_hex else "hex"
        info("Burning",what_to_burn)
        if self.customized:
            portfile = fs.path(self.path,"port.bin")
            portbin = fs.readfile(portfile,"b")
        try:
            if isinstance(vm[what_to_burn],str):
                vmbin=bytearray(base64.standard_b64decode(vm[what_to_burn]))
                if options.get("probe") or self.preferred_burn_with_jtag:
                    if self.preferred_burn_with_jtag:
                        options = self.preferred_burn_with_jtag
                    tp = start_temporary_probe(self.target,options.get("probe"))
                    res,out = self.burn_with_probe(vmbin,vm["map"]["vm"][0])
                    stop_temporary_probe(tp)
                else:
                    if portbin:
                        res,out = self.burn_custom(vmbin,portbin,outfn)
                    else:
                        res,out = self.burn(vmbin,outfn)
            else:
                vmbin=[ base64.standard_b64decode(x) for x in vm[what_to_burn]]
                if options.get("probe"):
                    tp = start_temporary_probe(self.target,options.get("probe"))
                    res,out = self.burn_with_probe(vmbin)
                    stop_temporary_probe(tp)
                else:
                    if portbin:
                        res,out = self.burn_custom(vmbin,portbin,outfn)
                    else:
                        res,out = self.burn(vmbin,outfn)
            return res,out
        except Exception as e:
            return False, str(e)

    def do_burn_layout(self,layout,options={},outfn=None):
        if not self.jtag_capable and options.get("probe"):
            return False, "Target does not support probes!"
        # TODO: add support for custom
        if self.customized:
            return False, "Layout burning is not supported for custom VMs"
            # portfile = fs.path(self.path,"port.bin")
            # portbin = fs.readfile(portfile,"b")
        try:
            if self.custom_burn_layout:
                return self.custom_burn_layout(layout,options,outfn)
            else:
                if options.get("probe") or self.preferred_burn_with_jtag:
                    if self.preferred_burn_with_jtag:
                        options = self.preferred_burn_with_jtag
                    tp = start_temporary_probe(self.target,options.get("probe"))
                    for chunk in layout.chunks():
                        info("Burning chunk at",hex(chunk["loc"]) if not isinstance(chunk["loc"],str) else chunk["loc"],"size",len(chunk["bin"]),"bytes")
                        res,out = self.burn_with_probe(chunk["bin"],chunk["loc"],reset=False)
                        if not res:
                            stop_temporary_probe(tp)
                            return False,"Burning failed for "+str(chunk["dsc"])
                    stop_temporary_probe(tp)
                    return True,""
                else:
                    return False, "Layout burning not supported without a probe"
        except Exception as e:
            return False, str(e)

    def do_get_chipid(self,probe,skip_probe=False):
        if not self.jtag_capable:
            return False, "Target does not support probes!"
        try:
            # start temporary probe
            if not skip_probe:
                tp = start_temporary_probe(self.target,probe)
            chipid = self.get_chipid()
            # stop temporary probe
            if not skip_probe:
                stop_temporary_probe(tp)
            if not chipid:
                return None,"Can't retrieve chip id"
            return chipid,""
        except Exception as e:
            warning(e)
            return None,"Can't retrieve chip id"

    def do_erase_flash(self,outfn=None):
        if not self.flash_erasable:
            return False, "Target does not support erase flash feature!"
        try:
            res,out = self.erase(outfn=outfn)
            return res,out
        except Exception as e:
            warning(e)
            return None,"Can't erase flash"

    def do_custom_action(self, action, outfn=None, action_param=None):
        try:
            action_meth = getattr(self, action.lower())
            if not action_meth:
                return None,"unsupported action '%s'" % action
            if not action_param:
                res,out = action_meth(outfn=outfn)
            else:
                res,out = action_meth(action_param, outfn=outfn)
            return res,out
        except Exception as e:
            warning(e)
            return None,"exception while executing custom action"

    def reset(self):
        pass

    def restore(self):
        pass

    def load_family(self):
        dpath = fs.path(env.vhal,self.family_type,self.family_name,"vhal.json")
        try:
            self.family = fs.get_json(dpath)
            return True
        except Exception as e:
            warning("Can't load device family!",self.family_name,"@",dpath)
        return False


    def load_specs(self):
        try:
            defines, peripherals, pinout = self.__get_specs()
            names = set()
            for k,v in pinout.items():
                names.add(k)
                for z,w in v.items():
                    names.add(w)
            names.update(peripherals)
            self.defines = defines
            self.peripherals=peripherals
            self.pinmap=pinout
            self.names=names

            classes = {
                "D":0x0000,
                "A":0x0100,
                "SPI":0x0200,
                "I2C":0x0300,
                "PWM":0x0400,
                "ICU":0x0500,
                "CAN":0x0600,
                "SER":0x0700,
                "DAC":0x0800,
                "LED":0x0900,
                "BTN":0x0A00
            }

            vcls = {
               "SPI":["MOSI","MISO","SCLK"],
                "I2C":["SDA","SCL"],
                "SER":["RX","TX"],
                "CAN":["CANRX","CANTX"]
            }
            prphs = {
                "SERIAL":0x700,
                "SPI":0x0200,
                "I2C":0x0300,
                "ADC":0x0100,
                "PWMD":0x0400,
                "ICUD":0x0500,
                "CAN":0x0600,
                "SD":0x0C00,
                "RTC":0x2000
            }

            # build dictionary with all valid pin names and prph names
            self.allnames = {}
            for k,v in classes.items():
                if k in vcls:
                    lst =vcls[k]
                    for x in range(0,128):
                        kname = lst[x%len(lst)]+str(x//len(lst))
                        kvalue = classes[k]+x
                        if kname in self.names:
                            self.allnames[kname]=kvalue
                else:
                    for x in range(0,128):
                        kname = k+str(x)
                        kvalue = classes[k]+x
                        if kname in self.names:
                            self.allnames[kname]=kvalue

            for k,v in prphs.items():
                for x in range(0,32):
                    kname = k+str(x)
                    kvalue = v+x
                    if kname in self.names:
                        self.allnames[kname]=kvalue
        except Exception as e:
            raise e

    def __get_specs(self):
        #TODO: additional_pins are not yet loaded py port.yml
        portfile = fs.path(self.path,"port.yml")
        if fs.exists(portfile):
            tmpl = fs.get_yaml(portfile)
            return tmpl["defines"],tmpl["peripherals"],tmpl["pinout"]

        # failsafe on port.def
        portfile = fs.path(self.path,"port","port.def")

        with open(portfile,"r") as ff:
            lines = ff.readlines()

        mth_list = re.compile('////(.*): (.*)')
        mth_pin = re.compile('\s*/\*\s*([DA0-9]*)\s.*\*/\s*MAKE_PIN\(')
        mth_cls = re.compile('.*MAKE_PIN_CLASS\(([0-9]*)\s*,')
        mth_header = re.compile('.*\sconst\s*_(.*)class\[\]\s*STORED')

        names = {
            "SPI":["MOSI","MISO","SCLK"],
            "I2C":["SDA","SCL"],
            "SER":["RX","TX"],
            "CAN":["CANRX","CANTX"],
            "PWM":["PWM"],
            "ICU":["ICU"],
            "ADC":["A"],
            "DAC":["DAC"],
        }

        vpins = {}
        vnames = {}
        vlayout = []
        vprph = []
        cdefs = []

        cfun = None
        clsc = 0
        npin = 0
        additional_pins = set()
        for line in lines:
            mth = mth_list.match(line)
            if mth:
                if mth.group(1)=="LAYOUT":
                    vlayout = mth.group(2).strip().split(" ")
                elif mth.group(1)=="PERIPHERALS":
                    vprph = mth.group(2).strip().split(" ")
                elif mth.group(1)=="CDEFINES":
                    cdefs.extend(mth.group(2).strip().split(" "))
                elif mth.group(1)=="EXTPINS":
                    for pname in mth.group(2).strip().split(" "):
                        additional_pins.add(pname)
                continue
            mth = mth_pin.match(line)
            if mth:
                #print("matched p",line)
                pname = mth.group(1)
                pidx = npin
                if pidx not in vpins:
                    vpins[pidx] = {
                        "name":pname,
                        "idx":pidx,
                        "fx":{}
                    }
                npin+=1
            else:
                mth = mth_header.match(line)
                if mth:
                    #print("matched h",line)
                    cfun = mth.group(1).upper()
                    clsc = 0
                else:
                    mth = mth_cls.match(line)
                    if mth:
                        #print("matched c",line)
                        pidx = int(mth.group(1))
                        pin = vpins[pidx]
                        if cfun=="DIGITAL":
                            continue
                        if cfun=="ANALOG":
                            cfun="ADC"

                        if cfun in ["LED","BTN"]:
                            vnames[cfun+str(clsc)]=pidx
                        elif cfun not in pin["fx"]:
                            lst = names[cfun]
                            if len(lst)>1:
                                pin["fx"][lst[clsc%len(lst)]]=lst[clsc%len(lst)]+str(clsc//len(lst))
                            else:
                                pin["fx"][cfun]=lst[0]+str(clsc)
                        clsc+=1

        #import pprint
        import collections

        #pp = pprint.PrettyPrinter(indent=4)

        if additional_pins:
            for pin in additional_pins:
                idx = int(pin[1:])
                vpins[idx]={
                    "idx":idx,
                    "name":pin,
                    "fx":{}  #all digitals
                }
        pinout = collections.OrderedDict()
        lpins = [v for k,v in vpins.items()]
        lpins.sort(key= lambda x: x["idx"])

        for lpin in lpins:
            pinout[lpin["name"]]=lpin["fx"]

        for vname in vnames:
            pinout[vname]=vpins[vnames[vname]]["fx"]

        defines = {
            "BOARD": self.target,
            "LAYOUT": vlayout,
            "CDEFS": cdefs
        }
        return (defines,vprph,pinout)

class Board(Device):
    def __init__(self,info={},dev={}):
        super().__init__(info,dev)







