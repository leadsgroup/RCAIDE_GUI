from utilities import Units

import RCAIDE.Framework.Mission.Segments as Segments

segment_data_fields = [
    { # Climb Subsegments
        "Constant CAS/Constant Rate": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Climb Rate", Units.Velocity, "climb_rate"), 
            ("CAS", Units.Velocity, "calibrated_air_speed"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Dynamic Pressure/Constant Angle": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Climb Angle", Units.Angle, "climb_angle"), 
            ("Dynamic Pressure", Units.Pressure, "dynamic_pressure"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Dynamic Pressure/Constant Rate": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Climb Rate", Units.Velocity, "climb_rate"), 
            ("Dynamic Pressure", Units.Pressure, "dynamic_pressure"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant EAS/Constant Rate": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Climb Rate", Units.Velocity, "climb_rate"), 
            ("EAS", Units.Velocity, "equivalent_air_speed"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Mach/Constant Angle": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Climb Angle", Units.Angle, "climb_angle"), 
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Mach/Constant Rate": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Climb Rate", Units.Velocity, "climb_rate"), 
            ("Mach Number", Units.Unitless, "mach_number"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Mach/Linear Altitude": [
            ("Mach Number", Units.Unitless, "mach_number"), 
            ("Distance", Units.Length, "distance"),
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Speed/Constant Angle Noise": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Climb Angle", Units.Angle, "climb_angle"), 
            ("Air Speed", Units.Velocity, "air_speed"),
            ("True Course Speed", Units.Velocity, "true_course_speed")
        ],
        "Constant Speed/Constant Angle": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Climb Angle", Units.Angle, "climb_angle"), 
            ("Air Speed", Units.Velocity, "air_speed"),
            ("True Course Speed", Units.Velocity, "true_course_speed")
        ],
        "Constant Speed/Constant Rate": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Climb Rate", Units.Velocity, "climb_rate"), 
            ("Air Speed", Units.Velocity, "air_speed"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Speed/Linear Altitude": [
            ("Air Speed", Units.Velocity, "air_speed"), 
            ("Distance", Units.Length, "distance"),
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Throttle/Constant Speed": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Throttle", Units.Unitless, "throttle"), 
            ("Air Speed", Units.Velocity, "air_speed"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Linear Mach/Constant Rate": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Climb Rate", Units.Velocity, "climb_rate"), 
            ("Mach Number End", Units.Unitless, "mach_number_end"),
            ("Mach Number Start", Units.Unitless, "mach_number_start"), 
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Linear Speed/Constant Rate": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Climb Rate", Units.Velocity, "climb_rate"), 
            ("Air Speed Start", Units.Velocity, "air_speed_start"),
            ("Air Speed End", Units.Velocity, "air_speed_end"), 
            ("True Course Angle", Units.Angle, "true_course")
        ],
    }, 
    {
        # Cruise Subsegments
        "Constant Acceleration/Constant Altitude": [
            ("Altitude", Units.Length, "altitude"), 
            ("Acceleration", Units.Acceleration, "acceleration"),
            ("Air Speed Start", Units.Velocity, "air_speed_start"),
            ("Air Speed End", Units.Velocity, "air_speed_end"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Dynamic Pressure/Constant Altitude Loiter": [
            ("Altitude", Units.Length, "altitude"),
            ("Dynamic Pressure", Units.Pressure, "dynamic_pressure"),
            ("Time", Units.Time, "time"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Dynamics Pressure/Constant Altitude": [
            ("Altitude", Units.Length, "altitude"),
            ("Acceleration", Units.Acceleration, "acceleration"),
            ("Air Speed Start", Units.Velocity, "air_speed_start"),
            ("Air Speed End", Units.Velocity, "air_speed_end"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Mach/Constant Altitude Loiter": [
            ("Altitude", Units.Length, "altitude"), 
            ("Mach Number", Units.Unitless, "mach_number"),
            ("Time", Units.Time, "time"), 
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Mach/Constant Altitude": [
            ("Altitude", Units.Length, "altitude"), 
            ("Mach Number", Units.Unitless, "mach_number"),
            ("Distance", Units.Length, "distance"), 
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Pitch Rate/Constant Altitude": [
            ("Altitude", Units.Length, "altitude"), 
            ("Pitch Rate", Units.Velocity, "pitch_rate"),
            ("Pitch Initial", Units.Angle, "pitch_initial"), 
            ("Pitch Final", Units.Angle, "pitch_final"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Speed/Constant Altitude Loiter": [
            ("Altitude", Units.Length, "altitude"), 
            ("Air Speed", Units.Velocity, "air_speed"),
            ("Time", Units.Time, "time"), 
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Speed/Constant Altitude": [
            ("Altitude", Units.Length, "altitude"), 
            ("Air Speed", Units.Velocity, "air_speed"),
            ("Distance", Units.Length, "distance"), 
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Throttle/Constant Altitude": [
            ("Throttle", Units.Unitless, "throttle"), 
            ("Altitude", Units.Length, "altitude"),
            ("Air Speed Start", Units.Velocity, "air_speed_start"), 
            ("Air Speed End", Units.Velocity, "air_speed_end"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
    }, 
    {
        # Descent Subsegments
        "Constant CAS/Constant Rate": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Descent Rate", Units.Velocity, "descent_rate"), 
            ("CAS", Units.Velocity, "calibrated_air_speed"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant EAS/Constant Rate": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Descent Rate", Units.Velocity, "descent_rate"), 
            ("EAS", Units.Velocity, "equivalent_air_speed"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Speed/Constant Angle Noise": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Descent Angle", Units.Angle, "descent_angle"), 
            ("Air Speed", Units.Velocity, "air_speed"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Speed/Constant Angle": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Descent Angle", Units.Angle, "descent_angle"), 
            ("Air Speed", Units.Velocity, "air_speed"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Speed/Constant Rate": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Descent Rate", Units.Velocity, "descent_rate"), 
            ("Air Speed", Units.Velocity, "air_speed"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Linear Mach/Constant Rate": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Descent Rate", Units.Velocity, "descent_rate"), 
            ("Mach Number End", Units.Unitless, "mach_number_end"),
            ("Mach Number Start", Units.Unitless, "mach_number_start"), 
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Linear Speed/Constant Rate": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"),
            ("Descent Rate", Units.Velocity, "descent_rate"), 
            ("Air Speed Start", Units.Velocity, "air_speed_start"),
            ("Air Speed End", Units.Velocity, "air_speed_end"), 
            ("True Course Angle", Units.Angle, "true_course")
        ],
    }, 
    {
        # Ground Subsegments
        "Landing": [
            ("Velocity Start", Units.Velocity, "velocity_start"), 
            ("Velocity End", Units.Velocity, "velocity_end"), 
            ("Friction Coefficient", Units.Unitless, "friction_coefficient"),
            ("Throttle", Units.Angle, "throttle"),
            ("Altitude", Units.Length, "altitude"),
            ("Reverse Thrust Ratio", Units.Unitless, "reverse_thrust_ratio"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Takeoff": [
            ("Ground Incline", Units.Angle, "ground_incline"),
            ("Velocity Start", Units.Velocity, "velocity_start"), 
            ("Velocity End", Units.Velocity, "velocity_end"), 
            ("Friction Coefficient", Units.Unitless, "friction_coefficient"),
            ("Throttle", Units.Unitless, "throttle"),
            ("Altitude", Units.Length, "altitude"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Battery Discharge": [
            ("Altitude", Units.Length, "altitude"), 
            ("Time", Units.Time, "time"), 
            ("Current", Units.Unitless, "current"),
            ("Overcharge Contingency", Units.Unitless, "overcharge_contingency"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Battery Recharge": [
            ("Altitude", Units.Length, "altitude"), 
            ("Time", Units.Time, "time"), 
            ("Current", Units.Unitless, "current"),
            ("Overcharge Contingency", Units.Unitless, "overcharge_contingency"),
            ("True Course Angle", Units.Angle, "true_course")
        ]
    }, 
    {
        # Single Point Subsegments
        "Set Speed/Set Altitude/No Propulsion": [
            ("Altitude", Units.Length, "altitude"), 
            ("Air Speed", Units.Velocity, "air_speed"),
            ("Distance", Units.Length, "distance"), 
            ("Acceleration Z", Units.Acceleration, "acceleration_z"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Set Speed/Set Altitude": [
            ("Altitude", Units.Length, "altitude"), 
            ("Air Speed", Units.Velocity, "air_speed"),
            ("Distance", Units.Length, "distance"), 
            ("Acceleration X", Units.Acceleration, "acceleration_x"),
            ("Acceleration Z", Units.Acceleration, "acceleration_z"),
            ("State Numerics Number of Control Points", Units.Unitless, "state_numerics_control_points")
        ],
        "Set Speed/Set Throttle": [
            ("Altitude", Units.Length, "altitude"), 
            ("Air Speed", Units.Velocity, "air_speed"),
            ("Throttle", Units.Unitless, "throttle"), 
            ("Acceleration Z", Units.Acceleration, "acceleration_z"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
    }, 
    {
        # Transition Subsegments
        "Constant Acceleration/Constant Angle/Linear Climb": [
            ("Altitude Start", Units.Length, "altitude_start"),
            ("Altitude End", Units.Length, "altitude_end"),
            ("Air Speed Start", Units.Velocity, "air_speed_start"),
            ("Climb Angle", Units.Angle, "climb_angle"),
            ("Acceleration", Units.Acceleration, "acceleration"),
            ("Pitch Initial", Units.Angle, "pitch_initial"),
            ("Pitch Final", Units.Angle, "pitch_final"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Constant Acceleration/Constant Pitchrate/Constant Altitude": [
            ("Altitude", Units.Length, "altitude"),
            ("Acceleration", Units.Acceleration, "acceleration"),
            ("Air Speed Start", Units.Velocity, "air_speed_start"),
            ("Air Speed End", Units.Velocity, "air_speed_end"),
            ("Pitch Initial", Units.Angle, "pitch_initial"),
            ("Pitch Final", Units.Angle, "pitch_final"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
    }, 
    {
        # Vertical Flight Subsegments
        "Climb": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"), 
            ("Climb Rate", Units.Velocity, "climb_rate"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Descent": [
            ("Altitude Start", Units.Length, "altitude_start"), 
            ("Altitude End", Units.Length, "altitude_end"), 
            ("Descent Rate", Units.Velocity, "descent_rate"),
            ("True Course Angle", Units.Angle, "true_course")
        ],
        "Hover": [
            ("Altitude", Units.Length, "altitude"), 
            ("Time", Units.Time, "time"), 
            ("True Course Angle", Units.Angle, "true_course")
        ]
    }
]

segment_rcaide_classes = [
    { # Climb Subsegments
        "Constant CAS/Constant Rate": Segments.Climb.Constant_CAS_Constant_Rate,
        "Constant Dynamic Pressure/Constant Angle": Segments.Climb.Constant_Dynamic_Pressure_Constant_Angle,
        "Constant Dynamic Pressure/Constant Rate": Segments.Climb.Constant_Dynamic_Pressure_Constant_Rate,
                "Constant EAS/Constant Rate": Segments.Climb.Constant_EAS_Constant_Rate,
        "Constant Mach/Constant Angle": Segments.Climb.Constant_Mach_Constant_Angle,
        "Constant Mach/Constant Rate": Segments.Climb.Constant_Mach_Constant_Rate,
        "Constant Mach/Linear Altitude": Segments.Climb.Constant_Mach_Linear_Altitude,
        "Constant Speed/Constant Angle Noise": Segments.Climb.Constant_Speed_Constant_Angle_Noise,
        "Constant Speed/Constant Angle": Segments.Climb.Constant_Speed_Constant_Angle,
        "Constant Speed/Constant Rate": Segments.Climb.Constant_Speed_Constant_Rate,
        "Constant Speed/Linear Altitude": Segments.Climb.Constant_Speed_Linear_Altitude,
        "Constant Throttle/Constant Speed": Segments.Climb.Constant_Throttle_Constant_Speed,
        "Linear Mach/Constant Rate": Segments.Climb.Linear_Mach_Constant_Rate,
        "Linear Speed/Constant Rate": Segments.Climb.Linear_Speed_Constant_Rate,
    }, 
    {
        # Cruise Subsegments
        "Constant Acceleration/Constant Altitude": Segments.Cruise.Constant_Acceleration_Constant_Altitude,
        "Constant Dynamic Pressure/Constant Altitude Loiter": Segments.Cruise.Constant_Dynamic_Pressure_Constant_Altitude_Loiter,
        "Constant Dynamics Pressure/Constant Altitude": Segments.Cruise.Constant_Dynamic_Pressure_Constant_Altitude,
        "Constant Mach/Constant Altitude Loiter": Segments.Cruise.Constant_Mach_Constant_Altitude_Loiter,
        "Constant Mach/Constant Altitude": Segments.Cruise.Constant_Mach_Constant_Altitude,
        "Constant Pitch Rate/Constant Altitude": Segments.Cruise.Constant_Pitch_Rate_Constant_Altitude,
        "Constant Speed/Constant Altitude Loiter": Segments.Cruise.Constant_Speed_Constant_Altitude_Loiter,
        "Constant Speed/Constant Altitude": Segments.Cruise.Constant_Speed_Constant_Altitude,
        "Constant Throttle/Constant Altitude": Segments.Cruise.Constant_Throttle_Constant_Altitude,
    }, 
    {
        # Descent Subsegments
        "Constant CAS/Constant Rate": Segments.Descent.Constant_CAS_Constant_Rate,
        "Constant EAS/Constant Rate": Segments.Descent.Constant_EAS_Constant_Rate,
        "Constant Speed/Constant Angle Noise": Segments.Descent.Constant_Speed_Constant_Angle_Noise,
        "Constant Speed/Constant Angle": Segments.Descent.Constant_Speed_Constant_Angle,
        "Constant Speed/Constant Rate": Segments.Descent.Constant_Speed_Constant_Rate,
        "Linear Mach/Constant Rate": Segments.Descent.Linear_Mach_Constant_Rate,
        "Linear Speed/Constant Rate": Segments.Descent.Linear_Speed_Constant_Rate,
    }, 
    {
        # Ground Subsegments
        "Landing": Segments.Ground.Landing,
        "Takeoff": Segments.Ground.Takeoff,
        "Battery Discharge": Segments.Ground.Battery_Discharge,
        "Battery Recharge": Segments.Ground.Battery_Recharge
    }, 
    {
        # Single Point Subsegments
        "Set Speed/Set Altitude/No Propulsion": Segments.Single_Point.Set_Speed_Set_Altitude_No_Propulsion,
        "Set Speed/Set Altitude": Segments.Single_Point.Set_Speed_Set_Altitude,
        "Set Speed/Set Throttle": Segments.Single_Point.Set_Speed_Set_Throttle,
    }, 
    {
        # Transition Subsegments
        "Constant Acceleration/Constant Angle/Linear Climb": Segments.Transition.Constant_Acceleration_Constant_Angle_Linear_Climb,
        "Constant Acceleration/Constant Pitchrate/Constant Altitude": Segments.Transition.Constant_Acceleration_Constant_Pitchrate_Constant_Altitude,
    }, 
    {
        # Vertical Flight Subsegments
        "Climb": Segments.Vertical_Flight.Climb,
        "Descent": Segments.Vertical_Flight.Descent,
        "Hover": Segments.Vertical_Flight.Hover,
    }
]