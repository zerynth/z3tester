"""
.. _zdm-cmd-gates-export:


Export gates
============

List of commands:

* :ref:`Create <zdm-cmd-gates-export-create>`
* :ref:`Update export gate <zdm-cmd-gates-export-update>`
* :ref:`List export gates <zdm-cmd-gates-export-get-all>`

    """

import click
from zdevicemanager.cli.helper import handle_error
from zdevicemanager.base.cfg import env
from zdevicemanager.base.base import log_table, pass_zcli, info, log_json


@click.group(help="Manage the export gates")
def export():
    pass


@export.command(help="Create a new export gate. ")
@click.argument('name')
@click.argument('type')
@click.argument("frequency")
@click.argument('workspace-id')
@click.argument('email')
@click.option('--tag', multiple=True)
@click.option('--fleet', multiple=True)
@click.option('--export-name', default="", help="Name of the export")
@click.option('--day', default='1', help="Day for the export (0 Sunday... 6 Saturday)",
              type=click.Choice(['0', '1', '2', '3', '4', '5', '6']))
@pass_zcli
@handle_error
def create(zcli, name, export_name, type, frequency, day, workspace_id, email, tag, fleet):
    # TODO
    pass


@export.command(help="Get all the export gates of a workspace")
@click.option('--status', default="active", type=click.Choice(['active', 'disabled']), help="Filter gates by status.")
@click.argument('workspace-id')
@pass_zcli
@handle_error
def all(zcli, workspace_id, status):
    # TODO
    pass

@export.command(help="Update an export gate")
@click.argument('gate-id')
@click.option('--name', help='To change webhook name')
@click.option('--cron', help='To change webhook period', type=int)
@click.option('--dump-type', help='To change webhook url', type=click.Choice(['json', 'csv']))
@click.option('--email', help='To change notifications email')
@click.option('--tag', multiple=True, help='To replace gate tags')
@pass_zcli
@handle_error
def update(zcli, gate_id, name=None, cron=None, dump_type=None, email=None, tag=None):
    # TODO
    pass