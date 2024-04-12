# depth_print.py
# update d_target_depth(m) that is mission_param_a in yo99.ma

import serial

uart_baud = 9600                # Desired baudrate for uart comms
send_chunk_size = 600           # amount of bytes per chunk when writing file to proglet
port_address = '/dev/ttyUSB0'   # Define comms port address

class extctl(object):
    def __init__(self, tty):
        self.port = serial.Serial(tty, baudrate=uart_baud, xonxoff=False, rtscts=False, 
        dsrdtr=False, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE, 
        bytesize=serial.EIGHTBITS, timeout=None)

    def send(self, s):
        csum = 0
        # bs = s.encode('ascii')
        bs = s
        for c in bs:
            csum ^= c
        nmea = b'$' + bs + (b'*%02X\r\n' % csum)
        print(nmea)
        self.port.write(nmea)

    def write_SW(self, index, value):
        self.send(b'SW,%d:%f' % (index, value))

    def write_TXT(self,value):
        self.send(b'TXT,%f' % (value))
                                  
###############################################################                        
test=0

serial.Serial(port_address, baudrate=uart_baud).close()
x = extctl(port_address)

while test == 0:
    port = serial.Serial(port_address, baudrate=uart_baud)
    x.write_SW(0, 42)   # update mission_param_a
    x.write_TXT(42)     # print value to glider terminal
    test = 1
    print('d_target_depth updated, message sent')