# -*- coding: utf-8 -*-
# @Author: Lorenzo
# @Date:   2017-10-03 09:34:26
# @Last Modified by:   Lorenzo
# @Last Modified time: 2017-10-19 09:57:29

"""
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

    """

from base import *
import base64
import time
import click
from . import awscli
from . import awsthing


@cli.group(help="ztc and AWS cli integration")
def aws():
    pass

def aws_iot():
    """ 
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

    """
    pass

zawsconf_filename = '.zawsconf'
thingsresources_dirname = '.aws_things_resources'

@aws.command("thing-project-from-template",help="create a Zerynth project based on a default AWS IoT project template")
@click.argument("project-name")
@click.argument("path",type=click.Path())
@click.option("--aws-endpoint")
@click.option("--aws-policy-name")
def __thing_template(project_name, path, aws_endpoint, aws_policy_name):
    """
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

    """
    thing_template_path = fs.path(fs.dirname(__file__), 'templates', 'thing_template')
    dst_path = fs.path(path, project_name)
    info("Cloning template")
    fs.copytree(thing_template_path, dst_path)
    pinfo = {
        "title": project_name,
        "created_at":str(datetime.datetime.utcnow()),
        "description":"AWS IoT Thing Template"
    }
    res = zpost(url=env.api.project, data=pinfo)
    rj = res.json()
    if rj["status"] == "success":
        pinfo.update({"uid": rj["data"]["uid"]})
    fs.set_json(pinfo, fs.path(dst_path,".zproject"))

    info("Customizing")
    conf_file = fs.path(dst_path, awsthing.thing_conf_filename)
    thing_conf = fs.get_json(conf_file)
    thing_conf['endpoint'] = aws_endpoint
    thing_conf['policy_name'] = aws_policy_name
    fs.set_json(thing_conf, conf_file)


@aws.command("add-things",help="create n new things bounded to chosen Zerynth Project")
@click.argument("project-path", type=click.Path())
@click.option("--thing-base-name", default='', type=str)
@click.option("--things-number", default=1, type=int)
def __add_things(project_path, thing_base_name, things_number):
    """
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

    """
    _awscli = awscli.AWSCli()
    zawsconf_file = fs.path(project_path, zawsconf_filename)
    zawsconf = {}
    zawsconf['last_thing_id'] = -1
    if fs.isfile(zawsconf_file):
        zawsconf = fs.get_json(zawsconf_file)
        thing_base_name = zawsconf['thing_base_name']

    if thing_base_name == '':
        fatal('--thing-base-name option mandatory for a Zerynth project with no things already bound to it')

    thingsresources_dir = fs.path(project_path, thingsresources_dirname)
    if not fs.exists(thingsresources_dir):
        fs.makedirs(thingsresources_dir)

    if not fs.isdir(thingsresources_dir):
        fatal(thingsresources_dir, 'should be a folder!')

    tconf_file = fs.path(project_path, awsthing.thing_conf_filename)
    if not fs.isfile(tconf_file):
        fatal('thing conf file missing!')
    tconf = fs.get_json(tconf_file)

    for i in range(zawsconf['last_thing_id']+1, zawsconf['last_thing_id']+1 + things_number):
        thingname = thing_base_name + '_' + str(i)
        thing = awsthing.Thing(thingname, _awscli, fs.path(thingsresources_dir, thingname))
        info('Creating thing', thingname)
        thing.create_with_keys_and_certificate()
        thing.set_policy(tconf['policy_name'])
        thing.store()

    zawsconf['thing_base_name'] = thing_base_name
    zawsconf['last_thing_id'] += (things_number)
    fs.set_json(zawsconf, zawsconf_file)

    if not 'active_thing_id' in zawsconf:
        awsthing.Thing.set_active(project_path, thing_base_name, 0)


