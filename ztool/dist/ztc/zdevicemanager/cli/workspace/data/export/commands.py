"""
.. _zdm-cmd-workspace-data-export:


Export
======

The ZDM allows to download devices data in JSON and CSV,
with the possibility to filter on fleets and tags and on time ranges, specifying
a start and end time (RFC3339 format).

List of commands:

* :ref:`Create <zdm-cmd-workspace-data-export-create>`
* :ref:`Get an export <zdm-cmd-workspace-data-export-get>`

    """

import click
from zdevicemanager.base.cfg import env
from zdevicemanager.base.base import log_table, pass_zcli, info, log_json

from zdevicemanager.cli.helper import handle_error


@click.group(help="Manage the exports")
def export():
    pass


@export.command(help="Create a new export")
@click.argument('name')
@click.argument('type')
@click.argument('workspace-id')
@click.argument('start')
@click.argument('end')
@click.option('--tag', multiple=True)
@click.option('--fleet', multiple=True)
@pass_zcli
@handle_error
def create(zcli, name, type, workspace_id, start, end, tag, fleet):
    """
.. _zdm-cmd-workspace-data-export-create:

Export creation
----------------

To create a new export use the command: ::

    zdm workspace data export create name type workspace_id

where :samp:`name` is the name of the new export
:samp:`type` is the type ox export (json or csv)
:samp:`workspace_id` is the uid of the workspace to receive data from
:samp:`start` is the starting date for data (RFC3339)
:samp:`end` is the ending date for data (RFC3339)

It's also possible to add filters on data using the following options:

:option:`--tag` To specify tags to filter data (can be specify more than one)
:option:`--fleet` To specify fleets to filter data (can be specify more than one)

    """

    tags = []
    fleets = []

    for t in tag:
        tags.append(t)

    for f in fleet:
        fleets.append(f)

    configurations = {"workspace_id": workspace_id, "start": start, "end": end, "tags": tags, "fleets": fleets}

    notifications = {

    }

    exp = zcli.zdm.exports.create(name, type, configurations, notifications)
    if env.human:
        info("Export [{}] created successfully.".format(exp.id))
    else:
        log_json(exp.toJson)


@export.command(help="Get export's information")
@click.argument('export-id')
@pass_zcli
@handle_error
def get(zcli, export_id):
    """
.. _zdm-cmd-workspace-data-export-get:

Get export
----------

To get an existing export information use the command: ::

    zdm workspace data export get export_id

where :samp:`export_id` is the uid of the export

    """
    exp = zcli.zdm.exports.get(export_id)

    log_table([[exp.id, exp.Name, exp.Type, exp.Status, exp.Url]],
      headers=["ID", "Name", "Type", "Status", "URL"])
