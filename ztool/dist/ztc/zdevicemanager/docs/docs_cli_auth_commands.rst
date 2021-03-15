.. _zdm-cmd-auth-login:

Login
-----

The :command:`login` command enables the user to retrieve an authentication token. The token is used in most zdm commands to communicate with the Zerynth backend.

The :command:`login` can be issued in interactive and non interactive mode. Interactive mode is started by typing: ::

    zdm login

The zdm opens the default system browser to the login/registration page and waits for user input.

In the login/registration page, the user can login providing a valid email and the corresponding password.
It is also possible (and faster) to login using Google plus or Facebook OAuth services. If the user do not have a Zerynth account it is possible to register
providing a valid email, a nick name and a password. Social login is also available for registration via OAuth.

Once a correct login/registration is performed, the browser will display an authentication token. Such token can be copied and pasted to the zdm prompt.

.. warning:: multiple logins with different methods (manual or social) are allowed provided that the email linked to the social OAuth service is the same as the one used in the manual login.

.. warning:: For manual registrations, email address confirmation is needed. An email will be sent at the provided address with instructions.

    
.. _zdm-cmd-auth-logout:

Logout
------

Delete current session with the following command ::

    zdm logout


.. note:: it will be necessary to login again.

    
