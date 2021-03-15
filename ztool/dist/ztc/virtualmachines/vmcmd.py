"""
.. _ztc-cmd-vm:

****************
Virtual Machines 
****************

Virtual machines are the core of Zerynth. From the point of view of the ZTC, a virtual machine is a binary blob to be flashed on a device
in order to enable Zerynth code execution. Virtual machines are tied to the unique identifier of the device microcontroller, therefore for each microcontroller a specific virtual machine must be created.

Virtual machines can be managed with the following commands:

* :ref:`create <ztc-cmd-vm-create>`
* :ref:`list <ztc-cmd-vm-list>`
* :ref:`available <ztc-cmd-vm-available>`
* :ref:`bin <ztc-cmd-vm-bin>`

It is also possible to create custom Virtual Machines for proprietary PCBs based on some Zerytnh supported microcontroller. The customizable parameters pertain to the GPIO routing (custom pinmap) and the selection of available peripherals. More custom parameters will be added in the future.

For the customization process please refer to the :ref:`dedicated section <ztc-cmd-cvm>`

    """
from base import *
from packages import *
from devices import get_device, get_device_by_target, probing
from jtag import *
import click
import datetime
import json
import sys
import base64
import re
import struct

def download_vm(uid,dev_type=None):
    res = zget(url=env.api.vm+"/"+uid)
    rj = res.json()
    if rj["status"]=="success":
        vmd = rj["data"]
        if not dev_type:
            vmpath = fs.path(env.vms, vmd["dev_type"],vmd["on_chip_id"])
        else:
            vmpath = fs.path(env.vms, dev_type, vmd["on_chip_id"])
            #update vm to custom device type
            vmd["original_type"]=vmd["dev_type"]
            vmd["dev_type"]=dev_type

        fs.makedirs(vmpath)
        vmname = uid+"_"+vmd["version"]+"_"+vmd["hash_features"]+"_"+vmd["rtos"]+".vm"
        fs.set_json(vmd, fs.path(vmpath,vmname))
        info("Downloaded Virtual Machine in", vmpath,"with uid",uid)
    else:
        fatal("Can't download virtual machine:", rj["message"])


@cli.group(help="Manage Zerynth Virtual Machine. This module contains all Zerynth Toolchain Commands for managing Zerynth Virtual Machine Entities.")
def vm():
    pass

@vm.command(help="Request virtual machine creation. \n\n Arguments: \n\n ALIAS: device alias. \n\n VERSION: requested virtual machine version. \n\n RTOS: virtual machine RTOS.")
@click.argument("alias")
@click.argument("version")
@click.argument("rtos")
@click.argument("patch", default="base")
@click.option("--feat", multiple=True, type=str,help="add extra features to the requested virtual machine (multi-value option)")
@click.option("--name", default="",help="Virtual machine name")
@click.option("--custom_target", default="",help="Original target for custom vms")
def create(alias,version,rtos,feat,patch,name,custom_target):
    """ 

.. _ztc-cmd-vm-create:

Create a Virtual Machine
------------------------

Virtual machine can be created with custom features for a specific device. Creation consists in requesting a virtual machine unique identifier (:samp:`vmuid`) to the Zerynth backend for a registered device.

The command: ::

    ztc vm create alias version rtos patch

executes a REST call to the Zerynth backend asking for the creation of a virtual machine for the registered device with alias :samp:`alias`. The created virtual machine will run on the RTOS specified by :samp:`rtos` using the virtual machine release version :samp:`version` at patch :samp:`patch`.

It is also possible to specify the additional option :option:`--feat feature` to customize the virtual machine with :samp:`feature`. Some features are available for pro accounts only. Multiple features can be specified repeating the option.

If virtual machine creation ends succesfully, the virtual machine binary is also downloaded and added to the local virtual machine storage. The :samp:`vmuid` is printed as a result.

    """
    dev = env.get_dev_by_alias(alias)
    if len(dev)==0:
        fatal("No such device")
    if len(dev)>1:
        fatal("Ambiguous alias")
    dev=dev[0]
    if not dev.remote_id:
        fatal("Device",dev.alias,"not registered")
    vminfo = {
        "name":name or (dev.name+" "+version),
        "dev_uid":dev.remote_id,
        "version": version,
        "rtos": rtos,
        "patch":patch,
        "features": feat
        }
    _vm_create(vminfo,custom_target=None if not custom_target else custom_target)



def _vm_create(vminfo,custom_target=None):
    info("Creating vm for device",vminfo["dev_uid"])
    try:
        res = zpost(url=env.api.vm, data=vminfo,timeout=20)
        rj = res.json()
        if rj["status"] == "success":
            vminfo["uid"]=rj["data"]["uid"]
            info("VM",vminfo["name"],"created with uid:", vminfo["uid"])
            download_vm(vminfo["uid"],custom_target)
            return vminfo["uid"]
        else:
            critical("Error while creating vm:", rj["message"])
    except TimeoutException as e:
        critical("No answer yet")
    except Exception as e:
        critical("Can't create vm", exc=e)

@vm.command(help="Request virtual machine creation given device uid")
@click.argument("dev_uid")
@click.argument("version")
@click.argument("rtos")
@click.argument("patch")
@click.option("--feat", multiple=True, type=str,help="add extra features to the requested virtual machine (multi-value option)")
@click.option("--name", default="",help="Virtual machine name")
@click.option("--custom_target", default="",help="Original target for custom vms")
@click.option("--share", default=False, flag_value=True, help="Create shareable VM")
@click.option("--reshare", default=False, flag_value=True, help="Create shareable VM")
@click.option("--locked", default=False, flag_value=True, help="Create a locked VM")
def create_by_uid(dev_uid,version,rtos,feat,name,patch,custom_target,share,reshare,locked):
    _create_by_uid(dev_uid,version,rtos,feat,name,patch,custom_target,share,reshare,locked)


