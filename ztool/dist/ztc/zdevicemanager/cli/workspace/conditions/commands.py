"""
.. _zdm-cmd-workspace-conditions:

**********
Conditions
**********

In the ZDM conditions are used in devices to notify some particular situations.
A condition can be opened and then closed.

List of commands:

* :ref:`List conditions <zdm-cmd-workspace-conditions-all>`

    """
import click
from zdevicemanager.base.base import log_table, log_json, pass_zcli, info
from zdevicemanager.base.cfg import env

from zdevicemanager.cli.helper import handle_error

@click.group(help='Manage the conditions of a workspace')
def condition():
    pass


@condition.command(help='Get all the condition of a workspace.')
@click.argument('workspace-id')
@click.argument('tag')
@click.option('--device-id', default=None, help="filter conditions sent by a device")
@click.option('--threshold', default="0", help="filter conditions that are opened (or closed) greater than threshold seconds.")
@click.option('--status', type=click.Choice(['open', 'closed']), default='open')
@pass_zcli
@handle_error
def all(zcli, workspace_id, tag, device_id,  threshold, status):

    """
.. _zdm-cmd-workspace-conditions-all:

List conditions
--------------

To get all the conditions of a device use the command: ::

    zdm workspace condition all workspace_id tag

where :samp:`workspace_id` is the uid of the workspace and `tag` is the tag of the conditions
:samp:`device_id` is the uid of the device
:samp:`threshold` is the min duration of the conditions in seconds

It's also possible to filter results using the options:

* :option:`--status` to filter on conditions status [open, closed]
* :option:`--device_id` to filter on devices
* :option:`--threshold` to indicate the minimum duration of the conditions to return

    """

    conditions = zcli.zdm.conditions.list(workspace_id, tag, device_id, threshold, status)
    if env.human:
        table = []
        for condition in conditions:
            table.append([condition.Uuid, condition.Tag, condition.DeviceId, condition.Start, condition.Finish, condition.Duration])
        log_table(table, headers=["ID", "Tag", "Device", "Start", "Finish", "Duration"])
    else:
        cc = []
        for c in conditions:
            cc.append(c.toJson)
        log_json(c)