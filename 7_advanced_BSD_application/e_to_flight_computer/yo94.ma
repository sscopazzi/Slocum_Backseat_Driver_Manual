behavior_name=yo

<start:b_arg>
	# Number of yo's: -1 infinite, n half-yos
	b_arg:  num_half_cycles_to_do(nodim)		-1

    ### DIVE_TO ARGUMENTS ###
	# Depth Arguments
		b_arg:  d_target_depth(m)       		995 
		b_arg:  d_target_altitude(m)    		-1
	# Ballast Pump Controls (absolute)
		b_arg:  d_use_bpump(enum)    			2
		b_arg:  d_bpump_value(X)     			-300.0
	# Thruster
		# b_arg: d_use_thruster(enum)			0		
		# b_arg: d_thruster_value(X)   			0.0		
		# b_arg: d_depth_rate_method(enum)		3		
	# Dive Angle
		b_arg:  d_use_pitch(enum)   			3		# 3 AP, 1 BP
		b_arg:  d_pitch_value(X)    			-0.39
	# Dive Stuck Scenario
		b_arg:  d_stop_when_stalled_for(sec)    90
		b_arg:  d_stop_when_hover_for(sec)      90

    ### CLIMB_TO ARGUMENTS ###
	# Depth Arguments
		b_arg:  c_target_depth(m)       		15   ### visual flag ###
		b_arg:  c_target_altitude(m)    		-1
	# Ballast Pump Controls (absolute)
		b_arg:  c_use_bpump(enum)    			2
		b_arg:  c_bpump_value(X)     			300.0
	# Thruster
		#b_arg: c_use_thruster(enum)   			0		#
		#b_arg: c_thruster_value(X)   			0.0		#
	# Climb Angle
		b_arg:  c_use_pitch(enum)   			3		# 3 AP, 1 BP
		b_arg:  c_pitch_value(X)    			0.39
	# Climb Stuck Scenario
		b_arg:  c_stop_when_stalled_for(sec)    90
		b_arg:  c_stop_when_hover_for(sec)      90
		
<end:b_arg>