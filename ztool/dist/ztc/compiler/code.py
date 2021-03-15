'''
Created on Oct 19, 2013

@author: giacomo
'''
from compiler.opcode import OpCode
from compiler.env import MiniTable
import struct


def _tohex(bb):
    res = ""
    c="0123456789ABCDEF"
    for b in bb:
        res=res+"\\x"+c[(b>>4)&0xf]+c[b&0xf]
    return res



class CodeObj():
    codesubtypes = {
        "fun":0,
        "module":1,
        "class":2,
        "cfun":0
    }
    def __init__(self, name, kind, idx, nargs,nkwargs, vargs,module=None,cls=None,ccode=None,srcfile=None):
        self.srcfile=srcfile
        self.consts = []
        self.pconst = {}
        self.const_table = []
        self.pconstsize = 0
        self.nargs = nargs
        self.nkwargs = nkwargs
        self.vargs = vargs
        self.stacksize = 0
        self.bstacksize = 0
        self.totargs = nkwargs+nargs+(1 if vargs else 0)
        self.bytecode = ByteCode()
        self.name = name
        self.argnames = []
        self.kwargnames = []
        self.argpos = []
        self.kwargpos = []
        self.localnames = []
        self.localpos = []
        self.kind = kind
        self.idx = idx
        self.scope = None
        self.module = module if kind!="module" else None
        self.cls = cls
        self.ccode = ccode
        self.refcodes = []
        self.refmodules = []
        self.refbuiltins = set()
        self.refnatives = set()
        self.namemap = {}
        self.cblocks=0
        self.lastline=0
        self.firstline=0
        self.prglines = {}
        self.nametypes = {}
        self.usednames = set()
        self.usedglobals = set()
        self.usedattrs = set()
        self.usedbuiltins = set()
        self.fullname = (self.module+"." if self.module!=None else "")+(self.cls+"." if self.cls!=None else "")+self.name

    def pushBlock(self):
        self.cblocks+=1
        if self.cblocks>self.bstacksize:
            self.bstacksize=self.cblocks

    def popBlock(self):
        self.cblocks-=1

    def getBlocks(self):
        return self.bstacksize
        
    def __str__(self):
        res = ";;" + "-" * 40 + "\n"
        res += ";;CodeObj: " + self.scope.uid + " :: " + self.kind + " :: " + str(self.idx)+"("+str(self.nargs) + ")\n"
        res += ";;      src      : " + str(self.srcfile) + ":"+str(self.firstline)+":"+str(self.lastline)+"\n"
        res += ";;      consts   : " + str(self.consts) + "\n"
        res += ";;      args     : " + str(self.argnames) + "\n"
        res += ";;      kwargs   : " + str(self.kwargnames) + "\n"
        res += ";;      locals   : " + str(self.scope.locals) + "\n"
        res += ";;      freevars : " + str(self.scope.freevars) + "\n"
        res += ";;      cellvars : " + str(self.scope.cellvars) + "\n"
        res += ";;      blocks   : " + str(self.bstacksize) + "\n"
        res += ";;      stacksize: " + str(self.stacksize) + "\n"
        res += ";;      argpos   : " + str(self.argpos) + "\n"
        res += ";;\n"
        res += ";;st   pos    op              params             args\n"
        res += "\n"
        res += str(self.bytecode)
        return res

    def toDict(self,dirs=[]):
        srcfile = [self.srcfile.replace(y,"") for y in dirs if y in self.srcfile]
        if srcfile:
            srcfile=srcfile[0][1:]
        else:
            srcfile=self.srcfile
        jc = {
            "header":{
                "src":srcfile,
                "scope":self.scope.uid,
                "kind":self.kind,
                "idx":self.idx,
                "args":[self.nargs,self.nkwargs,self.vargs],
                "consts":[(lambda x: x if not isinstance(x,bytes) else repr(x))(k) for k in self.consts],
                "locals":self.scope.locals,
                "freevars":self.scope.freevars,
                "cellvars":self.scope.cellvars,
                "stacksize":self.stacksize,
                "blocks":self.bstacksize
            },
            "bytecode":self.bytecode.toDict()
        }
        return jc

    def getUsedNames(self):
        res = {
            "LOOKUP_NAME":set(),
            "LOOKUP_BUILTIN":set(),
            "IMPORT_NAME":set(),
            "LOAD_ATTR":set(),
            "LOAD_FAST":set()
        }
        for op in self.bytecode.opcodes:
            if op.name in res:
                res[op.name].add(op.aname)
        for k,v in res.items():
            res[k] = list(res[k])
        return res

    def addUsedName(self,name):
        self.usednames.add(name)

    def getNameTypes(self):
        res = {}
        for k,v in self.nametypes.items():
            res[k] = list(v)
        return res

    def getLocalObjectName(self,name):
        return self.fullname+"."+name

    def addNameType(self,name,type):
        pass
        # if name not in self.nametypes:
        #     self.nametypes[name] = set()
        # self.nametypes[name].add(type)

    def isJustStop(self):
        return len(self.bytecode.opcodes)==1 and self.bytecode.opcodes[-1].name=="STOP"

    def swapTwo(self):
        self.bytecode.swapTwo()

    def getPrefix(self):
        return self.name+"." if self.kind=="module" else self.module+"."

    def hasName(self,name):
        return name in self.scope.locals or name in self.scope.freevars

    def getNameMap(self):
        if len(self.namemap)==0:
            self.generateNameMap()
        return self.namemap

    def generateNameMap(self):
        ref = {"__init__":[0,1,0,0]}
        for op in self.bytecode.opcodes:
            if op.isFinalizedLoad():
                if op.aname not in ref:
                    ref[op.aname]=[0,0,0,0]
                #print("check",op,op.isAttrOp(),op.isGlobalOp(),op.isBuiltin())
                if op.isAttrOp():
                    ref[op.aname][1]+=1
                elif op.isGlobalOp():
                    ref[op.aname][2]+=1
                elif not op.isLookupBuiltin():
                    ref[op.aname][0]+=1
                else:
                    ref[op.aname][3]+=1
        self.namemap =ref
        return ref

    def addCode(self, code):
        if isinstance(code, ByteCode):
            for op in code.opcodes:
                if op.hasConst():
                    cnst = op.getConst()
                    idx = self.addConst(cnst)
            for pline,val in code.plines.items():
                self.prglines[pline]=self.bytecode.size+val
        elif isinstance(code, OpCode):
            if code.hasConst():
                cnst = code.getConst()
                idx = self.addConst(cnst)
        else:
            for ll in code:
                self.addCode(ll)
        self.bytecode.addCode(code)
        return self

    def addKwArgName(self,name):
        if name not in self.kwargnames:
            self.kwargnames.append(name);

    def addArgName(self,name):
        if name not in self.argnames:
            self.argnames.append(name);

    def resolveExceptions(self,env):
        for op in self.bytecode.opcodes:
            if op.isBuildException():
                ename = op.params[0].val
                op.toBuildException(env.resolveException(ename))

    def finalize(self, env):
        
        self.scope = env.getScope()
        self.argpos = [None]*len(self.argnames)
        self.sigpos = [None]*(len(self.argnames)+len(self.kwargnames))
        self.kwargpos = [None]*len(self.kwargnames)
        self.namecode = env.getNameCode(self.name)

        if self.kind!="cfun":
            # Resolve Names
            curpos = 0;
            for op in self.bytecode.opcodes:
                #print("Res: "+str(op)+"\n")            
                if op.isRefOp():
                    name = op.getRefName()
                    nfo = env.nameInfo(name)
                    if nfo.isLocal():
                        op.toFastName(nfo.idx)
                        if name in self.argnames:
                            self.argpos[self.argnames.index(name)] = nfo.idx
                            self.sigpos[self.argnames.index(name)+len(self.kwargnames)] = nfo.idx
                        if name in self.kwargnames:
                            self.kwargpos[self.kwargnames.index(name)] = nfo.idx
                            self.sigpos[self.kwargnames.index(name)] = nfo.idx
                    elif nfo.isGlobal():
                        op.toGlobalName(nfo.idx)
                        self.usedglobals.add(name)
                        self.usednames.discard(name)
                    elif nfo.isDeref():
                        op.toDerefName(nfo.idx)
                        #print("DEREF for",self.name,"of",name,"@",nfo.idx,name in self.argnames,name in self.kwargnames)
                        if name in self.argnames:
                            self.argpos[self.argnames.index(name)] = -nfo.idx -1#+len(self.scope.locals)
                            self.sigpos[self.argnames.index(name)+len(self.kwargnames)] = -nfo.idx-1
                        if name in self.kwargnames:
                            self.kwargpos[self.kwargnames.index(name)] = -nfo.idx-1#+len(self.scope.locals)
                            self.sigpos[self.kwargnames.index(name)] = -nfo.idx-1
                    elif nfo.isBuiltin():
                        psz = op.size();
                        op.toLookupBuiltin()
                        self.refbuiltins.add(op.aname)
                        self.bytecode.refactorSize(curpos,op.size()-psz)
                        self.usedbuiltins.add(op.aname)
                        self.usednames.discard(op.aname)
                    elif nfo.isNative():
                        psz = op.size();
                        op.toLookupNative(nfo.idx)
                        self.refnatives.add(op.name)
                        self.bytecode.refactorSize(curpos,op.size()-psz)
                    else:
                        raise Exception("Uuuh?")
                elif op.isAttrOp():
                    name = op.getRefName()
                    op.toAttrName(env.getNameCode(name))
                    self.usedattrs.add(name)
                    self.usednames.discard(name)
                elif op.isLookupCode():
                    self.refcodes.append(op.getRefName())
                elif op.isImport():
                    self.refmodules.append(op.aname)
                elif op.isCellOp():
                    name = op.getRefName()
                    idx = env.resolveCell(name)
                    if idx<0:
                        raise Exception("Undefined Cell for name "+name)
                    if idx>255:
                        raise Exception("Too many cell names @ "+name)
                    op.toCellName(idx)

                curpos+=op.size()
        #self.argnames = [env.getNameCode(x) for x in self.argnames]
        #self.kwargnames = [env.getNameCode(x) for x in self.kwargnames]
        #print(env,self.argnames+self.kwargnames)
        self.signames = [env.getNameCode(x) for x in self.kwargnames]+[env.getNameCode(x) for x in self.argnames]#self.kwargnames+self.argnames#[env.getNameCode(x) for x in (self.kwargnames+self.argnames)]
        #print(self.signames)
        self.localnames = [env.getNameCode(x) for x in (self.scope.locals+self.scope.freevars)]
        self.localpos = [i for i,x in enumerate(self.scope.locals+self.scope.freevars)]

        #unused args!
        for i,y in enumerate(self.argpos):
            if y==None:
                nfo = env.nameInfo(self.argnames[i])
                self.argpos[i]=nfo.idx if not nfo.isDeref() else (-nfo.idx-1)
                self.sigpos[i+len(self.kwargnames)]=nfo.idx if not nfo.isDeref() else (-nfo.idx-1)#env.nameInfo(self.argnames[i]).idx

        for i,y in enumerate(self.kwargpos):
            if y==None:
                nfo = env.nameInfo(self.kwargnames[i])
                self.kwargpos[i]=nfo.idx if not nfo.isDeref() else (-nfo.idx-1)#env.nameInfo(self.kwargnames[i]).idx
                self.sigpos[i]=nfo.idx if not nfo.isDeref() else (-nfo.idx-1)#env.nameInfo(self.kwargnames[i]).idx

        self.pconstsize = 0
        self.stacksize = 0
        self.bstacksize = 0
        if self.kind!="cfun":
            # Stack Size
            self.stacksize,self.bstacksize = self.bytecode.calcStackSize()

            # Labels
            cs = 0
            for op in self.bytecode.opcodes:
                op.setLabels(self.bytecode.lab2pos, cs)
                cs += op.size()

            # Pack Consts            
            self.pconstheader=[]
            self.pconst={"int":[],"float":[],"str":[]}
            for c in self.consts:
                if isinstance(c, int):
                    pcsize =4 if (c<=0xffffffff and c>=-2147483648) else 8 
                    self.pconst["int"].append((c,pcsize))
                    # self.pconstsize += pcsize 
                elif isinstance(c, float):
                    self.pconst["float"].append((c,8))
                    # self.pconstsize += 8
                elif isinstance(c, str) or isinstance(c,bytes):
                    sz = len(c) + 2
                    sz = sz if sz % 4 == 0 else sz + (4-(sz % 4))
                    self.pconst["str"].append((c,sz))
                    # self.pconstsize += sz
            #sort pconst by size
            self.pconst["int"]=sorted(self.pconst["int"], key = lambda x: x[1])
            self.pconst["float"]=sorted(self.pconst["float"], key = lambda x: x[1])
            self.pconst["str"]=sorted(self.pconst["str"], key = lambda x: x[1])
            # build a ctable with packed consts
            self.const_table = []
            #assume cpos is aligned to 4; it will be enforce when generating bytes

            cpos = 0  
            for ctype in ["int","float","str"]:
                for cnc in self.pconst[ctype]:
                    cc,sz = cnc
                    align=0
                    if ctype!="str" and cpos%sz!=0:
                        #align int and float to boundaries
                        align=sz-(cpos%sz)
                    self.const_table.append((cpos+align,cc,sz,align))
                    self.pconstheader.append(cpos+align)
                    cpos+=sz+align
            #last cpos is full const size (actual size + alignment)
            self.pconstsize=cpos
            # align pconstheader to 8: (each element is 32bit)
            if len(self.pconstheader)%2!=0:
                # add fake constant
                self.pconstheader.append(0)
            self.pconstsize+=len(self.pconstheader)*4

            # scan opcodes and match constants
            # the index of a constant points into pconstheader for the offset
            for op in self.bytecode.opcodes:
                if op.hasConst():
                    cn = op.getConst()
                    #O(n^2) but hey, how many constants will you ever need?
                    for i,ch in enumerate(self.const_table):
                        cpos, cc, sz, aling = ch
                        if cc==cn and type(cc)==type(cn):
                            # same value, same type (in Python 1.0==1, not wanted)
                            op.resolveConst(i)
                            break
                    else:
                        fatal("Error in const table! Can't assign",cn)
            # print(self.scope)
            # print(self.pconstsize)
            # print(self.pconstheader)
            # print(self.const_table)
            # self.pconstheader=[]
            # for c in self.consts:
            #     if isinstance(c, int):
            #         if 4 not in self.pconst:
            #             self.pconst[4] = []
            #         self.pconst[4].append(c)
            #         self.pconstsize += 4
            #     elif isinstance(c, float):
            #         if 4 not in self.pconst:
            #             self.pconst[4] = []
            #         self.pconst[4].append(c)
            #         self.pconstsize += 4
            #     elif isinstance(c, str) or isinstance(c,bytes):
            #         sz = len(c) + 2
            #         sz = sz if sz % 4 == 0 else sz + (4-(sz % 4))
            #         if sz not in self.pconst:
            #             self.pconst[sz] = []
            #         self.pconst[sz].append(c)
            #         self.pconstsize += sz
            # for op in self.bytecode.opcodes:
            #     if op.hasConst():
            #         cn = op.getConst()
            #         cpos = 0
            #         for sz in sorted(self.pconst.keys()):
            #             cnst = self.pconst[sz]
            #             #if cn in cnst:
            #             ss = [(i,x) for i,x in enumerate(cnst) if x==cn and type(x)==type(cn)]
            #             if ss:
            #                 cpos += ss[0][0]*sz
            #                 #cpos += cnst.index(cn) * sz
            #                 if isinstance(cn,str) or isinstance(cn,bytes):
            #                     if cpos not in self.pconstheader:
            #                         op.resolveConst(len(self.pconstheader))
            #                         self.pconstheader.append(cpos)
            #                     else:
            #                         op.resolveConst(self.pconstheader.index(cpos))
            #                 else:
            #                     op.resolveConst(cpos)
            #                 break
            #             cpos += sz * len(cnst)
            # self.pconstsize+=len(self.pconstheader)*2


    def addConst(self, cnst):
        ss = [(i,x) for i,x in enumerate(self.consts) if x==cnst and type(x)==type(cnst)]
        if ss:
            return ss[0][0]
        self.consts.append(cnst)
        return len(self.consts) - 1

    def addName(self, name):
        if name in self.names:
            return self.names.index(name)
        self.names.append(name)
        return len(self.names) - 1

    def addRet(self):
        if len(self.bytecode.opcodes)==0 or self.bytecode.opcodes[-1].name!="RET":
            self.addCode(ByteCode().addCode(OpCode.CONST_NONE()).addCode(OpCode.RET()))
        elif len(self.bytecode.lab2pos)>0:
            lbm = max(self.bytecode.lab2pos.values())
            if lbm>=self.bytecode.size:
                self.addCode(ByteCode().addCode(OpCode.CONST_NONE()).addCode(OpCode.RET()))

    def toBytes(self):
        codetype = 0 if self.kind!="cfun" else 1
        buf = bytearray()    
        buf+=struct.pack("=B",codetype)
        buf += (struct.pack("=B", self.nargs))
        buf += (struct.pack("=B", self.nkwargs))
        buf += (struct.pack("=B", 1 if self.vargs else 0))
        
        buf += (struct.pack("=B", len(self.scope.locals)))
        buf += (struct.pack("=B", (len(self.scope.freevars)<<4)+len(self.scope.cellvars)))
        
        buf += (struct.pack("=B", self.stacksize))
        buf += (struct.pack("=B", self.bstacksize))

        buf+= struct.pack("=H", self.namecode) #name

        #precompute minitables
        if self.kind=="fun" or self.kind=="cfun":            
            #table = MiniTable(len(self.kwargnames))
            #table.putNames(self.kwargnames,self.kwargpos)
            table = MiniTable(len(self.signames))
            table.putNames(self.signames,self.sigpos)
            tablebuf = table.toBytes();
            self.bcstart = self.pconstsize+len(tablebuf)+len(self.argpos)
        elif self.kind=="class":            
            table = MiniTable(len(self.localnames))
            table.putNames(self.localnames,self.localpos)
            tablebuf = table.toBytes();
            self.bcstart = self.pconstsize+len(tablebuf)
        elif self.kind=="module":
            table = MiniTable(len(self.localnames))
            table.putNames(self.localnames,self.localpos)
            tablebuf = table.toBytes();            
            self.bcstart = self.pconstsize+len(tablebuf)


        if self.kind!="cfun":
            buf += (struct.pack("=H", len(self.pconstheader))) #nconsts
            
            self.nmstart = self.pconstsize
            
            buf += (struct.pack("=H", self.nmstart)) #nmstart
            buf += (struct.pack("=H", self.bcstart)) #bcstart
            # Consts
            #print("CONST TABLE FOR CODE",self.name)
            for cpos in self.pconstheader:
                #print("PCONSTH",len(buf),cpos)
                buf += (struct.pack("=I", cpos))
            cnsts = len(buf)
            for cpos,cn,sz,align in self.const_table:
                # add padding
                if align!=0:
                    buf+= (struct.pack("="+str(align)+"s", align*b'\x00'))
                if isinstance(cn, int):
                    #print("Int starting at",len(buf)-cnsts)
                    if sz==8:
                        try:
                            if cn<0:
                                buf += (struct.pack("=q", cn))
                            else:
                                buf += (struct.pack("=Q", cn))
                        except struct.error as e:
                            raise ValueError("Integer out of bounds")
                    else:
                        if cn<0:
                            buf += (struct.pack("=i", cn))
                        else:
                            buf += (struct.pack("=I", cn))
                elif isinstance(cn, float):
                    if cn == float('Inf'):
                        raise ValueError('Float out of bounds')
                    #print("Float starting at",len(buf)-cnsts)
                    buf += (struct.pack("=d", cn))
                elif isinstance(cn, str) or isinstance(cn,bytes):
                    #print("String starting at",len(buf)-cnsts)
                    buf += (struct.pack("=H", len(cn)))
                    if isinstance(cn,str):
                        buf+= (struct.pack("="+str(sz-2)+"s", cn.encode("utf8")))
                    else:
                        buf+= (struct.pack("="+str(sz-2)+"s", cn))
                    if len(buf)%2:
                        buf+= (struct.pack("=b", 0))
            # if self.scope.uid.startswith("__main_"):
            #     print(self.scope)
            #     print(self.const_table)
            #     print(self.pconstheader)
            # print(buf)
        else:
            buf += (struct.pack("=H", self.ccode)) #tableidx

        # if self.module!="__builtins__":
        #     print("\n\n-----------")
        #     print("MINITABLE FOR ",self.name)
        #     print(table)
        #     print("VECTORS FOR ",self.name)
        #     print("argnames",self.argnames)
        #     print("argpos",self.argpos)
        #     print("kwargnames",self.kwargnames)
        #     print("kwargpos",self.kwargpos)
        #     print("signames",self.signames)
        #     print("sigpos",self.sigpos)
        #     print("localnames",self.localnames)
        #     print("localpos",self.localpos)
        #     print("-----------\n\n")

        # Names:
        #   first the minitable
        buf+=table.toBytes()
        

        #   second the positions of positional args, only for non modules        
        if self.kind not in ("module","class"):
            for x in self.argpos:
                buf+=(struct.pack("=b",x))

        # third, bytecode if present
        if self.kind!="cfun":
            # Bytecode
            self.bytecode.toBytes(buf)

        # fourth, pad to 4
        pad = len(buf)%4
        for nop in range(0,4-pad,1):
            buf+=(struct.pack("=B", 0)) #zero pad
                                        #
        # print(self.fullname)
        # print("L:",self.usednames)
        # print("G:",self.usedglobals)
        # print("A:",self.usedattrs)
        # print("B:",self.usedbuiltins)
        return buf


