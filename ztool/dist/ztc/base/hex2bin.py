from .base import *
from .fs import *
import re


def _data_to_bytes(data):
    buf = bytearray()
    for i in range(0,len(data),2):
        buf.append(int(data[i:i+2],16))
    return buf

def _address(address):
    return (int(address[0:2],16)<<8) | (int(address[2:4],16))

#only for extended linear address
def hex2bin(hexfile,binfile=None,total_size=0):
    rc = re.compile(":([0-9A-Fa-f]{2})([0-9A-Fa-f]{4})([0-9A-Fa-f]{2})([0-9A-Fa-f]*)")
    lines = fs.readfile(hexfile).split("\n")
    fw = bytearray()
    chunks = {}
    base = 0
    for line in lines:
        mth = rc.match(line)
        if not mth: 
            log("skipped:",line)
            continue
        datasize = int(mth.group(1),16)
        address = _address(mth.group(2))
        record = int(mth.group(3),16)
        data = mth.group(4)[0:-2]
        checksum = int(mth.group(4)[-2:],16)
        if record==0:
            #data record
            chunks[base+address]=_data_to_bytes(data)
        elif record==1:
            #end of file
            pass
        elif record==2:
            #extended segment
            fatal("Unsupported!")
        elif record==3:
            #start segment
            fatal("Unsupported!")
        elif record==4:
            #extended linear
            base = (base&0x0000ffff)|(_address(data)<<16)
            log("Switched base to",hex(base))
        elif record==5:
            #start linear
            fatal("Unsupported!")
    last_addr=0
    sz=0
    for addr in sorted(chunks):
        v = chunks[addr]
        a = addr+len(v)
        #log("last",last_addr,addr,a,len(v))
        if addr-last_addr!=0:
            log("padding needed between",hex(last_addr),"and",hex(addr),"of",addr-last_addr,"bytes")
            fw.extend(b'\xff'*(addr-last_addr))
        fw.extend(v)
        sz+=len(v)
        last_addr = a
    log("FW:",len(fw),"SZ:",sz,"PD:",len(fw)-sz)
    if total_size>len(fw):
        fw.extend(b'\xff'*(total_size-len(fw)))

    if binfile:
        fs.write_file(fw,binfile)

