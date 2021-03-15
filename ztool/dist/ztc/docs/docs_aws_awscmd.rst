.. _ztc-cmd-aws:

===================
Amazon Web Services
===================

The integration between the Zerynth Toolchain and AWS command line tool allows to easily manage AWS resources while working on your embedded project.

.. note:: The Zerynth Toolchain assumes `AWS command line tool <https://aws.amazon.com/cli>`_ to be available and `configured <http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html>`_ to handle AWS resources.

Since AWS Platform provides several services, this page wil report the documentation of each ztc-aws-integrated command in a proper section depending on referred AWS service:

    * :ref:`AWS IoT Platform <ztc-cmd-aws-iot_platform>`:

        * :ref:`thing-project-from-template <ztc-cmd-aws-thing_project_from_template>`
        * :ref:`add-things <ztc-cmd-aws-add_things>`
        * :ref:`set-active-thing <ztc-cmd-aws-set_active_thing>`
        * :ref:`iot-cleanup <ztc-cmd-aws-iot_cleanup>`
        * :ref:`iot-fota-start <ztc-cmd-aws-iot_fota_start>`

    
.. _ztc-cmd-aws-iot_platform:

****************
AWS IoT Platform
****************

AWS IoT is a managed cloud platform that lets connected devices easily and securely interact with cloud applications and other devices: `AWS IoT platform <https://aws.amazon.com/iot-platform/>`_.
It is officially supported by Zerynth powered devices through a :ref:`specific module <lib.aws.iot>`.

Zerynth Toolchain and AWS IoT Platform integration provides a full device project workflow: from single Thing creation and testing to :ref:`mass programming <ztc-cmd-aws-set_active_thing_note>` utilies for production environment.

    * New project setup is made easy thanks to the available :ref:`aws-iot enabled device project template <ztc-cmd-aws-thing_project_from_template>`.
    * Testing the project on a single device, authenticating as an on-the-fly generated AWS IoT Thing, is immediate with :ref:`add-things <ztc-cmd-aws-add_things>` command.
    * :ref:`Scaling <ztc-cmd-aws-set_active_thing_note>` to multiple devices is allowed by the same :ref:`add-things <ztc-cmd-aws-add_things>` in combination with :ref:`set-active-thing <ztc-cmd-aws-set_active_thing>` command.

Environment cleanup (both local and remote) is also possible through :ref:`iot-cleanup <ztc-cmd-aws-iot_cleanup>` command.

    
.. _ztc-cmd-aws-thing_project_from_template:

Create a generic AWS IoT Thing project from template
----------------------------------------------------

The command: ::

    ztc aws thing-project-from-template project-name path

Creates a Zerynth project called :samp:`project-name` inside a newly created :samp:`project-name` folder placed at provided :samp:`path`.

The Zerynth project will be a clone of a template project capable of connecting to a wifi network and sending mqtt messages to the AWS IoT MQTT Broker, and made of the following files: ::

    ├── main.py
    ├── helpers.py
    ├── readme.md
    └── thing.conf.json

Where :code:`main.py` will contain device task logic, made independent of AWS IoT Thing specific names and references which will be placed inside :code:`thing.conf.json` configuration file.

The command provides also useful options: ::

    --aws-endpoint      endpoint-name
    --aws-policy-name   policy-name

which allow to specify configuration parameters such as mqtt broker endpoint or devices policy, common to different Things, directly at project cloning time.
These options simply set values inside :code:`thing.conf.json` which can also be easily edited manually.

After customizing the code it will be necessary to generate an AWS IoT Thing to allow device authentication to AWS IoT Platform.

    
.. _ztc-cmd-aws-add_things:

Bind AWS IoT Things to a Zerynth Project
----------------------------------------

The command: ::

    ztc aws add-things project_path --things-base-name first_project_thing

