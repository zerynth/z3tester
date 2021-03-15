# -*- coding: utf-8 -*-
# @Author: Lorenzo
# @Date:   2018-06-05 17:31:01
# @Last Modified by:   l.rizzello
# @Last Modified time: 2019-03-22 15:27:32

"""
.. _ztc-cmd-provisioning:

************
Provisioning
************

The Zerynth Toolchain allows to easily provision cryto elements by means of the ``provisioning`` commands group.


    """

from base import *
import click

import base64

from uplinker import uplinker
from compiler import compilercmd

from . import public_converter
from . import config_parser
from .serialcommander import *
from .utils import *

_supported_cryptofamilies = ['ateccx08a']
_family_cryptodevices = {
#   family: ((devices1, device2, ...), default_device)
    'ateccx08a': ((1, 5, 6), 5)
}

def _check_cryptodevicefamily(family, device):
    if device is None:
        return _family_cryptodevices[family][1] # return default family device
    if device not in _family_cryptodevices[family][0]:
        fatal("Unsupported device ", str(device), " for family", family)
    return device

@cli.group(help="Provision secure crypto elements")
def provisioning():
    pass

@provisioning.command("uplink-config-firmware", help="uplink configurator firmware")
@click.argument("alias")
@click.option("--i2caddr",default='0x60')
@click.option("--i2cdrv",default='I2C0')
@click.option("--cryptofamily",default='ateccx08a',type=click.Choice(_supported_cryptofamilies))
@click.option("--cryptodevice",default=None)
def __uplink_config_firmware(alias, i2caddr, i2cdrv, cryptofamily, cryptodevice):
    """
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

    """
    cryptodevice = _check_cryptodevicefamily(cryptofamily, cryptodevice)
    loop = 5
    dev = uplinker.get_device(alias, loop, perform_reset=False)

    configurator_firm = fs.path(fs.dirname(__file__), "firmware", "configurator")
    tmpdir = fs.get_tempdir()

    fs.copytree(configurator_firm, tmpdir)

    if "crypto_provisioning" in dev.to_dict() and dev.to_dict()["crypto_provisioning"] == "lightweight":
        configurator_projectyml_path = fs.path(tmpdir, "project.yml")
        configurator_projectyml = fs.get_yaml(configurator_projectyml_path)
        configurator_projectyml['config']['PROVISIONING_CONFIGURATOR_LIGHT'] = True
        configurator_projectyml['config']['ZERYNTH_HWCRYPTO_ATECCx08A'] = None
        fs.set_yaml(configurator_projectyml, configurator_projectyml_path)

    configurator_conf_path = fs.path(tmpdir, "config.json")
    configurator_conf = fs.get_json(configurator_conf_path)
    configurator_conf["i2caddr"] = int(i2caddr,16) if i2caddr.startswith('0x') else int(i2caddr, 10) 
    configurator_conf["i2cdrv"]  = int(i2cdrv[3:])
    fs.set_json(configurator_conf, configurator_conf_path)

    compilercmd._zcompile(tmpdir, dev.target, False, [], [], False, [], False)

    # reset before uplink
    dev = uplinker.get_device(alias,loop)
    if dev.preferred_uplink_with_jtag:
        # uplink code with jtag
        uplinker._link_uplink_jtag(dev,fs.path(tmpdir, "main.vbo"))
    else:
        uplinker._uplink_dev(dev,fs.path(tmpdir, "main.vbo"), loop)

    fs.del_tempdir(tmpdir)

