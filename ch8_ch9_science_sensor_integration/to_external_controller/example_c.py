# %% start
import datetime
start_time = datetime.datetime.now() # calculate total script time 

import serial       # communication
import base64       # 
import os           # 
import shutil       # move file between folders on the RP
import logging      # to hide the error: "End of file reached without termination char"
import numpy as np  # maths
import bitstring    # for tbd processing
import pandas as pd # for tbd processing
import time         # for tbd processing
import glob         # for tbd processing, list files in folders on RP
import xarray as xr # for tbd processing, save as netCDF

# uart_baud = 115200
# send_chunk_size = 720

uart_baud = 9600
send_chunk_size = 600

port_address = '/dev/ttyUSB0' # CHANGE x TO PORT USED

## Set path to save processed data files to give back to glider
to_dir='/home/rutgers/backseat_driver/to_glider/'

# Set path for .tbd files from glider
from_dir = '/home/rutgers/backseat_driver/from_glider/'

## Set path for completed files
pros_dir = '/home/rutgers/backseat_driver/files_processed/'

# %% class def
class extctl(object):
    def __init__(self, tty):
        self.port = serial.Serial(tty, baudrate=uart_baud, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE, 
        bytesize=serial.EIGHTBITS)

    def send(self, s):
        csum = 0
        # bs = s.encode('ascii')
        bs = s
        for c in bs:
            csum ^= c
        nmea = b'$' + bs + (b'*%02X\r\n' % csum)
        print("Sending: ", nmea)
        self.port.write(nmea)

    def write(self, index, value):
        self.send(b'SW,%d:%f' % (index, value))

    def mode(self, mask, value):
        self.send(b'MD,%d,%d' % (mask, value))

    def read(self):
        return self.port.readline()
    
    @staticmethod
    def send_file_data(data):
        # Encode the data in b64
        output_string = b'FO,' + base64.b64encode(data)
        x.send(output_string)

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
    
    def file_read(self, filename, sci_dir, data_type):
        # Send open read message to glider and open destination file
        command = b'FR,' + bytes(filename, 'utf-8') + b',' + bytes(sci_dir, 'utf-8')
        self.send(command)
        print(f'opening file {filename}')
        if data_type:
            file = open(f'/home/rutgers/backseat_driver/from_glider/{filename}', 'wb')
        else:
            file = open(f'/home/rutgers/backseat_driver/from_glider/{filename}', 'w')
        self.recieve_file_data(file, data_type)

    def GO(self):
        self.send(b'GO')

    def recieve_file_data(self, file, data_type):
        line = self.read()
        print(line)
        # print('chunk sent')
        if line.startswith(b'$ER'):
            return
        if line.startswith(b'$FI'):
            if line.startswith(b'$FI,'):
                line = line.split(b',')
                line = line[1]
                # print(f'line: {line}')
                content = line.split(b'*')[0]
                # print(f'content: {content}')
                if data_type == 'bin':
                    content = base64.decodebytes(content) # binary data
                else:
                    # original
                    # content = base64.b64decode(content).decode('utf-8') # other data
                    
                    # newtry
                    content = base64.decodebytes(content)
                    print(f'content = {content}')
                    # content = base64.b64decode(content) # other data

                file.write(content)
                self.GO()
                self.recieve_file_data(file,data_type)
            else:
                print('Reached EOF, closing file and exiting')
                file.close()                
                return
        else:
            self.recieve_file_data(file,data_type)

    # This function sends the command for the extctl proglet to list files in 'directory' matching 'wild_card'
    def list_directory(self, directory, wild_card):
        self.send(b'LS,' + bytes(directory, 'utf-8') + b',' + bytes(wild_card, 'utf-8'))
    
    # File write but with a specifier for
    def file_write_new(self, source_file, directory):
        # Send command to open a file in directory
        self.send(b'FW,' + bytes(source_file, 'utf-8') + b',' + bytes(directory, 'utf-8'))

###############################################
###############################################
###############################################

