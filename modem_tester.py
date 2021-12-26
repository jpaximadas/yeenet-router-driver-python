from yeenet_router import yeenet_router
from yeenet_router import loraBW
from yeenet_router import lora_modulation
from yeenet_router import remote_serial
import serial
import sys
import time

tries_per_modulation = 5
spreading_factors = [7,8,9,10]
#don't try anything narrower than 62500, it's too slow and unreliable
bandwidths = [loraBW.BW_500000,loraBW.BW_250000]
coding_rates = [5,6,7,8]
frequencies = [903000000,915000000,920000000]
packet = bytes.fromhex('DEADBEEF')

print("trying to set up routers")
host_router = yeenet_router(serial.Serial(port='/dev/ttyUSB0',baudrate=115200))
remote_router = yeenet_router(remote_serial('127.0.0.1',6262))
#remote_router = yeenet_router(serial.Serial(port='/dev/ttyUSB1',baudrate=115200))
host_router.reset()
host_router.modem_setup()

remote_router.reset()
remote_router.modem_setup()

data=[]
data.append(["Frequency (Hz)" , "BW (Hz)" , "SF", "CR" , "TX'er", "Successful?" , "Airtime (usec)", "Bytes" , "RSSI (dBm)" , "SNR (dB)" , "packet" ])

for frequency in frequencies:
    for bw in bandwidths:
        for sf in spreading_factors:
            for cr in coding_rates:  
                modulation = lora_modulation(sf=sf,bw=bw,cr=cr,header_enabled=True,crc_enabled=True,preamble_length=8,payload_length=255,frequency=920000000)
                host_router.modem_set_modulation(modulation)
                remote_router.modem_set_modulation(modulation)
                usec = host_router.modem_get_airtime_usec(len(packet))
                print("Frequency = " +str(frequency),end='')
                print(",BW = " +str(loraBW.get_bandwidth(bw)),end='')
                print(",SF = " +str(sf),end='')
                print(",CR = " +str(cr),end='')
                print(",Airtime = " +str(usec/1000000))

                print("remote->host")
                for i in range(tries_per_modulation):
                    print(str(i+1),end='')
                    sys.stdout.flush()
                    host_router.modem_listen()
                    remote_router.modem_load_and_transmit(packet)
                    time.sleep(usec/1000000)
                    cap = host_router.buffer_cap()
                    
                    if(cap==1):
                        [n,pkt1] = host_router.buffer_pop()
                        reading = [str(frequency) , str(loraBW.get_bandwidth(bw)) , str(sf), str(cr) , "remote", "True" , str(usec), str(len(packet)) , str(pkt1.rssi) , str(pkt1.snr) , str(pkt1.data) ]
                    elif(cap==0):
                        reading = [str(frequency) , str(loraBW.get_bandwidth(bw)) , str(sf) , str(cr) , "remote", "False" , str(usec), str(len(packet)), "N/A" , "N/A" , "N/A" ]
                        print('X',end='')
                    else:
                        reading = [str(frequency) , str(loraBW.get_bandwidth(bw)) , str(sf) , str(cr) , "remote", "False" , str(usec), str(len(packet)), "N/A" , "N/A" , "N/A" ]
                        print('I',end='')
                    print(' ',end='')
                    data.append(reading)
                print("")
                
                print("host->remote")
                for i in range(tries_per_modulation):
                    print(str(i+1),end='')
                    sys.stdout.flush()
                    remote_router.modem_listen()
                    host_router.modem_load_and_transmit(packet)
                    time.sleep(usec/1000000)
                    cap = remote_router.buffer_cap()
                    
                    if(cap==1):
                        [n,pkt1] = remote_router.buffer_pop()
                        reading = [str(frequency) , str(loraBW.get_bandwidth(bw)) , str(sf), str(cr) , "host", "True" , str(usec), str(len(packet)) , str(pkt1.rssi) , str(pkt1.snr) , str(pkt1.data) ]
                    elif(cap==0):
                        reading = [str(frequency) , str(loraBW.get_bandwidth(bw)) , str(sf) , str(cr) , "host", "False" , str(usec), str(len(packet)), "N/A" , "N/A" , "N/A" ]
                        print('X',end='')
                    else:
                        reading = [str(frequency) , str(loraBW.get_bandwidth(bw)) , str(sf) , str(cr) , "host", "False" , str(usec), str(len(packet)), "N/A" , "N/A" , "N/A" ]
                        print('I',end='')
                    print(' ',end='')
                    data.append(reading)
                print("")

                                    

import csv
with open('data.csv', 'w', newline='') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    for reading in data:
        spamwriter.writerow(reading)