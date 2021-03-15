from .base import *
from .cfg import *
from .tools import *
from .fs import *
import subprocess
import shlex
import sys

__all__=['proc']


class prc():
    def __init__(self):
        self.init()

    def init(self):
        #hack to avoid annoying windows consoles
        self.startupnfo = None
        if sys.platform.startswith("win"):
            self.startupnfo = subprocess.STARTUPINFO()
            self.startupnfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.startupnfo.wShowWindow = subprocess.SW_HIDE

    def runcmd(self,cmd,*args,outfn=None,shell=False):
        cmdval = tools[cmd]
        if cmdval is None:
            return 1,"","" #TODO: raise proper exception
        return self.run(cmdval,*args,outfn=outfn,shell=shell)

    def escape(self,args):
        return ["\""+x+"\"" for x in args]

    def run(self,cmd,*args,outfn=None,shell=False):
        try:
            if isinstance(cmd,str):
                cmd = "\""+cmd+"\""
                cmd = cmd+" "+(" ".join(self.escape(args)))
            else:
                cmd.extend(args)
                cmd = " ".join(self.escape(cmd))
            torun = shlex.split(cmd) #posix=not env.is_windows()
            #TODO: consider swicth to Python 3.5 for subprocess.run
            # print(torun)
            try:
                p=subprocess.Popen(torun,universal_newlines=True,stderr=subprocess.STDOUT,startupinfo=self.startupnfo,stdout=subprocess.PIPE,shell=shell)
            except FileNotFoundError:
                p=subprocess.Popen(torun,universal_newlines=True,stderr=subprocess.STDOUT,startupinfo=self.startupnfo,stdout=subprocess.PIPE,shell=True)
            lines=[]
            for line in p.stdout:
                lines.append(line)
                if outfn: outfn(line.strip("\n"))
            p.wait()
            #res = subprocess.check_output(torun,universal_newlines=True,stderr=subprocess.STDOUT,startupinfo=self.startupnfo)
            #return res.returncode, res.stdout, res.stderr
            res = "".join(lines)
            return p.returncode,res,res
        except subprocess.CalledProcessError as e:
            return e.returncode,e.output,e.output



    def run_get_lines(self,cmd,*args):
        r,out,err = self.run(cmd,*args)
        for line in out.split("\n"):
            yield line

    def runzcmd(self,*args):
        return self.run(
            env.zpython,
            env.ztc_cli,
            *args
        )

proc = prc()

#add_init(proc.init)

