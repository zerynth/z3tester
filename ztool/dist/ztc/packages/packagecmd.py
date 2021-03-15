"""
.. _ztc-cmd-package:

********
Packages
********

The ZTC features a package manager to search and install components of the Zerynth ecosystem.
A package is an archive generated from a tagged git repository and identified by a unique :samp:`fullname`.
There exist several package types, each one targeting a different Zerynth functionality:

* :samp:`core` packages contain core Zerynth components (i.e. the ZTC, the Studio, etc...)
* :samp:`sys` packages contain plaform dependent third party tools used by the ZTC (i.e. gcc, device specific tools, the Python runtime, etc..)
* :samp:`board` packages contain device definitions
* :samp:`vhal` packages contain low level drivers for various microcontroller families
* :samp:`lib` packages contain Zerynth libraries to add new modules to Zerynth programs

A package :samp:`fullname` is composed of three fields uniquely identifying the package:

* type
* namespace
* package name

For example, the package :samp:`lib.broadcom.bmc43362` contains the Python driver for the Broadcom bcm43362 wifi chip. 
Its fullname contains the type (:samp:`lib`), the namespace (:samp:`broadcom`) grouping all packages implementing Broadcom drivers, and the actual package name (:samp:`bcm43362`) specifying which particular driver is implemented.
A package has one or more available versions each one tagged following a modified `semantic versioning <http://semver.org>`_ scheme.

Moreover packages can belong to multiple "repositories" (collections of packages). There are two main public repositories, the :samp:`official` one, containing packages created, published and mantained by the Zerynth team, and the :samp:`community` one, containing packages created by community members.

The ZTC mantains a local databases of installed packages and refers to the online database of packages to check for updates and new packages.

    """
from base import *
import click
import datetime
import json
import sys
import re
import hashlib
import time
import hashlib
import webbrowser
from urllib.parse import quote_plus, unquote

def check_versions():
    try:
        res = zget(url=env.api.repo+"/versions", auth=None)
        return res
    except Exception as e:
        warning("Error while checking for updates",e)

def update_versions():
    repopath = fs.path(env.cfg, "versions.json")
    res = check_versions()
    if not res:
        warning("Can't retrieve updates")
    elif res.status_code == 304:
        pass
    elif res.status_code == 200:
        fs.set_json(res.json(),repopath)
        return res.json()
    else:
        warning("Error checking updates",res.status_code)

def check_matrix():
    try:
        res = zget(url=env.patchurl+"/matrix.json", auth=None)
        return res
    except Exception as e:
        warning("Error while checking for updates",e)

def update_matrix():
    mtxpath = fs.path(env.dist,"matrix.json")
    res = check_matrix()
    if not res:
        warning("Can't retrieve compatibility matrix")
    elif res.status_code == 304:
        pass
    elif res.status_code == 200:
        fs.set_json(res.json(),mtxpath)
        return res.json()
    else:
        warning("Error checking updates",res.status_code)


@cli.group(help="Manage packages.")
def package():
    pass


@package.command(help="Retrieve and store the available major releases of Zerynth")
def versions():
    """
.. _ztc-cmd-package-sync:

Available versions
------------------

The available versions of the full Zerynth suite can be retrieved with the command: ::

    ztc package versions

The command overwrites the local copy of available versions. 
Details about patches for each version are also contained in the database.

    """
    try:
        vrs = update_versions()
        update_matrix()
        if vrs:
            if not env.human:
                latest_installed = env.get_latest_installed_version()
                res = {
                    "versions":{},
                    "latest":latest_installed,
                    "last_hotfix": env.repo.get("hotfix","base"),
                    "major_update":False,
                    "minor_update":False
                }
                for v,p in vrs.items():
                    res["versions"][v]=p
                    if compare_versions(v,latest_installed)>0:
                        if compare_versions(res["latest"],v)<0:
                            res["latest"]=v
                            res["last_hotfix"]="base"
                            res["major_update"]=True
                if not res["major_update"]:
                    res["last_hotfix"]=res["versions"][env.var.version][-1]
                    res["minor_update"] = env.repo.get("hotfix","base")<res["last_hotfix"]

                if res["major_update"] or res["minor_update"]:
                    if res["major_update"]:
                        nfo = retrieve_packages_info(res["latest"])
                    else:
                        nfo = retrieve_packages_info()
                    res["changelog"] = nfo.get("changelogs",{}).get(res["last_hotfix"],"")
                    res["hotfixes"] = nfo.get("hotfixes",[])

                log_json(res)
            else:
                table = []
                for v,p in vrs.items():
                    table.append([v,p])
                log_table(table,headers=["version","hotfixes"])
    except Exception as e:
        fatal("Can't check versions",e)


