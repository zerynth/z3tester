import base64
import json
import os
import sqlite3
import sys
import uuid

from .base import *
from .fs import *

__all__ = ['env', 'Var', 'decode_base64']


class Var():
    def __init__(self, _dict={}, recursive=True):
        self._v = dict(_dict)
        for k, v in _dict.items():
            if isinstance(v, dict) and recursive:
                self._v[k] = Var(v)
            else:
                self._v[k] = v

    def __getattr__(self, attr):
        return self._v[attr]

    def to_dict(self):
        d = {}
        for k, v in self._v.items():
            if isinstance(v, Var):
                d[k] = v.to_dict()
            else:
                d[k] = v
        return d

    def set(self, key, value):
        self._v[key] = Var(value) if isinstance(value, dict) else value

    def get(self, key, default=None):
        return self._v.get(key, default)

    def __str__(self):
        return str(self._v)


class Environment():

    def __init__(self):
        pass

    def dirs(self):
        prefix = os.environ.get("ZERYNTH_HOME", fs.homedir())
        for x in self.__dict__:
            if isinstance(self[x], str) and self[x].startswith(prefix):
                yield self[x]

    def __getitem__(self, key):
        return getattr(self, key)

    def load(self, cfgdir):
        try:
            js = fs.get_json(fs.path(cfgdir, "config.json"))
            self.var = Var(js)
            self._var = js
        except Exception as e:
            critical("can't load configuration", exc=e)

    def load_versions(self, cfgdir):
        try:
            js = fs.get_json(fs.path(cfgdir, "versions.json"))
            self.versions = js
        except:
            self.versions = {self.var.version: ["base"]}

    def load_skin(self):
        try:
            js = fs.get_json(fs.path(fs.dirname(__file__), "skin.json"))
            self.skin = js["skin"]
        except:
            self.skin = ""

    def save_versions(self):
        try:
            js = fs.set_json(self.versions, fs.path(self.cfgdir, "versions.json"))
        except:
            pass

    def save(self, cfgdir=None, version=None):
        try:
            if not cfgdir:
                cfgdir = self.cfg
            dd = self.var.to_dict()
            if version:
                dd["version"] = version
            js = fs.set_json(dd, fs.path(cfgdir, "config.json"))
        except Exception as e:
            critical("can't save configuration", exc=e)

    def load_dbs(self, cfgdir, dbname):
        try:
            # js = fs.get_json(fs.path(cfgdir,dbname))
            self._dbs_cfgdir = cfgdir
            self._dbs_dbname = dbname
            self._dbs = sqlite3.connect(fs.path(cfgdir, dbname), check_same_thread=False)
            self._dbs.execute(
                "CREATE TABLE IF NOT EXISTS aliases (alias TEXT PRIMARY KEY, uid TEXT, target TEXT, name TEXT, chipid TEXT, remote_id TEXT, classname TEXT)")
            self._dbs.execute("CREATE UNIQUE INDEX IF NOT EXISTS aliases_idx ON aliases(alias)")
            self._dbs.execute("CREATE UNIQUE INDEX IF NOT EXISTS uid_idx ON aliases(uid)")
            self._dbs.execute("CREATE INDEX IF NOT EXISTS chip_idx ON aliases(chipid)")
            self._dbs.execute(
                "CREATE TABLE IF NOT EXISTS linked (alias TEXT PRIMARY KEY,uid TEXT,target TEXT, name TEXT, chipid TEXT, remote_id TEXT, classname TEXT)")
            self._dbs.execute("CREATE UNIQUE INDEX IF NOT EXISTS linked_a_idx ON linked(alias)")
            self._dbs.execute("CREATE INDEX IF NOT EXISTS linked_t_idx ON linked(target)")
            self._dbs.execute("CREATE INDEX IF NOT EXISTS linked_c_idx ON linked(chipid)")

        except Exception as e:
            self._dbs = None

    def save_dbs(self):
        try:
            self._dbs.commit()
        except Exception as e:
            critical("can't save configuration", exc=e)

    def load_repo_list(self):
        try:
            fs.get_json(fs.path(env.cfg, "repos.cfg"))
        except:
            pass
        return []

    def get_dev(self, key):
        res = {}
        for row in self._dbs.execute("select * from aliases where alias=? or uid=?", (key, key)):
            res[row[0]] = Var({"alias": row[0], "uid": row[1], "target": row[2], "name": row[3], "chipid": row[4],
                               "remote_id": row[5], "classname": row[6]})
        return res

    def get_linked_devs(self, target):
        res = {}
        for row in self._dbs.execute("select * from linked where target=?", (target,)):
            res[row[0]] = Var({"alias": row[0], "uid": row[1], "target": row[2], "name": row[3], "chipid": row[4],
                               "remote_id": row[5], "classname": row[6]})
        return res

    def get_dev_by_alias(self, alias):
        res = []
        for row in self._dbs.execute("select * from aliases where alias like '" + alias + "%'"):
            res.append(Var({"alias": row[0], "uid": row[1], "target": row[2], "name": row[3], "chipid": row[4],
                            "remote_id": row[5], "classname": row[6]}))
        if not res:  # if nothing in primary db, search linked db
            for row in self._dbs.execute("select * from linked where alias like '" + alias + "%'"):
                res.append(Var({"alias": row[0], "uid": row[1], "target": row[2], "name": row[3], "chipid": row[4],
                                "remote_id": row[5], "classname": row[6]}))
        return res

    def put_dev(self, dev, linked=False):
        if not isinstance(dev, Var):
            dev = Var(dev)
        if not linked:
            self._dbs.execute("insert or replace into aliases values(?,?,?,?,?,?,?)",
                              (dev.alias, dev.uid, dev.target, dev.name, dev.chipid, dev.remote_id, dev.classname))
        else:
            dev.alias = str(dev.target) + ":" + str(dev.chipid)
            dev.name = dev.name + " (" + str(dev.remote_id) + ")"
            self._dbs.execute("insert or replace into linked values(?,?,?,?,?,?,?)", (
                dev.alias, str(uuid.uuid4()), dev.target, dev.name, dev.chipid, dev.remote_id, dev.classname))
        self._dbs.commit()

    def del_dev(self, dev):
        self._dbs.execute("delete from aliases where alias=?", (dev.alias,))
        self._dbs.commit()

    def clean_db(self):
        self._dbs.execute("delete from aliases")
        self._dbs.commit()
        self._dbs.execute("delete from linked")
        self._dbs.commit()

    def get_all_dev(self):
        for row in self._dbs.execute("select * from aliases"):
            yield Var({"alias": row[0], "uid": row[1], "target": row[2], "name": row[3], "chipid": row[4],
                       "remote_id": row[5], "classname": row[6]})

    def make_dist_dirs(self, distpath):
        fs.makedirs(self.ztc_dir(distpath))
        fs.makedirs(self.lib_dir(distpath))
        fs.makedirs(self.stdlib_dir(distpath))
        fs.makedirs(self.studio_dir(distpath))
        fs.makedirs(self.docs_dir(distpath))
        fs.makedirs(self.examples_dir(distpath))
        fs.makedirs(self.idb_dir(distpath))

    def rm_token(self):
        # get token
        fs.rm_file(fs.path(env.cfg, "token.json"))

    def get_token(self):
        # get token
        try:
            token = Var(fs.get_json(fs.path(env.cfg, "token.json")))
        except:
            token = Var({
                "token": None,
                "expires": 0,
                "type": None
            })
        return token

    def set_token(self, rawtoken, toktype=None):
        pl = rawtoken.split(".")[1]
        js = json.loads(decode_base64(pl).decode("utf-8"))
        token = {
            "token": rawtoken,
            "expires": js["exp"],
            "type": toktype
        }
        fs.set_json(token, fs.path(env.cfg, "token.json"))

    def get_zdm_conditions(self):
        # get zdm conditions
        try:
            zdmcond = Var(fs.get_json(fs.path(env.cfg, "zdm.json")))
        except:
            zdmcond = Var({
                "acceptance": None,
            })
        return zdmcond

    def set_zdm_conditions(self):
        zdmcond = {
            "acceptance": True,
        }
        fs.set_json(zdmcond, fs.path(env.cfg, "zdm.json"))

    def get_latest_installed_version(self):
        res = self.var.version
        for dir in fs.dirs(fs.path(self.dist, "..")):
            bdir = fs.basename(dir)
            if match_version(bdir):
                if compare_versions(bdir, res) > 0:
                    res = bdir
        return res

    def load_matrix(self):
        mtxfile = fs.path(self.dist, "matrix.json")
        try:
            return fs.get_json(mtxfile)
        except:
            return {}

    def check_vm_compat(self, target, vmver, nooutput=False):
        # check previous VM versioning scheme
        if int32_version(vmver) <= int32_version("r2.2.0"):
            if not nooutput:
                warning(
                    "This virtual machine (" + vmver + ") is not compatible with the running version of Zerynth! A version before r2.3.0 is needed")
            return False

        matrix = env.load_matrix()
        if not matrix:
            if not nooutput:
                warning("Can't load compatibility matrix! Uplink at your own risk...")
            return True
        t2v = matrix["t2v"]
        v2t = matrix["v2t"]
        if target not in t2v:
            warning("Can't find target in matrix, assuming compatibility...")
            return True
        vmrange = t2v[target][env.var.version]
        if vmver >= vmrange[0] and vmver <= vmrange[1]:
            return True
        toolrange = v2t[target][vmver]
        if not nooutput:
            warning(
                "This virtual machine (" + vmver + ") is not compatible with the running version of Zerynth! A version between",
                toolrange[0], "and", toolrange[1], "is needed")
        return False