def do_create_by_uid(dev_uid,version,rtos,feat,name,patch,custom_target,share,reshare,locked):
    return _create_by_uid(dev_uid,version,rtos,feat,name,patch,custom_target,share,reshare,locked)

def _create_by_uid(dev_uid,version,rtos,feat,name,patch,custom_target,share,reshare,locked):
    vminfo = {
        "name": name or ("dev:"+dev_uid),
        "dev_uid":dev_uid,
        "version": version,
        "rtos": rtos,
        "patch":patch,
        "features": feat,
        "shared":[] if not share else ["*"],
        "reshareable":reshare,
        "locked":locked
        }
    return _vm_create(vminfo,custom_target=None if not custom_target else custom_target)


def _own_vm(vm_uid):
    res = zpost(url=env.api.vm+"/"+vm_uid,data={})
    rj = res.json()
    if rj["status"]=="success":
        vmd = rj["data"]
        info("VM",vm_uid,"successfully owned with chip_id",vmd["chip_id"],"and target",vmd["dev_type"])
        return vmd["chip_id"],vmd["dev_type"],vmd["dev_uid"]
    else:
        fatal("Can't own virtual machine",vm_uid,rj["message"])

def _vmuid_dev(dev):
    if not dev.port:
        fatal("Device has no serial port! Check that drivers are installed correctly...")
    # open channel to dev TODO: sockets
    conn = ConnectionInfo()
    conn.set_serial(dev.port,**dev.connection)
    ch = Channel(conn)
    try:
        ch.open(timeout=2)
    except:
        fatal("Can't open serial:",dev.port)

    try:
        version,vmuid,chuid,target = probing(ch,dev, True if not dev.fixed_timeouts else False)
        ch.close()
        return vmuid,version,target,chuid
    except Exception as e:
        warning(e)
        try:
            ch.close()
        except:
            warning("Error while closing serial")
        if dev.uplink_reset:
            fatal("Something wrong during the probing phase: too late reset or serial port already open?")
        else:
            fatal("Something wrong during the probing phase:",e)

def retrieve_vm_uid(alias):
    dev = get_device(alias,5)
    vm_uid,version,target,chipid = _vmuid_dev(dev)
    if target!=dev.target:
        fatal("Target mismatch!",target,"vs",dev.target)
    return vm_uid,version,target,chipid,dev


def retrieve_vm_uid_raw(target,__specs):
    options = {}
    for spec in __specs:
        pc = spec.find(":")
        if pc<0:
            fatal("invalid spec format. Give key:value")
        options[spec[:pc]]=spec[pc+1:]
    dev = get_device_by_target(target,options)
    vm_uid,version,target,chipid = _vmuid_dev(dev)
    if target!=dev.target:
        fatal("Target mismatch!",target,"vs",dev.target)
    return vm_uid,version,target,chipid,dev


def _reg_owning(dev,remote_uid,chipid):
    # register device
    dev = dev.to_dict()
    dev["chipid"]=chipid
    dev["remote_id"]=remote_uid
    env.put_dev(dev,linked=dev.get("sid")=="no_sid")

@vm.command(help="Redeem third party VM by uid")
@click.argument("vm_uid")
def own(vm_uid):
    chipid, devtype, remote_uid = _own_vm(vm_uid)

@vm.command(help="Redeem third party VM by uid taken from device")
@click.argument("alias")
def own_alias(alias):
    vm_uid,version,target,chipid,dev = retrieve_vm_uid(alias)
    chipid, devtype, remote_uid = _own_vm(vm_uid)
    _reg_owning(dev,remote_uid,chipid)

@vm.command(help="Redeem third party VM by uid taken from device raw")
@click.argument("target")
@click.option("--spec","__specs",default="",multiple=True)
def own_target(target,__specs):
    vm_uid,version,target,chipid,dev = retrieve_vm_uid_raw(target,__specs)
    chipid, devtype, remote_uid = _own_vm(vm_uid)
    # _reg_owning(dev,remote_uid,chipid)


@vm.command(help="Redeem third party VM by uid taken from device by probe")
@click.argument("target")
@click.argument("probe")
def own_by_probe(target,probe):
    dev = get_device_by_target(target,{},skip_reset=True)
    if not dev.jtag_capable:
        fatal("Target does not support probes!")
    tp = start_temporary_probe(target,probe)
    try:
        vm_uid = dev.get_vmuid()
    except Exception as e:
        vm_uid = None
        warning(e)
    stop_temporary_probe(tp)
    if vm_uid:
        chipid, devtype, remote_uid = _own_vm(vm_uid)
        # _reg_owning(dev,remote_uid,chipid)
    else:
        fatal("Can't retrieve vm uid!")


@vm.command("download",help="Download VM by uid")
@click.argument("vm_uid")
def vm_download(vm_uid):
    download_vm(vm_uid)


