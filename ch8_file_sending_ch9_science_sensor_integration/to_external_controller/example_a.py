'''
Chapter 9: Example A
1) Using a real CTD41CP sensor, ingest the data from the glider simulator
2) Append data to a .txt on the RP with a time stamp
3) May recall x past ocean values if desired
'''

import datetime # for m_present_time to normal time converting
start_time = datetime.datetime.now()

# import numpy as np
import serial
# import base64
# import pandas as pd

baud = 9600             # Desired baudrate for uart comms
send_chunk_size = 600   # amount of bytes per chunk when writing file to proglet

port_address = '/dev/ttyUSB0'   # Define comms port address

file_path = "/home/rutgers/backseat_driver/sci_data.txt" # where to save the science data on the RP

# from Teledyne 
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

    def mode(self, mask, value):
        self.send(b'MD,%d,%d' % (mask, value))

    @staticmethod
    def read(self):
        line = self.port.readline()
        return line

# with open(file_path, 'a') as file: # a is for append mode
#     # put a header on the file to make it easy to ingest later
#     file.write('m_present_time,sci_water_cond,sci_water_temp,sci_water_pressure\n')

################################################################################################                        

m_present_time_norm =   None
sci_water_cond =        None
sci_water_temp =        None
sci_water_pressure =    None

port = serial.Serial(port_address, baudrate=baud)
x = extctl(port_address)

done_with_loop = 0

while done_with_loop == 0:
    # print('starting while')
    cur_line = str(port.readline())     # full line coming from glider
    # print('fuck you')
    msg = cur_line.split('*')           # Split into separate fields
    fields = msg[0].split(',')          # Split into separate fields
    # print   (f'{datetime.datetime.now()}: Fields: {fields}')

    # the ifs MUST match the num order in extctl.ini
    for subscription in fields:      
        if '0:' in subscription:              # index number of m_present_time_epoc
            subs = subscription.split(':')    # from TWR    
            time_epoc = float(subs[1])
            m_present_time_norm = datetime.datetime.fromtimestamp(time_epoc) # convert to human timestamp 
            print(f'found 1 = {m_present_time_norm}')

        if '1:' in subscription:              # index number of sci_water_cond
            subs = subscription.split(':')    # from TWR
            sci_water_cond = round(float(subs[1]),6)   # 
            print(f'found 2 = {sci_water_cond}')
            
        if '2:' in subscription:              # index number of sci_water_temp
            subs = subscription.split(':')    # from TWR
            sci_water_temp = float(subs[1])   # 
            print(f'found 3 = {sci_water_temp}')
            
        if '3:' in subscription:                 # index number of sci_water_pressure
            subs = subscription.split(':')       # from TWR
            sci_water_pressure = float(subs[1])  # 
            print(f'found 4 = {sci_water_pressure}')
        
    if (m_present_time_norm != None) and \
        (sci_water_cond != None) and \
        (sci_water_temp != None) and \
        (sci_water_pressure != None):
        
        print(f'time: {m_present_time_norm} | cond: {sci_water_cond} | temp: {sci_water_temp} | pres: {sci_water_pressure}')
        # write the science data to a text file on the RP
        # sci_data = [m_present_time_norm,sci_water_cond,sci_water_temp,sci_water_pressure]

        with open(file_path, 'a') as file:      # a is for append mode
            file.write(f'{m_present_time_norm},{sci_water_cond},{sci_water_temp},{sci_water_pressure}\n')
            
            # for value in sci_data:              # append each value 
            #     file.write(str(value) + ',')    # comma so it's a csv
            # file.write('/n')                    # new line
            print('sci_data appended')

        done_with_loop = 1

# time calculation
end_time = datetime.datetime.now()
script_time = end_time - start_time
elapsed_seconds = str(round(script_time.total_seconds(),2))

# save script time in a .txt file by appending each iteration 
with open('script_times_example_a.txt','a') as file:
    file.write(f'{elapsed_seconds}\n')



# if desire ingesting data can look at past data 
# sci_data = pd.read_csv('sci_data.txt',index_col=0,header=True)