will generate an AWS IoT Thing called :code:`first_project_thing_0` and download Thing private key and certificate inside Zerynth project folder placed at :code:`project_path`.
Private key and certificate among with a Thing specific :code:`thing.conf.json` will be stored inside :code:`first_project_thing_0` folder under :code:`.aws_things_resources` one placed at project top-level folder.

The newly created Thing will be set as the :ref:`active <ztc-cmd-aws-set_active_thing>` one and its specific configuration will be placed inside top-level :code:`thing.conf.json` and its key and certificate copied into :code:`private.pem.key` and :code:`certificate.pem.crt` files respectively.

The Project is now ready for :ref:`compilation <ztc-cmd-compile>` and :ref:`uplink <ztc-cmd-uplink>` processes.

After testing the project on a single Thing it will be possible to add multiple things to the same project through: ::

    ztc aws add-things project_path --things-number 10

creating 10 new Things with private keys and certificates with names from :code:`first_project_thing_1` to :code:`first_project_thing_10`. 
Otherwise it will be possible to specify a new base name calling again the proper option: ::

    ztc aws add-things project_path --things-number 10 --things-base-name production_thing

After creation it is needed to choose each time a single Thing for :ref:`compilation <ztc-cmd-compile>` and :ref:`uplink <ztc-cmd-uplink>`.

    
.. _ztc-cmd-aws-set_active_thing:

Set a Thing as active for compilation and uplink
------------------------------------------------

The command: ::

    ztc aws set-active-thing project_path --thing-id 0

will set :code:`thing_base_name_0` as active Thing (:code:`first_project_thing_0` following the example above) for the Zerynth project placed at :code:`project_path`.
The process consists in:

    * copying Thing private key and certificate to top-level project folder;
    * filling Thing specific fields inside :code:`thing.conf.json` configuration file:

        * certificate `Amazon Resource Name (ARN) <http://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html>`_, 
        * Thing name,
        * MQTT ID to log to AWS IoT MQTT Broker (same as Thing name).

.. _ztc-cmd-aws-set_active_thing_note:

A note on mass programming
--------------------------

The simple script ::

    #!/usr/bin/sh

    things_number=1000
    ztc=/ztc_path/ztc

    $ztc aws add-things project_path --things-number $things_number --thing-base-name production_thing
    for thing_id in $(seq 0 $(expr $things_number - 1)); do
        $ztc aws set-active-thing project_path --thing-id $thing_id 
        $ztc compile project_path target_device
        $ztc uplink target_device project_path/main.vbo
    done


allows to scale a single Thing project to an arbitrary number of Things.

    
.. _ztc-cmd-aws-iot_cleanup:

Cleanup project deleting bound AWS IoT Things
---------------------------------------------

The command: ::

    ztc aws iot-cleanup project_path

Deletes AWS IoT Things bound to Zerynth project placed at :code:`project_path` and attached keys and certificates.

.. warning:: clean up process acts both **locally** and **remotely**

    
.. _ztc-cmd-aws-iot_fota_start:

Initiate a FOTA update via AWS IoT Jobs
---------------------------------------

The command: ::

    ztc aws iot-fota_start thing-name thing-firmware s3-bucket s3-role

Will perform the following operations:

    * Extract FOTA information from the :samp:`thing-firmware` file (created with the :ref:`link <ztc-cmd-link>` command and :option:`-J` option) 
    * Upload the new firmware to the :samp:`s3-bucket` S3 bucket url (must start with :samp:`s3://`)
    * Create an AWS IoT Job for the specified :samp:`thing-name`.

The AWS IoT endpoint must be able to read from the S3 bucket so an S3 read role named :samp:`s3-read-role` must be assigned to the endpoint. Such role must be used in the creation of the Job and therefore its name must be passed to this command. The Thing will receive a pre-signed https S3 url to download the new firmware; such url will be valid for a duration of one hour. It is possible to increase or decrease the duration validity using the :option:`--duration` followed by the number of seconds the link will remain valid.

    