@vm.command("list", help="List all owned virtual machines")
@click.option("--from","_from",default=0,help="skip the first n virtual machines")
@click.option("--dev_uid","_dev_uid",default=None,help="ask for specific device")
def __list(_from,_dev_uid):
    """ 
.. _ztc-cmd-vm-list:

List Virtual Machines
---------------------

The list of created virtual machines can be retrieved with the command: ::

    ztc vm list

The retrieved list contains at most 50 virtual machines.

Additional options can be provided to filter the returned virtual machine set:

* :option:`--from n`, skip the first :samp:`n` virtual machines

    """
    table=[]
    try:
        prms = {"from":_from}
        prms["version"]=env.var.version
        prms["dev_uid"]=_dev_uid
        res = zget(url=env.api.vm,params=prms)
        rj = res.json()
        if rj["status"]=="success":
            if env.human:
                for k in rj["data"]["list"]:
                    table.append([_from,k["uid"],k["name"],k["version"],k["patch"],k["dev_type"],k["rtos"],k["features"]])
                    _from += 1
                log_table(table,headers=["Number","UID","Name","Version","Patch","Dev Type","Rtos","Features"])
            else:
                log_json(rj["data"])
        else:
            critical("Can't get vm list",rj["message"])
    except Exception as e:
        critical("Can't get vm list",exc=e)

@vm.command(help="List available virtual machine parameters. \n\n Arguments: \n\n TARGET: target of the virtual machine")
@click.argument("target")
@click.option("--oneperline", default=False,flag_value=True, help="If Json output, one VM per line")
def available(target,oneperline):
    """ 
.. _ztc-cmd-vm-available:

Virtual Machine parameters
--------------------------

For each device target a different set of virtual machines can be created that takes into consideration the features of the hardware. Not every device can run every virtual machine. The list of available virtual machines for a specific target can be retrieved by: ::

    ztc vm available target

For the device target, a list of possible virtual machine configurations is returned with the following attributes:

* virtual machine version 
* RTOS
* additional features
* free/pro only

    """
    __vm_available(target,oneperline)

def do_vm_available(target,oneperline=False):
    __vm_available(target,oneperline)

def do_get_latest_vm(target):
    hh = env.human
    env.human = False
    lvm = __vm_available(target,oneperline=True,return_last=True)
    env.human = hh
    return lvm

def __vm_available(target,oneperline=False,return_last=False):
    table=[]
    try:
        res = zget(url=env.api.vmlist+"/"+target+"/"+env.var.version)
        rj = res.json()
        if rj["status"]=="success":
            if env.human:
                vml = rj["data"]["versions"]
                for vv, vmm in vml.items():
                    vmt = vmm["vms"]["base"]
                    for vm in vmt:
                        table.append([vm["title"],vm["description"],vm["rtos"],vm["features"],"Premium" if vm["pro"] else "Starter",vv])
                table = sorted(table, key= lambda x: x[5],reverse=True)
                log_table(table,headers=["Title","Description","Rtos","Features","Type","Version"])
            else:
                if oneperline:
                    data = rj["data"]
                    if not data:
                        return
                    info = data.get("info")
                    vms = []
                    for v,vmi in data.get("versions",{}).items():
                        for vx in vmi["vms"]["base"]:
                            vm = {}
                            vm["target"]=target
                            vm["version"]=v
                            vm["rtos"]=vx["rtos"]
                            vm["features"]=vx["features"]
                            vf = [ info["features"].get(x,"") for x in vm["features"] ]
                            vf = sorted(vf)
                            vm["xfeatures"] = vf
                            vm["description"] = ", ".join(vf) or "Standard"
                            vms.append(vm)
                    vms=sorted(vms,key=lambda x: -int32_version(x["version"]))
                    if return_last:
                        return vms[0]
                    for vm in vms:
                        log_json(vm)
                else:
                    log_json(rj["data"])
        else:
            fatal("Can't get vm list",rj["message"])
    except Exception as e:
        critical("Can't retrieve available virtual machines",exc=e)

@vm.command("bin", help="Convert a VM to binary format")
@click.argument("uid")
@click.option("--path", default="",help="Path for bin file")
def __bin(uid, path):
    """ 
.. _ztc-cmd-vm-bin:

Virtual Machine Binary File
---------------------------

The binary file(s) of an existing virtual machine can be obtained with the command: ::

    ztc vm bin uid

where :samp:`uid` is the unique identifier of the virtual machine

Additional options can be provided:

* :option:`--path path` to specify the destination :samp:`path`

    """
    vm_file = None
    vm_file = tools.get_vm_by_uid(uid)
    #print(vm_file)
    if not vm_file:
        fatal("VM does not exist, create one first")
    try:
        vmj = fs.get_json(fs.path(vm_file))
        if path:
            vmpath = path
        else:
            vmpath = fs.path(".")
        #info("Generating binary for vm:", vmj["name"], "with rtos:", vmj["rtos"], "for dev:", vmj["dev_uid"])
        if "bin" in vmj and isinstance(vmj["bin"], str):
            fs.write_file(base64.standard_b64decode(vmj["bin"]), fs.path(vmpath, "vm_"+vmj["dev_type"]+".bin"))
        elif "bin" in vmj and isinstance(vmj["bin"], list):
            for count,bb in enumerate(vmj["bin"]):
                fs.write_file(base64.standard_b64decode(bb), fs.path(vmpath, "vm_"+vmj["dev_type"]+"_part_"+str(count)+".bin"))
        info("Created vm binary in", vmpath)
    except Exception as e:
        fatal("Generic Error", e)

