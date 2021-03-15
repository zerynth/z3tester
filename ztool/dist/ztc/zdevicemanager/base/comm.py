from .base import *
import serial
import threading
import sys
import os
import codecs

__all__ = ["ConnectionInfo","Channel"]

def error_handler(error):
    result = []
    for i in range(error.start, error.end):
        if error.object[i] > 33 and error.object[i] < 126:
            result.append(chr(error.object[i]))
        else:
            result.append('?')
    return ''.join(result), error.end

codecs.register_error("custom_error",error_handler)

class ConnectionInfo():

    PARITY = {
        "n":serial.PARITY_NONE,
        "e": serial.PARITY_EVEN,
        "m": serial.PARITY_MARK,
        "o": serial.PARITY_ODD,
        "s": serial.PARITY_SPACE,
    }

    STOPS = {
        1:serial.STOPBITS_ONE,
        1.5:serial.STOPBITS_ONE_POINT_FIVE,
        2:serial.STOPBITS_TWO
    }

    BITS = {
        5:serial.FIVEBITS,
        6:serial.SIXBITS,
        7:serial.SEVENBITS,
        8:serial.EIGHTBITS
    }

    def __init__(self):
        pass

    def is_serial(self):
        return self.type=="serial"

    def is_socket(self):
        return self.type=="socket"

    def set_serial(self,port,baudrate=115200,bytesize=8,parity="n",stopbits=1,dsrdtr=False, rtscts=False):
        self.type = "serial"
        self.port=port
        self.baudrate = baudrate
        self.bytesize = ConnectionInfo.BITS[bytesize]
        self.parity = ConnectionInfo.PARITY[parity]
        self.stopbits = ConnectionInfo.STOPS[stopbits]
        self.dsrdtr = dsrdtr
        self.rtscts = rtscts

    def set_socket(self,ip,port):
        self.type="socket"
        self.ip = ip
        self.port = port


class ChannelException(Exception):
    def __init__(self,e):
        self.e=e

class Channel():
    def __init__(self,conn,echoing=False):
        self.conn = conn
        self.echoing=echoing

    def open(self,timeout=None):
        try:
            self.timeout = timeout
            if self.conn.is_serial():
                self.ch = serial.Serial(self.conn.port,
                    baudrate=self.conn.baudrate,
                    bytesize=self.conn.bytesize,
                    stopbits=self.conn.stopbits,
                    parity=self.conn.parity,
                    dsrdtr=self.conn.dsrdtr,
                    rtscts=self.conn.rtscts,
                    timeout=self.timeout)
            else:
                pass
                #TODO: implement socket
        except serial.SerialException as se:
            raise ChannelException(se)
        except ValueError as ve:
            raise ChannelException(ve)

    def _reader(self):
        try:
            while True:
                toread = self.ch.inWaiting() or 1
                data = self.ch.read(toread)
                log(data.decode("ascii","custom_error"),sep="",end="")
        except Exception as e:
            # print(e)
            critical("Lost connection!")

    def _writer(self):
        try:
            while True:
                data = sys.stdin.read(1) #TODO: do not block here, try select
                if not data:
                    self.close()
                    return
                self.write(data)
                if self.echoing: log(str(data))
        except Exception as e:
            print(e)


    def run(self):
        self.thguard = threading.Event()
        self.thw = threading.Thread(None,target=self._writer)
        self.thw.start()
        self._reader()


    def get_timeout(self):
        return self.ch.timeout

    def set_timeout(self,timeout):
        self.ch.timeout=timeout

    def write(self,data):
        if isinstance(data,str):
            data = bytes(data,"utf-8")
        self.ch.write(data)

    def read(self,n=1):
        return self.ch.read(n)

    def setDTR(self,val):
        self.ch.setDTR(True if val else False)

    def setRTS(self,val):
        self.ch.setRTS(True if val else False)

    def readline(self):
        return self.ch.readline().decode("ascii","ignore")

    def incoming(self):
        pass

    def flush(self):
        pass

    def close(self):
        return self.ch.close()

