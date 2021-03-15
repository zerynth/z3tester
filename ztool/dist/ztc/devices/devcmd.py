"""
.. _ztc-cmd-device:

*******
Devices
*******

In the ZTC a device is a peripheral that can execute Zerynth bytecode. In order to do so a device must be prepared and customized with certain attributes.
The main attributes of a device are:

* :samp:`alias`, a unique name given by the user to the device in order to identify it in ZTC commands
* :samp:`uid`, a unique id provided by the operative system identifying the device at hardware level
* :samp:`target`, specifies what kind of virtual machine can be run by the device
* :samp:`name`, a human readable name describing the device. Automatically set by the ZTC
* :samp:`chipid`, the unique identifier of the microcontroller present on the device
* :samp:`remote_id`, the unique identifier of the device in the pool of user registered device
* :samp:`classname`, a Python class name identifying the class containing commands to configure the device

When a new device is connected, some steps must be taken in order to make it able to run Zerynth code:

1. The device must be :ref:`discovered <ztc-cmd-device-discover>`, namely its hardware parameters must be collected (:samp:`uid`).
2. Once discovered an :samp:`alias` must be :ref:`assigned <ztc-cmd-device-alias_put>`. Depending on the type of device :samp:`target` and :samp:`classname` can be assigned in the same step.
3. The device must be :ref:`registered <ztc-cmd-device-register>` in order to create virtual machines for it (:samp:`chipid` and :samp:`remote_id` are obtained in this step)
4. The device must be :ref:`virtualized <ztc-cmd-device-virtualize>, namely a suited virtual machine must be loaded on the device microcontroller


Sometimes the device automatic recognition is not enough to gather all the device parameters or to allow the usage of JTAG/SWD probes. In such cases additional commands have been introduced in order to manually specify the additional parameters. A separate database of devices with advanced configurations is maintained.  

List of device commands:

* :ref:`discover <ztc-cmd-device-discover>`
* :ref:`alias put <ztc-cmd-device-alias_put>`
* :ref:`register <ztc-cmd-device-register>`
* :ref:`register by uid <ztc-cmd-device-register-by-uid>`
* :ref:`register raw <ztc-cmd-device-register-raw>`
* :ref:`virtualize <ztc-cmd-device-virtualize>`
* :ref:`virtualize raw <ztc-cmd-device-virtualize-raw>`
* :ref:`supported <ztc-cmd-device-supported>`
* :ref:`open <ztc-cmd-device-open>`
* :ref:`open raw <ztc-cmd-device-open-raw>`
* :ref:`db list <ztc-cmd-device-db-list>`
* :ref:`db put <ztc-cmd-device-db-put>`
* :ref:`db remove <ztc-cmd-device-db-remove>`


The list of supported devices is available :ref:`here <doc-supported-boards>`

    """
from base import *
from .discover import *
from jtag import *
import click
import re
import base64




_dsc = None

@cli.group(help="Manage devices.")
def device():
    global _dsc
    _dsc = Discover()

##### DEVICE ALIAS [PUT|DEL]

@device.group(help="Manage device configuration.")
def alias():
    pass


