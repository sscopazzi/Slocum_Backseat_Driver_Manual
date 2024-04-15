#   ___                    ____ ____  _   _   ____                _        
#  / _ \ _ __   ___ _ __  / ___|  _ \| \ | | |___ \    __ _  ___ | |_ ___  
# | | | | '_ \ / _ \ '_ \| |   | |_) |  \| |   __) |  / _` |/ _ \| __/ _ \ 
# | |_| | |_) |  __/ | | | |___|  __/| |\  |  / __/  | (_| | (_) | || (_) |
#  \___/| .__/ \___|_| |_|\____|_|   |_| \_| |_____|  \__, |\___/ \__\___/ 
#       |_|                                           |___/                

# OpenCPN route -> interactive .html map + goto.ma file for Slocum glider

    # 1) Create route in OpenCPN (may/may not name waypoints)
    # 2) Right click in route editor -> copy
    # 3) Paste into Excel -> Save as .csv
    # 4) Open created [filename].csv file using this .py
    # 5) It will output:
    #   5a) [filename].html for a user interactive (and website postable) map of the route, for ease communicating route and sharing with others
    #   5b) [filename_gotol10.ma] file (includes commented out waypoint names and bearings between)

import numpy as np                  # number processing
from datetime import datetime       # for goto file timestamp 
import pandas as pd                 # data processing
import folium                       # easy html maps, interactive
from folium.features import DivIcon # needed for map labels
from tkinter.filedialog import askopenfilename, askdirectory
import os

################################################################
# ask user for input file, output directory, and two questions #
################################################################
filename = askopenfilename(title='Select .csv File')                        # shows dialog box and returns the path to the selected file
wheresave = askdirectory(title='Select Folder')     # shows dialog box of where to save (returns the path)

# ask user to input glider name/number
glider_name = input('Glider Name [### or Name] (Default is 000) : ')
glider_name = glider_name or '000'

# ask user to input satisfying waypoint distance
radius = input('Satisfying radius(m)  [xxxx] (Default is 100) : ')
radius = radius or '100'

#####################################
# import, manipulate, process route #
#####################################

# import, remove header, and pick columns I want
wantcol = ['Leg','To waypoint','Distance','Bearing','Latitude','Longitude']

raw = pd.read_csv(filename,
                  header=9,
                  usecols=wantcol,
                  index_col=0,
                  sep=',',
                  )

raw['To waypoint'].fillna('unnamed',inplace=True) # replace nan values with a string so waypoint name looping doesn't break

# make loop variable
howmanytoloop = raw.shape[0]
loopnum = range(0,howmanytoloop)

# clean data to proper format
lat = []
lon = []
bear = []
dist = []
name = []
latmap = []
lonmap = []

for i in loopnum : 
    
    # latitude strings
    latdegstr = raw['Latitude'][i][0:2]
    latminstr = raw['Latitude'][i][4:8]
    latns     = raw['Latitude'][i][10]

    # latitude strings to integers for mapping later
    latmaploop = int(float(latdegstr)) + ((int(float(latminstr)))/60)
    if latns == 'S':
        latmaploop = latmaploop * -1
    latmap.append(latmaploop)

    # put strings together into goto10 format
    latloop = latdegstr + latminstr            # degrees + minutes.decimalminutes
    if latns == 'S':                           # check if in southern hemisphere
        latloop = '-' + latloop                # if so make number negative
    lat.append(latloop)                        # append result to lat

   # longitude strings
    londegstr = raw['Longitude'][i][0:3]
    lonminstr = raw['Longitude'][i][5:9]
    lonew     = raw['Longitude'][i][11]

    # longitude strings to integers for mapping later
    lonmaploop = int(float(londegstr)) + ((int(float(lonminstr)))/60)
    if lonew == 'W':
        lonmaploop = lonmaploop * -1
    lonmap.append(lonmaploop)

    lonloop = londegstr + lonminstr        # degrees + minutes.decimalminutes
    if lonew == 'W':                       # check if western
        lonloop = '-' + lonloop            # if so make number negative
    lon.append(lonloop)                    # append result to lon

    bearloop = raw['Bearing'][i][0:3]      # bearing between points 
    bear.append(bearloop)                  # append result

    nameloop = raw['To waypoint'][i][0:]   # name of waypoint
    name.append(nameloop)                  # append

    distloop = raw['Distance'][i][0:3]     # distance between points 
    distloop = int(float(distloop))        # convert string to float and make distloop = 
    distloop = (distloop * (1.852))        # convert nautical miles to kilometer 
    dist.append(distloop)                  # append

