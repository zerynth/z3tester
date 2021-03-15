"""


.. _zdm-synopsis:

Synopsis
========

The ZDM is launched by typing :command:`zdm` in a terminal.


.. note:: ZDM is in Beta version and is not still possible to call it from any directory. If you want to be able to use it globally, the :envvar:`PATH` must be set manually. In Linux, for example you must update the file at the following path: :file:`<installation-dir>/zdm/linux64`.


Global options
--------------

The following global options are accepted by :command:`zdm`

* :option:`--help` shows the global options and available commands. :option:`--help` can also be used as a local option showing the help relative to the given command.
* :option:`--colors / --no-colors` enables/disables colored output. Default is enabled. :command:`zdm` automatically detect if it is launched in a terminal capable of colored output and disables colors if not supported.
* :option:`--traceback / --no-traceback` enables/disables the full output for exceptions. The ZDM is written in Python and in case of unexpected errors can output the full Python traceback for debugging purposes.
* :option:`--user-agent agent` set the user-agent http header used in REST calls. It is used to monitor the integration of the ZDM in different tools. In general the :samp:`agent` value should be the name of the tool integrating the ZDM. The value :samp:`zdm` and :samp:`ide` are reserved for command line usage of the ZDM or usage through Zerynth Studio, respectively.
* :option:`-J` enables the JSON output for commands. It is generally used by external tools using the ZDM to get easily machine readable output. If the :option:`-J` is not given, the output of commands is more human readable.
* :option:`--pretty` is used in conjuction with :option:`-J` and produces nicely formatted JSON output.


Command List
------------

The ZDM contains many different commands to manage different entities (fleets, devices..). Commands can be divided into groups depending on entity on which they operate.

* :ref:`Login command <zdm-cmd-login>`
* :ref:`Logout command <zdm-cmd-logout>`
* :ref:`Device related commands <zdm-cmd-device>`
* :ref:`Fleet related commands <zzdm-cmd-fleet>`
* :ref:`Fota related commands <zdm-cmd-fota>`
* :ref:`Gate related commands <zdm-cmd-gates>`
* :ref:`Job related commands <zdm-cmd-job>`
* :ref:`Workspace related commands <zdm-cmd-workspace>`


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

The ZDM is organized on disk in a set of directories stored under :file:`~/zerynth2` for Linux and Mac or under :file:`C:\\Users\\username\\zerynth2` for Windows. The following directory tree is created: ::

    zerynth2
    |
    |--cfg    # configuration files, device database, clone of online package database
    |
    |--sys    # system packages, platform dependent
    |
    |--vms    # virtual machines storage
    |
    |--dist   # all installed ZDM versions

Every successful ZDM installation or update is kept in a separate directory (:samp:`dist/version`) so that in case of corrupted installation, the previous working ZDM can be used.

    """

import sys
import os

sys.path = [os.path.dirname(os.path.realpath(__file__))] + sys.path

from zdevicemanager.base import init_all
from zdevicemanager.base.tools import tools
from zdevicemanager.base.base import cli

if __name__ == "__main__":
    init_all()
    # load tools
    tools.init()
    cli()