# LOGGING and HIDING UNDESIRABLE OUTPUT 
_log = logging.getLogger(__name__)
# Define a custom filter to suppress specific log messages
class CustomFilter(logging.Filter):
    def filter(self, record):
        # Suppress log messages containing the specified text
        return "End of file reached without termination char" not in record.getMessage()

# Add the custom filter to the logger
_log.addFilter(CustomFilter())

# --- # DECODE THE BINARY DATA # --- #
def _decode_sensor_info(dfh, meta):
    """
    Helper to decode the sensor list.

    dfh must be a filehandle because we want to be able to say where we stopped
    in file.
    """

    nsensors_total = int(meta['total_num_sensors'])
    nsensors_used = int(meta['sensors_per_cycle'])
    activeSensorList = [{} for i in range(nsensors_used)]
    outlines = []
    sensorInfo = {}
    for i in range(nsensors_total):
        line = dfh.readline().decode('utf-8')
        if line.split(':')[0] != 's':
            raise ValueError('Failed to parse sensor info')
        splitLine = [string.strip() for string in line.split(' ')[1:]
                     if string and not string.isspace()]
        sensorInfo[splitLine[-2]] = splitLine
        if splitLine[0] == 'T':
            activeSensorList[int(splitLine[2])] = {
                'name': splitLine[-2], 'unit': splitLine[-1],
                'bits': splitLine[-3]}
        outlines = outlines + [line]

    bindatafilepos = dfh.tell()  # keep this for seeking

    return activeSensorList, sensorInfo, outlines, bindatafilepos
def _get_cached_sensorlist(cachedir, meta):
    """
    Helper to get the sensor list from a file in the cache
    """
    fname0 = cachedir + '/' + meta['sensor_list_crc'].upper() + '.CAC'
    dd = glob.glob(cachedir + '/*')
    found = False
    for d in dd:
        if (os.path.split(d)[1].upper() ==
                os.path.split(fname0)[1].upper()):
            found = True
            break
    if not found:
        raise FileNotFoundError(f'Could not find {fname0}')

    with open(d, 'rb') as dfh:
        activeSensorList, sensorInfo, outlines, bindatafilepos = \
                _decode_sensor_info(dfh, meta)

    return activeSensorList, sensorInfo
def _make_cache(outlines, cachedir, meta):
    """
    Helper to make a cache file if one doesn't exist.
    """
    try:
        os.mkdir(cachedir)
    except FileExistsError:
        pass

    fname = cachedir + '/' + meta['sensor_list_crc'] + '.CAC'
    with open(fname, 'w') as dfh:
        for line in outlines:
            dfh.write(line)
def dbd_get_meta(filename, cachedir):
    """
    Get metadata from a dinkum binary file.

    Parameters
    ----------

    filename : str
        filename of the dinkum binary file (i.e. *.dbd, *.ebd)

    cachedir : str
        Directory where the cached CAC sensor lists are kept.  These
        lists are often in directories like ``../Main_board/STATE/CACHE/``.
        These should be copied somewhere locally.  Recommend ``./cac/``.

    Returns
    -------
    meta : dict
        Dictionary of the meta data for this dinkum binary file.

    """

    meta = {}

    with open(filename, 'rb') as dfh:
        meta['num_ascii_tags'] = 99  # read the first 99 lines
        while (len(meta) < int(meta['num_ascii_tags'])):
            line = dfh.readline().decode('utf-8')
            meta[line.split(':')[0]] = line.split(':')[1].strip()
        if len(meta) != int(meta['num_ascii_tags']):
            raise ValueError('Did not find expected number of tags')
        bindatafilepos = dfh.tell()
        localcache = False
        # if the sensor data is here, we need to read it, even though we
        # will use the cache
        if ('sensor_list_factored' in meta and
                not int(meta['sensor_list_factored'])):
            localcache = True
            activeSensorList, sensorInfo, outlines, bindatafilepos = \
                _decode_sensor_info(dfh, meta)

        # read the cache first.  If its not there, try to make one....
        try:
            activeSensorList, sensorInfo = \
                _get_cached_sensorlist(cachedir, meta)
        except FileNotFoundError:
            if localcache:
                _log.info('No cache file found; trying to create one')
                _make_cache(outlines, cachedir, meta)
            else:
                raise FileNotFoundError(
                    'No active sensor list found for crc ',
                    f'{meta["sensor_list_crc"]}. These are often found in ',
                    'offloaddir/Science/STATE/CACHE/ or ',
                    'offloaddir/Main_board/STATE/CACHE/. ',
                    f'Copy those locally into {cachedir}')
        meta['activeSensorList'] = activeSensorList
        # get the file's timestamp...
        meta['_dbdfiletimestamp'] = os.path.getmtime(filename)

    return meta, bindatafilepos
