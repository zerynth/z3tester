"""
.. _ztc-cmd-probe:

******
Probes
******

The ZTC has support for JTAG/SWD probes. All steps of the Zerynth workflow (registration, virtualization, uplinking) can be made faster by using probes.

Probes are managed through `OpenOCD <http://openocd.org/>`_ , in particular the `GNU MCU Eclipse distribution <https://gnu-mcu-eclipse.github.io/openocd>`_ .
OpenOCD is automatically installed by Zerynth but in some systems it may require some additional manual steps. In particular, in Linux systems, UDEV rules must be
updated in order to allow access to the probe by non-root users: additional information can be found `here <https://gnu-mcu-eclipse.github.io/openocd/install/>`_ .

Probes are handled automatically in ZTC by all commands that can use probes. The following commands are available for advanced usage.

    """

from base import *
from .jtag import Probe
import click
import threading
import time
import requests
import sys
import base64

# Load here because other modules can call this module functions without accessing probe group comands
_interfaces = fs.get_yaml(fs.path(fs.dirname(__file__),"probes.yaml"),failsafe=True)

@cli.group(help="Manage probes.")
def probe():
    pass

@probe.command("list",help="List available probes")
def probe_list():
    """
.. _ztc-cmd-probe-list:

Available Probes
----------------

The command: ::

    ztc probe list

prints the list of supported probes. In particular, the short name of the probe is used to identify the probe in all commands that may need one.

    """
    if env.human:
        table = []
        for intf,iinfo in _interfaces.items():
            table.append([intf,iinfo.get("name","---"),iinfo.get("script","---")])
        log_table(table,headers=["probe","name","script"])
    else:
        log_json(_interfaces)


@probe.command(help="Start probe")
@click.argument("target")
@click.argument("probe")
def start(target,probe):
    start_probe(target,probe)


def start_temporary_probe(target,probe):
    info("Starting temporary probe...")
    thread = threading.Thread(target=start_probe, args = (target,probe))
    thread.start()
    pb = Probe()
    for attempt in range(5):
        try:
            info("Checking probe health...")
            pb.connect(0.5)
            pb.send("exit")
            info("Ok")
            return thread
        except Exception as e:
            time.sleep(1)
            continue
    else:
        warning("Temporary probe may be dead...")

    return thread

def stop_temporary_probe(tp):
    if not tp:
        return
    probe = Probe()
    probe.connect()
    probe.send("shutdown")
    info("Waiting temporary probe...")
    tp.join()
    info("Stopped temporary probe...")



def start_probe(target,probe):
    dev = tools.get_target(target)
    if not dev:
        fatal("Can't find target",target)
    jtagdir = tools.get_tool_dir(dev.jtag_tool or "openocd")
    if not jtagdir:
        fatal("Can't find OpenOCD!")
    interface_script = interface_to_script(probe)
    if not interface_to_script:
        fatal("Can't find interface!")
    target_script = dev.jtag_target
    if not target_script:
        fatal("Target does not support jtag!")

    jtag_interface = fs.path(jtagdir,"scripts","interface",interface_script)
    if "/" not in target_script:
        jtag_target = fs.path(jtagdir,"scripts","target",target_script)
    else:
        tts = target_script.split("/")
        jtag_target = fs.path(jtagdir,"scripts",*tts)

    info("Starting OpenOCD...")
    debug(jtag_interface,jtag_target)

    jtag_target_options = dev.jtag_target_options or ""
    if dev.custom_openocd:
        e,_,_ = proc.runcmd(dev.jtag_tool or "openocd","-s", fs.path(env.devices, dev.target),"-f", fs.path(env.devices, dev.target,"custom_openocd.cfg"), outfn=log)
    else:
        e,_,_ = proc.runcmd(dev.jtag_tool or "openocd","-s",fs.path(jtagdir,"scripts"),"-f",jtag_interface,"-c",jtag_target_options,"-f",jtag_target,outfn=log)



@probe.command(help="Query a running probe")
@click.argument("commands",nargs=-1)
def send(commands):
    if not commands:
        return
    probe = Probe()
    probe.connect()
    for command in commands:
        probe.send(command)
        for line in probe.read_lines():
            if line!=command:
                #do not print echo
                log(line)
    probe.disconnect()

def _inspect(dev,probe):
    tp = None
    try:
        # start temporary probe
        tp = start_temporary_probe(dev.target,probe)
        chipid = dev.get_chipid()
        vmuid = dev.get_vmuid()
        return chipid,vmuid
    except Exception as e:
        fatal("Error",str(e))
    finally:
        # stop temporary probe
        try:
            stop_temporary_probe(tp)
        except Exception as e:
            warning("Can't shutdown probe:",str(e))


