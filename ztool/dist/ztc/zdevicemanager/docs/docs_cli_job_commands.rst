.. _zdm-cmd-job:


Jobs
====

In the ZDM a job is a function defined in your firmware that you can call remotely through the ZDM.
There are to operations available in the ZDM for jobs:


List of device commands:

* :ref:`Schedule <zdm-cmd-job-schedule>`
* :ref:`Check a job status <zdm-cmd-job-check>`

    
.. _zdm-cmd-job-schedule:

Schedule a job
---------------

To call remotely a function defined in your firmware, use the command: ::

    zdm job schedule job uid

where :samp:`job` is the function name and :samp:`uid` is the device uid.

If your function expects parameters to work, you can use the command option :option:`--arg`

    
.. _zdm-cmd-job-check:

Check a job status
------------------

If you want to check the status of a job you scheduled, type the command: ::

    zdm job check job uid

where :samp:`job` is the job name and :samp:`uid` is the device uid you want to check, you will see if your device sent a response to the job.

    
