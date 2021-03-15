"""
.. _zdm-cmd-workspace:

Workspaces
==========

A workspace represents a project containing fleets of devices.
The main attributes of a workspace are:

* :samp:`uid` a unique id provided by the ZDM with the :ref:`workspace creation <zdm-cmd-workspace-create>` command
* :samp:`name` a name given by the user to the workspace in order to identify it
* :samp:`description` a string given by the user to describe the project

At the first log in, a 'default' workspace containing a 'default' fleet will be created.


List of workspace commands:

* :ref:`Create <zdm-cmd-workspace-create>`
* :ref:`List workspaces <zdm-cmd-workspace-get-all>`
* :ref:`List fleets of a workspace <zdm-cmd-workspace-get-all-fleets>`
* :ref:`Get a single workspace <zdm-cmd-workspace-get-workspace>`
* :ref:`Manage data <zdm-cmd-workspace-data>`
* :ref:`List firmwares <zdm-cmd-workspace-firmware>`
* :ref:`Manage conditions <zdm-cmd-workspace-conditions>`


The list of supported devices is available :ref:`here <doc-supported-boards>`

    """

import click
from zdevicemanager.base.base import log_table, log_json, pass_zcli, info
from zdevicemanager.base.cfg import env
from .conditions.commands import condition
from .data.commands import data
from .alert.commands import alert
from .stream.commands import stream
from .export.commands import export


from ..helper import handle_error


@click.group(help="Manage the workspaces")
def workspace():
    pass


@workspace.command(help="List all the workspaces")
@pass_zcli
@handle_error
def all(zcli):
    """
.. _zdm-cmd-workspace-get-all:

List workspaces
---------------

To see the list of all workspaces, use the command: ::

    zdm workspace all

 The output is a table containing workspaces with ID, name, description

    """
    wks = zcli.zdm.workspaces.list()
    if env.human:
        table = []
        for ws in wks:
            table.append([ws.id, ws.name, ws.description])
        log_table(table, headers=["ID", "Name", "Description"])
    else:
        log_json([wk.toJson for wk in wks])


@workspace.command(help="Get a workspace by its uid")
@click.argument('id')
@pass_zcli
@handle_error
def get(zcli, id):
    """
.. _zdm-cmd-workspace-get-workspace:

Get workspace
-------------

To get a single workspace information, use this command: ::

    zdm workspace get uid

where :samp:`uid` is the workspace uid.

    """
    ws = zcli.zdm.workspaces.get(id)
    if env.human:
        data = [ws.id, ws.name, ws.description]
        log_table([data], headers=["ID", "Name", "Description"])
    else:
        log_json(ws.toJson)


@workspace.command(help="Create a new workspace")
@click.argument('name')
@click.option('--description', default="", type=click.STRING, help="Small description af the workspace.")
@pass_zcli
@handle_error
def create(zcli, name, description):
    """
.. _zdm-cmd-workspace-create:

Create workspace
------------------

To create a new workspace on the ZDM use the command: ::

    zdm workspace create name

where :samp:`name` is the name of the new workspace

It's possible to insert a description of the workspace adding the option :option:`--description desc`

    """
    wks = zcli.zdm.workspaces.create(name, description)
    if env.human:
        log_table([[wks.id, wks.name, wks.description]], headers=["ID", "Name", "Description"])
    else:
        log_json(wks.toJson)


@workspace.command(help="List all the firmwares of a workspace")
@click.argument('workspace-id')
@pass_zcli
@handle_error
def firmwares(zcli, workspace_id):
    """
.. _zdm-cmd-workspace-firmware:

List firmwares
--------------

To have a list of the firmwares uploaded to the ZDM associated to a workspace use the command: ::

    zdm workspace firmwares uid

where :samp:`uid` is the uid of the workspace.

    """
    table = []
    firmwares = zcli.zdm.firmwares.list(workspace_id)
    if env.human:
        for d in firmwares:
            table.append([d.id, d.version, d.metadata, d.workspace_id])
        log_table(table, headers=["ID", "Version", "Metadata", "WorkspaceID"])
    else:
        log_json([frm.toJson for frm in firmwares])


@workspace.command(help="Get all the fleets of a workspace")
@click.argument('workspace-id')
@pass_zcli
@handle_error
def fleets(zcli, workspace_id):
    """
.. _zdm-cmd-workspace-get-all-fleets:

List fleets
------------

Use this command to have the list of fleets inside a workspace: ::

    zdm workspace fleet all uid

where :samp:`uid` is the uid of the workspace.

    """
    fleets = zcli.zdm.fleets.list(workspace_id)
    if env.human:
        table = []
        for fl in fleets:
            table.append([fl.id, fl.name, fl.description, fl.workspace_id])
        log_table(table, headers=["ID", "Name", "Description", "WorkspaceId"])
    else:
        log_json([fl.toJson for fl in fleets])



workspace.add_command(data)
workspace.add_command(condition)
workspace.add_command(alert)
workspace.add_command(stream)
# TODO: add exports
#workspace.add_command(export)
