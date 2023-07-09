#!/usr/bin/env python3
#
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <phk@FreeBSD.ORG> wrote this file.  As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return.   Poul-Henning Kamp
# ----------------------------------------------------------------------------

# pylint: disable=line-too-long, missing-module-docstring, missing-class-docstring, missing-function-docstring

# You need pySerial
from argparse import ArgumentParser
from pprint import pprint
import logging
import serial

#######################################################################
# These are the variables I have managed to identify
# Submissions welcome.

kamstrup_603_var = {
    0x003C: "Heat energy E1",
    0x003F: "Cooling energy E3",
    0x0044: "Volume V1",
    0x0056: "Inlet temperature t1",
    0x0057: "Outlet temperature t2",
    0x0059: "Differential temperature t1-t2",
    0x0050: "Actual power",
    0x004A: "Actual flow",
    0x0063: "Info codes",
    0x0171: "Info codes",
    0x03EC: "Operating hour counter",
    0x00AF: "Error hour counter",
    0x0194: "Meter type",
    0x03E9: "Serial number"
}

kamstrup_382_var = {
    0x0001: "Energy in",
    0x0002: "Energy out",
    0x000D: "Energy in hi-res",
    0x000E: "Energy out hi-res",
    0x041E: "Voltage p1",
    0x041F: "Voltage p2",
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
    0x03FF: "Power In",
    0x0438: "Power p1 In",
    0x0439: "Power p2 In",
    0x043A: "Power p3 In",
    0x0400: "Power In",
    0x0540: "Power p1 Out",
    0x0541: "Power p2 Out",
    0x0542: "Power p3 Out",
}

kamstrup_681_var = {
    0x0001: "Date",
    0x003C: "Heat",
    0x003D: "x",
    0x003E: "x",
    0x003F: "x",
    0x005F: "x",
    0x0060: "x",
    0x0061: "x",
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
    0x0044: 'Volume register V1', # (m3)
    0x004A: 'Current flow', # (l/h)
    0x00EF: 'Volume', #  (l)
}

kamstrup_MC403_var = {
    0x003C: 'Energy register 1: Heat energy', # (MWh)
    0x0050: 'Current Power', #  (kW)
    0x0056: 'Current flow temperature', # (C)
    0x0057: 'Current return flow temperature', # (C)
    0x0059: 'Current temperature difference', # (K)
    0x004A: 'Current flow', # (l/h)
    0x0044: 'Volume register V1', # (m3)
}

kamstrup_681_var = {
    0x0001: "Date",
    0x003C: "Heat",
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
    0x000D: "Ap",
    0x000E: "Am",
    0x041E: "U1",
    0x0434: "I1",
    0x0438: "P1",
    0x03E9: 'Meter-serialnumber',
}

