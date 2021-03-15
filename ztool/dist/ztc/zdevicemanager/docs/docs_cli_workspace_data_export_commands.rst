.. _zdm-cmd-exports:


Export
======

Using the ZDM you’re able to download your device’s data in different formats.
You can download devices' data in Json and CSV, with the possibility to filter on fleets and tags, specifying
a start and end time (RFC3339 format).

List of commands:

* :ref:`Create <zdm-cmd-workspace-data-export-create>`
* :ref:`Get an export <zdm-cmd-workspace-data-export-get>`

    
.. _zdm-cmd-workspace-data-export-create:

Export creation
----------------

To create a new export use the command: ::

    zdm workspace data export create name type workspace_id

where :samp:`name` is the name that you want to give to your new export
:samp:`type` is the type ox export (json or csv)
:samp:`workspace_id` is the uid of the workspace you want to receive data from
:samp:`start` is the starting date for data (RFC3339)
:samp:`end` is the ending date for data (RFC3339)

You also have the possibility to add filters on data using the following options:

:option:`--tag` To specify tags to filter data (you can specify more than one)
:option:`--fleet` To specify fleets to filter data (you can specify more than one)

    
.. _zdm-cmd-workspace-data-export-get:

Get export
----------

To get an existing export information use the command: ::

    zdm workspace data export get export_id

where :samp:`export_id` is the uid of the export you want to get

    
