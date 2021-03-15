from base import *
from compiler import gcc
import re
import base64
import struct
import time

class Relocator():
    def __init__(self,zcode,vm,device):
        self.zcode = zcode
        #self.vmsym = []
        self.device = device
        self.thevm = vm
        self.symtable = dict(vm["map"]["table"])

        for k in self.symtable:
            self.symtable[k]=int(self.symtable[k],16)
            #debug(k,self.symtable[k])

        self.vmsym = dict(vm["map"]["sym"])
        for k in self.vmsym:
            self.vmsym[k]=int(self.vmsym[k],16)
            #debug(k,self.vmsym[k])


        # lines = vm["symdef"].split("\n")
        # for txt in lines:
        #     m = re.match('\s*(SYM|VAR)\((.*)\)',txt)
        #     if m and m.group(2):
        #         self.vmsym.append(m.group(2))

    def get_relocated_code(self,symreloc,ofile,lfile,rodata_in_ram=False):
        # print("GCCOPTS",self.device.gccopts)
        cc = gcc(tools[self.device.cc],self.device.gccopts)
        undf = cc.get_undefined(ofile)
        fund = set()
        srel = dict(symreloc)
        debug(undf)
        for u in undf:
            if u in self.vmsym:
                srel[u] = self.vmsym[u]
                fund.add(u)
            elif u in self.symtable:
                srel[u] = self.symtable[u]
                fund.add(u)

        #if undf!=fund:
        #    undf = undf-fund;
        #    debug("There are",len(undf),"missing symbols! This VM does not support the requested features!",undf)

        ret,output = cc.link([ofile],srel,reloc=False,ofile=lfile,abi=True)
        debug(output)
        if ret!=0:
            #logger.info("Relocation: %s",output)
            undf = output.count("undefined reference")
            if undf > 0:
                lines = output.split("\n")
                undefs = []
                umth = re.compile(".*undefined reference to (.+).*")

                for line in lines:
                    mth = umth.match(line)
                    if mth:
                        undefs.append(mth.group(1).replace("`","").replace("'",""))
                warning("There are",undf,"missing symbols! This VM does not support the requested features!",undefs)
                fatal("Check if the device is virtualized with the last available version-patch of the virtual machine")
            else:
                fatal("Relocation error",output)
        sym = cc.symbol_table(lfile)
        vcobj = cc.generate_zerynth_binary(sym,lfile,rodata_in_ram)
        vcobj.info()
        #sym.info()
        return vcobj

    def align_to(self,x,n):
        return x if x%n==0 else x+(n-(x%n))

    # relocate code normally, without moving rodata to ram (this is the standard for ARM mcus)
    def _relocate_noromdata(self,_memstart,vcobj,symreloc,tmpdir,ofile,lfile,debug_info):
        # no rodata_in_ram
        #adjust padding
        cbin = bytearray()
        cbin.extend(vcobj.get_section(".text"))
        data_start = vcobj.romdata_start()
        data_end = vcobj.romdata_end()
        hsize = vcobj.data_bss_size()
        if vcobj.rodata_start():
            #pad
            cbin.extend(b'\x00'*(vcobj.rodata_start()-vcobj.text_end()))
            debug("padding text",(vcobj.rodata_start()-vcobj.text_end()))
        cbin.extend(vcobj.get_section(".rodata"))
        if vcobj.romdata_start():
            #has romadata
            if vcobj.rodata_start():
                #has rodata
                cbin.extend(b'\x00'*(vcobj.romdata_start()-vcobj.rodata_end()))
                debug("padding rodata",(vcobj.romdata_start()-vcobj.rodata_end()))
            else:
                #no rodata
                cbin.extend(b'\x00'*(vcobj.romdata_start()-vcobj.text_end()))
                debug("padding rodata2")

        debug(hex(len(cbin)))
        cbin.extend(vcobj.get_section(".data"))
        debug("data_start",hex(data_start))
        if debug_info is not None:
            debug_info.append(lfile)

        return hsize, data_start, data_end, _memstart, cbin, vcobj


    # relocate code by moving rodata to ram. This is necessary in some architecture that have
    # strict differenciation between code and data segments (i.e. esp32)
    def _relocate_romdata(self,_memstart,vcobj,symreloc,tmpdir,ofile,lfile,debug_info):
        debug("Relocation .rodata")
        #align everything to 16
        new_memstart = self.align_to(_memstart,16)
        mem_pad = new_memstart-_memstart

        acc = 0
        new_text_size  = vcobj.text[2]
        new_text_start = vcobj.text[0]
        new_text_end   = vcobj.text[1]
        new_text_pad   =  self.align_to(new_text_end,16)-new_text_end

        new_rodata_size  = vcobj.rodata_size()
        new_rodata_start = 0 if not new_rodata_size else self.align_to(vcobj.rodata_start()+mem_pad,16)  #reserve space for mem_pad
        new_rodata_end   = 0 if not new_rodata_size else new_rodata_start+new_rodata_size
        new_rodata_pad   = self.align_to(new_rodata_size,16)-new_rodata_size

        acc = vcobj.romdata_start() if not new_rodata_size else new_rodata_start+new_rodata_size+new_rodata_pad
        new_romdata_size  = vcobj.romdata_size()
        new_romdata_start = 0 if not new_romdata_size else self.align_to(acc,16)
        new_romdata_end   = 0 if not new_romdata_size else new_romdata_start+new_romdata_size
        new_romdata_pad   = self.align_to(new_romdata_size,16)-new_romdata_size

        new_data_size  = vcobj.data_size()
        new_data_start = 0 if not new_data_size else self.align_to(vcobj.data_start(),16)
        new_data_end   = 0 if not new_data_size else new_data_start+new_data_size
        new_data_pad   = self.align_to(new_data_size,16)-new_data_size

        acc = vcobj.bss_start() if not new_data_size else new_data_start+new_data_size+new_data_pad
        new_bss_size  = vcobj.bss_size()
        new_bss_start = 0 if not new_bss_size else self.align_to(acc,16)
        new_bss_end   = 0 if not new_bss_size else new_bss_start+new_bss_size
        new_bss_pad   = self.align_to(new_bss_size,16)-new_bss_size

        debug("Code blueprints with relocation")
        debug("text        ::",hex(new_text_start),"::",hex(new_text_end),"::",hex(new_text_size))
        debug("rodata      ::",hex(new_rodata_start),"::",hex(new_rodata_end),"::",hex(new_rodata_size),"::",hex(new_rodata_start-new_text_end))
        debug("romdata     ::",hex(new_romdata_start),"::",hex(new_romdata_end),"::",hex(new_romdata_size),"::",hex(new_romdata_start-new_text_end))
        debug("data        ::",hex(new_data_start),"::",hex(new_data_end),"::",hex(new_data_size))
        debug("bss         ::",hex(new_bss_start),"::",hex(new_bss_end),"::",hex(new_bss_size),"::",hex(new_bss_start-new_data_end))


        sects = {
            ".text":new_text_start,
            ".data":new_data_start,
            ".romdata":new_romdata_start,
            ".rodata":new_rodata_start,
            ".bss":new_bss_start,
            ".eh_frame":new_bss_end,
            ".ctors":new_romdata_end
        }
        symreloc.update(sects)


        # adjust data in mem
        if vcobj.rodata[2]:
            # has rodata
            sects.update({".rodata":new_memstart})
            if vcobj.data[2]:
                sects.update({".data":self.align_to(new_memstart+vcobj.rodata[2],16)})
                if vcobj.bss[2]:
                    sects.update({".bss":self.align_to(sects[".data"]+vcobj.data[2],16)})
                    sects.update({".eh_frame":sects[".bss"] + new_bss_size})
                else:
                    sects.update({".eh_frame":sects[".data"] + new_data_size})
            else:
                if vcobj.bss[2]:
                    sects.update({".bss":self.align_to(new_memstart+vcobj.rodata[2],16)})
                    sects.update({".eh_frame":sects[".bss"] + new_bss_size})
                else:
                    sects.update({".eh_frame":sects[".rodata"] + new_rodata_size})
        elif vcobj.data[2]:
            # no rodata, has data
            sects.update({".data":new_memstart})
            if vcobj.bss[2]:
                sects.update({".bss":self.align_to(new_memstart+vcobj.data[2],16)})
                sects.update({".eh_frame":sects[".bss"] + new_bss_size})
            else:
                sects.update({".eh_frame":sects[".data"] + new_data_size})
        elif vcobj.bss[2]:
            # only bss
            sects.update({".bss":new_memstart})
            sects.update({".eh_frame":sects[".bss"] + new_bss_size})

 
        symreloc.update(sects)
        debug("Relocated sections")
        for k,v in sects.items():
            debug(k,"==>",hex(v))


        ###########################################
        # text - pad - rodata - pad - romdata - pad


        lfile2 = fs.path(tmpdir,"zerynth.lo2")
        if debug_info is not None:
            debug_info.append(lfile2)
        vcobj2 = self.get_relocated_code(symreloc,ofile,lfile2,True)

        fwend = new_romdata_end if new_romdata_size else new_rodata_end
        fwsize = fwend - new_text_start
        cbin = bytearray(b'\x00'*fwsize)

        cbin[0:new_text_size] = vcobj2.get_section(".text")
        prev_end = new_text_start
        if new_rodata_size:
            cbin[new_rodata_start-new_text_start:new_rodata_end-new_text_start] = vcobj.get_section(".rodata")
        if new_romdata_size:
            cbin[new_romdata_start-new_text_start:new_romdata_end-new_text_start] = vcobj.get_section(".data")

        if new_rodata_size:
            data_start = new_rodata_start-mem_pad
            data_end = new_rodata_end if not new_romdata_size else new_romdata_end
        elif  new_romdata_size:
            data_start = new_romdata_start-mem_pad
            data_end = new_romdata_end

        if vcobj2.bss_end() or vcobj2.data_end():
            hsize = max(vcobj2.bss_end(),vcobj2.data_end())-_memstart
        else:
            hsize = data_end-data_start
        # else:
        #     hsize = 0
        #     data_start = 0
        #     data_end = 0

        debug("ram data size",hex(hsize))
        debug("ram data start",hex(data_start))
        debug("ram data end",hex(data_end))
        debug("binary data size",len(cbin))

        return hsize, data_start, data_end, _memstart, cbin, vcobj

    def _fill_bcode_header(self,header,_textstart,_romstart,_memstart,data_start,data_end,hsize,pyobjs,vcobj):
        zinfo = self.zcode["info"]
        cnatives = self.zcode["cnatives"]
        # padding pyobjs
        pdsz = _textstart-_romstart-len(header)-len(pyobjs)
        for i in range(0,pdsz):
            pyobjs+=struct.pack("=B",0)
        # updating header
        header[12:16] = struct.pack("=I",_memstart)
        header[16:20] = struct.pack("=I",data_start)
        header[20:24] = struct.pack("=I",data_end)
        header[24:28] = struct.pack("=I",hsize)

        # updating native table
        hbg = zinfo["pyobjtable_end"]
        #logger.debug("cnatives: %i symbols: %i",len(self.upl.cnatives),len(vcobj.symbols))
        rlct = self.device.relocator
        for nn in cnatives:
            try:
                addr = vcobj.symbols[nn]
            except Exception as e:
                fatal("Missing symbols!",nn)
            #print(nn,hex(addr))
            #logger.info("%s => %s",tohex(addr), nn)
            # WARNING!!! +1 because it's thumb instructions! (maybe we should add thumb in arch)
            if rlct=="cortex-m":
                header[hbg:hbg+4]=struct.pack("=I",addr+1)
            else:
                header[hbg:hbg+4]=struct.pack("=I",addr)
            hbg+=4

    def _fill_thebin(self,thebin):
        # insert bytecode length
        thebin[52:56]=struct.pack("=I",len(thebin))
        # insert vm version
        thebin[56:60]=struct.pack("=I",int(self.thevm["hexversion"],16))
        # calculate hash with ts=0 and hash=0
        hash = md5b(thebin)
        # insert hash
        thebin[28:44]=hash
        # insert timestamp
        thebin[44:48]=struct.pack("=I",int(time.time()))

        return thebin


    def _get_objs_from_zcode(self,_romstart):
        cobjs = self.zcode["cobjs"]
        header = bytearray(base64.standard_b64decode(self.zcode["header"]))
        pyobjs = bytearray(base64.standard_b64decode(self.zcode["pyobjs"]))

        if cobjs:
            cobj = base64.standard_b64decode(cobjs)
        else:
            cobj = bytes()

        _textstart = _romstart+len(header)+len(pyobjs)
        debug("textstart",hex(_textstart))
        #info("Relocation Info: memstart %x romstart %x",_memstart,_romstart)
        _textstart=self.align_to(_textstart,16)#+(16-(_textstart%16))
        debug("textstart",hex(_textstart))

        return cobj,header,pyobjs,_textstart

    # old relocation, with memdelta, before r19.09.16
    def relocate_with_memstart(self,_memstart,_romstart,debug_info=None,tempdir=None):
        #logger.info("Relocating Bytecode for %s",self.upl.board["shortname"])
        # cc = gcc(tools[self.device.cc],opts=self.device.gccopts)
        # unpack zcode

        cobj,header,pyobjs,_textstart = self._get_objs_from_zcode(_romstart)
        rodata_in_ram=self.device.get("rodata_in_ram",False)

        if cobj:
            tmpdir = tempdir or fs.get_tempdir()
            ofile = fs.path(tmpdir,"zerynth.rlo")
            lfile = fs.path(tmpdir,"zerynth.lo")
            fs.write_file(cobj,ofile)
            symreloc = {}
            symreloc.update({"_start":0,".data":_memstart,".text":_textstart})
            vcobj = self.get_relocated_code(symreloc,ofile,lfile,rodata_in_ram)
            if rodata_in_ram:
                debug("Relocation .rodata")
                hsize, data_start,data_end,_memstart,cbin,vcobjl = self._relocate_romdata(_memstart,vcobj,symreloc,tmpdir,ofile,lfile,debug_info)
            else:
                hsize, data_start,data_end,_memstart,cbin,vcobjl = self._relocate_noromdata(_memstart,vcobj,symreloc,tmpdir,ofile,lfile,debug_info)

            if debug_info is not None:
                debug_info.append(_textstart)

            self._fill_bcode_header(header,_textstart,_romstart,_memstart,data_start,data_end,hsize,pyobjs,vcobjl)

            thebin = header+pyobjs+cbin
        else:
            thebin = header+pyobjs

        return self._fill_thebin(thebin)


    def relocate_with_memend(self,_memend,_romstart,debug_info=None,tempdir=None):
        #logger.info("Relocating Bytecode for %s",self.upl.board["shortname"])
        # cc = gcc(tools[self.device.cc],opts=self.device.gccopts)
        # unpack zcode
        cobj,header,pyobjs,_textstart = self._get_objs_from_zcode(_romstart)

        rodata_in_ram=self.device.get("rodata_in_ram",False)

        if cobj:
            tmpdir = tempdir or fs.get_tempdir()
            ofile = fs.path(tmpdir,"zerynth.rlo")
            lfile = fs.path(tmpdir,"zerynth.lo")
            fs.write_file(cobj,ofile)
            symreloc = {}
            symreloc.update({"_start":0,".data":_memend,".text":_textstart})
            vcobj = self.get_relocated_code(symreloc,ofile,lfile,rodata_in_ram)
            # cbin = vcobj.binary
            # data_start = vcobj.romdata_start()
            # data_end = vcobj.romdata_end()
            hsize = vcobj.data_bss_size()
            #now calculate real memstart
            _memstart = _memend-hsize;
            if _memstart%16:
                _memstart=_memstart&(~0xf)
            symreloc.update({"_start":0,".data":_memstart,".text":_textstart})
            vcobj = self.get_relocated_code(symreloc,ofile,lfile,rodata_in_ram)
            debug("MEMSTART 1",hex(_memstart))
            if rodata_in_ram:
                # pass 1: calculate hsize
                debug("RODATA IN RAM STEP 1",hex(_memstart))
                hsize,_,_,_,_,_ = self._relocate_romdata(_memstart,vcobj,symreloc,tmpdir,ofile,lfile,debug_info)
                # pass 2: relink with correct memstart
                _memstart = _memend-hsize
                if _memstart%16:
                    _memstart=_memstart&(~0xf)
                debug("MEMSTART 2",hex(_memstart))
                symreloc = {"_start":0,".data":_memstart,".text":_textstart}
                debug("RODATA IN RAM STEP 2",hex(_memstart))
                # vcobj = self.get_relocated_code(symreloc,ofile,lfile,rodata_in_ram)
                hsize, data_start,data_end,_memstart,cbin,vcobjl = self._relocate_romdata(_memstart,vcobj,symreloc,tmpdir,ofile,lfile,debug_info)
            else:
                hsize, data_start,data_end,_memstart,cbin,vcobjl = self._relocate_noromdata(_memstart,vcobj,symreloc,tmpdir,ofile,lfile,debug_info)

            if debug_info is not None:
                debug_info.append(_textstart)

            self._fill_bcode_header(header,_textstart,_romstart,_memstart,data_start,data_end,hsize,pyobjs,vcobjl)

            thebin = header+pyobjs+cbin
        else:
            thebin = header+pyobjs

        return self._fill_thebin(thebin)


    def relocate(self,_memstart_or_memend,_romstart,debug_info=None,tempdir=None):
        vm = self.thevm
        vmversion = vm["version"]
        if vmversion<"r20.01.30":
            #old vm with memdelta
            if _memstart_or_memend == -1:
                # linking without knowning memdelta (called by ztc.link)
                debug("Relocating with vm.memstart strategy")
                _memstart_or_memend = int(vm["map"]["memstart"],16)+vm["map"]["memdelta"]
            else:
                debug("Relocating with dev.memstart strategy")

            return self.relocate_with_memstart(_memstart_or_memend,_romstart,debug_info,tempdir)
        else:
            if _memstart_or_memend == -1:
                # linking without knowning memdelta (called by ztc.link)
                debug("Relocating with map.memend strategy")
                _memstart_or_memend = int(vm["map"]["memend"],16)
            else:
                debug("Relocating with dev.memend strategy")

            # new vm without memdelta
            return self.relocate_with_memend(_memstart_or_memend,_romstart,debug_info,tempdir)

