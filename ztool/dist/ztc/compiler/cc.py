from base import *
import re


# CPU = -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=$(FLOAT_ABI)
# CC_FLAGS = $(CPU) -c -g -fno-common -fmessage-length=0 -Wall -fno-exceptions -ffunction-sections -fdata-sections -fomit-frame-pointer -fdiagnostics-color=auto
# CC_FLAGS += -MMD -MP


# -mcpu=cortex-m4 -O2 -ggdb -fomit-frame-pointer -falign-functions=16 -fdiagnostics-color=auto -ffunction-sections -fdata-sections -fno-common  -Wall -Wextra -Wstrict-prototypes
# -MD -MP -MF
# -mthumb


class ZerynthCObj():
    def __init__(self):
        self.sections = {}
        self.binary = bytearray()
        self.data = [None,None,None]
        self.rodata = [None,None,None]
        self.text = [None,None,None]
        self.bss = [None,None,None]
        self.romdata = [None,None,None]
        self.symbols = {}        
    def add_data(self, section, data):
        if section:
            if section not in self.sections:
                self.sections[section]=bytearray()
            self.sections[section].append(data)

    def get_section(self,name):
        return self.sections.get(name,bytes())

    def romdata_size(self):
        return self.romdata[2] if self.romdata[2] is not None else 0

    def romdata_start(self):
        return self.romdata[0] if self.romdata[0] is not None else 0
    
    def romdata_end(self):
        return self.romdata[1] if self.romdata[1] is not None else 0

    def rodata_size(self):
        return self.rodata[2] if self.rodata[2] is not None else 0

    def rodata_start(self):
        return self.rodata[0] if self.rodata[0] is not None else 0
    
    def rodata_end(self):
        return self.rodata[1] if self.rodata[1] is not None else 0

    def data_size(self):
        return self.data[2] if self.data[2] is not None else 0

    def data_start(self):
        return self.data[0] if self.data[0] is not None else 0
    
    def data_end(self):
        return self.data[1] if self.data[1] is not None else 0

    def bss_size(self):
        return self.bss[2] if self.bss[2] is not None else 0

    def bss_start(self):
        return self.bss[0] if self.bss[0] is not None else 0
    
    def bss_end(self):
        return self.bss[1] if self.bss[1] is not None else 0

    def text_size(self):
        return self.text[2] if self.text[2] is not None else 0

    def text_start(self):
        return self.text[0] if self.text[0] is not None else 0
    
    def text_end(self):
        return self.text[1] if self.text[1] is not None else 0




    def data_bss_size(self):
        hstart=0
        hend = 0
        if self.data[2]:
            hstart = self.data[0]
            hend = self.data[1]
            #hsize+=vcobj.data[2]
        if self.bss[2]:
            if hstart:
                hend = self.bss[1]
            else:
                hstart=self.bss[0]
                hend=self.bss[1]
            #hsize+=vcobj.bss[2]
        return hend-hstart



    def finalize(self,table,rodata_in_ram=False):
        #print("Finalizing with",table.table)
        has_bss = ".bss" in table.sections
        has_data = ".data" in table.sections
        has_rodata = ".rodata" in table.sections
        has_text = ".text" in table.sections
        #print(has_bss,has_data,has_rodata,has_text)
        #print(table)
        #table.info()
        for k,v in table.table.items():
            #info("Checking",k,v)
            if v[3]==".text":
                self.symbols[v[0]]=int(v[2],16)
            elif v[3]==".bss" and (v[0]=="__bss_end__" or v[0]=="_end"):
                bss_end = int(v[2],16)
            elif v[3]==".data" and v[0]=="_edata":
                data_end = int(v[2],16)
        if has_bss:            
            bss_start = int(table.sections[".bss"][2],16)
            self.bss = [bss_start,bss_end,bss_end-bss_start]
        if has_text:
            text_start = int(table.sections[".text"][2],16)
            text_end = text_start+len(self.sections[".text"])
            self.text = [text_start,text_end,text_end-text_start]
            #print("extending .text",len(self.binary))
            self.binary.extend(self.sections[".text"])
            #print("extended .text",len(self.binary))
        if has_rodata:
            rodata_start = int(table.sections[".rodata"][2],16)
            rodata_end = int(rodata_start)+len(self.sections[".rodata"])
            self.rodata = [rodata_start,rodata_end,rodata_end-rodata_start]
            #print("extending .rodata",len(self.binary))
            self.binary.extend(self.sections[".rodata"])        
            #print("extended .rodata",len(self.binary))
        if has_data:
            data_start = int(table.sections[".data"][2],16)
            self.data = [data_start,data_end,data_end-data_start]            
            if has_rodata:
                data_rom_start = rodata_end
                data_rom_end = data_rom_start+len(self.sections[".data"])    
                self.romdata = [data_rom_start,data_rom_end,data_rom_end-data_rom_start]
            elif has_text:
                data_rom_start = text_end
                data_rom_end = data_rom_start+len(self.sections[".data"])    
                self.romdata = [data_rom_start,data_rom_end,data_rom_end-data_rom_start]
            else:
                pass                
                #RAISE EXCEPTION! no cobj without .text allowed
            #print("extending .romdata",len(self.binary))
            self.binary.extend(self.sections[".data"])
            #print("extended .romdata",len(self.binary))
                
    def info(self):
        if self.data[0]:
            debug(".data   :",hex(self.data[0]),"=>",hex(self.data[1]),"::",hex(self.data[2]))
        if self.bss[0]:
            debug(".bss    :",hex(self.bss[0]),"=>",hex(self.bss[1]),"::",hex(self.bss[2]))
        if self.text[0]:
            debug(".text   :",hex(self.text[0]),"=>",hex(self.text[1]),"::",hex(self.text[2]))
        if self.rodata[0]:
            debug(".rodata :",hex(self.rodata[0]),"=>",hex(self.rodata[1]),"::",hex(self.rodata[2]))
        if self.romdata[0]:
            debug(".romdata:",hex(self.romdata[0]),"=>",hex(self.romdata[1]),"::",hex(self.romdata[2]))
        debug("binsize :",len(self.binary))
        #for sym,addr in self.symbols.items():
        #    debug(hex(addr),"::",sym)


