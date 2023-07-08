#!/usr/bin/env python3
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
from icecream import ic

import math
import sys

#######################################################################
# These are the variables I have managed to identify
# Submissions welcome.

kamstrup_603_var = {
  60: "Heat energy E1",
  63: "Cooling energy E3",
  68: "Volume V1",
  86: "Inlet temperature t1",
  87: "Outlet temperature t2",
  89: "Differential temperature t1-t2",
  80: "Actual power",
  74: "Actual flow",
  99: "Info codes",
  369: "Info codes",
  1004: "Operating hour counter",
  175: "Error hour counter",
  404: "Meter type",
  1001: "Serial number"
}

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

kamstrup_multical402_var = ({'baudrate':1200},{
	0x003C: "Energy",
	0x0044: "Volume",
	0x004A: "Flow",#"Current flow in flow",
	0x004B: "ReturnFlow",#"Current flow in return flow"
	0x0050: "Power",
	0x0056: "FlowTemp",# "Current flow temperature",
	0x0057: "RetFlowTemp",#"Current return flow temperature",
	0x0058: "T3Temp",#"Current temperature T3",
	0x0059: "DiffTemp",#"Current temperature difference",
	0x005B: "FlowPressure",#"Pressure in flow",
	0x005C: "ReturnFlowPressure",#"Pressure in return flow",
	0x007A: "T4Temp",#"Current temperature T4",
})

kamstrup_MC21_var = {
	0x44: 'Volume register V1', # (m3)
	0x4A: 'Current flow', # (l/h)
	0xEF: 'Volume', #  (l)
}

kamstrup_MC403_var = {
	0x3C: 'Energy register 1: Heat energy', # (MWh)
	0x50: 'Current Power', #  (kW)
	0x56: 'Current flow temperature', # (C)
	0x57: 'Current return flow temperature', # (C)
	0x59: 'Current temperature difference', # (K)
	0x4A: 'Current flow', # (l/h)
	0x44: 'Volume register V1', # (m3)
}

kamstrup_681_var = {
	1:	"Date",
	60:	"Heat",
}

kamstrup_MC601_var = {
        0x003C: "Energy register 1: Heat energy",
        0x0044: "Volume register V1",
        0x0058: "Current temperature T3",
        0x03EC: "Operation hours counter",
}

kamstrup_162J_var = {

    0x0001: "Energy-in-low-res",
    0x0002: "Energy-out-low-res",

    0x000d: "Ap",
    0x000e: "Am",

    0x041e: "U1",

    0x0434: "I1",

    0x0438: "P1",
    0x03e9: 'Meter-serialnumber',
}

kamstrup_362J_var = {

    0x0001: "Energy-in-low-res",
    0x0002: "Energy-out-low-res",

    0x000d: "Ap",
    0x000e: "Am",

    0x041e: "U1",
    0x041f: "U2",
    0x0420: "U3",

    0x0434: "I1",
    0x0435: "I2",
    0x0436: "I3",

    0x0438: "P1",
    0x0439: "P2",
    0x043a: "P3",
    0x03e9: 'Meter-serialnumber',
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
class Kamstrup(object):

  def __init__(self, serial_port = "/dev/cuaU0"):
    #self.debug_fd = open("/tmp/_kamstrup", "a")
    self.debug_fd = sys.stderr
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
      ic(d)
      if d == None:
        return None
      if d == 0x40:
        ic()
        b = bytearray()
      b.append(d)
      if d == 0x0d:
        ic()
        break
    c = bytearray()
    i = 1
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
    ic(c)
    return c#[:-2]

  def readvar(self, nbr):
    # I wouldn't be surprised if you can ask for more than
    # one variable at the time, given that the length is
    # encoded in the response.  Havn't tried.

    self.send(0x80, (0x3f, 0x10, 0x01, nbr >> 8, nbr & 0xff))

    b = self.recv()
    if b == None:
      return (None, None)
    ic(b)

    if b[0] != 0x3f or b[1] != 0x10:
      return (None, None)

    if b[2] != nbr >> 8 or b[3] != nbr & 0xff:
      return (None, None)

    if b[4] in units:
      u = units[b[4]]
    else:
      u = None

    # Decode the mantissa
    x = 0
    for i in range(0,b[5]):
      x <<= 8
      x |= b[i + 7]

    # Decode the exponent
    i = b[6] & 0x3f
    if b[6] & 0x40:
      i = -i
    i = math.pow(10,i)
    if b[6] & 0x80:
      i = -i
    x *= i

    if False:
      # Debug print
      s = ""
      for i in b[:4]:
        s += " %02x" % i
      s += " |"
      for i in b[4:7]:
        s += " %02x" % i
      s += " |"
      for i in b[7:]:
        s += " %02x" % i

      print(s, "=", x, units[b[4]])

    return (x, u)


if __name__ == "__main__":

  import time

  foo = Kamstrup(serial_port='/dev/ttyUSB2')

  for i in kamstrup_603_var:
    x,u = foo.readvar(i)
    print("%-25s" % kamstrup_603_var[i], x, u)
