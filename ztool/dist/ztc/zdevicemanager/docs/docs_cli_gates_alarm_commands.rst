.. _zdm-cmd-gates-alarm:


Alarm gates
===========

List of commands:

* :ref:`Create <zdm-cmd-gates-alarm-create>`
* :ref:`Update alarm <zdm-cmd-gates-alarm-update>`
* :ref:`List alarm gates <zdm-cmd-gates-alarm-get-all>`

    
.. _zdm-cmd-gates-alarm-create

Create alarm gate
-----------------

To create a new alarm gate (notifications about opened and closed conditions by devices) use the command: ::
    
    zdm gate alarm create name workspace_id threshold email tag(s)
    
where :samp:`name` is the name of the gate
:samp:`workspace_id` is the uid of the workspace in which you want to monitor condition
:samp:`threshold` is a int representing the minimum duration of a condition to be notified
:samp:`email` is the email where you want to receive notifications
:samp:`tag(s)` is a list of tags to filter on conditions labels

    
.. _zdm-cmd-gates-alarm-update

Update alarm gate
-----------------

To update an alarm gate use the command: ::

    zdm gate alarm update gate_id

you can change gate's configuration using the following options: ::
* :option:`--name` to change the gate's name
* :option:`--tag` (multiple option) to replace gate's tag array
* :option:`--threshold` to change the gate's threshold

    
.. _zdm-cmd-gates-alarm-get-all:

List export gates
-----------------

To see a list of your alarm gates use the command: ::

    zdm gate alarm all workspace_id

where :samp:`workspace_id` is the uid of the workspace

You also have the possibility to add filters on gates using the following options:

* :option:`--status active|disabled` to filter on gate's status

    
