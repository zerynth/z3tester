"""
=========================================
Device Configuration and Mass Programming
=========================================

In the lifecycle of an IoT device particular attention must be given to the initial programming and provisioning.
Zerynth provides some firmware modules and toolchain commands to ease the task.

In particular the toolchain is capable of accepting a description of the resources needed by the device and automatically
store them in the device flash memory together with the VM and the firmware. To do so, a Zerynth project must be accompained
by a :samp:`dcz.yml` file with all the information on the needed resources and the ways to generate them.

To automate the task of mass programming, it is also possible to write a :samp:`massprog.yml` file containing the information
about the kind of device to mass program, its vm parameters and more. In this way it is not necessary to manually register-virtualize-uplink
all the devices and the whole task is performed by a single command.



Device Configuration Zones
==========================

If a valid :samp:`dcz.yml` file is present in the project folder, every time an uplink command is performed, the file is read
and the described resources are generated and stored in the device flash before any uplinking. The device must support some means of
programming with jtag probes or custom uploaders for this process to work correctly.

The :samp:`dcz.yml` file is composed of various sections: ::

    # Zerynth Device Configuration Map
    #
    # this file declares a set of resources to be loaded on the device
    # in a way that is indipendent from the firmware in order to facilitate
    # mass programming and mass provisioning.
    #
    # It is in Yaml format, and the various sections/options are documented below


    # this field must be true to enable this configuration!
    # if not present or false, the configuration is skipped
    # and no resource is transferred in the device
    active: true


    ############################
    # Provisioning Section
    #
    # in the "provisioning" section, the various resources
    # with their location and their generation method are listed
    #
    # For each resource the following fields are mandatory:
    #
    # - name: an ascii string specifying the resource name (max 16 bytes)
    # - type: the type of the resource [file, prvkey, pubkey, cert]
    # - args: a list of arguments needed to load or generate the resource
    # - mapping: a list of addresses where the resource must be copied
    # 
    # When using DCZ (see next section), an optional parameter "format" can be given.
    # It must be an ascii string of at most 4 bytes, by default it is set to "bin"
    #
    # uncomment the following section to enable provisioning
    provisioning:
        # the provisioning method (used to generate device credentials)
        method: aws_iot_key_cert
        # the list of resources
        resources:
            # the device CA certificate: obtained from the ones provided by Amazon
            - name: cacert
              type: cacert
              mapping: [0x326000,0x327000]
            # the device certificate: will be created by calling into AWS API
            - name: clicert
              type: clicert
              mapping: [0x320000,0x321000]
            # the device private key: will be created by calling into AWS API and will be encrypted
            - name: prvkey
              type: prvkey
              mapping: [0x322000,0x323000]
              encrypt: True
            # the endpoint where to connect to. Obtained by calling into AWS API
            - name: endpoint
              type: endpoint
              mapping: [0x324000,0x325000]
              format: json
            # some device info useful to have in the firmware (for this to work, aws.thing_prefix must be given!)
            - name: devinfo
              type: devinfo
              mapping: [0x328000,0x329000]
              format: json
            # an encrypted resource where wifi credentials can be stored
            - name: wificred
              type: file
              args: files/wificred.json
              mapping: [0x330000, 0x331000]
              format: json
              encrypt: True


    ############################
    # DCZ Section
    #
    # in the "dcz" section the provisioned resources (or a subset of them)
    # can be included in the Device Configuration Zone. The DCZ is a versionable index
    # of the available resources that can be easily accessed and updated 
    # with the dcz Zerynth module.
    #
    # DCZ supports up to 8 replication zones for safety. If a resource is included in a DCZ
    # with replication n, it must be placed in exactly n different locations for versioning
    #
    # uncomment the section below to enable dcz
    dcz:
        # locations of the DCZs (replication 2)
        mapping: [0x310000,0x311000]
        # list of resource names to be included
        resources:
            - endpoint
            - clicert
            - prvkey
            - cacert
            - devinfo
            - wificred

    ############################
    # AWS Section
    #
    # in the "aws" section, the various credentials and options
    # for aws iot services are spcified
    aws:
        # specify the access key id of the IAM user that can create certificate and things
        aws_access_key_id: "your-access-key"
        # the IAM user credentials
        aws_secret_access_key: "your-secret-key"
        # the region where certificates will be created
        region_name: "your-region"
        # specify the Amazon CA certificate to use [verisign, ecc, rsa]
        endpoint_type: verisign
        # activation of certificate upon creation
        activate_cert: true
        # the thing prefix for the thing name (optional: if not given, no thing is created)
        thing_prefix: "MyThing"
        # the thing policy to attach to the certificate (optional if not given no policy is attached to cert)
        thing_policy: test_policy


The flexibility provided by :samp:`dcz.yml` is very high. The :samp:`provisioning` section contains a list of resources of different types. Resource types and the provisioning :samp:`method` specify how the resouce is generated. The following types of resources are available:

    * :samp:`file`, specifies an existing file identified by the path in the :samp:`args` field
    * :samp:`cacert`, specifies a CA certificate.
    * :samp:`clicert`, specifies a device certificate.
    * :samp:`prvkey`, specifies a device private key.
    * :samp:`pubkey`, specifies a device public key.
    * :samp:`endpoint`, specifies the list of endpoints the device can connect to.
    * :samp:`devinfo`, specifies some device properties needed to correctly connect to the cloud service.


Resources are created in a different way depending on :samp:`provisioning.method`:

    * :samp:`manual` method treats all resource types as files loaded from the path given in :samp:`args`.
    * :samp:`aws_iot_key_cert` method generates device credentials by calling the appropriate AWS API endpoint (via boto3). In particular, both the private key and the
      device certificate are requested, while the CA certificate is loaded from file shipping with the erynth toolchain. Device info and endpoints are again generated
      through API calls and saved in json format. Optionally a Thing is also automatically created and the policy/certificate are attached to it.
    * :samp:`aws_iot_csr_cert` method generates device credentials from a CSR signed with an openssl generated private key. [Not yet implemented]
    * :samp:`gcp_jwt` method generates device credentials for GCP based on JWT tokens. [Not yet implemented]

Resources also have a :samp:`name` (max 16 characters) and a :samp:`mapping`, a list of addresses on the device flash where the resource will be saved. Addresses can be more than one since resources can be replicated and versioned for a safer device lifecycle. Optionally resources can have a format (default "bin") and can be ecnrypted. 
Encrypted resources are stored in clear and are encrypted by the device using the :ref:`DCZ module <lib-zerynth-dcz>` when the firmware first run (typically during end of line testing). This method does not replace gold standard security approaches like the use of dedicated crypto elements, but can protect sensitive data from simple attacks.
The encryption is device dependent and a ciphertext can only be decrypted by the device that produced it.


The optional :samp:`dcz` section provides information to be used together with the :ref:`DCZ module <lib-zerynth-dcz>`.



Mass Programming
================

When producing small to medium batches of IoT devices, it is useful to have an automatic mean of provisioning and flashing. This feature is provided
by the mass programming command documented below. A mass programming configuration file is needed to describe the device parameters: ::

    ############################
    # Mass Programming Section
    #
    # in the "config" section, all the options necessary
    # to avoid human intervention are specified.

    config:
        # the name of the target micro/board (i.e. esp32_devkitc)
        target: esp32_devkitc
        # options relative to the device itself (port, baudrate, probe, etc...)
        dev:
            # the serial port of the device
            port: /dev/ttyUSB0
            # the baud rate of the port (defaults to 115200)
            baud: 1500000
            # the programming probe
            probe: null
        # specify the method for device registration [jtag, target_custom]
        register: target_custom
        # specify the parameters for VM to be mass programmed
        vm:
            # the specific rtos of the VM
            rtos: "esp32-rtos"
            # vm version
            version: "r2.2.0"
            # vm patch
            patch: "base"
            # list of vm features
            feats: []
            # set vm to shareable [if set to True, the final user of the device will be able to uplink firmware to the device
            and obtain a copy of the VM: useful for demo boards and kits]
            shareable: False
            # if set to true, the VM will not accept any new firmware from the uplink command [Not yet implemented]
            locked: False
        # path of the project to compile
        project: awesome/zerynth/project


"""


