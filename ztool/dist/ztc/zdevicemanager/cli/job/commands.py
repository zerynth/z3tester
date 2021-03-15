"""
.. _zdm-cmd-job:


Jobs
====

In the ZDM a job is a function defined in device's firmware that can be called remotely through the ZDM.
There are to operations available in the ZDM for jobs:


List of device commands:

* :ref:`Schedule <zdm-cmd-job-schedule>`
* :ref:`Check a job status <zdm-cmd-job-check>`

    """

import click
from zdevicemanager.base.base import info, pass_zcli, log_table

from ..helper import handle_error


@click.group(help="Manage the jobs")
def job():
    pass


@job.command(help="Schedule a job")
@click.argument('name')
@click.argument('devices', nargs=-1, type=click.STRING)
@click.option('--arg', type=(str, str), multiple=True)
@pass_zcli
@handle_error
def schedule(zcli, name, arg, devices):
    """

.. _zdm-cmd-job-schedule:

Schedule a job
---------------

To call remotely a function defined in the firmware, use the command: ::

    zdm job schedule job uid

where :samp:`job` is the function name and :samp:`uid` is the device uid.

If the function expects parameters to work, use the command option :option:`--arg`

    """

    # args is a tuple of typle (('temp', 'yes'), ('on', True))
    args_dict = {}
    for a in arg:
        arg_name = a[0]
        arg_value = a[1]
        if check_int(a[1]):
            arg_value = int(a[1])
        args_dict[arg_name] = arg_value
    res = zcli.zdm.jobs.schedule(name, args_dict, devices, on_time="")
    info("Job [{}] scheduled correctly.".format(name))


def check_int(s):
    if s[0] in ('-', '+'):
        return s[1:].isdigit()
    return s.isdigit()


@job.command(help="Check a job's status for a single device")
@click.argument('name')
@click.argument('device-id', nargs=1, type=click.STRING)
@pass_zcli
@handle_error
def check(zcli, name, device_id):
    """

.. _zdm-cmd-job-check:

Check a job status
------------------

To check the status of a scheduled job, type the command: ::

    zdm job check job uid

where :samp:`job` is the job name and :samp:`uid` is the device uid to check

    """
    status_exp = zcli.zdm.jobs.status_expected(name, device_id)
    status_cur = zcli.zdm.jobs.status_current(name, device_id)
    schedule_at = status_exp.version if status_exp else "<unknown>"

    if status_exp is None and status_cur is not None:
        # the job has been scheduled (exp is None)  and the device has sent the response (status_cur not None)
        status = "done"
        result = status_cur.value if status_cur is not None else "<no result>"
        result_at = status_cur.version if status_cur is not None else "<no result>"

    elif status_exp is None and status_cur is None:
        # the job has not been scheduled nor a device has not sent a response
        status = "<none>"
        result = "<none>"
        result_at = "<none>"
    elif status_exp is not None and status_cur is not None:
        if status_cur.version > status_exp.version:
            # job has been scheduled and the device has sent a response
            status = "done"
            result = status_cur.value if status_cur is not None else "<no result>"
            result_at = status_cur.version if status_cur is not None else "<no result>"
        else:
            status = "pending"
            result = "<none>"
            result_at = "<none>"
    elif status_exp is not None and status_cur is None:
        # the job has been scheduled bu the device has not sent a response
        status = "pending"
        result = "<none>"
        result_at = "<none>"
    else:
        status = "<unknown>"
        result = "<none>"
        result_at = "<none>"

    log_table([[name, status, schedule_at, result, result_at, ]],
              headers=["Name", "Status", "ScheduleAt", "Result", "ResultAt"])
