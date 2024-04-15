behavior_name=goto_list 
#============================================================ 
# --- goto_l93.ma

<start:b_arg>
    b_arg: num_legs_to_run(nodim)   -1    # loop through waypoints
    b_arg: start_when(enum)          0    # BAW_IMMEDIATELY
    b_arg: list_stop_when(enum)      7    # BAW_WHEN_WPT_DIST
	b_arg: initial_wpt(enum)	     0    # 0 to n-1, -1 first after last, -2 closest

    # SATISFYING RADIUS
      b_arg:  list_when_wpt_dist(m)  1000 # this may be important later

    # LIST PARAMETERS                  LON     LAT
      b_arg: initial_wpt(enum)       0   # first (only) wpt in list
      b_arg: num_waypoints(nodim)    1                	# number of waypoints in list
<end:b_arg>

<start:waypoints>
#     LON     LAT            name
#   -8630.0    2100.0    |  location of simulation start
    -2522.0    2100.0    |  far far away (westernmost point of Africa)
 
<end:waypoints>

# head due east of Yucatan 