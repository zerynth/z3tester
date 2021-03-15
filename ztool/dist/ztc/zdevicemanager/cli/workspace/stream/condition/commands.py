"""
Manage the condition stream
"""

import click
from zdevicemanager.cli.helper import handle_error
from zdevicemanager.base.base import log_table, pass_zcli, info, log_json
from zdevicemanager.base.cfg import env

@click.group(help="Manage condition streams")
def condition():
    pass


@condition.command(help="List all condition streams")
@click.argument('workspace-id')
@click.option('--status', default="", type=click.Choice(['active', 'disabled', ""]), help='Filter stream by its status')
@pass_zcli
@handle_error
def all(zcli, workspace_id, status):
    dstream = zcli.zdm.streams.list(workspace_id, "condition", status)
    if env.human:
        table = []
        for stream in dstream:
            table.append([stream.name, stream.status, stream.period, stream.subtype, stream.last_time_scheduled])
        log_table(table, headers=["Name", "Status", "Period (s)", "To", "Last Schedule"])
    else:
        log_json([s.toJson for s in dstream])