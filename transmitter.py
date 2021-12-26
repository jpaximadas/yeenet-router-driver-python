from yeenet_router import yeenet_router
from yeenet_router import loraBW
from yeenet_router import lora_modulation
from yeenet_router import remote_serial
import serial
import sys
import time

print("trying to set up router")
host_router = yeenet_router(serial.Serial(port='/dev/ttyUSB0',baudrate=115200))
host_router.reset()
host_router.modem_setup()
modulation = lora_modulation(sf=7,bw=loraBW.BW_500000,cr=5,header_enabled=True,crc_enabled=True,preamble_length=8,payload_length=255,frequency=915000000)
host_router.modem_set_modulation(modulation)
packet_num=0  
try:
    while(True):
        packet = int.to_bytes(packet_num,byteorder='big',length=10)
        print(packet.hex())
        host_router.modem_load_and_transmit(packet)
        packet_num = packet_num + 1
except Exception as E:
    print(E)
print("Done!")