class ByteCode():
    codeIds = -1

    _curcode = None

    @staticmethod
    def set_current_code(code):
        ByteCode._curcode = code

    @staticmethod
    def get_line():
        if OpCode._line_hook:
            return OpCode._line_hook()
        return -1

    def __init__(self, lineno=None, prgline=None):
        self.opcodes = []
        self.lab2pos = {}
        self.pos2lab = {}
        self.prgline = prgline
        self.lineno = lineno
        self.size = 0
        ByteCode.codeIds += 1
        self.id = ByteCode.codeIds
        self.stacksize = []
        self.bstacksize = [0]
        self.trace = []
        self.plines = {}
        if lineno:
            self.plines[lineno]=0

    def len(self):
        return len(self.opcodes)

    def last_op(self):
        return self.opcodes[-1]

    def __str__(self):
        res = ""
        curpos = 0
        for i,op in enumerate(self.opcodes):
            if curpos in self.pos2lab:
                res += ("              @" + (", ".join(self.pos2lab[curpos])) + ":\n")
            try:
                res += (" {0:<{1}}".format(self.stacksize[i], 4) + " ")
            except:
                pass
            #res += ("{:<5}{:<20}".format(str(i),str(self.trace[i])))
            res += ("{0:0{1}}".format(curpos, 6) + ". " + str(op)+"\n")
            curpos += op.size()
        if curpos in self.pos2lab:
            res += ("              @" + \
                    (", ".join(self.pos2lab[curpos])) + ":\n")
        return res

    def toDict(self):
        opcs = []
        curpos = 0
        for i,op in enumerate(self.opcodes):
            opc = [op.line,curpos,self.stacksize[i]]
            opc.extend(op.toList())
            curpos+=op.size()
            opcs.append(opc)
        jb = {
            "size":self.size,
            "opcodes": opcs
        }
        return jb

    def swapTwo(self):
        if len(self.opcodes)>=2:
            op = self.opcodes[-1]
            self.opcodes[-1] = self.opcodes[-2]
            self.opcodes[-2] = op

    def refactorSize(self,pos,delta):
        temp = dict(self.lab2pos)
        self.pos2lab = {}
        for k,v in self.lab2pos.items():
            if v>pos:
                temp[k]=v+delta
            else:
                temp[k]=v
            if temp[k] not in self.pos2lab:
                self.pos2lab[temp[k]]=set()
            self.pos2lab[temp[k]].add(k)        
        self.lab2pos = temp

    def pushBlock(self):
        self.bstacksize.append(self.bstacksize[-1]+1)

    def popBlock(self):
        self.bstacksize.append(self.bstacksize[-1]-1)

    #TODO: do it better...
    def calcBlockStackSize(self):
        bstack = [""]
        for op in self.opcodes:
            if op.isSetupLoop():
                self.pushBlock()
                bstack.append("L")
            elif op.isSetupFinally():
                self.pushBlock()
                bstack.append("F")
            elif op.isSetupExcept():
                self.pushBlock()
                bstack.append("E")
            elif op.isPopBlock():
                if bstack[-1]=="L":
                    bstack.pop()
                    self.popBlock()
            elif op.isEndFinally():                
                if bstack[-1]=="E":
                    bstack.pop()                    
                    self.popBlock()
                if bstack[-1]=="F":
                    bstack.pop()                    
                    self.popBlock()
            #print(bstack)
            #print(self.bstacksize)
        #print("BSTACKSIZE",max(self.bstacksize))
    
    def calcStackSize(self):
        self.calcBlockStackSize()
        bs = max(self.bstacksize)
        if len(self.opcodes)==0:
            return 0
        pos2op = {}
        self.stacksize = []
        pos = 0
        trace = []
        for i,op in enumerate(self.opcodes):            
            pos2op[pos]=i
            #print(i,pos,op.size(),op)
            pos+=op.size()
            trace.append({})
        #print(self.lab2pos)

        #print(self)
        trace.append({})
        trace[0][-1]=0
        for i,op in enumerate(self.opcodes): 
            #print("checking",i,op.name,"reachable from",trace[i])
            vals = list(trace[i].values())
            if not vals:
                continue
                #trace[i][i-1]=vals[0]
                #print("UNREACHABLE CODE>>",i,".",op.name)                
                #vals.append(list(trace[i-1].values())[0])

            pstack = vals[0]
            if any(x!=pstack for x in vals):
                self.trace = trace
                #print(op.name,"===>",trace[i])
                #print(self)
                #print(self.trace)
                raise Exception("Stack Mistmatch at "+str(op))

            if op.jump:
                #print(op)
                if not op.isRaise():
                    pos = self.lab2pos[op.opLabel()]
                    #print(op,pos,pos2op)
                    opn = pos2op[pos]
                    #print("    is a jump to",opn)                
                    trace[opn][i]=pstack+op.stj
                if not op.uncnd:
                    trace[i+1][i]=pstack+op.stu
                    #print("    is a jump to",i+1)
            elif op.intr:
                # break
                #print("    is a break")                                
                for j in range(i-1,0,-1):
                    if self.opcodes[j].isSetupLoop():
                        vals = list(trace[j].values())
                        pstack = vals[0]
                        pos = self.lab2pos[self.opcodes[j].opLabel()]
                        opn = pos2op[pos]
                        trace[opn][i]=pstack+op.stj
                        #print("    updating corresponding opcode at",opn)
                        break
            else:
                trace[i+1][i]=pstack+op.stu
            #print(op.name, "at", i,"=>",trace[i])
        self.trace = trace
        #print(self)
        #print(self.trace)
        mx = -1
        mn = 65535
        for i,st in enumerate(self.trace):            
            vals = list(st.values())
            sts = max(vals) if vals else 0#vals[0]
            if any(x!=sts for x in vals):
                print("WARNING: conflicting stack size!")
                #print(i,"==",st)
                #print(vals)
                #print(sts)
                #print(self)
                #raise Exception("Unknown Stack Size!!")
            self.stacksize.append(sts)
            mx = max(sts,mx)
            mn = min(sts,mn)
        if mn<0 or mx<0:
            raise Exception("Negative Stack Size!!")
        #print(">>>>",mx,mn)
        return (mx,bs) 


    def addCode(self, code):    
        if isinstance(code, ByteCode):
            if len(self.opcodes)>0 and self.opcodes[-1].name=="NOP" and len(code.opcodes)>0:
                #remove trailing nops
                #self.opcodes.pop()
                #self.stacksize.pop()
                #self.size-=1
                pass

            self.opcodes += code.opcodes
            self.stacksize+= [None]*len(code.opcodes)
            for k, v in code.lab2pos.items():
                self.lab2pos[k] = self.size + v
                np = self.size+v
                if np not in self.pos2lab:
                    self.pos2lab[np]=set()
                self.pos2lab[np].add(k)
            for pline,val in code.plines.items():
                self.plines[pline]=val+self.size
            self.size += code.size
        elif isinstance(code, OpCode):
            if len(self.opcodes)>0 and self.opcodes[-1].name=="NOP":
                #remove trailing nops
                #self.opcodes.pop()
                #self.stacksize.pop()
                #self.size-=1
                pass
            self.opcodes.append(code)
            self.stacksize.append(None)
            self.size += code.size()
        else:
            for ll in code:
                self.addCode(ll)
        return self

    def addLabel(self, lab):
        pos = self.size
        label = lab + "_" + str(self.id)
        self.lab2pos[label] = pos
        if pos not in self.pos2lab:
            self.pos2lab[pos]=set()
        self.pos2lab[pos].add(label)
        return self

    def toBytes(self,buf):
        for op in self.opcodes:
            op.toBytes(buf)