@aws.command("set-active-thing",help="set active thing for Zerynth project compilation")
@click.argument("project-path", type=click.Path())
@click.option("--thing-id", default=0, type=int)
def __set_active_thing(project_path, thing_id):
    """
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

    """
    zawsconf_file = fs.path(project_path, zawsconf_filename)
    if not fs.isfile(zawsconf_file):
        fatal('cannot set active Thing for a Zerynth project with no things bound to it')

    thingsresources_dir = fs.path(project_path, thingsresources_dirname)
    if not fs.isdir(thingsresources_dir):
        fatal(thingsresources_dir, ' should be a folder!')

    zawsconf = fs.get_json(zawsconf_file)
    thingname = zawsconf['thing_base_name'] + '_' + str(thing_id)
    thing_resources = fs.path(thingsresources_dir, thingname)
    if not fs.isdir(thing_resources):
        fatal(thing_resources, 'should be a folder!')

    awsthing.Thing.set_active(project_path, zawsconf['thing_base_name'], thing_id)
    info(thingname, 'set as active thing')


@aws.command("iot-cleanup",help="destroy things and certificates (both local and remote)")
@click.argument("project-path", type=click.Path())
def __iot_cleanup(project_path):
    """
.. _ztc-cmd-aws-iot_cleanup:

Cleanup project deleting bound AWS IoT Things
---------------------------------------------

The command: ::

    ztc aws iot-cleanup project_path

Deletes AWS IoT Things bound to Zerynth project placed at :code:`project_path` and attached keys and certificates.

.. warning:: clean up process acts both **locally** and **remotely**

    """
    _awscli = awscli.AWSCli()

    thingsresources_dir = fs.path(project_path, thingsresources_dirname)

    for thing_path in fs.glob(thingsresources_dir, '*'):
        thingname = fs.split(thing_path)[-1]
        info('deleting ', thingname)
        thing = awsthing.Thing(thingname, _awscli, fs.path(thingsresources_dir, thingname))
        thing.delete()

    fs.rmtree(thingsresources_dir)
    fs.rm_file(fs.path(project_path, zawsconf_filename))


@aws.command("iot-fota-start",help="send a fota job for a thing")
@click.argument("thing-name", type=str)
@click.argument("thing-firmware", type=click.Path())
@click.argument("s3-bucket", type=str)
@click.argument("s3-role", type=str)
@click.option("--duration",type=int,default=3600)
def __iot_fota_start(thing_name,thing_firmware,s3_bucket,s3_role,duration):
    """
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

    """
    _awscli = awscli.AWSCli()

    fw = fs.get_json(thing_firmware)
    bc_bin = base64.b64decode(fw["bcbin"])
    tmpdir = fs.get_tempdir()
    now = str(int(time.time()))
    fw_file = fs.path(tmpdir,"fota-"+now+"-bc")
    job_file = fs.path(tmpdir,"fota-"+now+"-job")
    http_bucket = s3_bucket.replace("s3://","https://s3.amazonaws.com/")
    job_doc = {
        "operation":"fota",
        "bc_crc":md5(bc_bin),
        "bc_size":len(bc_bin),
        "bc_idx":fw["bc_idx"],
        "bc_url":"${aws:iot:s3-presigned-url:"+http_bucket+"/"+thing_name+"/"+fs.basename(fw_file)+"}"
    }

    fs.set_json(job_doc,job_file)
    log_json(job_doc)
    fs.write_file(bc_bin,fw_file)
    
    if not _awscli.upload_to_s3(tmpdir,s3_bucket+"/"+thing_name):
        fatal("Can't upload to S3!")
    thing = _awscli.describe_thing(thing_name)   
    if thing is None:
        fatal("Can't retrieve thing description!")
    role = _awscli.list_iam_roles(s3_role)
    if not role:
        fatal("Can't find s3 role!")

    thing_arn = thing["thingArn"]
    role_arn = role["Arn"]
    job_source = http_bucket+"/"+thing_name+"/"+fs.basename(job_file)
    rolestr = '"{\\"roleArn\\":\\"'+role_arn+'\\",\\"expiresInSec\\":'+str(duration)+'}"'
    job_name = "fota-"+thing_name+"-"+now
    if not _awscli.create_iot_job(job_name,[thing_arn],job_source,rolestr):
       fatal("Error creating Job!")
    info("Job created:",job_name)

  

