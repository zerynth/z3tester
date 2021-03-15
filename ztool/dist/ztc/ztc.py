"""


.. _ztc-synopsis:

Synopsis
========

The ZTC is launched by typing :command:`ztc` in a console. 

.. note:: In Windows and Mac installations, the :envvar:`PATH` environmental variable is automatically updated in such a way that :command:`ztc` is globally available for the user. In Linux installations, due to the many different shells, the :envvar:`PATH` must be set manually to the following path: :file:`<installation-dir>/ztc/linux64`.

:command:`ztc` takes commands and options as arguments::
    
    ztc [g_options] [command] [l_options]

* [g_options] are global options that alter the behaviour of all subcommands
* [command] is a specific command for the available :ref:`list of commands <ztc-cmd-list>`
* [l_options] are options specific to the command and are documented in each command section

Global options
--------------

The following global options are accepted by :command:`ztc`

* :option:`--help` shows the global options and avaialable commands. :option:`--help` can also be used as a local option showing the help relative to the given command.
* :option:`--colors / --no-colors` enables/disables colored output. Default is enabled. :command:`ztc` automatically detect if it is launched in a terminal capable of colored output and disables colors if not supported.
* :option:`--traceback / --no-traceback` enables/disables the full output for exceptions. The ZTC is written in Python and in case of unexpected errors can output the full Python traceback for debugging purposes.
* :option:`--user-agent agent` set the user-agent http header used in REST calls. It is used to monitor the integration of the ZTC in different tools. In general the :samp:`agent` value should be the name of the tool integrating the ZTC. The value :samp:`ztc` and :samp:`ide` are reserved for command line usage of the ZTC or usage through Zerynth Studio, respectively.
* :option:`-J` enables the JSON output for commands. It is generally used by external tools using the ZTC to get easily machine readable output. If the :option:`-J` is not given, the output of commands is more human readable. 
* :option:`--pretty` is used in conjuction with :option:`-J` and produces nicely formatted JSON output.


.. _ztc-cmd-list

Command List
------------

The ZTC contains many different commands and each one may take subcommand as additional parameters. Commands are best listed by grouping them by functionality as follows.

* :ref:`Account related commands <ztc-cmd-user>`
* :ref:`Project related commands <ztc-cmd-project>`
* :ref:`Device related commands <ztc-cmd-device>`
* :ref:`Virtual Machine related commands <ztc-cmd-vm>`
* :ref:`Compile command <ztc-cmd-compile>`
* :ref:`Uplink command <ztc-cmd-uplink>`
* :ref:`Package related commands <ztc-cmd-package>`
* :ref:`Namespace related commands <ztc-cmd-namespace>`
* :ref:`Other commands <ztc-cmd-misc>`


Output conventions
------------------

All commands can produce tagged and untagged messages. Tagged messages are prefixed by :samp:`[type]` where :samp:`type` can be one of:

* :samp:`info`: informative message, printed to :samp:`stdout`
* :samp:`warning`: warning message, printed to :samp:`stderr`
* :samp:`error`: error message, printed to :samp:`stderr`. Signals a non fatal error condition without stopping the execution
* :samp:`fatal`: error message, printed to :samp:`stderr`. Signals a fatal error condition stopping the execution and setting an error return value. It can optionally be followed by a Python traceback in case of unexpected Exception.

Untagged messages are not colored and not prefixed. The result of a command  generally consists of one or more untagged messages. If the :option:`-J` option is given without :option:`--pretty`, almost every command output is a single untagged line.


Directories
-----------

The ZTC is organized on disk in a set of directories stored under :file:`~/zerynth2` for Linux and Mac or under :file:`C:\\Users\\username\\zerynth2` for Windows. The following directory tree is created: ::

    zerynth2
    |
    |--cfg    # configuration files, device database, clone of online package database
    |
    |--sys    # system packages, platform dependent
    |
    |--vms    # virtual machines storage
    |
    \--dist   # all installed ZTC versions
        |
        |--r2.0.0  # ZTC version r2.0.0
        |--r2.0.1  # ZTC version r2.0.1
        |
        .
        .
Every successful ZTC installation or update is kept in a separate directory (:samp:`dist/version`) so that in case of corrupted installation, the previous working ZTC can be used.

    """

import sys
import os
# set sys.path to the directory containing ztc.py (this file) so that modules can be loaded correctly
sys.path = [os.path.dirname(os.path.realpath(__file__))]+sys.path

import click
from base import *
import compiler
import devices
import uplinker
import projects
import packages
import virtualmachines
import user
import linter
import misc
import aws
import jtag
import provisioning

if __name__=="__main__":
    init_all()
    # load tools
    tools.init()
    cli()