@vm.command("reg", help="Convert a registering bootloader to binary format")
@click.argument("target")
@click.option("--path", default="",help="Path for bin file")
def __reg(target, path):
    """ 
.. _ztc-cmd-vm-reg:

Registering Binary File
-----------------------

The binary file(s) of a a registering bootloader can be obtained with the command: ::

    ztc vm reg target

where :samp:`target` is the name of the device to register.

Additional options can be provided:

* :option:`--path path` to specify the destination :samp:`path`

    """
    reg_file = fs.path(env.devices,target,"register.vm")
    if not reg_file:
        fatal("No such target",target)
    try:
        vmj = fs.get_json(reg_file)
        if path:
            vmpath = path
        else:
            vmpath = fs.path(".")
        info("Generating binary...")
        if "bin" in vmj and isinstance(vmj["bin"], str):
            fs.write_file(base64.standard_b64decode(vmj["bin"]), fs.path(vmpath, "reg_"+target+".bin"))
        elif "bin" in vmj and isinstance(vmj["bin"], list):
            for count,bb in enumerate(vmj["bin"]):
                fs.write_file(base64.standard_b64decode(bb), fs.path(vmpath, "reg_"+target+"_part_"+str(count)+".bin"))
    except Exception as e:
        fatal("Generic Error", e)

################# CUSTOM VMs

@vm.group(help="Manage custom virtual machines.")
def custom():
    """
.. _ztc-cmd-vm-custom:

***********************
Custom Virtual Machines 
***********************

Some Zerynth VMs are customizable. The process of customization can be handled entirely via ZTC commands. In order to create a custom VMs the following steps are needed:

    1. List the supported customizable microcontrollers with the :ref:`vm custom original <ztc-cmd-vm-custom-original>` command
    2. Choose a short name for the custom VM and create it starting from one of the available microcontrollers listed in step 1
    3. The newly created custom VM configuration can be found under the Zerynth folder in the cvm/short_name directory
    4. Before being usable, the custom VM template specifying the role of each pin must be compiled with the :ref:`dedicated command <ztc-cmd-vm-custom-compile>`
    5. The compilation step takes as input a Yaml template file (short_name.yml) and generates the binary file (port.bin) needed for VM customization
    6. Once compiled, the new VM will behave as a normal VM and the standard Zerynth flow of device registration, VM creation and virtualization will be available for the choosen short_name. The only difference is that the port.bin file will be transparently flashed during the virtualization phase.
    7. As an add-on, a new device type is create together with the VM in order to allow automatic discovery of the custom device for seamless integration in Zerynth Studio and other third party IDEs. As detailed below, some parameters of the device (e.g. usb VID:PID) can be defined in the custom VM template
    8. Each time the VM template is changed, it must be recompiled and the VM revirtualized in order for the changes to take effect
    

It is also possible to export custom VMs to file or to Github in order to easily distribute custom VMs.

    """
    pass


@custom.command("create")
@click.argument("target")
@click.argument("short_name")
@click.option("--name",default="",help="Set custom device name")
def _custom_create(target,short_name,name):
    """
.. _ztc-cmd-vm-custom-create:

Create Custom VM
----------------

The command: ::

    ztc vm custom create target short_name

clones the configuration files for the :samp:`target` customizable VM into a custom VM instance named :samp:`short_name`.
The command creates a directory cvm/short_name under the Zerynth folder containing the following items:

    * :samp:`short_name.yml`: the Yaml template file specifying the VM custom parameters. Upon creation, it is initialized with the parameters for one of the existing devices based on the selected microcontroller
    * :samp:`device.json`: a json document containing info about the device that will host the VM. Such document is generated starting from parameters contained in the Yanml template.
    * :samp:`short_name.py`: a Python module that is used by the ZTC to automatically discover the custom device.
    * :samp:`port` and :samp:`svg` folders: configuration files needed for correct bytecode generation and management for the custom VM. The only possible customization is adding a :samp:`short_name.svg` under the :samp:`svg` folder in order to provide a visual representation of the custom device pinmap in Zerynth Studio.
    * :samp:`register.vm`: the registration bootloader to allow registering the custom device.

The custom VMs are entirely local and not saved on Zerynth servers. For this reason it is suggested to export the custom VM files and store them somewhere safe. Moreover, the choosen short name is never saved on Zerynth server and each custom device will be registered as a device of type :samp:`target`. The link between :samp:`target` and :samp:`short_name` is done on the development machine.

    """
    dev = tools.get_target(target)
    if not dev:
        fatal("Target does not exists!")
    if not dev.customizable:
        fatal("Target does not support custom VMs!")
    if short_name.count("_")>1:
        fatal("Too many underscores in the given short_name!")
    if len(short_name)>31:
        fatal("short_name too long! max 31 ascii chars allowed...")
    tdir = fs.path(env.devices,target)
    ddir = fs.path(env.cvm,short_name)
    fs.copytree(tdir,ddir)
    #remove unneeded
    fs.rmtree(fs.path(ddir,"docs"))
    fs.rmtree(fs.path(ddir,"__pycache__"))
    fs.rmtree(fs.path(ddir,".git"))
    fs.rm_file(fs.path(ddir,"package.json"))

    djf = fs.path(ddir,"device.json") 
    yjf = fs.path(ddir,"template.yml")
    cjf = fs.path(ddir,short_name+".yml")
    pjf = fs.path(ddir,short_name+".py")
    dj = fs.get_json(djf)
    #update device.json fields
    djname = short_name+"Device" 
    oldname = dj["virtualizable"]
    oldtarget = dj["target"]
    dj["target"]=short_name
    dj["classes"]=[short_name+"."+djname]
    dj["virtualizable"]=djname
    dj["jtag_class"]=djname
   
    # create new template by concatenating files
    # this is because yaml.dump does not mantain the order of keys
    ytmpl = fs.readfile(yjf)
    ytmpl = ytmpl.replace("XXXX_short_name_XXXX",short_name)
    tmpl = {}
    # add device info to template
    tmpl["device"]=dj
    tmpl["device"]["original_target"]=oldtarget
    if name:
        tmpl["device"]["name"]=name
    # remove customizable property: on first compile "customized" will be added
    del tmpl["device"]["customizable"]
    tmpstr = fs.set_yaml(tmpl,None)  # dump to string 
    #remove start and end
    tmpstr = tmpstr.replace("---\n","").replace("...\n","")
    #concat to template
    ytmpl=ytmpl+"\n"+tmpstr+"    vids: []\n    pids: []"

    # rename device class
    fs.move(fs.path(ddir,target+".py"),pjf)
    djs = fs.readfile(pjf)
    djs = djs.replace(oldname,djname)
    fs.write_file(djs,pjf)
    
    # update device.json
    fs.set_json(dj,djf)

    # save template
    fs.write_file(ytmpl,cjf)
    info("Custom device created at",ddir)

        
