.. _ztc-cmd-provisioning:

************
Provisioning
************

The Zerynth Toolchain allows to easily provision cryto elements by means of the ``provisioning`` commands group.


    
.. _ztc-cmd-provisioning-uplink_config_firmware:

Uplink Configurator Firmware to the device
------------------------------------------

The command: ::

    ztc provisioning uplink-config-firmware device_alias

Performs a preliminary step for subsequent provisioning commands.
A Configurator firmware is compiled and flashed onto the device, with alias :samp:`alias`, the crypto element to provision is plugged to.
The Configurator makes the device ready to accept serial commands which will be translated into provisioning actions.

The implementation of the Configurator is dependent on target cryptoelement, but not on the device used to provision it.

Available command options are:

* :option:`--cryptofamily family`, to specify the family of the crypto element to provision (at the moment ``ateccx08a`` is the only supported  option). Default :samp:`family` is ``ateccx08a``;
* :option:`--cryptodevice device`, to specify the device, from those available in chosen family, to provision. For ``ateccx08a`` family, devices ``atecc508a`` is supported and can be chosen with a :samp:`device` value of ``5`` which is also the default for ``ateccx08a`` family;
* :option:`--i2caddr address`, to specify the i2c address of the crypto element. Needed only if the crypto element uses an i2c interface. Default :samp:`address` value depends on chosen family: ``0x60`` for ``ateccx08a`` family;
* :option:`--i2cdrv drv`, to specify the device i2c driver the crypto element is plugged to. Needed only if the crypto element uses an i2c interface. :samp:`drv` can be ``I2C0``, ``I2C1``, ... . Default :samp:`drv` value is ``I2C0``.

    
.. _ztc-cmd-provisioning-crypto_scan:

Scan for a Crypto Element Address
---------------------------------

The command: ::

    ztc provisioning crypto-scan device_alias


Available command options are:

* :option:`--output path`, to specify a path to store scanned device address and type. If a folder is given, retrieved info is saved to ``scanned_crypto.json`` file.
    
.. warning:: It is mandatory for the following commands to correctly execute to flash the Configurator firmware first.

.. _ztc-cmd-provisioning-read_config:

Read Crypto Element Configuration
---------------------------------

The command: ::

    ztc provisioning read-config device_alias

Reads and outputs the configuration of the crypto element plugged to device with alias :samp:`alias`.

Available command options are:

* :option:`--output path`, to specify a path to store read configuration in binary format.

    
.. _ztc-cmd-provisioning-get_public:

Retrieve Public Key
-------------------

The command: ::

    ztc provisioning get-public device_alias private_slot

Retrieves the public key derived from private key stored in :samp:`private_slot` key slot of the crypto element plugged to the device with alias :samp:`device_alias`.

Available command options are:

* :option:`--format pubkey_format`, to specify the output format of the public key: ``pem`` or ``hex``. ``pem`` by default;
* :option:`--output path`, to specify a path to store retrieved public key. If a folder is given, the key is saved to ``public.pubkey_format`` file.

    
.. _ztc-cmd-provisioning-write_config:

Write Crypto Element Configuration
----------------------------------

The command: ::

    ztc provisioning write-config device_alias configuration_file

Writes configuration specified in :samp:`configuration_file` file to the crypto element plugged to device with alias :samp:`device_alias`.
Configuration can be a YAML or a binary file.

An example YAML configuration file can be copied to :samp:`configuration_file` path if ``get`` is passed as :samp:`device_alias`: ::

    ztc provisioning write-config get 'my_configuration.yaml'

while valid binary configurations are output by the :ref:`read config <ztc-cmd-provisioning-read_config>` command.

Available command options are:

* :option:`--lock lock_value`, if True locks written configuration;


    
.. _ztc-cmd-provisioning-get_csr:

Get Certificate Signing Request
-------------------------------

The command: ::

    ztc provisioning get-csr device_alias private_slot subject

Retrieves a Certificate Signing Request built on subject :samp:`subject` and signed with private key store in slot :samp:`private_slot` of the crypto element plugged to device with alias :samp:`alias`.
:samp:`subject` is a string containing a comma-separated list of OID types and values (e.g. ``"C=IT,O=ZER,CN=device 1"``).

Available command options are:

* :option:`--output path`, to specify a path to store retrieved CSR. If a folder is given, the CSR is saved to ``atecc.csr`` file.
    
.. _ztc-cmd-provisioning-locked:

Locked
------

The command: ::

    ztc provisioning locked device_alias

Outputs the lock state of the crypto element plugged to device with alias :samp:`alias`.

    
.. _ztc-cmd-provisioning-serial_number:

Serial Number
-------------

The command: ::

    ztc provisioning serial-number device_alias

Outputs the serial number of the crypto element plugged to device with alias :samp:`alias`.

    
.. _ztc-cmd-provisioning-store_public:

Store Public
------------

The command: ::

    ztc provisioning store-public device_alias slot public_key

Stores a public key in slot :samp:`slot` of the crypto element plugged to device with alias :samp:`alias`.
Public key is retrieved from file :samp:`public_key` and is expected to be in pem format.

    
.. _ztc-cmd-provisioning-store_certificate:

Store Certificate
-----------------

The command: ::

    ztc provisioning store-certificate device_alias certificate_type certificate

Stores a compressed certificate to the crypto element plugged to device with alias :samp:`alias`.
Certificate is retrieved from file :samp:`certificate` and is expected to be in pem format.

    
