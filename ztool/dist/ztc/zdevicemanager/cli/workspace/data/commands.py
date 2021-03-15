"""
.. _zdm-cmd-workspace-data:

Data
===============

List of commands:

* :ref:`Get data <zdm-cmd-workspace-data-get>`
* :ref:`List tags <zdm-cmd-workspace-data-tags>`
* :ref:`Export data <zdm-cmd-workspace-data-export>`

    """

import click
from zdevicemanager.base.base import log_table, log_json, pass_zcli, info
from zdevicemanager.base.cfg import env

from zdevicemanager.cli.helper import handle_error

from .export.commands import export

@click.group(help='Manage the data of a workspace')
def data():
    pass


@data.command(help='Get all the data of a workspace.')
@click.argument('workspace-id')
@click.argument('tag')
@click.option('--device-id', default=None, help='filter data by device id')
@click.option('--start', default=None, help='start date filter (RFC3339)')
@click.option('--end', default=None, help='end date filter (RFC3339')
@pass_zcli
@handle_error
def all(zcli, workspace_id, tag, device_id, start, end):
    """
.. _zdm-cmd-workspace-data-get:

Get data
--------

To get all the data of a workspace associated to a tag use the command: ::

    zdm workspace data all uid tag

where :samp:`uid` is the uid of the workspace, and  :samp:`tag` is the tag of the data to download.

To filter result use the options:

* :option:`--device-id`
* :option:`--start`
* :option:`--end`

    """

    tags = zcli.zdm.data.get(workspace_id, tag, device_id=device_id, start=start, end=end)
    if env.human:
        if len(tags) > 0:
            table = []
            for tag in tags:
                table.append([tag.Tag, tag.Payload, tag.DeviceId, tag.DeviceName, tag.TimestampDevice, tag.TimestampCloud])
            log_table(table, headers=["Tag", "Payload", "DeviceId", "DeviceName", "TimestampDevice", "TimestampCloud"])
        else:
            info("No data present for to tag [{}].".format(tag))
    else:
        log_json([tag.toJson for tag in tags])


@data.command(help="Get all the data tags of a workspace")
@click.argument('workspace-id')
@pass_zcli
@handle_error
def tags(zcli, workspace_id):
    """
.. _zdm-cmd-workspace-data-tags:

List tags
---------

When a device publish data to the ZDM it label them with a string called tag. With the following command it's possible to see all the tags
that devices associated to the workspace used as data label. ::

    zdm workspace data tags uid

where :samp:`uid` is the uid of the workspace

    """
    tags = zcli.zdm.data.list(workspace_id)
    if env.human:
        if len(tags) > 0:
            log_table([[tags]], headers=["Tags"])
        else:
            info("Empty tags for workspace {}.".format(workspace_id))
    else:
        log_json([tag.toJson for tag in tags])


data.add_command(export)