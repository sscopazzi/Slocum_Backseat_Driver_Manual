#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 15 14:48:31 2023

@author: dennis

refs
https://stackoverflow.com/questions/61125808/geopandas-how-to-convert-the-column-geometry-to-string
https://stackoverflow.com/questions/72960340/attributeerror-nonetype-object-has-no-attribute-drvsupport-when-using-fiona
https://gis.stackexchange.com/questions/433460/extracting-latitude-and-longitude-pairs-as-list-from-linestring-in-geopandas
"""
import geopandas as gpd
from shapely.geometry import Point, Polygon
from shapely.geometry import LineString, mapping
from datetime import datetime

import pandas as pd

from fiona.drvsupport import supported_drivers
from shapely import wkt

import sys

def line_to_coords(geom): 
    m = mapping(geom)
    #print(m)
    #list_of_tuples = m['coordinates'] # alternative -> geom.coords[:]
    list_of_tuples =geom.coords[:]
    list_of_lists = list(map(list, list_of_tuples))
    return list_of_lists

def Point_to_gliderstring(point): # convert dec degrees to deg & decimal minutes as strings for the glider in the format DDDMM.MMM , DDMM.MMM
    #these lines format the lat long degrees to fixed lenghth strings with zero padding 3dig for longs 2 dig for lats
    #problem is python counts the -sign in the string size which we don't want
    #so we format them all as positive then add a mius sign as required 
    Long_deg='%003.0f' % abs(int(point[0])) #integer part always positive alys 3 digits zero pad if required 
    Lat_deg='%002.0f' % abs(int(point[1])) #integer part always positive alys 2 digits zero pad if required 
    #now we add a minus sign in front if the value is negative
    if point[1] < 0 : Lat_deg="-"+Lat_deg
    if point[0] < 0 : Long_deg="-"+Long_deg
    #now we add the minutes to the string minutes are always positive
    Long_dec_mins='{:006.3f}'.format((abs(point[0]-int(point[0])) *60))
    Lat_dec_mins='{:006.3f}'.format((abs(point[1]-int(point[1])) *60))
    return Long_deg+Long_dec_mins,Lat_deg+Lat_dec_mins


#ask the user for some input 

source_kml= input('Source KML file [goto.kml] : ')
source_kml = source_kml or 'goto.kml'

glider_name = input('Glider Name [000] : ')
glider_name = glider_name or '000'

initial_wpt = input('intiial wypoint stating with 0 is the first waypoint  [0] : ')
initial_wpt = initial_wpt or '0'

radius = input('satisfying radius(m)  [100] : ')
radius = radius or '100'



savepath="../{}/".format(glider_name)

supported_drivers['KML'] = 'rw'
my_path = gpd.read_file(source_kml, driver='KML')


#  for GE generated paths and CPN generated paths last object is the linestring so we'll work with last object

my_linestring=my_path[-1:]["geometry"].values[0] # extract just the linestring 

coordinate_list=(line_to_coords(my_linestring)) #now extract a coordinte list from the linestring object
print(coordinate_list)
for points in coordinate_list:
   print ("string vals", Point_to_gliderstring(points))
print ("saving file to {}goto_l10.ma".format(savepath))

GotoFile = open(savepath+"goto_l10.ma", "w")



GotoFile.write("behavior_name=goto_list \n")
GotoFile.write("#============================================================ \n")
GotoFile.write("# --- goto_l10.ma             ---\n")
GotoFile.write("# Generated for Unit{} by KML2Goto.py from {} at {} \n".format(glider_name,source_kml,datetime.now().strftime("%b %d %Y %H:%M:%S")))   
GotoFile.write("# {}m Satisfying Radius\n".format(radius))
GotoFile.write("#============================================================\n")
GotoFile.write("\n")
GotoFile.write("<start:b_arg>\n")
GotoFile.write("    b_arg: num_legs_to_run(nodim)   -1    # traverse list once\n")
GotoFile.write("    b_arg: start_when(enum)          0    # BAW_IMMEDIATELY\n")
GotoFile.write("    b_arg: list_stop_when(enum)      7    # BAW_WHEN_WPT_DIST\n")
GotoFile.write("\n")
GotoFile.write("    # SATISFYING RADIUS\n")
GotoFile.write("      b_arg:  list_when_wpt_dist(m)  {}\n".format(radius))
GotoFile.write("\n")
GotoFile.write("    # LIST PARAMETERS\n")
GotoFile.write("      b_arg: initial_wpt(enum)       {}    # First wpt in list\n".format(initial_wpt))
GotoFile.write("      b_arg: num_waypoints(nodim)    {}    # Number of waypoints in list\n".format(len(coordinate_list)))
GotoFile.write("<end:b_arg>\n")
GotoFile.write("\n")
GotoFile.write("<start:waypoints>\n")
for points in coordinate_list:
   Long,Lat = Point_to_gliderstring(points)
   GotoFile.write("    {}   {}\n".format(Long,Lat))
   
GotoFile.write("<end:waypoints>\n")

GotoFile.close()
