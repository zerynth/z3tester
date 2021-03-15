.. _ztc-cmd-package:

********
Packages
********

The ZTC features a package manager to search and install components of the Zerynth ecosystem.
A package is an archive generated from a tagged git repository and identified by a unique :samp:`fullname`.
There exist several package types, each one targeting a different Zerynth functionality:

* :samp:`core` packages contain core Zerynth components (i.e. the ZTC, the Studio, etc...)
* :samp:`sys` packages contain plaform dependent third party tools used by the ZTC (i.e. gcc, device specific tools, the Python runtime, etc..)
* :samp:`board` packages contain device definitions
* :samp:`vhal` packages contain low level drivers for various microcontroller families
* :samp:`lib` packages contain Zerynth libraries to add new modules to Zerynth programs

A package :samp:`fullname` is composed of three fields uniquely identifying the package:

* type
* namespace
* package name

For example, the package :samp:`lib.broadcom.bmc43362` contains the Python driver for the Broadcom bcm43362 wifi chip. 
Its fullname contains the type (:samp:`lib`), the namespace (:samp:`broadcom`) grouping all packages implementing Broadcom drivers, and the actual package name (:samp:`bcm43362`) specifying which particular driver is implemented.
A package has one or more available versions each one tagged following a modified `semantic versioning <http://semver.org>`_ scheme.

Moreover packages can belong to multiple "repositories" (collections of packages). There are two main public repositories, the :samp:`official` one, containing packages created, published and mantained by the Zerynth team, and the :samp:`community` one, containing packages created by community members.

The ZTC mantains a local databases of installed packages and refers to the online database of packages to check for updates and new packages.

    
.. _ztc-cmd-package-sync:

Available versions
------------------

The available versions of the full Zerynth suite can be retrieved with the command: ::

    ztc package versions

The command overwrites the local copy of available versions. 
Details about patches for each version are also contained in the database.

    
.. _ztc-cmd-package-available:

Available packages
------------------

The list of official packages for a specific version of Zerynth can be retrieved with the command: ::

    ztc package available version

The command returns info on every official Zerynth package.

    
.. _ztc-cmd-package-trigger:

Trigger Update
--------------

As soon as a new major release of Zerynth is available, it can be installed by triggering it with the following command: ::

    ztc package trigger_update

The next time the Zerynth installer is started, it will try to install the new version of Zerynth. 
    
.. _ztc-cmd-package-install:

Install community packages
--------------------------

Community packages can be installed and updated with the following command: ::

    ztc package install fullname version

The package archive will be downloaded and installed from the corresponding Github release tarball.
    
    
.. _ztc-cmd-package-authorize:

Github Authorization
--------------------

A necessary step in order to publish community packages is the generation of a Github authorization token
allowing the ZTC to interact with the user's Github repositories where the packages are stored and mantained.

Retrieve an authorization token with the following command: ::

    ztc package authorize

The Github authorization url for Zerynth will be opened in the system browser asking for the user credentials. Upon correct authorization, the Zerynth backend will display the user access token that must be copied back to the ZTC prompt. From this point on, the Zerynth user account will be associated with the Github account. 

    
.. _ztc-cmd-package-publish:

Publishing a community library
------------------------------

Zerynth projects can be published as library packages and publicly shared on different repositories (default is :samp:`community`). 
The library files need to be stored on a public Github repository owned by the user and the repository must be associated with the Zerynth user account by means
of the :ref:`authorize <ztc-cmd-package-authorize>` command. The authorization is necessary only on first time publishing; from there on, the Zerynth backend will automatically query Github for library updates.

The library updates are managed through `Github releases <https://help.github.com/articles/creating-releases/>`_; when a new version is ready, a Github release is created (manually or via ZTC) with a tag and a description. The release tag will be used as the library version while the release description will be used as library changelog. 




In order to convert a project into a publishable library, a json file with the library info must be created and filled with:

* :samp:`title`: the title of the library (will be shown in Zerynth Studio library manager)
* :samp:`description`: a longer description of the library (will be shown in Zerynth Studio library manager)
* :samp:`keywords`: an array of keywords to make the library easily searchable
* :samp:`version`: the version to assign to the current release of the library. It is suggested to keep using the Zerynth convention (rx.y.z).
* :samp:`release`: the current release description. It can be used as a changelog and it will be shown in Zerynth Studio as the text associated to this specific version of the library.

