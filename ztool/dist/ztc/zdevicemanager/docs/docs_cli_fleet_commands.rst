.. _zdm-cmd-fleet:


Fleets
======

In the ZDM a fleet is a set of devices. When you log in for the first time, a 'default' workspace containing a
'default' fleet will be created.
The main attributes of a fleet are:

* :samp:`uid`, a unique id provided by the ZDM after the :ref:`fleet creation <zdm-cmd-fleet-create>` command
* :samp:`name`, a name given by the user to the fleet in order to identify it


List of fleet commands:

* :ref:`Create <zdm-cmd-fleet-create>`
* :ref:`List fleets <zdm-cmd-fleet-get-all>`
* :ref:`Get a single fleet <zdm-cmd-fleet-get-fleet>`

    
.. _zdm-cmd-fleet-create:

Fleet creation
--------------

To create a new fleet of devices inside a workspace use the command: ::

    zdm fleet create name workspace_uid

where :samp:`name` is the name you want to give to your new fleet and :samp:`workspace_id` is the uid of the workspace that will contain the fleet.

    
.. _zdm-cmd-fleet-get-all:

List fleets
------------

If you want to list all your fleets, you can use this command to have information about the associated workspace, and the list of devices inside: ::

    zdm fleet all

    
.. _zdm-cmd-fleet-get-fleet:

Get fleet
---------

To get a single fleet information, you can use this command to see its name, the uid of the workspace that contains it and the list of devices inside::

    zdm fleet get uid

where :samp:`uid` is the fleet uid

    
