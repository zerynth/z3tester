"""
Alert of a workspace
"""

import click
from zdevicemanager.cli.helper import handle_error
from zdevicemanager.base.cfg import env
from zdevicemanager.base.base import log_table, pass_zcli, info, log_json


@click.group(help="Manage the alerts")
def alert():
    pass


@alert.command(help="Get all the alerts of a workspace")
@click.option('--status', default="active", type=click.Choice(['active', 'disabled']), help="Filter alerts by status.")
@click.argument('workspace-id')
@pass_zcli
@handle_error
def all(zcli, workspace_id, status):
    table = []

    alerts = zcli.zdm.alerts.list(workspace_id, status)
    if env.human:
        for a in alerts:
            table.append([a.name, a.threshold, a.status, a.last_time_scheduled])
        log_table(table, headers=["Name", "Threshold", "Status", "LastSchedule"])

    else:
        log_json([a.toJson for a in alerts])
