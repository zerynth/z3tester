
from collections import OrderedDict
import struct


class Name():

    def __init__(self, idx, tag):
        self.idx = idx
        self.tag = tag

    def isFree(self):
        return self.tag=="free"

    def isCell(self):
        return self.tag=="cell"

    def isDeref(self):
        return self.tag == "cell" or self.tag=="free"

    def isLocal(self):
        return self.tag == "loc"

    def isGlobal(self):
        return self.tag == "glb"

    def isBuiltin(self):
        return self.tag == "blt"

    def isNative(self):
        return self.tag == "nat"

    def __str__(self):
        return "N:["+str(self.idx)+", "+str(self.tag)+"]"


class Scope():

    def __init__(self, name, scopes):
        self.kind = ""
        if scopes:
            self.uid = Scope.getid(name,scopes[-1].uid)
            self.parent =scopes[-1]
        else:
            self.uid=name
            self.parent = None
        self.names = []
        self.locals = []
        self.freevars = []
        self.cellvars = []
        self.globals = []

        self.level = len(scopes)
        self.blocks=0
        self.cblock=0

    def __str__(self):
        res = "\n+Scope: " + self.uid + "@" + str(self.level) + "\n"
        res += "    locals: " + (", ".join([str(x) for x in self.locals])) + "\n"
        res += "      free: " + (", ".join([str(x) for x in self.freevars])) + "\n"
        res += "     cells: " + (", ".join([str(x) for x in self.cellvars])) + "\n"
        res += "   globals: " + (", ".join([str(x) for x in self.globals])) + "\n"
        res += "\n"
        return res


    def forget(self):
        self.forgot = self.locals
        self.locals = []

    def remember(self):
        self.locals = list(set(self.forgot+self.locals))

    @staticmethod
    def getid(name,scopename):
        res = scopename+"."+name
        #if not res.startswith("__main__."):
        #    res = "__main__."+res
        return res

    def nameSpec(self, name):
        #print("namespec from scope",self)
        if name in self.locals:
            return (self.locals.index(name), "loc")
        elif name in self.freevars:
            return (self.freevars.index(name), "free")
        elif name in self.cellvars:
            return (len(self.freevars)+self.cellvars.index(name), "cell")
        elif name in self.globals:
            return (-1, "glb")
        return None

    def hasName(self, name):
        return name in self.names

    def hasGlobalName(self, name):
        return name in self.globals

    def hasNonlocalName(self, name):
        return name in self.cellvars

    def hasNonlocalNames(self):
        return len(self.cellvars)>0

    def pushBlock(self):
        self.cblock+=1
        if self.cblock>self.blocks:
            self.blocks=self.cblock

    def popBlock(self):
        self.cblock-=1

    def getBlocks(self):
        return self.blocks

    def addArg(self,name):
        if name not in self.names:
            self.locals.append(name)
            self.names.append(name)

    def getArgs(self,nargs):
        return self.locals[0:nargs]

    def addName(self, name, level):
        if level == self.level:
            # local var
            if name not in self.names:
                self.locals.append(name)
                self.names.append(name)
#                print("ADDING "+str(name)+" LOCAL @ "+str(self.level))
            return False
        elif level <= 0:  # global
            if name not in self.globals:
                self.globals.append(name)
                self.names.append(name)
#                print("ADDING "+str(name)+" GLOBAL @ "+str(self.level))
            return False
        else:  # self.level<level  and level > 0:
            # name is already in an enclosing scope
            # it is a cellvar for the current scope
            # and a freevar for the enclosing scope
            # therefore the index is assigned relative cellvars for the current scope
            # and relative to freevars in the enclosing scope
            if name not in self.cellvars:
                self.cellvars.append(name)
#                print("ADDING "+str(name)+" CELL @ "+str(self.level))
                return True
        return False

    def retName(self, name, level):
        if level == self.level:
            # get local var
            if name in self.names:
                return False
            return False
        elif level <= 0:  # global
            return False
        else:
            # we asked for a name in an enclosing scope
            # make it a cellvar here
            # and freevar in the enclosing scope
            if name not in self.cellvars:
                self.cellvars.append(name)