@device.command(help="Discover connected devices.")
@click.option("--loop","loop",flag_value=True, default=False,help="Set continuous discover mode.")
@click.option("--looptime",default=2000,help="Set polling delay for discover")
@click.option("--matchdb","matchdb",flag_value=True, default=False,help="Match raw device data with device db.")
def discover(loop,looptime,matchdb):
    """ 
.. _ztc-cmd-device-discover:

Discover
--------

Device discovery is performed by interrogating the operative system database for USB connected peripherals. Each peripheral returned by the system has at least the following "raw" attributes:

* :samp:`vid`, the USB vendor id
* :samp:`pid`, the USB product id
* :samp:`sid`, the unique identifier assigned by the operative system, used to discriminate between multiple connected devices with the same :samp:`vid:pid`
* :samp:`port`, the virtual serial port used to communicate with the device, if present
* :samp:`disk`, the mount point of the device, if present
* :samp:`uid`, a unique identifier assigned by the ZTC
* :samp:`desc`, the device description provided by the operative system (can differ between different platforms)

Raw peripheral data can be obtained by running: ::

    ztc device discover

.. note:: In Linux peripheral data is obtained by calling into libudev functions. In Windows the WMI interface is used. In Mac calls to ioreg are used.

Raw peripheral data are not so useful apart from checking the effective presence of a device. To obtain more useful data the option :option:`-- matchdb` must be provided. Such option adds another step of device discovery on top of raw peripheral data that is matched against the list of supported devices and the list of already known devices.

A :option:`--matchdb` discovery returns a different set of more high level information:

* :samp:`name`, the name of the device taken from the ZTC supported device list
* :samp:`alias`, the device alias (if set)
* :samp:`target`, the device target, specifying what kind of microcontroller and pcb routing is to be expected on the device
* :samp:`uid`, the device uid, same as raw peripheral data
* :samp:`chipid`, the unique identifier of the device microcontrolloer (if known)
* :samp:`remote_id`, the unique identifier of the device in the Zerynth backend (if set)
* :samp:`classname`, the Python class in charge of managing the device

All the above information is needed to make a device usable in the ZTC. The information provided helps in distinguishing different devices with different behaviours. A device without an :samp:`alias` is a device that is not yet usable, therefore an alias must be :ref:`set <ztc-cmd-device-alias_put>`. A device without :samp:`chipid` and :samp:`remote_id` is a device that has not been :ref:`registered <ztc-cmd-device-register> yet and can not be virtualized yet.

To complicate the matter, there are additional cases that can be spotted during discovery:

1. A physical device can match multiple entries in the ZTC supported device list. This happens because often many different devices are built with the same serial USB chip and therefore they all appear as the same hardware to the operative system. Such device are called "ambiguous" because the ZTC can not discriminate their :samp:`target`. For example, both the Mikroelektronika Flip&Click development board and the Arduino Due, share the same microcontroller and the same USB to serial converter and they both appear as a raw peripheral with the same :samp:`vid:pid`. The only way for the ZTC to differentiate between them is to ask the user to set the device :samp:`target`. For ambiguous devices the :samp:`target` can be set while setting the :samp:`alias`. Once the :samp:`target` is set, the device is disambiguated and subsequent discovery will return only one device with the right :samp:`target`.
2. A physical device can appear in two or more different configurations depending on its status. For example, the Particle Photon board has two different modes: the DFU modes in which the device can be flashed (and therefore virtualized) and a "normal" mode in which the device executes the firmware (and hence the Zerynth bytecode). The device appears as a different raw peripherals in the two modes with different :samp:`vid:pid`. In such cases the two different devices will have the same :samp:`target` and, once registered, the same :samp:`chipid` and :samp:`remote_id`. They will appear to the Zerynth backend as a single device (same :samp:`remote_id`), but the ZTC device list will have two different devices with different :samp:`alias` and different :samp:`classname`. The :samp:`classname` for such devices can be set while setting the alias. In the case of the Particle Photon, the :samp:`classname` will be "PhotonDFU" for DFU mode and "Photon" for normal mode. PhotonDFU is the :samp:`alter_ego` of Photon in ZTC terminology.
3. Some development boards do not have USB circuitry and can be programmed only through a JTAG or an external usb-to-serial converter. Such devices can not be discovered. To use them, the programmer device (JTAG or usb-to-serial) must be configured by setting :samp:`alias` and :samp:`target` to the ones the development device.

Finally, the :command:`discover` command can be run in continuous mode by specifying the option :option:`--loop`. With :option:`--loop` the command keeps printing the set of discovered devices each time it changes (i.e. a new device is plugged or a connected device is unplugged). In some operative system the continuous discovery is implemented by polling the operative system device database for changes. The polling time can be set with option :option:`--looptime milliseconds`, by default it is 2000 milliseconds.

    """
    try:
        _dsc.run(loop,looptime,matchdb)
    except Exception as e:
        warning("Exception while discovering devices:",str(e))


@alias.command("put", help="assign an unique alias to a device. \n\n Arguments: \n\n UID: device uid. \n\n ALIAS: device alias. \n\n TARGET: device target.")
@click.argument("uid")
@click.argument("alias")
@click.argument("target")
@click.option("--name",default=False,help="Set device name.")
@click.option("--chipid",default="")
@click.option("--remote_id",default="")
@click.option("--classname",default="",help="Set device classname.")
def alias_put(uid,alias,name,target,chipid,remote_id,classname):
    """ 
.. _ztc-cmd-device-alias_put:

Device configuration
--------------------

Before usage a device must be configured. The configuration consists in linking a physical device identified by its :samp:`uid` to a logical device identified by its :samp:`alias` and :samp:`target` attributes. Additional attributes can be optionally set.
The configuration command is: ::

    ztc device alias put uid alias target

where :samp:`uid` is the device hardware identifier (as reported by the discovery algorithm), :samp:`alias` is the user defined device name (no spaces allowed) and :samp:`target` is one of the supported the :ref:`supported <ztc-cmd-device-supported>` devices target. A :samp:`target` specifies what kind of microcontroller, pin routing and additional perpherals can be found on the device. For example, the :samp:`target` for NodeMCU2 development board id :samp:`nodemcu2` and informs the ZTC about the fact that the configured device is a NodeMCU2 implying an esp8266 microcontroller, a certain pin routing and an onboard FTDI controller. 

There is no need to write the whole :samp:`uid` in the command, just a few initial character suffice, as the list of known uids is scanned and compared to the given partial :samp:`uid` (may fail if the given partial :samp:`uid` matches more than one uid).

Additional options can be given to set other device attributes:

* :option:`--name name` set the human readable device name to :samp:`name` (enclose in double quotes if the name contains spaces)
* :option:`--chipid chipid` used by external tools to set the device :samp:`chipid` manually
* :option:`--remote_id remote_id` used by external tools to set device :samp:`remote_id` manually
* :option:`--classname classname` used to set the device :samp:`classname` in case of ambiguity.

Aliases can be also removed from the known device list with the command: ::

    ztc device alias del alias



    """
    #if not re.match("^[A-Za-z0-9_:-]{4,}$",alias):
    #    fatal("Malformed alias")
    devs = _dsc.run_one(True)
    #print(devs)
    uids=_dsc.matching_uids(devs, uid)
    #print(uids)
    if len(uids)<=0:
        fatal("No devices with uid",uid)
    else:
        uid = uids[0]
        dd = [dev for uu,dev in devs.items() if dev.uid==uid]
        dd = dd[0]
        if not classname and len(dd["classes"])>1:
            fatal("Multiclass device! Must specify --classname option")
        if not classname:
            classname = dd["classes"][0].split(".")[1]
        aliaskey = alias
        aliases = env.get_dev(uid)
        aliasuid = aliases[alias].uid if alias in aliases else None
        if not _target_exists(target):
            fatal("No such target",target)
        ###TODO to define chipid and remote_id if needed ... related option are not documented
        deventry = {
            "alias":alias,
            "uid":uid,
            "name": aliases[alias].name if not name and aliasuid!=None else "",
            "target": target,
            "chipid":chipid,
            "remote_id":remote_id,
            "classname":classname
        }
        env.put_dev(deventry) 
        

