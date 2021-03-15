# -*- coding: utf-8 -*-
# @Author: Lorenzo
# @Date:   2018-06-06 16:08:32
# @Last Modified by:   Lorenzo
# @Last Modified time: 2018-07-10 11:48:45

from .utils import *

config_zone_size = 128
config_zone_bin  = bytearray(config_zone_size)
word_size        = 4

def config_put_special(config_special_zone=None):
    if config_special_zone is None:
        config_special_zone = b'\x01\x23\x52\xaa\x00\x00\x50\x00\xd1\xbb\xf3\x78\xee'
    config_zone_bin[:len(config_special_zone)] = config_special_zone

def dict_to_bin(off_map, dictionary):
    binary = 0
    for elem, off in off_map.items():
        binary |= int(dictionary[elem]) << off
    return binary

def build_chipmode(cd):
    # cd: chipmode_dictionary
    return int(cd['selectorwriteonce']) | int(cd['ttlenable']) << 1 | int(cd['watchdogduration'] == '10s') << 2

def build_slotconfig(scd):
    # scd: slotconfig_dictionary
    scd_map = {
        'writeconfig': 12,
        'writekey': 8,
        'issecret': 7,
        'encryptread': 6,
        'limiteduse': 5,
        'nomac': 4
    }
    binary = dict_to_bin(scd_map, scd)
    if 'privatekeyslotconfig' in scd:
        pksc_map = {
          'extsignenable': 0,
          'intsignenable': 1,
          'ecdhenable': 2,
          'ecdhtonextslot': 3
        }
        binary |= dict_to_bin(pksc_map, scd['privatekeyslotconfig'])
    else:
        binary |= scd['readkey']
    return binary.to_bytes(2, byteorder='little')

def build_keyconfig(kcd):
    # kcd: keyconfig_dictionary
    kcd_map = {
        'private': 0,
        'pubinfo': 1,
        'lockable': 5,
        'reqrandom': 6,
        'reqauth': 7,
        'authkey': 8,
        'intrusiondisable': 12,
        'x509id': 14
    }
    binary = dict_to_bin(kcd_map, kcd)
    if kcd['keytype'] == 'ECC':
        binary |= (0b100 << 2)
    else:
        binary |= (0b111 << 2)
    return binary.to_bytes(2, byteorder='little')

def build_slotinfo(sd):
    # sd: slotinfo_dictionary
    slotconfig = build_slotconfig(sd['slotconfig'])
    keyconfig  = build_keyconfig(sd['keyconfig'])
    return [slotconfig, keyconfig]

def custom_offset_slotinfo(base_offset, info, _):
    return (base_offset[0] + info['num']*2, base_offset[1] + info['num']*2)


def build_x509format(xd):
    # xd: x509format_dictionary
    return xd['templatelength'] << 4 | xd['publicposition']

def custom_offset_x509format(base_offset, _, i):
    return base_offset + i

fields_map = {
    'i2cenable': 14,
    'i2caddress': 16,
    'otpmode': 18,
    'chipmode': 19,
    'slotinfo': (20,96), # base addr for SlotConfig and KeyConfig
    'counter0': (52, (8, 'big')),
    'counter1': (60, (8, 'big')),
    'lastkeyuse0': (68, (8, 'big')),
    'lastkeyuse1': (76, (8, 'big')),
    'userextra': 84,
    'selector': 85,
    'lockvalue': 86,
    'lockconfig': 87,
    'slotlocked': (88, (2, 'little')),
    'x509format': 92
}

def parse_cmd(cmd, value, stacked=None):
    if type(value) == list:
        for i, _value in enumerate(value):
            parse_cmd(cmd, _value, stacked=i)

    elif cmd.startswith('reserved'):
        offset = int(cmd[len('reserved'):])
        toconfig(offset, value)
    elif cmd in fields_map:
        if type(value) == dict:
            offset = fields_map[cmd]
            try:
                offset = globals()['custom_offset_'+cmd](offset, value, stacked)
            except KeyError:
                pass
            toconfig(offset, globals()['build_'+cmd](value))
        else:
            if value <= 0xff:
                toconfig(fields_map[cmd], value)
            else:
                # counterX, lastkeyuseX and slotlocked
                offset = fields_map[cmd][0]
                tb_info = fields_map[cmd][1] # tobytes_info
                toconfig(offset, value.to_bytes(tb_info[0], byteorder=tb_info[1]))


def toconfig(offset, binary):
    if type(offset) == tuple:
        for i in range(len(offset)):
            toconfig(offset[i], binary[i])
        return

    if type(binary) == bytearray or type(binary) == bytes:
        config_zone_bin[offset:offset+len(binary)] = binary
    else:
        config_zone_bin[offset] = binary

def print_desired_config():
    des_config = ''
    for i in range((config_zone_size)//word_size):
        des_config += word_fmt(i*word_size, config_zone_bin[i*word_size:(i+1)*word_size]) + '\n'
    return des_config

