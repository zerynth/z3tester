.. _zdm-cmd-gates-export:


Export gates
============

List of commands:

* :ref:`Create <zdm-cmd-gates-export-create>`
* :ref:`Update export gate <zdm-cmd-gates-export-update>`
* :ref:`List export gates <zdm-cmd-gates-export-get-all>`

    
.. _zdm-cmd-gates-export-create:

Export gate creation
--------------------

To create a new export gate use the command: ::

    zdm gate export create name type frequency workspace_id email

where :samp:`name` is the name that you want to give to your new webhook
:samp:`type` is your export type (json, csv)
:samp:`frequency` is the export frequency [daily, weekly]
:samp:`workspace_id` is the uid of the workspace you want to receive data from
:samp:`email` is the email to receive the link to download the export

You also have the possibility to add filters on data using the following options:

:option:`--tag` To specify a tag to filter data (you can specify more than one)
:option:`--fleet` To specify a fleet to filter data (you can specify more than one)
:option:`--export-name` To specify the export's name
:option: '--day' To specify the day (if frequency is weekly) [0 Sunday... 6 Saturday]
    
.. _zdm-cmd-gates-export-get-all:

List export gates
-----------------

To see a list of your export gates use the command: ::

    zdm gate export all workspace_id

where :samp:`workspace_id` is the uid of the workspace

You also have the possibility to add filters on gates using the following options:

* :option:`--status active|disabled` to filter on gate's status

    
.. _zdm-cmd-gates-export-update

Update export
--------------

To update an export gate use the command: ::

    zdm gate export update gate_id

you can change gate's configuration using the following options: ::
* :option:`--name` to change the gate name
* :option:`--cron` to change the gate period (cron string hour day)
* :option:`--dump_type` to change the dump format (json, csv)
* :option:`--email` to change the notifications email
* :option:`--tag` (multiple option) to replace webhook tag array

    
