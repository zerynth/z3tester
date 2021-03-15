.. _ztc-main:

*****************
Zerynth Toolchain
*****************


The Zerynth Toolchain (ZTC) is a command line tool that allows managing all the aspects of the typical Zerynth workflow.

Such workflow extends across different areas of the Zerynth programming experience: 

* Managing :ref:`projects <ztc-cmd-project>`
* Discovering, managing and virtualizing :ref:`devices <ztc-cmd-device>` with :ref:`virtual machines <ztc-cmd-vm>`
* :ref:`Compiling <ztc-cmd-compile>` projects into executable bytecode
* :ref:`Uplinking <ztc-cmd-uplink>` bytecode to virtualized devices
* Adding  :ref:`packages <ztc-cmd-package>` (e.g. libraries, drivers, device classes...) to the current installation
* Turn projects into libraries and :ref:`publish <ztc-cmd-package-publish>` them to the community repository

The workflow is made possible by the Zerynth backend that provides a set of REST API called by the ZTC.
Therefore, most ZTC commands require an authentication token to act on the Zerynth backend on behalf of the user. Such token can be obtained by specific commands.

A typical workflow consists in:

* Creating a project 
* Choosing a target device
* Preparing the device to execute Zerynth code by loading a virtual machine on it, a process called "virtualization"
* Adding Python files (and optionally other files) to the project
* Compiling the project for the target device obtaining executable bytecode
* Uplinking the bytecode to the virtualized device
* Inspecting the output of the device via serial monitor

.. include:: __toc.rst

