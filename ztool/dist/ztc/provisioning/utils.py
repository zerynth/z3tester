# -*- coding: utf-8 -*-
# @Author: Lorenzo
# @Date:   2018-06-06 17:38:00
# @Last Modified by:   Lorenzo
# @Last Modified time: 2018-06-06 17:39:51

def crc16(data):
    crc_polyn = 0x8005
    crc_register = 0

    for byte in data:
        shift_register = 1
        while shift_register <= 128:
            data_bit = 1 if (byte & shift_register) else 0
            crc_bit = crc_register >> 15
            crc_register = (crc_register << 1) & 0xffff # Keep only 16 bit
            if (data_bit ^ crc_bit) != 0:
                crc_register = crc_register ^ crc_polyn
            shift_register <<= 1

    return bytes([crc_register & 0xff, crc_register >> 8])


def word_fmt(index, word):
    return ("%03d: " % index) + ("%02X-"*len(word))[:-1] % tuple(word)