@custom.command("compile")
@click.argument("short_name")
def _custom_compile(short_name):
    """
.. _ztc-cmd-vm-custom-compile:

Compile Custom VM Template
--------------------------

The command: ::

    ztc vm custom compile short_name

compiles the :samp:`short_name.yml` template file of a custom VM to binary form.
The format of the template file is documented in the Yaml file itself.

Upon successful compilation, the custom VM is made available to all other VM related commands (registration, virtualization,...).

    """
    cvm_dir = fs.path(env.cvm,short_name)
    if not fs.exists(cvm_dir):
        fatal("Custom device does not exist yet! Run the create command first...")
    cvm_tmpl = fs.path(cvm_dir,short_name+".yml")
    cvm_port = fs.path(cvm_dir,"port.yml")
    cvm_bin = fs.path(cvm_dir,"port.bin")
    cvm_dev = fs.path(cvm_dir,"device.json")
    
    # generate cvm files:
    # - yaml original template
    # - yaml file for compiler
    # - binary cvminfo

    tmpl = fs.get_yaml(cvm_tmpl)
    tmpl["device"]["customized"]=True
    info("Saving binary template @",cvm_bin)
    _custom_generate(tmpl,cvm_port,cvm_bin)
    info("Saving device info @",cvm_dev)
    fs.set_json(tmpl["device"],cvm_dev)
    info("Activating custom vm")
    fs.set_json({"short_name":short_name},fs.path(cvm_dir,"active"))
    info("Done")

@custom.command("remove")
@click.argument("short_name")
def _custom_remove(short_name):
    """
.. _ztc-cmd-vm-custom-remove:

Remove Custom VM
----------------

The command: ::

    ztc vm custom remove short_name

deletes the custom VM identified by :samp:`short_name` from the system.
    """
    cvmdir = fs.path(env.cvm,short_name)
    fs.rmtree(cvmdir)



@custom.command("export")
@click.argument("short_name")
@click.argument("destination")
def _custom_export(short_name,destination):
    """
.. _ztc-cmd-vm-custom-export:

Export Custom VMs
-----------------

The command: ::

    ztc vm custom export short_name destination

exports the custom VM identified by :samp:`short_name` to :samp:`destination`. If :samp:`destination` is a folder, a file :samp:`short_name.tar.xz` will be generated in the folder packing together all the needed custom VM files. Such archive can be shared with other users completely enabling them to use the custom device and custom VM with their ZTC. If :samp:`destination` is a Github url, the custom VM files are pushed to the repository (provided that Github credentials are known to the ZTC).

    """
    cvmdir = fs.path(env.cvm,short_name)
    active = fs.path(cvmdir,"active")
    if not fs.exists(cvmdir):
        fatal("Custom VM does not exist!")
    if not fs.exists(active):
        fatal("Can't export, VM has not been compiled yet!")
    #remove pycache
    fs.rmtree(fs.path(cvmdir,"__pycache__"))

    if destination.startswith("https://github.com") or destination.startswith("git://github.com"):
        destination = destination.replace("git://","https://")
        tmpdir = fs.get_tempdir()
        gh = fs.get_json(fs.path(env.cfg,"github.json"))
        info("Cloning repo...")
        git.git_clone_from_url(destination,gh["access_token"],"x-oauth-basic",tmpdir)
        info("Updating repo...")
        for f in fs.all_files(cvmdir):
            if "/.git" not in f:
                dst = fs.path(tmpdir,fs.rpath(f,cvmdir))
                fs.makedirs(fs.dirname(dst))
                info("Copying",f,"to",dst)
                fs.copyfile(f,dst)
            else:
                info("Skipping",f)
        git.git_commit(tmpdir,"Zerynth Studio automatic commit")
        git.git_push(tmpdir,"origin",zcreds=False)
        fs.del_tempdir(tmpdir)
    else:
        if not fs.exists(destination):
            fatal("Destination folder",destination,"does not exist!")
        outfile = fs.path(destination,short_name+".tar.xz")
        fs.tarxz(cvmdir,outfile,filter="/.git")
        info("Custom VM exported at",outfile)


