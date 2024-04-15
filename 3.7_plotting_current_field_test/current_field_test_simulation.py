import glob
import os
import logging
import bitstring
import time
import numpy as np
# import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import re 
import cartopy.crs as ccrs
import cartopy.feature as cfeature
# import cmocean.cm as cmo
import cartopy.crs as ccrs
import cool_maps.plot as cplt
from geopy.distance import geodesic
from tkinter.filedialog import askdirectory

wheresave = askdirectory(title='Select Folder')   
fz_s = 200
fz_e = 1500
fz_speed = 1.5

what_to_plot = input('Choose plots(loc, lmc, fzb, yo, or all): ')

# --- # LOGGING and HIDING UNDESIRABLE OUTPUT # --- #
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

# process strings from glider into numbers for plotting
# convert lmc coordinates to lat and lon using initial location and distance from
def str2num_north_west(lat_str,lon_str):
    """
    Docstring: Converts glider lat/lon coords to decimals, then processes into Pandas dataframe. 

    Parameters:
    - parameter1 (str): latitude strings from [m_lat]
    - parameter2 (str): longitude strings from [m_lon]
    ...

    Returns:
    type: Float lat, lon, indexed by time. 
    """
    lat = []
    lon = []

    for i in range(len(lon_str)): 
        
        # latitude strings
        latdegstr = str(lat_str[i])[0:2]    # first 2
        latminstr = str(lat_str[i])[2:]     # everything but first 2

        # latitude strings to integers for mapping 
        latmaploop = (float(latdegstr)) + ((float(latminstr)))/60
        lat.append(latmaploop)

        # longitude strings
        londegstr = str(lon_str[i])[1:3]
        lonminstr = str(lon_str[i])[3:]

        # longitude strings to integers for mapping 
        lonmaploop = (float(londegstr)) + ((float(lonminstr)))/60
        lon.append(-lonmaploop)

    coords = pd.DataFrame()     # put the above into final dataframe
    coords['lat'] = lat
    coords['lon'] = lon
    coords = coords.set_index(lon_str.index)

    # Return statement: If the function returns a value
    return coords
def lmc2deg(x_lmc, lat, lon):
    """
    Convert linear distance in meters (both latitude and longitude) to angular distance in degrees using geopy.

    Parameters:
    - x_lmc: Linear distance in meters for longitude.
    - y_lmc: Linear distance in meters for latitude.
    - lat: Latitude of the location in degrees.
    - lon: Longitude of the location in degrees.

    Returns:
    - lmc_lat: Angular distance in degrees for latitude.
    - lmc_lon: Angular distance in degrees for longitude.
    """
    # Convert linear distances to kilometers
    # lat_km = y_lmc / 1000.0
    lat_km = 0
    lon_km = x_lmc / 1000.0

    # Use geopy to calculate the destination points for both latitude and longitude
    dest_lat = geodesic(kilometers=lat_km).destination(point=(lat, lon), bearing=0)
    dest_lon = geodesic(kilometers=lon_km).destination(point=(lat, lon), bearing=90)

    # Get the latitude and longitude of the destination points
    lmc_lat = dest_lat.latitude
    lmc_lon = dest_lon.longitude

    # Get the latitude and longitude of the destination points
    lmc_lat = dest_lat.latitude
    lmc_latbot = lmc_lat - 5
    lmc_lattop = lmc_lat + 5

    lat = (lmc_latbot,lmc_lattop)
    lon = (lmc_lon,lmc_lon)

    return lat,lon
# --- # Made by me # --- #

# create list of all files in folder
sbd_raw  = sorted(glob.glob('../process_glider_files/spectre/*.sbd'),key=alphanum_key)
tbd_raw  = sorted(glob.glob('../process_glider_files/spectre/*.tbd'),key=alphanum_key)

# sbd_raw  = sorted(glob.glob('../process_glider_files/ru23/*.sbd'),key=alphanum_key)
# tbd_raw  = sorted(glob.glob('../process_glider_files/ru23/*.tbd'),key=alphanum_key)

# init final Pandas dataframe
final = pd.DataFrame()

# how many times to loop through and append data
loopnum = range(0,len(sbd_raw))
print(f'Files to process: {len(sbd_raw)}') # visual check
loopdisp = 1 # init

