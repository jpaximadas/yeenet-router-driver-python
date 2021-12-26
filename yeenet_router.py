import serial
from cobs import cobs
from serial.serialposix import Serial
from packet_record import packet_record
import struct
from enum import IntEnum
import math

class BadModulation(Exception):
    pass

class loraBW(IntEnum):
    BW_7800 = 0
    BW_10400 = 1
    BW_15600 = 2
    BW_20800 = 3
    BW_31250 = 4
    BW_41700 = 5
    BW_62500 = 6
    BW_125000 = 7
    BW_250000 = 8
    BW_500000 = 9

    def get_bandwidth(bw):
        if(bw==loraBW.BW_7800):
            return 7800
        if(bw==loraBW.BW_10400):
            return 10400
        if(bw==loraBW.BW_15600):
            return 15600
        if(bw==loraBW.BW_20800):
            return 20800
        if(bw==loraBW.BW_31250):
            return 31250
        if(bw==loraBW.BW_41700):
            return 41700
        if(bw==loraBW.BW_62500):
            return 62500
        if(bw==loraBW.BW_125000):
            return 125000
        if(bw==loraBW.BW_250000):
            return 250000
        if(bw==loraBW.BW_500000):
            return 500000

class lora_modulation():
    def __init__(self,sf : int,bw : loraBW,cr : int,header_enabled : bool,crc_enabled : bool,preamble_length : int,payload_length : int,frequency : int):
        if(sf>=6 or sf<=12):
            sf_byte = int.to_bytes(sf-6,length=1,byteorder='little')
        else:
            raise BadModulation("spreading factor isn't the right value")
        #print("sf byte: " + str(sf_byte.hex()))
        
        if(type(bw)==loraBW):
            bw_byte = int.to_bytes(int(bw),length=1,byteorder='little')
        else:
            raise BadModulation("bandwidth isn't the right type")
        #print("bw byte: " + str(bw_byte.hex()))

        if(cr>=5 or cr<=8):
            cr_byte = int.to_bytes(int(cr-5),length=1,byteorder='little')
        else:
            raise BadModulation("coding rate needs to be 4/X where X is 5,6,7,8")
        #print("cr byte: " + str(cr_byte.hex()))
        
        if(type(header_enabled)==bool):
            header_enabled_byte = bytes.fromhex('00')
            if(header_enabled):
                header_enabled_byte = bytes.fromhex('01')
        else:
            raise BadModulation("coding rate needs to be boolean")
        #print("header_enabled byte: " + str(header_enabled_byte.hex()))

        if(type(crc_enabled)==bool):
            crc_enabled_byte = bytes.fromhex('00')
            if(crc_enabled):
                crc_enabled_byte = bytes.fromhex('01')
        else:
            raise BadModulation("coding rate needs to be boolean")
        #print("crc_enabled byte: " + str(crc_enabled_byte.hex()))

        if(type(preamble_length) == int and preamble_length>=0 and preamble_length<2**16):
            preamable_bytes = int.to_bytes(preamble_length,length=2,byteorder='little')
        else:
            raise BadModulation("preamable length is nonnegative 2 bytes")
        #print("preamable_length bytes: " + str(preamable_bytes.hex()))

        if(type(payload_length) == int and payload_length>=0 and payload_length<2**8):
            payload_length_byte = int.to_bytes(payload_length,length=1,byteorder='little')
        else:
            raise BadModulation("payload length is 1 byte")
        #print("payload_length byte: " + str(payload_length_byte.hex()))

        if(type(frequency) == int and frequency>=0 and frequency<2**32):
            frequency_bytes = int.to_bytes(frequency,length=4,byteorder='little')
        else:
            raise BadModulation("frequency is 4 bytes")
        #print("frequency bytes: " + str(frequency_bytes.hex()))

        self.command = sf_byte + bw_byte + cr_byte + header_enabled_byte + crc_enabled_byte + preamable_bytes + payload_length_byte + frequency_bytes

class RouterCOBSError(Exception):
    pass

class RouterCommandParseError(Exception):
    pass

class InvalidFrameHeaderError(Exception):
    pass

class InvalidResponseLength(Exception):
    pass