class symtable():
    undef = "*UND*"
    abs = "*ABS*"
    def __init__(self):
        self.table = {}
        self.sections = {"*ABS*":["*ABS*",0,0,0],"*UND*":["*UND*",0,0,0]}
    def add(self, name, size, addr, sect):
        #info("<<adding",name,size,addr,sect)
        if name.startswith("."):
            debug("--",name,size,addr)
            self.sections[name]=[name,int(size,16),addr,0]
        else:
            if sect=="*COM*":
                sect=".bss"
            self.table[name]=(name,int(size,16),addr,sect)
            debug(sect,name,size,int(size,16))
            self.sections[sect][1]+=int(size,16)
            self.sections[sect][3]+=1
    def getfrom(self,sect):
        res = {}
        for k,v in self.table.items():
            if v[3]==sect:
                res[v[0]]=v[2]
        return res
    def sizeof(self,sect):
        return self.sections[sect][1]
    def elementsof(self,sect):
        return self.sections[sect][3]
    def symbols(self):
        return frozenset(self.table.keys())
    def info(self):
        for k,v in self.sections.items():
            debug(k,":",v[1],"@",v[2],"#",v[3])
        for k,v in self.table.items():
            debug(k,"in",v[3],v[1],"@",v[2])

#TODO: abstract for generic platform
class gcc():
    def __init__(self,tools, opts={}):
        self.gcc = tools["gcc"]
        self.gccopts = ["-c"]
        self.defines=[]
        self.incpaths=[]
        if "cflags" in opts:
            self.gccopts.extend(opts["cflags"])
        if "defs" in opts:
            self.defines = ["-D"+str(x) for x in opts["defs"]]
        if "inc" in opts:
            self.incpaths = ["-I"+str(x) for x in opts["inc"]]
        self.archopts = opts["arch"]


        self.objdump = tools["objdump"]
        self.ld = tools["ld"]
        self.readelf = tools["readelf"]

        # find search path: https://stackoverflow.com/a/21610523
        ret, output = self.run_command(self.gcc,self.archopts+["-print-search-dirs"])
        if ret != 0:
            error("Linking Error:",output);

        lines = output.split('\n')
        self.libpaths=[]
        for line in lines:
            if line.startswith("libraries: ="):
                if env.platform.startswith("win"):  #how cool is that? -_-
                    paths = line[12:].split(";")
                else:
                    paths = line[12:].split(":")
                for path in paths:
                    self.libpaths.append(fs.apath(path))
                break
        if not self.libpaths:
            warning("No library path found!")
        # else:
        #     print(self.libpaths)


        # search for compiler libraries in ../lib
        # libpath = None
        # libfiles = fs.all_files(fs.path(fs.dirname(self.gcc),"..","lib"))
        # libgcc = []
        # for libfile in libfiles:
        #     if fs.basename(libfile)=="libgcc.a":
        #         libgcc.append(libfile) 
        # if not libgcc:    
        #     fatal("Can't find libgcc!")
        # for libfile in libgcc:
        #     # select thumb libgcc if existing
        #     libpath = fs.dirname(libfile)
        #     if "thumb" in libfile:
        #         break
        # debug("libgcc:",libpath)
        # self.libpath = libpath

        # # find math lib
        # libmath=None
        # libfiles = fs.all_files(fs.path(fs.dirname(self.gcc),".."),filter="libm.a")
        # for libfile in libfiles:
        #     if fs.basename(fs.dirname(libfile))=="lib":
        #         libmath=libfile
        #         break
        # if not libmath:    
        #     fatal("Can't find libmath!")
        # self.libmath = libmath
        # print(self.libpath,self.libmath)
                


    def run_command(self,cmd, args):
        ret = 0
        torun = [cmd]
        torun.extend(args)
        debug("Exec:",torun)
        ecode,cout,cerr = proc.run(torun)
        return (ecode,cout)

    def get_headers(self,fnames):
        res = {}
        for fname in fnames:
            inc = []
            res[fname]=[]
            dirname, filename = fs.split(fname)
            if dirname:
                inc.append("-I"+dirname)
            inc.extend(self.incpaths)
            nm = [fname]
            ret, output = self.run_command(self.gcc,self.gccopts+["-M"]+inc+nm+self.defines)
            if not ret:
                lines = output.split("\n")
                for line in lines:
                    if line.endswith("\\"):
                        line=line[0:-1]
                    line=line.strip()
                    if fs.exists(line):
                        res[fname].append(line)
            return res

    def compile(self, fnames,o=None):
        wrn = {}
        err = {}
        ret = 1
        for fname in fnames:
            inc = []
            dirname, filename = fs.split(fname)
            if dirname:
                inc.append("-I"+dirname)
            inc.extend(self.incpaths)
            #print(inc)
            nm = [fname]
            if o:
                nm.append("-o")
                if not fs.isdir(o):
                    nm.append(o)
                else:
                    nm.append(fs.path(o,fs.basename(fname).replace(".c",".o")))
                    
            ret, output = self.run_command(self.gcc,self.gccopts+inc+nm+self.defines+["-g"])
            #print(output)
            lines = output.split("\n")
            catcher = re.compile("(.+):([0-9]+):([0-9]+):[^:]*(warning|error)(.*)")
            for line in lines:
                res = catcher.match(line)
                if res:
                    if res.group(4)=="warning":
                        cnt = wrn
                    elif res.group(4)=="error":
                        cnt = err
                    else:
                        continue
                    fname = res.group(1)
                    if fname not in cnt:
                        cnt[fname] = []
                    cnt[fname].append({
                        "type":res.group(4),
                        "line":int(res.group(2)),
                        "col":int(res.group(3)),
                        "msg":res.group(5)
                    })
            if ret!=0:
                break
        return (ret,wrn,err,output)
    def symbol_table(self,fname):
        ret = symtable()
        res, output = self.run_command(self.objdump,["-t",fname])
        output = output.replace("\t"," ")
        if res==0:
            catcher = re.compile("([0-9a-fA-F]+)([A-Za-z ]+)([^ ]+) ([0-9a-fA-F]+) ([^ ]+)")
            lines = output.split("\n")
            for line in lines:
                #print(">>",line,"<<")
                mth = catcher.match(line)
                if mth:
                    #info("matched\n",mth.group(5),mth.group(4))
                    debug(line)
                    ret.add(mth.group(5),mth.group(4),mth.group(1),mth.group(3))
                else:
                    pass
                    #print("not matched\n")
        return ret
    def get_undefined(self,fname):
        res, output = self.run_command(self.objdump,["-t",fname])
        output = output.replace("\t"," ")
        ret = set()
        if res==0:
            catcher = re.compile("([0-9a-fA-F]+)([A-Za-z ]+)([^ ]+) ([0-9a-fA-F]+) ([^ ]+)")
            lines = output.split("\n")
            for line in lines:
                # print(">>",line,"<<")
                mth = catcher.match(line)
                
                if mth and mth.group(3) in ["*ABS*","*UND*"] and "f" not in mth.group(2):
                    #info("matched\n",mth.group(5),mth.group(4))
                    #debug(line)
                    ret.add(mth.group(5))
                else:
                    pass
                    #print("not matched\n")
        return ret
    def link(self, fnames, symt={}, reloc=True, ofile=None, abi=False, libs=[]):
        ldopt =[]
        for k,v in symt.items():
            if k.startswith("."):
                ldopt.append("--section-start="+k+"="+hex(v))
            else:
                ldopt.append("--defsym="+k+"="+hex(v))
        #ldopt.append("--gc-sections")
        if reloc:
            ldopt.append("-r")
        ldopt.extend(fnames)

        # add library paths
        for l in self.libpaths:
            ldopt.append("-L")
            ldopt.append(l)

        # First, libraries
        for lib in libs:
            if fs.exists(lib):
                if fs.isfile(lib):
                    #add to linker
                    ldopt.append(lib)
                else:
                    #it's a dir, add -L
                    ldopt.append("-L")
                    ldopt.append(lib)
            else:
                #it's an abbreviated lib
                ldopt.append("-l"+lib)

        #add libgcc as last one (symbols in gcc.a are needed by previous libraries)
        if abi:
            # ldopt.append("-L")
            # ldopt.append(self.libpath)
            ldopt.append("-lgcc")


        if ofile:
            ldopt.append("-o")
            ldopt.append(ofile)
        # print(ldopt)
        ret,output = self.run_command(self.ld,ldopt)
        # print(output)
        return (ret,output)
    def retrieve_sections(self,fname):
        res,output = self.run_command(self.objdump,["-s",fname])
        lines = output.replace("\t"," ").split("\n")
        bcatcher = re.compile(" ([0-9a-fA-F]+) ([0-9a-fA-F]*) ([0-9a-fA-F]*) ([0-9a-fA-F]*) ([0-9a-fA-F]*)(.*)")
        hcatcher = re.compile("Contents of section ([^:]+)")
        cursect = None
        sections = {}
        for line in lines:
            hmth = hcatcher.match(line)
            if hmth:
                #header line
                grps = hmth.group(1).split(".")
                grp = "."+grps[1]
                if grp not in [".text",".rodata",".data",".bss"]:
                    cursect = None
                else:
                    cursect = grp
                    if cursect not in sections:
                        sections[cursect]=0
                continue
            bmth = bcatcher.match(line)
            if bmth:
                if cursect:
                    bstr = bmth.group(2).strip()+bmth.group(3).strip()+bmth.group(4).strip()+bmth.group(5).strip()
                    bstr = [bstr[i:i + 2] for i in range(0, len(bstr), 2)]
                    for byte in bstr:
                        sections[cursect]+=1
                        #cobj.add_data(cursect,int(byte,16))
        return sections

    def generate_zerynth_binary(self,table,fname,rodata_in_ram=False):
        res,output = self.run_command(self.objdump,["-s",fname])
        cobj = ZerynthCObj()
        if res==0:
            lines = output.replace("\t"," ").split("\n")
            bcatcher = re.compile(" ([0-9a-fA-F]+) ([0-9a-fA-F]*) ([0-9a-fA-F]*) ([0-9a-fA-F]*) ([0-9a-fA-F]*)(.*)")
            hcatcher = re.compile("Contents of section ([^:]+)")
            cursect = None
            for line in lines:
                #info("--",line)
                hmth = hcatcher.match(line)
                if hmth:
                    #header line                    
                    if hmth.group(1) not in [".text",".rodata",".data"]:
                        cursect = None
                    else:
                        cursect = hmth.group(1)
                    continue
                bmth = bcatcher.match(line)
                if bmth:
                    if cursect:
                        bstr = bmth.group(2).strip()+bmth.group(3).strip()+bmth.group(4).strip()+bmth.group(5).strip()
                        bstr = [bstr[i:i + 2] for i in range(0, len(bstr), 2)]
                        for byte in bstr:
                            cobj.add_data(cursect,int(byte,16))
        cobj.finalize(table,rodata_in_ram)
        #cobj.info()
        return cobj                                                
    def info(self):
        print("GCC")
        print(self.gcc)
        print(self.objdump)
        print(self.ld)
        print(self.readelf)


# cmp = gcc("tools/linux64/gcc/arm","arm-none-eabi-")
# cmp.info()
# print(cmp.compile(["linktest.c"]))
# print(cmp.link(["linktest.o"],{"_vsymbase":0x0805000,"_start":0x800000,".text":0x808000,".data":0x208000}))
# st=cmp.symbol_table("viper.vy")
# st.info()
# bin=cmp.generate_viper_binary(st,"viper.vy")
# bin.info()