@alias.command("del", help="Delete a device from the known device list. \n\n Arguments: \n\n ALIAS: The alias of the device to remove.")
@click.argument("alias")
def alias_del(alias):
    env.del_dev(Var({"alias":alias}))



#TODO: remove
def _target_exists(target):
    if not target: return False
    for k,v in _dsc.device_cls.items():
        if "target" in v and v["target"]==target:
            return True
    return False


def _extract_chipid_from_serial(tgt):
    conn = ConnectionInfo()
    conn.set_serial(tgt.port,**tgt.connection)
    ch = Channel(conn)
    try:
        ch.open(timeout=2)
    except:
        return False, "Can't open serial port!"
    lines = []
    for x in range(30):
        line=ch.readline()
        lines.append(line.strip("\n"))
    ch.close()
    cnt = [lines.count(x) for x in lines]
    pos = cnt.index(max(cnt))
    
    if pos>=0 and cnt[pos]>3 and len(lines[pos])>=8:
        return True,lines[pos]
    else:
        return False, "Can't find chipid"


@device.command(help="Register a new device. \n\n Arguments: \n\n ALIAS: device alias")
@click.argument("alias")
@click.option("--skip_burn",flag_value=True, default=False,help="bootloader is not flashed on the device (must be flashed manually!)")
def register(alias,skip_burn):
    """ 
.. _ztc-cmd-device-register:

Device Registration
-------------------

To obtain a virtual machine a device must be registered first. The registration process consists in flashing a registration firmware on the device, obtaining the microcontroller unique identifier and communicating it to the Zerynth backend.
The process is almost completely automated, it may simply require the user to put the device is a mode compatible with burning firmware.

Device registration is performed by issuing the command: ::

    ztc device register alias

where :samp:`alias` is the device alias previously set (or just the initial part of it).

The result of a correct registration is a device with the registration firmware on it, the device :samp:`chipid` and the device :samp:`remote_id`. Such attributes are automatically added to the device entry in the known device list.

The option :option:`--skip_burn` avoid flashing the device with the registering firmware (it must be made manually!); it can be helpful in contexts where the device is not recognized correctly.

.. note:: Devices with multiple modes can be registered one at a time only!

    """
    tgt = _dsc.search_for_device(alias)
    if not tgt:
        fatal("Can't find device",alias)
    elif isinstance(tgt,list):
        fatal("Ambiguous alias",[x.alias for x in tgt])
    if not tgt.virtualizable:
        fatal("Device is not virtualizable! Try to put it in a virtualizable mode...")
    
    if tgt.virtualizable != tgt.classname:
        fatal("Device must be put in virtualizable mode!")
    
    alter_ego = None

    if tgt.preferred_register_with_jtag:
        # with jtags
        chipid,err = tgt.do_get_chipid(tgt.preferred_register_with_jtag["probe"],False)
        if err:
            fatal(err)
    else:
        # open register.vm
        reg = fs.get_json(fs.path(tgt.path,"register.vm"))

        info("Starting device registration")
        # burn register.vm
        if not skip_burn:
            info("Burning bootloader...")
            res,out = tgt.do_burn_vm(reg,outfn=info)
            if not res:
                fatal("Can't burn bootloader! -->",out)
        else:
            info("Skipping bootloader burning...")

        if tgt.has_alter_ego:
            alter_ego = tgt
            clsname = tgt.has_alter_ego
            uids,devs = _dsc.wait_for_classname(clsname)
            if not uids:
                fatal("Can't find this device alter ego!")
            elif len(uids)>1:
                fatal("Too many devices matching this device alter ego! Please unplug them all and retry...")
            tgt = devs[uids[0]]
        else:
            # virtualizable device is the same as uplinkable device :)
            # search for dev again and open serial
            tgt = _dsc.find_again(tgt)
            if not tgt:
                fatal("Can't find device",alias)

        if tgt.reset_after_register:
            info("Please reset the device!")

        if tgt.sw_reset_after_register is True:
            tgt.reset()

        res,chipid = _extract_chipid_from_serial(tgt)
        if not res:
            fatal(chipid)
    # common execution path
    info("Chip id retrieved:",chipid)
    dinfo = {
        "name": tgt.custom_name or tgt.name,
        "on_chip_id": chipid,
        "type": tgt.original_target or tgt.target,  #custom devices are registered as the original_target!
        "category": tgt.family_name
    }
    remote_uid = _register_device(dinfo)
    tgt2 = tgt
    tgt = tgt.to_dict()
    tgt["chipid"]=chipid
    tgt["remote_id"]=remote_uid
    if alter_ego:
        alter_ego = alter_ego.to_dict()
        alter_ego["chipid"]=chipid
        alter_ego["remote_id"]=remote_uid
    do_put_dev(tgt,alter_ego)

