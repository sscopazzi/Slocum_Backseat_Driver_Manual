
import serial                       # for BSD communication
import numpy as np                  # math 
import math                         # used for function
from math import radians, sin, cos, sqrt, atan2
import pandas as pd                 # data managment
import matplotlib.pyplot as plt     # plot
import cartopy.crs as ccrs          # plot
import cartopy.feature as cfeature  # plot
import datetime                     # convert m_present_time to human time

timer_start = datetime.datetime.now()

# WE SHALL ROAM THE OCEAN IN AN EASTERLY DIRECTION ON OUR JOURNEY TO SAMPLE
# DESCRIPTIONS OF BSD ERROR MESSAGES SENT VIA GLIDER TERMINAL
er_m_water_vel_dir = 0100011.0 # PRESS F TO PAY RESPECTS

# PROGRESS MESSAGES SENT VIA GLIDER TERMINAL
values_present = 3
data_done = 7
plot_done = 15
all_done = 42

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

    def write_SW(self, index, value):
        self.send(b'SW,%d:%f' % (index, value))

    def write_TXT(self,value):
        self.send(b'TXT,%f' % (value))

    def mode(self, mask, value):
        self.send(b'MD,%d,%d' % (mask, value))

    @staticmethod
    def read(self):
        #ser = serial.Serial(port_address, baudrate=uart_baud)
        #line = ser.readline()
        line = self.port.readline()
        
        return line

    # This function sends command for extctl proglet to list files in 'directory' matching 'wild_card'
    def list_directory(self, directory, wild_card):
        self.send(b'LS,' + bytes(directory, 'utf-8') + b',' + bytes(wild_card, 'utf-8'))

    # Handles reading and writing of a file to logs folder of a SCI-CPU
    def file_write(self, source_file):

        # Send command to open a file on SCI-CPU logs directory
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
        # open specified file.
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
                # Read uart line until you read get confirmation message from
                # proglet
                while waiting:
                    check_line = uart_port.readline()
                    check_line = check_line.decode('utf-8')
                    check_line = check_line.split('*')[0]
                    # Recieved ok to send next chunk, otherwise keep checking for it
                    if check_line == '$NEXT':
                        print('Got next')
                        waiting = 0

# to calculate best heading
def what_is_best_heading(underwater_time_sec, m_avg_speed_mps, m_heading_rad, m_water_vel_dir_rad, m_water_vel_mag_mps):
    """
    Calculate the best heading based on input parameters.
    
    Parameters:
    - underwater_time (float): Time spent underwater in hours.
    - m_avg_speed_mps (float): Average speed of the glider in meters per second.
    - m_heading_rad (float): Glider's heading in radians.
    - m_water_vel_dir_rad (float): Water velocity direction in radians.
    - m_water_vel_mag_mps (float): Water velocity magnitude in meters per second.
    
    Returns:
    - final_vel_mag_mps (float): Magnitude of the final velocity in meters per second.
    - final_vel_dir_rad (float): Direction of the final velocity in radians.
    - deflection_distance_km (float): Distance glider would travel at the heading in km. 
    """
    # calculate estimated distance from time and speed
    # km = m/s * 60 for min * 60 for hour * hours underwater
    # est_distance_km = m_avg_speed_mps * 60 * 60 * underwater_time
    
    # glider vel components (horiz and vert)
    glider_vx_mps = m_avg_speed_mps * math.sin(m_heading_rad)  # m_heading is radians
    glider_vy_mps = m_avg_speed_mps * math.cos(m_heading_rad)  # take average of last x number somehow???

    # water vel components (horiz and vert)
    water_vx_mps = m_water_vel_mag_mps * math.sin(m_water_vel_dir_rad)  # m_water_vel_dir is radians
    water_vy_mps = m_water_vel_mag_mps * math.cos(m_water_vel_dir_rad)
    
    # combine glider and water velocities
    final_vx_mps = glider_vx_mps + water_vx_mps
    final_vy_mps = glider_vy_mps + water_vy_mps

    # calculate the magnitude of the resultant velocity
    final_vel_mag_mps = math.sqrt(final_vx_mps ** 2 + final_vy_mps ** 2)

    # calculate the direction of the resultant velocity
    final_vel_dir_rad = math.atan2(final_vy_mps, final_vx_mps)

    # what is new estimated distance?
    new_dist_m = final_vel_mag_mps * 3600 * underwater_time_sec # underwater time to seconds

    # d=s*t --> t=d/s, used for calculating distance value
    deflect_time_sec = new_dist_m / final_vel_mag_mps

    # Calculate the deflection distance 
    deflection_distance_km = (final_vel_mag_mps * deflect_time_sec)/1000

    return final_vel_mag_mps, final_vel_dir_rad, deflection_distance_km  # for km, returning magnitude and direction as well

