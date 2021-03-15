from .base import *
from .fs import *
from .cfg import *
from .pygtrie import *

__all__ = ["tools"]



class Tools():
    def __init__(self):
        self.tools = {}
        self.installed = {}

    def init(self):
        #register platform tools
        if env.is_windows():
            self.tools["stty"]="mode"
        elif env.is_linux():
            self.tools["stty"]="/bin/stty -F"
        else:
            self.tools["stty"]="/bin/stty -f"

        for tooldir in fs.dirs(env.sys):
            self.add_tool(tooldir)

        for tooldir in fs.dirs(fs.path(env.dist,"sys")):
            self.add_tool(tooldir)

        ifile = fs.path(env.dist,"installed.json")
        self.installed = fs.get_json(ifile)

    def get_package(self,fullname):
        return env.repo["packs"][env.repo["byname"][fullname]]

    def get_packages_by_tag(self,tag):
        idx = env.repo["bytag"][tag]
        res = set()
        for i in idx:
            pack = env.repo["packs"][i]
            if pack.get("sys") and pack.get("sys")!=env.platform:
                # skip other platforms
                continue
            res.add(pack["fullname"])
        return sorted(list(res))

    def get_package_deps(self,fullname):
        try:
            pack = self.get_package(fullname)
        except:
            pack = {}
        res = []
        for dep in pack.get("deps",[]):
            res.extend(self.get_packages_by_tag(dep))
        res = sorted(list(set(res)))
        return res

    def has_all_deps(self,fullname):
        deps = self.get_package_deps(fullname)
        for fname in deps:
            if fname not in self.installed:
                return False
        return True

    def get_pack_info(self,packdir):
        pfiles = [fs.path(packdir,"z.yml"), fs.path(packdir,"package.json")]
        for pfile in pfiles:
            if fs.exists(pfile):
                pkg = fs.get_yaml_or_json(pfile)
                return pkg
        return None


    def add_tool(self,tooldir):
        if fs.basename(tooldir) in ["browser","newbrowser","newpython"]:
            # ignore some sys packages
            return
        try:
            pkg = self.get_pack_info(tooldir)
            if pkg is None:
                warning("Can't load tool package",tooldir)
                return
            else:
                fullname = pkg["fullname"]
                toolname = pkg.get("tool")
                pkg = pkg["sys"]
        except Exception as e:
            warning("Can't load tool",tooldir,e)
            return
        if toolname:
            self.tools[toolname]={}
            addto = self.tools[toolname]
        else:
            addto = self.tools
        if isinstance(pkg,dict):
            for k,v in pkg.items():
                addto[k]=fs.path(env.sys,tooldir,v)
        elif isinstance(pkg,list) or isinstance(pkg,tuple):
            for k,v in pkg:
                addto[k]=fs.path(env.sys,tooldir,v)
        else:
            warning("Can't load tool info",tooldir,err=True)
        #print(self.tools)

    def get_tool_dir(self,toolname):
        for tooldir in fs.dirs(env.sys):
            if fs.basename(tooldir)==toolname:
                return tooldir
        for tooldir in fs.dirs(fs.path(env.dist,"sys")):
            if fs.basename(tooldir)==toolname:
                return tooldir
        return None

    def __getattr__(self,attr):
        if attr in self.tools:
            return self.tools[attr]
        raise AttributeError

    def __getitem__(self,attr):
        if attr in self.tools:
            return self.tools[attr]
        raise KeyError

    def get_vm(self,vmuid,version,chipid,target):
        vmpath = fs.path(env.vms,target,chipid)
        vmfs = fs.glob(vmpath,"*.vm")
        vm = None
        for vmf in vmfs:
            vmm = fs.basename(vmf)
            if vmm.startswith(vmuid+"_"+version+"_"):
                vm=vmf
        return vm

    def get_vm_by_uid(self,vmuid):
        #for root,dirnames,files in os.walk(fs.path(env.vms)):
        for target in fs.dirs(env.vms):
            for chid in fs.dirs(fs.path(env.vms,target)):
                for ff in fs.files(fs.path(env.vms,target,chid)):
                    path_splitted = ff.split('/')
                    ff_ = fs.basename(ff)
                    if ff_.startswith(vmuid+"_"):
                        return fs.path(ff)
        return None

    def get_vms(self,target,chipid=None,full_info=False):
        vms = {}
        targetpath = fs.path(env.vms,target)
        if not fs.exists(targetpath):
            return vms
        for chid in fs.dirs(targetpath):
            chid=fs.basename(chid)
            if chipid and chipid!=chid:
                continue
            vmfs = fs.glob(fs.path(targetpath,chid),"*.vm")
            for vmf in vmfs:
                vmbf = fs.basename(vmf)
                rpos = vmbf.rfind("_") #rtos
                hpos = vmbf.rfind("_",0,rpos-1) #hash
                vpos = vmbf.rfind("_",0,hpos-1) #version
                vmrtos = vmbf[rpos+1:-3]
                vmhash = vmbf[hpos+1:rpos]
                vmversion = vmbf[vpos+1:hpos]
                vmuid = vmbf[0:vpos] #TODO: add check
                if full_info:
                    vms[vmuid]=(vmf,vmversion,vmrtos,vmhash)
                else:
                    vms[vmuid]=vmf
        return vms

    def get_vm_by_prefix(self,vmuid):
        #for root,dirnames,files in os.walk(fs.path(env.vms)):
        res = []
        for target in fs.dirs(env.vms):
            for chid in fs.dirs(fs.path(env.vms,target)):
                for ff in fs.files(fs.path(env.vms,target,chid)):
                    path_splitted = ff.split('/')
                    ff_ = fs.basename(ff)
                    if ff_.startswith(vmuid):
                        res.append(fs.path(ff))
        return res

    def _parse_order(self,path):
        try:
            order = fs.readfile(fs.path(path,"order.txt"))
            debug("Can't open order.txt at",path)
        except:
            return []
        lines = order.split("\n")
        stack = []
        rs = []
        for line in lines:
            line = line.strip()
            if not line or len(line)<4 or line.startswith(";"):
                continue
            pos = line.count("#")
            if pos>0:
                label = line[pos:]
                while (len(stack)>=(pos)): stack.pop()
                stack.append(label)
            else:
                try:
                    ex = {
                        "tag":list(stack),
                        "name":line.replace("_"," "),
                        "path":fs.path(path,line),
                        "desc":fs.readfile(fs.path(path,line,"project.md")),
                        "code":fs.readfile(fs.path(path,line,"main.py")),
                    }
                    rs.append(ex)
                except:
                    pass
        return rs


    def _get_examples(self,path):
        return self._parse_order(path)

    def get_examples(self):
        exs = {}
        exr = []
        srcs = [(fs.path(env.stdlib,"examples"),"core.zerynth.stdlib")]
        repos = fs.dirs(env.libs)
        if "official" in repos: #put official on top
            repos.remove("official")
            repos = ["official"]+repos
        for repo in repos:
            nms = fs.dirs(repo)
            for nm in nms:
                libs = fs.dirs(nm)
                for lib in libs:
                    srcs.append((fs.path(lib,"examples"),"lib."+fs.basename(nm)+"."+fs.basename(lib)))
        for exlib,lib in srcs:
            if fs.exists(exlib):
                ee = self._get_examples(exlib)
                for eee in ee:
                    eee["lib"]=lib
                exr.extend(ee)
        return exr

    def get_devices(self):
        bdirs = fs.dirs(env.devices)
        for bdir in bdirs:
            try:
                pkg = self.get_pack_info(bdir)
                if pkg is None:
                    continue
                bj = fs.get_json(fs.path(bdir,"device.json"))
                bj["path"] = bdir
                bj["deps"] = self.get_package_deps(pkg["fullname"])
                bj["has_all_deps"] = self.has_all_deps(pkg["fullname"])
                bj["fullname"] = pkg["fullname"]
                yield bj
            except Exception as e:
                warning(e)
        #load custom devices
        cdirs = fs.dirs(env.cvm)
        for cdir in cdirs:
            if not fs.exists(fs.path(cdir,"active")):
                #not compiled yet, skip
                continue
            try:
                pkg = self.get_pack_info(bdir)
                if pkg is None:
                    continue
                bj = fs.get_json(fs.path(cdir,"device.json"))
                bj["path"] = cdir
                bj["deps"] = self.get_package_deps(pkg["fullname"])
                bj["has_all_deps"] = self.has_all_deps(pkg["fullname"])
                bj["fullname"] = pkg["fullname"]
                yield bj
            except Exception as e:
                warning(e)

    def get_specs(self,specs):
        options = {}
        for spec in specs:
            pc = spec.find(":")
            if pc<0:
                fatal("invalid spec format. Give key:value")
            thespec = spec[pc+1:]
            if thespec=="null":
                thespec=None
            options[spec[:pc]]=thespec
        return options

    def get_target(self,target,options={}):
        import devices
        _dsc = devices.Discover()
        return _dsc.get_target(target,options)

    def get_modules(self):
        res = {}
        # libraries
        rdirs = fs.dirs(env.libs)
        for r in rdirs:
            repo = fs.basename(r)
            nsdirs = fs.dirs(r)
            for ns in nsdirs:
                namespace = fs.basename(ns)
                lbdirs = fs.dirs(ns)
                for l in lbdirs:
                    lib = fs.basename(l)
                    if repo=="official":
                        if namespace=="zerynth":
                            module = lib
                        else:
                            module = namespace+"."+lib
                    else:
                        module = repo+"."+namespace+"."+lib
                    imports = []
                    for f in fs.files(l):
                        fl = fs.basename(f)
                        if fl.endswith(".py") and fl!="main.py":
                            imports.append(fl[0:-3])
                    res[module]=imports
        return res

    def get_vhal(self):
        vhal = {}
        arch_dirs = fs.dirs(env.vhal)
        for ad in arch_dirs:
            fmdirs = fs.dirs(ad)
            for fm in fmdirs:
                vhal_file = fs.path(fm,"vhal.json")
                if fs.exists(vhal_file):
                    vj = fs.get_json(vhal_file)
                    vhal.update(vj)
        return vhal

    def disk_usage(self):
        bytes = fs.dir_size(env.home)
        return bytes





#fs.set_json(rj["data"], fs.path(vmpath,uid+"_"+version+"_"+rj["data"]["hash_features"]+"_"+rj["data"]["rtos"]+".vm"))


tools = Tools()


# add_init(tools.init)
