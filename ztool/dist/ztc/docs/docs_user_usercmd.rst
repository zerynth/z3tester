.. _ztc-cmd-user:

************************
Account related commands
************************

The ZTC allows the user to authenticate against the Zerytnh backend and modify profile information.

The following commands are available:

* :ref:`login <ztc-cmd-user-login>` to retrieve an authentication token.
* :ref:`reset <ztc-cmd-user-reset>` reset to request a password reset.
* :ref:`profile <ztc-cmd-user-profile>` set and get profile information.

    
.. _ztc-cmd-user-login:

Login
-----

The :command:`login` command enables the user to retrieve an authentication token. The token is used in most ZTC commands to communicate with the Zerynth backend.

The :command:`login` can be issued in interactive and non interactive mode. Interactive mode is started by typing: ::

    ztc login

The ZTC opens the default system browser to the login/registration page and waits for user input.

In the login/registration page, the user can login providing a valid email and the corresponding password. 
It is also possible (and faster) to login using Google plus or Facebook OAuth services. If the user do not have a Zerynth account it is possible to register
providing a valid email, a nick name and a password. Social login is also available for registration via OAuth.

Once a correct login/registration is performed, the browser will display an authentication token. Such token can be copied and pasted to the ZTC prompt.

.. warning:: multiple logins with different methods (manual or social) are allowed provided that the email linked to the social OAuth service is the same as the one used in the manual login.


Non interactive mode is started by typing: ::

    ztc login --token authentication_token

The :samp:`authentication_token` can be obtained by manually opening the login/registration `page <https://backend.zerynth.com/v1/sso>`_


.. warning:: For manual registrations, email address confirmation is needed. An email will be sent at the provided address with instructions.

    
.. _ztc-cmd-user-reset:

Reset Password
--------------

If a manual registration has been performed, it is possible to change the password by issuing a password reset: ::

    ztc reset email

where :samp:`email` is the email address used in the manual registration flow. An email with instruction will be sent to such address in order to allow a password change.

.. note:: on password change, all active sessions of the user will be invalidated and a new token must be retrieved.

    
.. _ztc-cmd-user-logout:

Logout
------

Delete current session with the following command ::

    ztc logout


.. note:: it will be necessary to login again.

    
.. _ztc-cmd-user-profile:

Get/Set Profile Info
--------------------

By issuing the command: ::

    ztc profile

the user profile is retrieved and displayed. The user profile consists of the following data:

* Generic Info

    * Username (non mutable)
    * Email (non mutable)
    * Name
    * Surname
    * Age
    * Country
    * Job
    * Company
    * Website

# * Subscription Info

#     * Subscription type
#     * Date of subscription expiration
#     * List of roles
#     * List of active repositories

* Asset and Purchase History list 

    * List of account linked assets
    * List of bought virtual machines

The profile  command can be used to change mutable generic info with the following syntax: ::

    ztc profile --set options

where :samp:`options` is a list of one or more of the following options: 

* :option:`--name name` update the Name field
* :option:`--surname name` update the Surname field
* :option:`--age age` update the Age field
* :option:`--country country` update the Country field
* :option:`--job job` update the Job field
* :option:`--company company` update the Company field
* :option:`--website website` update the Website field

    
