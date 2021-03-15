.. _zdm-cmd-device:

*******
Devices
*******

In the ZDM a device is a peripheral that can execute Zerynth bytecode. In order to do so a device must be prepared and customized with certain attributes.
The main attributes of a device are:

* :samp:`uid` a unique id provided by the ZDM with the :ref:`device creation <zdm-cmd-device-create>` command
* :samp:`name` a name given by the user to the device in order to identify it

1. The first step to connect your device to the ZDM, once you are logged, is the device :ref:`creation <zdm-cmd-device-create>`.
2. Then you have to type the :ref:`provision <zdm-cmd-device-provision>` command

There also are commands to :ref:`list your devices <zdm-cmd-device-get-all>`, to :ref:`get a single device info <zdm-cmd-device-get-device>`,
:ref:`update a device <zdm-cmd-device-update>`

List of device commands:

* :ref:`Create <zdm-cmd-device-create>`
* :ref:`Update <zdm-cmd-device-update>`
* :ref:`List devices <zdm-cmd-device-get-all>`
* :ref:`Get a single device <zdm-cmd-device-get-device>`
* :ref:`Create device's credentials <zdm-cmd-device-provision>`

The list of supported devices is available :ref:`here <doc-supported-boards>`

    
.. _zdm-cmd-device-create:

Device creation
---------------

To connect your device to the ZDM you must first create a new device on ZDM, to obtain a new device uid.
The creation command is: ::

    zdm device create name

where :samp:`name` is the name that you want to give to your new device

If you create your device using this command, it will be associated to your default fleet inside your default workspace.
If you want, you can choose to associate the device to another fleet with the optional argument:

:option:`--fleet-id uid`

If you want to associate the device to another fleet, see the :ref:`update command <zdm-cmd-device-update>`
    
.. _zdm-cmd-device-provision:

Device provisioning
-------------------

To create a set of device credentials an existent device uid is needed.

The provisioning command is: ::

    zdm device provision device_id --credentials ctype --endpoint_mode etype --output dest-folder

where :samp:`device_id` is the device uid, :samp:`ctype` is the credentials type (chosen from :samp:`device_token` or :samp:`cloud_token`), :samp:`etype` is the endpoint security mode (choosen from :samp:`secure` or :samp:`insecure`), and :samp:`dest-folder` is the path where to save the credential file (named :samp:`zdevice.json`).

All options are not mandatory and if not given a default value is assigned:

    * :samp:`device_token` for :samp:`ctype`
    * :samp:`secure` for :samp:`etype`
    * current directory for :samp:`dest-folder`


    
.. _zdm-cmd-device-get-all:

List devices
------------

If you want to list all your devices, you can use this command to see a table with a device for each rows
with the device uid, name and the uid of the fleet and workspace containing them.
To see all your devices use the command: ::

    zdm device all

    
.. _zdm-cmd-device-get-device:

Get device
----------

To get a single device information, you can use this command to see the device name and the uid
of the fleet and the workspace that contain the device. ::

    zdm device get uid

where :samp:`uid` is the device uid.

    
.. _zdm-cmd-device-update:

Update a device
---------------

Once you've created a device, you can use this command to update the device name, or to change the fleet uid.
To update a device you just need its uid as argument, then you can use optional arguments to update its name or fleet uid.
Use the command: ::

    zdm device update uid

And the optional arguments are:

* :option:`--fleet-id uid` the uid of the fleet you want to associate the device to
* :option:`--name name` the name you want to give to the device

    