@custom.command("import")
@click.argument("source")
def _custom_import(source):
    """
.. _ztc-cmd-vm-custom-import:

Import Custom VMs
-----------------

The command: ::

    ztc vm custom import source

imports a custom VM from :samp:`source`. If :samp:`source` is a tar.xz file generated by the export command, it is unpacked and installed in the current Zerynth instance. If :samp:`source` is a Github repository, it is cloned and installed.

    """
    if source.startswith("https://github.com"):
        tmpdir = fs.get_tempdir()
        git.git_clone_from_url(source,None,None,tmpdir)
        try:
            active=fs.path(tmpdir,"active")
            active = fs.get_json(active)
            short_name = active["short_name"]
            cvmdir = fs.path(env.cvm,short_name)
            fs.copytree(tmpdir,cvmdir)
        except Exception as e:
            fatal("repository seems corrupted:",e)
        finally:
            fs.del_tempdir(tmpdir)
    else:
        #import from archive
        tmpdir = fs.get_tempdir()
        try:
            fs.untarxz(source,tmpdir)
            active=fs.path(tmpdir,"active")
            active = fs.get_json(active)
            short_name = active["short_name"]
            cvmdir = fs.path(env.cvm,short_name)
            fs.copytree(tmpdir,cvmdir)
        except Exception as e:
            fatal("file seems corrupted:",e)
        finally:
            fs.del_tempdir(tmpdir)
        
@custom.command("original")
def _custom_list_original():
    """
.. _ztc-cmd-vm-custom-original:

List customizable VMs
---------------------

The command: ::

    ztc vm custom original

lists the VMs that are customizable. Not all VMs support customization. The output of the command contains the list of :samp:`target` names to be used in the :ref:`create <ztc-vm-custom-create>` command.

    """
    lst = []

    for dev in tools.get_devices():
        if dev.get("customizable") and dev["path"].startswith(env.devices):
            lst.append(dev)
            if env.human:
                log(dev["target"])
    if not env.human:
        log_json(lst)

@custom.command("list")
def _custom_list():
    """
.. _ztc-cmd-vm-custom-list:

List custom VMs
---------------

The command: ::

    ztc vm custom list

prints the list of custom VMs available on the current Zerynth instance.

    """
    lst = []
    for d in fs.dirs(env.cvm):
        ff = fs.path(d,"active")
        try:
            tmpl = fs.get_yaml(fs.path(d,fs.basename(d)+".yml"))
            lst.append({
                "target":tmpl["short_name"],
                "original_target":tmpl["device"]["original_target"],
                "name":tmpl["device"]["name"],
                "chip":tmpl["device"]["chip_model"],
                "active":fs.exists(ff)
            })
            if env.human:
                log(d)
        except Exception as e:
            warning("Can't read",d,e)
    if not env.human:
        log_json(lst)
            
##################

_classes = {
    "D":0x0000,
    "A":0x0100,
    "ADC":0x0100,
    "SPI":0x0200,
    "I2C":0x0300,
    "PWM":0x0400,
    "ICU":0x0500,
    "CAN":0x0600,
    "SER":0x0700,
    "DAC":0x0800,
    "LED":0x0900,
    "BTN":0x0A00
}

_classes_id = {
    0x01: "ADC",
    0x02: "SPI",
    0x03: "I2C",
    0x04: "PWMD",
    0x05: "ICUD",
    0x06: "CAN",
    0x07: "SERIAL",
    0x08: "DAC",
    0x09: "LED",
    0x0A: "BTN",
    0x0D: "HTM",
    0x0E: "RTC"
    }

_flags = {
    "SPI":1<<0x02,
    "I2C":1<<0x03,
    "SER":1<<0x07,
    "CAN":1<<0x06,
    "PWM":1<<0x04,
    "ICU":1<<0x05,
    "ADC":1<<0x01,
    "DAC":1<<0x08,
    "EXT":1<<0x00
}

_prphs = {
    "SER":0x700,
    "SPI":0x0200,
    "I2C":0x0300,
    "ADC":0x0100,
    "PWMD":0x0400,
    "ICUD":0x0500,
    "CAN":0x0600,
    "SD":0x0C00,
    "RTC":0x2000
}

_names = {
    "SPI":["MOSI","MISO","SCLK"],
    "I2C":["SDA","SCL"],
    "SER":["RX","TX"],
    "CAN":["CANRX","CANTX"],
    "PWM":["PWM"],
    "ICU":["ICU"],
    "ADC":["A"],
    "DAC":["DAC"],
    "BTN":["BTN"],
    "LED":["LED"]
}

_s_classes = {
    "ADC": "_analogclass",
    "SPI": "_spiclass",
    "I2C": "_i2cclass",
    "PWM": "_pwmclass",
    "ICU": "_icuclass",
    "CAN": "_canclass",
    "DAC": "_dacclass",
    "LED": "_ledclass",
    "BTN": "_btnclass"
}

_ports = {
    "PA":0,
    "PB":1,
    "PC":2,
    "PD":3,
    "PE":4,
    "PF":5,
    "PG":6,
    "PH":7
}

_psplitter = re.compile("([A-Z]+)([0-9]+)")

def get_pin_class(pinname):
    mth = _psplitter.match(pinname)
    if not mth:
        return ""
    pin = mth.group(1)
    num = int(mth.group(2))
    for cls,cls_names in _names.items():
        if pin in cls_names:
            return cls

    return ""

def get_prph(prph):
    if prph.startswith("I2C"):
        return prph[0:3],int(prph[3:])
    mth = _psplitter.match(prph)
    if not mth:
        return "",-1
    return mth.group(1),int(mth.group(2))

