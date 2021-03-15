"""
Manage the streams of a workspace
"""

import click

from .data.commands import data
from .condition.commands import condition

@click.group(help="Manage the stream")
def stream():
    pass

stream.add_command(data)
stream.add_command(condition)
