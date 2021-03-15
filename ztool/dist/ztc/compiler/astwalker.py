import ast
from compiler.code import ByteCode, CodeObj
from compiler.opcode import OpCode
from compiler.env import Name, Env, Scope
from collections import OrderedDict
import sys
from ast import *
import os
import os.path

from compiler.exceptions import *


class AstWalker(ast.NodeVisitor):

    def __init__(self, prg, hooks, filename, modulename="__main__",scopes=None):
        self.codes = []
        self.codequeue = []
        self.code = None
        self.prg = prg.split("\n")
        self.continue_label = []
        self.modulename = modulename
        self.hooks = hooks
        self.env = hooks.getEnvHook()
        self.imports = set()
        self.atendmodule = False
        self.scopes = scopes
        self.filename = filename
        self.builtins_module = "__builtins__"
        self.special_names = ["__builtins__","__module__"]
        self.cbase = os.path.split(filename)[0]
        self.curline = -1

    def opcode_hook(self):
        return self.curline

    def setup_emitter(self,node=None):
        OpCode.set_line_hook(self.opcode_hook)
        if node and hasattr(node,"lineno"):
            self.curline=node.lineno

    def prgLine(self, n):
        return self.prg[n - 1]

    def pushCode(self, code):
        self.codes.append(code)
        self.code = code
        return self.code

    def pushCodeObj(self, name, kind, nargs, kwargs, vargs,cls=None,ccode=None):
        e = CodeObj(name, kind, self.hooks.numCodeHook(),
                    nargs, kwargs, vargs, self.modulename,cls,ccode,self.filename)
        self.codes.append(e)
        self.code = e
        self.hooks.pushCodeHook(e)
        if kind == "module":
            self.hooks.putModuleCode(name, e)
        return self.code

    def addNameType(self,name,type):
        pass
        # if self.code:
        #     self.code.addNameType(name,type)

    def addUsedName(self,name):
        pass
        # if self.code:
        #     self.code.addUsedName(name)

    def popCodeObj(self):
        self.codes.pop()
        try:
            self.code = self.codes[-1]
        except:
            self.code = None

    def pushBlock(self):
        self.code.pushBlock()

    def popBlock(self):
        self.code.popBlock()

    def getBlocks(self):
        return self.code.getBlocks()

    def popBlock(self):
        pass

    def genCodeList(self, clist):
        listcode = []
        for cc in clist:
            listcode.append(self.visit(cc))
        return listcode

    def visit_Module(self, node):
        self.setup_emitter(node)
        self.env.addNameCode(self.modulename)
        self.env.pushScope(self.modulename)
        self.atendmodule = False
        self.pushCodeObj(self.modulename, "module", 0, 0, 0)
        self.addNameType(self.modulename,"module")
        for stmt in node.body:
            self.code.addCode(self.visit(stmt))
        self.code.addCode(OpCode.STOP())
        # print(self.env)
        self.atendmodule = True
        self.generateCodeObjs()
        if self.scopes:
            self.code.finalize(self.env)
        self.popCodeObj()
        self.env.popScope()

    def visit_Import(self, node):
        self.setup_emitter(node)
        code = ByteCode(node.lineno, self.prgLine(node.lineno))
        for alias in node.names:
            if not self.hooks.shouldGenerateModule(alias.name):
                continue
            try:
                mod = self.hooks.getModuleCode(alias.name)
            except:
                self.hooks.importHook(alias.name,node.lineno,self.filename)
                mod = self.hooks.getModuleCode(alias.name)

            if alias.name == self.builtins_module and self.modulename == "__main__":
                code.addCode(OpCode.IMPORT_BUILTINS())
                code.addCode(OpCode.POP())
                return code
            # don't import builtins, they are loaded in __main__
            if alias.name == self.builtins_module:
                return code
            if alias.asname == None:
                self.env.putName(alias.name)
                self.addNameType(alias.name,"module")
                code.addCode(OpCode.IMPORT_NAME(mod.idx, alias.name))
                code.addCode(OpCode.STORE(alias.name, self.hooks.getBuiltinCoding))
            else:
                self.env.putName(alias.asname)
                self.addNameType(alias.asname,"module")
                code.addCode(OpCode.IMPORT_NAME(mod.idx, alias.asname))
                code.addCode(OpCode.STORE(alias.asname, self.hooks.getBuiltinCoding))
        return code

    def visit_ImportFrom(self, node):
        self.setup_emitter(node)
        code = ByteCode(node.lineno, self.prgLine(node.lineno))
        for alias in node.names:
            modname = node.module+"."+alias.name
            if not self.hooks.shouldGenerateModule(modname):
                continue
            try:
                mod = self.hooks.getModuleCode(modname)
            except:
                self.hooks.importHook(modname,node.lineno,self.filename)
                mod = self.hooks.getModuleCode(modname)
            if alias.asname == None:
                #raise CUnsupportedFeatureError(node.lineno, node.col_offset,self.filename, node.__class__.__name__)
                alias.asname = alias.name
            #else:
            self.env.putName(alias.asname)
            self.addNameType(alias.asname,"module")
            code.addCode(OpCode.IMPORT_NAME(mod.idx, alias.asname))
            code.addCode(OpCode.STORE(alias.asname, self.hooks.getBuiltinCoding))
        return code

    def visit_None(self, node):
        self.setup_emitter(node)
        return ByteCode().addCode(OpCode.CONST_NONE())

    def visit_Num(self, node):
        self.setup_emitter(node)
        return ByteCode().addCode(OpCode.CONST(node.n))

    def visit_Str(self, node):
        self.setup_emitter(node)
        return ByteCode().addCode(OpCode.CONST(node.s))

    def visit_Bytes(self, node):
        self.setup_emitter(node)
        return ByteCode().addCode(OpCode.CONST(node.s))

    def visit_keyword(self, node):
        code = ByteCode()
        # vr = self.namestore.putName(node.arg)
        # val = self.pushConst(vr)
        # code.addCode(OpCode.NAME(val, node, node.arg))
        # code.addCode(self.visit(node.value))
        return code

    def visit_List(self, node):
        self.setup_emitter(node)
        code = ByteCode()
        ll = len(node.elts)
        if ll>0x7fff:
            raise CUnsupportedFeatureError(node.lineno,node.col_offset,self.filename,"Lists specified in code must be not longer than 32768 elements!")
        code.addCode(OpCode.BUILD_LIST(ll))
        for x in range(0,ll,16):
            to = min(x+16,ll)
            code.addCode(self.genCodeList(node.elts[x:to]))
            code.addCode(OpCode.BUILD_LIST( ((to-x-1)<<11)|(x//16)|0x8000) )
        #code.addCode(OpCode.BUILD_LIST(len(node.elts)))
        return code

    def visit_Tuple(self, node):
        self.setup_emitter(node)
        code = ByteCode()
        ll = len(node.elts)
        if ll>0x7fff:
            raise CUnsupportedFeatureError(node.lineno,node.col_offset,self.filename,"Tuples specified in code must be not longer than 32768 elements!")
        code.addCode(OpCode.BUILD_TUPLE(ll))
        for x in range(0,ll,16):
            to = min(x+16,ll)
            code.addCode(self.genCodeList(node.elts[x:to]))
            code.addCode(OpCode.BUILD_TUPLE( ((to-x-1)<<11)|(x//16)|0x8000))
        return code

    def visit_Dict(self, node):
        self.setup_emitter(node)
        code = ByteCode()
        code.addCode(OpCode.BUILD_DICT(len(node.keys)))
        for i, key in enumerate(node.keys):
            code.addCode(self.visit(key))
            code.addCode(self.visit(node.values[i]))
            code.addCode(OpCode.MAP_STORE(0))
        return code

    def visit_Set(self, node):
        self.setup_emitter(node)
        code = ByteCode()
        for i, item in enumerate(node.elts):
            code.addCode(self.visit(item))
        code.addCode(OpCode.BUILD_SET(len(node.elts)))
        return code

    def visit_Expr(self, node):
        self.setup_emitter(node)
        code = ByteCode()
        code.addCode(self.visit(node.value))
        #Remove lonely new_exception
        if code.len()==1 and code.last_op().isBuildException():
            return ByteCode()
        code.addCode(OpCode.POP())
        return code

    def visit_BinOp(self, node):
        self.setup_emitter(node)
        left = node.left
        right = node.right
        op = node.op
        leftcode = self.visit(left)
        rightcode = self.visit(right)
        code = ByteCode()
        code.addCode(leftcode)
        code.addCode(rightcode)
        self.addBINOP(op, code)
        return code

    def visit_UnaryOp(self, node):
        self.setup_emitter(node)
        operand = node.operand
        op = node.op
        if isinstance(op, ast.USub) and isinstance(operand, ast.Num):
            return ByteCode().addCode(OpCode.CONST(-operand.n))
        code = ByteCode()
        operandcode = self.visit(operand)
        code.addCode(operandcode)
        self.addUNARYOP(op, code)
        return code

    def visit_BoolOp(self, node):
        self.setup_emitter(node)
        values = node.values
        op = node.op
        code = ByteCode()
        code.addCode(self.visit(values[0]))
        for num, val in enumerate(values[1:]):
            if isinstance(op, ast.And):
                code.addCode(
                    OpCode.JUMP_IF_FALSE("shorter_evaluation", code.id))
                code.addCode(self.visit(val))
            elif isinstance(op, ast.Or):
                code.addCode(
                    OpCode.JUMP_IF_TRUE("shorter_evaluation", code.id))
                code.addCode(self.visit(val))
        code.addLabel("shorter_evaluation")
        return code

    def visit_IfExp(self,node):
        self.setup_emitter(node)
        code = ByteCode()
        code.addCode(self.visit(node.test))
        code.addCode(OpCode.IF_FALSE("false",code.id))
        code.addCode(self.visit(node.body))
        code.addCode(OpCode.JUMP("endif",code.id))
        code.addLabel("false")
        code.addCode(self.visit(node.orelse))
        code.addLabel("endif")
        return code

    def visit_Compare(self, node):
        self.setup_emitter(node)
        code = ByteCode()
        leftcode = self.visit(node.left)
        code.addCode(leftcode)
        if len(node.ops) > 1:
            for num, op in enumerate(node.ops):
                code.addCode(
                    self.visit(node.comparators[num]))  # compcodes[num])
                code.addCode(OpCode.DUP())
                code.addCode(OpCode.ROT_THREE())
                self.addCOMPAREOP(op, code)
                if num < len(node.ops) - 1:
                    code.addCode(
                        OpCode.JUMP_IF_FALSE("end_comparison", code.id))
                # if num < len(node.ops) - 1:
                #    code.addCode(OpCode.POP())
            code.addLabel("end_comparison")
            code.addCode(OpCode.ROT_TWO())
            code.addCode(OpCode.POP())
        else:
            code.addCode(self.visit(node.comparators[0]))
            self.addCOMPAREOP(node.ops[0], code)
        return code

    def loadName(self,node):
        name = self.env.loadName(node.id)
        if not name:
            name = self.env.loadName(node.id,asGlobal=True)
            if not name:
                raise CNameError(node.lineno,node.col_offset,self.filename,"local name "+node.id+" reference but never assigned!")
        return name

    def visit_Name(self, node):
        self.setup_emitter(node)
        try:
            if node.id == "None":
                return self.visit_None(node)
            if isinstance(node.ctx, ast.Load):
                if node.id in self.special_names:
                    return ByteCode().addCode(OpCode.LOOKUP_BUILTIN(256+self.special_names.index(node.id)))
                name = self.env.getName(node.id)
                #name = self.loadName(node)
                bcode = ByteCode().addCode(
                    OpCode.LOAD(name, self.hooks.getBuiltinCoding))
                self.addUsedName(name)
                return bcode
            elif isinstance(node.ctx, ast.Store):
                if node.id in self.special_names:
                    raise CUnsupportedFeatureError(node.lineno,node.col_offset,self.filename,"Can't store reserved named!")
                name = self.env.putName(node.id)
                #print("@STORE",name,self.env)
                if self.modulename == self.builtins_module and self.env.atGlobalScope():
                    self.hooks.saveBuiltinNameInfo(name)
                    self.env.addBuiltin(name)
                bcode = ByteCode().addCode(OpCode.STORE(name, self.hooks.getBuiltinCoding))
                return bcode
            elif isinstance(node.ctx, ast.Del):
                if node.id in self.special_names:
                    raise CUnsupportedFeatureError(node.lineno,node.col_offset,self.filename,"Can't delete reserved names!")
                name = self.env.getName(node.id)
                return Code().addCode(OpCode.DEL(name, self.hooks.getBuiltinCoding))
        except CError:
            raise
        except:
            #print("==>",self.prgLine(node.lineno))
            raise CNameError(node.lineno,node.col_offset,self.filename,node.id)

    def visit_NameConstant(self, node):
        self.setup_emitter(node)
        if node.value == None:
            return ByteCode().addCode(OpCode.CONST_NONE())
        elif node.value == True:
            return ByteCode().addCode(OpCode.CONST_TRUE())
        elif node.value == False:
            return ByteCode().addCode(OpCode.CONST_FALSE())
        else:
            raise CNameConstantError(node.lineno,node.col_offset,self.filename)

    def visit_Attribute(self, node):
        self.setup_emitter(node)
        code = ByteCode()
        valuecode = self.visit(node.value)
        self.env.addNameCode(node.attr)
        self.addUsedName(node.attr)

        code.addCode(valuecode)
        if isinstance(node.ctx, ast.Load):
            code.addCode(OpCode.LOAD_ATTR(node.attr))
        elif isinstance(node.ctx, ast.Store):
            code.addCode(OpCode.STORE_ATTR(node.attr))
        elif isinstance(node.ctx, ast.Del):
            code.addCode(OpCode.DEL_ATTR(node.attr))
        return code

    def visit_Subscript(self, node):
        self.setup_emitter(node)
        code = ByteCode()
        code.addCode(self.visit(node.value))
        code.addCode(self.visit(node.slice))
        if isinstance(node.ctx, ast.Store):
            code.addCode(OpCode.STORE_SUBSCR())
        elif isinstance(node.ctx, ast.Load):
            code.addCode(OpCode.LOAD_SUBSCR())
        else:
            code.addCode(OpCode.DELETE_SUBSCR())
        return code

    def visit_Index(self, node):
        self.setup_emitter(node)
        code = ByteCode()
        code.addCode(self.visit(node.value))
        return code

    def visit_Slice(self, node):
        self.setup_emitter(node)
        code = ByteCode()
        code.addCode(OpCode.CONST_NONE() if node.lower == None else self.visit(node.lower))
        code.addCode(OpCode.CONST_NONE() if node.upper == None else self.visit(node.upper))
        code.addCode(OpCode.CONST_NONE() if node.step == None else self.visit(node.step))
        code.addCode(OpCode.BUILD_SLICE())
        return code

    def visit_Global(self,node):
        self.setup_emitter(node)
        for x in node.names:
            self.env.putName(x,asGlobal=True)
        #print("@GLOBAL",self.env)
        return ByteCode()

    def visit_Nonlocal(self,node):
        self.setup_emitter(node)
        for x in node.names:
            self.env.putName(x,asNonLocal=True)
        #print("@NONLOCAL",self.env)
        return ByteCode()

    def gen_comp(self,chs,nchs,tch):
        ch = chs.pop(0)
        if not isinstance(ch,ast.comprehension):
            raise CUnsupportedFeatureError(tch.lineno,tch.col_offset,self.filename,"no generators allowed in comprehensions")
        code = ByteCode()
        code.addCode(OpCode.SETUP_LOOP("lc_exitfor", code.id))
        code.addCode(self.visit(ch.iter))
        code.addCode(OpCode.GET_ITER())
        code.addLabel("lc_beginfor")
        code.addCode(OpCode.FOR_ITER("lc_endfor", code.id))
        if isinstance(ch.target,ast.Tuple):
            code.addCode(OpCode.UNPACK(len(ch.target.elts)))
            for nn in ch.target.elts:
                code.addCode(self.visit(nn))
        else:
            code.addCode(self.visit(ch.target))
        if ch.ifs:
            if len(ch.ifs)>1:
                raise CUnsupportedFeatureError(tch.lineno,tch.col_offset,self.filename,"comprehensions support is just for one if or less")
            code.addCode(self.visit(ch.ifs[0]))
            code.addCode(OpCode.IF_FALSE("lc_beginfor",code.id))
        if chs:
            #still comprehensions in the list
            code.addCode(self.gen_comp(chs,expr,nchs))
        else:
            #no more comprehensions
            if isinstance(tch,ast.ListComp):
                code.addCode(self.visit(tch.elt))
                code.addCode(OpCode.LIST_STORE(nchs))
            else:
                code.addCode(self.visit(tch.key))
                code.addCode(self.visit(tch.value))
                code.addCode(OpCode.MAP_STORE(nchs))
        code.addCode(OpCode.JUMP("lc_beginfor", code.id))
        code.addLabel("lc_endfor")
        code.addCode(OpCode.POP_BLOCK())
        code.addLabel("lc_exitfor")
        return code

    def visit_ListComp(self,node):
        self.setup_emitter(node)
        code = ByteCode()
        code.addCode(OpCode.BUILD_LIST(0))
        chs = list(node.generators)
        code.addCode(self.gen_comp(chs,len(chs),node))
        return code

    def visit_DictComp(self,node):
        self.setup_emitter(node)
        code = ByteCode()
        code.addCode(OpCode.BUILD_DICT(0))
        chs = list(node.generators)
        code.addCode(self.gen_comp(chs,len(chs),node))
        return code


    def generic_visit(self, node):
        self.setup_emitter(node)
        raise CUnsupportedFeatureError(node.lineno, node.col_offset,self.filename, node.__class__.__name__)
        super().generic_visit(node)

    def visit_Assign(self, node):
        self.setup_emitter(node)
        #visit only, to get the names
        #backup current code
        code_copy = self.code
        self.code = None
        codes_copy = self.codes
        self.codes = []
        for num, vv in enumerate(node.targets):
            if isinstance(vv,ast.Tuple):
                for nn in vv.elts:
                    self.visit(nn)
            else:
                self.visit(vv)
        self.code = code_copy
        self.codes = codes_copy

        #evaluate left
        valuecode = self.visit(node.value)
        code = ByteCode(node.lineno, self.prgLine(node.lineno))
        code.addCode(valuecode)
        for i in range(0,len(node.targets)-1):
            code.addCode(OpCode.DUP())

        for num, vv in enumerate(node.targets):
            if isinstance(vv,ast.Tuple):
                code.addCode(OpCode.UNPACK(len(vv.elts)))
                for nn in vv.elts:
                    code.addCode(self.visit(nn))
            else:
                code.addCode(self.visit(vv))
        return code

    def visit_AugAssign(self, node):
        self.setup_emitter(node)
        code = ByteCode(node.lineno,self.prgLine(node.lineno))

        code.addLabel("aug_assign")
        node.target.ctx=ast.Load()
        code.addCode(self.visit(node.target))
        if isinstance(node.target,ast.Attribute):
            code.addCode(OpCode.DUP())
            attrname = node.target.attr
            code.swapTwo()
        elif isinstance(node.target,ast.Subscript):
            code.addCode(OpCode.DUP_TWO())
            code.swapTwo()
        elif isinstance(node.target,ast.Name):
            pass
        else:
            raise CUnsupportedFeatureError(node.lineno,node.col_offset,self.filename,node.target.__class__.__name__)

        node.target.ctx=ast.Store()

        code.addCode(self.visit(node.value))

        self.addINPLACE(node.op,code)
        if isinstance(node.target, ast.Name):
            code.addCode(self.visit(node.target))
        elif isinstance(node.target, ast.Attribute):
            code.addCode(OpCode.ROT_TWO())
            code.addCode(OpCode.STORE_ATTR(attrname))
        elif isinstance(node.target, ast.Subscript):
            code.addCode(OpCode.ROT_THREE())
            code.addCode(OpCode.STORE_SUBSCR())
        return code

    def visit_Delete(self, node):
        self.setup_emitter(node)
        code = ByteCode(node.lineno, self.prgLine(node.lineno))
        for x in node.targets:
            if isinstance(x,ast.Subscript):
                code.addCode(self.visit(x))
            elif isinstance(x,ast.Name):
                code.addCode(self.visit(x))
            else:
                raise CUnsupportedFeatureError(node.lineno,node.col_offset,self.filename,"del not supported for this type!")
        return code

    def visit_If(self, node):
        self.setup_emitter(node)
        code = ByteCode(node.lineno, self.prgLine(node.lineno))
        testcode = self.visit(node.test)
        code.addCode(testcode)
        if len(node.orelse) > 0:
            code.addCode(OpCode.IF_FALSE("else", code.id))
            bodycode = self.genCodeList(node.body)
            code.addCode(bodycode)
            code.addCode(OpCode.JUMP("endif", code.id))
            code.addLabel("else")
            elsecode = self.genCodeList(node.orelse)
            code.addCode(elsecode)
            code.addLabel("endif")
            #code.addCode(OpCode.NOP())
        else:
            code.addCode(OpCode.IF_FALSE("endif", code.id))
            bodycode = self.genCodeList(node.body)
            code.addCode(bodycode)
            code.addLabel("endif")
            #code.addCode(OpCode.NOP())
        return code

    def visit_For(self, node):
        self.setup_emitter(node)
        code = ByteCode(node.lineno,self.prgLine(node.lineno))
        itercode = self.visit(node.iter)
        self.pushBlock()
        code.addCode(OpCode.SETUP_LOOP("exitfor", code.id))
        code.addCode(itercode)
        code.addCode(OpCode.GET_ITER())
        code.addLabel("beginfor")
        self.continue_label.append(("beginfor", code.id))
        code.addCode(OpCode.FOR_ITER("endfor", code.id))
        if isinstance(node.target,ast.Tuple):
            code.addCode(OpCode.UNPACK(len(node.target.elts)))
            for nn in node.target.elts:
                code.addCode(self.visit(nn))
        else:
            code.addCode(self.visit(node.target))
        code.addCode(self.genCodeList(node.body))
        code.addCode(OpCode.JUMP("beginfor", code.id))
        code.addLabel("endfor")
        self.continue_label.pop()
        code.addCode(OpCode.POP_BLOCK())
        self.popBlock()
        code.addCode(self.genCodeList(node.orelse))
        code.addLabel("exitfor")
        code.addCode(OpCode.NOP())
        return code

    def visit_While(self, node):
        self.setup_emitter(node)
        code = ByteCode(node.lineno,self.prgLine(node.lineno))
        testcode = self.visit(node.test)
        self.pushBlock()
        code.addCode(OpCode.SETUP_LOOP("exit_while", code.id))
        code.addLabel("test_while")
        self.continue_label.append(("test_while", code.id))
        code.addCode(testcode)
        code.addCode(OpCode.IF_FALSE("end_while", code.id))
        code.addCode(self.genCodeList(node.body))
        code.addCode(OpCode.JUMP("test_while", code.id))
        code.addLabel("end_while")
        self.continue_label.pop()
        code.addCode(OpCode.POP_BLOCK())
        self.popBlock()
        code.addCode(self.genCodeList(node.orelse))
        code.addLabel("exit_while")
        code.addCode(OpCode.NOP())
        return code

    def visit_Break(self, node):
        self.setup_emitter(node)
        code = ByteCode(node.lineno,self.prgLine(node.lineno))
        code.addCode(OpCode.BREAK())
        return code

    def visit_Continue(self, node):
        self.setup_emitter(node)
        code = ByteCode(node.lineno,self.prgLine(node.lineno))
        code.addCode(
            OpCode.CONTINUE(self.continue_label[-1][0], self.continue_label[-1][1]))
        return code

    def visit_Return(self, node):
        self.setup_emitter(node)
        code = ByteCode(node.lineno,self.prgLine(node.lineno))
        if node.value is None:
            code.addCode(OpCode.CONST_NONE())
            code.addCode(OpCode.RET())
        else:
            code.addCode(self.visit(node.value))
            code.addCode(OpCode.RET())
        return code

    def isBuiltinFun(self, f):
        for x in f.decorator_list:
            if isinstance(x,ast.Name) and x.id == "builtin":
                return True
        return False

    def isNativeC(self, f):
        for x in f.decorator_list:
            if isinstance(x,ast.Call) and (x.func.id == "native_c" or x.func.id == "c_native"):
                res = []
                vbl = []
                prms = []
                for s in x.args[1].elts:
                    res.append(s.s)
                if len(x.args)>=3:
                    for s in x.args[2].elts:
                        vbl.append(s.s)
                if len(x.args)==4:
                    for s in x.args[3].elts:
                        prms.append(s.s)
                return (x.args[0].s,res,vbl,prms)
        return False


    def visit_Pass(self,node):
        self.setup_emitter(node)
        code = ByteCode(node.lineno,self.prgLine(node.lineno))
        code.addCode(OpCode.NOP())
        return code

    def visit_ClassDef(self,node):
        self.setup_emitter(node)
        if not self.env.atGlobalScope():
            raise CUnsupportedFeatureError(node.lineno,node.col_offset,self.filename,"No nested classes!")
        code = ByteCode(node.lineno,self.prgLine(node.lineno))

        if self.isBuiltinFun(node):
            self.env.addBuiltin(node.name)
            self.hooks.saveBuiltinInfo(node.name, self.hooks.numCodeHook(), (0,0,0))
        # add function name to env

        for b in node.bases:
            if isinstance(b,ast.Name):
                if self.env.getName(b.id)==None:
                    raise CNameError(node.lineno,node.col_offset,self.filename,b.id)
                code.addCode(OpCode.LOAD(b.id,self.hooks.getBuiltinCoding))
                self.addUsedName(b.id)
            elif isinstance(b,ast.Attribute):
                code.addCode(self.visit_Attribute(b))

        self.env.putName(node.name)
        self.env.addNameCode(node.name)
        self.addNameType(node.name,"class")

        code.addCode(OpCode.LOOKUP_NAME(self.env.getNameCode(node.name),node.name))

        # create new CodeObj for class body because i need code.idx...
        self.pushCodeObj(node.name, "class", 0,0,0,cls=node.name)

        # load CodeObj to stack & make function in previous code
        code.addCode(OpCode.LOOKUP_CODE(self.code.idx, self.code.name))
        code.addCode(OpCode.BUILD_CLASS(len(node.bases)))
        code.addCode(OpCode.STORE(node.name, self.hooks.getBuiltinCoding))

        # put pushed code object in code queue to be generated at end of
        # current scope
        self.codequeue.append((self.code, (node, 0, 0, 0), "class"))
        self.popCodeObj()
        return code

    def visit_FunctionDef(self, node):
        self.setup_emitter(node)
        code = ByteCode(node.lineno,self.prgLine(node.lineno))
        args = node.args.args
        vargs = node.args.vararg
        defs = node.args.defaults
        kwargs = node.args.kwonlyargs
        kwdd = node.args.kw_defaults

        if node.args.kwarg!=None:
            raise CUnsupportedFeatureError(node.lineno,node.col_offset,self.filename,"*kwargs")

        if not self.hooks.shouldGenerateCodeFor(node.name, self.modulename):
            return code

        if self.isBuiltinFun(node):
            self.env.addBuiltin(node.name)
            self.hooks.saveBuiltinInfo(node.name, self.hooks.numCodeHook(), (
                len(defs), len(kwdd), 1 if vargs != None else 0))

        # Generate code for defaults
        defscode = self.genCodeList(defs)
        code.addCode(defscode)

        # Generate code for kwdefaults
        kwdeflen = 0
        for i, dd in enumerate(kwdd):
            if dd != None:
                self.env.addNameCode(kwargs[i].arg)
                self.addNameType(kwargs[i].arg,"kwarg")
                code.addCode(
                    OpCode.LOOKUP_NAME(self.env.getNameCode(kwargs[i].arg), kwargs[i].arg))
                code.addCode(self.visit(dd))
                kwdeflen += 1

        # add function name to env
        self.env.putName(node.name)
        self.addNameType(node.name,"function")


        #ncodeargs = (len(kwargs)<<8)+len(args)
        nfunargs = (kwdeflen << 8) + len(defs)

        ncfprms = self.isNativeC(node)
        if not ncfprms:
            ftype = "fun"
            cidx = None
        else:
            ftype = "cfun"
            self.hooks.addCThings(ncfprms[0],[os.path.join(self.cbase,f) for f in ncfprms[1]],ncfprms[2],ncfprms[3],fbase=self.cbase)
            cidx = self.hooks.decodeCNative(ncfprms[0])
            if cidx<0:
                raise CUnknownNative(node.lineno,node.col_offset,self.filename,ncfprms[0]+" should be somewhere in "+str(ncfprms[1]))

        # create new CodeObj for function body because i need code.idx...
        self.pushCodeObj(node.name, ftype, len(args), len(kwargs), vargs != None,ccode=cidx)

        # load CodeObj to stack & make function in previous code
        code.addCode(OpCode.LOOKUP_CODE(self.code.idx, self.code.name))
        # put pushed code object in code queue to be generated at end of
        # current scope
        self.codequeue.append((self.code, (node, args, vargs, kwargs), ftype))
        self.popCodeObj()

        if self.scopes:
            scope = self.scopes[Scope.getid(node.name,self.env.getScope().uid)]["scope"]
            if scope.hasNonlocalNames():
                code.addCode(OpCode.BUILD_TUPLE(len(cellvars)))
                cellvars = scope.cellvars
                for cell in cellvars:
                    code.addCode(OpCode.MAKE_CELL(cell))
                code.addCode(OpCode.BUILD_TUPLE(len(cellvars)|0x8000))
                code.addCode(OpCode.MAKE_CLOSURE(nfunargs))
            else:
                code.addCode(OpCode.MAKE_FUNCTION(nfunargs))
        else:
            code.addCode(OpCode.MAKE_FUNCTION(nfunargs))
        code.addCode(OpCode.STORE(node.name, self.hooks.getBuiltinCoding))
        return code

    def generateCodeObjs(self):
        codelist = self.codequeue
        self.codequeue = []
        for cx in codelist:
            code = cx[0]
            kind = cx[2]
            cargs = cx[1]

            if kind == "fun":
                # Generate Function CodeObj code
                self.pushCode(code)

                node = cargs[0]
                args = cargs[1]
                vargs = cargs[2]
                kwargs = cargs[3]
                self.env.pushScope(code.name)

                # add parameters name to scope
                for nn in args:
                    self.env.putArg(nn.arg)
                    self.code.addArgName(nn.arg)
                if vargs != None:
                    self.env.putArg(vargs.arg)
                    self.code.addArgName(vargs.arg)
                for nn in kwargs:
                    self.env.putArg(nn.arg)
                    self.code.addKwArgName(nn.arg)

                fcode = ByteCode()
                fcode.addCode(self.genCodeList(node.body))
                if node.body:
                    self.code.firstline = node.body[0].lineno
                    self.code.lastline = node.body[-1].lineno
                self.code.addCode(fcode)
                self.code.addRet()
                self.generateCodeObjs()
                if self.scopes:
                    self.code.finalize(self.env)
                self.code.eblocks = self.getBlocks()
                self.popCodeObj()
                self.env.popScope()
            elif kind == "cfun":
                # Generate cfun as fun without body
                # Generate Function CodeObj code
                self.pushCode(code)

                node = cargs[0]
                args = cargs[1]
                vargs = cargs[2]
                kwargs = cargs[3]
                self.env.pushScope(code.name)

                # add parameters name to scope
                for nn in args:
                    self.env.putArg(nn.arg)
                    self.code.addArgName(nn.arg)
                if vargs != None:
                    self.env.putArg(vargs.arg)
                    self.code.addArgName(vargs.arg)
                for nn in kwargs:
                    self.env.putArg(nn.arg)
                    self.code.addKwArgName(nn.arg)
                if self.scopes:
                    self.code.finalize(self.env)
                self.popCodeObj()
                self.env.popScope()
            elif kind == "class":
                # Generate Class CodeObj code
                self.pushCode(code)
                node = cargs[0]
                self.env.pushScope(code.name)
                fcode = ByteCode()
                fcode.addCode(self.genCodeList(node.body))
                self.code.addCode(fcode)
                self.code.addCode(OpCode.END_CLASS())
                #print("SCOPE AT END CLASS",self.env.getScope())
                self.env.getScope().forget()
                #print("SCOPE AT END CLASS AFTER FORGET",self.env.getScope())
                self.generateCodeObjs()
                #print("SCOPE AT END GENERATE",self.env.getScope())
                self.env.getScope().remember()
                #print("SCOPE AT END GENERATE AFTER REMEMBER",self.env.getScope())
                if self.scopes:
                    self.code.finalize(self.env)
                self.popCodeObj()
                self.env.popScope()

    def visit_new_exception(self,node):
        self.setup_emitter(node)
        code = ByteCode(node.lineno,self.prgLine(node.lineno))
        if len(node.args)==2:
            excmsg=""
        elif len(node.args)==3:
            if not isinstance(node.args[2],ast.Str):
                raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"new_exception: third parameter must be a string")
            excmsg=node.args[2].s
        else:
            raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"new_exception: need at least 2 arguments and at most 3")

        if (not isinstance(node.args[0],ast.Name)) or (not isinstance(node.args[1],ast.Name)):
            raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"new_exception: need names as argument 1 and 2")
        if not self.env.hasException(node.args[1].id):
            if node.args[1].id!="Exception":
                raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"new_exception: parent not defined")
            else:
                self.env.addException(node.args[1].id,node.args[1].id)
        ename = self.env.addNameCode(node.args[0].id)
        self.addNameType(node.args[0].id,"exception")
        #pname = self.env.getNameCode(node.args[1].id)
        self.env.addException(node.args[0].id,node.args[1].id,excmsg)
        code.addCode(OpCode.BUILD_EXCEPTION(ename))
        return code

    def visit_nameof(self,node):
        self.setup_emitter(node)
        code = ByteCode(node.lineno,self.prgLine(node.lineno))
        if len(node.args)!=1:
            raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"__nameof: needs one argument")
        if (not isinstance(node.args[0],ast.Name)):
            raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"__nameof: need a name as argument")
        try:
            ename = self.env.getNameCode(node.args[0].id)
        except:
            raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"__nameof: unknown name "+node.args[0].id)

        code.addCode(OpCode.CONST(ename))
        return code

    def visit_new_resource(self,node):
        self.setup_emitter(node)
        code = ByteCode(node.lineno,self.prgLine(node.lineno))
        if len(node.args)!=1:
            raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"new_resource: needs one argument")
        if not isinstance(node.args[0],ast.Str):
            raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"new_resource: needs a string argument")
        rc = self.hooks.addResource(node.args[0].s)
        if rc<0:
            raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"new_resource: "+node.args[0].s+" does not exist!")
        code.addCode(OpCode.LOOKUP_CODE(rc,node.args[0].s))
        return code

    def visit_fnattr(self,node,fn):
        self.setup_emitter(node)
        code = ByteCode(node.lineno,self.prgLine(node.lineno))
        nargs = 2
        if fn =="setattr":
            nargs=3
        if len(node.args)!=nargs:
            raise CWrongSyntax(node.lineno,node.col_offset,self.filename,fn+" needs "+str(nargs)+" arguments")
        if not isinstance(node.args[1],ast.Str):
            raise CWrongSyntax(node.lineno,node.col_offset,self.filename,fn+" needs a string literal as second argument")
        code.addCode(self.visit(node.func))
        code.addCode(self.visit(node.args[0]))
        code.addCode(OpCode.LOOKUP_NAME(self.env.addNameCode(node.args[1].s), node.args[1].s))
        if fn=="setattr":
            code.addCode(self.visit(node.args[2]))

        code.addCode(OpCode.CALL(nargs, 0))
        return code


    def visit_fnprep(self,node,fn):
        self.setup_emitter(node)
        code = ByteCode(node.lineno,self.prgLine(node.lineno))
        if fn=="__ORD":
            if len(node.args)>1 or (not isinstance(node.args[0],ast.Str)) or len(node.args[0].s)>1:
                raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"__ORD needs one string argument of len <=1"+astdump(node))
            code.addCode(OpCode.CONST(ord(node.args[0].s)))
        return code

    def visit_Call(self, node):
        self.setup_emitter(node)
        #Check for modified builtin calls
        if isinstance(node.func,ast.Name) and node.func.id=="new_exception":
            return self.visit_new_exception(node)
        if isinstance(node.func,ast.Name) and node.func.id=="getattr":
            return self.visit_fnattr(node,"getattr")
        if isinstance(node.func,ast.Name) and node.func.id=="setattr":
            return self.visit_fnattr(node,"setattr")
        if isinstance(node.func,ast.Name) and node.func.id=="hasattr":
            return self.visit_fnattr(node,"hasattr")
        if isinstance(node.func,ast.Name) and node.func.id in ("__ORD",):
            return self.visit_fnprep(node,node.func.id)
        if isinstance(node.func,ast.Name) and node.func.id=="new_resource":
            return self.visit_new_resource(node)
        if isinstance(node.func,ast.Name) and node.func.id=="__nameof":
            return self.visit_nameof(node)

        #normal call
        code = ByteCode(node.lineno,self.prgLine(node.lineno))
        code.addCode(self.visit(node.func))

        # update for Python 3.5 -_-
        starargs = [arg for arg in node.args if isinstance(arg,ast.Starred)]
        pargs = [arg for arg in node.args if not isinstance(arg,ast.Starred)]
        code.addCode(self.genCodeList(pargs))
        for kw in node.keywords:
            #TODO: check for kw.arg!=None --> changed in Python 3.5
            code.addCode(
                OpCode.LOOKUP_NAME(self.env.addNameCode(kw.arg), kw.arg))
            code.addCode(self.visit(kw.value))
        if starargs:
            #print(starargs)
            starcode = self.genCodeList(starargs) #self.visit(starargs)
            code.addCode(starcode)
            code.addCode(OpCode.CALL_VAR(len(pargs), len(node.keywords)))
        else:
            code.addCode(OpCode.CALL(len(pargs), len(node.keywords)))
        return code

    def visit_Starred(self,node):
        return self.visit(node.value)

    def visit_Try(self,node):
        self.setup_emitter(node)
        code = ByteCode(node.lineno,self.prgLine(node.lineno))

        #setup blocks
        if node.finalbody:
            self.pushBlock()
            code.addCode(OpCode.SETUP_FINALLY("finally",code.id))
        self.pushBlock()
        code.addCode(OpCode.SETUP_EXCEPT("handlers",code.id))
        code.addCode(self.genCodeList(node.body))

        code.addCode(OpCode.POP_BLOCK())
        self.popBlock()
        if node.orelse:
            code.addCode(OpCode.JUMP("orelse",code.id))
        else:
            code.addCode(OpCode.JUMP("safe_exit",code.id))

        code.addLabel("handlers")
        if node.handlers:
            for i,h in enumerate(node.handlers,1):
                code.addLabel("handler"+str(i))
                if h.type:
                    if not self.env.hasException(h.type.id):
                        raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"except needs an exception name")
                    ename = self.env.getNameCode(h.type.id)
                    if h.name:
                        code.addCode(OpCode.DUP())
                        code.addCode(self.visit_Name(ast.Name(id=h.name,ctx=ast.Store())))
                    code.addCode(OpCode.DUP())
                    code.addCode(OpCode.CHECK_EXCEPTION(ename))

                        #code.addCode(OpCode.STORE(h.name, self.hooks.getBuiltinCoding))
                    if i == len(node.handlers):
                        code.addCode(OpCode.IF_FALSE("unhandled",code.id))
                    else:
                        code.addCode(OpCode.IF_FALSE("handler"+str(i+1),code.id))
                code.addCode(OpCode.POP())
                code.addCode(OpCode.POP_EXCEPT())
                code.addCode(self.genCodeList(h.body))
                code.addCode(OpCode.JUMP("safe_exit",code.id))

        if node.orelse:
            code.addLabel("orelse")
            code.addCode(self.genCodeList(node.orelse))
            code.addCode(OpCode.JUMP("safe_exit",code.id))
        code.addLabel("unhandled")
        code.addCode(OpCode.POP_EXCEPT())
        code.addCode(OpCode.JUMP("finally",code.id))
        code.addLabel("safe_exit")
        code.addCode(OpCode.CONST_NONE())
        code.addLabel("finally")
        if node.finalbody:
            code.addCode(OpCode.POP_BLOCK())
            self.popBlock()
            code.addCode(self.genCodeList(node.finalbody))
        code.addCode(OpCode.END_FINALLY())
        self.popBlock()

        return code

    def visit_Raise(self, node):
        self.setup_emitter(node)
        code = ByteCode(node.lineno,self.prgLine(node.lineno))
        if node.cause!=None:
            raise CUnsupportedFeatureError(node.lineno,node.col_offset,self.filename,"Raise does not support a cause")
        if isinstance(node.exc, ast.Name) and self.env.hasException(node.exc.id):
            code.addCode(OpCode.BUILD_EXCEPTION(self.env.getNameCode(node.exc.id)))
        else:
            code.addCode(self.visit(node.exc))
        code.addCode(OpCode.RAISE())
        return code


    def addBINOP(self, op, code):
        if isinstance(op, ast.Add):
            code.addCode(OpCode.ADD())
        elif isinstance(op, ast.Sub):
            code.addCode(OpCode.SUB())
        elif isinstance(op, ast.Mult):
            code.addCode(OpCode.MUL())
        elif isinstance(op, ast.Div):
            code.addCode(OpCode.DIV())
        elif isinstance(op, ast.FloorDiv):
            code.addCode(OpCode.FDIV())
        elif isinstance(op, ast.Mod):
            code.addCode(OpCode.MOD())
        elif isinstance(op, ast.Pow):
            code.addCode(OpCode.POW())
        elif isinstance(op, ast.LShift):
            code.addCode(OpCode.LSHIFT())
        elif isinstance(op, ast.RShift):
            code.addCode(OpCode.RSHIFT())
        elif isinstance(op, ast.BitOr):
            code.addCode(OpCode.BIT_OR())
        elif isinstance(op, ast.BitXor):
            code.addCode(OpCode.BIT_XOR())
        elif isinstance(op, ast.BitAnd):
            code.addCode(OpCode.BIT_AND())
        elif isinstance(op, ast.And):
            code.addCode(OpCode.L_AND())
        elif isinstance(op, ast.Or):
            code.addCode(OpCode.L_OR())

        return self

    def addINPLACE(self, op, code):
        if isinstance(op, ast.Add):
            code.addCode(OpCode.I_ADD())
        elif isinstance(op, ast.Sub):
            code.addCode(OpCode.I_SUB())
        elif isinstance(op, ast.Mult):
            code.addCode(OpCode.I_MUL())
        elif isinstance(op, ast.Div):
            code.addCode(OpCode.I_DIV())
        elif isinstance(op, ast.FloorDiv):
            code.addCode(OpCode.I_FDIV())
        elif isinstance(op, ast.Mod):
            code.addCode(OpCode.I_MOD())
        elif isinstance(op, ast.Pow):
            code.addCode(OpCode.I_POW())
        elif isinstance(op, ast.LShift):
            code.addCode(OpCode.I_LSHIFT())
        elif isinstance(op, ast.RShift):
            code.addCode(OpCode.I_RSHIFT())
        elif isinstance(op, ast.BitOr):
            code.addCode(OpCode.I_BIT_OR())
        elif isinstance(op, ast.BitXor):
            code.addCode(OpCode.I_BIT_XOR())
        elif isinstance(op, ast.BitAnd):
            code.addCode(OpCode.I_BIT_AND())

    def addUNARYOP(self, op, code):
        if isinstance(op, ast.UAdd):
            code.addCode(OpCode.UADD())
        elif isinstance(op, ast.USub):
            code.addCode(OpCode.UNEG())
        elif isinstance(op, ast.Not):
            code.addCode(OpCode.NOT())
        elif isinstance(op, ast.Invert):
            code.addCode(OpCode.INVERT())

    def addCOMPAREOP(self, op, code):
        if isinstance(op, ast.Eq):
            code.addCode(OpCode.EQ())
        elif isinstance(op, ast.NotEq):
            code.addCode(OpCode.NOT_EQ())
        elif isinstance(op, ast.Lt):
            code.addCode(OpCode.LT())
        elif isinstance(op, ast.LtE):
            code.addCode(OpCode.LTE())
        elif isinstance(op, ast.Gt):
            code.addCode(OpCode.GT())
        elif isinstance(op, ast.GtE):
            code.addCode(OpCode.GTE())
        elif isinstance(op, ast.Is):
            code.addCode(OpCode.IS())
        elif isinstance(op, ast.IsNot):
            code.addCode(OpCode.IS_NOT())
        elif isinstance(op, ast.In):
            code.addCode(OpCode.IN())
        elif isinstance(op, ast.NotIn):
            code.addCode(OpCode.IN_NOT())


