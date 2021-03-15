.. _ztc-cmd-project:

********
Projects
********

A Zerynth project consists of a directory containing source code files, documentation files and other assets as needed.
The project directory must also contain a :file:`.zproject` file containing information about the project. :file:`.zproject` creation and management is completely handled by the ZTC.

The following project commands are available: 

* :ref:`create <ztc-cmd-project-create>`
* :ref:`git_init <ztc-cmd-project-git_init>` and related repository management commands
* :ref:`list <ztc-cmd-project-list>` remote projects
* :ref:`make_doc <ztc-cmd-project-make_doc>`

    
.. _ztc-cmd-project-create:

Create a project
----------------

A project can be created by issuing the following command: ::

    ztc project create title path

where :samp:`title` is a string (preferably enclosed in double quotes) representing the title of the project and :samp:`path` is the path to the directory that will hold the project files. If such directory does not exist, it is created. If a project already exists at :samp:`path`, the command fails. 

An empty project consists of three files:

* :file:`main.py`, the empty template for the entry point of the program.
* :file:`readme.md`, a description file initially filled with project title and description in markdown format.
* :file:`.zproject`, a project info file used by the ZTC.


Projects can also be stored remotely on the Zerynth backend as git repositories. In order to do so, during project creation, an attempt is made to create a new project entity on the backend and prepare it to receive git operations. If such attempt fails, the project is still usable locally and can be remotely added later.

The :command:`create` can also accept the following options:

* :option:`--from from` where :samp:`from` is a path. If the option is given, all files and directories stored at :samp:`from` will be recursively copied in the new project directory. If the project directory at :samp:`path` already exists, its contents will be deleted before copying from :samp:`from`.
* :option:`--description desc` where :samp:`desc` is a string (preferably enclosed in double quotes) that will be written in :file:`readme.md`

    
.. _ztc-cmd-project-git_init:

Initialize a Git Repository
---------------------------

Projects can be stored as private remote git repositories on the Zerynth backend. In order to do so it is necessary to initialize a project as a git repository with the command: ::

    ztc project git_init path

where :samp:`path` is the project directory.

If the project is not already registered in the backend, the remote creation is performed first and a bare remote repository is setup. 
Subsequently, if the project directory already contains a git repository, such repository is configured by adding a new remote called :samp:`zerynth`. Otherwise a fresh git repository is initialized.

Zerynth remote repositories require authentication by basic HTTP authentication mechanism. The HTTPS url of the git repository is modified by adding the user token as username and :samp:`x-oath-basic` as password. If the token expires or is invalidated, the :command:`git_init` command can be repeated to update the remote with a fresh token.

    
.. _ztc-cmd-project-git_status:

Check repository status
-----------------------

The command: ::

    ztc project git_status path

Returns information about the current status of the repository at :samp:`path`. In particular the current branch and tag, together with the list of modified files not yet committed. 
It also returns the status of the repository HEAD with respect to the selected remote. The default remote is :samp:`zerynth` and can be changed with the option :option:`--remote`.

    
.. _ztc-cmd-project-git_fetch:

Fetch repository
----------------

The command: ::

    ztc project git_fetch path

is equivalent to the :samp:`git fetch` command executed at :samp:`path'. The default remote is :samp:`zerynth` and can be changed with the option :option:`--remote`.

    
.. _ztc-cmd-project-git_commit:

Commit
------

The command: ::

    ztc project git_commit path -m message

is equivalent to the command sequence :samp:`git add .` and :samp:`git commit -m "message"` executed at :samp:`path`.

    
.. _ztc-cmd-project-git_push:

Push to remote
--------------

The command: ::

    ztc project git_push path --remote remote

is equivalent to the command :samp:`git push origin remote` executed at :samp:`path`.

    
.. _ztc-cmd-project-git_pull:

Pull from remote
----------------

The command: ::

    ztc project git_pull path --remote remote

is equivalent to the command :samp:`git pull` executed at :samp:`path` for remote :samp:`remote`.

    
.. _ztc-cmd-project-git_branch:

Switch/Create branch
--------------------

The command: ::

    ztc project git_branch path branch  --remote remote

behave differently if the :samp:`branch` already exists locally. In this case the command checks out the branch. If :samp:`branch` does not exist, it is created locally and pushed to the :samp:`remote`.

    
.. _ztc-cmd-project-git_clone:

Clone a project
---------------

The command: ::

    ztc project git_clone project path

retrieves a project repository saved to the Zerynth backend and clones it to :samp:`path`. The parameter :samp:`project` is the project uid assigned dring project creation. It can be retrieved with the :ref:`list command <ztc-project-list>`.

    
.. _ztc-cmd-project-git_clone_external:

Clone a project
---------------

The command: ::

    ztc project git_clone project path

retrieves a project repository saved to the Zerynth backend and clones it to :samp:`path`. The parameter :samp:`project` is the project uid assigned dring project creation. It can be retrieved with the :ref:`list command <ztc-project-list>`.

    
.. _ztc-cmd-project-list:

List remote projects
--------------------

The command: ::

    ztc project list

retrieves the list of projects saved to the Zerynth backend. Each project is identified by an :samp:`uid`.
The max number of results is 50, the option :samp:`--from n` can be used to specify the starting index of the list to be retrieved.

    
.. _ztc-cmd-project-make_doc:

Build Documentation
-------------------

A project can be documented in reStructuredText format and the corresponding HTML documentation can be generated by `Sphinx <http://www.sphinx-doc.org/en/1.5/>`_. The process is automated by the following command: ::

    ztc project make_doc path

where :samp:`path` is the path to the project directory.

If the command has never been run before on the project, some documentation accessory files are created. In particular:

* :file:`docs` directory inside the project
* :file:`docs/index.rst`, the main documentation file
* :file:`docs/docs.json`, a configuration file to specify the structure of the documentation. When automatically created, it contains the following fields:

    * :samp:`title`, the title of the documentation
    * :samp:`version`, not used at the moment
    * :samp:`copyright`, not used at the moment
    * :samp:`text`, used for nested json files, see below
    * :samp:`files`, a list of tuples. The second element of the tuple is the file to be scanned for documentation: the first element of the tuple is the title of the corresponding generated documentation. The file types accepted are .py, .rst and .json. File paths are specified relative to the project directory.

All files specified in :file:`docs.json` are processed:

* Python files are scanned for docstrings that are extracted to generate the corresponding .rst file inside :file:`docs`.
* rst files are included in the documentation as is
* json files must have the same structure of :file:`docs/docs.json` and generate a rst file containing the specified title, the field :samp:`text` (if given) as a preamble and a table of contents generated from the contents of the :samp:`files` field.

By default the documentation is generated in a temporary directory, but it can also be generated in a user specified directory by adding the option :option:`--to doc_path` to the command. The option :option:`--open` can be added to fire up the system browser and show the built documentation at the end of the command.

.. note:: a :file:`docs/__toc.rst` file is always generated containing the table of contents for the project documentation. It MUST be included in :file:`docs/index.rst` in order to correctly build the documentation.


    
.. _ztc-cmd-project-config:

Configure
---------

The command: ::

    ztc project config path -D ZERYNTH_SSL 1 -X ZERYNTH_SSL_ECDSA

configures some project variables that turn on and off advanced features for the project at :samp:`path`. In particular the :option:`-D` option adds a new variable with its corresponding value to the project configuration, whereas the :option:`-X` option remove a variable. Both options can be repeated multiple times.

    
