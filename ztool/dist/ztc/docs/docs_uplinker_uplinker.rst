.. _ztc-cmd-uplink:

Uplink
======

Once a Zerynth program is compiled to bytecode it can be executed by transferring such bytecode to a running virtual machine on a device.
This operation is called "uplinking" in the ZTC terminology.

Indeed Zerynth virtual machines act as a bootloader waiting a small amount of time after device reset to check if new bytecode is incoming.
If not, they go on executing a previously loaded bytecode or just wait forever.

The command: ::

    ztc uplink alias bytecode

will start the uplinking process for the device with alias :samp:`alias` using the compiled :samp:`.vbo` file given in the :samp:`bytecode` argument. As usual :samp:`alias` ca be partially specified.

The uplinking process may require user interaction for manual resetting the device whan appropriate. The process consists of:

* a discovery phase: the device with the given alias is searched and its attributes are checked
* a probing phase: depending on the device target a manual reset can be asked to the user. It is needed to reset the virtual machine and put it in a receptive state. In this phase a "probe" is sent to the virtual machine, asking for runtime details
* a handshake phase: once runtime details are known, additional info are exchanged between the linker and the virtual machine to ensure correct bytecode transfer
* a relocation phase: the bytecode is not usually executable as is and some symbols must be resolved against runtime details
* a flashing phase: the relocated bytecode is sent to the virtual machine

Each of the previous phases may fail in different ways and the cause can be determined by inspecting error messages.

The :command:`uplink` may the additional :option:`--loop times` option that specifies the number of retries during the discovery phase (each retry lasts one second).



    
.. _ztc-cmd-uplink-raw:

Uplink (raw)
============

It is possible to perform an uplink against a configured device by specifying the relevant device parameters as in the :ref:`register raw <ztc-cmd-device-register-raw>` command, by specifying the :samp:`port` parameter.

The command: ::

    ztc uplink_raw target bytecode --spec port:the_port

performs an uplink on the device of type :samp:`target` using the bytecode file at :samp:`bytecode` using the serial port :samp:`port`.

    
.. _ztc-cmd-uplink-by-probe:

Uplink by probe
===============

It is possible to perform an uplink against a configured device by using a probe. Contrary to other uplink commands that require a bytecode file argument, the :samp:`uplink_by_probe` command requires a linked bytecode file argument (obtained with the :ref:`link <ztc-cmd-link>` command).

The command: ::

    ztc uplink_by_probe target probe linked_bytecode

perform an uplink on the device type :samp:`target` using probe :samp:`probe` to transfer the :samp:`linked_bytecode` file to the running VM.
It is possible to change the address where the bytecode will be flashed by specifying the :option:`--address` option followed by the hexadecimal representation of the address (useful for OTA VMs scenarios)

    
.. _ztc-cmd-link:

Link
====

The command: ::

    ztc link vmuid bytecode

generates a file containing the bytecode :samp:`bytecode` modified in such a way that it can be executed on the VM :samp:`vmuid` without the need for an uplink.

This command is mainly used to generate executable bytecode for FOTA updates. Alternatively it can be used to generate a binary firmware to be manually flashed on a device, skipping both device recognition and uplinking.

It takes the following options:

* :option:`--vm n`, for FOTA enabled VMs, generate a bytecode that can be executed by a VM running on slot :samp:`n`. Default :samp:`n` is zero.
* :option:`--bc n`, for FOTA enabled VMs, generate a bytecode that can be executed by on bytecode slot :samp:`n`. Default :samp:`n` is zero.
* :option:`--include_vm`, generate a single binary containing both the VM and the bytecode, ready to be flashed on the device. Not compatible with FOTA VMs!
* :option:`--otavm`, generate both bytecode and VM ready for a FOTA update
* :option:`--file file`, save the output to file :samp:`file`

FOTA updates
------------

Generating firmware for FOTA updates can be tricky. The following information is needed:

    * The VM unique identifier, :samp:`vmuid`
    * The unique identifier of a new FOTA enabled VM, :samp:`vmuid_new`
    * The current slot the VM is running on, :samp:`vmslot`. Can be retrieved with :ref:`fota library <stdlib.fota>`
    * The current slot the bytecode is running on, :samp:`bcslot`, Can be retrieved with :ref:`fota library <stdlib.fota>`

For example, assuming a project has been compiled to the bytecode file :samp:`project.vbo` and :samp:`vmslot=0` and :samp:`bcslot=0`, the following commands can be given: ::


    # generate bytecode capable of running on slot 1 with VM in slot 0
    # the resulting file can be used for a FOTA update of the bytecode
    ztc link vmuid project.vbo --bc 1 --file project.vbe

    # generate bytecode capable of running on slot 1 with VM in slot 1
    # the resulting file CAN'T be used for a FOTA update because the running VM is in slot 0
    # and project.vbe does not contain the new VM
    ztc link vmuid_new project.vbo --bc 1 --vm 1 --file project.vbe

    # generate bytecode capable of running on slot 1 with VM in slot 1
    # the resulting file can be used for a FOTA update of the bytecode and VM
    # because project.vbe contains the new VM
    ztc link vmuid_new project.vbo --bc 1 --vm 1 --otavm --file project.vbe


.. note:: It is not possible to generate a FOTA update of the VM only!

.. note:: To generate a Zerynth ADM compatible FOTA bytecode update, add option :option:`-J` before the link command. The resulting file will be JSON and not binary.


    