# need to look through ^ files and put into one dataframe 
for i in loopnum:

    sbd_file = sbd_raw[i]
    tbd_file = tbd_raw[i]

    # where are the cac files
    sbd,sbd_meta = dbd_to_dict(sbd_file,'rutgers-cac/')
    tbd,tbd_meta = dbd_to_dict(tbd_file,'rutgers-cac/')

    # imports the data into two Pandas DataFrames using proper time for type of file
    sbd = pd.DataFrame.from_dict(sbd, orient='columns', dtype=None, columns=None).set_index('m_present_time')
    tbd = pd.DataFrame.from_dict(tbd, orient='columns', dtype=None, columns=None).set_index('sci_m_present_time')

    # cleans up the DataFrame time indices.
    sbd.index = pd.to_datetime(sbd.index,unit='s').round(freq='S')
    tbd.index = pd.to_datetime(tbd.index,unit='s').round(freq='S')

    # combines them into one DataFrame
    data = pd.concat([tbd, sbd]).sort_index()

    # append data to the final dataframe
    # this is what combines each file's segmement into one dataframe 
    final = pd.concat([final, data])

    print(f'{loopdisp}',end=' ',flush=True) # needs a print('\n') after loop now
    loopdisp = loopdisp +1

    if loopdisp == 43:
        print('"That\'s it. That\'s all there is."')
print('\n') # needed

# -------------------------- #
# --- # PLOT FUNCTIONS # --- #
def plot_loc(lat,lon,fast_zone):
    '''
    Input coords and T/F for whether you have fast zones defined
    '''
    
    print('running plot_loc')
    extent_buff_lon = 0.05
    extent_buff_lat = 0.02
    big_extent_buff = 4

    extent = ([min(lon) - extent_buff_lon,
               max(lon) + extent_buff_lon,
               min(lat) - extent_buff_lat,
               max(lat) + extent_buff_lat])

    big_extent = ([min(lon) - big_extent_buff,
                   max(lon) + big_extent_buff,
                   min(lat) - big_extent_buff,
                   max(lat) + big_extent_buff])

    # Create the main map
    fig, ax = cplt.create(extent, proj=ccrs.Mercator(), bathymetry=False, figsize=(10, 7))
    plt.title('Location', fontsize=14)

    # Plot the main data on the main map
    ax.scatter(lon, lat, marker='.', s=20, alpha=0.5, cmap='cool', transform=ccrs.PlateCarree())
    ax.plot(lon, lat, linewidth=0.5, color='black', transform=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, edgecolor='black')
    ax.add_feature(cfeature.OCEAN, color='lightblue')
    ax.add_feature(cfeature.LAND, color='burlywood')

    # Plot fast zone
    if fast_zone == True:
        lat1, lon1 = lmc2deg(fz_s, lat[0], lon[0])
        lat2, lon2 = lmc2deg(fz_e, lat[0], lon[0])
        ax.plot(lon1, lat1, marker='o', linestyle='--', color='red', markersize=0.2, transform=ccrs.PlateCarree())
        ax.plot(lon2, lat2, marker='o', linestyle='--', color='red', markersize=0.2, transform=ccrs.PlateCarree())

    # Add gridlines to main map
    gl = ax.gridlines(draw_labels=True, linewidth=0.1, color='black', alpha=0.5, linestyle='-')
    gl.top_labels = False
    gl.right_labels = False

    # Remove labels
    ax.xaxis.set_ticks_position('none')
    ax.yaxis.set_ticks_position('none')
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    # Create the locator map
    ax_locator = fig.add_axes([0.545, 0.12, 0.2, 0.2], projection=ccrs.PlateCarree())
    plt.plot(lon, lat, linewidth=2, color='red', transform=ccrs.PlateCarree())

    # Set the extent for the locator map
    ax_locator.set_extent(big_extent)
    ax_locator.add_feature(cfeature.COASTLINE, edgecolor='black')
    ax_locator.add_feature(cfeature.OCEAN, color='lightblue')
    ax_locator.add_feature(cfeature.LAND, color='burlywood')

    # Save the plot as a PNG file
    plt.savefig(os.path.join(wheresave,'plot_loc.png'), dpi=300, bbox_inches='tight')
    filename = os.path.join(wheresave,'plot_loc.png')
    print(f'plot_loc saved: {filename}')

def plot_lmc(m_y_lmc,m_x_lmc):
    print('running plot_lmc')
    fig,ax = plt.subplots()
    ax.plot(m_x_lmc, m_y_lmc, linewidth=1.2)

    start_curr = fz_s
    ax.axvline(start_curr, color='red', linestyle='--', linewidth=2, label='Static Line')
    ax.set_facecolor('lightblue')
    end_curr = fz_e
    ax.axvline(end_curr, color='red', linestyle='--', linewidth=2, label='Static Line')

    ax.text(((fz_s+fz_e)/2), 12000, f'{fz_speed} m/s boundary', color='red', fontsize=12, horizontalalignment='center')

    ax.set_ylim(0, 13000)
    ax.set_xlim(-10, 1750)
    ax.set_xlabel('x_lmc (m)')
    ax.set_ylabel('y_lmc (m)')
    ax.set_title('LMC Coords)')

    plt.savefig(os.path.join(wheresave,'plot_lmc.png'), dpi=300, bbox_inches='tight')
    filename = os.path.join(wheresave,'plot_lmc.png')
    print(f'plot_lmc saved: {filename}')

