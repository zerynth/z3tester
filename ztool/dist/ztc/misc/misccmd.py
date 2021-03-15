"""

.. _ztc-cmd-misc:

Miscellanea
===========

Non specific commands are grouped in this section.


.. _ztc-cmd-linter:

Linter
------

    Not documented yet.

   """

from base import *
from packages import *
import click




@cli.command("info",help="Display info about ZTC status.")
@click.option("--tools","__tools",flag_value=True, default=False,help="Display installed tools")
@click.option("--version","__version",flag_value=True, default=False,help="Display current version")
@click.option("--fullversion","__fullversion",flag_value=True, default=False,help="Display current version with patches")
@click.option("--modules","__modules",flag_value=True, default=False,help="Display installed Zerynth modules")
@click.option("--devices","__devices",flag_value=True, default=False,help="Display supported devices currently installed")
@click.option("--vms","__vms", help="Display installed virtual machines for a specific target")
@click.option("--examples","__examples",flag_value=True, default=False,help="Display the list of installed examples")
@click.option("--disk_usage","__disk_usage",flag_value=True, default=False,help="Display the disk used up by Zerynth installation")
@click.option("--messages","__messages",flag_value=True, default=False,help="Display the list of system messages")
def __info(__tools,__devices,__vms,__examples,__version,__fullversion,__modules,__messages,__disk_usage):
    """ 
Info
----

The :command:`info` command  displays information about the status of the ZTC.

It takes the following options (one at a time):

* :option:`--version` display the current version of the ZTC.
* :option:`--fullversion` display the current version of the ZTC together with current update.
* :option:`--devices` display the list of supported devices currently installed.
* :option:`--tools` display the list of available ZTC tools. A ZTC tool is a third party program used to accomplish a particular task. For example the gcc compiler for various architecture is a ZTC tool.
* :option:`--modules` display the list of installed Zerynth libraries that can be imported in a Zerynth program.
* :option:`--examples` display the list of installed examples gathered from all the installed libraries.
* :option:`--vms target` display the list of virtual machines in the current installation for the specified :samp:`target`
* :option:`--messages` display the list of unread system messages

    """
    if __tools:
        if env.human:
            table = []
            for k,v in tools.tools.items():
                if isinstance(v,str):
                    table.append([k,v])
                    #log(k,"=>",v)
                else:
                    for kk,vv in v.items():
                        table.append([k+"."+kk,vv])
            log_table(table)
        else:
            log_json(tools.tools)
        return

    if __devices:
        table = []
                
        for dev in tools.get_devices():
            if env.human:
                #TODO: print in human readable format
                table.append([dev["type"],dev.get("target","---"),dev.get("name","---")])
            else:
                log_json(dev)
        if env.human:
            log_table(table,headers=["type","target","name"])
        return
    if __vms:
        if ":" in __vms:
            __vms,chipid = __vms.split(":")
        else:
            chipid = None
        vms = tools.get_vms(__vms,chipid,full_info=True)
        vmdb = {}
        # im = ZpmVersion(env.min_vm_dep)                             # minimum vm version compatible with current ztc
               
        for uid,vmc in vms.items():
            vmf = vmc[0]
            vv= vmc[1]
            # ik = ZpmVersion(vv)   # vm version
            #if ik<im
            #log(vv)
            if not env.check_vm_compat(__vms,vv,True):
                # skip versions lower than min_dep
                continue
            # load vm
            vm = fs.get_json(vmf)
            target = vm["dev_type"]
            if target not in vmdb:
                vmdb[target]={}
            if vm["on_chip_id"] not in vmdb[target]:
                vmdb[target][vm["on_chip_id"]]=[]
            vmdb[target][vm["on_chip_id"]].append({
                "file": vmf,
                "target":target,
                "uuid":uid,
                "version":vm["version"],
                "features": vm["features"],
                "hash_features": vm["hash_features"],
                "chipid":vm["on_chip_id"],
                "name":vm["name"],
                "desc":vm.get("desc",""),
                "rtos":vm["rtos"],
                "patch":vm["patch"]
            })
        if env.human:
            table = []
            for target,chv in vmdb.items():
                for chipid,nfo in chv.items():
                    for nn in nfo:
                        table.append([target,chipid,nn["uuid"],nn["rtos"],nn["features"],nn["file"]])
            log_table(table,headers=["target","chipid","uid","rtos","features","path"])
        else:
            log_json(vmdb)
        return

    if __examples:
        exl = tools.get_examples()
        if env.human:
            table = []
            for ex in exl:
                table.append([ex["name"],ex["path"],ex["tag"]])
            log_table(table,headers=["title","path","tags"])
        else:
            log_json(exl)
        return

    if __version or __fullversion:
        vrs = env.var.version+"-"+env.repo.get("hotfix","base")
        if env.skin:
            vrs = vrs + " "+env.skin
        if __fullversion:
            log(vrs)
        else:
            log(env.var.version)
        return

    if __disk_usage:
        bytes= tools.disk_usage()
        bytes = int(bytes/1024/1024/1024*100)/100  # in Gb
        log(bytes)
        return

    if __modules:
        mods = tools.get_modules()
        if env.human:
            table = []
            for mod in sorted(mods):
                table.append([mod,mods[mod]])
            log_table(table,headers=["from","import"])
        else:
            log_json(mods)

    if __messages:
        msg_file = fs.path(env.cfg,"messages.json")
        if fs.exists(msg_file):
            try:
                msg_list = fs.get_json(msg_file)
                for msg in msg_list:
                    msg["read"]=True
            except:
                msg_list = []

        else:
            msg_list = []
        last_msg = msg_list[0]["visibleFrom"] if msg_list else ""
        try:
            res = zget(url=env.api.user+"/messages",params={"from":last_msg,"version":env.var.version})
            rj = res.json()
            if rj["status"]=="success":
                msg_list = rj["data"]["list"]+msg_list
                if env.human:
                    for k in msg_list:
                        log(k["visibleFrom"])
                        log(k["message"])
                        log("------------------------")
                else:
                    log_json(msg_list)
            else:
                critical("Can't retrieve message list",rj["message"])
        except Exception as e:
            critical("Can't retrieve message list",exc=e)
        msg_list = msg_list[:100]
        fs.set_json(msg_list,msg_file)
        