# m_avg_speed, running averages over what 

# length of a degree of longitude at a given latitude
def lon_to_km(m_lat):
    # latitude from degrees to radians
    latitude_rad = math.radians(m_lat)
    # length of a degree of longitude
    length_of_lon = EARTH_RADIUS * math.cos(latitude_rad) * (math.pi / 180)
    return length_of_lon

# Function to calculate distance between two points using haversine formula
def haversine(lon1, lat1, lon2, lat2):
    # Convert latitude and longitude from degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    radius_earth = 6371  # Radius of the Earth in kilometers
    distance = radius_earth * c  # Distance in kilometers
    return distance

# Constants for the conversion of degrees to distance (considering a simplified flat Earth)
EARTH_RADIUS = 6371    
LAT_TO_KM = 111.32  # 1 degree latitude = 111.32 km
LON_TO_KM = lon_to_km(20)    # use function to account for latitude of glider
         # Earth's radius in kilometers    

# Initialize lists to hold data
# there's a better way, but this works so *shrug*
final_vel_mag_mps_list = []
final_vel_dir_rad_list = []
deflection_distance_km_list = []
glider_positions_list = []

final_vel_mag_mps_list_all = []
final_vel_dir_rad_list_all = []
deflection_distance_km_list_all = []
glider_positions_list_all = []

final_vel_mag_mps_list_12 = []
final_vel_dir_rad_list_12 = []
deflection_distance_km_list_12 = []
glider_positions_list_12 = []

angles_deg = list(range(45,136))  # list of angles, degrees
angles_rad = [math.radians(angle_deg) for angle_deg in angles_deg]  # degrees to radians

angles_deg_all = list(range(0,361))  # List of ALL angles in degrees
angles_rad_all = [math.radians(angle_deg_all) for angle_deg_all in angles_deg_all]  # degrees to radians

# init false
done_with_for_loop = 0 
m_dr_time_12 = 24 # want a 24 projection for the plot
################################################################################################                        
# should match extctl.ini
baud = 9600 
send_chunk_size = 600

# comms port address
port_address = '/dev/ttyUSB0'

#  ///
# <' \___/|
#  \_  _/
#    \ \
# THIS IS WHAT THE GLIDER UPDATES
# THIS IS WHAT THE GLIDER UPDATES
# init glider sensor values waiting for as None
m_present_time_norm = None # 2
m_heading_rad       = None # 3
m_avg_speed         = None # 4
m_water_vel_dir_rad = None # 5
m_water_vel_mag     = None # 6
m_dr_time           = None # 7
m_lat               = None # 8
m_lon               = None # 9

port = serial.Serial(port_address, baudrate=baud)
x = extctl(port_address)