def do_put_dev(tgt,alter_ego=None):
    env.put_dev(tgt,linked=tgt["sid"]=="no_sid")
    if alter_ego:
        env.put_dev(alter_ego)


def _register_device(dinfo):
    # call api to register device
    # dinfo = {
    #     "name": tgt.custom_name or tgt.name,
    #     "on_chip_id": chipid,
    #     "type": tgt.target,
    #     "category": tgt.family_name
    # }
    try:
        res = zpost(url=env.api.devices, data=dinfo)
        rj = res.json()
        if rj["status"] == "success":
            info("Device",dinfo.get("name",""),"registered with uid:", rj["data"]["uid"])
            return rj["data"]["uid"]
        else:
            fatal("Remote device registration failed with:", rj["message"])
    except Exception as e:
        critical("Error during remote registration",exc=e)


@device.command(help="Register a new device without extracting the uid")
@click.argument("chipid")
@click.argument("target")
def register_by_uid(chipid,target):
    """ 
.. _ztc-cmd-device-register-by-uid:

Device Registration by UID
--------------------------

If the microcontroller unique identifier is already known (i.e. obtained with a JTAG probe), the device can be registered skipping the registration firmware flashing phase.

Device registration is performed by issuing the command: ::

    ztc device register_by_uid chipid target

where :samp:`chipid` is the microcontroller unique identifier  and :samp:`target` is the type of the device being registered. A list of available targets can be obtained  with the ref:`supported <ztc-cmd-device-supported>`.

Upon successful registration the device is assigned an UID by the backend.

    """
    dinfo = {
        "on_chip_id": chipid,
        "type": target
    }
    _register_device(dinfo)

@device.command(help="Register a new device giving target details")
@click.argument("target")
@click.option("--skip-remote","__skip_remote",default=False,flag_value=True)
@click.option("--skip-probe","__skip_probe",default=False,flag_value=True)
@click.option("--spec","__specs",default=[],multiple=True)
def register_raw(target,__skip_remote,__specs,__skip_probe):
    """ 
.. _ztc-cmd-device-register-raw:

Device Raw Registration
-----------------------

Sometimes it is useful to manually provide the device parameters for registration. The parameters that can be provided are:

* :samp:`port`, the serial port exposed by the device
* :samp:`disk`, the mass storage path provided by the device
* :samp:`probe`, the type of JTAG/SWD probe to use during registering

The above parameters must be specified using the :option:`--spec` option followed by the pair parameter name and value separated by a colon (see the example below).

Device registration is performed by issuing the command: ::

    ztc device register_raw target --spec port:the_port --spec disk:the_disk --spec probe:the_probe

It is necessary to provide at least one device parameter and the registration will be attempted gibing priority to the probe parameter. Registration by probe is very fast (and recommended for production scenarios) beacuse the registration firmware is not required.

    """
    __register_raw(target,__skip_remote,__specs,__skip_probe)

def do_search_attached_device(target=None):
    global _dsc
    if not _dsc:
        _dsc = Discover()
    return _dsc.search_for_attached_device(target)

def do_register_raw(target,__skip_remote,__specs,__skip_probe):
    return __register_raw(target,__skip_remote,__specs,__skip_probe)

def __register_raw(target,__skip_remote,__specs,__skip_probe):
    global _dsc
    options = tools.get_specs(__specs)
    if not _dsc:
        _dsc = Discover()
    dev =  _dsc.get_target(target,options)    
    if not dev:
        fatal("No such target!")
   
    probe = options.get("probe")
    port = options.get("port")
    disk = options.get("disk")
    if probe:
        if not dev.jtag_capable:
            fatal("Registration by probe not supported, check your configuration")
        chipid,err = dev.do_get_chipid(probe,__skip_probe)
        if err:
            fatal(err)
    else:
        # open register.vm
        reg = fs.get_json(fs.path(dev.path,"register.vm"))
        info("Burning bootloader...")
        if not port:
            fatal("Unknown serial port. Please specify device serial port in configuration")
        res, out = dev.do_burn_vm(reg,options,info)
        if not res:
            fatal("Can't burn bootloader! -->",out)
        if dev.reset_after_register:
            info("Please reset the device!")
            sleep((dev.reset_time or 3000)/1000)
        if dev.sw_reset_after_register is True:
            dev.reset()
        res,chipid = _extract_chipid_from_serial(dev)
        if not res:
            fatal(chipid)

    if not chipid:
        fatal("Can't retrieve chip id!")
    info("Chip id retrieved:",chipid)
    if not __skip_remote:
        dinfo = {
            "on_chip_id": chipid,
            "type": dev.original_target or target
        }
        remote_uid = _register_device(dinfo)
        try:
            tgt = do_search_attached_device(dev.target)
            tgt = tgt.to_dict()
            tgt["chipid"]=chipid
            tgt["remote_id"]=remote_uid
            do_put_dev(tgt)
        except Exception as e:
            debug(e)
            pass
        return remote_uid