class CodeReprElement():
    def __init__(self):
        self.bpos = 0
        self.line = 0
        self.label = None
        self.prgline = None
        self.opcode = None
        self.prm = None
        self.val = None
        self.pline = 0
    def __str__(self):
        return "{:<12} {:<3} {:>6}".format(self.opcode,(str(self.prm.val) if self.prm!=None else ""),(str(self.val) if self.val!=None else ""))
    def toDict(self):
        return {
            "bpos":self.bpos,
            "line":self.line,
            "label":list(self.label) if self.label else None,
            "prgline":self.prgline,
            "opcode":self.opcode,
            "prm":self.prm.toDict() if self.prm else None,
            "val":self.val if not isinstance(self.val,bytes) else _tohex(self.val),
            "pline":self.pline
        }

class CodeRepr():
    def __init__(self):
        self.map = {}
        self.lines = []
        self.consts = []
        self.locals = []
        self.freevars = []
        self.name = ""  
    def makeFromByteCode(self,code,prglines={}):
        curpos = 0
        for op in code.opcodes:
            cre = CodeReprElement()
            cre.bpos = curpos
            cre.line = len(self.lines)
            cre.label = code.pos2lab[curpos] if curpos in code.pos2lab else None
            cre.opcode = op.name
            cre.prm = None if op.params==[] else op.params[0]
            cre.val = op.augVal()
            cre.pline = -1
            for pline in sorted(prglines):
                if prglines[pline]<=curpos:
                    cre.pline=pline
                else:
                    break

            self.lines.append(curpos)
            self.map[curpos]=cre
            curpos+=op.size()
    def makeFromCode(self,code):
        self.consts = code.consts
        self.stacksize = code.stacksize
        self.bcodesize = code.bytecode.size
        self.args = code.argnames
        self.kwargs = code.kwargnames
        self.locals = code.scope.locals
        self.freevars = code.scope.freevars
        self.name = code.fullname
        self.filename = code.srcfile
        self.prglines = code.prglines
        self.makeFromByteCode(code.bytecode,self.prglines)
    def toIndex(self):
        ret = {
            "src":self.filename,
            "lines":self.prglines
        }
        return ret
    def toDict(self):
        return {
            "src":self.filename,
            "lines":{-1 if k is None else k:v for k,v in self.prglines.items()},
            "consts": [x if not isinstance(x,bytes) else _tohex(x) for x in self.consts],
            "stacksize":self.stacksize,
            "bcodesize":self.bcodesize,
            "args":self.args,
            "kwargs":self.kwargs,
            "locals":self.locals,
            "freevars":self.freevars,
            "name":self.name,
            "items": [
                self.map[k].toDict() for k in sorted(self.map)
            ]
        }
