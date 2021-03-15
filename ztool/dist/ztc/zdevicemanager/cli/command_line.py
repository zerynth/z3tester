from zdevicemanager.base import cli

from .device.commands import device
from .fleet.commands import fleet
from .job.commands import job
from .fota.commands import fota
from .workspace.commands import workspace
from .auth.commands import login, logout


# Account commands
cli.add_command(login)
cli.add_command(logout)

# workspace commands
cli.add_command(workspace)
cli.add_command(device)
cli.add_command(fleet)


# gates commands
# cli.add_command(gate)
# gate.add_command(webhook)
# gate.add_command(exportgate)
# gate.add_command(alarm)

#job
cli.add_command(job)

# fota
cli.add_command(fota)