def _get_sorted_classes(tbl,cls):
    if cls in ["SPI","I2C","SER"]:
        ret = []
        if cls=="SER":
            n = len(tbl)//2
            for i in range(n):
                ret.append("RX"+str(i))
                ret.append("TX"+str(i))
        elif cls=="SPI":
            n = len(tbl)//3
            for i in range(n):
                ret.append("MOSI"+str(i))
                ret.append("MISO"+str(i))
                ret.append("SCLK"+str(i))
        elif cls=="I2C":
            n = len(tbl)//2
            for i in range(n):
                ret.append("SDA"+str(i))
                ret.append("SCL"+str(i))
        return ret
    else:
        return sorted(tbl)

def _get_pin_code(pin):
    mth = _psplitter.match(pin)
    if not mth:
        return -1
    pin = mth.group(1)
    num = int(mth.group(2))
    if pin=="RX":
        return 0x0700+2*num
    elif pin=="TX":
        return 0x0701+2*num
    elif pin=="SDA":
        return 0x0300+2*num
    elif pin=="SCL":
        return 0x0301+2*num
    elif pin=="MOSI":
        return 0x0200+3*num
    elif pin=="MISO":
        return 0x0201+3*num
    elif pin=="SCLK":
        return 0x0202+3*num
    return -1

def _pad_to(bb,pad=16):
    if len(bb)%pad==0:
        return bb
    padding = pad - len(bb)%pad
    bb.extend(b'\x00'*padding)
    return bb


