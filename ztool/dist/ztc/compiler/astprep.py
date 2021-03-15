from base import *
import ast
import json
from compiler.exceptions import CSyntaxError, CNameError,CNameConstantError, CUnsupportedFeatureError,CWrongSyntax
from compiler.globals import lookup_table

class AstPreprocessor(ast.NodeTransformer):
    def __init__(self,names,pinmap,defines,cfiles,just_imports=False):
        self.allnames = {}
        self.allnames.update(names)
        self.pinmap = pinmap
        self.defines = defines
        self.cfiles = cfiles
        self.curpath = ""
        self.modules = set()
        self.just_imports=just_imports

    def visit_Import(self,node):
        for alias in node.names:
            self.modules.add(alias.name)
        return node

    def visit_ImportFrom(self,node):
        for alias in node.names:
            self.modules.add(node.module+"."+alias.name)
        return node

    #remove docstrings
    def visit_FunctionDef(self,node):
        node = self.generic_visit(node)
        if node.body and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value, ast.Str):
            node.body.pop(0)
        return node
    #remove docstrings
    def visit_ClassDef(self,node):
        node = self.generic_visit(node)
        if node.body and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value, ast.Str):
            node.body.pop(0)
        return node
    #remove docstrings
    def visit_Module(self,node):
        node = self.generic_visit(node)
        if node.body and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value, ast.Str):
            node.body.pop(0)
        elif len(node.body)>=2 and isinstance(node.body[0],ast.Import) and node.body[0].names[0].name=="__builtins__":
            if isinstance(node.body[1],ast.Expr) and isinstance(node.body[1].value,ast.Str):
                node.body.pop(1)
        return node
    
    def visit_Name(self,node):
        name = node.id
        # print("CHECKING NAME",name,"IN",self.allnames)
        if name in self.allnames:
            pos = self.allnames[name]
        else:
            return node
        if isinstance(node.ctx,ast.Load):
            return ast.Num(pos)
        raise CNameError(node.lineno,node.col_offset,"","Unsupported preprocessor name usage for "+str(name))

    def visit_Call(self,node):
        if self.just_imports:
            return self.generic_visit(node)
        if isinstance(node.func,ast.Name) and node.func.id=="__define":
            if len(node.args)!=2:
                raise CWrongSyntax(node.lineno,node.col_offset,"","__define needs 2 arguments")
            if not isinstance(node.args[0],ast.Name):
                raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"__define needs a name and an integer as arguments")
            if isinstance(node.args[1],ast.UnaryOp) and isinstance(node.args[1].op,ast.USub):
                val = -node.args[1].operand.n
            elif isinstance(node.args[1],ast.Num) and isinstance(node.args[1].n,int):
                val = node.args[1].n
            else:
                raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"__define needs an integer as second argument")
            #print("===>>>> ADDING",node.args[0].id,"AS",node.args[1].n)
            self.allnames[node.args[0].id]=val
            return None
        elif isinstance(node.func,ast.Name) and node.func.id=="__lookup":
            if len(node.args)!=1:
                raise CWrongSyntax(node.lineno,node.col_offset,"","__lookup need 1 argument")
            if not isinstance(node.args[0],ast.Name):
                raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"__lookup needs a name as first argument")
            
            try:
                val = lookup_table[node.args[0].id]
            except:
                raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"__lookup can't find "+node.args[0].id)
            debug("__lookup value assigned to",node.args[0].id,"is",str(val))
            if isinstance(val,str):
                return ast.Str(val)
            elif isinstance(val,bytes):
                return ast.Bytes(val)
            elif isinstance(val,int) or isinstance(val,float):
                return ast.Num(val)
            return None
        elif isinstance(node.func,ast.Name) and node.func.id=="__cdefine":
            if len(node.args)>2:
                raise CWrongSyntax(node.lineno,node.col_offset,"","__cdefine needs 2 arguments at most")
            if not isinstance(node.args[0],ast.Name):
                raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"__cdefine needs a name as first argument")
            val=None
            if len(node.args)==2:
                if isinstance(node.args[1],ast.UnaryOp) and isinstance(node.args[1].op,ast.USub):
                    val = -node.args[1].operand.n
                elif isinstance(node.args[1],ast.Num) and isinstance(node.args[1].n,int):
                    val = node.args[1].n
                else:
                    raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"__cdefine needs an integer as second argument")
                #print("===>>>> ADDING",node.args[0].id,"AS",node.args[1].n)
            if "CDEFS" not in self.defines:
                self.defines["CDEFS"]=[]
            if val is None:
                self.defines["CDEFS"].append(node.args[0].id)
            else:
                self.defines["CDEFS"].append(node.args[0].id+"="+str(val))
            return None
        elif isinstance(node.func,ast.Name) and node.func.id=="__cfile":
            if len(node.args)>1:
                raise CWrongSyntax(node.lineno,node.col_offset,"","__cfile needs 1 argument at most")
            if not isinstance(node.args[0],ast.Str):
                raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"__cfile needs a string as first argument")
            #print("__cfile: ", os.path.join(self.curpath,node.args[0].s))
            self.cfiles.add(fs.path(self.curpath,node.args[0].s))
            return None
        else:
            return self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.value,ast.Name) and node.value.id in self.allnames:
            #print("ASTPREP",node.value.id,self.pinmap,self.allnames)
            #pin attribute, resolve
            if isinstance(node.ctx, ast.Load):
                if node.value.id in self.pinmap and node.attr in self.pinmap[node.value.id] and self.pinmap[node.value.id][node.attr] in self.allnames:
                    return ast.Num(self.allnames[self.pinmap[node.value.id][node.attr]])
                elif node.value.id in self.pinmap:
                    raise CNameError(node.lineno,node.col_offset,"","This board does not support such pin function! "+str(node.value.id)+"."+str(node.attr))
                else:
                    raise CNameError(node.lineno,node.col_offset,"",str(node.value.id)+" can't have attributes")
            else:
                raise CNameError(node.lineno,node.col_offset,"","Unsupported preprocessor name usage for "+str(node.value.id)+".")
        return self.generic_visit(node)

    def handle_bodies(self,body):
        if isinstance(body,list):
            ret = [self.visit(nn) for nn in body]
            if len(ret)==1:
                ret = ret[0]
        else:
            ret = self.visit(body)
        return ret

    def visit_If(self,node):
        if self.just_imports:
            return self.generic_visit(node)
        if isinstance(node.test,ast.Call) and isinstance(node.test.func,ast.Name) and node.test.func.id=="__defined":
            fun = node.test
            if len(fun.args)==2 and isinstance(fun.args[0],ast.Name) and (isinstance(fun.args[1],ast.Str) or isinstance(fun.args[1],ast.Num)):
                name = fun.args[0].id
                val = fun.args[1].s if isinstance(fun.args[1],ast.Str) else fun.args[1].n
                if not name in self.defines:
                    raise CNameError(node.lineno,node.col_offset,"",str(name)+" is not defined!")
                #print(name,"is in",self.defines)
                if isinstance(self.defines[name],list) and val in self.defines[name]:
                    return self.handle_bodies(node.body)
                elif self.defines[name]==val:
                    return self.handle_bodies(node.body)
                else:
                    #remove
                    return self.handle_bodies(node.orelse)
            else:
                raise CWrongSyntax(node.lineno,node.col_offset,self.filename,"__defined needs a name and an integer or string as arguments")
        return self.generic_visit(node)


    def clean(self,tree):
        torem = []
        for x in tree.body:
            if isinstance(x,ast.Expr):
                try:
                    v = x.value
                except:
                    torem.append(x)
        for x in torem:
            tree.body.remove(x)

