from base import *
import ast
import struct
import os
from collections import OrderedDict

class Var():

    def __init__(self, name):
        self.val = name
        self.size = 1

class Var2():

    def __init__(self, name):
        self.val = name
        self.size = 2



class Label():

    def __init__(self, name, codeid):
        self.label = name
        self.size = 2
        self.codeid = codeid

    def getLabel(self):
        return self.label + "_" + str(self.codeid)

    def toDict(self):
        return {
            "name":self.label,
            "size":self.size,
            "codeid":self.codeid,
            "label":self.getLabel()
        }

class Byte():

    def __init__(self, n):
        self.val = n
        self.size = 1

    def toBytes(self, bar):
        bar += (struct.pack("=B", self.val & 0xff))

    def __str__(self):
        return "B(" + str(self.val) + ")" + str(hex(id(self)))

    def toDict(self):
        return {"byte":self.val}

class Short():

    def __init__(self, n):
        self.val = n
        self.size = 2

    def toBytes(self, bar):
        bar += (struct.pack("=H", self.val & 0xffff))

    def toDict(self):
        return {"short":self.val}


class Word():

    def __init__(self, n):
        self.val = n
        self.size = 4

    def toBytes(self, bar):
        bar += (struct.pack("=I", self.val & 0xffffffff))

    def toDict(self):
        return {"word":self.val}


class Double():

    def __init__(self, n):
        self.val = n
        self.size = 8

    def toBytes(self, bar):
        bar += (struct.pack("=d", self.val & 0xffffffffffffffff))

    def toDict(self):
        return {"double":self.val}


bytecodemap = {}


def genByteCodeMap():
    global bytecodemap
    fname = os.path.join(env.stdlib,"__lang","opcodes.h")
    f = open(fname)
    lines = f.readlines()
    for txt in lines:
        tmp = txt.replace("\t", " ")
        flds = tmp.split()
        if len(flds) >= 3 and flds[0] == "#define" and not (flds[1].startswith("_") or flds[1].startswith("NAME_")):
            bytecodemap[flds[1]] = Byte(int(flds[2], 16))
            #print("{} = {}/{}".format(flds[1],flds[2],str(bmap[flds[1]])))


