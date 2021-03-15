.. _zdm-cmd-workspace-conditions:

**********
Conditions
**********

In the ZDM conditions are used in devices to notify some particular situations.
A condition can be opened and then closed.

List of commands:

* :ref:`List conditions <zdm-cmd-workspace-conditions-all>`

    
.. _zdm-cmd-workspace-conditions-all:

List conditions
--------------

To get all the conditions of a device use the command: ::

    zdm workspace condition all workspace_id tag

where :samp:`workspace_id` is the uid of the workspace and `tag` is the tag of the conditions
:samp:`device_id` is the uid of the device
:samp:`threshold` is the min duration of the conditions in seconds

You can also filter condition on status [open, closed], device_id, or duration:

* :option:`--status`
* :option:`--device_id`
* :option:`--threshold`

    
