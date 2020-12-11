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
import math


#######################################################################
# These are the variables I have managed to identify
# Submissions welcome.

kamstrup_382_var = {

	0x0001: "Energy in",
	0x0002: "Energy out",

	0x000d: "Energy in hi-res",
	0x000e: "Energy out hi-res",

	0x041e: "Voltage p1",
	0x041f: "Voltage p2",
	0x0420: "Voltage p3",

	0x0434: "Current p1",
	0x0435: "Current p2",
	0x0436: "Current p3",

	0x0438: "Power p1",
	0x0439: "Power p2",
	0x043a: "Power p3",

	0x0056: "Current flow temperature",
	0x0057: "Current return flow temperature",
	0x0058: "Current temperature T3",
	0x007A: "Current temperature T4",
	0x0059: "Current temperature difference",
	0x005B: "Pressure in flow",
	0x005C: "Pressure in return flow",
	0x004A: "Current flow in flow",
	0x004B: "Current flow in return flow",
	0x03ff: "Power In",
	0x0438: "Power p1 In",
	0x0439: "Power p2 In",
	0x043a: "Power p3 In",

	0x0400: "Power In",
	0x0540: "Power p1 Out",
	0x0541: "Power p2 Out",
	0x0542: "Power p3 Out",
}

kamstrup_681_var = {
	1:	"Date",
	60:	"Heat",
	61:	"x",
	62:	"x",
	63:	"x",
	95:	"x",
	96:	"x",
	97:	"x",
}

kamstrup_MC601_var = {
	0x003C: "Energy register 1: Heat energy",
	0x0044: "Volume register V1",
	0x0058: "Current temperature T3",
	0x03EC: "Operation hours counter",
}

kamstrup_MC21_var = {
	0x0044: "V1",
	0x00f3: "V1 Reverse",
	0x004a: "Flow",
	0x03ec: "Hours counter",
	0x0063: "Info",
	0x012b: "Meter temperature",
	0x0124: "Water temperature",
}


#######################################################################
# Units, provided by Erik Jensen

units = {
	0: '', 1: 'Wh', 2: 'kWh', 3: 'MWh', 4: 'GWh', 5: 'j', 6: 'kj', 7: 'Mj',
	8: 'Gj', 9: 'Cal', 10: 'kCal', 11: 'Mcal', 12: 'Gcal', 13: 'varh',
	14: 'kvarh', 15: 'Mvarh', 16: 'Gvarh', 17: 'VAh', 18: 'kVAh',
	19: 'MVAh', 20: 'GVAh', 21: 'kW', 22: 'kW', 23: 'MW', 24: 'GW',
	25: 'kvar', 26: 'kvar', 27: 'Mvar', 28: 'Gvar', 29: 'VA', 30: 'kVA',
	31: 'MVA', 32: 'GVA', 33: 'V', 34: 'A', 35: 'kV',36: 'kA', 37: 'C',
	38: 'K', 39: 'l', 40: 'm3', 41: 'l/h', 42: 'm3/h', 43: 'm3xC',
	44: 'ton', 45: 'ton/h', 46: 'h', 47: 'hh:mm:ss', 48: 'yy:mm:dd',
	49: 'yyyy:mm:dd', 50: 'mm:dd', 51: '', 52: 'bar', 53: 'RTC',
	54: 'ASCII', 55: 'm3 x 10', 56: 'ton x 10', 57: 'GJ x 10',
	58: 'minutes', 59: 'Bitfield', 60: 's', 61: 'ms', 62: 'days',
	63: 'RTC-Q', 64: 'Datetime'
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
		    baudrate = 1200,
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
		self.debug("Wr", b)
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
		# Skip first response, which is repetition of initial command,
		# only break on 0x0d if it comes after 0x40
		b = None
		while True:
			d = self.rd()
			if d == None:
				return None
			if d == 0x40:
				b = bytearray()
			if b != None:
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

	def process_response(self, nbr, data):
		# Process response data

		if data[0] != nbr >> 8 or data[1] != nbr & 0xff:
			self.debug_msg("NBR error")
			return (None, None)

		if data[2] in units:
			u = units[data[2]]
		else:
			u = None

		# Decode the mantissa
		x = 0
		for i in range(0,data[3]):
			x <<= 8
			x |= data[i + 5]

		# Decode the exponent
		i = data[4] & 0x3f
		if data[4] & 0x40:
			i = -i
		i = math.pow(10,i)
		if data[4] & 0x80:
			i = -i
		x *= i

		if False:
			# Debug print
			s = ""
			for i in data[:2]:
				s += " %02x" % i
			s += " |"
			for i in data[2:5]:
				s += " %02x" % i
			s += " |"
			for i in data[5:5+data[3]]:
				s += " %02x" % i
			s += " ||"
			for i in data[5+data[3]:]:
				s += " %02x" % i

			print(s, "=", x, units[data[2]])

		return x, u

	def readvar(self, nbr):
		# Read single variable

		self.send(0x80, (0x3f, 0x10, 0x01, nbr >> 8, nbr & 0xff))

		b = self.recv()
		if b == None:
			return (None, None)

		if b[0] != 0x3f or b[1] != 0x10:
			return (None, None)

		x, u = self.process_response(nbr, b[2:])

		return (x, u)

	def readvar_multiple(self, multiple_nbr):
		# Read multiple vars at once

		# Construct request
		req = bytearray()
		req.append(0x3f) #destination address
		req.append(0x10) #CID
		req.append(len(multiple_nbr)) #number of nbrs
		for nbr in multiple_nbr:
			req.append(nbr >> 8)
			req.append(nbr & 0xff)

		self.send(0x80, req)

		# Process response
		b = self.recv()
		if b == None:
			return (None, None)

		# Check destination address and CID
		if b[0] != 0x3f or b[1] != 0x10:
			return (None, None)

		# Decode response data, containing multiple variables
		result = {}
		remaining_data = b[2:]
		counter = 0
		# Continue processing data until all variables processed
		while counter < (len(multiple_nbr)):
			current_nbr = multiple_nbr[counter]
			x, u = self.process_response(current_nbr,remaining_data)
			result[current_nbr] = (x,u)
			# length of current variable response data =
			# nbr (2) + units (1) + length (1) + sigexp (1) (=5)
			# + length of actual value
			len_current_nbr = 5 + remaining_data[3]
			remaining_data = remaining_data[len_current_nbr:]
			counter += 1

		return result

if __name__ == "__main__":

	import time

	foo = kamstrup()

	for i in kamstrup_382_var:
		x,u = foo.readvar(i)
		print("%-25s" % kamstrup_382_var[i], x, u)

	# Multiple var example using multical 21:
	# result = foo.readvar_multiple(kamstrup_MC21_var.keys())
	# for i in result:
	#     x, u = result[i]
	#     print("%-25s" % kamstrup_MC21_var[i], x, u)