# TODO: all opcodes must be single param! remove param list from OpCode
class OpCode():

    _line_hook = None

    @staticmethod
    def set_line_hook(hook):
        OpCode._line_hook = hook

    @staticmethod
    def get_line():
        if OpCode._line_hook:
            return OpCode._line_hook()
        return -1


    def __init__(self, name="", params=None):
        self.name = name
        self.params = [] if params == None else params
        self.code = -1
        self.bytecode = Byte(0)
        self.aconst = None
        self.aname = None
        self.alabel = None
        # stack usage
        self.stu = 0
        self.stj = 0
        # stack jump op
        self.jump = False
        self.uncnd = False
        self.intr = False
        self.line = OpCode.get_line()

    def __str__(self):
        res = "{:<15}".format(self.name)
        if self.aconst != None:
            res += " {:<6}{:>15}*".format(
                str("unresolved" if self.params == [] else self.params[0].val), str(self.aconst).replace("\n", "\\n"))
        elif self.aname != None:
            res += " {:<6}{:>15}*".format(
                str("unresolved" if self.params == [] else self.params[0].val), str(self.aname).replace("\n", "\\n"))
        elif self.alabel != None:
            res += " {:<6}{:>15}*".format(
                str("unresolved" if self.params == [] else str(self.params[0].val)), "to " + str(self.alabel).replace("\n", "\\n"))
        else:
            if len(self.params) > 0:
                if isinstance(self.params[0], Label):
                    res += " {:<6}{:>15}*".format(
                        str("unresolved" if self.params == [] else str(self.params[0].getLabel())), "")
                else:
                    res += " {:<6}{:>15}*".format(
                        str("unresolved" if self.params == [] else str(self.params[0].val)), "")
        return res

    def toList(self):
        res = [self.name]
        if len(self.params)>0:
            res.append(self.params[0].val)
        else:
            res.append(None)
        if self.aconst != None:
            res.append(str(self.aconst).replace("\n", "\\n"))
        elif self.aname != None:
            res.append(str(self.aname).replace("\n", "\\n"))
        elif self.alabel != None:
            res.append(str(self.alabel).replace("\n", "\\n"))
        else:
            res.append("")
        return res


    def augVal(self):
        if self.aconst != None:
            return self.aconst
        elif self.aname != None:
            return self.aname
        elif self.alabel != None:
            return self.alabel
        return None

    def opLabel(self):
        return self.params[0].getLabel()

    def isRefOp(self):
        return self.name == "LOAD" or self.name == "STORE" or self.name == "DEL"

    def isCellOp(self):
        return self.name == "MAKE_CELL"

    def isBuildException(self):
        return self.name == "BUILD_EXCEPTION"

    def isAttrOp(self):
        return "_ATTR" in self.name

    def isGlobalOp(self):
        return "_GLOBAL" in self.name

    def isLookupCode(self):
        return self.name=="LOOKUP_CODE"

    def isImport(self):
        return "IMPORT_NAME" in self.name

    def isLookupBuiltin(self):
        return "LOOKUP_BUILTIN" in self.name

    def isLookupNative(self):
        return "LOOKUP_NATIVE" in self.name

    def isSetupLoop(self):
        return "SETUP_LOOP"==self.name

    def isSetupExcept(self):
        return "SETUP_EXCEPT"==self.name

    def isSetupFinally(self):
        return "SETUP_FINALLY"==self.name

    def isEndFinally(self):
        return "END_FINALLY"==self.name

    def isRaise(self):
        return "RAISE"==self.name

    def isPopBlock(self):
        return "POP_BLOCK"==self.name   

    def isBreakOrContinue(self):
        return "BREAK"==self.name or "CONTINUE"==self.name

    def isFinalizedLoad(self):
        return "LOAD_" in self.name and not "SUBSCR" in self.name
        #self.name == "LOAD_FAST" or self.name == "LOAD_ATTR" or self.name == "LOAD_GLOBAL" or self.name == "LOAD_BUILTIN"

    def getRefName(self):
        return self.params[0].val

    def toBuildException(self,idx):
        self.params[0]=Short(idx)

    def toAttrName(self, idx):
        if self.isAttrOp():
            self.params[0] = Short(idx)

    def toFastName(self, idx):
        if self.isRefOp():
            self.name += "_FAST"
            self.params[0] = Byte(idx)

    def toGlobalName(self, idx):
        if self.isRefOp():
            self.name += "_GLOBAL"
            self.params[0] = Byte(idx)

    def toLookupBuiltin(self):
        if self.isRefOp():
            self.name = "LOOKUP_BUILTIN"
            self.params[0] = Short(self.fn(self.aname))

    def toLookupNative(self, idx):
        if self.isRefOp():
            self.name = "LOOKUP_NATIVE"
            self.params[0] = Short(idx)

    def toDerefName(self, idx):
        if self.isRefOp():
            self.name += "_DEREF"
            self.params[0] = Byte(idx)
    
    def toCellName(self, idx):
        if self.isCellOp():
            self.params[0] = Byte(idx)

    def hasConst(self):
        return self.aconst != None

    def getConst(self):
        return self.aconst

    def resolveConst(self, n):
        if self.aconst != None:
            try:
                self.params[0] = (Short(n))
            except:
                self.params.append((Short(n)))

    def hasName(self):
        return self.aname != None

    def getName(self):
        return self.aname

    def resolveName(self, n):
        self.params[0] = Short(n)

    def strprms(self):
        res = ""
        if self.aconst != None:
            res += " {0} = {1}".format(
                str("unresolved" if self.params == [] else self.params[0].val), str(self.aconst).replace("\n", "\\n"))
        elif self.aname != None:
            res += " {0} = {1}".format(
                str("unresolved" if self.params == [] else self.params[0].val), str(self.aname).replace("\n", "\\n"))
        else:
            for p in self.params:
                if isinstance(p, Label):
                    res += ' ' + p.getLabel(self.code)
                else:
                    res += ' ' + str(p.val)
        return res

    def size(self):
        res = 1
        for p in self.params:
            res += p.size
        return res

    def toBytes(self, bar):
        OpCode.getByteCode(self).toBytes(bar)
        for p in self.params:
            p.toBytes(bar)

    def setParentCode(self, code):
        self.code = code.myCode

    def setConst(self, lc):
        self.params[0] = Short(lc[self.params[0].val])
        return self

    def setLabels(self, lc, cs):
        for i, p in enumerate(self.params):
            if isinstance(p, Label):
                if self.name=="CONTINUE":
                    self.params[i] = Short(lc[p.getLabel()])
                else:
                    self.params[i] = Short(lc[p.getLabel()] - cs - self.size())
                self.alabel = lc[p.getLabel()]

    def isRet(self):
        return self.name == "RET" or self.name == "RETN"

    @staticmethod
    def getByteCode(opcode):
        global bytecodemap
        return bytecodemap[opcode.name]

    @staticmethod
    def NOP():
        opc = OpCode("NOP")
        opc.stu = 0
        return opc

    @staticmethod
    def STOP():
        opc = OpCode("STOP")
        opc.stu = 0
        return opc

    @staticmethod
    def BEGIN_MODULE(nglobs):
        return OpCode("BEGIN_MODULE", [Byte(nglobs)])

    @staticmethod
    def END_MODULE():
        return OpCode("END_MODULE")

    @staticmethod
    def LOOKUP_CODE(idx, name):
        opc = OpCode("LOOKUP_CODE", [Short(idx)])
        opc.aname = name
        opc.stu = 1
        return opc

    @staticmethod
    def LOOKUP_DYNCODE(idx, name):
        opc = OpCode("LOOKUP_DYNCODE", [Short(idx)])
        opc.aname = name
        opc.stu = 1
        return opc

    @staticmethod
    def LOOKUP_NAME(idx, name):
        opc = OpCode("LOOKUP_NAME", [Short(idx)])
        opc.aname = name
        opc.stu = 1
        return opc

    @staticmethod
    def CONST_NONE():
        opc = OpCode("CONST_NONE")
        opc.stu = 1
        return opc

    @staticmethod
    def CONST_TRUE():
        opc = OpCode("CONST_TRUE")
        opc.stu = 1
        return opc

    @staticmethod
    def CONST_FALSE():
        opc = OpCode("CONST_FALSE")
        opc.stu = 1
        return opc

    @staticmethod
    def MAKE_CELL(name):
        opc = OpCode("MAKE_CELL",[Var(name)])
        opc.stu = 1
        opc.aname = name
        return opc

    @staticmethod
    def CONST(val):
            if isinstance(val, int):
                if val == 1:
                    opc = OpCode("CONSTI_1")
                elif val == -1:
                    opc = OpCode("CONSTI_M1")
                elif val == 0:
                    opc = OpCode("CONSTI_0")
                else:
                    # Need to pass byte for size() to be correct
                    if val<0:
                        #signed constant
                        if val<-2147483648:  #less than -2^31 => it's 64 bits
                            opc = OpCode("CONSTI64", [Short(0)])
                        else:
                            opc = OpCode("CONSTI", [Short(0)])
                    else:
                        #unsigned constant
                        if val>0xffffffff:  #greater then max uint32_t => it's64 bits
                            opc = OpCode("CONSTU64", [Short(0)])
                        else:
                            opc = OpCode("CONSTU", [Short(0)])
                    opc.aconst = val
                opc.stu = 1
                return opc
            elif isinstance(val, float):
                if val == 1.0:
                    opc = OpCode("CONSTF_1")
                elif val == 0.0:
                    opc = OpCode("CONSTF_0")
                else:
                    # Need to pass byte for size() to be correct
                    opc = OpCode("CONSTF", [Short(0)])
                    opc.aconst = val
                opc.stu = 1
                return opc
            elif isinstance(val, str):
                if val == "":
                    opc = OpCode("CONSTS_0")
                elif val == " ":
                    opc = OpCode("CONSTS_S")
                elif val == "\n":
                    opc = OpCode("CONSTS_N")
                else:
                    # Need to pass byte for size() to be correct
                    opc = OpCode("CONSTS", [Short(0)])
                    opc.aconst = val
                opc.stu = 1
                return opc
            elif isinstance(val, bytes):
                # Need to pass byte for size() to be correct
                opc = OpCode("CONSTB", [Short(0)])
                opc.aconst = val
                opc.stu = 1
                return opc
            else:
                raise Exception("Wrong CONST Argument!")

    @staticmethod
    def BUILD_LIST(n):
        opc = OpCode("BUILD_LIST", [Short(n)])
        #opc.stu = -(n&0x7f) + 1 if n<0x80 else -(n&0x7f)
        opc.stu = 1 if n<0x8000 else -((n&0x7fff)>>11)-1
        return opc

    @staticmethod
    def BUILD_TUPLE(n):
        #opc = OpCode("BUILD_TUPLE", [Short(n)])
        #opc.stu = -n + 1
        opc = OpCode("BUILD_TUPLE", [Short(n)])
        opc.stu = 1 if n<0x8000 else -((n&0x7fff)>>11)-1
        return opc

    @staticmethod
    def BUILD_SLICE():
        opc = OpCode("BUILD_SLICE")
        opc.stu = -2
        return opc

    @staticmethod
    def BUILD_DICT(n):
        opc = OpCode("BUILD_DICT", [Short(n)])
        opc.stu = 1
        return opc

    @staticmethod
    def BUILD_SET(n):
        return OpCode("BUILD_SET", [Short(n)])

    @staticmethod
    def BUILD_CLASS(nparents):
        lst = [Byte(nparents)]
        opc = OpCode("BUILD_CLASS", lst)
        opc.stu = -(nparents+1)
        return opc

    @staticmethod
    def BUILD_EXCEPTION(idx):
        lst = [Short(idx)]
        opc = OpCode("BUILD_EXCEPTION", lst)
        opc.stu = 1
        return opc

    @staticmethod
    def CHECK_EXCEPTION(idx):
        lst = [Short(idx)]
        opc = OpCode("CHECK_EXCEPTION", lst)
        opc.stu = 0
        return opc

    @staticmethod
    def END_CLASS():
        return OpCode("END_CLASS")

    @staticmethod
    def ADD():
        opc = OpCode("ADD")
        opc.stu = -1
        return opc

    @staticmethod
    def SUB():
        opc = OpCode("SUB")
        opc.stu = -1
        return opc

    @staticmethod
    def MUL():
        opc = OpCode("MUL")
        opc.stu = -1
        return opc

    @staticmethod
    def DIV():
        opc = OpCode("DIV")
        opc.stu = -1
        return opc

    @staticmethod
    def FDIV():
        opc = OpCode("FDIV")
        opc.stu = -1
        return opc

    @staticmethod
    def MOD():
        opc = OpCode("MOD")
        opc.stu = -1
        return opc

    @staticmethod
    def POW():
        opc = OpCode("POW")
        opc.stu = -1
        return opc

    @staticmethod
    def LSHIFT():
        opc = OpCode("LSHIFT")
        opc.stu = -1
        return opc

    @staticmethod
    def RSHIFT():
        opc = OpCode("RSHIFT")
        opc.stu = -1
        return opc

    @staticmethod
    def BIT_OR():
        opc = OpCode("BIT_OR")
        opc.stu = -1
        return opc

    @staticmethod
    def BIT_XOR():
        opc = OpCode("BIT_XOR")
        opc.stu = -1
        return opc

    @staticmethod
    def BIT_AND():
        opc = OpCode("BIT_AND")
        opc.stu = -1
        return opc

    @staticmethod
    def I_ADD():
        opc = OpCode("IADD")
        opc.stu = -1
        return opc

    @staticmethod
    def I_SUB():
        opc = OpCode("ISUB")
        opc.stu = -1
        return opc

    @staticmethod
    def I_MUL():
        opc = OpCode("IMUL")
        opc.stu = -1
        return opc

    @staticmethod
    def I_DIV():
        opc = OpCode("IDIV")
        opc.stu = -1
        return opc

    @staticmethod
    def I_FDIV():
        opc = OpCode("IFDIV")
        opc.stu = -1
        return opc

    @staticmethod
    def I_MOD():
        opc = OpCode("IMOD")
        opc.stu = -1
        return opc

    @staticmethod
    def I_POW():
        opc = OpCode("IPOW")
        opc.stu = -1
        return opc

    @staticmethod
    def I_LSHIFT():
        opc = OpCode("ILSHIFT")
        opc.stu = -1
        return opc

    @staticmethod
    def I_RSHIFT():
        opc = OpCode("IRSHIFT")
        opc.stu = -1
        return opc

    @staticmethod
    def I_BIT_OR():
        opc = OpCode("IBIT_OR")
        opc.stu = -1
        return opc

    @staticmethod
    def I_BIT_XOR():
        opc = OpCode("IBIT_XOR")
        opc.stu = -1
        return opc

    @staticmethod
    def I_BIT_AND():
        opc = OpCode("IBIT_AND")
        opc.stu = -1
        return opc

    @staticmethod
    def UPOS():
        return OpCode("UPOS")

    @staticmethod
    def UNEG():
        opc = OpCode("UNEG")
        opc.stu = 0
        return opc

    @staticmethod
    def NOT():
        return OpCode("NOT")

    @staticmethod
    def INVERT():
        return OpCode("INVERT")

    @staticmethod
    def L_AND():
        opc = OpCode("L_AND")
        opc.stu = -1
        return opc

    @staticmethod
    def L_OR():
        opc = OpCode("L_OR")
        opc.stu = -1
        return opc

    @staticmethod
    def EQ():
        opc = OpCode("EQ")
        opc.stu = -1
        return opc

    @staticmethod
    def NOT_EQ():
        opc = OpCode("NOT_EQ")
        opc.stu = -1
        return opc

    @staticmethod
    def LT():
        opc = OpCode("LT")
        opc.stu = -1
        return opc

    @staticmethod
    def LTE():
        opc = OpCode("LTE")
        opc.stu = -1
        return opc

    @staticmethod
    def GT():
        opc = OpCode("GT")
        opc.stu = -1
        return opc

    @staticmethod
    def GTE():
        opc = OpCode("GTE")
        opc.stu = -1
        return opc

    @staticmethod
    def IS():
        opc = OpCode("IS")
        opc.stu = -1
        return opc

    @staticmethod
    def IS_NOT():
        opc = OpCode("IS_NOT")
        opc.stu = -1
        return opc

    @staticmethod
    def IN():
        opc = OpCode("IN")
        opc.stu = -1
        return opc

    @staticmethod
    def IN_NOT():
        opc = OpCode("IN_NOT")
        opc.stu = -1
        return opc

    @staticmethod
    def JUMP_IF_TRUE(label, codeid):
        opc = OpCode("JUMP_IF_TRUE", [Label(label, codeid)])
        opc.jump = True
        opc.stu = -1
        opc.stj = 0
        return opc

    @staticmethod
    def JUMP_IF_FALSE(label, codeid):
        opc = OpCode("JUMP_IF_FALSE", [Label(label, codeid)])
        opc.jump = True
        opc.stu = -1
        opc.stj = 0
        return opc

    @staticmethod
    def LOAD(name,fn=None):
        if name == None:
            raise Exception("Undefined Name!! " + str(name))
        opc = OpCode("LOAD", [Var(name)])
        opc.aname = name
        opc.fn = fn
        opc.stu = 1
        return opc        
    @staticmethod
    def STORE(name,fn=None):
        if name == None:
            raise Exception("Undefined Name!! " + name)
        opc = OpCode("STORE", [Var(name)])
        opc.aname = name
        opc.stu = -1
        opc.fn = fn
        return opc

        # if name.isLocal():
        #     opc = OpCode("STORE_FAST", [Byte(name.idx)])
        #     opc.aname = name.name
        #     return opc
        # elif name.isGlobal():
        #     opc = OpCode("STORE_GLOBAL", [Byte(name.idx)])
        #     opc.aname = name.name
        #     return opc
        # elif name.isBuiltin():
        #     opc = OpCode("STORE_BUILTIN", [Byte(name.idx)])
        #     opc.aname = name.name
        #     return opc
        # else:
        #     opc = OpCode("STORE_DEREF", [Byte(name.idx)])
        #     opc.aname = name.name
        #     return opc

    @staticmethod
    def DEL(name,fn=None):
        if name == None:
            raise Exception("Undefined Name!! " + name)
        opc = OpCode("DEL", [Var(name)])
        opc.aname = name
        opc.stu = 0
        opc.fn = fn
        return opc

        # if name.isLocal():
        #     opc = OpCode("DELETE_FAST", [Byte(name.idx)])
        #     opc.aname = name.name
        #     return opc
        # elif name.isGlobal():
        #     opc = OpCode("DELETE_GLOBAL", [Byte(name.idx)])
        #     opc.aname = name.name
        #     return opc
        # elif name.isBuiltin():
        #     opc = OpCode("DELETE_BUILTIN", [Byte(name.idx)])
        #     opc.aname = name.name
        #     return opc
        # else:
        #     opc = OpCode("DELETE_DEREF", [Byte(name.idx)])
        #     opc.aname = name.name
        #     return opc
    @staticmethod
    def STORE_SUBSCR():
        opc = OpCode("STORE_SUBSCR")
        opc.stu = -3
        return opc

    @staticmethod
    def LOAD_SUBSCR():
        opc = OpCode("LOAD_SUBSCR")
        opc.stu = -1
        return opc

    @staticmethod
    def DELETE_SUBSCR():
        opc = OpCode("DELETE_SUBSCR")
        opc.stu = -2
        return opc

    @staticmethod
    def STORE_ATTR(name):
        opc = OpCode("STORE_ATTR", [Var2(name)])
        opc.aname = name
        opc.stu=-2
        return opc

    @staticmethod
    def LOOKUP_BUILTIN(name):
        opc = OpCode("LOOKUP_BUILTIN", [Short(name)])
        opc.stu = 1
        return opc

    @staticmethod
    def LOOKUP_NATIVE(name):
        opc = OpCode("LOOKUP_NATIVE", [Short(name)])
        opc.stu = 1
        return opc

    @staticmethod
    def LOAD_ATTR(name):
        opc = OpCode("LOAD_ATTR", [Var2(name)])
        opc.aname = name
        opc.stu=0
        return opc

    @staticmethod
    def DEL_ATTR(name):
        opc = OpCode("DELETE_ATTR", [Var2(name)])
        opc.aname = name
        opc.stu=-1
        return opc

    @staticmethod
    def IMPORT_NAME(idx,name):
        opc =OpCode("IMPORT_NAME", [Short(idx)])
        opc.aname = name
        opc.stu = 1
        return opc

    @staticmethod
    def IMPORT_FROM(idx):
        return OpCode("IMPORT_FROM", [Short(idx)])

    @staticmethod
    def IMPORT_BUILTINS():
        opc = OpCode("IMPORT_BUILTINS")
        opc.stu=1
        return opc

    @staticmethod
    def DUP():
        opc = OpCode("DUP")
        opc.stu = 1
        return opc

    @staticmethod
    def DUP_TWO():
        opc = OpCode("DUP_TWO")
        opc.stu = 2
        return opc

    @staticmethod
    def ROT_THREE():
        return OpCode("ROT_THREE")

    @staticmethod
    def ROT_TWO():
        return OpCode("ROT_TWO")

    @staticmethod
    def POP():
        opc = OpCode("POP")
        opc.stu = -1
        return opc

    @staticmethod
    def IF_TRUE(label, codeid):
        opc = OpCode("IF_TRUE", [Label(label, codeid)])
        opc.stu = -1
        opc.jump = True
        opc.stj = -1
        return opc

    @staticmethod
    def IF_FALSE(label, codeid):
        opc = OpCode("IF_FALSE", [Label(label, codeid)])
        opc.stu = -1
        opc.jump = True
        opc.stj = -1
        return opc

    @staticmethod
    def FOR_ITER(label, codeid):
        opc = OpCode("FOR_ITER", [Label(label, codeid)])
        opc.stu = 1
        opc.jump = True
        opc.stj = -1
        return opc

    @staticmethod
    def GET_ITER():
        return OpCode("GET_ITER")

    @staticmethod
    def JUMP(label, codeid):
        opc = OpCode("JUMP", [Label(label, codeid)])
        opc.jump = True
        opc.stj = 0
        opc.stu = 0
        opc.uncnd = True
        return opc

    @staticmethod
    def SETUP_EXCEPT(j1,codeid):
        opc = OpCode("SETUP_EXCEPT", [Label(j1,codeid)])
        opc.jump = True
        opc.stj = 2
        opc.stu = 1
        return opc

    @staticmethod
    def POP_EXCEPT():
        opc = OpCode("POP_EXCEPT")
        return opc

    @staticmethod
    def SETUP_FINALLY(j1,codeid):
        opc = OpCode("SETUP_FINALLY", [Label(j1,codeid)])
        opc.jump = True
        opc.stj = 2
        opc.stu = 0
        return opc

    @staticmethod
    def END_FINALLY():
        opc = OpCode("END_FINALLY")
        #opc.jump = True
        opc.stu = -2
        return opc

    @staticmethod
    def RAISE():
        opc= OpCode("RAISE")
        opc.stu=0
        opc.jump=True
        opc.uncnd=True
        return opc

    @staticmethod
    def SETUP_LOOP(j1, codeid):
        opc = OpCode("SETUP_LOOP", [Label(j1, codeid)])
        opc.stu = 0
        opc.stj = 0
        opc.jump = True
        return opc

    @staticmethod
    def POP_BLOCK():
        return OpCode("POP_BLOCK")

    @staticmethod
    def BREAK():
        opc = OpCode("BREAK")
        opc.intr = True
        return opc

    @staticmethod
    def CONTINUE(label, codeid):
        opc = OpCode("CONTINUE", [Label(label, codeid)])
        opc.jump = True
        opc.uncnd = True
        return opc

    @staticmethod
    def MAKE_FUNCTION(nargs):
        opc = OpCode("MAKE_FUNCTION", [Short(nargs)])
        opc.stu = -(nargs & 0xff) - ((nargs >> 8)) - 1 + 1
        return opc

    @staticmethod
    def MAKE_CLOSURE(nargs):
        opc = OpCode("MAKE_CLOSURE", [Short(nargs)])
        opc.stu = -(nargs & 0xff) - ((nargs >> 8)) - 1 + 1
        return opc

    @staticmethod
    def CALL(nargs, kargs):
        opc = OpCode("CALL", [Short(nargs + (kargs << 8))])
        opc.stu = -(nargs + 2 * kargs + 1) + 1
        return opc

    @staticmethod
    def CALL_VAR(nargs, kargs):
        opc = OpCode("CALL_VAR", [Short(nargs + (kargs << 8))])
        opc.stu = -(nargs + 2 * kargs + 1 + 1) + 1
        return opc

    @staticmethod
    def RET():
        opc = OpCode("RET")
        opc.stu = -1
        return opc

    @staticmethod
    def RETN():
        return OpCode("RETN")

    @staticmethod
    def UNPACK(n):
        opc = OpCode("UNPACK", [Byte(n)])
        opc.stu=n-1
        return opc

    @staticmethod
    def MAP_STORE(n):
        opc =  OpCode("MAP_STORE",[Byte(n)])
        opc.stu = -2
        return opc
    @staticmethod
    def LIST_STORE(n):
        opc =  OpCode("LIST_STORE",[Byte(n)])
        opc.stu = -1
        return opc
