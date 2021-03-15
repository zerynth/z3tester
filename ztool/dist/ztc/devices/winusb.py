from base import *
import re
import win32com.client
import pythoncom
from .wmi import WMI
import serial.tools.list_ports

class WinUsb():
	def __init__(self):
		self.smth = re.compile("USB\\\\(?:[^\\\\]*&)*VID_([0-9a-fA-F]*)&PID_([0-9a-fA-F]*)(?:&[^\\\\]*)*\\\\([^\\\\]*)")
		self.ftdimth = re.compile("FTDIBUS\\\\(?:[^\\\\]*&)*VID_([0-9a-fA-F]*)\+PID_([0-9a-fA-F]*)\+([^\\\\]*).\\\\(?:[^\\\\]*)")
		self.hmth = re.compile('.*="(.*)"')
		self.matchcom = re.compile(".*\((COM[0-9]+)\).*")
		pythoncom.CoInitialize()
		self.wmic = win32com.client.GetObject("winmgmts:")
		self.wmi = WMI()
		self.pnps = {}
		self.devs = []
		self.allusb = []


	def find_sid(self,pnps,ssid):
		for k,s in pnps.items():
			if ssid in s:
				return k
		return None

	def parse(self):
		pnps = self._get_hw_specs()
		if pnps == self.pnps:
			return self.devs
		sersids= set()
		devs=[]
		for x in self.wmi.Win32_SerialPort():
			vid,pid,sid = self._get_win_device_id(x.PNPDeviceID)
			if sid:
				ddisk=None
				if sid not in pnps:
					# it's a composite device, hack a bit
					# split the sid to get the part between '&'
					# check if some pnps set contains ssid
					# if yes, try to find mount point and change sid to parent sid (ksid)
					ssid = self._split_sid(sid)
					ddisk = None
					ksid = self.find_sid(pnps,ssid)
					if ksid:
						ddisk = self._get_drive_letter_from_id(ksid)
						sid=ksid
					else:
						sid = None						
			if sid:
				dev = {					
					"vid":vid,
					"pid":pid,
					"sid":sid,
					"port":x.DeviceID,
					"desc":x.Description,
					"disk":ddisk
				}
				devs.append(dev)
				sersids.add(sid)

		# get every device not already included in the previous search
		usbdevs = self._get_hw(pnps.keys(),sersids)
		for iid,usbdev in usbdevs.items():
			vid,pid,sid = self._get_win_device_id(usbdev.PNPDeviceID)
			if sid:
				dev = {
					"vid":vid,
					"pid":pid,
					"sid":sid if "&" not in sid else "no_sid", # for no sid devices -_-
					"port":None,
					"desc":usbdev.Name,
					"disk":None
				}
				# check if it has a port
				mth = self.matchcom.match(usbdev.Name)
				if mth:
					dev["port"]=mth.group(1)
				else:
					dev["port"]=self._get_com_from_vid_pid(vid,pid)
				ddisk = self._get_drive_letter_from_id(sid)
				if ddisk:
					dev["disk"]=ddisk
				devs.append(dev)
		self.pnps = pnps
		self.devs = devs
		return self.devs
		
	def _get_com_from_vid_pid(self,vid,pid):
		for usb in self.allusb:
			v,p,s = self._get_win_device_id(usb.PNPDeviceID)
			if vid == v and pid == p:
				mth = self.matchcom.match(usb.Name)
				if mth:
					return mth.group(1)
		return None

	# def stop_win(self):
	# 	pythoncom.CoUninitialize()

	def _get_win_device_id(self,pnp):
		mth =self.smth.match(pnp)
		if mth:
			return ( mth.group(1).upper(), mth.group(2).upper(), mth.group(3).upper() )
		mth =self.ftdimth.match(pnp)
		if mth:
			return ( mth.group(1).upper(), mth.group(2).upper(), mth.group(3).upper() )
		return ( None, None, None )

	def _split_sid(self,sid):
		if "&" in sid:
			return sid.split("&")[1]
		return None

	def _get_hw_specs(self):
		pnps = {}
		curpnp = None
		curvid = None
		curpid = None
		for usb in self.wmi.InstancesOf ("Win32_USBControllerDevice"):
			mth = self.hmth.match(usb.Dependent)
			if mth:
				unescaped = bytes(mth.group(1),"utf-8").decode('unicode_escape')
				vid,pid,sid = self._get_win_device_id(unescaped)
				if vid:
					if "&" in sid:
						#not a device spec, get instance id code
						iid = self._split_sid(sid)
						if curpnp and vid==curvid and pid==curpid:
							pnps[curpnp].add(iid)
						else:#if not curpnp:
							# device with no sid -_-
							pnps[sid]=set()
							curpnp=None
					else:
						if curpnp!=sid:
							pnps[sid]=set()
							curpnp=sid
							curvid=vid
							curpid=pid
		return pnps
	
	def _get_hw(self,sids=[],nouids=[]):
		pnps = {}
		curpnp=None
		self.allusb = self.wmi.InstancesOf ("Win32_PNPEntity")
		for usb in self.allusb:
			#unescaped = bytes(usb.PNPDeviceID,"utf-8").decode('unicode_escape')
			vid,pid,sid = self._get_win_device_id(usb.PNPDeviceID)
			if sid in sids and sid not in nouids:
				if sid not in pnps:
					pnps[sid]=usb
				else:
					mth = self.matchcom.match(usb.Name)
					if mth:
						pnps[sid]=usb
		return pnps
		
	def _get_drive_letter_from_id(self,sid):
		for physical_disk in self.wmi.Win32_DiskDrive (InterfaceType="USB"):
			for partition in physical_disk.associators ("Win32_DiskDriveToDiskPartition"):
				for logical_disk in partition.associators ("Win32_LogicalDiskToPartition"):
					if sid in physical_disk.PNPDeviceID:
						return logical_disk.DeviceID
		return ""

	def find_all_serial_ports(self):
		ports = list(serial.tools.list_ports.comports())
		return list([port[0] for port in ports])

	def find_all_mount_points(self):
		mnt = set()
		for physical_disk in self.wmi.Win32_DiskDrive (InterfaceType="USB"):
			for partition in physical_disk.associators ("Win32_DiskDriveToDiskPartition"):
				for logical_disk in partition.associators ("Win32_LogicalDiskToPartition"):
						mnt.add(logical_disk.DeviceID)
		return list(mnt)