while done_with_for_loop == 0:
    #print('start while')
    cur_line = str(port.readline())     # full line coming from glider
    #print(f'cur_line: {cur_line}')     # view full line if viewed from RasPi
    msg = cur_line.split('*')           # Split into separate fields
    fields = msg[0].split(',')          # Split into separate fields
    # print(f'{datetime.datetime.now()}: Fields: {fields}')   # see fields not cur_line

    # number must match index number in extctl.ini
    for subscription in fields:
        if '2:' in subscription:              # index number of m_present_time_epoc
            subs = subscription.split(':')    # from TWR
            m_present_time_epoc = float(subs[1])       
            m_present_time_norm = datetime.datetime.fromtimestamp(m_present_time_epoc) # convert to human timestamp 
            print(f'found 2 = {m_present_time_norm}')

        if '3:' in subscription:              # index number of m_heading
            subs = subscription.split(':')    # from TWR
            m_heading_rad = float(subs[1])       
            print(f'found 3 = {m_heading_rad}')
            m_heading_deg = math.degrees(m_heading_rad)

        if '4:' in subscription:              # index number of m_water_vel_mag 
            subs = subscription.split(':')    # from TWR
            m_avg_speed = float(subs[1])      
            print(f'found 4 = {m_avg_speed}')
        
        if '5:' in subscription:              # index number of m_avg_speed
            subs = subscription.split(':')    # from TWR
            m_water_vel_dir_rad = float(subs[1])  # 
            print(f'found 5 = {m_water_vel_dir_rad}')
            m_water_vel_dir_deg = math.degrees(m_water_vel_dir_rad)

        if '6:' in subscription:              # index number of m_water_vel_mag
            subs = subscription.split(':')    # from TWR
            m_water_vel_mag = float(subs[1])  # 
            print(f'found 6 = {m_water_vel_mag}')

        if '7:' in subscription:              # index number of m_water_vel_mag
            subs = subscription.split(':')    # from TWR
            m_dr_time = float(subs[1])   
            print(f'found 7 = {m_dr_time}')

        if '8:' in subscription:              # index number of m_water_vel_mag
            subs = subscription.split(':')    # from TWR
            m_lat = float(subs[1]) 
            print(f'found 8 = {m_lat}')

        if '9:' in subscription:              # index number of m_water_vel_mag
            subs = subscription.split(':')    # from TWR
            m_lon = float(subs[1])
            print(f'found 9 = {m_lon}')
        
    if (m_present_time_norm		!= None) and \
        (m_heading_rad 			!= None) and \
        (m_avg_speed 			!= None) and \
        (m_water_vel_dir_rad 	!= None) and \
        (m_water_vel_mag 		!= None) and \
        (m_dr_time 				!= None) and \
        (m_lat					!= None) and \
        (m_lon					!= None):
        
        #print(m_present_time_norm,m_heading_rad,m_avg_speed,m_water_vel_dir_rad,m_water_vel_mag,m_dr_time,m_lat,m_lon)
        
        print(f'{datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}_values present, lets go!')
        # x.write_TXT(values_present)
        m_dr_time = (3600*3)
        # make m_lat and m_lon computer readable
        m_lat_deg = float((str(m_lat))[:2])
        m_lat_min = (float((str(m_lat))[2:]))/60
        m_lat_map = round((m_lat_deg + m_lat_min),4)

        m_lon_deg = float((str(m_lon))[:3])
        m_lon_min = (float((str(m_lon))[3:]))/60
        m_lon_map = round((m_lon_deg - m_lon_min),4)

        print(f'Lat: {m_lat_map} | Lon: {m_lon_map}')
        # print('whatthefuck')
        # Calculate time and distance for angles_deg
        for angle in angles_deg:
            theory_heading = math.radians(angle)
            final_vel_mag_mps, final_vel_dir_rad, deflection_distance_km = what_is_best_heading(m_dr_time, m_avg_speed, theory_heading, m_water_vel_dir_rad, m_water_vel_mag)
            final_vel_mag_mps_list.append(final_vel_mag_mps)  # Considering total distance traveled downstream
            final_vel_dir_rad_list.append(final_vel_dir_rad)
            deflection_distance_km_list.append(deflection_distance_km)

            current_distance = ((final_vel_mag_mps)*(m_dr_time*3600))/1000 # results in km
            glider_positions_list.append((current_distance * math.cos(final_vel_dir_rad) / LON_TO_KM + m_lon_map,
                                    current_distance * math.sin(final_vel_dir_rad) / (LAT_TO_KM + m_lat_map)))
            
        # Calculate time and distance for angles_deg_all 
        for angle in angles_deg_all:
            theory_heading = math.radians(angle)
            # last segment hours, for inset
            final_vel_mag_mps_all, final_vel_dir_rad_all, deflection_distance_km_all = what_is_best_heading(m_dr_time, m_avg_speed, theory_heading, m_water_vel_dir_rad, m_water_vel_mag)
            final_vel_mag_mps_list_all.append(final_vel_mag_mps_all)  # Considering total distance traveled downstream
            final_vel_dir_rad_list_all.append(final_vel_dir_rad_all)
            deflection_distance_km_list_all.append(deflection_distance_km_all)

            current_distance_all = ((final_vel_mag_mps_all)*(m_dr_time*3600))/1000 # results in km
            glider_positions_list_all.append((current_distance_all * math.cos(final_vel_dir_rad_all) / LON_TO_KM + m_lon_map,
                                    current_distance_all * math.sin(final_vel_dir_rad_all) / (LAT_TO_KM + m_lat_map)))

            # 12 location plot
            final_vel_mag_mps_12, final_vel_dir_rad_12, deflection_distance_km_12 = what_is_best_heading(m_dr_time_12, m_avg_speed, theory_heading, m_water_vel_dir_rad, m_water_vel_mag)
            final_vel_mag_mps_list_12.append(final_vel_mag_mps_12)  # Considering total distance traveled downstream
            final_vel_dir_rad_list_12.append(final_vel_dir_rad_12)
            deflection_distance_km_list_12.append(deflection_distance_km_12)

            current_distance_12 = ((final_vel_mag_mps_12)*(m_dr_time_12*3600))/1000 # results in km
            glider_positions_list_12.append((current_distance_12 * math.cos(final_vel_dir_rad_12) / LON_TO_KM + m_lon_map,
                                    current_distance_12 * math.sin(final_vel_dir_rad_12) / LAT_TO_KM + m_lat_map))
        
        # DataFrame from the lists
        three_hr_dataframe = pd.DataFrame({
            'final_vel_mag_mps': final_vel_mag_mps_list,
            'final_vel_dir_rad': final_vel_dir_rad_list,
            'deflection_distance_km': deflection_distance_km_list})

        angles_index = pd.Index(angles_deg)
        angles_index_12 = pd.Index(angles_deg_all)

        # Set the 'angles' list as the index of the DataFrame
        three_hr_dataframe.index = angles_index

        # Find the index of the minimum deflect distance
        min_deflect_index_loc = three_hr_dataframe['deflection_distance_km'].idxmin()

        # Retrieve the corresponding heading value
        heading_with_min_deflection = min_deflect_index_loc
        # NEEDS FLOAT BEFORE THE PATH PLOTTING
        # Convert heading_with_min_deflection to a float value
        heading_with_min_deflection_deg = int(heading_with_min_deflection)
        heading_with_min_deflection_rad = (math.radians(heading_with_min_deflection_deg))
        
        # theoretical heading 90 degrees from current
        # THUS MUST BE AN ABSOLUTE VALUE AND NOT HAVE .9812734891234 CUZ THAT IS NOT IN THE THEORY ANGLES
        # LATE NIGHT SOPHIE FTWWWWWWWWW
        theory_m_heading = int(abs(((m_water_vel_dir_deg + 90) % 360))) 
        # print(f'theory{theory_m_heading}')

        ##### ##### ##### ##### ##### ##### 
        ##  THREE HOUR SEGMENT (INSET)
        # theory_loc of glider if it flew true 90 deg from current @ glider speed
        
        glider_positions = pd.DataFrame(glider_positions_list,index=angles_index)   # put in dataframe
        glider_positions_all = pd.DataFrame(glider_positions_list_all,index=angles_index_12)   # put in dataframe
        theory_dist = m_avg_speed * 3600 * m_dr_time    # km
        
        theory_lon = theory_dist * math.cos(theory_m_heading) / LON_TO_KM + m_lon_map
        theory_lat = theory_dist * math.sin(theory_m_heading) / LAT_TO_KM + m_lat_map

        # location of glider at 90 deg true IRRESPECTIVE OF CURRENT
        ninety_loc_lat = glider_positions.loc[90,1]
        ninety_loc_lon = glider_positions.loc[90,0]

        
        # location of glider at 90 deg from current (RED)
        ninety_current_loc_lat = glider_positions_all.loc[theory_m_heading,1]
        ninety_current_loc_lon = glider_positions_all.loc[theory_m_heading,0]
        # location of glider at optimal heading (GREEN)
        optimal_loc_lat = glider_positions.loc[heading_with_min_deflection_deg,1]
        optimal_loc_lon = glider_positions.loc[heading_with_min_deflection_deg,0]
        
        # Calculate distances
        distance_theory_ninety = round(haversine(theory_lon, theory_lat, ninety_loc_lon, ninety_loc_lat),1)
        distance_theory_optimal = round(haversine(theory_lon, theory_lat, optimal_loc_lon, optimal_loc_lat),1)
        diff = abs(round(distance_theory_optimal-distance_theory_ninety,1) ) 
        
        ##### ##### ##### ##### ##### ##### 
        ## LONGER HOUR SEGMENT (BIG MAP)
        # theory_loc of glider if it flew true 90 deg from current @ glider speed
        glider_positions_list_12_df = pd.DataFrame(glider_positions_list_12,index=angles_index_12)   # put in dataframe
        theory_dist_12 = m_avg_speed * 3600 * m_dr_time_12 # km

        theory_lon = theory_dist_12 * math.cos(theory_m_heading) / LON_TO_KM + m_lon_map
        theory_lat = theory_dist_12 * math.sin(theory_m_heading) / LAT_TO_KM + m_lat_map

        # location of glider at 90 deg from current (RED)
        ninety_true_loc_lat_12 = (glider_positions_list_12_df.loc[90,1])
        ninety_true_loc_lon_12 = (glider_positions_list_12_df.loc[90,0])
        print(f'ninety_true_loc_lat_12{ninety_true_loc_lat_12}')
        # location of glider at 90 deg from current (RED)
        ninety_loc_lat_12 = glider_positions_list_12_df.loc[theory_m_heading,1]
        ninety_loc_lon_12 = glider_positions_list_12_df.loc[theory_m_heading,0]

        # location of glider at optimal heading (GREEN)
        optimal_loc_lat_12 = glider_positions_list_12_df.loc[heading_with_min_deflection_deg,1]
        optimal_loc_lon_12 = glider_positions_list_12_df.loc[heading_with_min_deflection_deg,0]

        # Calculate distances
        distance_theory_ninety_12 = round(haversine(theory_lon, theory_lat, ninety_loc_lon_12, ninety_loc_lat_12),2)
        distance_theory_optimal_12 = round(haversine(theory_lon, theory_lat, optimal_loc_lon_12, optimal_loc_lat_12),2)
        diff_12 = abs(round(distance_theory_optimal_12-distance_theory_ninety_12,1))

        ##### ##### ##### ##### ##### #####
        print(f'{datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}_data done, starting figure')
        # x.write_TXT(data_done)
        ##### ##### ##### ##### ##### ##### 

        # Cartopy map with Plate Carree projection for larger map
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

        # Set the extent for the larger map
        map_extent = [-88, -84, 19, 22]  # Adjust as needed
        ax.set_extent(map_extent, crs=ccrs.PlateCarree())

        # Adding coastline, land, and other features to the larger map
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.LAND, facecolor='burlywood', edgecolor='black')
        ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
        ax.set_facecolor('lightblue')

        ax_inset = fig.add_axes([0.54, 0.06, 0.52, 0.52], projection=ccrs.PlateCarree())

        map_buff = 0.08
        ax_inset.set_extent([m_lon_map-0.04,
                    m_lon_map+map_buff,
                    m_lat_map+map_buff,
                    m_lat_map-0.06
                    ], crs=ccrs.PlateCarree())  # Adjusted extent to include more land

        # Scales for all arrows
        scale_arrows = 2
        scale_arrows_inset = 20

        ##### ##### ##### ##### ##### ##### 
        # LOCATION OF GLIDER
        ax.plot(m_lon_map, m_lat_map,color='black', markersize=6,label=f'Location & Prior heading',zorder=9) #(86.5W, 21N)
        ax_inset.plot(m_lon_map, m_lat_map,color='black', markersize=4,zorder=9) #(86.5W, 21N)
        ##### ##### ##### ##### ##### ##### 


        ##### ##### ##### ##### ##### ##### 
        # BLACK ARROW - prior heading 
        # Convert m_heading to delta_lon and delta_lat
        delta_heading_lon = math.sin((m_heading_rad))   # gotta be rad bro *hang loose*
        delta_heading_lat = math.cos((m_heading_rad))   # radians

        # Plotting the m_heading vector originating from the starting point
        ax.quiver(m_lon_map, m_lat_map, delta_heading_lon, delta_heading_lat,
                angles='uv', scale_units='xy', scale=scale_arrows, color='black',zorder=1)
        ax_inset.quiver(m_lon_map, m_lat_map, delta_heading_lon, delta_heading_lat,
                angles='uv', scale_units='xy', scale=scale_arrows_inset, color='black',zorder=1)
        ##### ##### ##### ##### ##### ##### 


        ##### ##### ##### ##### ##### ##### 
        # GRAY ARROW - current vector
        delta_current_lon = math.sin(m_water_vel_dir_rad)
        delta_current_lat = math.cos(m_water_vel_dir_rad)
        # Plotting the current vector originating from the starting point
        ax.quiver(m_lon_map, m_lat_map, delta_current_lon, delta_current_lat,
                angles='uv', scale_units='xy', scale=scale_arrows, color='gray', label=f'Ocean Current',zorder=2)
        ax_inset.quiver(m_lon_map, m_lat_map, delta_current_lon, delta_current_lat,
                angles='uv', scale_units='xy', scale=scale_arrows_inset, color='gray',zorder=2)
        ##### ##### ##### ##### ##### ##### 


        ##### ##### ##### ##### ##### ##### 
        # BIG GREEN ARROW - heading with min deflection
        # Convert heading_with_min_deflection to delta_lon and delta_lat for plotting
        heading_delta_lon = math.sin(heading_with_min_deflection_rad)
        heading_delta_lat = math.cos(heading_with_min_deflection_rad)

        # Plotting the heading_with_min_deflection vector originating from the starting point
        ax.quiver(m_lon_map, m_lat_map, heading_delta_lon, heading_delta_lat,
                angles='uv', scale_units='xy', scale=scale_arrows, color='green', label=f'Optimal heading: {heading_with_min_deflection:.1f}°',zorder=1)
        # Plotting the heading_with_min_deflection vector originating from the starting point
        ax_inset.quiver(m_lon_map, m_lat_map, heading_delta_lon, heading_delta_lat,
                angles='uv', scale_units='xy', scale=scale_arrows_inset, color='green',zorder=1)
        ##### ##### ##### ##### ##### ##### 


        ##### ##### ##### ##### ##### ##### 
        # BIG MAP location of the glider (blue circle representing all possible terminations of COG based on headings)
        path_lon_map, path_lat_map = zip(*glider_positions_list_12)
        ax.plot(path_lon_map, path_lat_map, color='blue',linewidth=2,label=f'Glider COG terminations\nfor all headings\n(Inset 0{angles_deg[0]}°-{angles_deg[-1]}°)',zorder=9)

        # INSET 
        # plot all angles possible circle in light blue
        path_lon_inset_all, path_lat_inset_all = zip(*glider_positions_list_all)
        ax_inset.plot(path_lon_inset_all, path_lat_inset_all, color='lightblue',linewidth=1,zorder=1)

        # plot only angles 045-135 in darker blue
        path_lon_inset, path_lat_inset = zip(*glider_positions_list)
        ax_inset.plot(path_lon_inset, path_lat_inset, color='blue',linewidth=2,zorder=9) #label=f'Glider path terminations\nfor headings 0{angles_deg[0]}°-{angles_deg[-1]}°'
        ##### ##### ##### ##### ##### ##### 


        ##### ##### ##### ##### ##### ##### 
        # BIG MAP
        # RED: 90deg true east
        ax.scatter(ninety_true_loc_lon_12,ninety_true_loc_lat_12,label='Location @ 090° true',color='red',zorder=10) # ONLY FOR LEGEND
        ax.plot([ninety_true_loc_lon_12, m_lon_map], [ninety_true_loc_lat_12, m_lat_map],color='red',linestyle='--')

        # ORANGE: 90deg from current
        ax.scatter(ninety_loc_lon_12,ninety_loc_lat_12,color='orange',label='Location @ 090° from current',zorder=10)
        ax.plot([ninety_loc_lon_12, m_lon_map], [ninety_loc_lat_12, m_lat_map],color='orange',linestyle='--')

        # GREEN: 
        ax.scatter(optimal_loc_lon_12,optimal_loc_lat_12,color='green',label=f'Location @ {int(heading_with_min_deflection_deg)}°',zorder=10)
        ax.plot([optimal_loc_lon_12, m_lon_map], [optimal_loc_lat_12, m_lat_map],color='green',linestyle='--')
        ##### ##### ##### ##### ##### ##### 


        ##### ##### ##### ##### ##### ##### 
        # INSET
        # RED: 90deg true east
        ax_inset.scatter(ninety_loc_lon,ninety_loc_lat,color='red',zorder=10)
        ax_inset.plot([ninety_loc_lon, m_lon_map], [ninety_loc_lat, m_lat_map],color='red',linestyle='--')

        # ORANGE: 90deg from current
        ax_inset.scatter(ninety_current_loc_lon,ninety_current_loc_lat,color='orange',zorder=10)
        ax_inset.plot([ninety_current_loc_lon, m_lon_map], [ninety_current_loc_lat, m_lat_map],color='orange',linestyle='--')

        # GREEN: optimal heading location
        ax_inset.scatter(optimal_loc_lon,optimal_loc_lat,color='green',zorder=10)
        ax_inset.plot([optimal_loc_lon, m_lon_map], [optimal_loc_lat, m_lat_map],color='green',linestyle='--')
        ##### ##### ##### ##### ##### ##### 


        # legend label
        label=f'\n$\mathbf{{Last\ Segment}}$\nTime: {round(m_dr_time,3)}hrs\nGlider: {round(m_heading_deg,3)}° @ {round(m_avg_speed,3)}m/s\nCurrent: {round(m_water_vel_dir_deg,3)}° @ {round(m_water_vel_mag,3)}m/s'
        dummy_plot = ax.plot([], [], color='white', marker='', linestyle='-', label=label)

        ax.set_title(f'Optimal Glider Heading Calculation ({m_dr_time_12}hr plot)',fontsize=14)
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.legend()
        plt.tight_layout() #has errors 

        # where to save plot data on RP
        file_path = "/home/rutgers/backseat_driver/plots/"  

        # used for filenames
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

        # save plot image
        print('saving figure...')
        plt.savefig(f"{file_path}{current_time}_optimal_glider_heading_calculation.png")
        print(f'{datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}_figure_saved!')
        # x.write_TXT(plot_done)

        ##############################################################################################################################
        # and finally, update heading on glider based upon 
        # 270 - 45 - optimal heading
        # 45 - 90 use 90 deg from current
        # 90 - 270 - use heading of 90

        if 270 <= m_water_vel_dir_deg < 360 or 0 <= m_water_vel_dir_deg < 90: #was 45
            # use optimal heading
            new_heading_send = np.round(heading_with_min_deflection_rad,3)       # round to three digits #.## because we don't need all
            x.write_SW(0,new_heading_send)                                       # change heading on glider
            x.write_TXT(new_heading_send)                                        # print message in glider terminal
            print(f'{current_time}: new_heading(270-45) = {math.degrees(new_heading_send)}T') # print new heading with timestamp in RP terminal
                
        # elif 45 <= m_water_vel_dir_deg < 90:
        #     # use 90 degrees from current (relative to current)
        #     new_heading_send = np.round(math.radians(m_water_vel_dir_deg + 90),3)
        #     x.write_SW(0,new_heading_send)                                       # change heading on glider
        #     x.write_TXT(new_heading_send)                                        # print message in glider terminal
        #     print(f'{current_time}: new_heading(45-90) = {math.degrees(new_heading_send)}T') # print new heading with timestamp in RP terminal
             
        elif 90 <= m_water_vel_dir_deg < 270:
            # use 90 degrees (due east)
            new_heading_send = math.radians(90)
            x.write_SW(0,new_heading_send)                                       # change heading on glider
            x.write_TXT(new_heading_send)                                        # print message in glider terminal
            print(f'{current_time}: new_heading(90-270) = 90T') # print new heading with timestamp in RP terminal
             
        else:
            x.write_TXT(er_m_water_vel_dir)
            pass

        done_with_for_loop = 1 # true, finish while loop and done with script

timer_end = datetime.datetime.now()
script_time = timer_end - timer_start
elapsed_seconds = str(round(script_time.total_seconds(),2))

with open('script_times.txt','a') as file:
    file.write(f'{elapsed_seconds}\n')

x.write_TXT(all_done)
print(f'script is done! ({elapsed_seconds}s)')

# serial.Serial(port_address, baudrate=baud).close()