def dbd_to_dict(dinkum_file, cachedir, keys=None):
    """
    Translate a dinkum binary file to a dictionary of data and meta values.

    Parameters
    ----------
    dinkum_file : dbd file name (full path)
        These are the raw data from the glider, either offloaded from a card
        or from the dockserver.

    cachedir : str
        Directory where the cached CAC sensor lists are kept.  These
        lists are often in directories like ``../Main_board/STATE/CACHE/``.
        These should be copied somewhere locally.  Recommend ``./cac/``.

    keys : list of str
        list of sensor names to include in the *data* dictionary.  This
        allows us to make the dictionaries more compact and not have
        all the redundant sensor info.  If a single string then keys is a
        file name and passed to  `~.slocum.parse_filter_file` to get the list
        of keys.

    Returns
    -------
    data : dict
        dictionary of all the data with sensor names as keys, filtered
        according to the *keys* kwarg.

    meta : dict
        dictionary of all the meta data in the file.

    """
    # Parse ascii header - read in the metadata.
    data = []
    DINKUMCHUNKSIZE = int(3e4)  # how much data to pre-allocate

    if isinstance(keys, str):
        keys = parse_filter_file(keys)

    meta, bindatafilepos = dbd_get_meta(dinkum_file, cachedir)
    activeSensorList = meta['activeSensorList']
    dfh = open(dinkum_file, 'rb')
    # ------------------------------------------
    # All subsequent lines are in binary format.
    # Grab the seek pos and use that for a bookmark.
    # ------------------------------------------
    # offset for number of characters already read in.
    _log.debug('reading file from %d', bindatafilepos * 8)
    binaryData = bitstring.BitStream(dfh, offset=bindatafilepos * 8)
    # First there's the s,a,2byte int, 4 byte float, 8 byte double.
    # sometimes the endianess seems to get swapped.
    # ref_tuple = ['s', 'a', 4660, 123.456, 123456789.12345]
    diag_header = binaryData.readlist(['bits:8', 'bits:8'])
    diag_header[0] = chr(int(diag_header[0].hex, 16))
    diag_header[1] = chr(int(diag_header[1].hex, 16))
    if not (diag_header[0] == 's') and (diag_header[1] == 'a'):
        _log.warning("character failure: %s != 's', 'a'", diag_header)
        raise ValueError('Diagnostic header check failed.')

    endian = 'be'
    data = binaryData.read(f'uint{endian}:16')
    _log.debug('Checking endianness %s == 4660 or 13330', data)
    if data == 4660:
        pass
    elif data == 13330:
        endian = 'le'
    else:
        _log.warning("integer failure: %s != 4660", data)
        raise ValueError("Diagnostic header check failed.")
    _log.debug('Endianness is %s', endian)

    data = binaryData.read(f'float{endian}:32')
    if not np.allclose(data, 123.456):
        _log.warning("float32 failure: %s != 123.456", data)
        raise ValueError("Diagnostic header check failed.")

    data = binaryData.read(f'float{endian}:64')
    if not np.allclose(data, 123456789.12345):
        _log.warning("float64 failure: %s != 123456789.12345", data)
        raise ValueError("Diagnostic header check failed.")
    _log.debug('Diagnostic check passed.  Endian is %s', endian)

    nsensors = int(meta['sensors_per_cycle'])
    currentValues = np.zeros(int(meta['sensors_per_cycle'])) + np.NaN
    data = np.zeros((DINKUMCHUNKSIZE, nsensors)) + np.NaN
    # Then there's a data cycle with every sensor marked as updated, giving
    # us our initial values.
    # 01 means updated with 'same value', 10 means updated with a new value,
    # 11 is reserved, 00 is not updated.
    # This character leads off each byte cycle.
    frameCheck = binaryData.read('bytes:1').decode("utf-8")
    updatedCode = ['00'] * int(meta['sensors_per_cycle'])

    # Data cycle begins now.
    # Cycle tag is a ascii 'd' character. Then
    # state_bytes_per_cycle * state_bytes (2bits per sensor) of state bytes.
    # Then data for each updated sensor as per the state bytes.
    # Then zeroes until the last byte is completed, should they be necessary.
    _log.info('Parsing binary data')
    proctimestart = time.time()
    ndata = 0
    while frameCheck == 'd':
        for i in range(int(meta['sensors_per_cycle'])):
            updatedCode[i] = binaryData.read('bin:2')
        # burn off any remaining bits to get to the first full bit.
        binaryData.bytealign()
        for i, code in enumerate(updatedCode):
            if code == '00':  # No new value
                currentValues[i] = np.NaN
            elif code == '01':  # Same value as before.
                continue
            elif code == '10':  # New value.
                if int(activeSensorList[i]['bits']) in [4, 8]:
                    currentValues[i] = binaryData.read(
                        f'float{endian}:' +
                        str(int(activeSensorList[i]['bits']) * 8))
                elif int(activeSensorList[i]['bits']) in [1, 2]:
                    currentValues[i] = binaryData.read(
                        f'uint{endian}:' +
                        str(int(activeSensorList[i]['bits']) * 8))
                else:
                    raise ValueError('Bad bits')
            else:
                raise ValueError(('Unrecognizable code in data cycle. ',
                                  'Parsing failed'))
        data[ndata] = currentValues
        binaryData.bytealign()

        # We've arrived at the next line.
        try:
            d = binaryData.peek('bytes:1').decode('utf-8')
        except bitstring.ReadError:
            _log.debug('position at end of stream %d',
                       binaryData.pos + 8 * bindatafilepos)
            _log.warning('End of file reached without termination char')
            d = 'X'
        if d == 'd':
            frameCheck = binaryData.read('bytes:1').decode('utf-8')
            ndata += 1
            if ndata % DINKUMCHUNKSIZE == 0:
                # need to allocate more data!
                data = np.concatenate(
                    (data, np.NaN + np.zeros((DINKUMCHUNKSIZE, nsensors))),
                    axis=0)
        elif d == 'X':
            # End of file cycle tag. We made it through.
            # throw out pre-allocated data we didn't use...
            data = data[:ndata]
            break
        else:
            raise ValueError(f'Parsing failed at {binaryData.bytepos}. ',
                             f'Got {d} expected d or X')

    proctimeend = time.time()

    # THIS WAS GIVING ERRORS AS THE TIME WAS DIVIDING BY ZERO, seems to work without?
    # _log.info(('%s lines of data read from %s, data rate of %s rows '
    #            'per second') % (len(data), dinkum_file,
    #                             len(data) / (proctimeend - proctimestart)))
    # dfh.close()

    _log.info('Putting data into dictionary')
    ddict = dict()

    # deal 2-D array into a dictionary...  Only keep keys we want...
    for n, key in enumerate(meta['activeSensorList']):
        if keys is None or key['name'] in keys:
            ddict[key['name']] = data[:, n]

    return ddict, meta
