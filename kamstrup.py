#!/usr/local/bin/python
#
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <phk@FreeBSD.ORG> wrote this file.  As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return.   Poul-Henning Kamp
# ----------------------------------------------------------------------------
#

from __future__ import print_function

# You need pySerial 

import serial

#######################################################################
# These are the variables I have managed to identify
# Submissions welcome.

kamstrup_382_var = {

	0x0001: "Energy in (kWh)",
	0x0002: "Energy out (kWh)",

	0x000d: "Energy in hi-res (kWh)",
	0x000e: "Energy out hi-res (kWh)",

	0x041e: "Voltage p1 (V)",
	0x041f: "Voltage p2 (V)",
	0x0420: "Voltage p3 (V)",

	0x0434: "Current p1 (A)",
	0x0435: "Current p2 (A)",
	0x0436: "Current p3 (A)",

	0x0438: "Power p1 (kW)",
	0x0439: "Power p2 (kW)",
	0x043a: "Power p3 (kW)",
}


#######################################################################
# Kamstrup uses the "true" CCITT CRC-16
#

def crc_1021(message):
        poly = 0x1021
        reg = 0x0000
        for byte in message:
                mask = 0x80
                while(mask > 0):
                        reg<<=1
                        if byte & mask:
                                reg |= 1
                        mask>>=1
                        if reg & 0x10000:
                                reg &= 0xffff
                                reg ^= poly
        return reg

#######################################################################
# Byte values which must be escaped before transmission
#

escapes = {
	0x06: True,
	0x0d: True,
	0x1b: True,
	0x40: True,
	0x80: True,
}

#######################################################################
# And here we go....
#
class kamstrup(object):

	def __init__(self, serial_port = "/dev/cuaU0"):
		self.debug_fd = open("/tmp/_kamstrup", "a")
		self.debug_fd.write("\n\nStart\n")
		self.debug_id = None

		self.ser = serial.Serial(
		    port = serial_port,
		    baudrate = 9600,
		    timeout = 1.0)

	def debug(self, dir, b):
		for i in b:
			if dir != self.debug_id:
				if self.debug_id != None:
					self.debug_fd.write("\n")
				self.debug_fd.write(dir + "\t")
				self.debug_id = dir
			self.debug_fd.write(" %02x " % i)
		self.debug_fd.flush()

	def debug_msg(self, msg):
		if self.debug_id != None:
			self.debug_fd.write("\n")
		self.debug_id = "Msg"
		self.debug_fd.write("Msg\t" + msg)
		self.debug_fd.flush()

	def wr(self, b):
		b = bytearray(b)
		self.debug("Wr", b);
		self.ser.write(b)

	def rd(self):
		a = self.ser.read(1)
		if len(a) == 0:
			self.debug_msg("Rx Timeout")
			return None
		b = bytearray(a)[0]
		self.debug("Rd", bytearray((b,)));
		return b

	def send(self, pfx, msg):
		b = bytearray(msg)

		b.append(0)
		b.append(0)
		c = crc_1021(b)
		b[-2] = c >> 8
		b[-1] = c & 0xff

		c = bytearray()
		c.append(pfx)
		for i in b:
			if i in escapes:
				c.append(0x1b)
				c.append(i ^ 0xff)
			else:
				c.append(i)
		c.append(0x0d)
		self.wr(c)

	def recv(self):
		b = bytearray()
		while True:
			d = self.rd()
			if d == None:
				return None
			if d == 0x40:
				b = bytearray()
			b.append(d)
			if d == 0x0d:
				break
		c = bytearray()
		i = 1;
		while i < len(b) - 1:
			if b[i] == 0x1b:
				v = b[i + 1] ^ 0xff
				if v not in escapes:
					self.debug_msg(
					    "Missing Escape %02x" % v)
				c.append(v)
				i += 2
			else:
				c.append(b[i])
				i += 1
		if crc_1021(c):
			self.debug_msg("CRC error")
		return c[:-2]

	def readvar(self, nbr):
		self.send(0x80, (0x3f, 0x10, 0x01, nbr >> 8, nbr & 0xff))
		b = self.recv()
		if b == None:
			return b
		if b[0] != 0x3f or b[1] != 0x10:
			return None
		if b[2] != nbr >> 8 or b[3] != nbr & 0xff:
			return None
		x = 0
		for i in b[7:]:
			x <<= 8
			x |= i

		s = ""
		for i in b[:4]:
			s += " %02x" % i
		s += " |"
		for i in b[4:7]:
			s += " %02x" % i
		s += " |"
		for i in b[7:]:
			s += " %02x" % i

		decimals = b[6] & 0x0f
		while decimals > 0:
			x *= .1
			decimals -= 1

		#print(s, "=", x)
		return x
			

if __name__ == "__main__":

	import time

	foo = kamstrup()

	for i in kamstrup_382_var:
		x = foo.readvar(i)
		print("%-25s" % kamstrup_382_var[i], x)
