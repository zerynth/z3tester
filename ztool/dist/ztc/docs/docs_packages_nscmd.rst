.. _ztc-cmd-namespace:

**********
Namespaces
**********

Namespaces are attributes of packages used to better organize them. A namespace can be created by a user and packages can be subsequently published under it.
A namespace is owned by a single user that can publish under it. A namespace can be shared with other users to grant them publishing rights.

    
.. _ztc-cmd-namespace-create:

Create
------

The command: ::

    ztc namespace create name

will create the namespace :samp:`name` and associate it with the user. 
There is a limit on the number of namespaces a user can own and the command fails if the limit is reached.


    
.. _ztc-cmd-namespace-share:

Share
-----

This feature is not implemented yet.
    
.. _ztc-cmd-namespace-list:

List
----

The command: ::

    ztc namespace list

retrieves the list of the user namespaces.

    
