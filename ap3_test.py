import serial
import time
ports='tty-huanxintrans'
ser=serial.Serial('/dev/'+ports, 9600)
time.sleep(2)
ser.writelines('\n')
time.sleep(2)
ser.writelines('\n')
time.sleep(2)
ser.writelines('i\n')
time.sleep(4)
ser.writelines('ylb 0000000000000\n')