coord_list = pd.DataFrame()     # put the above into final dataframe
coord_list['lat'] = lat
coord_list['lon'] = lon
coord_list['name'] = name
coord_list['bearing (T)'] = bear
coord_list['dist (km)'] = dist

#####################################################
# save waypoint list as interactive HTML via Folium #
#####################################################

mapcenter = [(np.max(latmap)+np.min(latmap))/2, (np.max(lonmap)+np.min(lonmap))/2] #set the initial extent of map to min/max of route

f = folium.Figure(width=200, height=200)

map = folium.Map( 
    location=mapcenter,
    zoom_start=8,           # found this to be a good value
    control_scale=True,     # rest allows user interaction
    zoom_control=True,
    scrollWheelZoom=True,
    dragging=True)

for i in loopnum :                                                  # add markers and text to map one at a time (hense for loop)
    folium.Marker([latmap[i],lonmap[i]], popup='{}').add_to(map)    # add markers
    folium.map.Marker(                                              # add waypoint name text
        [latmap[i],lonmap[i]],
        icon=DivIcon(
            icon_size=(30,30),
            icon_anchor=(0,0),
            html='<div style="color:#ffffff;font-size: 12pt">{}</div>'.format(coord_list['name'][i]),
            )
        ).add_to(map)

line_between =[]                        # make line segments connecting the markers
for i in loopnum :
    oneline = [latmap[i],lonmap[i]]
    line_between.append(oneline)

line=folium.PolyLine(                   # put all line segments on map
    locations=line_between,
    weight=3,
    color='#e02525'
    ).add_to(map)

tosplit = os.path.basename(filename)    # get only the '[filename].csv' for export file naming
filename = os.path.split(tosplit)[1]    # take out last split part, which is the selected file
filename = filename[0:-4]               # don't want the .csv in final name

completeHTML_Name = os.path.join(wheresave,filename+'.html')

map.save(completeHTML_Name)  # name of the output file

##############################################
# Export a properly formatted goto10.ma file #
##############################################
# From Joe's KML2Goto.py, changed a bit

gotoFileName = 'goto_l10'
complete_goto_Name = os.path.join(wheresave,gotoFileName+'.ma')

GotoFile = open(complete_goto_Name, 'w')

GotoFile.write('behavior_name=goto_list \n')
GotoFile.write('#============================================================ \n')
GotoFile.write('# --- goto_l10.ma\n')
GotoFile.write('# Generated for {} by OpenCPN2goto.py from {}.csv at {} \n'.format(glider_name,filename,datetime.now().strftime('%b %d %Y %H:%M:%S')))   
GotoFile.write('# {}m Satisfying Radius\n'.format(radius))
GotoFile.write('#============================================================\n')
GotoFile.write('\n')
GotoFile.write('<start:b_arg>\n')
GotoFile.write('    b_arg: num_legs_to_run(nodim)   -1    # loop through waypoints\n')
GotoFile.write('    b_arg: start_when(enum)          0    # BAW_IMMEDIATELY\n')
GotoFile.write('    b_arg: list_stop_when(enum)      7    # BAW_WHEN_WPT_DIST\n')
GotoFile.write('\n')
GotoFile.write('    # SATISFYING RADIUS\n')
GotoFile.write('      b_arg:  list_when_wpt_dist(m)  {}\n'.format(radius))
GotoFile.write('\n')
GotoFile.write('    # LIST PARAMETERS                  LON     LAT\n')
GotoFile.write('      b_arg: initial_wpt(enum)       {}    # First wpt in list\n'.format(lon[0] + '    ' + lat[0]))
GotoFile.write('      b_arg: num_waypoints(nodim)    {}                # Number of waypoints in list\n'.format(len(coord_list)))
GotoFile.write('<end:b_arg>\n')
GotoFile.write('\n')
GotoFile.write('<start:waypoints>\n')
GotoFile.write('#     LON     LAT       T         name\n')
for i in loopnum:
   GotoFile.write('    {}   # {}  |  {}\n'.format((lon[i] + '    ' + lat[i]),(coord_list['bearing (T)'][i]),coord_list['name'][i]))

GotoFile.write('<end:waypoints>')
GotoFile.write('\n')
GotoFile.write('\n')
GotoFile.write('# File generated from {} using OpenCPN2goto.py\n'.format(filename+'.csv'))
GotoFile.write('# The {} has the same waypoints as this goto file\n'.format(filename+'.html'))
GotoFile.write('# If it looks weird in the HTML something went wrong (are you sure the route is good in OpenCPN?)')
GotoFile.close()

print('Processed ' + filename + '.csv')
print('Export to: ' + wheresave)