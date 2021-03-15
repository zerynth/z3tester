"""
.. _zdm-cmd-device:

*******
Devices
*******

In the ZDM a device is a peripheral that can execute Zerynth bytecode. In order to do so a device must be prepared and customized with certain attributes.
The main attributes of a device are:

* :samp:`uid` a unique id provided by the ZDM with the :ref:`device creation <zdm-cmd-device-create>` command
* :samp:`name` a name given by the user to the device in order to identify it

1. The first step to connect device to the ZDM is the device :ref:`creation <zdm-cmd-device-create>`.
2. Device :ref:`security <zdm-cmd-device-credentials>` command

There also are commands to :ref:`list devices <zdm-cmd-device-get-all>`, to :ref:`get a single device info <zdm-cmd-device-get-device>`,
:ref:`update a device <zdm-cmd-device-update>`

List of device commands:

* :ref:`Create <zdm-cmd-device-create>`
* :ref:`Update <zdm-cmd-device-update>`
* :ref:`List devices <zdm-cmd-device-get-all>`
* :ref:`Get a single device <zdm-cmd-device-get-device>`
* :ref:`Create device's credentials <zdm-cmd-device-credentials>`

The list of supported devices is available :ref:`here <doc-supported-boards>`

    """

import click
from zdevicemanager.base.base import log_table, pass_zcli, info, log_json
from zdevicemanager.base.cfg import env
from zdevicemanager.base.cfg import fs

from ..helper import handle_error


@click.group(help="Manage the devices")
def device():
    pass


@device.command(help="Create a new device")
@click.option('--fleet-id', default=None, help='Fleet ID where the device is assigned')
@click.argument('name')
@pass_zcli
@handle_error
def create(zcli, fleet_id, name):
    """
.. _zdm-cmd-device-create:

Device creation
---------------

To connect a device to the ZDM, create a new device on ZDM to obtain a new device uid.
The creation command is: ::

    zdm device create name

where :samp:`name` is the name that of the device

Creating a device with this command, will associate it to the default fleet inside the default workspace.
To associate the device to another fleet with the optional argument:

:option:`--fleet-id uid`

To associate the device to another fleet, see the :ref:`update command <zdm-cmd-device-update>`
    """
    dev = zcli.zdm.devices.create(name, fleet_id)
    if env.human:
        log_table([[dev.id, dev.name, dev.fleet_id]], headers=["ID", "Name", "fleet_id"])
    else:
        log_json(dev.toJson)

@device.command(help="Generate credentials for an existing device")
@click.option('--endpoint_mode', default="secure", type=click.Choice(['secure', 'insecure']), help='Choose endpoint security')
@click.option('--credentials', default="device_token", type=click.Choice(['device_token', 'cloud_token']), help='Choose device credentials')
@click.option('--output','-o', default=".", type=str, help='Path to save zdevice.json')
@click.argument('device_id')
@pass_zcli
@handle_error
def credentials(zcli, device_id, endpoint_mode, credentials, output):
    """
.. _zdm-cmd-device-credentials:

Devices credentials
-------------------

To create a set of device credentials an existent device uid is needed.

The credentials generation command is: ::

    zdm device credentials device_id --credentials ctype --endpoint_mode etype --output dest-folder

where :samp:`device_id` is the device uid, :samp:`ctype` is the credentials type (chosen from :samp:`device_token` or :samp:`cloud_token`), :samp:`etype` is the endpoint security mode (choosen from :samp:`secure` or :samp:`insecure`), and :samp:`dest-folder` is the path where to save the credential file (named :samp:`zdevice.json`).

All options are not mandatory and if not given a default value is assigned:

    * :samp:`device_token` for :samp:`ctype`
    * :samp:`secure` for :samp:`etype`
    * current directory for :samp:`dest-folder`


    """
    res = zcli.zdm.devices.credentials(device_id, credentials, endpoint_mode)
    if env.human:
        outfile = fs.path(output,"zdevice.json")
        fs.set_json(res,outfile)
        info("Credentials file for",device_id,"saved at",outfile)
    else:
        log_json(res)


@device.command(help="Get all devices")
@pass_zcli
@handle_error
def all(zcli):
    """
.. _zdm-cmd-device-get-all:

List devices
------------

To list all the devices, use this command to see a table with a device for each rows
with the device uid, name and the uid of the fleet and workspace containing them.
To see all the devices use the command: ::

    zdm device all

    """

    table = []
    devs = zcli.zdm.devices.list()
    if env.human:
        for d in devs:
            table.append([d.id, d.name, d.fleet_id if d.fleet_id else "<none>", d.workspace_id, d.workspace_name])
        log_table(table, headers=["ID", "Name", "FleeId", "WorkspaceID", "WorkspaceName"])
    else:
        log_json([dev.toJson for dev in devs])


@device.command(help="Get a single device by its uid")
@click.argument('id')
@pass_zcli
@handle_error
def get(zcli, id):
    """
.. _zdm-cmd-device-get-device:

Get device
----------

To get a single device information, use this command to see the device name and the uid
of the fleet and the workspace that contain the device. ::

    zdm device get uid

where :samp:`uid` is the device uid.

    """

    device = zcli.zdm.devices.get(id)
    if env.human:
        log_table([[device.id, device.name, device.fleet_id, device.workspace_id, device.workspace_name]],
                  headers=["ID", "Name", "FleetID", "WorkspaceID", "WorkspaceName"])
    else:
        dev = device.toJson
        dev.update({"workspace_id":device.workspace_id})
        log_json(dev)


@device.command(help="Update a device")
@click.option('--fleet-id', default=None, help='Id of the new fleet')
@click.option('--name', default=None, help='Name of the device')
@click.argument('id')
@pass_zcli
@handle_error
def update(zcli, id, fleet_id, name):
    """
.. _zdm-cmd-device-update:

Update a device
---------------

Use this command to update the device name, or to change the fleet uid.
To update a device use its uuid, with the possibility to use optional arguments to update its name or fleet uid.
Use the command: ::

    zdm device update uid

And the optional arguments are:

* :option:`--fleet-id uid` the uid of the fleet that will contain the device
* :option:`--name name` the new name for the device

    """
    zcli.zdm.devices.update(id, name, fleet_id)
    info("Device [{}] updated correctly.".format(id))