from base import *
from devices import get_device_by_target
import click
import base64
import struct
from jtag import *
from .dcz import *


@cli.group(help="Manage mass programming.")
def massprog():
    pass

@massprog.command("start",help="Start mass programming")
@click.argument("mppath")
@click.option("--clean",flag_value=True,default=False,help="rebuild project")
def mp_start(mppath,clean):
    """
.. _ztc-cmd-massprog:

Massprog command
================

The command: ::

    ztc massprog start path

will start a register-virtualize-uplink process in a single command using information contained in the :samp:`massprog.yml` file present at :samp:`path`.
If the project specified in :samp:`massprog.yml` contains a :samp:`dcz.yml` file, resources will be provisioned and flashed to the device together with the VM and the firmware.

The :command:`massprog` may take the additional :option:`--clean` option that forces a firmware compilation and link.


    """
    mapfile = fs.path(mppath,"massprog.yml")
    map = fs.get_yaml(mapfile)
    config = map["config"]
    target = config["target"]
    register = config["register"]
    project = config["project"]
    vmopts = config["vm"]
    shareable = vmopts.get("shareable", False)
    locked = vmopts.get("locked", False)
    vm_rtos = vmopts["rtos"]
    vm_version = vmopts["version"]
    vm_patch = vmopts["patch"]
    vm_feats = vmopts.get("feats",[])
    dev_options = config.get("dev",{})
    dczmapfile = fs.path(project,"dcz.yml")
    dcz_map = map.get("dcz",{})
    resources = {}


    info("===== Registration")
    dev = get_device_by_target(target,dev_options,skip_reset=True)
    info("Target",target)
    if register=="target_custom":
        chipid = dev.custom_get_chipid(outfn=info)
    elif register=="jtag":
        if not dev.jtag_capable:
            fatal("Target does not support probes!")
        probe = dev_options.get("probe")
        if not probe:
            fatal("Missing probe definition in dev_options section!")
        tp = start_temporary_probe(target,probe)
        chipid = dev.get_chipid()
        stop_temporary_probe(tp)
    elif register=="standard":
        chipid = True
    else:
        fatal("Unknown registration method!")

    if not chipid:
        fatal("Can't find chipid!")

    if register == "standard":
        res, out, _ = proc.run_ztc("device","register_raw",target,"--spec", "port:%s" % dev_options["port"], "--spec", "baud:%s" % dev_options["baud"], outfn=log)
    else:
        res, out, _ = proc.run_ztc("device","register_by_uid",chipid,target,outfn=log)
    if res:
        fatal("Can't register!")
    lines = out.split("\n")
    for line in lines:
        if "registered with uid:" in line:
            pos = line.rindex(":")
            dev_uid = line[pos+1:].strip()
            print("[",dev_uid,"]")
            break
    else:
        fatal("Can't find device uid!")

    info("===== Licensing")
    args = []
    for feat in vm_feats:
        args.append("--feat")
        args.append(feat)
    if shareable:
        args.append("--reshare")
        args.append("--share")
    if locked:
        args.append("--locked")
    info("Getting vm for",dev_uid,vm_version,vm_rtos,vm_patch,*args)
    res, out, _ = proc.run_ztc("vm","create_by_uid",dev_uid,vm_version,vm_rtos,vm_patch,*args,outfn=log)
    if res:
        fatal("Can't create vm!")
    lines = out.split("\n")
    for line in lines:
        if "created with uid:" in line:
            pos = line.rindex(":")
            vm_uid = line[pos+1:].strip()
            print("[",vm_uid,"]")
            break
    else:
        fatal("Can't find vm uid!")

    info("===== VM")
    # get vm bin
    vmfile = tools.get_vm_by_uid(vm_uid)
    vm = fs.get_json(vmfile)
    vmpath = fs.path(mppath,"vms",vm_uid)
    if not fs.exists(vmpath):
        fs.makedirs(vmpath)
    if isinstance(vm["bin"],str):
        vmbin  = bytearray(base64.standard_b64decode(vm["bin"]))
        vmbinfile = fs.path(vmpath,"vm.bin")
        fs.write_file(vmbin,vmbinfile)
        vmloc = vm["loc"]
        resources["VM"] = Resource({"type":"file","name":"VM","mapping":vm["loc"],"args":vmbinfile})
        resources["VM"].load_from_file()
    else:
        vmbin=[base64.standard_b64decode(x) for x in vm["bin"]]
        for i,vv in enumerate(vmbin):
            vmbinfile = fs.path(vmpath,"vm"+str(i)+".bin")
            fs.write_file(vv,vmbinfile)
            resources["VM-Fragment-"+str(i)] = Resource({"type":"file","name":"VM-Fragment-"+str(i),"mapping":[vm["loc"][i]],"args":vmbinfile})
            resources["VM-Fragment-"+str(i)].load_from_file()
    info("     using",vmpath)


    # check for binary fw
    info("===== Firmware")
    fwbin = fs.path(mppath,"fw.bin")
    bytecode = fs.path(mppath,"fw.vbo")
    if clean:
        info("Cleaning...")
        fs.rm_file(fwbin)
        fs.rm_file(bytecode)
        clean=False
    if not fs.exists(fwbin):
        warning("No binary bytecode present, checking vbo for",project)
        if not fs.exists(bytecode):
            warning("No bytecode present either, compiling project at",project)
            res, out, _ = proc.run_ztc("compile",project,target,"-o",fs.path(mppath,"fw.vbo"),outfn=log)
            if res:
                fatal("Can't compile project at",project)
        res, out, _ = proc.run_ztc("link",vm_uid,bytecode,"--bin","--file",fs.path(mppath,"fw.bin"),outfn=log)
        if res:
            fatal("Can't link project at",project)
    info("     using",fwbin)
    resources["Firmware"]=Resource({"type":"file","args":fwbin,"mapping":vm["bcloc"],"name":"Firmware"})
    resources["Firmware"].load_from_file()

    info("===== Provisioning Resources")
    layout = get_layout_at(project,fail=True)
    layout.add_resources(resources)
    layout.validate()
    log_table(layout.to_table(),headers=["Name","Address","Size","Checksum"])


    info("===== Burn Layout")
    # burn layout
    dev.do_burn_layout(layout,dev_options,outfn=info)




