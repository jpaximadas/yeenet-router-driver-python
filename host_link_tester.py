from yeenet_router import yeenet_router
import serial
from yeenet_router import remote_serial

print("trying to set up router")

router = yeenet_router(serial.Serial(port='/dev/ttyUSB0',baudrate=115200))
#router = yeenet_router(remote_serial('127.0.0.1',6262))

print("attempting reset...")
router.reset()
print("probably reset")

test_frames = [
    bytes.fromhex('6d6d'),
    bytes.fromhex('deadbeef'),
    bytes.fromhex('5000') * 140,
    bytes.fromhex('FE') * 299,
    bytes.fromhex('EE') *100,
    bytes.fromhex('00') * 100,
    bytes.fromhex('FE') * 299,
    bytes.fromhex('FF') * 299
]

print('starting echo tests')
for i,test_data in enumerate(test_frames):
    print("sending " + str(i) + "...",end='\n')
    retval = router.echo(test_data)

    if(retval==test_data):
        print("Pass")
    else:
        print("Fail")
        print("Sent:"+str(test_frames[i]))
        print("Length:"+str(len(test_frames[i])))
        print("Recv:"+str(retval))
        print("Length:"+str(len(retval)))
router.close()
