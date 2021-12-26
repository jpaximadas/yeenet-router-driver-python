from yeenet_router import yeenet_router
import serial
from yeenet_router import remote_serial

print("trying to set up router")

router = yeenet_router(serial.Serial(port='/dev/ttyUSB0',baudrate=115200))
#router = yeenet_router(remote_serial('127.0.0.1',6262))

print("attempting reset...")
router.reset()
print("probably reset")

problem_packet = bytes.fromhex('FF') * 299
i = 1

try:
    while(True):
        print("sending " + str(i))
        retval = router.echo(problem_packet)
        i = i+1
finally:
    router.close()