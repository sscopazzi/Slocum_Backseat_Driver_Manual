behavior_name=sample

# SAMPLE90.MA (EXTCTL)

<start:b_arg>
    b_arg: sensor_type(enum)                    90  # c_extctl_on
    b_arg: sample_time_after_state_change(s)    0   # start sampling right away

    # Sampling Arguments
        b_arg: intersample_time(sec)    0 	# if < 0 then off, if = 0 then fast as posible, >0 that number
        b_arg: state_to_sample(enum)    15  	# 
		b_arg: nth_yo_to_sample(nodim)	1  	# +n: first and nth: 1,3,5 
											# -n: exclude first: 2,4,6
<end:b_arg>

												# 1  diving
                                                # 2  hovering
                                                # 3  diving|hovering
                                                # 4  climbing
                                                # 5  diving|climbing
                                                # 6  hovering|climbing
                                                # 7  diving|hovering|climbing
                                                # 8  on_surface
                                                # 9  diving|on_surface
                                                # 10 hovering|on_surface
                                                # 11 diving|hovering|on_surface
                                                # 12 climbing|on_surface
                                                # 13 diving|climbing|on_surface
                                                # 14 hovering|climbing|on_surface
                                                # 15 diving|hovering|climbing|on_surface