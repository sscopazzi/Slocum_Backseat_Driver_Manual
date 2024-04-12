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

    def file_read_old(self, filename):
        # Send open read message to glider and open destination file
        command = b'FR,' + bytes(filename, 'utf-8')
        self.send(command)
        print('opening file'.format(filename))
        file = open('/home/rutgers/rtp_glider_processing/from_glider/{}'.format(filename), 'w')
        self.recieve_file_data(file)

    def file_read(self, filename, sci_dir, data_type):
        # Send open read message to glider and open destination file
        command = b'FR,' + bytes(filename, 'utf-8') + b',' + bytes(sci_dir, 'utf-8')
        self.send(command)
        print('opening file'.format(filename))
        if data_type:
            file = open('/home/rutgers/rtp_glider_processing/from_glider/{}'.format(filename), 'wb')
        else:
            file = open('/home/rutgers/rtp_glider_processing/from_glider/{}'.format(filename), 'w')
        self.recieve_file_data(file, data_type)

    # This function sends the command for the extctl proglet to list files in 'directory' matching 'wild_card'
    def list_directory(self, directory, wild_card):
        self.send(b'LS,' + bytes(directory, 'utf-8') + b',' + bytes(wild_card, 'utf-8'))

    # Handles the reading and writing of a file to the logs folder of a SCI-CPU
    def file_write(self, source_file):

        # Send command to open a file on the SCI-CPU logs directory
        self.send(b'FW,' + bytes(source_file, 'utf-8'))

    # File write but with a specifier for
    def file_write_new(self, source_file, directory):

        # Send command to open a file in directory
        self.send(b'FW,' + bytes(source_file, 'utf-8') + b',' + bytes(directory, 'utf-8'))

    # Runs full loop to send a
    @staticmethod
    def send_file(uart_port, file_path, dest_name, dest_dir, byte_bool):
        # Bool for if need confirmation message
        x.file_write_new(dest_name, dest_dir)
        # open the specified file.
        with open(file_path, 'rb') as file_object:
            while True:
                 # This for binary based files
                if byte_bool:
                    data = file_object.read(send_chunk_size)
                # This for text data
                else:
                    data = bytes(file_object.read(send_chunk_size), 'utf-8')
                # End of file, break loop
                if not data:
                    print("file send break")
                    break
                # Send data and set waiting bool
                x.send_file_data(data)
                waiting = 1
                # Read the uart line until you read get the confirmation message from
                # the proglet
                while waiting:
                    check_line = uart_port.readline()
                    check_line = check_line.decode('utf-8')
                    check_line = check_line.split('*')[0]
                    # Recieved ok to send next chunk, otherwise keep checking for it
                    if check_line == '$NEXT':
                        print('Got the next')
                        waiting = 0

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

    # if '6:' in subscription:              # index number of m_heading
    #     subs = subscription.split(':')    # from TWR
    #     m_water_vel_mag = float(subs[1])  # 
    # else:
        # print('No subscription index 5: to read! :()')

# serial.Serial(port_address, baudrate=baud).close()