@device.command(help="Virtualize a device. \n\n Arguments: \n\n ALIAS: device alias. \n\n VMUID: Virtual Machine identifier.")
@click.argument("alias")
@click.argument("vmuid")
def virtualize(alias,vmuid):
    """ 
.. _ztc-cmd-device-virtualize:

Virtualization
--------------

Device virtualization consists in flashing a Zerynth virtual machine on a registered device. One or more virtual machines for a device can be obtained with specific ZTC :ref:`commands <ztc-cmd-vm-create>`.
Virtualization is started by: ::

    ztc device virtualize alias vmuid

where :samp:`alias` is the device alias and :samp:`vmuid` is the unique identifier of the chosen vm. :samp:`vmuid` can be typed partially, ZTC will try to match it against known identifiers. :samp:`vmuid` is obtained during virtual machine :ref:`creation <ztc-cmd-vm-create>`.

The virtualization process is automated, no user interaction is required.

    """
    tgt = _dsc.search_for_device(alias)
    if not tgt:
        fatal("Can't find device",alias)
    elif isinstance(tgt,list):
        fatal("Ambiguous alias",[x.alias for x in tgt])
    if tgt.virtualizable!=tgt.classname:
        fatal("Device not virtualizable")
    vms=tools.get_vms(tgt.target)
    if vmuid not in vms:
        vuids = []
        for vuid in vms:
            if vuid.startswith(vmuid):
                vuids.append(vuid)
        if len(vuids)==1:
            vmuid=vuids[0]
        elif len(vuids)>1:
            fatal("Ambiguous VM uid",vuids)
        else:
            fatal("VM",vmuid,"does not exist")
    vm = fs.get_json(vms[vmuid])
    info("Starting Virtualization...")
    res,out = tgt.do_burn_vm(vm,{},info)
    # if isinstance(vm["bin"],str):
    #     res,out = tgt.burn(bytearray(base64.standard_b64decode(vm["bin"])),info)
    # else:
    #     res,out = tgt.burn([ base64.standard_b64decode(x) for x in vm["bin"]],info)
    if not res:
        fatal("Error in virtualization",out)
    else:
        info("Virtualization Ok")


@device.command(help="Virtualize a device providing manual parameters.")
@click.argument("vmuid")
@click.option("--spec","__specs",default=[],multiple=True)
def virtualize_raw(vmuid,__specs):
    """ 
.. _ztc-cmd-device-virtualize-raw:

Raw Virtualization
------------------

Device virtualization consists in flashing a Zerynth virtual machine on a registered device. One or more virtual machines for a device can be obtained with specific ZTC :ref:`commands <ztc-cmd-vm-create>`.

Sometimes it is useful to manually provide the device parameters for virtualization. The parameters that can be provided are the same of the :ref:`register_raw <ztc-device-register-raw>` command.

Virtualization is started by: ::

    ztc device virtualize vmuid --spec port:the_port --spec disk:the_disk --spec  probe:the_probe

where :samp:`vmuid` is the unique identifier of the chosen vm. :samp:`vmuid` can be typed partially, ZTC will try to match it against known identifiers. :samp:`vmuid` is obtained during virtual machine :ref:`creation <ztc-cmd-vm-create>`.

The virtualization by probe has priority over the other device parameters and is recommended for production scenarios.

    """
    _virtualize_raw(vmuid,__specs)

def do_virtualize_raw(vmuid,__specs):
    _virtualize_raw(vmuid,__specs)

def _virtualize_raw(vmuid,__specs):
    global _dsc
    if not _dsc:
        _dsc = Discover()
    vms = tools.get_vm_by_prefix(vmuid)
    if len(vms)==0:
        fatal("No such VM uid")
    if len(vms)>1:
        fatal("Ambiguous VM uid:",vms[:10])
    vmfile = vms[0]
    vm = fs.get_json(vmfile)
    # manage specs
    options = tools.get_specs(__specs)
    dev =  _dsc.get_target(vm["dev_type"],options)    
    if not dev:
        fatal("No such target!",vm["dev_type"])
    info("Starting Virtualization...")
    res,out = dev.do_burn_vm(vm,options,info)
    if not res:
        fatal("Error in virtualization",out)
    else:
        info("Virtualization Ok")
    