def decode_base64(data):
    missing_padding = len(data) % 4
    if missing_padding != 0:
        data += '=' * (4 - missing_padding)
    return base64.standard_b64decode(data)


env = Environment()


# ####
#     .Zerynth/
#         cfg/
#         workspace/
#         sys/
#         tmp/
#         nest/
#         dist/
#             version/
#                 ztc/
#                 libs/
#                 nest/
#                 stdlib/
#                 vhal/
#                 studio/
#                 docs/
#                 devices/
#                 examples/


def init_cfg():
    # platform
    env.load_skin()
    env.nbits = "64" if sys.maxsize > 2 ** 32 else "32"
    if sys.platform.startswith("win"):
        env.platform = "windows" + env.nbits
    elif sys.platform.startswith("linux"):
        env.platform = "linux" + env.nbits
    elif sys.platform.startswith("darwin"):
        env.platform = "mac"

    env.is_windows = lambda: env.platform.startswith("win")
    env.is_unix = lambda: not env.platform.startswith("win")
    env.is_mac = lambda: env.platform.startswith("mac")
    env.is_linux = lambda: env.is_unix() and not env.is_mac()

    testmode = int(os.environ.get("ZERYNTH_TESTMODE", 0))

    env.is_production = True

    # main directories TODO: change zdir to official zdir
    if testmode == 3:  # enable STAGE on zdm, and REMOTE on Zerynth. Because Zerynth doesn't have Stage env.
        zdir = "zerynth2" if env.is_windows() else ".zerynth2"
    elif testmode == 2:
        # special testing mode
        zdir = "zerynth2_test" if env.is_windows() else ".zerynth2_test"
        env.is_production = False
    elif testmode == 0:
        zdir = "zerynth2" if env.is_windows() else ".zerynth2"
    elif testmode == 1:
        #zdir = "zerynth2_local" if env.is_windows() else ".zerynth2_local"
        zdir = "zerynth2_test" if env.is_windows() else ".zerynth2_test"
        env.is_production = False
    if env.skin:
        zdir = zdir + "_" + env.skin

    env.home = fs.path(os.environ.get("ZERYNTH_HOME", fs.homedir()), zdir)
    env.cfg = fs.path(env.home, "cfg")
    env.tmp = fs.path(env.home, "tmp")
    env.sys = fs.path(env.home, "sys")
    env.vms = fs.path(env.home, "vms")
    env.edb = fs.path(env.home, "cfg", "edb")
    env.zdb = fs.path(env.home, "cfg", "zdb")
    env.cvm = fs.path(env.home, "cvm")

    # load configuration
    env.load(env.cfg)
    env.load_dbs(env.cfg, "devices.db")
    env.load_versions(env.cfg)
    # env.load_zpack_db(env.zdb,"packages.db")
    # env.load_ipack_db(env.idb,"packages.db")
    version = env.var.version
    env.var.bytecode_version = 2
    if testmode == 1:
        # local
        env.git_url = os.environ.get("ZERYNTH_GIT_URL", "http://localhost/git")
        # env.backend = os.environ.get("ZERYNTH_BACKEND_URL", "http://localhost/v1")
        env.backend = os.environ.get("ZERYNTH_BACKEND_URL", "https://test.zerynth.com/v1")
        env.connector = os.environ.get("ZERYNTH_ADM_URL", "http://localhost/v1")
        env.zdm = os.environ.get("ZERYNTH_ZDM_URL", "http://api.zdm.localhost")
        env.patchurl = os.environ.get("ZERYNTH_PATCH_URL", "http://localhost/installer")
        env.packurl = os.environ.get("ZERYNTH_PACK_URL", "http://localhost")
        github_app = "NO_APP"
    elif testmode == 2:
        # CI
        env.git_url = os.environ.get("ZERYNTH_GIT_URL", "https://test.zerynth.com/git")
        env.backend = os.environ.get("ZERYNTH_BACKEND_URL", "https://test.zerynth.com/v1")
        env.connector = os.environ.get("ZERYNTH_ADM_URL", "https://testapi.zerynth.com:444/v1")
        env.zdm = os.environ.get("ZERYNTH_ZDM_URL", "https://api.zdm.test.zerynth.com")
        env.patchurl = os.environ.get("ZERYNTH_PATCH_URL", "https://test.zerynth.com/installer")
        env.packurl = os.environ.get("ZERYNTH_PACK_URL", "https://test.zerynth.com")
        github_app = "882c71c6f98cd0354d97"
    elif testmode == 3:
        # STAGE of ZDM, and REMOTE for Zerynth
        env.git_url = os.environ.get("ZERYNTH_GIT_URL", "https://backend.zerynth.com/git")
        env.backend = os.environ.get("ZERYNTH_BACKEND_URL", "https://backend.zerynth.com/v1")
        env.connector = os.environ.get("ZERYNTH_ADM_URL", "https://api.zerynth.com/v1")
        env.zdm = os.environ.get("ZERYNTH_ZDM_URL", "https://api.zdm.stage.zerynth.com")
        env.patchurl = os.environ.get("ZERYNTH_PATCH_URL", "https://backend.zerynth.com/installer")
        env.packurl = os.environ.get("ZERYNTH_PACK_URL", "https://backend.zerynth.com")
        github_app = "99fdc1e39d8ce3051ce6"
    else:
        # remote
        env.git_url = "https://backend.zerynth.com/git"
        env.backend = "https://backend.zerynth.com/v1"
        env.connector = "https://api.zerynth.com/v1"
        env.zdm = os.environ.get("ZERYNTH_ZDM_URL", "https://api.zdm.zerynth.com")
        env.patchurl = os.environ.get("ZERYNTH_PATCH_URL", "https://backend.zerynth.com/installer")
        env.packurl = os.environ.get("ZERYNTH_PACK_URL", "https://backend.zerynth.com")
        github_app = "99fdc1e39d8ce3051ce6"

    if env.skin:
        env.packurl = env.packurl + "/" + env.skin
        env.patchurl = env.patchurl + "/" + env.skin

    # dist directories
    env.dist = fs.path(env.home, "dist", version)
    env.ztc = fs.path(env.home, "dist", version, "ztc")
    env.libs = fs.path(env.home, "dist", version, "libs")
    env.official_libs = fs.path(env.home, "dist", version, "libs", "official")
    env.nest = fs.path(env.home, "dist", version, "nest")
    env.stdlib = fs.path(env.home, "dist", version, "stdlib")
    env.vhal = fs.path(env.home, "dist", version, "vhal")
    env.studio = fs.path(env.home, "dist", version, "studio")
    env.distsys = fs.path(env.home, "dist", version, "sys")
    env.docs = fs.path(env.home, "dist", version, "docs")
    env.examples = fs.path(env.home, "dist", version, "examples")
    env.devices = fs.path(env.home, "dist", version, "devices")
    env.idb = fs.path(env.home, "dist", version, "idb")

    env.dist_dir = lambda x: fs.path(env.home, "dist", x)
    env.ztc_dir = lambda x: fs.path(x, "ztc")
    env.lib_dir = lambda x: fs.path(x, "libs")
    env.stdlib_dir = lambda x: fs.path(x, "stdlib")
    env.studio_dir = lambda x: fs.path(x, "studio")
    env.vhal_dir = lambda x: fs.path(x, "vhal")
    env.devices_dir = lambda x: fs.path(x, "devices")
    env.docs_dir = lambda x: fs.path(x, "docs")
    env.examples_dir = lambda x: fs.path(x, "examples")
    env.idb_dir = lambda x: fs.path(x, "idb")

    # set global temp dir
    fs.set_temp(env.tmp)

    # create dirs
    fs.makedirs(env.dirs())

    # Zerynth python to run ZTC
    if env.is_windows():
        env.zpython = fs.path(env.home, 'sys', 'python', 'python.exe')
    elif env.is_linux():
        env.zpython = fs.path(env.home, 'sys', 'python', 'bin', 'python')
    else:
        env.zpython = fs.path(env.home, 'sys', 'python', 'bin', 'python')

    # Ztcl python entry point (used in proc.py for running ZTC commands from zdm)
    env.ztc_cli = fs.path(env.ztc, "ztc.py")

    # backend & api
    env.api = Var({
        "project": env.backend + "/projects",
        "renew": env.backend + "/user/renew",
        "sso": env.backend + "/sso",
        "github_api": "https://api.github.com",
        "github": "https://github.com/login/oauth/authorize?client_id=" + github_app + "&scope=user,repo",
        "pwd_reset": env.backend + "/user/reset",
        "devices": env.backend + "/devices",
        "vm": env.backend + "/vms",
        "vmlist": env.backend + "/vmlist",
        "community": env.backend + "/community",
        "packages": env.packurl + "/packages",
        "ns": env.backend + "/namespaces",
        "repo": env.packurl,
        "search": env.backend + "/packages/search",
        "profile": env.backend + "/user/profile",
        "installation": env.backend + "/installations",
        "user": env.backend + "/user"
    })

    env.user_agent = "zdm/" + version

    env.proxies = None
    env.proxyfile = fs.path(env.cfg, "proxy.json")
    if fs.exists(env.proxyfile):
        try:
            env.proxies = fs.get_json(env.proxyfile)
        except:
            warning("Bad json in", env.proxyfile)

    # load repository
    env.repofile = fs.path(env.dist, "repository.json")
    try:
        env.repo = fs.get_json(env.repofile)
    except:
        warning("Can't load repository.json at", env.dist)

    # load installer folder
    env.root = ""
    try:
        env.root = fs.get_json(fs.path(env.cfg, "root.json"))["root"]
    except:
        warning("Can't load root.json at", env.cfg)


add_init(init_cfg, prio=0)
