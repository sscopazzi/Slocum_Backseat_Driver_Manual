behavior_name=goto_list 
#============================================================ 
# --- goto_l10.ma
# Generated for 023 by OpenCPN2goto.py from endurance_line.csv at Oct 21 2023 21:38:37 
# 200m Satisfying Radius
#============================================================

<start:b_arg>
    b_arg: num_legs_to_run(nodim)   -1    # loop through waypoints
    b_arg: start_when(enum)          0    # BAW_IMMEDIATELY
    b_arg: list_stop_when(enum)      7    # BAW_WHEN_WPT_DIST

    # SATISFYING RADIUS
      b_arg:  list_when_wpt_dist(m)  200

    # LIST PARAMETERS                  LON     LAT
      b_arg: initial_wpt(enum)       -07300.0    3850.2    # First wpt in list
      b_arg: num_waypoints(nodim)    5                # Number of waypoints in list
<end:b_arg>

<start:waypoints>
#     LON     LAT      �T         name
    -07300.0    3850.2   # 088  |  end
    -07318.8    3900.0   # 304  |  NM003
    -07335.6    3908.3   # 302  |  middle
    -07353.3    3917.3   # 303  |  unnamed
    -07411.5    3927.0   # 305  |  start
<end:waypoints>

# File generated from endurance_line.csv using OpenCPN2goto.py
# The endurance_line.html has the same waypoints as this goto file
# If it looks weird in the HTML something went wrong (are you sure the route is good in OpenCPN?)