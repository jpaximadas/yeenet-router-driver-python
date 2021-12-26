from yeenet_router import yeenet_router
from yeenet_router import loraBW
from yeenet_router import lora_modulation
from yeenet_router import remote_serial
import serial
import sys
import time

modulation = lora_modulation(sf=7,bw=loraBW.BW_500000,cr=5,header_enabled=True,crc_enabled=True,preamble_length=8,payload_length=255,frequency=915000000)

print("trying to set up TXer")
txer = yeenet_router(serial.Serial(port='/dev/ttyUSB0',baudrate=115200))
txer.reset()
txer.modem_setup()
txer.modem_set_modulation(modulation)
print("done!")

print("trying to set up RXer")
rxer = yeenet_router(serial.Serial(port='/dev/ttyUSB1',baudrate=115200))
rxer.reset()
rxer.modem_setup()
rxer.modem_set_modulation(modulation)
print("done")

n_overflow = rxer.buffer_get_n_overflow()
print("reading "  + str(n_overflow) + " as overflow coutner on rxer")
rxer.modem_listen()
print("rxer listening")
for i in range(4):
    print("sending " + str(i))
    txer.modem_load_and_transmit(bytes.fromhex('DEADBEEF'))
packets = rxer.buffer_cap()
print(str(packets) + " packets in buffer")
print(str(rxer.buffer_get_n_overflow()) + " overflow events detected")