@probe.command(help="Inspect a device by probe")
@click.argument("target")
@click.argument("probe")
def inspect(target,probe):
    """
.. _ztc-cmd-probe-inspect:

Inspect device
--------------

The command: ::

    ztc probe target probe

queries the device identified by :samp:`target` by means of the probe :samp:`probe` in order to extract the device chip identifier
and the virtual machine identifier.

    """
    dev = tools.get_target(target)
    if not dev:
        fatal("Can't find target",target)
    if not dev.get_chipid:
        fatal("Target does not support probes!")

    chipid,vmuid = _inspect(dev,probe)

    if not chipid:
        fatal("Can' retrieve chip id!")
    if not vmuid:
        fatal("Can' retrieve vm uid!")

    if env.human:
        info("chip id:",chipid)
        info(" vm uid:",vmuid)
    else:
        log_json({"chipid":chipid,"vmuid":vmuid})



def interface_to_script(interface):
    return _interfaces.get(interface,{}).get("script")



############### GDBGUI

@cli.group("debugger",help="Debugging sessions")
def debugger():
    pass


@debugger.command()
@click.argument("target")
@click.argument("probe")
@click.option("--bytecode",default="",help="Bytecode file with debug info")
def start(target,probe,bytecode):
    dev = tools.get_target(target)
    if not dev:
        fatal("Can't find device!")

    info("Inspecting device...")
    chipid, vmuid = _inspect(dev,probe)
    if not chipid or not vmuid:
        fatal("Can't inspect device!")

    info("Loading VM debug info...")
    # search and open VM for dbg info
    vmpath = tools.get_vm_by_uid(vmuid)
    vm = fs.get_json(vmpath)
    if not "dbg" in vm["map"]:
        fatal("VM",vmuid,"has no debug info!")
    dbgbin=bytearray(base64.standard_b64decode(vm["map"]["dbg"]))
    tmpdir = fs.get_tempdir()
    dbgpath = fs.path(tmpdir,"zerynth.dbg")
    fs.write_file(dbgbin,dbgpath)

    # prepare gdb exec file
    gdbfile = fs.path(tmpdir,"gdbfile")
    gdbcommands = "target remote localhost:3333\nmonitor reset halt\nsymbol-file "+dbgpath+"\n"
    # if needed add command for dynamic uplinked code
    if bytecode:
        # read dyn debug info
        bf = fs.get_json(bytecode)
        if bf["info"].get("ofiles"):
            for ofile in bf["info"]["ofiles"]:
                if not fs.exists(ofile):
                    warning(ofile,"does not exist!")
                    continue
                gdbcommands=gdbcommands+"file "+ofile+"\n"

        if "dbg" not in bf:
            warning("Bytecode has no debug info!")
        else:
            dbgbin=bytearray(base64.standard_b64decode(bf["dbg"]["info"]))
            dbgpath = fs.path(tmpdir,"bytecode.dbg")
            fs.write_file(dbgbin,dbgpath)
            gdbcommands=gdbcommands+"add-symbol-file "+dbgpath+" "+bf["dbg"]["address"]+"\n"

    if env.platform.startswith("win"):
        gdbcommands = gdbcommands.replace('\\','\\\\') #for windows -_-

    fs.write_file(gdbcommands,gdbfile)
    print(gdbfile)

    info("Starting GDB...")
    # find appropriate gdb for target
    gdb=tools[dev.cc]["gdb"]
    #"/home/giacomo/Downloads/gcc-arm-none-eabi-7-2017-q4-major/bin/arm-none-eabi-gdb"
    # alter sys.path for gdbgui dependencies
    sys.path = [fs.path(fs.dirname(__file__),"gdbgui")]+sys.path


    # start temporary probe
    try:
        tp = start_temporary_probe(dev.target,probe)
    except:
        fatal("Can't start probe!")
    # import gdbgui
    from .gdbgui import backend
    sys.argv = ["","-g",gdb,"--hide_gdbgui_upgrades","-n","-x",gdbfile]
    info("**Starting GDB GUI**")
    backend.main()
    try:
        stop_temporary_probe(tp)
    except:
        warning("Can't shutdown probe")
    fs.del_tempdir(tmpdir)

@debugger.command()
def stop():
    try:
        #retrieve main page
        rr = requests.get("http://127.0.0.1:5000/")
    except:
        warning("Can't connect to gdbgui!")
        return
    #search for csrf_token
    matcher = re.compile(".*\"csrf_token\":\s*\"([0-9a-z]+)\".*")
    lines = rr.text.split("\n")
    for line in lines:
        mm = matcher.match(line)
        if mm:
            csrf_token = mm.group(1)
            break
    else:
        fatal("Something wrong while retrieving gdbgui info")

    #save cookie
    jar = rr.cookies
    #request shutdown with GET: this saves the csrf token in the session: https://github.com/cs01/gdbgui/blob/master/gdbgui/backend.py#L489
    rr = requests.get("http://127.0.0.1:5000/shutdown",params={"csrf_token":csrf_token},cookies=jar)
    #now POST a shutdown
    rr = requests.post("http://127.0.0.1:5000/_shutdown",params={"csrf_token":csrf_token},headers={"x-csrftoken":csrf_token},cookies=jar)
    info("Done")