# @custom.command("compile")
# @click.argument("template")
# @click.argument("outdir")
def _custom_generate(tmpl,ymlfile,binfile):
    short_name = tmpl["short_name"]
    port = {}
    pinmap = tmpl["pinmap"]
    pinclasses = tmpl["pinclasses"]
    peripherals = tmpl["peripherals"]
    
    pin_names = ["D"+str(i) for i in range(0,256)]
    npins = len(pinmap)
    cls_table = {}
    prph_table = {}
    vbl_table = {}
    prphs = set()

    for i in range(npins):
        pin = "D"+str(i)
        pindata = pinmap.get(pin)
        if not pindata or len(pindata)!=2:
            fatal("Missing pinmap for pin", pin)
        pindata.append(set([1])) # prepare space for flags: add ext
        
        
    # search pin attributes
    # fill pinmap with pin classes
    # create pinclasses lists
    for pc, pv in pinclasses.items():
        cls = get_pin_class(pc)
        if not cls:
            fatal("Bad pin name in pinclasses section:",pc)
        
        # build class tables
        if cls not in cls_table:
            cls_table[cls]={}
        
        if pc in cls_table[cls]:
            fatal("Duplicate pin!",pc)
        
        if isinstance(pv,str):
            thepin = pv
            thepindata = [pv, 0, 0, 0]
        elif isinstance(pv,list):
            pv.extend( (4-len(pv))*[0])  
            thepindata = pv
            thepin = pv[0]
        else:
            fatal("Bad format: expected list or string at",pc)

        # add pinflags
        if cls in _flags:
            pinmap.get(thepin)[2].add(_flags[cls])
        # add pindata to classes
        cls_table[cls][pc]=thepindata

    for prph, prph_info in peripherals.items():
        prp, num = get_prph(prph)
        if num<0:
            fatal("unknown perpheral",prph)
        if prp not in prph_table:
            prph_table[prp]={}
            vbl_table[prp]=set()
        prph_table[prp][num]=prph_info["hw"]-1 #minus one to start from 0: old legacy from viper
        prphs.add(prph)
        if prp=="SERIAL":
            vbl_table[prp].add((num,prph_info["rx"],prph_info["tx"]))
        elif prp=="SPI":
            vbl_table[prp].add((num,prph_info["mosi"],prph_info["miso"],prph_info["sclk"]))
        elif prp=="I2C":
            vbl_table[prp].add((num,prph_info["sda"],prph_info["scl"]))
        else:
            vbl_table[prp].add(num)

    # add implicit peripherals

    if "A0" in pinclasses:
        prph_table["ADC"]=1
        prphs.add("ADC0")
    if "PWM0" in pinclasses:
        prph_table["PWMD"]=1
        prphs.add("PWMD0")
    if "ICU0" in pinclasses:
        prph_table["ICUD"]=1
        prphs.add("ICUD0")
    if "DAC0" in pinclasses:
        prph_table["DAC"]=1
        prphs.add("DAC0")


    # generate port.yml ~ port.def
   
    prphs = list(prphs)
    prphs.sort()

    port["defines"]={
        "LAYOUT":  tmpl.get("layout",short_name),
        "BOARD":short_name,
        "CDEFS": tmpl.get("cmacros",[])
    }
    names = set()
    for pin in pinmap:
        names.add(pin)
    for pin in pinclasses:
        names.add(pin)
    for prph in prphs:
        names.add(prph)
    port["peripherals"]=[x for x in prphs]
    port["names"]=list(names)
    pinout = {}
    for pin in pinmap:
        pinout[pin]={}
        for pc, pv in pinclasses.items():
            if isinstance(pv,list):
                pv=pv[0]
            if pv==pin:
                mth = _psplitter.match(pc)
                pinout[pin][mth.group(1)]=pc
                if mth.group(1)=="A":
                    pinout[pc]={"ADC":pc}

    port["pinout"]=pinout
                

    # generate port.bin

    header = bytearray()
    body = bytearray()

    # c prefix is for PinClass* structures
    # m prefix is for vhal_prph_map structures
    # v prefix is for vbl structures

    # set offsets to 0
    c_offsets = [0]*16
    # set table sizes to 0
    c_sizes = [0]*16
    # set offsets to 0
    m_offsets = [0]*16
    # set table sizes to 0
    m_sizes = [0]*16
    # set offsets to 0
    v_offsets = [0]*16
    # set table sizes to 0
    v_sizes = [0]*16

    # generate binary pinmap
    bmap = bytearray()
    for pin in pin_names:
        if pin not in pinmap:
            break
        pindata = pinmap[pin]
        pp = _ports[pindata[0]]
        pn = pindata[1]
        pf = sum(pindata[2])
        bmap.extend(struct.pack("<B",pp)+struct.pack("<B",pn)+struct.pack("<H",pf))

    
    # generate peripheras maps and classes
    mmap = {}
    cmap = {}
    for cid in sorted(_classes_id):
        cname = _classes_id[cid]
        # if the peripheral has a map, generate it
        if cname in prph_table:
            cdata = prph_table[cname]
            if isinstance(cdata,int):
                cdata = {0:1}
            bbmap = bytearray()
            for k in sorted(cdata):
                bbmap.extend(struct.pack("<B",cdata[k]))
            mmap[cid] = bbmap
            m_sizes[cid] = len(cdata)

        # ugly, but necessary: convert long prph to short prph
        if cname in ["PWMD","ICUD","SERIAL"]:
            cname = cname[0:3]
        if cname not in cls_table:
            #skip peripherals without pins: HTM,RTC,...
            continue
        # set classes
        tbl = cls_table[cname]
        cmap[cid]=bytearray()
        for pn in _get_sorted_classes(tbl, cname):
            pdata = tbl[pn]
            pdata[0]=int(pdata[0][1:]) #strip the D
            cmap[cid].extend(struct.pack("<4B",*pdata))
        c_sizes[cid] = len(tbl) 

    # generate vbl maps; TODO: make it general when more vbl maps will be needed
    vmap={}
    for mn,mt in [(0x07,"SERIAL"),(0x03,"I2C"),(0x02,"SPI")]:
        lst = sorted(vbl_table[mt])
        v_sizes[mn]=len(lst)
        vmap[mn]=bytearray()
        for pdata in lst:
            for pd in pdata:
                if isinstance(pd,int):
                    #skip index
                    continue
                vmap[mn].extend(struct.pack("<H",_get_pin_code(pd)))
            if mt=="SPI":
                #add 0 padding for SPI: TODO remove when not more needed
                vmap[mn].extend(b'\x00\x00')
    
    #build the full cvm structure 

    #begin with pinmap
    c_offsets[0]=0
    c_sizes[0]=len(pinmap)  # NUM_PINS
    body.extend(bmap)
    _pad_to(body)

    # now fill with classes
    for cid in sorted(_classes_id):
        cname = _classes_id[cid]
        if cname not in prph_table:
            # not defined, set to 0
            continue
        if cid not in cmap:
            continue
        c_offsets[cid]=len(body)
        body.extend(cmap[cid])
        _pad_to(body)

    # now fill prph maps
    for cid in sorted(_classes_id):
        cname = _classes_id[cid]
        if cname not in prph_table:
            # not defined, set to 0
            continue
        m_offsets[cid]=len(body)
        body.extend(mmap[cid])
        _pad_to(body)

    # now fill vbl maps
    for mn in [0x07,0x03,0x02]:
        v_offsets[mn] = len(body)
        body.extend(vmap[mn])
        _pad_to(body)


    # set header parameters
    header.extend(struct.pack("<H",len(body))) #size
    header.extend(struct.pack("<H",1)) #version
    # set offsets
    header.extend(struct.pack("<16H",*c_offsets))
    header.extend(struct.pack("<16H",*m_offsets))
    header.extend(struct.pack("<16H",*v_offsets))
    # set sizes
    header.extend(struct.pack("<16B",*c_sizes))
    header.extend(struct.pack("<16B",*m_sizes))
    header.extend(struct.pack("<16B",*v_sizes))
    #set target name
    header.extend(struct.pack("32s",short_name.encode("ascii")))
    #set target size
    header.extend(struct.pack("<H",len(short_name)))
    #add padding
    header.extend(struct.pack("<10B",*([0]*10)))



    bin = header+body

    debug("Header size:         ",len(header),hex(len(header)))
    debug("Header.size:         ",hex(struct.unpack("<H",header[0:2])[0]))
    debug("Header.version:      ",hex(struct.unpack("<H",header[2:4])[0]))
    debug("Header.c_offsets:    ",[ hex(x) for x in struct.unpack("<16H",header[4:4+32])])
    debug("Header.c_sizes:      ",[ hex(x) for x in struct.unpack("<16B",header[4+96:4+112])])
    debug("Header.m_offsets:    ",[ hex(x) for x in struct.unpack("<16H",header[4+32:4+64])])
    debug("Header.m_sizes:      ",[ hex(x) for x in struct.unpack("<16B",header[4+112:4+128])])
    debug("Header.v_offsets:    ",[ hex(x) for x in struct.unpack("<16H",header[4+64:4+96])])
    debug("Header.v_sizes:      ",[ hex(x) for x in struct.unpack("<16B",header[4+128:4+144])])
    debug("Header.target:       ",struct.unpack("32s",header[4+144:4+176])[0])
    debug("Header.target_size:  ",struct.unpack("<H",header[4+176:4+178])[0])

    # ymlfile = fs.path(outdir,"port.yml")
    # binfile = fs.path(outdir,"port.bin")

    fs.set_yaml(port,ymlfile)
    fs.write_file(bin,binfile)
    