# --- #          https://github.com/c-proof/pyglider/blob/main/pyglider/slocum.py         # --- #
# --- # I commented out part of dbd_to_dict due to ZeroDivisionErrors (lines 309-312) # --- #

# this is for the alphanum_key at the end of the initial glob data ingest
# process numbered files in the way a human would think to do it, nicely and numerically
###############################################################################
def tryint(s):
    """
    Return an int if possible, or `s` unchanged.
    """
    try:
        return int(s)
    except ValueError:
        return s
def alphanum_key(s):
    """
    Turn a string into a list of string and number chunks.
    >>> alphanum_key("z23a")
    ["z", 23, "a"]
    """
    return [ tryint(c) for c in re.split('([0-9]+)', s) ]
def human_sort(l):
    """
    Sort a list in the way that humans expect.
    """
    l.sort(key=alphanum_key)
# --- # # from https://nedbatchelder.com/blog/200712/human_sorting.html # --- #




serial.Serial(port_address, baudrate=uart_baud).close()
x = extctl(port_address)
port = serial.Serial(port_address, baudrate=uart_baud)

test=0
count=0

file_list=[]
x.list_directory("logs",".tbd")

print('before while')
while test == 0:
    cur_line = str(port.readline())
    # print(cur_line)
    # ["b'$DIR",'c:/logs/00100000.tbd', 'c:/logs/00110000.tbd', 'c:/logs/00120000.tbd', '']
    # Split into separate fields
    msg = cur_line.split('*')
    fields = msg[0].split(',')
    # print(fields)
    # ["b'$DIR", 'c:/logs/00100000.tbd', 'c:/logs/00110000.tbd', 'c:/logs/00120000.tbd', '']
    
    for subscription in fields:
        if 'c:' in subscription:# get files from the list_dir function
            subs=subscription.split(':')
            pfile=subs[1]
            # print(subs)
            file_list.append(subscription)
            print(f'file_list: {file_list}')

    if (file_list != None):
        # print(f'file_list -1: {file_list[-1]}')         #  c:/logs/00120000.nbd
        # tbd_file_name = os.path.basename(file_list[-1]) # 00120000.nbd
        # tbd_file_name = '00120000.tbd'
        # tbd_file_full = 'c:/logs/00120000.tbd'
        # tbd_file_name = '03590094.tbd'
        # 01790015

        tbd_file_name = 'ru34-2024-089-0-22.tbd'
        # x.send_file(port, "/home/rutgers/backseat_driver/"+str(name), str(name), "logs", 1)
        # send_file(uart_port, file_path, dest_name, dest_dir, byte_bool):

        #get file from glider to pi
        x.file_read(tbd_file_name,"logs",1)
        ## add path to most recent filename
        print('file transferred, trying to process now...')
        file = '/home/rutgers/backseat_driver/from_glider/'+tbd_file_name

        if (os.path.isfile(file)>0):

            # must have the cac files for the glider on the RP
            tbd,tbd_meta = dbd_to_dict(file,'rutgers-cac/')

            # imports the data into Pandas DataFrame using proper time for type of file
            tbd_data = pd.DataFrame.from_dict(tbd, orient='columns', dtype=None, columns=None).set_index('sci_m_present_time')

            # cleans up the DataFrame time indices.
            tbd_data.index = pd.to_datetime(tbd_data.index,unit='s').round(freq='S')
        
            # make xarray dataset
            tbd_xr = xr.Dataset.from_dataframe(tbd_data)
            xr_file_name = f'{tbd_file_name}.nc'

            # Save the Dataset to a NetCDF file
            tbd_xr.to_netcdf(to_dir+xr_file_name)

            ncname = os.path.basename(to_dir+xr_file_name)

            #send nc from pi to glider
            x.send_file(port, "/home/rutgers/backseat_driver/to_glider/"+str(ncname), str(ncname), "logs", 1)
            #once sent to glider, move processed nc to files_processed folder
            # os.remove(file)

        elif (os.stat(tbd_file_name).st_size==0):
            print(tbd_file_name, 'created, but data did NOT write to file.')
            os.remove(tbd_file_name)
        elif not os.path.isfile(tbd_file_name):
            print('Failed to create ',tbd_file_name)
            os.remove(tbd_file_name) 
        print('Finished')
    else:
        print('File does not exist.')

    test = 1

# time calculation
end_time = datetime.datetime.now()
script_time = end_time - start_time
elapsed_seconds = str(round(script_time.total_seconds(),2))

# save script time in a .txt file by appending each iteration 
with open('script_times_example_b.txt','a') as file:
    file.write(f'{elapsed_seconds}\n')
# %%