def astdump(node, annotate_fields=True, include_attributes=False, indent='  '):
    """
    Return a formatted dump of the tree in *node*.  This is mainly useful for
    debugging purposes.  The returned string will show the names and the values
    for fields.  This makes the code impossible to evaluate, so if evaluation is
    wanted *annotate_fields* must be set to False.  Attributes such as line
    numbers and column offsets are not dumped by default.  If this is wanted,
    *include_attributes* can be set to True.
    """
    def _format(node, level=0):
        if isinstance(node, AST):
            fields = [(a, _format(b, level)) for a, b in iter_fields(node)]
            if include_attributes and node._attributes:
                fields.extend([(a, _format(getattr(node, a), level))
                               for a in node._attributes])
            return ''.join([
                node.__class__.__name__,
                '(',
                ', '.join(('%s=%s' % field for field in fields)
                          if annotate_fields else
                          (b for a, b in fields)),
                ')'])
        elif isinstance(node, list):
            lines = ['[']
            lines.extend((indent * (level + 2) + _format(x, level + 2) + ','
                          for x in node))
            if len(lines) > 1:
                lines.append(indent * (level + 1) + ']')
            else:
                lines[-1] += ']'
            return '\n'.join(lines)
        return repr(node)
    if not isinstance(node, AST):
        raise TypeError('expected AST, got %r' % node.__class__.__name__)
    return _format(node)