class InputLengthError(Exception):
    pass

class InvalidResponse(Exception):
    pass


default_baudrate = 115200

import socket
class remote_serial:
    def __init__(self,addr,port):

        # create an INET, STREAMing socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # now connect to the web server on port 80 - the normal http port
        self.s.connect((addr,port))

    def close(self):
        self.s.close()

    def exchange(self,command):
        self.s.send(command)
        return self.s.recv(1024)


class yeenet_router:
    def __init__(self,serial_device):
        self.iface = serial_device
        if(type(self.iface)==remote_serial):
            self.is_remote = True
        elif(type(self.iface==Serial)):
            self.is_remote = False
        else:
            raise Exception("need Serial or remote_serial")
        

    ROUTER_BUF_SIZE = 300

    FRAME_DELIMETER = bytes.fromhex('00')
    RDY_FRAME = bytes.fromhex('00')
    COBSERR_FRAME = bytes.fromhex('01')
    PARSEERR_FRAME = bytes.fromhex('02')

    RESET = bytes.fromhex('00')
    ECHO = bytes.fromhex('01')
    BUFFER_POP = bytes.fromhex('02')
    BUFFER_CAP = bytes.fromhex('03')
    MODEM_SETUP = bytes.fromhex('04')
    MODEM_LISTEN = bytes.fromhex('05')
    MODEM_LOAD_PAYLOAD = bytes.fromhex('06')
    MODEM_LOAD_AND_TRANSMIT = bytes.fromhex('07')
    MODEM_TRANSMIT = bytes.fromhex('08')
    MODEM_STANDBY = bytes.fromhex('09')
    MODEM_IS_CLEAR = bytes.fromhex('0A')
    MODEM_GET_LAST_PAYLOAD_RSSI = bytes.fromhex('0B')
    MODEM_GET_LAST_PAYLOAD_SNR = bytes.fromhex('0C')
    MODEM_GET_AIRTIME_USEC = bytes.fromhex('0D')
    MODEM_SET_MODULATION = bytes.fromhex('0E')
    MODEM_GET_LOCAL_ADDRESS = bytes.fromhex('0F')
    BUFFER_GET_N_OVERFLOW = bytes.fromhex('10')
    BUFFER_RESET_N_OVERFLOW = bytes.fromhex('11')

    def close(self):
        #reset router
        self.iface.close()

    def exchange_blocking(self,command: bytes):
        if(self.is_remote):
            decoded = self.iface.exchange(command)
        else:
            encoded = cobs.encode(command) + self.FRAME_DELIMETER
            self.iface.write(encoded)
            incoming = self.iface.read_until(self.FRAME_DELIMETER)
            decoded = cobs.decode(incoming[:-1])


        if(decoded[:1] == self.RDY_FRAME):
            pass 
        elif(decoded[:1] == self.COBSERR_FRAME):
            raise RouterCOBSError(decoded)
        elif(decoded[:1] == self.PARSEERR_FRAME):
            raise RouterCommandParseError(decoded)
        else:
            raise InvalidFrameHeaderError(decoded)

        data_present = len(decoded)>1
        if(data_present):
            return decoded[1:]
        else:
            return

    #takes bytes input
    def echo(self,echo_bytes: bytes) -> bytes:
        command = self.ECHO + echo_bytes
        return self.exchange_blocking(command)

    def reset(self):
        command = self.RESET
        self.exchange_blocking(command)
   
    def buffer_pop(self):
        command = self.BUFFER_POP
        retval = self.exchange_blocking(command)
        if(len(retval)==0):
            raise InvalidResponseLength(retval)
        packets_waiting = int(retval[0])
        if(packets_waiting==0):
            return [0,None]
        if(len(retval)<10):
            raise InvalidResponseLength(retval)
        rssi = int.from_bytes(retval[1:5],byteorder='little',signed=True)
        snr = struct.unpack('f',retval[5:9])[0]
        data = retval[9:]
        return [packets_waiting, packet_record(rssi,snr,data)]

    def buffer_cap(self):
        command = self.BUFFER_CAP
        retval = self.exchange_blocking(command)
        if(len(retval)!=1):
            raise InvalidResponseLength(retval)
        return int(retval[0])

    def modem_setup(self):
        command = self.MODEM_SETUP
        self.exchange_blocking(command)

    def modem_listen(self):
        command = self.MODEM_LISTEN
        self.exchange_blocking(command)

    def modem_load_payload(self, data : bytes):
        command = self.MODEM_LOAD_PAYLOAD
        command = command + data
        retval = self.exchange_blocking(command)
        if(len(retval)!=1):
            raise InvalidResponseLength(retval)
        if(retval[0]==bytes.fromhex('00')):
            return
        if(retval[0]==bytes.fromhex('01')):
            raise InputLengthError("packet data cannot be empty!")
        if(retval[0]==bytes.fromhex('02')):
            raise InputLengthError("packet data is too long!")

    def modem_load_and_transmit(self, data : bytes):
        command = self.MODEM_LOAD_AND_TRANSMIT
        command = command + data
        #print(command)
        retval = self.exchange_blocking(command)
        if(len(retval)!=1):
            raise InvalidResponseLength(retval)
        if(retval[:1]==bytes.fromhex('00')):
            return
        if(retval[:1]==bytes.fromhex('01')):
            raise InputLengthError("packet data cannot be empty!")
        if(retval[:1]==bytes.fromhex('02')):
            raise InputLengthError("packet data is too long!")
        raise InvalidResponse()

    def modem_transmit(self):
        command = self.MODEM_TRANSMIT
        self.exchange_blocking(command)

    def modem_standby(self):
        command = self.MODEM_STANDBY
        self.exchange_blocking(command)

    def modem_is_clear(self):
        command = self.MODEM_IS_CLEAR
        retval = self.exchange_blocking(command)
        if(len(retval)!=1):
            raise InvalidResponseLength(retval)
        if(retval[:1]==bytes.fromhex('00')):
            return False
        if(retval[:1]==bytes.fromhex('01')):
            return True
        raise InvalidResponse()

    def modem_get_last_payload_rssi(self):
        command = self.MODEM_GET_LAST_PAYLOAD_RSSI
        retval = self.exchange_blocking(command)
        if(len(retval != 4)):
            raise InvalidResponseLength(retval)
        return retval

    def modem_get_last_payload_snr(self):
        command = self.MODEM_GET_LAST_PAYLOAD_SNR
        retval = self.exchange_blocking(command)
        if(len(retval != 4)):
            raise InvalidResponseLength(retval)
        return retval

    def modem_get_airtime_usec(self,length : int):
        
        command = self.MODEM_GET_AIRTIME_USEC
        command = command + int.to_bytes(length,length=1,byteorder='little')
        retval = self.exchange_blocking(command)
        if(len(retval)==0):
            raise InvalidResponseLength
        elif(retval[:1] == bytes.fromhex('00')):
            if(len(retval)==5):
                return int.from_bytes(retval[1:],"little")
            else:
                raise InvalidResponseLength(retval)
        elif(retval[:1]==bytes.fromhex('01')):
            raise InputLengthError('length of packet must be a one byte value')
        else:
            raise InvalidResponse()

    def modem_set_modulation(self,modulation : lora_modulation):
        command = self.MODEM_SET_MODULATION + modulation.command
        retval = self.exchange_blocking(command)
        #print("got back:" + str(retval))
        if(len(retval)!=1):
            raise InvalidResponseLength
        if(retval[:1] == bytes.fromhex('00')):
            return
        if(retval[:1] == bytes.fromhex('01')):
            raise BadModulation("modem reports bad command")
        raise InvalidResponse()

    def modem_get_local_address(self):
        command = self.MODEM_GET_LOCAL_ADDRESS
        retval = self.exchange_blocking(command)
        #print("got back:" + str(retval))
        if(len(retval)!=1):
            raise InvalidResponseLength
        return int.from_bytes(retval[0])

    def buffer_get_n_overflow(self):
        command = self.BUFFER_GET_N_OVERFLOW
        retval = self.exchange_blocking(command)
        return int.from_bytes(retval,byteorder='little')

    def buffer_reset_n_overflow(self):
        command = self.BUFFER_RESET_N_OVERFLOW
        self.exchange_blocking(command)
        return