@device.command(help="Open device serial. \n\n Arguments: \n\n ALIAS: device alias.")
@click.argument("alias")
@click.option("--echo","__echo",flag_value=True, default=False,help="print typed characters to stdin")
@click.option("--baud","__baud", default=0,type=int,help="open with a specific baudrate")
def open(alias,__echo,__baud):
    """ 
.. _ztc-cmd-device-open:

Serial Console
--------------

Each virtual machine provides a default serial port where the output of the program is printed. Such port can be opened in full duplex mode allowing bidirectional communication between the device and the terminal.

The command: ::

    ztc device open alias

tries to open the default serial port with the correct parameters for the device. Output from the device is printed to stdout while stdin is redirected to the serial port. Adding the option :option:`--echo` to the command echoes back the characters from stdin to stdout.

    """
    tgt = _dsc.search_for_device(alias)
    if not tgt:
        fatal("Can't find device",alias)
    elif isinstance(tgt,list):
        fatal("Ambiguous alias",[x.alias for x in tgt])

    conn = ConnectionInfo()
    if __baud:
        tgt.connection["baudrate"]=__baud
    conn.set_serial(tgt.port,**tgt.connection)
    ch = Channel(conn,__echo)
    ch.open()
    ch.run()
    # import serial
    # ser = serial.Serial(tgt.port,115200)
    # while True:
    #     data = ser.read()
    #     log(data.decode("ascii","replace"),sep="",end="")
    #     #print(,sep="",end="")

@device.command(help="Open device serial.")
@click.argument("port")
@click.option("--echo","__echo",flag_value=True, default=False,help="print typed characters to stdin")
@click.option("--baud","__baud", default=115200,type=int,help="open with a specific baudrate")
@click.option("--parity","__parity", default="n",type=str,help="open with a specific parity")
@click.option("--bits","__bits", default=8,type=int,help="")
@click.option("--stopbits","__stopbits", default=1,type=int,help="")
@click.option("--dsrdtr","__dsrdtr", default=False,flag_value=True,help="")
@click.option("--rtscts","__rtscts", default=False,flag_value=True,help="")
def open_raw(port,__echo,__baud,__parity,__bits,__stopbits,__dsrdtr,__rtscts):
    """ 
.. _ztc-cmd-device-open-raw:

Serial Console (raw)
--------------------

Each virtual machine provides a default serial port where the output of the program is printed. Such port can be opened in full duplex mode allowing bidirectional communication between the device and the terminal.

it is sometime useful to directly specify the serial port on the command line.

The command: ::

    ztc device open port

tries to open :samp:`port` with the correct parameters for the device. Output from the device is printed to stdout while stdin is redirected to the serial port. Adding the option :option:`--echo` to the command echoes back the characters from stdin to stdout.

    """
    _open_raw(port,__echo,__baud,__parity,__bits,__stopbits,__dsrdtr,__rtscts)

def do_open_raw(port,__echo,__baud,__parity,__bits,__stopbits,__dsrdtr,__rtscts):
    _open_raw(port,__echo,__baud,__parity,__bits,__stopbits,__dsrdtr,__rtscts)


def _open_raw(port,__echo,__baud,__parity,__bits,__stopbits,__dsrdtr,__rtscts):
    conn = ConnectionInfo()
    options={
        "baudrate":__baud,
        "parity":__parity,
        "bytesize":__bits,
        "stopbits":__stopbits,
        "dsrdtr":__dsrdtr,
        "rtscts":__rtscts
    }
    conn.set_serial(port,**options)
    ch = Channel(conn,__echo)
    ch.open()
    ch.run()



@device.command(help="List of supported devices.")
@click.option("--type",default="board",type=click.Choice(["board","jtag","usbtoserial"]),help="type of device [board, jtag,usbtoserial]")
@click.option("--single",default=False,flag_value=True)
@click.option("--nice",default=False,flag_value=True)
def supported(type,single,nice):
    """ 
.. _ztc-cmd-device-supported:

Supported Devices
-----------------

Different versions of the ZTC may have a different set of supported devices. To find the device supported by the current installation type: ::

    ztc device supported

and a table of :samp:`target` names and paths to device support packages will be printed.

    """
    do_get_supported(type,single,nice)

def do_get_supported(type,single,nice):
    table = []
    jst = []
    inserted = set()
    global _dsc
    if not _dsc:
        _dsc = Discover()
    for k,v in _dsc.device_cls.items():
        if v["type"]==type:
            if env.human:
                if not nice:
                    table.append([v["target"],v["path"]])
                else:
                    if v["target"] in inserted:
                        continue
                    inserted.add(v["target"])
                    table.append([v["target"],v["name"],v.get("preferred_uplink_with_jtag",{"probe":"none"})["probe"]])
            else:
                tt ={
                    "target":v["target"],
                    "path":v["path"]
                }
                jst.append(tt)
                if not single:
                    log_json(tt)
    if env.human:
        if not nice:
            log_table(table,headers=["Target","Path"])
        else:
            table = sorted(table,key=lambda x:x[0])
            log_table(table,headers=["Target","Name","Probe"])
    elif single:
        log_json(jst)

@device.command(help="List of serial ports and disk devices")
def ports_and_disks():
    res = {
            "disks":_dsc.devsrc.find_all_mount_points(),
            "ports":_dsc.devsrc.find_all_serial_ports()
    }
    log_json(res)

