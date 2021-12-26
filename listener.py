from yeenet_router import yeenet_router
from yeenet_router import loraBW
from yeenet_router import lora_modulation
from yeenet_router import remote_serial
import serial
import sys
import time


print("trying to set up router")
host_router = yeenet_router(serial.Serial(port='/dev/ttyUSB1',baudrate=115200))
host_router.reset()
host_router.modem_setup()
modulation = lora_modulation(sf=7,bw=loraBW.BW_500000,cr=5,header_enabled=True,crc_enabled=True,preamble_length=8,payload_length=255,frequency=915000000)
host_router.modem_set_modulation(modulation)
host_router.modem_listen()

try:
    while(True):
        
        i = 0
        loading_animation = ['|','/','-','\\']
        while(host_router.buffer_cap() == 0):
            char = loading_animation[i%len(loading_animation)]
            print('Waiting for packet ' + char ,end="\r")
            time.sleep(.1)
            i = i+1
        print("\nGot packet!")
        while(True):
            [num,pkt] = host_router.buffer_pop()
            print(pkt.data.hex())
            if(num == 1):
                break
        

except KeyboardInterrupt:
    print("stopped")
    host_router.close()
