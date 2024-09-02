from utilities import Units

segment_data_fields = [
    {
        "Constant CAS/Constant Rate": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Climb Rate", Units.Velocity), 
            ("CAS", Units.Velocity),
            ("True Course Angle", Units.Angle)
        ],
        "Constant Dynamic Pressure/Constant Angle": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Climb Angle", Units.Angle), 
            ("Dynamic Pressure", Units.Pressure),
            ("True Course Angle", Units.Angle)
        ],
        "Constant Dynamic Pressure/Constant Rate": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Climb Angle", Units.Angle), 
            ("Dynamic Pressure", Units.Pressure),
            ("True Course Angle", Units.Angle)
        ],
        "Constant EAS/Constant Rate": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Climb Rate", Units.Velocity), 
            ("EAS", Units.Velocity),
            ("True Course Angle", Units.Angle)
        ],
        "Constant Mach/Constant Angle": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Climb Angle", Units.Angle), 
            ("True Course Angle", Units.Angle)
        ],
        "Constant Mach/Constant Rate": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Climb Rate", Units.Velocity), 
            ("Mach Number", Units.Unitless),
            ("True Course Angle", Units.Angle)
        ],
        "Constant Mach/Linear Altitude": [
            ("Mach Number", Units.Unitless), 
            ("Distance", Units.Length),
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("True Course Angle", Units.Unitless)
        ],
        "Constant Speed/Constant Angle Noise": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Climb Angle", Units.Angle), 
            ("Air Speed", Units.Velocity),
            ("True Course Speed", Units.Velocity)
        ],
        "Constant Speed/Constant Angle": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Climb Angle", Units.Angle), 
            ("Air Speed", Units.Velocity),
            ("True Course Speed", Units.Velocity)
        ],
        "Constant Speed/Constant Rate": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Climb Rate", Units.Velocity), 
            ("Speed", Units.Velocity),
            ("True Course Angle", Units.Unitless)
        ],
        "Constant Speed/Linear Altitude": [
            ("Air Speed", Units.Velocity), 
            ("Distance", Units.Length),
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("True Course Angle", Units.Unitless)
        ],
        "Constant Throttle/Constant Speed": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Throttle", Units.Unitless), 
            ("Air Speed", Units.Velocity),
            ("True Course Angle", Units.Unitless)
        ],
        "Linear Mach/Constant Rate": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Climb Rate", Units.Velocity), 
            ("Mach Number End", Units.Unitless),
            ("Mach Number Start", Units.Unitless), 
            ("True Course Angle", Units.Unitless)
        ],
        "Linear Speed/Constant Rate": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Climb Rate", Units.Velocity), 
            ("Air Speed Start", Units.Velocity),
            ("Air Speed End", Units.Velocity), 
            ("True Course Angle", Units.Unitless)
        ],
    }, 
    {
        # Cruise Subsegments
        "Constant Acceleration/Constant Altitude": [
            ("Altitude", Units.Length), 
            ("Acceleration", Units.Acceleration),
            ("Air Speed Start", Units.Velocity),
            ("Air Speed End", Units.Velocity),
            ("True Course Angle", Units.Angle)
        ],
        "Constant Dynamic Pressure/Constant Altitude Loiter": [
            ("Altitude", Units.Length),
            ("Dynamic Pressure", Units.Pressure),
            ("Time", Units.Time),
            ("True Course Angle", Units.Angle)
        ],
        "Constant Dynamics Pressure/Constant Altitude": [
            ("Altitude", Units.Length),
            ("Acceleration", Units.Acceleration),
            ("Air Speed Start", Units.Velocity),
            ("Air Speed End", Units.Velocity),
            ("True Course Angle", Units.Angle)
        ],
        "Constant Mach/Constant Altitude Loiter": [
            ("Altitude", Units.Length), 
            ("Mach Number", Units.Unitless),
            ("Time", Units.Time), 
            ("True Course Angle", Units.Angle)
        ],
        "Constant Mach/Constant Altitude": [
            ("Altitude", Units.Length), 
            ("Mach Number", Units.Unitless),
            ("Distance", Units.Length), 
            ("True Course Angle", Units.Angle)
        ],
        "Constant Pitch Rate/Constant Altitude": [
            ("Altitude", Units.Length), 
            ("Pitch Rate", Units.Velocity),
            ("Pitch Initial", Units.Angle), 
            ("Pitch Final", Units.Angle),
            ("True Course Angle", Units.Angle)
        ],
        "Constant Speed/Constant Altitude Loiter": [
            ("Altitude", Units.Length), 
            ("Air Speed", Units.Velocity),
            ("Time", Units.Time), 
            ("True Course Angle", Units.Angle)
        ],
        "Constant Speed/Constant Altitude": [
            ("Altitude", Units.Length), 
            ("Air Speed", Units.Velocity),
            ("Distance", Units.Length), 
            ("True Course Angle", Units.Angle)
        ],
        "Constant Throttle/Constant Altitude": [
            ("Throttle", Units.Unitless), 
            ("Altitude", Units.Length),
            ("Air Speed Start", Units.Velocity), 
            ("Air Speed End", Units.Velocity),
            ("True Course Angle", Units.Angle)
        ],
    }, 
    {
        # Descent Subsegments
        "Constant CAS/Constant Rate": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Descent Rate", Units.Velocity), 
            ("CAS", Units.Velocity),
            ("True Course Angle", Units.Angle)
        ],
        "Constant EAS/Constant Rate": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Descent Rate", Units.Velocity), 
            ("EAS", Units.Velocity),
            ("True Course Angle", Units.Angle)
        ],
        "Constant Speed/Constant Angle Noise": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Descent Angle", Units.Unitless), 
            ("Air Speed", Units.Velocity),
            ("True Course Angle", Units.Angle)
        ],
        "Constant Speed/Constant Angle": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Descent Angle", Units.Unitless), 
            ("Air Speed", Units.Velocity),
            ("True Course Angle", Units.Angle)
        ],
        "Constant Speed/Constant Rate": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Descent Rate", Units.Velocity), 
            ("Air Speed", Units.Velocity),
            ("True Course Angle", Units.Angle)
        ],
        "Linear Mach/Constant Rate": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Descent Rate", Units.Velocity), 
            ("Mach Number End", Units.Unitless),
            ("Mach Number Start", Units.Unitless), 
            ("True Course Angle", Units.Angle)
        ],
        "Linear Speed/Constant Rate": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length),
            ("Descent Rate", Units.Velocity), 
            ("Air Speed Start", Units.Velocity),
            ("Air Speed End", Units.Velocity), 
            ("True Course Angle", Units.Angle)
        ],
    }, 
    {
        # Ground Subsegments
        "Climb": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length), 
            ("Climb Rate", Units.Velocity),
            ("True Course Angle", Units.Angle)
        ],
        "Descent": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length), 
            ("Descent Rate", Units.Velocity),
            ("True Course Angle", Units.Angle)
        ],
        "Hover": [
            ("Altitude", Units.Length), 
            ("Time", Units.Time), 
            ("True Course Angle", Units.Angle)
        ]
    }, 
    {
        # Single Point Subsegments
        "Set Speed/Set Altitude/No Propulsion": [
            ("Altitude", Units.Length), 
            ("Air Speed", Units.Velocity),
            ("Distance", Units.Length), 
            ("Acceleration Z", Units.Acceleration),
            ("True Course Angle", Units.Angle)
        ],
        "Set Speed/Set Altitude": [
            ("Altitude", Units.Length), 
            ("Air Speed", Units.Velocity),
            ("Distance", Units.Length), 
            ("Acceleration X", Units.Acceleration),
            ("Acceleration Z", Units.Acceleration),
            ("State Numerics Number of Control Points", Units.Unitless)
        ],
        "Set Speed/Set Throttle": [
            ("Altitude", Units.Length), 
            ("Air Speed", Units.Velocity),
            ("Throttle", Units.Unitless), 
            ("Acceleration Z", Units.Acceleration),
            ("True Course Angle", Units.Angle)
        ],
    }, 
    {
        # Transition Subsegments
        "Constant Acceleration/Constant Angle/Linear Climb": [
            ("Altitude Start", Units.Length),
            ("Altitude End", Units.Length),
            ("Air Speed Start", Units.Velocity),
            ("Climb Angle", Units.Unitless),
            ("Acceleration", Units.Acceleration),
            ("Pitch Initial", Units.Angle),
            ("Pitch Final", Units.Angle),
            ("True Course Angle", Units.Angle)
        ],
        "Constant Acceleration/Constant Pitchrate/Constant Altitude": [
            ("Altitude", Units.Length),
            ("Acceleration", Units.Acceleration),
            ("Air Speed Start", Units.Velocity),
            ("Air Speed End", Units.Velocity),
            ("Pitch Initial", Units.Angle),
            ("Pitch Final", Units.Angle),
            ("True Course Angle", Units.Angle)
        ],
    }, 
    {
        # Vertical Flight Subsegments
        "Climb": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length), 
            ("Climb Rate", Units.Velocity),
            ("True Course Angle", Units.Angle)
        ],
        "Descent": [
            ("Altitude Start", Units.Length), 
            ("Altitude End", Units.Length), 
            ("Descent Rate", Units.Velocity),
            ("True Course Angle", Units.Angle)
        ],
        "Hover": [
            ("Altitude", Units.Length), 
            ("Time", Units.Time), 
            ("True Course Angle", Units.Angle)
        ]
    }
]