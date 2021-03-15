"""
Manage he data stream
"""

import click
from zdevicemanager.cli.helper import handle_error
from zdevicemanager.base.cfg import env
from zdevicemanager.base.base import log_table, pass_zcli, info, log_json


@click.group(help="Manage data streams")
def data():
    pass


@data.command(help="List all data streams")
@click.argument('workspace-id')
@click.option('--status', default="", type=click.Choice(['active', 'disabled', ""]), help='Filter stream by its status')
@pass_zcli
@handle_error
def all(zcli, workspace_id, status):

    dstream = zcli.zdm.streams.list(workspace_id, "data", status)
    if env.human:
            table = []
            for stream in dstream:
                table.append([stream.name, stream.status, stream.period,  stream.subtype, stream.last_time_scheduled])
            log_table(table, headers=["Name", "Status", "Period (s)", "To", "Last schedule"])
    else:
        log_json([s.toJson for s in dstream])