@provisioning.command("crypto-scan", help="scan for crypto element")
@click.argument("alias")
@click.option("--output", "-o", default='', type=click.Path())
def __crypto_scan(alias, output):
    """
.. _ztc-cmd-provisioning-crypto_scan:

Scan for a Crypto Element Address
---------------------------------

The command: ::

    ztc provisioning crypto-scan device_alias


Available command options are:

* :option:`--output path`, to specify a path to store scanned device address and type. If a folder is given, retrieved info is saved to ``scanned_crypto.json`` file.
    """
    cmd_ch = _serial_channel(alias)
    commander = SerialCommander(cmd_ch, info, fatal)

    address, devtype = commander.scan_cryptoelement()
    info("Cryto element address:", hex(address))
    info("Cryto element type:    ATECC%i08A" % devtype)

    if output:
        scanned_info = {
            'address': address,
            'devtype': ("ATECC%i08A" % devtype)
        }

        if fs.is_dir(output):
            output=fs.path(output,"scanned_crypto.json")
        fs.set_json(scanned_info, output)

    cmd_ch.close()

def _serial_channel(alias):
    loop = 5
    dev = uplinker.get_device(alias,loop,perform_reset=False)
    if not dev.port:
        fatal("Device has no serial port! Check that drivers are installed correctly...")
    conn = ConnectionInfo()
    conn.set_serial(dev.port,**dev.connection)
    ch = Channel(conn)
    try:
        ch.open(timeout=2)
    except:
        fatal("Can't open serial:",dev.port)
    return ch

@provisioning.command("read-config", help="read crypto element configuration")
@click.argument("alias")
@click.option("--output", "-o", default='', type=click.Path())
def __read_config(alias, output):
    """
.. warning:: It is mandatory for the following commands to correctly execute to flash the Configurator firmware first.

.. _ztc-cmd-provisioning-read_config:

Read Crypto Element Configuration
---------------------------------

The command: ::

    ztc provisioning read-config device_alias

Reads and outputs the configuration of the crypto element plugged to device with alias :samp:`alias`.

Available command options are:

* :option:`--output path`, to specify a path to store read configuration in binary format.

    """
    cmd_ch = _serial_channel(alias)
    commander = SerialCommander(cmd_ch, info, fatal)
    config = commander.read_config()

    if output:
        config_bytes = bytearray()
        config = config.split('\n')
        for config_line in config:
            if not config_line:
                continue
            line_bytes = bytes([ int(byte, 16) for byte in config_line.split(' ')[-1].split('-') ])
            config_bytes.extend(line_bytes)

        if fs.is_dir(output):
            output=fs.path(output,"configuration.bin")
        fs.write_file(config_bytes , output)
    cmd_ch.close()

@provisioning.command("get-public", help="retrieve public key associated to private stored in specified slot")
@click.argument("alias")
@click.argument("private_slot")
@click.option("--format", "pub_format", default="pem", type=click.Choice(["pem","hex"]))
@click.option("--output", "-o", default='', type=click.Path())
def __get_public(alias, private_slot, pub_format, output):
    """
.. _ztc-cmd-provisioning-get_public:

Retrieve Public Key
-------------------

The command: ::

    ztc provisioning get-public device_alias private_slot

Retrieves the public key derived from private key stored in :samp:`private_slot` key slot of the crypto element plugged to the device with alias :samp:`device_alias`.

Available command options are:

* :option:`--format pubkey_format`, to specify the output format of the public key: ``pem`` or ``hex``. ``pem`` by default;
* :option:`--output path`, to specify a path to store retrieved public key. If a folder is given, the key is saved to ``public.pubkey_format`` file.

    """
    cmd_ch = _serial_channel(alias)
    commander = SerialCommander(cmd_ch, info, fatal)
    public_key = commander.get_public(int(private_slot))

    if pub_format == "pem":
        formatted_key = public_converter.xytopem(public_key)
        info(" Public key:\n", formatted_key, sep="", end="")
    elif pub_format == "hex":
        formatted_key = public_converter.xytohex(public_key)
        info(" Public key:\n", formatted_key, sep="")

    if output:
        if fs.is_dir(output):
            output=fs.path(output,"public." + pub_format)
        fs.write_file(formatted_key, output)
    cmd_ch.close()

