import telnetlib


class Probe():
    def __init__(self,host="localhost",port=4444,read_timeout=0.1):
        self.host = host
        self.port = port
        self.tn = telnetlib.Telnet()
        self.read_timeout = read_timeout
    
    def connect(self,timeout=0):
        self.tn.open(self.host,self.port,timeout or 2)

    def disconnect(self):
        self.tn.close()

    def send(self,command,outfn=None):
        if outfn:
            outfn("Probe Command:",command)
        self.tn.write(command.encode("ascii")+b'\n')

    def read_lines(self,timeout=0):
        lines = []
        while True:
            line = self.tn.read_until(b'\n',timeout=timeout or self.read_timeout)
            # print(line)
            if not line or line==b'\r> ':
                return lines
            if line.startswith(b'\r> '):
                # skip echo
                continue
            if line==b'Open On-Chip Debugger\r\n':
                # skip header
                continue
            lines.append(line.decode("ascii").strip())