kamstrup_362J_var = {
    0x0001: "Energy-in-low-res",
    0x0002: "Energy-out-low-res",
    0x000D: "Ap",
    0x000E: "Am",
    0x041E: "U1",
    0x041F: "U2",
    0x0420: "U3",
    0x0434: "I1",
    0x0435: "I2",
    0x0436: "I3",
    0x0438: "P1",
    0x0439: "P2",
    0x043A: "P3",
    0x03E9: 'Meter-serialnumber',
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
        while mask > 0:
            reg<<=1
            if byte & mask:
                reg |= 1
            mask>>=1
            if reg & 0x10000:
                reg &= 0xFFFF
                reg ^= poly
    return reg

#######################################################################
# Byte values which must be escaped before transmission
#
escapes = {
    0x06: True,
    0x0D: True,
    0x1B: True,
    0x40: True,
    0x80: True,
}

#######################################################################
# And here we go....
#
class Kamstrup(object):
    def __init__(self, serial_port = "/dev/cuaU0"):
        self.ser = serial.Serial(port = serial_port, baudrate = 1200, timeout = 1.0)

    def debug(self, message_id, bytes_as_array):
        log_message = f"{message_id}\t"
        for byte in bytes_as_array:
            log_message += f" {byte:02x} "
        logging.info(log_message)

    def debug_msg(self, msg):
        logging.info("Msg\t%s", msg)

    def write(self, bytes_list):
        bytes_as_array = bytearray(bytes_list)
        self.debug("Write", bytes_as_array)
        self.ser.write(bytes_as_array)

    def read(self):
        byte = self.ser.read(1)
        if len(byte) == 0:
            self.debug_msg("Rx Timeout")
            return None
        bytes_as_array = bytearray(byte)[0]
        self.debug("Rd", bytearray((bytes_as_array)))
        return bytes_as_array

    def send(self, prefix, msg):
        bytes_as_array = bytearray(msg)

        bytes_as_array.append(0)
        bytes_as_array.append(0)
        crc = crc_1021(bytes_as_array)
        bytes_as_array[-2] = crc >> 8
        bytes_as_array[-1] = crc & 0xFF

        message_bytes = bytearray()
        message_bytes.append(prefix)
        for byte in bytes_as_array:
            if byte in escapes:
                message_bytes.append(0x1B)
                message_bytes.append(byte ^ 0xFF)
            else:
                message_bytes.append(byte)
        message_bytes.append(0x0D)
        self.write(message_bytes)

    def recv(self):
        bytes_read = bytearray()
        while True:
            byte = self.read()
            if byte is None:
                return None
            if byte == 0x40:
                bytes_read = bytearray()
            bytes_read.append(byte)
            if byte == 0x0D:
                break
        message_bytes = bytearray()
        i = 1
        while i < len(bytes_read) - 1:
            if bytes_read[i] == 0x1B:
                byte = bytes_read[i + 1] ^ 0xFF
                if byte not in escapes:
                    self.debug_msg(f"Missing Escape {byte:02x}")
                message_bytes.append(byte)
                i += 2
            else:
                message_bytes.append(bytes_read[i])
                i += 1
        if crc_1021(message_bytes):
            self.debug_msg("CRC error")
        return message_bytes#[:-2]

    def readvar(self, nbr):
        # I wouldn't be surprised if you can ask for more than
        # one variable at the time, given that the length is
        # encoded in the response.  Havn't tried.
        self.send(0x80, (0x3F, 0x10, 0x01, nbr >> 8, nbr & 0xFF))
        message_bytes = self.recv()
        if message_bytes is None:
            return (None, None)

        if message_bytes[0] != 0x3F or message_bytes[1] != 0x10:
            return (None, None)
        if message_bytes[2] != nbr >> 8 or message_bytes[3] != nbr & 0xFF:
            return (None, None)
        if message_bytes[4] in units:
            unit = units[message_bytes[4]]
        else:
            unit = None
        # Decode the mantissa
        mantissa = 0
        for i in range(0, message_bytes[5]):
            mantissa <<= 8
            mantissa |= message_bytes[i + 7]

        # Decode the exponent
        i = message_bytes[6] & 0x3F
        if message_bytes[6] & 0x40:
            i = -i
        i = pow(10, i)
        if message_bytes[6] & 0x80:
            i = -i
        value = mantissa * i

        if logging.root.level == 0:
            string = ""
            for i in message_bytes[:4]:
                string += f" {i:02x}"
            string += " |"
            for i in message_bytes[4:7]:
                string += f" {i:02x}"
            string += " |"
            for i in message_bytes[7:]:
                string += f" {i:02x}"
            logging.debug(string, "=", value, units[message_bytes[4]])

        return (value, unit)

def main():
    arg_parser = ArgumentParser(description="Retrieve data from Kamstrup devices")#, formatter_class=RawTextHelpFormatter)
    arg_parser.add_argument('-v', action='count', help='Set verbosity, repeat to increase level', dest='verbosity_level', default=0)
    # arg_parser.add_argument('sources', nargs='*', help='Power meters to retrieve', choices=list(e.value for e in Powermeters).append(None))
    args = arg_parser.parse_args()

    # if len(args.sources) == 0:
    #     args.sources = list(e.value for e in Powermeters)

    verbosity_level = args.verbosity_level
    log_levels = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG, 0]
    print(log_levels[verbosity_level if verbosity_level < len(log_levels) else len(log_levels)-1])
    logging.basicConfig(format='%(message)s', level=log_levels[verbosity_level if verbosity_level < len(log_levels) else len(log_levels)-1])

    kamstrup = Kamstrup(serial_port='/dev/ttyUSB2')
    for register, description in kamstrup_603_var.items():
        value, unit = kamstrup.readvar(register)
        print(f"{description:25s} {value} {unit}")



if __name__ == "__main__":
    main()