@provisioning.command("gen-private", help="generate private key in chosen slot")
@click.argument("alias")
@click.argument("private_slot")
@click.option("--format", "pub_format", default="pem", type=click.Choice(["pem","hex"]))
def __gen_private(alias, private_slot, pub_format):
    cmd_ch = _serial_channel(alias)
    commander = SerialCommander(cmd_ch, info, fatal)
    public_key = commander.generate_private(int(private_slot))

    if pub_format == "pem":
        formatted_key = public_converter.xytopem(public_key)
        info(" Public key:\n", formatted_key, sep="", end="")
    elif pub_format == "hex":
        formatted_key = public_converter.xytohex(public_key)
        info(" Public key:\n", formatted_key, sep="")

    # if output:
    #     if fs.is_dir(output):
    #         output=fs.path(output,"public." + pub_format)
    #     fs.write_file(formatted_key, output)
    cmd_ch.close()


def _do_lock(commander, config_crc):
    commander.lock_config_cmd(config_crc)
    commander.lock_data_cmd()

def _do_write_config(commander):
    #00:16  write forbidden
    #16:84  simple write command
    #84:86  update extra command
    #86:88  lock command
    #88:128 simple write command

    current_byte = 0
    while True:
        if current_byte < 16:
            config_parser.config_put_special(commander.getspecial_cmd())
            des_config = config_parser.print_desired_config()
            info(' Desired config (special zone retrieved from device)\n', des_config, end='', sep='')
            config_crc = crc16(config_parser.config_zone_bin)
            # crc is returned LSb first
            info('crc16:', '%02X-%02X' % (config_crc[0], config_crc[1]))
            current_byte += 16
        if current_byte < 84 or (current_byte >= 88 and current_byte < 128):
            commander.write_cmd(current_byte, config_parser.config_zone_bin[current_byte:current_byte+config_parser.word_size])
            current_byte += config_parser.word_size
        elif current_byte < 86:
            commander.extra_cmd(current_byte, config_parser.config_zone_bin[current_byte])
            current_byte += 1
        elif current_byte < 88:
            # skip lock zone, should use lock single slot for 88-90 but also simple write works...
            current_byte += 2
        elif current_byte == 128:
            break

    return config_crc

@provisioning.command("write-config", help="write crypto element configuration")
@click.argument("alias")
@click.argument("configuration_file", type=click.Path())
@click.option("--lock", default=False, type=bool)
def __write_config(alias, configuration_file, lock):
    """
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


    """
    if alias == 'get':
        configuration_test = fs.path(fs.dirname(__file__), "conf", "atca-test-config.yaml")
        if fs.is_dir(configuration_file):
            configuration_file = fs.path(configuration_file, "atca-test-config.yaml")
        fs.copyfile(configuration_test, configuration_file)

    else:
        cmd_ch = _serial_channel(alias)
        commander = SerialCommander(cmd_ch, info, fatal)

        if configuration_file.endswith('.bin'):
            config_bytes = fs.readfile(configuration_file,'b')
            config_parser.toconfig(0, config_bytes)
        else:
            desired_config = fs.get_yaml(configuration_file)
            for cmd, value in desired_config.items():
                config_parser.parse_cmd(cmd, value)

        config_crc = _do_write_config(commander)
        if lock:
            _do_lock(commander, config_crc)
        cmd_ch.close()


@provisioning.command("get-csr", help="get a Certificate Signing Request")
@click.argument("alias")
@click.argument("private_slot")
@click.argument("subject")
@click.option("--output", "-o", default='', type=click.Path())
def __get_csr(alias, private_slot, subject, output):
    """
.. _ztc-cmd-provisioning-get_csr:

Get Certificate Signing Request
-------------------------------

The command: ::

    ztc provisioning get-csr device_alias private_slot subject

Retrieves a Certificate Signing Request built on subject :samp:`subject` and signed with private key store in slot :samp:`private_slot` of the crypto element plugged to device with alias :samp:`alias`.
:samp:`subject` is a string containing a comma-separated list of OID types and values (e.g. ``"C=IT,O=ZER,CN=device 1"``).

Available command options are:

* :option:`--output path`, to specify a path to store retrieved CSR. If a folder is given, the CSR is saved to ``atecc.csr`` file.
    """
    cmd_ch = _serial_channel(alias)
    commander = SerialCommander(cmd_ch, info, fatal)
    csr = commander.get_csr(int(private_slot), subject)

    if output:
        if fs.is_dir(output):
            output=fs.path(output,"atecc.csr")
        fs.write_file(csr, output)
    cmd_ch.close()