#                print("ADDING "+str(name)+" (CELL) @ "+str(self.level))
                return True
        return False

    def makeFree(self, name):
        if name in self.freevars:
            return
        self.freevars.append(name)
        self.locals.remove(name)

    def makeCell(self,name,stopscope):
        scope = self
        while scope and scope!=stopscope:
            if name not in scope.cellvars:
                scope.cellvars.append(name)
            scope = scope.parent
#        print("MAKING "+str(name)+" FREE @ "+str(self.level))


class Env():
    builtins = []
    natives = []
    namestore = {}
    exceptions = {}
    exc_strings = {}
    curnamecode = 256

    def __init__(self):
        self.scopes = []
        self.scopedir={}
        #Env.builtins = []
        #Env.natives = []
        #Env.namestore = {}
        #Env.curnamecode = 256        

    def __str__(self):
        res = "ENV {\n"
        res+= "   builtins:"+str(Env.builtins)
        for i, scope in enumerate(self.scopes):
            res += str(scope).replace("\n", "\n"+("   " * i))
        res+= "   natives:"+str(Env.natives)+"\n"
        res += "}"
        #res+=str(self.scopedir)
        return res

    def print_scopedir(self):
        for x,v in self.scopedir.items():
            print(x,"=>",str(v["scope"]))

    def get_scopedir(self):
        return self.scopedir

    def transferHyperGlobals(self,env):
        Env.builtins = list(env.builtins)
        Env.natives = list(env.natives)
        Env.namestore = dict(env.namestore)
        Env.curnamecode = env.curnamecode

    def addNative(self, name):
        if name not in Env.natives:
            Env.natives.append(name)

    def addBuiltin(self, name):
        if name not in Env.builtins:
            Env.namestore[name]=len(Env.builtins)
            Env.builtins.append(name)

    def addNameCode(self,name):
        if name not in Env.namestore:
            Env.namestore[name]=Env.curnamecode
            Env.curnamecode+=1
        return Env.namestore[name]    

    def getNameCode(self,name):
        if name not in Env.namestore:
            return Env.builtins.index(name)
        return Env.namestore[name]

    def hasNameCode(self,name):
        return name in Env.namestore


    def getException(self,name,parent):
        return Env.exceptions[name]

    def addException(self,name,parent,msg=""):
        Env.exceptions[name]=parent
        if msg:
            Env.exc_strings[name]=name+": "+msg
        else:
            Env.exc_strings[name]=name
    def hasException(self,name):
        return name in Env.exceptions

    def getScope(self):
        return self.scopes[-1]

    def getLevel(self):
        return self.scopes[-1]

    def atGlobalScope(self):
        return len(self.scopes)==1

    def resolveCell(self,name):
        cell=0
        for scope in reversed(self.scopes):
            #print("Resolving",name,"in",scope)
            if name in scope.freevars:
                cell+=scope.freevars.index(name)
                return cell
            elif name in scope.cellvars:
                cell+=scope.cellvars.index(name)+len(scope.freevars)
                return cell
            else:
                cell+=len(scope.cellvars)+len(scope.freevars)
        return -1


    def nameInfo(self, name):
        nfo = self.scopes[-1].nameSpec(name)
        if nfo!=None:
            idx, tag = nfo
            if tag=="glb":
                gnfo = self.scopes[0].nameSpec(name)
                if gnfo!=None:
                    return Name(gnfo[0],"glb")
                else:
                    if name in Env.builtins:
                        return Name(Env.builtins.index(name),"blt")
                    elif name in Env.natives:
                        return Name(Env.natives.index(name),"nat")
                    return None
            else:
                return Name(idx,tag)
        else:
            gnfo = self.scopes[0].nameSpec(name)
            if gnfo!=None:
                return Name(gnfo[0],gnfo[1])
            elif name in Env.builtins:
                return Name(Env.builtins.index(name),"blt")
            elif name in Env.natives:
                return Name(Env.natives.index(name),"nat")
            return None

    def pushScope(self, kind):
        scope = Scope(kind, self.scopes)
        self.scopedir[scope.uid]={"parents":[x for x in self.scopes],"scope":scope}
        self.scopes.append(scope)
        return self

    def popScope(self):
        self.scopes.pop()
        return self

    def putArg(self,name):
        scope = self.scopes[-1]
        scope.addArg(name)
        self.addNameCode(name)

    def putName(self, name,asGlobal=False,asNonLocal=False):
        scope = self.scopes[-1]
        # for ascope in reversed(self.scopes):
        #     if ascope.hasName(name):
        #         if(scope.addName(name, ascope.level)):
        #             ascope.makeFree(name)
        #         break
        # else:
        #     scope.addName(name, len(self.scopes) - 1)
        if asGlobal:
            scope.addName(name,0)
            self.scopes[0].addName(name,0)
        elif asNonLocal:
            for ascope in reversed(self.scopes):
                if ascope.hasName(name):
                    if(scope.addName(name, ascope.level)):
                        ascope.makeFree(name)
                        scope.makeCell(name,ascope)
                    break
            else:
                scope.addName(name, len(self.scopes) - 1)
        else:
            if not scope.hasNonlocalName(name):
                scope.addName(name, len(self.scopes) - 1)
        self.addNameCode(name)
        return name

    def getName(self, name):
        scope = self.scopes[-1]
        #print("GETNAME "+str(name)+" @ "+str(scope.level))
        for ascope in reversed(self.scopes):
            if ascope.hasName(name):
                if ascope.hasGlobalName(name):
                    scope.addName(name,0)
                else:
                    if(scope.retName(name, ascope.level)):
                        ascope.makeFree(name)
                        scope.makeCell(name,ascope)
                if ascope.level<=0:
                    scope.addName(name,0)
                return name        
        if name in Env.builtins:
            return name
        if name in Env.natives:
            return name
        return None

    def buildExceptionTable(self):
        etable = []
        pdict = {}
        mdict = {}
        #print(Env.exceptions)
        for k,v in Env.exceptions.items():
            ecode = self.getNameCode(k)
            pdict[ecode] = self.getNameCode(v)
            mdict[ecode] = Env.exc_strings[k]
            #print("ecode",ecode,"=>",pdict[ecode],"=>",mdict[ecode])
            etable.append(ecode)
        etable.sort()
        self.etable = etable
        edict = {}
        for k,v in pdict.items():
            edict[k]=etable.index(v)
        self.edict = edict
        self.mdict = mdict
        # print(etable)  
        #print(edict)

    def resolveException(self,name):
        return self.etable.index(name)

    def getBinaryExceptionTable(self):
        ll = []
        ss = []
        mlen = 0;
        for i,k in enumerate(self.etable):
            ss.append((len(self.mdict[k]),self.mdict[k]))
            ll.append((k,self.edict[k],mlen))
            mlen+=2+len(self.mdict[k])
            if mlen%4:
                mlen+=(4-(mlen%4))
        return (ll,ss,mlen)



