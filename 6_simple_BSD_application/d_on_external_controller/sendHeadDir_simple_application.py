import numpy as np
import serial 

# Desired baudrate for uart comms
baud = 9600 
# amount of bytes per chunk when writing file to proglet
send_chunk_size = 600

# Define comms port address
port_address = '/dev/ttyUSB0'

class extctl(object):
    def __init__(self, tty):
        self.port = serial.Serial(tty, baudrate=baud, xonxoff=False, rtscts=False, 
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

    def write(self, index, value):
        self.send(b'SW,%d:%f' % (index, value))

    def mode(self, mask, value):
        self.send(b'MD,%d,%d' % (mask, value))

    @staticmethod
    def read(self):
        #ser = serial.Serial(port_address, baudrate=uart_baud)
        #line = ser.readline()
        line = self.port.readline()
        return line

################################################################################################                        

port = serial.Serial(port_address, baudrate=baud)
x = extctl(port_address)

cur_line = str(port.readline())     # full line coming from glider
#print(f'cur_line: {cur_line}')    # view full line if viewed from RasPi
msg = cur_line.split('*')           # Split into separate fields
fields = msg[0].split(',')          # Split into separate fields
print(f'Fields: {fields}')

# the ifs MUST match the num order in extctl.ini
for subscription in fields:
    # if '3:' in subscription:              # index number of m_water_vel_dir in extctl.ini
    #     subs = subscription.split(':')    # from TWR
    #     m_heading = float(subs[1])        # get the angle

    # if '4:' in subscription:              # index number of m_water_vel_mag 
    #     subs = subscription.split(':')    # from TWR
    #     m_avg_speed = float(subs[1])      # get the angle
    
    if '5:' in subscription:              # index number of m_avg_speed
        print('found 5: -> processing!')
        subs = subscription.split(':')    # from TWR
        m_water_vel_dir = float(subs[1])  # 

        new_heading = m_water_vel_dir + np.pi / 2    # Adding 90 degrees still in radians
        new_heading = np.round(new_heading,5)
        print(f'From Glider (m_water_vel_dir): {m_water_vel_dir} | From RasPi (perp_angle): {new_heading}') # see them for debug
        x.write(0,new_heading)

    # else:
        # print('No subscription index 5: to read! :()')