def do_get_serial_ports():
    global _dsc
    if not _dsc:
        _dsc = Discover()
    table = []
    for p in _dsc.devsrc.find_all_serial_ports():
        table.append([p])
    log_table(table,headers=["Port"])

    

@device.command(help="Erase the flash of the device. \n\n Arguments: \n\n ALIAS: device alias")
@click.argument("alias")
def erase_flash(alias):
    """ 
.. _ztc-cmd-device-erase-flash:

Erase of the device flash memory
--------------------------------

Erase completely the flash memory of the device (all data stored will be deleted).

This operation is performed by issuing the command: ::

    ztc device erase_flash alias

where :samp:`alias` is the device alias previously set (or just the initial part of it).

    """
    tgt = _dsc.search_for_device(alias)
    if not tgt:
        fatal("Can't find device",alias)
    elif isinstance(tgt,list):
        fatal("Ambiguous alias",[x.alias for x in tgt])

    info("Starting erasing flash...")
    res,out = tgt.do_erase_flash(outfn=info)
    if not res:
        fatal("Can't erase flash! -->",out)
    info("Memory flash erased")

@device.command(help="Execute a custom action for the device. \n\n Arguments: \n\n ALIAS: device alias \n\n ACTION: selected action")
@click.argument("alias")
@click.argument("action")
@click.option("--action-param",default="",type=str,multiple=True,help="action parameter")
def custom_action(alias, action, action_param):
    """ 
.. _ztc-cmd-device-custom-action:

Execute a device custom action
------------------------------

Some devices provide custom actions to be executed (e.g., burn proprietary bootloaders, put the device in a specific mode).
These actions are performed by issuing the command: ::

    ztc device custom_action alias action

where :samp:`alias` is the device alias previously set (or just the initial part of it) and :samp:`action` is the selected action.

    """
    tgt = _dsc.search_for_device(alias)
    if not tgt:
        fatal("Can't find device",alias)
    elif isinstance(tgt,list):
        fatal("Ambiguous alias",[x.alias for x in tgt])

    if env.human:
        info("Executing action: %s" % action)
    def outfn(*args,**kwargs):
        echo("###",*args,**kwargs)
    res,out = tgt.do_custom_action(action, outfn=outfn, action_param=action_param)
    if not res:
        fatal("Cannot execute selected action! -->",out)
    if out:
        if env.human:
            for key, val in out.items():
                print(key,':', val)
        else:
            click.echo(json.dumps(out))
    if env.human:
        info("Action successfully executed")

@device.group(help="Manage device configurations manually.")
def db():
    pass

@db.command("list")
@click.option("--filter-target",default="",type=str,help="list only matching target")
def _db_list(filter_target):
    """
.. _ztc-cmd-device-db-list:

Configured Devices
------------------

Manual device configurations can be saved in a local database in order to avoid retyping device parameters every time.
The command: ::

    ztc device db list

prints the list of configured devices with relevant parameters. By providing the oprion :option:`--filter-target` the list for a specific target can be retrieved.

    """
    db = fs.get_yaml(fs.path(env.cfg,"devices.yaml"),failsafe=True)
    
    if not env.human:
        if not filter_target:
            log_json(db)
        else:
            log_json({k:v for k,v in db.items() if v["target"]==filter_target})
        return

    table = []
    for devid, devinfo in db.items():
        if filter_target and devinfo["target"]!=filter_target:
            continue
        table.append([devid,devinfo["target"],devinfo.get("port","---"),devinfo.get("disk","---"),devinfo.get("probe","---"),devinfo.get("chipid","---"),devinfo.get("remote_id","---")])

    log_table(table,headers = ["name","target","port","disk","probe","chip id","remote id"])

@db.command("put")
@click.argument("target")
@click.argument("name")
@click.option("--spec","__specs",default=[],multiple=True)
def _db_put(target,name,__specs):
    """
.. _ztc-cmd-device-db-put:

Add Configured Devices
----------------------

Manual device configurations can be saved in a local database in order to avoid retyping device parameters every time.
The relevant parameter for a device are:

    * :samp:`target`, the device type
    * :samp:`name`, the device name. It must be unique and human readable
    * :samp:`port`, the device serial port (may change upon device reset!)
    * :samp:`disk`, the mass storage path of the device (if exposed)
    * :samp:`probe`, the JTAG/SWD probe used for device programming
    * :samp:`chipid`, the device microcontroller unique identifier
    * :samp:`remote_id`, the device UID assigned by the backend after registation

If the device :samp:`name` is not present in the database, a new device is created; otherwise the existing device is updated with the provided parameters. To unset a parameter pass the "null" value (as a string). If a parameter is not given it is not modified in the database. A parameter is set tonull if not specified upon device creation.

The command: ::

    ztc device db put target device_name --spec port:the_port --spec disk:the_disk --spec probe:the_probe --spec chipid:the_chipid --spec remote_uid:the_remote_uid

inserts or modifies the configured device :samp:`device_name` in the database. The given parameters are updated as well. For the probe parameter, the list of available probes can be obtained with the :ref:`probe list <ztc-cmd-probe-list>` command.

    """
    db = fs.get_yaml(fs.path(env.cfg,"devices.yaml"),failsafe=True)
    options = tools.get_specs(__specs)
    dinfo = db.get(name,{})
    db[name]={
        "target":target,
        "name":name,
        "port":options.get("port",dinfo.get("port")),
        "disk":options.get("disk",dinfo.get("disk")),
        "probe":options.get("probe",dinfo.get("probe")),
        "chipid":options.get("chipid",dinfo.get("chipid")),
        "remote_id":options.get("remote_id",dinfo.get("remote_id")),
        "custom":options.get("custom",dinfo.get("custom"))
    }
    if dinfo:
        info("Updating device...")
    else:
        info("Saving device...")
    fs.set_yaml(db,fs.path(env.cfg,"devices.yaml"))