An example of such file: ::

    {
        "title": "DS1307 Real Time Clock",
        "description": "Foo's DS1307 RTC Driver ... ",
        "keywords": [
            "rtc",
            "maxim",
            "time"
        ],
        "release": "Fixed I2C bugs",
        "version": "r2.0.0"
    }

The library can be published in two ways: manual and automatic. In the manual procedure, the user is responsible for manually updating the Github repository and create the Github release. In this case, it is necessary to publish the library just once providing :samp:`title`,:samp:`description` and :samp:`keywords` in the json file. Each time the user adds a new release, the Zerynth backend will automatically include the new release in the available versions of the library. In the automatic procedure, the user is responsible for the creation of a Github repository to store the library while the management of the repository updates and the release creation is performed by th ZTC. In this case the additional :samp:`version` and :samp:`release` must be given in the json file. It is suggested to store the json file in the Github repository itself to track its changes.



The command: ::

    ztc package publish reponame json_file

will publish the library with the manual procedure. It just informs the Zerynth backend of a new association between :samp:`reponame` and the user account (already associated with a Github account). The user must then create every new Github release to make the library updates available to users.

The command: ::

    ztc package publish reponame json_file --automatic project_dir

will publish the library with the automatic procedure. The following operations are performed: 

    * the Zerynth backend is informed of a new association between :samp:`reponame` and the user account
    * the :samp:`reponame` Github repository is clone to a temp directory
    * the project files in the folder :samp:`project_dir` are copied to the cloned repository
    * a new commit is created
    * the commit is pushed to the Github repository master branch
    * the commit is tagged with the :samp:`version` field of :samp:`json_file`
    * a new Github release is created using the :samp:`release` field of :samp:`json_file` as the descriptive text


The resulting library will be importable as: ::

    from community.github_username.repo_name import ...

where :samp:`github_username` and :samp:`repo_name` are the Github username and Github repository name associated to the library, with minus signs (:samp:`-`) replaced by underscores (:samp:`_`).

For example, if the user :samp:`foo` wants to publish the :samp:`bar` library, the following steps must be taken: 

    * a json file with the required fields is created, :samp:`bar.json`.
    * the library files are stored in the folder :samp:`bar_lib`.
    * the command :samp:`ztc package publish bar --automatic bar_lib` is used to publish the library :samp:`community.foo.bar`  



Library Documentation
^^^^^^^^^^^^^^^^^^^^^

It is suggested to write the library documentation in the README.md file in the root of the repository. Zerynth Studio will redirect users to the Github repository page for doc info.


Library Examples
^^^^^^^^^^^^^^^^

Libraries can bedistributed with a set of examples stored under an :file:`examples` folder in the project. Each example must be contained in its own folder accordinto to the following requirements:

* The example folder name will be converted into the example "title" (shown in the Zerynth Studio example panel) by replacing underscores ("_") with spaces
* The example folder can contain any number of files, but only two are mandatory: :file:`main.py`, the entry point file and :file:`project.md`, a description of the example. Both files will be automatically included in the library documentation.

Moreover, for the examples to be displayed in the Zerynth Studio example panel, a file :file:`order.txt` must be placed in the :file:`examples` folder. It contains information about the example positioning in the example tree: ::

    ; order.txt of the lib.adafruit.neopixel package
    ; comments starts with ";"
    ; inner tree nodes labels start with a number of "#" corresponding to their level
    ; leaves corresponds to the actual example folder name
    #Adafruit
        ##Neopixel
           Neopixel_LED_Strips
           Neopixel_Advanced

    ; this files is translated to:
    ; example root
    ; |
    ; |--- ...
    ; |--- ...
    ; |--- Adafruit
    ; |        |--- ...
    ; |        \--- Neopixel
    ; |                |--- Neopixel LED Strips
    ; |                \--- Neopixel Advanced
    ; |--- ...
    ; |--- ...
    
.. _ztc-cmd-package-installed:

Installed packages
------------------

The list of currently installed official and community packages (of type lib) can be retrieved with: ::

    ztc package installed

    