@provisioning.command("locked", help="check if crypto element is locked")
@click.argument("alias")
def __locked(alias):
    """
.. _ztc-cmd-provisioning-locked:

Locked
------

The command: ::

    ztc provisioning locked device_alias

Outputs the lock state of the crypto element plugged to device with alias :samp:`alias`.

    """
    cmd_ch = _serial_channel(alias)
    commander = SerialCommander(cmd_ch, info, fatal)
    locked = commander.get_locked()

    for key, value in locked.items():
        info(key + ':' + ' '*(8-len(key)), value)

    cmd_ch.close()

@provisioning.command("serial-number", help="retrieve crypto element serial number")
@click.argument("alias")
def __serial_number(alias):
    """
.. _ztc-cmd-provisioning-serial_number:

Serial Number
-------------

The command: ::

    ztc provisioning serial-number device_alias

Outputs the serial number of the crypto element plugged to device with alias :samp:`alias`.

    """
    cmd_ch = _serial_channel(alias)
    commander = SerialCommander(cmd_ch, info, fatal)
    serial_number = commander.get_serial_number()

    formatted_sn = public_converter.xytohex(serial_number)
    info(" Serial number:\n", formatted_sn, sep="")

    cmd_ch.close()


@provisioning.command("store-public", help="store a public key on a crypto element slot")
@click.argument("alias")
@click.argument("slot", type=int)
@click.argument("public_key",type=click.Path())
def __store_public(alias, slot, public_key):
    """
.. _ztc-cmd-provisioning-store_public:

Store Public
------------

The command: ::

    ztc provisioning store-public device_alias slot public_key

Stores a public key in slot :samp:`slot` of the crypto element plugged to device with alias :samp:`alias`.
Public key is retrieved from file :samp:`public_key` and is expected to be in pem format.

    """
    cmd_ch = _serial_channel(alias)
    commander = SerialCommander(cmd_ch, info, fatal)

    xy = public_converter.from_pem(fs.readfile(public_key,'b')).to_string()
    status = commander.store_pubkey(slot, xy)

    info(status)

    cmd_ch.close()


@provisioning.command("store-certificate", help="store a certificate (device or signer)")
@click.argument("alias")
@click.argument("certificate_type", type=click.Choice(["device", "signer"]))
@click.argument("certificate",type=click.Path())
def __store_certificate(alias, certificate_type, certificate):
    """
.. _ztc-cmd-provisioning-store_certificate:

Store Certificate
-----------------

The command: ::

    ztc provisioning store-certificate device_alias certificate_type certificate

Stores a compressed certificate to the crypto element plugged to device with alias :samp:`alias`.
Certificate is retrieved from file :samp:`certificate` and is expected to be in pem format.

    """
    cmd_ch = _serial_channel(alias)
    commander = SerialCommander(cmd_ch, info, fatal)

    certificate_types = {"device": 0, "signer": 1}
    certificate_type = certificate_types[certificate_type]

    pem_certificate = fs.readfile(certificate, 'b')
    pem_certificate = pem_certificate.replace(b'-----BEGIN CERTIFICATE-----\n',b'')
    pem_certificate = pem_certificate.replace(b'-----END CERTIFICATE-----\n',b'')
    pem_certificate = pem_certificate.strip().replace(b'\n',b'')
    der_certificate = base64.b64decode(pem_certificate)

    status = commander.store_certificate(certificate_type, der_certificate)

    info(status)

    cmd_ch.close()
