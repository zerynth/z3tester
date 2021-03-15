.. _zdm-cmd-workspace-data:

Data
===============

List of commands:

* :ref:`Get data <zdm-cmd-workspace-data-get>`
* :ref:`List tags <zdm-cmd-workspace-data-tags>`
* :ref:`Export data <zdm-cmd-workspace-data-export>`

    
.. _zdm-cmd-workspace-data-get:

Get data
--------

To get all the data of a workspace associated to a tag use the command: ::

    zdm workspace data all uid tag

where :samp:`uid` is the uid of the workspace, and  :samp:`tag` is the tag of the data to download.

You can also filter result adding the options:

* :option:`--device-id`
* :option:`--start`
* :option:`--end`

    
.. _zdm-cmd-workspace-data-tags:

List tags
---------

When a device publish data to the ZDM it label them with a string called tag. With the following command you can see all the tags
that devices associated to your workspace used as data label. ::

    zdm workspace data tags uid

where :samp:`uid` is the uid of the workspace

    
