.. _zdm-cmd-workspace:

Workspaces
==========

A workspace represents a project containing fleets of devices.
The main attributes of a workspace are:

* :samp:`uid` a unique id provided by the ZDM with the :ref:`workspace creation <zdm-cmd-workspace-create>` command
* :samp:`name` a name given by the user to the workspace in order to identify it
* :samp:`description` a string given by the user to describe the project

At your first log in, a 'default' workspace containing a 'default' fleet will be created.


List of workspace commands:

* :ref:`Create <zdm-cmd-workspace-create>`
* :ref:`List workspaces <zdm-cmd-workspace-get-all>`
* :ref:`Get a single workspace <zdm-cmd-workspace-get-workspace>`
* :ref:`Manage data <zdm-cmd-workspace-data>`
* :ref:`List firmwares <zdm-cmd-workspace-firmware>`
* :ref:`Manage conditions <zdm-cmd-workspace-conditions>`


The list of supported devices is available :ref:`here <doc-supported-boards>`

    
.. _zdm-cmd-workspace-get-all:

List workspaces
---------------

To see the list of all your workspaces, use the command: ::

    zdm workspace all

You will see a table containing your workspaces with ID, name, description, fleets and devices

    
.. _zdm-cmd-workspace-get-workspace:

Get workspace
-------------

To get a single workspace information, you can use this command: ::

    zdm workspace get uid

where :samp:`uid` is the workspace uid.

    
.. _zdm-cmd-workspace-create:

Create workspace
------------------

To create a new workspace on the ZDM use the command: ::

    zdm workspace create name

where :samp:`name` is the name that you want to give to your new workspace

You can also insert a description of your workspace adding the option :option:`--description desc`

    
.. _zdm-cmd-workspace-firmware:

List firmwares
--------------

To have a list of the firmwares you uploaded to the ZDM associated to a workspace use the command: ::

    zdm workspace firmwares uid

where :samp:`uid` is the uid of the workspace.

    
