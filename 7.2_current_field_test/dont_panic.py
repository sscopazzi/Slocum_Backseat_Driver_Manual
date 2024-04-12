# import sys
# import glob
# import numpy as np
#import matplotlib,
# import netCDF4
#import matplotlib.pyplot as plt
# import datetime
# import struct
# import pandas as pd
# import math
# import scipy
from scipy.sparse.linalg import lsqr
from scipy.spatial.transform import Rotation as R
# import time as timeit
# import time
# import shutil
from pathlib import Path
# from rtp_adcp_class import *
import serial

#time.sleep(20)
# print('done sleep')

# Desired baudrate for uart comms
uart_baud = 9600 #230400 # 115200 # 230400 
# amount of bytes per chunk when writing file to proglet
send_chunk_size = 1200

# Define comms port address
port_address = '/dev/ttyUSB0'


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

    def write(self, index, value):
        self.send(b'SW,%d:%f' % (index, value))

    def mode(self, mask, value):
        self.send(b'MD,%d,%d' % (mask, value))

    @staticmethod
    def send_file_data(data):
        # Encode the data in b64
        output_string = b'FO,' + base64.b64encode(data)
        x.send(output_string)
        
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

    # Read in data from a incoming file
    def recieve_file_data(self, file, byte_data):
        incoming = 1
        no_fi_message_count = 0
        all_file_data = b''
        while incoming:
            line = self.read()
            # print(line)
            if line.startswith(b'$FI'):
                x.send(bytes('GO', 'utf-8'))
                line = line.split(b',')
                if len(line) == 1:
                    incoming = 0
                else:
                    line = line[1]
                    content = line.split(b'*')[0]
                    # all_file_data = all_file_data + content
                    # print('')
                    if byte_data:
                        # Do this for pd0 files and other binary data files
                        content = base64.decodebytes(content)
                    else:
                        # Do this for text files
                         content = base64.b64decode(content).decode('utf-8')
                    file.write(content)
                    # x.send(bytes('GO', 'utf-8'))
            else:
                no_fi_message_count += 1
                print('')
            if no_fi_message_count == 10:
                incoming = 0
        # Close up file
        if incoming == 0:
            print('No More File Data')
            # all_file_data = base64.b64decode(all_file_data).decode('utf-8')
            # file.write(all_file_data)
            file.close()
            print('Closing File')

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
                                  
#################################################################################################                        
test=0
count=0
serial.Serial(port_address, baudrate=uart_baud).close()
x = extctl(port_address)
while x=0:
    port = serial.Serial(port_address, baudrate=uart_baud)
    x.write(0, 42)
    serial.Serial(port_address, baudrate=uart_baud).close()