import RCAIDE
import json


# Geometry Data
geometry_data = []
propulsor_names = [[]]
vehicle = RCAIDE.Vehicle()

# Aircraft Configs Data
config_data = []
rcaide_configs = RCAIDE.Library.Components.Configs.Config.Container() # type: ignore

# Analysis Data
analysis_data = []
rcaide_analyses = RCAIDE.Framework.Analyses.Analysis.Container() # type: ignore

# Mission Data
mission_data = []
rcaide_mission = RCAIDE.Framework.Mission.Sequential_Segments()


def write_to_json():
    data = {
        "geometry_data": geometry_data,
        "config_data": config_data,
        "analysis_data": analysis_data,
        "mission_data": mission_data,
        "propulsor_names": propulsor_names
    }

    data_str = json.dumps(data, indent=4)
    return data_str


def read_from_json(data_str):
    global geometry_data, config_data, analysis_data, mission_data, propulsor_names

    data = json.loads(data_str)
    geometry_data = data["geometry_data"]
    config_data = data["config_data"]
    analysis_data = data["analysis_data"]
    mission_data = data["mission_data"]
    propulsor_names = data["propulsor_names"]
