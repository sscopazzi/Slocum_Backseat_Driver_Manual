# this is from Ella Wawrzynek (MIT)
# she reads in .dbd data from a real glider deployment
# and sends that to the glider
# I have not tested this method, but it worked for her
# Uses same connector as simCTD_synthetic.py
##################################################

# Note: 1 Hz sampling for ctd41cp
# %% Imports and parameters
import serial
import time
import numpy as np
import dbdreader

port = 'COM5' # USB port 
baud = 9600
timeout = 0 # Non-blocking read

class ctd41cp(object):
    def __init__(self, port):
        self.port = serial.Serial(port, baudrate=baud, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE, 
        timeout=timeout, bytesize=serial.EIGHTBITS)

    def write(self, s):
        print("Sending: ", s)
        self.port.write(s)
        
    def read(self):
        return self.port.readline()

def get_tCTDxy_data_array(files,comp=False):
    xbd=dbdreader.MultiDBD(files,complemented_files_only=comp,complement_files=comp)
    t_ctd,C,T,P=xbd.get_CTD_sync()
    tCTDxy_data = np.array([t_ctd,C,T,P])
    return tCTDxy_data
    
def get_data_array(files,comp=False):
    xbd=dbdreader.MultiDBD(files,complemented_files_only=comp,complement_files=comp)
    raw_array = xbd.get("sci_water_cond","sci_water_temp", "sci_water_pressure",return_nans=True)
    return raw_array

# %% Get CTD data from previous ebd files

datapath = r''
datafiles = [datapath+"00810000.ebd",datapath+"00820000.ebd",datapath+"00910002.ebd"] 

print('Decoding CTD data...')
ctd_data = get_tCTDxy_data_array(datafiles)
#ctd_data_raw = get_data_array(datafiles)

# %% Send CTD data over uart line

print('Opening port...')
u = ctd41cp(port)
# u.write(b'<!--start logging-->\r\n') # This line appears to be unnecessary

print('Sending CTD data to simulator...')
indx = len(ctd_data[0])-1
while indx > 0:
    u.write(b'%f, %f, %f\r\n' %(ctd_data[1][0],ctd_data[2][0],ctd_data[3][0]))
    time.sleep(1) # approx 1 Hz data rate
    indx = indx - 1