@package.command(help="Retrieve and store current available packages")
@click.argument("version")
def available(version):
    """
.. _ztc-cmd-package-available:

Available packages
------------------

The list of official packages for a specific version of Zerynth can be retrieved with the command: ::

    ztc package available version

The command returns info on every official Zerynth package.

    """
    try:
        nfo = retrieve_packages_info()
        if nfo:
            if not env.human:
                log_json(nfo)
            else:
                table = []

                for pack in nfo["packs"]:
                    table.append([pack["fullname"],pack["patches"],pack["size"]//1024])
                table.sort()
                log_table(table,headers=["fullname","patches","size Kb"])
    except Exception as e:
        fatal("Can't check packages",e)


@package.command("info",help="Get info for package")
@click.argument("fullname")
def get_info(fullname):
    npth = retrieve_community()
    if not npth: 
        fatal("Can't find package info")

    for p in npth:
        if p["fullname"]==fullname:
            log_json(p)
            break
    else:
        fatal("Can't find package",fullname)



@package.command(help="Retrieve and store current available packages")
@click.argument("fullname")
def install_deps(fullname):
    _install_deps(fullname)

def do_install_deps(fullname):
    _install_deps(fullname)

def _install_deps(fullname):
    pack = tools.get_package(fullname)
    has_deps = tools.has_all_deps(fullname)
    if has_deps:
        info("All dependencies already installed!")
        return
    args = ["--keep","--no_runtime","--no_skip_msg","--no_progress"]
    for dep in pack.get("deps",[]):
        args.append("--tag")
        args.append(dep)
    for dep in tools.get_package_deps(fullname):
        args.append("--pack")
        args.append(dep)
    if not env.root:
        fatal("oops, something wrong with the installer!")
    zpm = fs.path(env.root,"zpm.py")
    e,out,_ = proc.runcmd("python",zpm,"install",env.repofile,*args,outfn=log)
    if e:
        fatal("oops, can't install dependencies!")
    info("All dependencies installed!")


# @package.command(help="Describe a hotfix relative to current installation")
# @click.argument("hotfix")
# def describe(hotfix):
#     try:
#         nfo = retrieve_packages_info()
#         if nfo:
#             res = {
#                 "packs":[],
#                 "changelog":""
#             }
#             res["changelog"]=nfo["changelogs"][hotfix]
#             for fullname in nfo.get("hotfixes",[]):
#                 pack = nfo["packs"][nfo["byname"][fullname]]
#                 if pack.get("sys",env.platform)!=env.platform:
#                     # skip, not for this platform
#                     continue
#                 res["packs"].append({
#                     "fullname":fullname,
#                     "size":pack["size"],
#                     "hash":pack["hashes"][-1]
#                 })

#             if not env.human:
#                 log_json(res)
#             else:
#                 table = []

#                 for pack in res["packs"]:
#                     table.append([pack["fullname"],pack["hash"],pack["size"]//1024 if pack["hash"]!="-" else "-"])
#                 table.sort()
#                 log_table(table,headers=["fullname","hash","size Kb"])
#     except Exception as e:
#         fatal("Can't describe patch",exc=e)

@package.command(help="Triggers a Zerynth update")
def trigger_update():
    """
.. _ztc-cmd-package-trigger:

Trigger Update
--------------

As soon as a new major release of Zerynth is available, it can be installed by triggering it with the following command: ::

    ztc package trigger_update

The next time the Zerynth installer is started, it will try to install the new version of Zerynth. 
    """
    fs.set_json({"version":env.var.version},fs.path(env.tmp,"major_release.json"))

@package.command(help="Triggers a Zerynth hotfix")
def trigger_hotfix():
    fs.set_json({"version":env.var.version},fs.path(env.tmp,"hotfix.json"))



@package.command(help="Install community packages")
@click.argument("fullname")
@click.argument("version")
def install(fullname,version):
    """
.. _ztc-cmd-package-install:

Install community packages
--------------------------

Community packages can be installed and updated with the following command: ::

    ztc package install fullname version

The package archive will be downloaded and installed from the corresponding Github release tarball.
    
    """
    flds = fullname.split(".")
    user = flds[1]
    reponame = flds[2]
    if flds[0]!="lib":
        fatal("No such package",fullname)
    # github url
    tarball = "https://github.com/"+user+"/"+reponame+"/archive/"+version+".tar.gz"
    outfile = fs.path(env.tmp,"community-"+user+"-"+reponame+".tar.gz")
    #namespace
    destdir = fs.path(env.libs,"community",user.replace("-","_"))
    #temporary unpacked dir
    tdir = fs.path(destdir,reponame+"-"+version)
    #reponame dir
    edir = fs.path(destdir,reponame.replace("-","_"))
    #ztc file with info
    zfile = fs.path(edir,".zerynth")
    try:
        info("Downloading",tarball) 
        if download_url(tarball,outfile):
            #untar
            fs.rmtree(tdir)
            fs.rmtree(edir)
            fs.makedirs(destdir)
            info("Unpacking in",destdir)
            fs.untargz(outfile,destdir)
            #find tdir...not always as expected (see release with v1.0.0 tag)
            for dd in fs.dirs(destdir):
                if fs.basename(dd).startswith(reponame+"-"):
                    tdir = dd
                    info("new tdir",tdir)
                    break

            #rename dir to correct reponame
            fs.move(tdir,edir)
            fs.set_json({
                "fullname":fullname,
                "version":version,
                "url":"https://github.com/"+user+"/"+reponame+"/tree/"+version,
                "import":user.replace("-","_")+"."+reponame.replace("-","_")
                },zfile)
            retrieve_community()
            info("Done")
        else:
            warning("Can't download",fullname)
    except Exception as e:
        warning("Can't install",fullname,e)
        fs.rmtree(tdir)
        fs.rmtree(edir)



@package.command(help="Authorize Zerynth to access Github use info")
@click.option("--user",default="")
@click.option("--token",default="")
def authorize(user,token):
    """
.. _ztc-cmd-package-authorize:

Github Authorization
--------------------

A necessary step in order to publish community packages is the generation of a Github authorization token
allowing the ZTC to interact with the user's Github repositories where the packages are stored and mantained.

Retrieve an authorization token with the following command: ::

    ztc package authorize

The Github authorization url for Zerynth will be opened in the system browser asking for the user credentials. Upon correct authorization, the Zerynth backend will display the user access token that must be copied back to the ZTC prompt. From this point on, the Zerynth user account will be associated with the Github account. 

    """
    if user and token:
        gdata = {"user":user,"access_token":token}
        fs.set_json(gdata,fs.path(env.cfg,"github.json"))
        info("Done")
        return
    try:
        res = zget(url=env.api.profile)
        rj = res.json()
        if rj["status"]=="success":
            state = rj["data"]["github"]["challenge"]
        else:
            fatal("Can't retrieve user info")
        log("Hello!")
        log("In a few seconds a browser will open to the Github authorization page")
        log("Once logged, copy the authorization token and paste it here")
        time.sleep(1)
        webbrowser.open(env.api.github+"&state=-"+state)
        token = input("Paste the token here and press enter -->")
        user,token = token.split(":")
        fs.set_json({"user":user,"access_token":token},fs.path(env.cfg,"github.json"))
        info("Done")
    except Exception as e:
        fatal("Can't get Github authorization",e)

@package.command(help="Publish a community library")
@click.argument("repo")
@click.argument("nfofile")
@click.option("--automatic",default=False)
def publish(repo,nfofile,automatic):
    """
.. _ztc-cmd-package-publish:

Publishing a community library
------------------------------

Zerynth projects can be published as library packages and publicly shared on different repositories (default is :samp:`community`). 
The library files need to be stored on a public Github repository owned by the user and the repository must be associated with the Zerynth user account by means
of the :ref:`authorize <ztc-cmd-package-authorize>` command. The authorization is necessary only on first time publishing; from there on, the Zerynth backend will automatically query Github for library updates.

The library updates are managed through `Github releases <https://help.github.com/articles/creating-releases/>`_; when a new version is ready, a Github release is created (manually or via ZTC) with a tag and a description. The release tag will be used as the library version while the release description will be used as library changelog. 




In order to convert a project into a publishable library, a json file with the library info must be created and filled with:

* :samp:`title`: the title of the library (will be shown in Zerynth Studio library manager)
* :samp:`description`: a longer description of the library (will be shown in Zerynth Studio library manager)
* :samp:`keywords`: an array of keywords to make the library easily searchable
* :samp:`version`: the version to assign to the current release of the library. It is suggested to keep using the Zerynth convention (rx.y.z).
* :samp:`release`: the current release description. It can be used as a changelog and it will be shown in Zerynth Studio as the text associated to this specific version of the library.

An example of such file: ::

    {
        "title": "DS1307 Real Time Clock",
        "description": "Foo's DS1307 RTC Driver ... ",
        "keywords": [
            "rtc",
            "maxim",
            "time"
        ],
        "release": "Fixed I2C bugs",
        "version": "r2.0.0"
    }

The library can be published in two ways: manual and automatic. In the manual procedure, the user is responsible for manually updating the Github repository and create the Github release. In this case, it is necessary to publish the library just once providing :samp:`title`,:samp:`description` and :samp:`keywords` in the json file. Each time the user adds a new release, the Zerynth backend will automatically include the new release in the available versions of the library. In the automatic procedure, the user is responsible for the creation of a Github repository to store the library while the management of the repository updates and the release creation is performed by th ZTC. In this case the additional :samp:`version` and :samp:`release` must be given in the json file. It is suggested to store the json file in the Github repository itself to track its changes.



The command: ::

    ztc package publish reponame json_file

will publish the library with the manual procedure. It just informs the Zerynth backend of a new association between :samp:`reponame` and the user account (already associated with a Github account). The user must then create every new Github release to make the library updates available to users.

The command: ::

    ztc package publish reponame json_file --automatic project_dir

will publish the library with the automatic procedure. The following operations are performed: 

    * the Zerynth backend is informed of a new association between :samp:`reponame` and the user account
    * the :samp:`reponame` Github repository is clone to a temp directory
    * the project files in the folder :samp:`project_dir` are copied to the cloned repository
    * a new commit is created
    * the commit is pushed to the Github repository master branch
    * the commit is tagged with the :samp:`version` field of :samp:`json_file`
    * a new Github release is created using the :samp:`release` field of :samp:`json_file` as the descriptive text


The resulting library will be importable as: ::

    from community.github_username.repo_name import ...

where :samp:`github_username` and :samp:`repo_name` are the Github username and Github repository name associated to the library, with minus signs (:samp:`-`) replaced by underscores (:samp:`_`).

For example, if the user :samp:`foo` wants to publish the :samp:`bar` library, the following steps must be taken: 

    * a json file with the required fields is created, :samp:`bar.json`.
    * the library files are stored in the folder :samp:`bar_lib`.
    * the command :samp:`ztc package publish bar --automatic bar_lib` is used to publish the library :samp:`community.foo.bar`  



Library Documentation
^^^^^^^^^^^^^^^^^^^^^

It is suggested to write the library documentation in the README.md file in the root of the repository. Zerynth Studio will redirect users to the Github repository page for doc info.


Library Examples
^^^^^^^^^^^^^^^^

Libraries can bedistributed with a set of examples stored under an :file:`examples` folder in the project. Each example must be contained in its own folder accordinto to the following requirements:

* The example folder name will be converted into the example "title" (shown in the Zerynth Studio example panel) by replacing underscores ("_") with spaces
* The example folder can contain any number of files, but only two are mandatory: :file:`main.py`, the entry point file and :file:`project.md`, a description of the example. Both files will be automatically included in the library documentation.

Moreover, for the examples to be displayed in the Zerynth Studio example panel, a file :file:`order.txt` must be placed in the :file:`examples` folder. It contains information about the example positioning in the example tree: ::

    ; order.txt of the lib.adafruit.neopixel package
    ; comments starts with ";"
    ; inner tree nodes labels start with a number of "#" corresponding to their level
    ; leaves corresponds to the actual example folder name
    #Adafruit
        ##Neopixel
           Neopixel_LED_Strips
           Neopixel_Advanced

    ; this files is translated to:
    ; example root
    ; |
    ; |--- ...
    ; |--- ...
    ; |--- Adafruit
    ; |        |--- ...
    ; |        \--- Neopixel
    ; |                |--- Neopixel LED Strips
    ; |                \--- Neopixel Advanced
    ; |--- ...
    ; |--- ...
    """
    nfo = fs.get_json(nfofile)
    if not nfo.get("keywords") or not nfo.get("title") or not nfo.get("description"): 
        fatal("Missing fields in",nfofile)
    if automatic and (not nfo.get("version") or not nfo.get("release")):
        fatal("Missing fields in",nfofile)

    data = {
        "repo":repo,
        "title":nfo["title"],
        "description":nfo["description"],
        "keywords":nfo["keywords"]
    }
    try:
        res = zpost(env.api.community,data)
        rj = res.json()
        if rj["status"] == "success":
            info("Thanks for publishing! You will receive an email with the library status")
        else:
            fatal("Can't publish!",rj["message"])
    except Exception as e:
        fatal("Can't publish",e)

    ## automatic publishing: automatic is the path of the project
    if not automatic: return
    gh = fs.get_json(fs.path(env.cfg,"github.json"))
    repopath = fs.path(env.tmp,"community_lib")
    fs.rmtree(repopath)
    # credentials as per: https://github.com/blog/1270-easier-builds-and-deployments-using-git-over-https-and-oauth
    git.git_clone_from_url("https://github.com/"+gh["user"]+"/"+repo,gh["access_token"],"x-oauth-basic",repopath)    
    info("Copying project...")
    for f in fs.all_files(automatic):
        if "/.git" not in f:
            dst = fs.path(repopath,fs.rpath(f,automatic))
            fs.makedirs(fs.dirname(dst))
            info("Copying",f,"to",dst)
            fs.copyfile(f,dst)
        else:
            info("Skipping",f)
    fs.rm_file(fs.path(repopath,".zproject")) 
    git.git_commit(repopath,"Zerynth Studio automatic commit")
    git.git_push(repopath,"origin",zcreds=False)
    # publish git release
    info("Publishing a new release on Github...")
    try:
        res = zpost(env.api.github_api+"/repos/"+gh["user"]+"/"+repo+"/releases?access_token="+gh["access_token"],{"tag_name":nfo["version"],"body":nfo["release"],"name":nfo["version"]},auth=False)
        if res.status_code==201 or res.status_code==200:
            info("Done")
        else:
            raise Exception("Github API error",res.status_code)
    except Exception as e:
        fatal("Error publishing the Github release",e)

@package.command(help="Get info about a github account")
def github():
    try:
        gh = fs.get_json(fs.path(env.cfg,"github.json"))
        url = env.api.github_api+"/users/"+gh["user"]+"/repos?per_page=100&access_token="+gh["access_token"]
        res = zget(url,auth=False)
        rj = res.json()
        if res.status_code==200:
            repos = []
            for repo in rj:
                if repo["private"]:
                    continue
                r = {
                    "name":repo["full_name"],
                    "reponame":repo["name"],
                    "url":repo["git_url"],
                    "fullname":repo["name"].replace("-","_"),
                    "import":repo["full_name"].replace("/",".").replace("-","_")
                }
                repos.append(r)
            log_json({
                "user":gh["user"],
                "repos":repos})
        else:
            raise Exception("API failure:"+str(res.status_code))
    except Exception as e:
        fatal("Can't retrieve Github credentials!",e)
        

def retrieve_packages_info(version=None):
    if not version:
        version = env.var.version
    try:
        res = zget(url=env.api.repo+"/repository/"+version,auth=False)
        if res.status_code == 200:
            npth = res.json()
            return npth
        else:
            debug("Can't get package list for",version,[res.status_code])
    except Exception as e:
        warning("Can't get package list for",version,e)

@package.command(help="Get community repository")
@click.option("--force",default=False,flag_value=True)
def repository(force):
    npth = retrieve_community(force)
    if npth:
        log_json(npth)

def retrieve_community(force=False):
    try:
        pfile = fs.path(env.cfg,"community.json")
        retrieve = not fs.exists(pfile) or fs.unchanged_since(pfile,3600) or force 
        if retrieve:
            debug("Retrieve from network")
            res = zget(url=env.api.repo+"/community",auth=False)
            if res.status_code == 200:
                npth = res.json()
                fs.set_json(npth,fs.path(env.cfg,"community.json"))
            else:
                debug("Can't get community repo",[res.status_code])
                if fs.exists(pfile):
                    npth = fs.get_json(pfile)
                else:
                    npth={}
        else:
            debug("Retrieve from disk")
            npth = fs.get_json(pfile)
        fln = {p["fullname"]:p for p in retrieve_installed_community()}
        for pp in npth:
            pp["last_version"]=pp["versions"][-1]
            pp["import"]="community."+pp["fullname"].replace("-","_")[4:]  #starts with lib
            fp = fln.get(pp["fullname"])
            if fp:
                pp["installed"]=fp["version"]
        
        return npth
    except Exception as e:
        warning("Can't get community repo",e)


def retrieve_installed_community():
    community = fs.all_files(fs.path(env.libs,"community"),filter=".zerynth")
    for p in community:
        try:
            pp = fs.get_json(p)
            yield {
                "fullname":pp["fullname"],
                "version":pp["version"],
                "url":pp["url"]
            }
        except:
            # .zerynth missing or bad
            pass


@package.command(help="List of all installed packages")
def installed():
    """
.. _ztc-cmd-package-installed:

Installed packages
------------------

The list of currently installed official and community packages (of type lib) can be retrieved with: ::

    ztc package installed

    """
    table = []
    inst = []
    official = fs.all_files(fs.path(env.libs,"official"),filter="z.yml")
    for p in official:
        try:
            pp = fs.get_yaml(p)
            inst.append({
                "fullname":pp["fullname"],
                "last_version":env.var.version,
                "import":pp["fullname"][4:],
                "repo":"official",
                "installed":env.var.version,
                "title":pp["title"],
                "keywords":pp.get("keywords",[]),
                "description":pp["description"]
                })
            table.append([pp["fullname"],env.var.version,"official",pp["title"],0])
        except:
            # subdirs can contain spurious package.json files
            pass
    for pp in retrieve_installed_community():
        inst.append({
            "fullname":pp["fullname"],
            "last_version":pp["version"],
            "repo":"community",
            "import":pp["fullname"].replace("-","_")[4:],
            "url":pp["url"]
        })

    if env.human:
        log_table(table,headers=["fullname","last version","repository","title","rating"])
    else:
        log_json(inst)

# @package.command(help="Checks and prepares updates")
# @click.option("--finalize",flag_value=True,default=False)
# def patches(finalize):

#     versions = env.versions
#     print(env.var.version)
#     curpatch = env.patches[env.var.version]
    
#     if not curpatch:
#         warning("Can't retrieve patch info")
#         return
   
#     patchid = curpatch
#     lastpatchid = versions[env.var.version][-1]

#     if lastpatchid==patchid:
#         info("No updates to apply")
#         return
   
#     npth = retrieve_packages_info()
#     if not npth:
#         warning("Can't retrieve current patch")
#         return

#     # create the patches
#     ppath=fs.path(env.tmp,"patch")
#     fs.rmtree(ppath)
#     fs.makedirs(ppath)
#     to_update = []
#     pres = {"packs":[]}
#     for pack in npth["packs"]:
#         fullname = pack["fullname"]
#         patches = pack["patches"]
#         # retrieve valid patches
#         packpatches = [ (x,pack["hashes"][i]) for i,x in enumerate(patches) if x>patchid and x<=lastpatchid ]
#         if not packpatches:
#             #this package must be skipped, already installed or newer 
#             continue
#         if pack.get("sys",env.platform)!=env.platform:
#             # skip, not for this platform
#             continue
#         to_update.append(pack)
#         if not finalize:
#             # skip donwload and install if not finalizing
#             continue
#         #finalize
#         pack = Var({
#             "fullname":fullname,
#             "version":env.var.version,
#             "repo":"official",
#             "type":fullname.split(".")[0],
#             "file":fs.path(env.tmp,fullname+"-"+env.var.version+".tar.xz")
#         })
#         packpatch,packhash = packpatches[-1]
#         todelete = packhash=="-"
#         if not todelete:
#             # download and unpack
#             info("Downloading",fullname)
#             if download_package(pack,env.var.version,packpatch) is not True:
#                 fatal("Error while downloading",fullname)
#         else:
#             info("Deleting",fullname)

#         if pack.type=="lib":
#             src,dst =  install_lib_patch(pack,pack.version,ppath,simulate = todelete)
#         elif pack.type=="core":
#             src,dst =  install_core_patch(pack,pack.version,ppath)
#         elif pack.type=="board":
#             src,dst =  install_device_patch(pack,pack.version,ppath,simulate = todelete)
#         elif pack.type=="vhal":
#             src,dst =  install_vhal_patch(pack,pack.version,ppath)
#         elif pack.type=="sys":
#             src,dst =  install_sys_patch(pack,pack.version,ppath)
#         else:
#             warning("unpatchable package",pack.fullname)
#             continue
#         pres["packs"].append({
#             "destdir":dst,
#             "srcdir":src  #src is empty if package need to be deleted
#         })
        

#     pres["patch"]=npth
#     pres["version"]=env.var.version
#     if finalize:
#         fs.set_json(pres,fs.path(env.tmp,"patchfile.json"))
#         # fs.set_json(npth,patchfile)
#         info("Update ready!")
#     else:
#         npth["packs"]=to_update
#         log_json(npth)

    

