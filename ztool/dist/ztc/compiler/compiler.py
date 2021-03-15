from base import *
from devices import Discover

import re
import uuid
import ast
import struct
import base64
import hashlib
import os
import os.path

from compiler.env import Env
from compiler.astprep import AstPreprocessor
from compiler.astwalker import AstWalker
from compiler.codecache import CodeCache
from compiler.opcode import genByteCodeMap
from compiler.exceptions import *
from compiler.code import CodeRepr
from compiler import cc
#toolbelt.viper_import("compiler.astwalker")
# from compiler.astwalker import astdump, AstWalker
# from compiler.utils.code import CodeRepr
# from compiler.utils.env import Env
# from compiler.utils.exceptions import *
# from compiler.u
# from compiler import cc
# from compiler import _board_family
# import viper.viperlogger

# logger = viper.viperlogger.logger(__name__,"compiler")



class Compiler():

    PREPROCESS = 0
    COMPILE = 1

    def __init__(self, inputfile, target, syspath=[],cdefines=[],mode=COMPILE,localmods={},tempdir=None):
        # build syspath
        self.tempdir=tempdir or env.tmp
        self.syspath = []
        # add current mainfile dir
        self.curpath = fs.apath(fs.dirname(inputfile))
        self.syspath.append(self.curpath)
        # then add provided syspath (for library trees)
        self.syspath.extend(syspath)
        # then add standard syspath
        self.syspath.append(env.stdlib)
        # then add official libraries
        self.syspath.append(fs.path(env.libs,"official"))
        # then add all repos
        self.syspath.append(env.libs)
        # then add a shortcut to all official zerynth libraries
        self.syspath.append(fs.path(env.libs,"official","zerynth"))
        # then add a shortcut to the target
        self.syspath.append(fs.path(env.devices,target))
        #for zd in fs.dirs(fs.path(env.libs,"official","zerynth")):
        #    self.syspath.append(zd)
        # ZDM provisioning check

    


        self.file_options = {}
        self.localmods = localmods
        self.mainfile = inputfile
        self.phase = 0
        self.env = Env()
        self.vmsym = []
        self.target = target
        self.prepcfiles = set()
        self.prepdefines = {}
        self.has_options = False
        discover = Discover()
        if self.target!="no_device": ## no_device is passed only when no code generation is needed!
            if self.target not in discover.get_targets():
                fatal("Target",target,"does not exist")
            self.board = discover.get_target(target)
            self.board.load_specs()
            if not self.board.load_family():
                fatal("Can't load family parameters for",target)
            self.parseNatives()
            self.builtins_module = "__builtins__"
            self.zdm_provisioning()


            self.prepdefines.update(self.board.defines)
            if "CDEFS" not in self.prepdefines:
                self.prepdefines["CDEFS"] = []
            if "CFG" not in self.prepdefines:
                self.prepdefines["CFG"] = {}
            self.prepdefines["CDEFS"].extend(list(cdefines))

            self.allnames = {}
            self.dcz_check()
            self.allnames.update(self.board.allnames)

            self.astp = AstPreprocessor(self.allnames,self.board.pinmap,self.prepdefines,self.prepcfiles)
            self.scopes = {}
            self.moduletable = {}
            self.maindir=None
            self.resources={}
            self.cncache = CodeCache(self.tempdir)
            self.scratch()
            self.mode=mode
            genByteCodeMap()

    def  zdm_provisioning(self):
        dcz_file = fs.path(self.curpath,"dcz.yml")
        zdm_provisioning_file = fs.path(self.curpath,"zdevice.json")
        zdm_device_dcz = fs.path(env.devices,self.target,"dcz","zdm","dcz.yml")
        if fs.exists(zdm_provisioning_file):
            info("ZDM provisioning file detected at",zdm_provisioning_file)
            if fs.exists(dcz_file):
                info("DCZ file already present")
            else:
                if fs.exists(zdm_device_dcz):
                    # target supports ZDM DCZ provisioning
                    info("Target supports ZDM DCZ provisioning, copying configuration...")
                    fs.copyfile(zdm_device_dcz,dcz_file)
                else:
                    warning("Target does not support ZDM DCZ provisioning, using resource files...")

    def dcz_check(self):
        dcz_file = fs.path(self.curpath,"dcz.yml")
        if fs.exists(dcz_file):
            dczfile = fs.get_yaml(dcz_file,failsafe=True)
            if not dczfile.get("disabled",False):
                info("DCZ enabled, adding ZERYNTH_USE_DCZ flag")
                self.prepdefines["CDEFS"].append("ZERYNTH_USE_DCZ")
                mapping = dczfile.get("dcz",{}).get("mapping",[])
                maplen = len(mapping)
                if maplen<8:
                    mapping.extend([0]*(8-maplen))
                for i,addr in enumerate(mapping):
                    info("DCZ enabled, adding ZERYNTH_DCZ_MAPPING_"+str(i)+" flag")
                    # self.prepdefines["CDEFS"].append("ZERYNTH_DCZ_MAPPING_"+str(i)+"="+hex(addr))
                    self.allnames["ZERYNTH_DCZ_MAPPING_"+str(i)]=addr
                self.allnames["ZERYNTH_DCZ_MAPPINGS"]=maplen



            else:
                info("DCZ disabled")

    def scratch(self):
        self.codeobjs = []
        self.codemap = {}
        self.modules = {}
        self.cnatives = {}
        self.cdefines = set()
        self.cincpaths = set()
        self.cfiles = set()
        self.reachable_names = set()
        self.reachable_modules = set()
        self.bltinfo = {}
        self.stripped_modules = set()
        self.stripped = set()
        self.maindir=None
        self.resources={}

    def newPhase(self):
        self.codeobjs = []
        self.modules = {}
        self.bltinfo = {}
        self.stripped = set()
        self.lastbuiltincode = 1


    def shouldGenerateCodeFor(self,name,module):
        return True
        # if self.phase == 0:
        #     return True
        # fullname = module+"."+name
        # return fullname in self.reachable_names

    def shouldGenerateModule(self,name):
        if self.phase <= 2:
            return True
        return name not in self.stripped_modules


    def getBuiltinCoding(self,name):
        # nfo = self.bltinfo[name]
        # # code(8)|vararg(1)|kwargs(3)|args(4)
        # return (nfo[0]<<8)|((nfo[1][2]<<7)|(nfo[1][1]<<4)|(nfo[1][0]))
        bltmod = self.modules[self.builtins_module]
        #print(bltmod.scope.locals)
        return bltmod.scope.locals.index(name)

    def saveBuiltinInfo(self,name,code,args):
        self.bltinfo[name] = (code,args)
        self.lastbuiltincode = code

    def saveBuiltinNameInfo(self,name):
        self.lastbuiltincode+=1
        self.bltinfo[name] = (self.lastbuiltincode,(0,0,0))

    def putModuleCode(self,name,code):
        self.modules[name]=code

    def getModuleCode(self,name):
        return self.modules[name]

    def pushCodeHook(self, code):
        self.codeobjs.append(code)

    def getEnvHook(self):
        #tenv = self.env
        self.env = Env()
        #self.env.transferHyperGlobals(tenv)
        return self.env

    def numCodeHook(self):
        return len(self.codeobjs)

    def importHook(self,name,line,filename):
        #logger.info("   Importing module: %s",name)
        self.compileModule(name,line,filename)

    def addResource(self,filename):
        if os.path.exists(os.path.join(self.maindir,filename)):
            ret = len(self.resources)
            self.resources[filename]=ret
            return ret
        return -1

    def addCConf(self,afile):
        cj = fs.get_json(afile,strict=False)
        for k,v in cj.items():
            self.cdefines.add(k+"="+str(v)) #TODO: add support for strings

    def addCBuild(self,afile):
        warning("Following CBuild",afile)
        cj = fs.get_json(afile,strict=False)
        dname = fs.dirname(afile)
        for k,v in cj.items():
            warning(k,v,self.cdefines,self.prepdefines)
            if k in self.cdefines or k in self.prepdefines.get("CDEFS",[]): # if macro is defined, add corresponding code
                for x in v["src"]:
                    self.cfiles.add(fs.apath(fs.path(dname,x)))
                for x in v["inc"]:
                    self.cincpaths.add(fs.apath(fs.path(dname,x)))
                    warning("added",fs.apath(fs.path(dname,x)))
                for x in v["defs"]:
                    self.cdefines.add(k+"="+str(x)) #TODO: add support for strings


    def addCThings(self,natives,files,vbls,opts,fbase=""):
        # print("addCThings:",natives,files,vbls,opts,fbase)
        for file in files:
            #file.replace("/",os.path.sep);
            if "#csrc" in file:
                #absolute path given, point to stdlib
                file = fs.path(env.stdlib,file.replace(fbase,"").replace("#","")[1:])
                # warning(file, file.replace("fbase","")[1:])

            if file.endswith("*"):
                pt = fs.dirname(file)
                afile = fs.glob(pt,"*.c")
            else:
                afile = [file.replace("\\","/")]
            if afile and afile[0].endswith("cbuild.json"):
                self.addCBuild(afile[0])
            else:
                self.cfiles.update(afile)
        for vbl in vbls:
            # if vbl.startswith("VBL_"):
            #     vblf = fs.path(env.stdlib,"__common","vbl",vbl.lower()+".c")
            #     if os.path.exists(vblf):
            #         self.cfiles.add(vblf)
            #         self.cincpaths.add(os.path.realpath(os.path.join(vconf.envdirs["vm"],"common","vbl")))
            #     else:
            #         raise CNativeNotFound(0,0,vblf)
            if vbl.startswith("VHAL_"):
                self.cdefines.add(vbl)
                #print(self.board.family)
                lookup = self.board.family[self.board.family_name]
                if vbl in lookup["vhal"]:
                    for x in lookup["vhal"][vbl]["src"]:
                        self.cfiles.add(os.path.realpath(os.path.join(env.vhal,lookup["path"],x)))
                    for x in lookup["vhal"][vbl]["inc"]:
                        self.cincpaths.add(os.path.realpath(os.path.join(env.vhal,lookup["path"],x)))
                    self.cdefines.update(lookup["vhal"][vbl]["defs"])
            else:
                self.cdefines.add(vbl)
        for opt in opts:
            if opt.startswith("-I#"):
                self.cincpaths.add(os.path.realpath(fs.path(env.stdlib,opt[3:])))
            elif opt.startswith("-I@"):
                self.cincpaths.add(os.path.realpath(fs.path(env.official_libs,opt[3:])))
            elif opt.startswith("-I"):
                # -I.../mylibh can be used instead of -Imylibh to make compilation work when not called from
                # project folder so that ... can be replaced with project absolute path
                # to make it work also when called from project folder (where fbase is ''),
                # leading slash shall be stripped otherwise /mylibh would be obtained
                incpath = os.path.realpath(opt[2:].replace("...",fbase))
                if not fbase and incpath.startswith('/'):
                    incpath = incpath[1:]
                self.cincpaths.add(incpath)
        if isinstance(natives,str):
            if natives not in self.cnatives:
                self.cnatives[natives]=len(self.cnatives)
        else:
            for x in natives:
                if x not in self.cnatives:
                    self.cnatives[x]=len(self.cnatives)

    def decodeCNative(self,cnative):
        if cnative in self.cnatives:
            return self.cnatives[cnative]
        else:
            return -1

    def searchModule(self,modname):
        modfld = modname.split(".")
        modfile = fs.path(*modfld)+".py"
        # # search in localmods
        # if modfld[0]=="local":
        #     # local modules
        # else if modname in self.localmods:
        #     # local modules

        # search syspath for modname
        for path in self.syspath:
            modpath = fs.path(path,modfile)
            info("Searching for",modpath)
            if fs.exists(modpath):
                modfile=modpath
                break
        else: #TODO: search for module to be translated (example: local.namespace.module --> projdir)
            return None
        return modpath

    def readfile(self,file,module=None):
        # load file options if present
        if file==self.mainfile:
            optfile = fs.path(fs.dirname(file),"project.yml")
        else:
            optfile = fs.path(fs.dirname(file),fs.basename(file).replace(".py",".yml"))
        if fs.exists(optfile):
            try:
                opts = fs.get_yaml(optfile)
            except Exception as e:
                raise CSyntaxError(0,0,optfile,"Something wrong in config file "+optfile)
            try:
                if "config" in opts:
                    for opt,value in opts["config"].items():
                        if value is not None:  # null values disable the macro
                            if value is True:  # boolean must be converted to int
                                self.prepdefines["CFG"][opt]=1
                            elif value is False:
                                self.prepdefines["CFG"][opt]=0
                            else:
                                self.prepdefines["CFG"][opt]=value
                if "options" in opts:
                    self.has_options = True
            except Exception as e:
                raise CSyntaxError(0,0,optfile,"Something wrong in config file format "+optfile+" :: "+str(e))
            if module:
                self.file_options[module]={
                    "py":file,
                    "yml":optfile,
                    "cfg":opts
                }

        # add CDEFS in board port.def to CFG options
        for opt in self.prepdefines["CDEFS"]:
            self.prepdefines["CFG"][opt]=1
        self.prepdefines["CFG"]["TARGET"]=self.prepdefines["BOARD"]

        preg = re.compile("\s*(#+-)(if|else|endif|warning|error)\s*(!{0,1}[a-zA-Z0-9_]*)(?:\s+(>=|<=|==|!=|>|<)\s+([A-Za-z0-9_ ]+)){0,1}")
        stack = []
        modprg = fs.readfile(file)
        lines = modprg.split("\n")
        result = []
        keepline = True
        for nline,line in enumerate(lines):
            mth = preg.match(line)
            if mth:
                lvl = len(mth.group(1))-2  # level of nesting strating from 0
                op = mth.group(2)
                cmacro = mth.group(3)
                negated=False
                if cmacro.startswith("!"):
                    cmacro = cmacro[1:]
                    negated=True
                cop = mth.group(4)
                cval = mth.group(5)
                vmacro = self.prepdefines.get("CFG",{}).get(cmacro,None)
                #print("Matched:",lvl,op,cmacro,cset,stack,keepline)
                #check lvl
                if op=="if":
                    if len(stack)!=lvl:
                        raise CSyntaxError(nline,0,file,"Bad preprocessor nesting! Expected "+str(len(stack))+" but found "+str(lvl) )
                    if not cmacro:
                        raise CSyntaxError(nline,0,file,"Bad preprocessor: missing -if argument")

                    if cop:
                        if negated:
                            raise CSyntaxError(nline,0,file,"Bad preprocessor: can't use (!) operator with values")
                        #evaluate expr
                        try:
                            cval=int(cval)
                        except:
                            #not an integer
                            try:
                                cval=float(cval)
                            except:
                                #not a float, failsafe to str
                                pass
                        try:
                            if cop=="==":
                                kl = vmacro==cval
                            elif cop==">=":
                                kl = vmacro>=cval
                            elif cop==">":
                                kl = vmacro>cval
                            elif cop=="<=":
                                kl = vmacro<=cval
                            elif cop=="<":
                                kl = vmacro<cval
                            elif cop=="!=":
                                kl = vmacro!=cval
                        except:
                            #in case of error, failsafe to false (can happen of typeerror)
                            kl = False
                    else:
                        #no expr
                        if not negated:
                            kl = vmacro is not None
                        else:
                            kl = vmacro is None

                    kl = all(stack) and kl
                    keepline = kl
                    stack.append(kl)
                    # debug
                    info("PREP:",cmacro,"=",vmacro,"(",keepline,")","[ if",lvl+1,"]","@",nline+1)
                elif op=="else":
                    if len(stack)!=lvl+1:
                        raise CSyntaxError(nline,0,file,"Bad preprocessor else! Probably missing some endif")
                    if all(stack[:-1]):
                        keepline=not stack[-1]
                        stack[-1]=keepline
                        info("PREP:","(",keepline,")","[ else",lvl+1,"]","@",nline+1)

                elif op=="endif":
                    ## endif
                    if len(stack)!=lvl+1:
                        raise CSyntaxError(nline,0,file,"Bad preprocessor endif! Check nesting")
                    stack.pop()
                    keepline = True if not stack else stack[-1]
                elif op=="warning":
                    # warning
                    if keepline:
                        warning("PREPROCESSOR WARNING:",cval,"@",nline+1)
                else:
                    # error
                    if keepline:
                        fatal("PREPROCESSOR ERROR:",cval,"@",nline+1)

            if keepline:
                result.append(line)
            else:
                result.append("# prep removed # "+line)

        modprog = "\n".join(result)
        # log(modprog)
        # if "zerynth2" not in file:
        #     log(modprog)
        debug(modprog)
        return modprog





    def find_imports(self):
        ## Preload builtins to get all __defines
        astp = AstPreprocessor({},{},self.prepdefines,self.prepcfiles,just_imports=True)
        modprg = self.readfile(self.mainfile)
        tree = ast.parse(modprg)
        astp.visit(tree)
        res = {}
        ures = set()
        for modname in astp.modules:
            flp = self.searchModule(modname)
            if not flp:
                ures.add(modname)
            else:
                res[flp]=modname
        return (res,ures)

    def compileModule(self,name,line=0,filename=0):
        if name==self.mainfile:
            mfile = name
            name = "__main__"
            self.maindir = fs.dirname(mfile)
        else:
            mfile = self.searchModule(name)

        if mfile!=None:
            info("Compiling module:",name,"@",mfile)
            modprg = self.readfile(mfile,name)
            if name!=self.builtins_module:
                # add builtins to each module
                modprg = "import "+self.builtins_module+"\n"+modprg

            try:
                tree = ast.parse(modprg)
            except SyntaxError as e:
                raise CSyntaxError(e.lineno,e.offset,mfile,str(e))

            self.astp.curpath = fs.dirname(mfile)
            self.astp.filename = mfile
            tree = self.astp.visit(tree)
            if self.phase==0 and name!="__builtins__":
                #print("\n\n## Syntax Tree ##\n")
                #print(astdump(tree))
                #TODO: print syntax if requested
                pass

            self.astp.clean(tree)
            mc = AstWalker(modprg,self,mfile,name,None if self.phase==0 else self.scopes)
            mc.visit(tree)
            self.scopes.update(mc.env.get_scopedir())
            self.moduletable[mfile]=name
        else:
            raise CModuleNotFound(line,0,filename,name)

    def parse_config(self):
        ## Preload builtins to get all __defines
        mf = self.searchModule(self.builtins_module)
        if mf is None:
            fatal("Can't find builtins module")
        modprg = self.readfile(mf,self.builtins_module)
        tree = ast.parse(modprg)
        self.astp.visit(tree)

        self.newPhase()
        self.compileModule(self.mainfile)
        return self.file_options,self.prepdefines


    def compile(self):
        ## Preload builtins to get all __defines
        mf = self.searchModule(self.builtins_module)
        if mf is None:
            fatal("Can't find builtins module")
        modprg = self.readfile(mf,self.builtins_module)
        tree = ast.parse(modprg)
        self.astp.visit(tree)

        if self.mode==Compiler.PREPROCESS:
            # preprocessing info
            return

        info("#"*10,"STEP",self.phase,"- first pass")
        self.newPhase()
        self.compileModule(self.mainfile)
        objs_at_0 = len(self.codeobjs)
        mods_at_0 = len(self.modules)



        self.scratch()
        info("#"*10,"STEP",self.phase,"- second pass")
        self.phase = 1
        self.newPhase()
        self.compileModule(self.mainfile)
        objs_at_0 = len(self.codeobjs)
        mods_at_0 = len(self.modules)


        # map, attributes, modules, builtins, locals = self.optimizeNames()

        # print(map)
        # print(attributes)
        # print(modules)
        # print(builtins)
        # print(locals)

        #print(self.bltinfo)

        # #Phase 1: compute reachable code
        # logger.info("PHASE 2: compute reachability (not implemented yet)")
        # self.phase = 1
        # #self.computeReachableCode()


        # #Phase 2: compile stripped code
        # logger.info("PHASE 3: second pass compile")
        # self.phase = 2
        # self.newPhase()
        # self.compileModule(self.mainfile)
        # objs_at_2 = len(self.codeobjs)

        # for k,v in self.modules.items():
        #     if v.isJustStop():
        #         self.stripped_modules.add(k);

        # mods_at_2 = len(self.modules)

        # #print("\n   Stripped codeobjs:",objs_at_0-objs_at_2)
        # #print("   Stripped modules:",mods_at_0-mods_at_2)

        # #Phase 4: strip modules
        # logger.info("PHASE 4: third pass compile")
        # self.phase = 3
        # self.newPhase()
        # self.compileModule(self.mainfile)
        # mods_at_3 = len(self.modules)
        # objs_at_3 = len(self.codeobjs)

        # #print("\n   Stripped codeobjs:",objs_at_0-objs_at_3)
        # #print("   Stripped modules:",mods_at_0-mods_at_3)

        self.cfiles.update(self.prepcfiles)
        self.cfiles = fs.unique_paths(self.cfiles)
        ofiles = None

        if self.cfiles:

            info("#"*10,"STEP",self.phase,"- C code compilation")
            gccopts = dict(self.board.gccopts)
            if "CDEFS" in self.prepdefines:
                self.cdefines.update(self.prepdefines["CDEFS"])
            if fs.exists(fs.path(self.maindir,"cconf.json")):
                info("Adding global C configuration...")
                self.addCConf(fs.path(self.maindir,"cconf.json"),strict=False)


            gccopts["defs"].extend(self.cdefines)
            for k,v in self.prepdefines.get("CFG",{}).items():
                gccopts["defs"].append(k+"="+str(v))
            gccopts["inc"]=set(self.cincpaths)
            gccopts["inc"].add(fs.path(env.stdlib,"__cdefs"))
            gccopts["inc"].add(fs.path(env.stdlib,"__lang"))
            gccopts["inc"].add(fs.path(env.stdlib,"__common"))
            gccopts["inc"].add(fs.path(self.board.path,"port"))
            gccopts["inc"].add(fs.path(self.board.path,"port","config"))

            #TODO: add support for other than gcc
            gcc = cc.gcc(tools[self.board.cc],gccopts)

            ofilecnt = None
            self.cncache.set_target(self.maindir,self.board.target,self.cdefines)
            tmpdir = self.tempdir
            ofiles = {}
            for cfile in self.cfiles:
                if not fs.exists(cfile):
                    warning(cfile,"does not exist")
                hfile = fs.path(tmpdir,self.target+"_"+self.cncache.hashme(cfile)+"_"+fs.basename(cfile).replace(".c","")+".o")
                ofiles[cfile]=hfile
                if cfile.endswith(".rvo"):
                    #handle rvo files
                    info("Including precompiled binary",cfile)
                    fs.copyfile(cfile,hfile)
                elif cfile.endswith(".c"):
                    #handle c files
                    cnr = self.cncache.has_object(cfile)
                    if cnr:
                        #in cache!
                        info("Getting",cfile,"from cache")
                        fs.copyfile(cnr,hfile)
                    else:
                        #not in cache -_-
                        info("Compiling",cfile)
                        cheaders = gcc.get_headers([cfile])
                        #print("HEADERS",cheaders)
                        ret,wrn,err,cout = gcc.compile([cfile],o=hfile)
                        debug(cout)
                        if ret==0:
                            if wrn:
                                for k,v in wrn.items():
                                    for vv in v:
                                        warning(k,"=> line",vv["line"],vv["msg"])
                            self.cncache.add_object(cfile,hfile,cheaders[cfile])
                        else:
                            for k,v in err.items():
                                for vv in v:
                                    error(k,"=> line",vv["line"],vv["msg"])
                            #TODO: fix exception
                            raise CNativeError(0,0,cfile,"---")
            info("Linking...")
            obcfile = fs.path(tmpdir,"zerynth.vco")
            ofile = fs.path(tmpdir,"zerynth.rlo")
            #ofiles = [os.path.join(tmpdir,get_filename(c).replace(".c",".o")) for c in self.cfiles if "vhal_" not in get_filename(c) and get_filename(c).endswith(".c")]
            rvofiles=[]
            vhalfiles=[]
            obcfiles=[]
            for cfile,hfile in ofiles.items():
                if cfile.endswith(".rvo"):
                    rvofiles.append(hfile)
                elif fs.basename(cfile).startswith("vhal_"):
                    vhalfiles.append(hfile)
                elif cfile.endswith(".c"):
                    obcfiles.append(hfile)

            #print(obcfiles,vhalfiles,rvofiles)
            # linking non vhal, non rvo
            if obcfiles:
                ret,output = gcc.link(obcfiles,{},reloc=True,ofile=obcfile,libs=["m"])
                if ret!=0:
                    error("Linking Error:",output)
                    raise CNativeError(0,0,"","C Native Linking Error!")
                #save relocatable viper object
                fs.copyfile(obcfile,fs.path(tmpdir,"lastbuilt.rvo"))

            ofiles = []
            ofiles.extend(obcfiles)
            ofiles.extend(vhalfiles)
            ofiles.extend(rvofiles)
            ret,output = gcc.link(ofiles,{},reloc=True,ofile=ofile,libs=["m"])
            ##### IMPORTANT
            # When using reloc=True, gcc-ld can't find libraries with "-lxxx" switches.
            # The reason is not clear, still investigating.
            # However, passing the full path of the library with -L works...
            # gcc class automatically searches for libraries and selects the right ones, making them available as gcc.libxxx
            if ret!=0:
                error("Linking Error:",output);
                raise CNativeError(0,0,"","C Native Linking Error!")
            sym = gcc.symbol_table(ofile)
            syms = sym.symbols()
            #info("Linked symbols:")
            #for ss in syms:
            #    info("==>",ss)
            #warning("Undefined symbols!")
            undf = sym.getfrom(sym.undef)
            # undf = {k:v for k,v in undf.items() if k not in set(self.vmsym)}
            for uu in undf:
               debug("==>",uu)
            csym = frozenset(self.cnatives)
            if not(csym<=syms):
                error("The following @cnatives are missing:")
                for ss in csym-syms:
                    error(ss)
                raise CNativeError(0,0,"","some C natives are not defined!!")
            ofilecnt = fs.readfile(ofile,"b")
            # if len(undf)>0:
            #     error("The following symbols are undefined:")
            #     for ss in undf:
            #         error(ss)
            #     raise CNativeError(0,0,"","undefined symbols!")
        else:
            ofilecnt = bytearray()
            if self.cnatives:
                error("the following @cnatives are missing:")
                for ss in self.cnatives:
                    error(ss)
                raise CNativeError(0,0,"","some C natives are not defined!!")

        #Phase 4: generate binary repr and debug file
        self.phase = 4
        info("#"*10,"STEP",self.phase,"- generate binary")

        rt = self.generateBinary(ofilecnt,ofiles)
        return rt


    def generateResourceTable(self):
        head = bytearray()
        res = bytearray()
        headsize=0
        for name in self.resources:
            headsize+=4+4+4+len(os.path.split(name)[1])
            if headsize%4!=0:
                headsize+=4-headsize%4

        if headsize:
            head+=struct.pack("=I",headsize+4)
            headsize+=4

        for name in self.resources:
            bin = fs.readfile(fs.path(self.maindir,name),"b")
            rname = os.path.split(name)[1]
            head+=struct.pack("=I",len(rname))
            head+=struct.pack("=I",len(bin))
            head+=struct.pack("=I",headsize+len(res))
            head+=struct.pack("="+str(len(rname))+"s", rname.encode("latin1"))
            #pad head
            if len(rname)%4!=0:
                for x in range(4-len(rname)%4):
                    head+=struct.pack("=B",0)
            res+=bin
        #pad res
        if len(res)%4!=0:
            for x in range(4-len(res)%4):
                res+=struct.pack("=B",0)
        return head+res

    def generateBinary(self,ofile=None,ofiles=None):
        bin = {}
        self.env.buildExceptionTable()
        codereprs = []
        for co in self.codeobjs:
            co.resolveExceptions(self.env)
            cr = CodeRepr()
            cr.makeFromCode(co)
            codereprs.append(cr)

        # Generate Code Image
        objbuf = []
        buf = bytearray()
        lmap = {}
        for co in self.codeobjs:
            bcf = co.toBytes()
            objbuf.append(bcf)

        #Generate Header
        #Magic Number
        buf+= (struct.pack("=B", ord('G') )) #GGGD
        buf+= (struct.pack("=B", ord('G') )) #GGGD
        buf+= (struct.pack("=B", ord('G') )) #GGGD
        buf+= (struct.pack("=B", ord('D') )) #GGGD
        #Flags
        buf+= (struct.pack("=B", 0 ))
        #NModules
        buf+= (struct.pack("=B", len(self.modules) ))
        #Nobjs
        buf+= (struct.pack("=H", len(objbuf) ))

        #Exceptions
        etable,emtable,emtablelen = self.env.getBinaryExceptionTable()
        rtable = self.generateResourceTable()
        buf+=struct.pack("=H",len(etable))
        #Unused --> now is num of cnatives
        buf+=struct.pack("=H",len(self.cnatives))
        #ram_start
        buf+=struct.pack("=I",0)
        #data_start
        buf+=struct.pack("=I",0)
        #data_end
        buf+=struct.pack("=I",0)
        #data_bss
        buf+=struct.pack("=I",0)
        #hash: 16 bytes for md5
        buf+=struct.pack("=I",0)
        buf+=struct.pack("=I",0)
        buf+=struct.pack("=I",0)
        buf+=struct.pack("=I",0)
        #ts
        buf+=struct.pack("=I",0)
        #marker
        buf+=struct.pack("=I",0)
        #blen: bytecode size (filled by uplinker)
        buf+=struct.pack("=I",0)
        #vversion: VM version (filled by uplinker)
        buf+=struct.pack("=I",0)
        #bversion: sdk version (tool version used to compile the code. WARNING: can be different from the uplinker version -_-)
        buf+=struct.pack("=I",int32_version(env.var.version))
        #bcoptions
        buf+=struct.pack("=I",0)

        cobsz = 4*len(objbuf)+(len(buf)+4)+(len(etable)*8+emtablelen)+4*len(self.cnatives)

        #res_table
        if rtable:
            info("Resource table is at",len(buf),hex(len(buf)))
            buf+=struct.pack("=I",cobsz)
            cobsz+=len(rtable)
        else:
            buf+=struct.pack("=I",0)

        #CodeObjs table
        cobsztable = []
        pyobjtablestart = len(buf)
        for cob in objbuf:
            buf+=(struct.pack("=I", cobsz ))
            cobsztable.append(cobsz)
            cobsz+=len(cob)
        pyobjtableend = len(buf)

        #add space for c natives addresses
        for i in range(0,len(self.cnatives)):
            buf+=(struct.pack("=I", i ))

        #exception table
        etablestart = len(buf)
        for e in etable:
            buf+=struct.pack("=H",e[0]) #name
            buf+=struct.pack("=H",e[1]) #parent
            buf+=struct.pack("=I",e[2]) #msg offs
            #print("etable entry:",e[0],e[1],e[2])

        pckd=0
        for e in emtable:
            buf+=struct.pack("=H",e[0]) #len
            buf+=struct.pack("="+str(e[0])+"s", e[1].encode("latin1")) #str
            pckd+=2+e[0]
            ssz = (len(buf))%4
            if ssz:
                ssz=4-ssz
                while ssz>0:
                    buf+=struct.pack("=B",0) #pad
                    pckd+=1
                    ssz-=1
        etableend = len(buf)

        #resource table
        buf+=rtable
        info("Resource table at",len(buf),hex(len(buf)))

        bin["info"]={
            "nmodules":len(self.modules),
            "npyobjs":len(objbuf),
            "pyobjtable_start":pyobjtablestart,
            "pyobjtable_end":pyobjtableend,
            "ncnatives":len(self.cnatives),
            "etable_start":etablestart,
            "etable_end":etableend,
            "rtable_start":etableend,
            "rtable_elements": len(self.resources),
            "header_size": len(buf),
            "version":env.var.version,
            "bversion":env.var.version,
            "target":self.board.target,
            "project":self.curpath,
            "ofiles": [] if not ofiles else ofiles
        }

        bin["header"]=str(base64.standard_b64encode(buf),'utf-8')
        buf = bytearray()

        #Store CodeObjs
        for ic,cob in enumerate(objbuf):
            buf+=cob

        bin["pyobjs"]=str(base64.standard_b64encode(buf),'utf-8')
        bin["info"]["pyobjs_size"]=len(buf)
        bin["cobjs"]=None
        bin["modules"]=self.moduletable

        onatives = {v:k for k,v in self.cnatives.items()}
        bin["cnatives"]=[onatives[i] for i in range(0,len(onatives))]
        if ofile:
            bin["cobjs"]=str(base64.standard_b64encode(ofile),'utf-8')
        #TODO: add proper stats
        bin["stats"]={}
        bin["stats"]["modules"]={}#{k.replace(homepath,""):v for k,v in self.moduletable.items() }
        bin["stats"]["natives"]=self.cnatives
        bin["stats"]["cfiles"]=list(self.cfiles)
        bin["stats"]["target"]=self.board.target

        bin["lmap"]=lmap

        return (bin, codereprs)#, self.codeobjs)


    #TODO: experimental code, do not run in production
    def optimizeNames(self):
        self.env.buildExceptionTable()
        lmap={}
        for co in self.codeobjs:
            co.resolveExceptions(self.env)
            if co.fullname not in lmap:
                lmap[co.fullname]={
                    "co":co.fullname,
                    "idx":co.idx,
                    "names":co.getUsedNames(),
                    "types":co.getNameTypes()
                }
        attributes = set()
        builtins = set()
        modules = set()
        locals = set()
        nodes = ["__main__"]
        seen = set()
        map = {}
        while nodes:
            node = nodes.pop()
            seen.add(node)
            co = self.codeobjs[lmap[node]["idx"]]
            lco = lmap[node]
            print(co.fullname)
            if co.fullname not in map:
                map[co.fullname]={
                    "locals":set(),
                    "modules":set(),
                    "builtins":set(),
                    "attrs":set()
                }
            #add used modules
            for x in lco["names"]["IMPORT_NAME"]:
                if x not in seen:
                    nodes.append(x)
                modules.add(x)
                map[co.fullname]["modules"].add(x)
            for x in lco["names"]["LOAD_FAST"]:
                locals.add(x)
                map[co.fullname]["locals"].add(x)
                xx = co.getLocalObjectName(x)
                if xx in lmap and xx not in seen:
                    nodes.append(xx)
            for x in lco["names"]["LOAD_ATTR"]:
                attributes.add(x)
                map[co.fullname]["attrs"].add(x)
            for x in lco["names"]["LOOKUP_BUILTIN"]:
                builtins.add(x)
                map[co.fullname]["builtins"].add(x)
        return map,attributes,builtins,modules,locals



    def parseNatives(self):
        # parse natives.def
        fname = fs.path(env.stdlib,"__lang","natives.def")
        lines = fs.readlines(fname)
        for txt in lines:
            #print(txt)
            m = re.search('BUILD_NATIVE\(([a-zA-Z0-9_ \t]*),',txt)
            if m and m.group(1):
                #print("Adding Native:",m.group(1))
                self.env.addNative(m.group(1).strip())
        # parse pnames.h
        fname = fs.path(env.stdlib,"__lang","pnames.h")
        lines = fs.readlines(fname)
        for txt in lines:
            m = re.search(' NAME_([a-zA-Z0-9_]*)',txt)
            #print(txt)
            if m and m.group(1):
                #print("Adding Name:",m.group(1).lower())
                self.env.addNameCode(m.group(1))
        # parse vmsymdef
        # fnames = []
        # fname = fs.path(self.board.path,"port","config","vmsym.def")
        # if not fs.exists(fname):
        #     for dname in fs.glob(fs.path(self.board.path,"port","config","symbols"),"*.def"):
        #         fnames.append(dname)
        # else:
        #     fnames.append(fname)
        # seen = set()
        # for fname in fnames:
        #     lines = fs.readlines(fname)
        #     for txt in lines:
        #         m = re.match('\s*(SYM|VAR)\((.*)\)',txt)
        #         if m and m.group(2):
        #             if m.group(2) in seen: continue
        #             seen.add(m.group(2))
        #             self.vmsym.append(m.group(2))