# @cli.command("hex2bin")
# @click.argument("hexfile",type=click.Path())
# @click.option("--output","-o",default=False,help="output file path")
# @click.option("--padto","-p",default=0,help="pad with zeroes up to size")
# def __hex2bin(hexfile,output,padto):
#     hex2bin(hexfile,output,padto)



@cli.command("clean",help="Clean up old installations and temp files")
@click.option("--tmp",default=False,flag_value =True,help="clear temporary folder")
@click.option("--inst",multiple=True,type=str,help="delete previous installed version (can be repeated multiple times)")
@click.option("--db",default=False,flag_value =True,help="forget all devices")
@click.option("--older",default=False,flag_value =True,help="delete all previous installations")
def __clean(tmp,inst,db,older):
    """ 
Clean
-----

The :command:`clean` command behave differently based on the following options:

* :option:`--tmp` if given clears the temporary folder.
* :option:`--inst version` can be repeated multiple times and removes a previous installed :samp:`version` of Zerynth
* :option:`--db` if given forgets all devices (clears all devices from database).

    """
    if tmp:
        info("Cleaning temp folder...")
        sz = fs.dir_size(env.tmp)
        fs.rmtree(env.tmp)
        fs.makedirs(env.tmp)
        info("Cleaned up",sz//(1024*1024),"Mb")
    if db:
        info("Forgetting all devices...")
        env.clean_db()
        info("Ok")

    inst = list(inst)
    if older:
        vdirs = fs.dirs(fs.path(env.dist,".."))
        for dir in vdirs:
            bdir = fs.basename(dir)
            if not match_version(bdir):
                continue
            if compare_versions(bdir,env.var.version)<0:
                inst.append(bdir)

    inst = set(inst)
    for ii in inst:
        if fs.exists(env.dist_dir(ii)):
            sz = fs.dir_size(env.dist_dir(ii))
            info("Removing installation",ii)
            fs.rmtree(env.dist_dir(ii))
            info("Cleaned up",sz//(1024*1024),"Mb")


