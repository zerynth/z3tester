from base import *
import platform
import re

class MacUsb():
	def __init__(self):
		self.text = ""
		self.devkeys = {
			"idVendor":"vid",
			"idProduct":"pid",
			"USB Serial Number":"sid",
			"USB Product Name":"desc",
			"IODialinDevice":"port",
			"BSD Name":"disk",
			"sessionID":"hid"
		}
		self.re_plane = re.compile(".*\+-o (.*) <class AppleUSBDevice,.*")
		self.re_node = re.compile('.*"(idVendor|idProduct|USB Serial Number|USB Product Name|IODialinDevice|BSD Name)"\s+=\s+(.*)')
		self.nodes = []

	def find_all_serial_ports(self):
		ports = set()
		matcher = re.compile("/dev/tty\.(.+)")
		devs = fs.files("/dev")
		for dev in devs:
			if matcher.match(dev):
				ports.add(dev)
		return list(ports)

	def find_all_mount_points(self):
		mnt = set()
		skip_mounts = ["/private"]
		e,out,err = proc.run("mount -v")
		if not e:
			lines = out.split("\n")
			for line in lines:
				if line.startswith("/"):
					flds = line.split(" ")
					if len(flds)<4 or any([ flds[2].startswith(s) for s in skip_mounts]) or flds[2]=="/":
						continue
					if flds[1]=="on" and flds[3].startswith("("):
						mnt.add(flds[2])
					else:
						# merge path with spaces -_-
						try:
							p = flds.index("(")
							path = " ".join(flds[2:p])
							mnt.add(path)
						except Exception as e:
							continue

		return list(mnt)

	def find_mount_point(self,disk):
		try:
			code,out,_ = proc.run("/usr/sbin/diskutil info "+disk)
			lines = out.split("\n")
			for line in lines:
				if "Mount Point:" in line:
					return line.replace("Mount Point:","").strip()
			return disk
		except:
			return disk

	def parse_usb_plane(self,text):
		usb_plane = set()
		lines = text.split("\n")
		rgx = self.re_plane
		for line in lines:
			mth = rgx.match(line)
			if mth:
				usb_plane.add(mth.group(1).strip())
		return usb_plane

	def list_usb_plane(self):
		code,text,_ = proc.run("/usr/sbin/ioreg","-p", "IOUSB")
		#if text==self.text:
		#	return None
		self.text = text
		self.usb_plane= self.parse_usb_plane(self.text)
		return self.usb_plane

	def get_node_info(self,usbid):
		code,txt,_ = proc.run("/usr/sbin/ioreg","-n",usbid,"-r","-l","-x")
		lines = txt.split("\n")
		res = self.re_node 
		node = {}
		for line in lines:
			mth = res.match(line)
			if mth:
				key = mth.group(1)
				if key in self.devkeys:
					key = self.devkeys[key]
				else:
					continue
				if key in node:
					continue
				value = mth.group(2).strip('"')
				if key=="pid" or key=="vid":
					value = value[value.find("0x")+2:].upper()
					value = ("0"*(4-len(value)))+value
				elif key=="disk":
					value = self.find_mount_point(value)
				node[key]= value
		if "sid" not in node and "hid" in node:
			node["sid"]=node["hid"]
		if "sid" not in node:
			node["sid"]="no_sid"
		if "port" not in node:
			node["port"]=None
		if "disk" not in node:
			node["disk"]=None
		return node

	def parse(self):
		res = self.list_usb_plane()
		#if not res:
			# no change to usb_plane
			#return self.nodes
		self.nodes = []
		for usbid in self.usb_plane:
			node = self.get_node_info(usbid)
			if "sid" not in node: continue
			self.nodes.append(node)
		return self.nodes



