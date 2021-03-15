"""
.. _zdm-cmd-fota:


Fota
====

The ZDM allows to enable FOTA (over the air firmware updates) on devices.

List of FOTA commands:

* :ref:`Upload a firmware <zdm-cmd-fota-prepare>`
* :ref:`Start a FOTA <zdm-cmd-fota-schedule>`
* :ref:`Check FOTA status <zdm-cmd-fota-check>`

    """

import click
import json
from zdevicemanager.base import proc
from zdevicemanager.base.base import info, error, log_table, pass_zcli, debug, fatal, log_json, warning
from zdevicemanager.base.fs import fs
from zdevicemanager.base.tools import tools
from zdevicemanager.base.cfg import env
from ..helper import handle_error

@click.group(help="Manage the FOTA update")
def fota():
    pass


@fota.command(help="Prepare FOTA to the ZDM")
@click.argument("project", type=click.Path(), required=False)
@click.argument("device-id", required=False)
@click.argument('version', required=False)
@pass_zcli
@handle_error
def prepare(zcli, project, device_id, version):
    """
    .. _zdm-cmd-fota-prepare:

    Prepare the FOTA
    -----------------

    The command compiles and uploads the firmware for a device into ZDM.
    The version is a string identifying the version of the firmware (e.g., "1.0"). ::

        zdm fota prepare [Firmware project path] [DeviceId] [Version]

    """
    if project is None or device_id is None or version is None:
        # search for information in project.yml
        project = "." if not project else project
        cfg = fs.get_project_config(project,fail=True)
        device_id = cfg.get("zdm",{}).get("device_id")
        version = cfg.get("zdm",{}).get("fota",{}).get("version")
        if "zdm" not in cfg:
            cfg["zdm"]={}
        if not device_id:
            cfg["zdm"]["device_id"] = None
            fs.set_project_config(project,cfg)
        if not version:
            if "fota" not in cfg["zdm"]:
                cfg["zdm"]["fota"]={}
            cfg["zdm"]["fota"]["version"] = None
            fs.set_project_config(project,cfg)

        if not device_id:
            fatal("Please add ZDM device_id in the project configuration in zdm section")
        if not version:
            fatal("Please add firmware version in the project configuration in zdm section")
        else:
            # convert to string
            version = str(version)

    do_prepare(zcli,project,device_id,version)
    # if device_id:
    #    get 'vm_uid', 'vm_target' from status service of a device (__vm_info)
    #    get the 'workspace_id' of the device
    #    ztc compile(project_path, vm_target, vbo)
    #    ztc link(project_path, target, vbo_file)
    #    (ztc get metadata)
    #    upload firmwares
    # else:
    #    zdm device all    # with the 'vm_uid', and 'vm_target' of ztc vm list. user must select one of them.


def do_prepare(zcli,project,device_id,version):
    status = zcli.zdm.status.get_device_vm_info(device_id)
    if status is None:
        fatal("Fota cannot be prepared. Please connect device '{}' to the ZDM at least one time.".format(device_id))

    vm_info = status.value

    if "vm_target" not in vm_info:
        fatal("The target of the virutal machine is missing. Please reconnect the device '{}' to the ZDM.".format(device_id))
    vm_target = vm_info['vm_target']
    if "vm_uid" not in vm_info:
        fatal("The ID of the virtual machine is missing. Please reconnect the device '{}' to the ZDM.".format(device_id))
    vm_uid = vm_info['vm_uid']
    if "vm_version" in vm_info:
        vm_version = vm_info['vm_version']

    vm_hash_feature = ""
    target_device = ""

    vms = _ztc_vm_list()
    if vms['total'] > 0:
        for vm in vms['list']:
            if vm['uid'] == vm_uid:
                if "ota" not in vm['features']:
                    fatal("The vm '{}' of device '{}' doesn't support FOTA. Please use a VM with feature OTA enabled.".format(vm_uid, device_id))
                else:
                    vm_hash_feature = vm['hash_features']
                    target_device  = vm['dev_type']
    else:
        fatal("No virtual machine found. Please create a virtual machine")

    device = zcli.zdm.devices.get(device_id)
    workspace_id = device.workspace_id
    info("workspace id '{}'".format(workspace_id))
    vbo_file = fs.path(env.tmp, 'test_temp_fw.vbo')

    try:
        _ztc_compile(project, vm_target, vbo_file)
        fw_json1 = _ztc_link(vbo_file, vm_uid, '0')
        fw_json2 = _ztc_link(vbo_file, vm_uid, '1')
        fw_bin1 = fw_json1['bcbin']
        fw_bin2 = fw_json2['bcbin']
    except Exception as e:
        fatal(e)

    metadata = {"vm_version": vm_version, "vm_feature": vm_hash_feature, "dev_type": target_device}
    res = zcli.zdm.firmwares.upload(workspace_id, version, [fw_bin1, fw_bin2], metadata)
    if env.human:
        log_table([[res.id, res.version, res.metadata]], headers=["ID", "Version", "Metadata"])
    else:
        raw = res.toJson
        del raw['firmware']
        log_json(raw)


