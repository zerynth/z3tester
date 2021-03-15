import os
import os.path
import tempfile
import json
import shutil
import tarfile
import hashlib
import sys
import time
from . import yaml
from .cfg import *
import glob

__all__ = ["fs"]


class zfs():


    def __init__(self,tmpdir="."):
        self.tmpdir = self.apath(tmpdir)
        self.tempfiles=set()
        self.sep = os.sep
        # fix misnaming -_-
        self.read_file = self.readfile

    # Temporary files
    def set_temp(self,tmpdir):
        self.tmpdir = self.apath(tmpdir)


    def get_tempfile(self,data):
        td = self.get_tempdir()
        fs.write_file(data,fs.path(td,"tmp.bin"))
        return fs.path(td,"tmp.bin")
        
    def del_tempfile(self,src):
        pass

    def get_tempdir(self):
        return tempfile.mkdtemp(dir=self.tmpdir)

    def del_tempdir(self,tmp):
        fs.rmtree(tmp)

    def get_hashdir(self,path):
        hh = hashlib.md5()
        hh.update(bytes(path,"utf-8"))
        pth = self.path(self.tmpdir,hh.hexdigest())
        self.rmtree(pth)
        self.makedirs(pth)
        return pth

    def get_yaml(self,src, failsafe=False):
        try:
            self.check_path(src)
            with open(src,"r",encoding="utf8") as ff:
                return yaml.safe_load(ff) 
        except Exception as e:
            if failsafe:
                return {}
            else:
                raise e

    def set_yaml(self,ym,dst,flow_style=None):
        if dst:
            self.check_path(dst)
            with open(dst,"w",encoding="utf8") as ff:
                yaml.dump(ym,ff,indent=4,encoding="utf-8",explicit_start=True,explicit_end=True,default_flow_style=flow_style,allow_unicode=True)
        else:
            return yaml.dump(ym,indent=4,encoding="utf-8",explicit_start=True,explicit_end=True,default_flow_style=flow_style,allow_unicode=True).decode("utf-8")

    def get_yaml_or_json(self,src):
        try:
            data = self.get_yaml(src)
            return data
        except:
            return self.get_json(src)


    def get_json(self,src,strict=True):
        self.check_path(src)
        with open(src,"r",encoding="utf8") as ff:
            if strict:
                return json.load(ff)
            else:
                return commentjson.load(ff)

    def set_json(self,js,dst):
        self.check_path(dst)
        with open(dst,"w",encoding="utf8") as ff:
            json.dump(js,ff,indent=4,sort_keys=True)

    def is_dir(self,src):
        self.check_path(src)
        return os.path.isdir(src)

    def check_path(self,path):
        if sys.platform.startswith("win"):
            if isinstance(path,str):
                path = [path]
            for pp in path:
                if len(pp) > 256:
                    error("OS ERROR:",pp)
                    fatal("Path too long!")

    def rmtree(self,dst):
        self.check_path(dst)
        try:
            if not fs.exists(dst):
                return
            shutil.rmtree(dst)
        except Exception as e:
            log(e)
            for path, dirs, files in os.walk(dst):
                for file in files:
                    try:
                        os.remove(os.path.join(path, file))
                    except Exception as e:
                        log("Warning: can't remove file :", file, "error: ", e)

    def rm_file(self, dst):
        self.check_path(dst)
        try:
            os.remove(os.path.join(dst))
        except Exception as e:
            log("Warning: can't remove file :", dst, "error: ", e)

    def copyfileobj(self,src,dst):
        shutil.copyfileobj(src,dst)


    def copytree(self,src,dst):
        self.check_path([src, dst])
        shutil.rmtree(dst,ignore_errors=True)
        try:
            shutil.copytree(src,dst,ignore_dangling_symlinks=True)
        except:
            pass
            #TODO: copy by walking

    def copyfile(self,src,dst):
        self.check_path([src,dst])
        shutil.copyfile(src,dst)

    # Must be used in board support files only!
    def copyfile2(self,src,dst):
        self.check_path([src,dst])
        if sys.platform.startswith("win"):
            # some block devices don't work with shutil in some windows configurations (e.g. st_nucleo) -_-
            # can't use proc.py with pipes...use os.system -_-
            os.system("echo f | xcopy /f /y \"%s\" \"%s\""%(src,dst))
        else:
            shutil.copyfile(src,dst)

    def file_hash(self,dst):
        self.check_path(dst)
        hh = hashlib.md5()
        with open(dst,"rb") as ff:
            hh.update(ff.read())
        return hh.hexdigest()

    def untarxz(self,src,dst):
        self.check_path([src,dst])
        zp = tarfile.open(src,"r:xz")
        zp.extractall(dst)
        zp.close()
    
    def untargz(self,src,dst):
        self.check_path([src,dst])
        zp = tarfile.open(src,"r:gz")
        zp.extractall(dst)
        zp.close()

    def mergetree(self,src,dst):
        pass

    def __tarfn(self,obj,original, archive):
        obj.add(original,arcname=archive)


    def __zipdir(self,path, zip, fn, rmpath,root_filter="/."):
        self.check_path(path)
        for root, dirs, files in os.walk(path):
            for file in files:
                if root_filter in root:
                    continue
                elif file.startswith("."):
                    continue
                #print(os.path.join(root, file),"=>",os.path.join(root.replace(rmpath,"").strip("/"),file))
                fn(zip,os.path.join(root, file),os.path.join(root.replace(rmpath,"").strip("/"),file))


    def tarxz(self,src,dst,filter=None):
        self.check_path([src,dst])
        tar = tarfile.open(dst,"w:xz",preset=9)
        if filter:
            self.__zipdir(src,tar,self.__tarfn,src,root_filter=filter)
        else:
            self.__zipdir(src,tar,self.__tarfn,src)
        tar.close()


    def unique_paths(self,pths):
        self.check_path(pths)
        pths = list(pths)
        res = []
        dups = set()
        for i in range(len(pths)):
            pi = pths[i]
            for j in range(i+1,len(pths)):
                if j in dups:
                    continue # skip checked
                pj = pths[j]
                if pi==pj or os.path.samefile(pi,pj):
                    dups.add(j)
            if i not in dups:
                res.append(pi)
        return res

    def path(self,*args):
        self.check_path(os.path.normpath(os.path.join(*args)))
        return os.path.normpath(os.path.join(*args))

    def apath(self,path):
        self.check_path(path)
        return os.path.normpath(os.path.abspath(os.path.realpath(path)))

    def rpath(self,path,parent):
        self.check_path([path, os.path.relpath(path,parent)])
        return os.path.relpath(path,parent)

    def wpath(self,path):
        return path.replace(os.path.sep,"/")

    def homedir(self):
        return self.apath(os.path.expanduser("~"))

    def basename(self,path):
        self.check_path(path)
        return os.path.basename(os.path.normpath(path))

    def dirname(self,path):
        self.check_path(path)
        return os.path.dirname(os.path.normpath(path))

    def split(self,path):
        self.check_path(path)
        return os.path.split(os.path.normpath(path))

    def glob(self,path,pattern):
        self.check_path([path, glob.glob(fs.path(path,pattern))])
        return glob.glob(fs.path(path,pattern))

    def exists(self,path):
        self.check_path(path)
        return os.path.exists(path)

    def isfile(self,path):
        self.check_path(path)
        return os.path.isfile(path)

    def isdir(self,path):
        self.check_path(path)
        return os.path.isdir(path)

    def stat(self,path):
        self.check_path(path)
        return os.stat(path)

    def dirs(self,path):
        self.check_path(path)
        root,dirnames,files = next(os.walk(path))
        return [self.path(path,x) for x in dirnames]

    def files(self,path):
        self.check_path(path)
        root,dirnames,files = next(os.walk(path))
        return [self.path(path,x) for x in files]
    
    def all_files(self,path,filter=None):
        self.check_path(path)
        res = []
        for root,dirnames,files in os.walk(path):
            if not filter:
                res.extend([self.path(root,x) for x in files])
            else:
                res.extend([self.path(root,x) for x in files if x==filter])

        return res

    def write_file(self,data,dst):
        self.check_path(dst)
        if isinstance(data,str):
            d="w"
            with open(dst,d,encoding="utf8") as ff:
                ff.write(data)
        else:
            d="wb"
            with open(dst,d) as ff:
                ff.write(data)
        

    def readfile(self,path,param=""):
        self.check_path(path)
        if param:
            with open(path,"r"+param) as ff:
                return ff.read()
        else:
            with open(path,"r",encoding="utf8") as ff:
                return ff.read()

    def readlines(self,path):
        self.check_path(path)
        with open(path,encoding="utf8") as ff:
            return ff.readlines()
 
    def makedirs(self,dirs):
        #self.check_path(dirs)
        if isinstance(dirs,str):
            os.makedirs(dirs,exist_ok=True)
        else:
            for d in dirs:
                os.makedirs(d,exist_ok=True)

    def rm_readonly(self, func, path):
        self.check_path(path)
        try:
            if not os.path.exists(path):
                return
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception as e:
            log("ERROR in rmtree %s"%str(e))

    def move(self,src,dst):
        shutil.move(src,dst)

    def mtime(self,src):
        return os.path.getmtime(src)

    def unchanged_since(self,src,seconds):
        mt = self.mtime(src)
        return time.time()-mt>seconds

    def dir_size(self,thedir):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(thedir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.isfile(fp):
                    total_size += os.path.getsize(fp)
        return total_size
    def get_project_config(self,project,fail=False):
        #search for project configuration file
        cfgfile = self.path(project,"project.yml")
        if not self.exists(cfgfile):
            if fail:
                fatal(cfgfile, "does not exist! Create a project configuration file first...")
            else:
                raise Exception("Project config file missing")
        try:
            cfg = self.get_yaml_or_json(cfgfile)
        except Exception as e:
            if fail:
                fatal(cfgfile, "is not readable")
            else:
                raise Exception("Project config file not readable")
        return cfg
    def set_project_config(self,project,cfg):
        cfgfile = self.path(project,"project.yml")
        fs.set_yaml(cfg,cfgfile,False)

    # def remove_readonly_no_output(self, func, path, excinfo):
    #     #used to hide the whooosh bug when updating the index in, guess.., windows -_-
    #     try:
    #         if not os.path.exists(path):
    #             return
    #         os.chmod(path, stat.S_IWRITE)
    #         func(path)
    #     except Exception as e:
    #         pass

fs=zfs()