class MiniTable():
    def __init__(self,size):
        self.empty = 65535
        self.nonext = 255
        self.nopos = 255
        self.hash = [[self.empty,self.nonext,self.nopos] for l in range(0,size)]
        self.size = size
    def putNames(self,names,poss):
        #print("putting",names,poss)
        for pos,l in enumerate(names):
            probe = l%self.size
            place = 0
            tail = self.nonext
            #print("INSERTING",l,"@",probe)
            if self.hash[probe][0]!=self.empty:
                while probe!=self.nonext:
                    #print("CHECKING",l,"@",probe,"=",self.hash[probe],"tail",tail)
                    tail = probe
                    probe = self.hash[probe][1]
                while self.hash[place][0]!=self.empty:
                    place = (place+1)%self.size
            else:
                place = probe
            self.hash[place][0] = l
            self.hash[place][1] = self.nonext
            self.hash[place][2] = poss[pos]
            if tail!=self.nonext:
                self.hash[tail][1]=place
                #print("TAIL SET TO",self.hash[tail])                
            #print("OK INS",l,"@",place,"=",self.hash[place],"tail",tail)                
            
    def __str__(self):
        res = "minitable: "+str(len(self.hash))+"\n"
        cnv = {v:k for k,v in Env.namestore.items()}
        for i,h in enumerate(self.hash):
            res+=str(h[0])+": "+str(cnv[h[0]]) + " = " +str(i)+" -> "+str(h[1])+"@"+str(h[2])+"\n"
        return res
    def toBytes(self):
        res = bytearray()
        res+=struct.pack("=I",len(self.hash))
        for h in self.hash:
            res+=struct.pack("=H",h[0]);
            res+=struct.pack("=B",h[1]);
            res+=struct.pack("=B",h[2]);
        return res
    def getPos(self,name):
        for i,m in enumerate(self.hash):
            if m[0]==name:
                return i
        return -1
