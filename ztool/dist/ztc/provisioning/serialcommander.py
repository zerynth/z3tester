# -*- coding: utf-8 -*-
# @Author: Lorenzo
# @Date:   2018-06-06 17:22:52
# @Last Modified by:   Lorenzo
# @Last Modified time: 2018-09-03 16:39:31

from .utils import *
import json

raw_cmds = [
    'WCF', 'EXT', 'LCF', 'LDT', 'GSP', 'RCF', 'GPB', 'CSR', 'GPV', 'GLK', 'GSN', 'SCN', 'STP', 'STC'
]

WRITECFG_CMD    = 0
EXTRA_CMD       = 1
LOCKCFG_CMD     = 2
LOCKDATA_CMD    = 3
GETSPECIAL_CMD  = 4
READCFG_CMD     = 5
GETPUBLIC_CMD   = 6
GETCSR_CMD      = 7
GENPRIVATE_CMD  = 8
GETLOCKED_CMD   = 9
GETSERNUM_CMD   = 10
SCANCRYPTO_CMD  = 11
STOREPUBLIC_CMD = 12
STORECERT_CMD   = 13

ASCII_RESP_CODE = 1
BIN_RESP_CODE   = 2

class SerialCommander:

    def __init__(self, channel, out, error):
        self.cmd_ch = channel
        self.out = out
        self.error = error

    def _exe_cmd(self, cmd_code, args=None):
        retries = 0
        try:
            while True:
                self.cmd_ch.write(raw_cmds[cmd_code] + '\n')
                line = self.cmd_ch.readline()
                if line == 'acceptedcmd\n':
                    break
                if retries > 10:
                    raise Exception
                retries += 1
        except Exception:
            self.error('command not accepted')

        if args is not None:
            # number of args: two bytes, big endian
            self.cmd_ch.write(bytes([(len(args) >> 8), len(args) & 0xff]))

            while True:
                len_confirm = self.cmd_ch.read(1)[0]
                if len_confirm == 0:
                    break
                if len_confirm != (len(args) & 0xff):
                    self.error('wrong args len confirm:', len_confirm)

            chunk_size = 32
            for i in range(len(args)//chunk_size + 1):
                # written in chunks (writing chunks bigger thank 64 fails on some platforms)
                self.cmd_ch.write(args[i*chunk_size:(i+1)*chunk_size])

        resp_msg  = None
        resp_status  = None
        resp_type = self.cmd_ch.read(1)[0]
        if resp_type == ASCII_RESP_CODE:
            resp_msg = ''
            while True:
                line = self.cmd_ch.readline()
                if line.startswith('ok: '):
                    resp_status = line.strip()
                    break
                elif line.startswith('exc'):
                    self.error('error executing command:', raw_cmds[cmd_code])
                resp_msg += line
        elif resp_type == BIN_RESP_CODE:
            resp_len = self.cmd_ch.read(1)[0]
            resp_msg = self.cmd_ch.read(resp_len)
        return resp_status, resp_msg

    def read_config(self):
        status, msg = self._exe_cmd(READCFG_CMD)
        self.out(" Read command sent\n", msg, sep='', end='')
        self.out(status)
        return msg

    def get_public(self, private_slot):
        status, msg = self._exe_cmd(GETPUBLIC_CMD, bytes([private_slot]))
        return msg

    def generate_private(self, private_slot):
        status, msg = self._exe_cmd(GENPRIVATE_CMD, bytes([private_slot]))
        return msg

    def getspecial_cmd(self):
        self.out('Getting Crypto Element Special Zone')
        status, specialzone = self._exe_cmd(GETSPECIAL_CMD)
        return specialzone

    def write_cmd(self, offset, bb):
        self.out('Write cmd:', word_fmt(offset, bb))
        status, msg = self._exe_cmd(WRITECFG_CMD, bytes([offset]) + bb)
        self.out(status)

    def extra_cmd(self, offset, bb):
        self.out('Extra cmd:', offset, bb)
        status, msg = self._exe_cmd(EXTRA_CMD, bytes([offset, bb]))
        self.out(status)

    def lock_config_cmd(self, config_crc):
        self.out('Lock config cmd:', config_crc[0], config_crc[1])
        status, msg = self._exe_cmd(LOCKCFG_CMD, config_crc)
        self.out(status)

    def lock_data_cmd(self):
        self.out('Lock data cmd')
        status, msg = self._exe_cmd(LOCKDATA_CMD)
        self.out(status)

    def get_csr(self, private_slot, subject):
        timeout = self.cmd_ch.get_timeout()
        self.cmd_ch.set_timeout(10)
        status, msg = self._exe_cmd(GETCSR_CMD, bytes([private_slot]) + subject.encode('ascii'))
        self.out('Certificate Request:\n', msg, end='')
        self.out(status)
        self.cmd_ch.set_timeout(timeout)
        return msg

    def get_locked(self):
        status, msg = self._exe_cmd(GETLOCKED_CMD)
        return json.loads(msg)

    def get_serial_number(self):
        status, msg = self._exe_cmd(GETSERNUM_CMD)
        return msg

    def scan_cryptoelement(self):
        timeout = self.cmd_ch.get_timeout()
        self.cmd_ch.set_timeout(40)
        status, msg = self._exe_cmd(SCANCRYPTO_CMD)
        self.cmd_ch.set_timeout(timeout)
        return msg[0], msg[1]

    def store_pubkey(self, slot, pubkey):
        status, msg = self._exe_cmd(STOREPUBLIC_CMD, bytes([slot]) + pubkey)
        return status

    def store_certificate(self, certtype, certificate):
        status, msg = self._exe_cmd(STORECERT_CMD, bytes([certtype]) + certificate)
        return status
