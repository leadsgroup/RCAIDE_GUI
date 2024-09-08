import RCAIDE
import json


# Geometry Data
vehicle = RCAIDE.Vehicle()
geometry_data = []
propulsor_names = []

# Aircraft Configs Data
config_data = []
aircraft_configs = RCAIDE.Library.Components.Configs.Config.Container()

# Analysis Data
analysis_data = []

# Mission Data
rcaide_mission = RCAIDE.Framework.Mission.Sequential_Segments()
mission_data = []


def write_to_json():
    data = {
        "geometry_data": geometry_data,
        "config_data": config_data,
        "analysis_data": analysis_data,
        "mission_data": mission_data
    }

    data_str = json.dumps(data, indent=4)
    return data_str


def read_from_json(data_str):
    global geometry_data, config_data, analysis_data, mission_data

    data = json.loads(data_str)
    geometry_data = data["geometry_data"]
    config_data = data["config_data"]
    analysis_data = data["analysis_data"]
    mission_data = data["mission_data"]