@db.command("remove")
@click.argument("name")
def _db_remove(name):
    """
.. _ztc-cmd-device-db-remove:

Remove Configured Devices
-------------------------

The command: ::

    ztc device db remove device_name

removes the device :samp:`device_name` from the configured devices.

    """
    db = fs.get_yaml(fs.path(env.cfg,"devices.yaml"),failsafe=True)
    dinfo = db.pop(name,None)
    if dinfo:
        info("Removing device...")
    else:
        info("Nothing to remove")
    fs.set_yaml(db,fs.path(env.cfg,"devices.yaml"))


def get_device(alias,loop,perform_reset=True):
    _dsc = Discover()
    uids = []
    adev = _dsc.search_for_device(alias)
    if not adev:
        fatal("Can't find device",alias)
    elif isinstance(adev,list):
        fatal("Ambiguous alias",[x.alias for x in adev])
    uid = adev.uid

    # search for device
    info("Searching for device",uid,"with alias",alias)
    uids, devs = _dsc.wait_for_uid(uid,loop=loop)
    if not uids:
        fatal("No such device",uid)
    elif len(uids)>1:
        fatal("Ambiguous uid",uids)
    uid = uids[0]
    for k,d in devs.items():
        if d.uid == uid:
            dev = d
            hh = k
            break
    else:
        fatal("Error!",uid)
    # got dev object!

    if perform_reset:

        if dev.preferred_uplink_with_jtag:
            pass
        elif dev.uplink_reset is True:
            info("Please reset the device!")
            sleep(dev.reset_time/1000)
            info("Searching for device",uid,"again")
            # wait for dev to come back, port/address may change -_-
            uids,devs = _dsc.wait_for_uid(uid)
            if len(uids)!=1:
                fatal("Can't find device",uid)
        elif dev.uplink_reset == "reset":
            dev.reset()

    dev = devs[hh]
    return dev


def get_device_by_target(target,options,skip_reset=False):
    info("Searching for device",target)
    dev = tools.get_target(target,options)
    if not dev:
        fatal("No such target!",target)

    if not skip_reset:
        if dev.uplink_reset is True:
            info("Please reset the device!")
            sleep(dev.reset_time/1000)
        elif dev.uplink_reset == "reset":
            dev.reset()
    return dev

def probing(ch,devtarget_obj, adjust_timeouts=True):
    devtarget = devtarget_obj.target
    # PROBING
    starttime = time.perf_counter()
    probesent = False
    hcatcher = re.compile("^(r[0-9]+\.[0-9]+\.[0-9]+) ([0-9A-Za-z_\-]+) ([^ ]+) ([0-9a-fA-F]+) ZERYNTH")
    # reduce timeout
    if adjust_timeouts: # Windows Driver for some USB serials (i.e. arduino_due) send simulated DTR (two zeros) when reconfiguring timeout -_- -_- -_-
        ch.set_timeout(0.5)
    while time.perf_counter()-starttime<5:
        line=ch.readline()
        debug("<=",line)
        if not line and not probesent:
            # Board class in devices redefines __getattr__
            if devtarget_obj.probing_pre_v_hook is not None:
                devtarget_obj.probing_pre_v_hook()
            probesent=True
            ch.write("V")
            debug("=> V")
            info("Probe sent")
        line = line.replace("\n","").strip()
        if line:
            info("Got header:",line)
        if line.endswith("ZERYNTH"):
            mth = hcatcher.match(line)
            if mth:
                version = mth.group(1)
                vmuid = mth.group(2)
                chuid = mth.group(4)
                target = mth.group(3)
                break
    else:
        fatal("No answer to probe")

    # im = ZpmVersion(env.min_vm_dep)                             # minimum vm version compatible with current ztc
    # ik = ZpmVersion(version)                                    # vm version

    # if compare_versions(version,env.var.version) != 0:
    #     fatal("VM version [",version,"] is not compatible with this uplinker! Virtualize again with a newer VM...")

    if target!=devtarget:
        fatal("Wrong VM: probing for",devtarget,"and found",target,"instead")
    else:
        info("Found VM",vmuid,"for",target)

    # restore timeout
    if adjust_timeouts:
        ch.set_timeout(2)
    return version,vmuid,chuid,target

