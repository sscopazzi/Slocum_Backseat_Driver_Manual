behavior_name=sample

# sample01.ma (CTD)

<start:b_arg>
    b_arg: sensor_type(enum)                    1   # c_profile_on, is CTD
    b_arg: sample_time_after_state_change(s)    0   # start sampling right away

    # Sampling Arguments
        b_arg: intersample_time(sec)    		1   # if < 0 then off, if = 0 then fast as posible, > 0 secs
        b_arg: state_to_sample(enum)    		15   # 7 diving|hovering|climbing, 15 all
		b_arg: nth_yo_to_sample(nodim)			1 	# After the first yo, sample only
											# on every nth yo. If argument is
											# negative then exclude first yo
<end:b_arg>