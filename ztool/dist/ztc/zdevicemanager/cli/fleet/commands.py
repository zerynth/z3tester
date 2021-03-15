"""
.. _zdm-cmd-fleet:


Fleets
======

In the ZDM a fleet is a set of devices. At the first login, a 'default' workspace containing a
'default' fleet will be created.
The main attributes of a fleet are:

* :samp:`uid`, a unique id provided by the ZDM after the :ref:`fleet creation <zdm-cmd-fleet-create>` command
* :samp:`name`, a name given by the user to the fleet in order to identify it


List of fleet commands:

* :ref:`Create <zdm-cmd-fleet-create>`
* :ref:`Get a single fleet <zdm-cmd-fleet-get-fleet>`

    """

import click
from zdevicemanager.base.base import log_table, info, pass_zcli, log_json
from zdevicemanager.base.cfg import env
from ..helper import handle_error


@click.group(help="Manage the fleets")
def fleet():
    pass


@fleet.command(help="Create a new fleet")
@click.argument('name')
@click.argument('workspaceid')
@pass_zcli
@handle_error
def create(zcli, name, workspaceid):
    """
.. _zdm-cmd-fleet-create:

Fleet creation
--------------

To create a new fleet of devices inside a workspace use the command: ::

    zdm fleet create name workspace_uid

where :samp:`name` is the fleet name and :samp:`workspace_id` is the uid of the workspace that will contain the fleet.

    """
    fleet = zcli.zdm.fleets.create(name, workspaceid)
    if env.human:
        log_table([[fleet.id, fleet.name, fleet.workspace_id]], headers=["ID", "Name", "WorkspaceID"])
    else:
        log_json(fleet.toJson)


@fleet.command(help="Get a single fleet by its uid")
@click.argument('id')
@pass_zcli
@handle_error
def get(zcli, id):
    """
.. _zdm-cmd-fleet-get-fleet:

Get fleet
---------

To get a single fleet information, use this command to see its name, the uid of the workspace that contains it and the list of devices inside::

    zdm fleet get uid

where :samp:`uid` is the fleet uid

    """
    fleet = zcli.zdm.fleets.get(id)
    if env.human:
        log_table([[fleet.id, fleet.name, fleet.workspace_id]],
              headers=["ID", "Name", "WorkspaceID"])
    else:
        log_json(fleet.toJson)


def list_fleets(zcli, workspace_id):
    """
    List fleets of a workspace
    """
    resp = zcli.zdm.fleets.list(workspace_id)

    if env.human:
        log_table([[fleet.id, fleet.name, fleet.workspace_id]],
                  headers=["ID", "Name", "WorkspaceID"])
    else:
        log_json(fleet.toJson)