.. _ztc-cmd-misc:

Miscellanea
===========

Non specific commands are grouped in this section.


.. _ztc-cmd-linter:

Linter
------

    Not documented yet.

   
Info
----

The :command:`info` command  displays information about the status of the ZTC.

It takes the following options (one at a time):

* :option:`--version` display the current version of the ZTC.
* :option:`--fullversion` display the current version of the ZTC together with current update.
* :option:`--devices` display the list of supported devices currently installed.
* :option:`--tools` display the list of available ZTC tools. A ZTC tool is a third party program used to accomplish a particular task. For example the gcc compiler for various architecture is a ZTC tool.
* :option:`--modules` display the list of installed Zerynth libraries that can be imported in a Zerynth program.
* :option:`--examples` display the list of installed examples gathered from all the installed libraries.
* :option:`--vms target` display the list of virtual machines in the current installation for the specified :samp:`target`
* :option:`--messages` display the list of unread system messages

    
Clean
-----

The :command:`clean` command behave differently based on the following options:

* :option:`--tmp` if given clears the temporary folder.
* :option:`--inst version` can be repeated multiple times and removes a previous installed :samp:`version` of Zerynth
* :option:`--db` if given forgets all devices (clears all devices from database).

    