def plot_fzb(lat,lon):
    print('running plot_fzb')
    # Create a map using PlateCarree projection (latitude and longitude)
    fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})

    buffer = 2
    # Set the extent of the map based on the trackline data
    ax.set_extent([min(lon) - buffer,
                    max(lon) + buffer, 
                    min(lat) - buffer, 
                    max(lat) + buffer
                    ])

    # Add coastlines
    ax.coastlines()
    ax.add_feature(cfeature.LAND, color='burlywood') # I liked that color
    ax.add_feature(cfeature.OCEAN, color='lightblue')

    gl = ax.gridlines(draw_labels=True, linewidth=0.1, color='black', alpha=0.5, linestyle='-')
    gl.top_labels = False  # Remove top labels
    gl.right_labels = False  # Remove right labels

    # remove labels from ax.gridlines
    ax.xaxis.set_ticks_position('none')
    ax.yaxis.set_ticks_position('none')

    # remove labels from cartopy
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    # Plot the trackline
    lat1,lon1 = lmc2deg(fz_s, lat[0], lon[0])
    lat2,lon2 = lmc2deg(fz_e, lat[0], lon[0])
    ax.plot(lon1,lat1, marker='o', linestyle='--', color='red', markersize=0.2, transform=ccrs.PlateCarree())
    ax.plot(lon2,lat2, marker='o', linestyle='--', color='red', markersize=0.2, transform=ccrs.PlateCarree())

    plt.title('Fast Zone Boundaries')
    plt.savefig(os.path.join(wheresave,'plot_fzb.png'), dpi=300, bbox_inches='tight')
    filename = os.path.join(wheresave,'plot_fzb.png')
    print(f'plot_fzb saved: {filename}')

def plot_yo (depth):
    print('running plot_yo')
    fig,ax = plt.subplots()

    ax.plot(depth,linewidth=1.2)
    ax.axhline(depth.min(), color='red', linestyle='--', linewidth=2,label='Static Line')
    plt.xlabel('Time')
    plt.ylabel('Depth (m)')
    plt.title('yo profile')
    plt.savefig(os.path.join(wheresave,'plot_yo.png'), dpi=300, bbox_inches='tight')
    filename = os.path.join(wheresave,'plot_yo.png')
    print(f'plot_yo saved: {filename}')

def plot_yo_moving(depth,time):
    # save the animation    
    # ani = animation.FuncAnimation(fig, update, frames=len(downsampled_lon) + repeat_last_frame, interval=1, blit=True)
    # ani.save(os.path.join(wheresave, title + '_static' + '.gif'), writer='imagemagick', fps=30)
    # print(f'\nSuccess! {title}_static.gif saved in {wheresave}')
    

# ------------------------------- #

# ---------------------------------------------- #
# --- # Parse data for individual plotting # --- #
# ---------------------------------------------- #
# for plot_loc and plot_fzp
lat_str = (final['m_lat'].dropna()) 
lon_str = (final['m_lon'].dropna())
coords = str2num_north_west(lat_str,lon_str)
lon = coords['lon']
lat = coords['lat']

# for plot_lmc
m_y_lmc = final['m_y_lmc'].dropna()
m_x_lmc = final['m_x_lmc'].dropna()

# for yo plot
time = final['time']
depth = final['m_pressure'].dropna()*-10.1974

if what_to_plot == 'loc':
    plot_loc(lat,lon,False)
elif what_to_plot == 'lmc':
    plot_lmc(m_y_lmc,m_x_lmc)
elif what_to_plot == 'fzb':
    plot_fzb(lat,lon)
elif what_to_plot == 'yo':
    plot_yo(depth)
elif what_to_plot == 'all':
    plot_loc(lat,lon,True)
    plot_lmc(m_y_lmc,m_x_lmc)
    plot_fzb(lat,lon)
    plot_yo(depth)

opsys = 1
    # open saved dir cuz I was tired of leaving it open / opening it manually
if opsys == 1:
    os.system(f'explorer {os.path.realpath(wheresave)}')  # Windows
elif opsys == 2:
    os.system(f'open {wheresave}')  # macOS
elif opsys == 3:
    os.system(f'xdg-open {wheresave}')  # Linux