@fota.command(help="Start a fota")
@click.argument('firmware-version')
@click.argument('devices', nargs=-1)
@pass_zcli
@handle_error
def schedule(zcli, firmware_version, devices):
    """
    .. _zdm-cmd-fota-schedule:

    Start a FOTA
    -----------------

    Once uploaded a firmware, it's possible to send the FOTA command to a device that will download it from the ZDM and uplink it.
    If the FOTA operation is finished, ZDM allows to check if the device has accepted or refused it using the :ref:`check fota status<zdm-cmd-fota-check>` command.

    To start a fota, type the command: ::

        zdm fota schedule fw_version device_id

    where :samp:`fw_version` is the firmware version associated to the device's workspace uid and :samp:`device_id` is the id of the device that will receive the command.

        """

    print(devices)
    zcli.zdm.fota.schedule(firmware_version, devices)
    info("Sent Fota to devices {}. Firmware Version [{}] ".format(devices, firmware_version))


@fota.command(help="Check the status of a FOTA update on a single device")
@click.argument('device-id')
@pass_zcli
@handle_error
def check(zcli, device_id):
    """
    .. _zdm-cmd-fota-check:

    Check FOTA status
    -----------------

    To check the status of a FOTA update, to know if the device finished the task or if an error occurred, type the
    following command: ::

        zdm fota check device_uid

    where :samp:`device_uid` is the uid of the device to check.

        """
    fota_exp = zcli.zdm.fota.status_expected(device_id)
    fota_cur = zcli.zdm.fota.status_current(device_id)

    schedule_at = fota_exp.version if fota_exp else "<none>"

    if fota_exp is None and fota_cur is not None:
        # the job has been scheduled (exp is None)  and the device has sent the response (fota_cur not None)
        status = "done"
        result = fota_cur.value if fota_cur is not None else "<no result>"
        result_at = fota_cur.version if fota_cur is not None else "<no result>"
    elif fota_exp is None and fota_cur is None:
        # the job has not been scheduled nor a response has been received
        status = "<none>"
        result = "<none>"
        result_at = "<none>"
    elif fota_exp is not None and fota_cur is not None:
        if fota_cur.version > fota_exp.version:
            # fota has been scheduled and the device has sent a response
            status = "done"
            result = fota_cur.value if fota_cur is not None else "<no result>"
            result_at = fota_cur.version if fota_cur is not None else "<no result>"
        else:
            status = "pending"
            result = "<none>"
            result_at = "<none>"
    elif fota_exp is not None and fota_cur is None:
        # the job has been scheduled bu the device has not sent a response
        status = "pending"
        result = "<none>"
        result_at = "<none>"
    else:
        status = "<unknown>"
        result = "<none>"
        result_at = "<none>"

    log_table([[status, schedule_at, result, result_at, ]],
              headers=["Status", "ScheduleAt", "Result", "ResultAt"])


def _ztc_vm_list():
    debug('ZTC: vm list')
    # ztc compile -o fw.c [Firmware project path] [target]
    e, out_vmlist_raw, err = proc.runzcmd(
        '-J',
        'vm',
        'list'
    )
    if e:
        fatal(err)
    else:
        res = _split_raw_json(out_vmlist_raw)
        return res

def _ztc_compile(project_path, target, vbo_file):
    debug('ZTC: compiling', project_path)
    # ztc compile -o fw.c [Firmware project path] [target]
    e, out_fw_raw, err = proc.runzcmd(
        'compile',
        '-o',
        vbo_file,
        project_path,
        target,
    )
    if e:
        fatal(err)


# def _ztc_link(vbo_file, vm_uid, bytecode, out_file):
#     debug('Linking firmware ', vbo_file, "on bytecode", bytecode)
#     e, out_fw_raw, err = proc.runzcmd(
#         '-J',
#         'link',
#         '--bc',
#         bytecode,
#         '--file',
#         out_file,
#         vm_uid,
#         vbo_file
#     )
#     if e:
#         fatal(err)

def _ztc_link(vbo_file, vm_uid, bytecode):
    debug('Linking firmware ', vbo_file)
    e, out_fw_raw, err = proc.runzcmd(
        '-J',
        'link',
        '--bc',
        bytecode,
        vm_uid,
        vbo_file
    )

    if e:
        fatal(err)
    else:
        res = _split_raw_json(out_fw_raw)
        return res

def _split_raw_json(raw_output):
    """Split the raw output of the ztc and parse only json"""
    raw = raw_output.split("\n")
    for r in raw:
        try:
            j = json.loads(r)
            return j
        except e:
            pass
            error(r)
