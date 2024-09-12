'''
Chapter 9: Examble B
Used to send fake CTD data via UART to a glider simulator by:
  1) Making fake data to send
  2) Sending the fake data via UART

This can be used with Example A's external controller script to verify proper input to glider
Best used for ensuring proper external controller (EC) behavior for a CTD sensor value change: i.e.,
the EC recognizes a temperature or salimity change and does something

Credits: 
  - Initial brainstorming and ideation with Dave Aragon (Rutgers)
  - First implimentation by Ella Wawrzynek (MIT, file: ctdDataUART.py)
    > Ingests .ebd files to send real ocean data

This program has been adapted from Ella's code.
'''
# %% making the fake CTD data to send
import numpy as np
import pandas as pd
import time
import serial 
import matplotlib.pyplot as plt # used for debugging 

# set length of fake CTD data
# runs at 1hz so determine minutes to run script here
min_to_run  = 10
time_to_run = np.arange(0,min_to_run*60,1)
length      = len(time_to_run)

# warmer surface, decrease with depth (time)
surface_temp = [20]
iterate_temp = np.cos(np.arange(0,1.5,(1.5/length)))
water_temp   = surface_temp * iterate_temp
# plt.plot(iterate_temp)
# plt.plot(water_temp)

# fresher surface, increase with depth
depth_salt   = [5]
iterate_salt = np.cos(np.arange(-1.5,0,(1.5/length)))
water_cond   = depth_salt * iterate_salt
# plt.plot(iterate_salt)
# plt.plot(water_cond)

# assume average dive speed with delay for start of mission initilization
# 0.2 m/s with a sample rate of 1hz, glider goes 20cm/s down
# depth changes 1 bar per 10 meters
# 0.1 bar / meter 
# (0.1 bar / 100cm) / 5
# 0.02 per 20cm 
# so increase pressure by 0.02 bar per second until done
# 1 minutes of diving at 0.2m/s = 12 meters * 10
# 120 meters = 120 bar
pressure_pause = [0]*60 # surface time before diving
pressure_data  = (np.arange(0,120,(120/(length-60))))
pressure       = pressure_pause.__iadd__(pressure_data)
# plt.plot(pressure_data) # surface pause before diving

sci_data = pd.DataFrame(index=time_to_run)
sci_data['cond']     = water_cond
sci_data['temp']     = water_temp
sci_data['pressure'] = pressure
indx = len(sci_data)-1

# %% Make saved subplots of above data
fig, ax = plt.subplots(3, 1, figsize=(8, 10))  # 3 rows, 1 column

# water temperature
ax[0].plot(sci_data.index, sci_data['temp'], color='blue')
ax[0].set_ylabel('Temperature (°C)')
ax[0].set_title('Water Temperature')
ax[0].set_xlim(0,610)

# water conductivity
ax[1].plot(sci_data.index, sci_data['cond'], color='green')
ax[1].set_ylabel('Conductivity (S/M)')
ax[1].set_title('Water Conductivity')
ax[1].set_xlim(0,610)

# pressure
ax[2].plot(sci_data.index, sci_data['pressure'], color='red')
ax[2].set_ylabel('Pressure (bar)')
ax[2].set_title('Pressure')
ax[2].set_xlim(0,610)

plt.tight_layout()
# plt.show()
ax[0].grid();ax[1].grid();ax[2].grid()
plt.savefig('simCTD_data.png')

################################################################

# %% FOR DEBUGGING: print to terminal and not port
# indx = len(sci_data)-1
# count = 0
# while indx > 0:
#     round = 4
#     cond = np.round(sci_data.cond[count],round)
#     temp = np.round(sci_data.temp[count],round)
#     pres = np.round(sci_data.pressure[count],round)
#     print(f'{cond},{temp},{pres}\r\n')

#     time.sleep(1) # approx 1 Hz data rate
#     indx  = indx - 1
#     count = count + 1

# # %% save as .txt file
# indx = len(sci_data)-1
# count = 0

# with open('fake_CTD.txt','w') as file:
#     file.write('cond,temp,pres\n')
#     while indx > 0:

#         round = 4
#         cond = np.round(sci_data.cond[count],round)
#         temp = np.round(sci_data.temp[count],round)
#         pres = np.round(sci_data.pressure[count],round)

#         file.write(f'{cond},{temp},{pres}\n')

#         indx  = indx - 1
#         count = count + 1
# print('file saved!')

################################################################

# %% SEND VIA COM PORT CONNECTION

port = 'COM5' # USB port 
baud = 9600
timeout = 0 # Non-blocking read

class ctd41cp(object):
    def __init__(self, port):
        self.port = serial.Serial(port, baudrate=baud, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE, 
        timeout=timeout, bytesize=serial.EIGHTBITS)

    def write(self, s,count):
        print('Sending: ', s,'| count is',count)
        self.port.write(s)
        
    def read(self):
        return self.port.readline()

print('Opening port...')
u = ctd41cp(port)

print('Sending CTD data to simulator...')
index_len = len(sci_data)-1 #-1 cuz zero starting list
count = 0
while indx > 0:
    round = 4
    cond = np.round(sci_data.cond[count],round)
    temp = np.round(sci_data.temp[count],round)
    pres = np.round(sci_data.pressure[count],round)
    write = (f'{pres},{temp},{cond}\r\n')
    encoded_bytes = write.encode('utf-8')
    u.write(encoded_bytes,count)

    time.sleep(1) # approx 1 Hz data rate
    indx  = index_len - 1
    count = count + 1

u.port.close() # have to close or can't reopen and run again
print('all data sent')
# to ensure is good
# time calculation
# end_time = datetime.datetime.now()
# script_time = start_time - end_time
# elapsed_seconds = str(round(script_time.total_seconds(),2))

# # save script time in a .txt file by appending each iteration 
# with open('script_times_example_b.txt','a') as file:
#     file.write(f'{elapsed_seconds}\n')
# %%


# this is verifying the data did in fact make it across to the external controller properly 
file = 'sci_data_example_b_second.txt'
column_names = ['cond', 'temp', 'pressure']
sci_data_EC = pd.read_csv(file, sep=',', names=column_names, header=None)
sci_data_EC.index = (range(len(sci_data_EC)))

fig, ax = plt.subplots(3, 1, figsize=(8, 10))  # 3 rows, 1 column

# water temperature
ax[0].plot(sci_data_EC.index, sci_data_EC['temp'], color='blue')
ax[0].set_ylabel('Temperature (°C)')
ax[0].set_title('Water Temperature')
ax[0].set_xlim(0,110)

# water conductivity
ax[1].plot(sci_data_EC.index, sci_data_EC['cond'], color='green')
ax[1].set_ylabel('Conductivity (S/M)')
ax[1].set_title('Water Conductivity')
ax[1].set_xlim(0,110)

# pressure
ax[2].plot(sci_data_EC.index, sci_data_EC['pressure'], color='red')
ax[2].set_ylabel('Pressure (bar)')
ax[2].set_title('Pressure')
ax[2].set_xlim(0,110)

plt.tight_layout()
# plt.show()
ax[0].grid();ax[1].grid();ax[2].grid()
plt.savefig('simCTD_data_FROM_EC.png')