import RCAIDE
import json
import os
from collections import OrderedDict
from RCAIDE.load import read_RCAIDE_json_dict
from RCAIDE.save import build_dict_base


# RCAIDE vehicle GUI data
def new_rcaide_vehicle_data():
    return [[] for _ in range(7)]


def make_json_safe(value):
    if is_mapping(value):
        safe = OrderedDict()
        for key, item in value.items():
            if isinstance(key, type):
                key = key.__name__
            safe[str(key)] = make_json_safe(item)
        return safe

    if isinstance(value, list):
        return [make_json_safe(item) for item in value]

    if isinstance(value, tuple):
        return [make_json_safe(item) for item in value]

    return value


def is_unit_argument_pair(value):
    return (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[1], int)
        and not isinstance(value[1], bool)
    )


def strip_unit_arguments(value):
    if is_mapping(value):
        clean = OrderedDict()
        for key, item in value.items():
            clean[key] = strip_unit_arguments(item)
        return clean

    if is_unit_argument_pair(value):
        return strip_unit_arguments(value[0])

    if isinstance(value, list):
        return [strip_unit_arguments(item) for item in value]

    return value


def add_default_unit_arguments(value):
    # RCAIDE uses base units; 0 marks the default GUI unit.
    if is_mapping(value):
        wrapped = OrderedDict()
        for key, item in value.items():
            wrapped[key] = add_default_unit_arguments(item)
        return wrapped

    if is_unit_argument_pair(value):
        return value

    if isinstance(value, list):
        safe_items = [make_json_safe(item) for item in value]
        # Lists of dictionaries are tree collections, not numeric.
        if all(is_mapping(item) for item in safe_items):
            return [add_default_unit_arguments(item) for item in safe_items]
        return [safe_items, 0]

    if isinstance(value, tuple):
        return [make_json_safe(value), 0]

    return [value, 0]


def repair_local_file_paths(value):
    if is_mapping(value):
        for key, item in value.items():
            if key == "coordinate_file" and isinstance(item, str):
                value[key] = repair_airfoil_path(item)
            else:
                repair_local_file_paths(item)
    elif isinstance(value, list):
        for item in value:
            repair_local_file_paths(item)


def repair_airfoil_path(path):
    if not path or os.path.exists(path):
        return path

    local_path = os.path.join("app_data", "aircraft", os.path.basename(path))
    if os.path.exists(local_path):
        return local_path

    return path


def restore_airfoil_components(value):
    if is_mapping(value):
        for key, item in list(value.items()):
            if key == "airfoil" and is_serialized_airfoil(item):
                value[key] = make_airfoil_component(item)
            else:
                restore_airfoil_components(item)
    elif isinstance(value, list):
        for item in value:
            restore_airfoil_components(item)


def is_serialized_airfoil(value):
    return (
        is_mapping(value)
        and (
            has_key(value, "coordinate_file")
            or has_key(value, "NACA_4_Series_code")
        )
    )


def make_airfoil_component(data):
    if data.get("NACA_4_Series_code"):
        airfoil = RCAIDE.Library.Components.Airfoils.NACA_4_Series_Airfoil()
    else:
        airfoil = RCAIDE.Library.Components.Airfoils.Airfoil()

    airfoil.update(data)
    return airfoil


def restore_nacelle_components(value):
    if is_mapping(value):
        for key, item in list(value.items()):
            if key == "nacelle" and is_serialized_nacelle(item):
                value[key] = make_nacelle_component(item)
            else:
                restore_nacelle_components(item)
    elif isinstance(value, list):
        for item in value:
            restore_nacelle_components(item)


def is_serialized_nacelle(value):
    return (
        is_mapping(value)
        and has_key(value, "length")
        and has_key(value, "diameter")
        and has_key(value, "origin")
    )


def make_nacelle_component(data):
    if has_key(data, "segments") and data.get("segments"):
        nacelle = RCAIDE.Library.Components.Nacelles.Stack_Nacelle()
    elif has_key(data, "airfoil") and data.get("airfoil") is not None:
        nacelle = RCAIDE.Library.Components.Nacelles.Body_of_Revolution_Nacelle()
    else:
        nacelle = RCAIDE.Library.Components.Nacelles.Nacelle()

    nacelle.update(data)
    return nacelle


def restore_propulsor_components(value):
    if is_mapping(value):
        for key, item in list(value.items()):
            if is_serialized_propulsor(item):
                value[key] = make_propulsor_component(item)
            else:
                restore_propulsor_components(item)
    elif isinstance(value, list):
        for item in value:
            restore_propulsor_components(item)


def is_serialized_propulsor(value):
    return (
        is_mapping(value)
        and has_key(value, "sealevel_static_thrust")
        and has_key(value, "nacelle")
    )


def make_propulsor_component(data):
    if has_key(data, "fan") and has_key(data, "bypass_ratio"):
        propulsor = RCAIDE.Library.Components.Powertrain.Propulsors.Turbofan()
    elif has_key(data, "propeller"):
        propulsor = RCAIDE.Library.Components.Powertrain.Propulsors.Turboprop()
    elif has_key(data, "core_nozzle") and has_key(data, "combustor"):
        propulsor = RCAIDE.Library.Components.Powertrain.Propulsors.Turbojet()
    else:
        propulsor = RCAIDE.Library.Components.Powertrain.Propulsors.Propulsor()

    propulsor.update(data)
    return propulsor


def restore_wing_components(vehicle_obj):
  # Restore wing classes after JSON load so RCAIDE recognizess main wing
    if not has_key(vehicle_obj, "wings") or not is_mapping(vehicle_obj.wings):
        return

    # Create a new RCAIDE wing container to replace the old loaded one.
    restored_wings = RCAIDE.Library.Components.Wings.Wing.Container()

    # Rebuild each loaded wing dictionary/object into the closest RCAIDE wing class.
    for key, item in list(vehicle_obj.wings.items()):
        # Append preserves RCAIDE's expected container behavior and key formatting.
        restored_wings.append(make_wing_component(item, key))

    # Swap the vehicle over to the restored wing container.
    vehicle_obj.wings = restored_wings
    # Keep Vehicle.append_component() pointing at the restored container.
    if hasattr(vehicle_obj, "_component_root_map"):
        vehicle_obj._component_root_map[RCAIDE.Library.Components.Wings.Wing] = restored_wings


def make_wing_component(data, key=None):
    # If this is already a real RCAIDE wing object, leave it unchanged.
    if isinstance(data, RCAIDE.Library.Components.Wings.Wing):
        return data

    # Infer the correct RCAIDE wing class from the saved key or tag.
    name = f"{key} {data.get('tag', '')}".lower()
    # Main wings must be Main_Wing objects for RCAIDE
    if "main" in name:
        wing = RCAIDE.Library.Components.Wings.Main_Wing()
    # Horizontal stabilizers should use RCAIDE's horizontal tail class.
    elif "horizontal" in name:
        wing = RCAIDE.Library.Components.Wings.Horizontal_Tail()
    # Vertical stabilizers should use RCAIDE's vertical tail class.
    elif "vertical" in name:
        wing = RCAIDE.Library.Components.Wings.Vertical_Tail()
    # Unknown wing-like objects fall back to the generic RCAIDE Wing class.
    else:
        wing = RCAIDE.Library.Components.Wings.Wing()

    # Copy the loaded geometry/properties into the restored RCAIDE object.
    wing.update(data)
    # Return the restored wing for insertion into the vehicle's wing container.
    return wing


def wing_type_label_for_ui(component_dict):
    # Infer the GUI combo-box label from the saved component tag.
    name = str(component_dict.get("tag", "")).lower()
    # Show loaded main wings as "Main Wing" in the geometry editor.
    if "main" in name:
        return "Main Wing"
    # Show loaded horizontal stabilizers as "Horizontal Tail".
    if "horizontal" in name:
        return "Horizontal Tail"
    # Show loaded vertical stabilizers as "Vertical Tail".
    if "vertical" in name:
        return "Vertical Tail"
    # Default label for any other wing component.
    return "Wing"


def is_mapping(value):
    return hasattr(value, "items") and hasattr(value, "__setitem__")


def has_key(value, key):
    return hasattr(value, "keys") and key in value.keys()


rcaide_vehicle = new_rcaide_vehicle_data()
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


def vehicle_to_ui_format(vehicle_obj):
    """Convert a RCAIDE vehicle object to UI format for display in frames."""
    from tabs.geometry.frames import VehicleFrame
    
    vehicle_dict = make_json_safe(build_dict_base(vehicle_obj))
    ui_dict = {}
    ui_dict["name"] = getattr(vehicle_obj, "tag", "")
    
    for ui_label, units, rcaide_path in VehicleFrame.data_units_labels:
        try:
            value = vehicle_dict
            for key in rcaide_path.split("."):
                value = value[key]
            ui_dict[ui_label] = [value, 0]
        except (KeyError, TypeError):
            ui_dict[ui_label] = [0, 0]
    
    return ui_dict


def vehicle_dict_to_ui_list_structure(vehicle_dict):
    """Convert rcaide_vehicle dict to UI structure (fallback if no geometry_data)."""
    from tabs.geometry.frames.booms.boom_frame import BoomFrame
    from tabs.geometry.frames.cargo_bays.cargo_bay_frame import CargoBayFrame
    from tabs.geometry.frames.fuselages.fuselage_frame import FuselageFrame
    from tabs.geometry.frames.landing_gears.landing_gear_frame import LandingGearFrame
    from tabs.geometry.frames.powertrain.powertrain_frame import PowertrainFrame
    from tabs.geometry.frames.wings.wings_frame import WingsFrame

    def wing_segment_to_ui(segment):
        return {
            "Segment Name": segment.get("tag", ""),
            "Percent Span Location": [segment.get("percent_span_location", 0), 0],
            "Twist": [segment.get("twist", 0), 0],
            "Root Chord Percent": [segment.get("root_chord_percent", 0), 0],
            "Thickness to Chord": [segment.get("thickness_to_chord", 0), 0],
            "Dihedral Outboard": [segment.get("dihedral_outboard", 0), 0],
            "Quarter Chord Sweep": [segment.get("sweeps", {}).get("quarter_chord", 0), 0],
            "Has Fuel Tank": [bool(segment.get("Fuel_Tank")), 0],
            "Has Aft Fuel Tank": [bool(segment.get("Aft_Fuel_Tank")), 0],
            "Airfoil Type": None,
        }

    def wing_control_surface_to_ui(control_surface):
        cs_type = {
            "aileron": 0,
            "slat": 1,
            "flap": 2,
            "elevator": 3,
            "rudder": 4,
            "spoiler": 5,
        }.get(control_surface.get("tag", "").lower(), 0)

        return {
            "CS name": control_surface.get("tag", ""),
            "CS type": cs_type,
            "Span Fraction Start": [control_surface.get("span_fraction_start", 0), 0],
            "Span Fraction End": [control_surface.get("span_fraction_end", 0), 0],
            "Deflection": [control_surface.get("deflection", 0), 0],
            "Chord Fraction": [control_surface.get("chord_fraction", 0), 0],
            "Number of Slots": [1, 0],
        }
    
    def to_ui_format(component_dict, frame_class):
        """Convert component dict to UI format using frame's data_units_labels."""
        ui_dict = {"name": component_dict.get("tag", component_dict.get("name", ""))}
        
        if hasattr(frame_class, 'data_units_labels'):
            for ui_label, units, rcaide_path in frame_class.data_units_labels:
                try:
                    value = component_dict
                    for key in rcaide_path.split("."):
                        value = value[key]
                    ui_dict[ui_label] = [value, 0]
                except (KeyError, TypeError):
                    ui_dict[ui_label] = [0, 0]
        else:
            ui_dict.update(component_dict)
        
        # Special handling for WingsFrame
        if frame_class.__name__ == 'WingsFrame':
            # add the UI labels if not already added
            if 'Spans Projected' not in ui_dict:
                ui_dict["Spans Projected"] = [component_dict.get("spans", {}).get("projected", 0), 0]
                ui_dict["Reference Area"] = [component_dict.get("areas", {}).get("reference", 0), 0]
                ui_dict["Wetted Area"] = [component_dict.get("areas", {}).get("wetted", 0), 0]
                ui_dict["Root Chord"] = [component_dict.get("chords", {}).get("root", 0), 0]
                ui_dict["Tip Chord"] = [component_dict.get("chords", {}).get("tip", 0), 0]
                ui_dict["Mean Aerodynamic Chord"] = [component_dict.get("chords", {}).get("mean_aerodynamic", 0), 0]
                ui_dict["Quarter Chord Sweep Angle"] = [component_dict.get("sweeps", {}).get("quarter_chord", 0), 0]
                ui_dict["Leading Edge Sweep Angle"] = [component_dict.get("sweeps", {}).get("leading_edge", 0), 0]
                ui_dict["Root Chord Twist Angle"] = [component_dict.get("twists", {}).get("root", 0), 0]
                ui_dict["Tip Chord Twist Angle"] = [component_dict.get("twists", {}).get("tip", 0), 0]
                ui_dict["Taper"] = [component_dict.get("taper", 0), 0]
                ui_dict["Dihedral"] = [component_dict.get("dihedral", 0), 0]
                ui_dict["Aspect Ratio"] = [component_dict.get("aspect_ratio", 0), 0]
                ui_dict["Thickness to Chord"] = [component_dict.get("thickness_to_chord", 0), 0]
                ui_dict["Aerodynamic Center"] = [component_dict.get("aerodynamic_center", [0,0,0]), 0]
                ui_dict["Origin"] = [component_dict.get("origin", [0,0,0]), 0]
                ui_dict["Vertical"] = [component_dict.get("vertical", False), 0]
                ui_dict["X-Y Plane Symmetric"] = [component_dict.get("xy_plane_symmetric", False), 0]
                ui_dict["High Lift"] = [component_dict.get("high_lift", False), 0]
                ui_dict["X-Z Plane Symmetric"] = [component_dict.get("xz_plane_symmetric", False), 0]
                ui_dict["T-Tail"] = [component_dict.get("t_tail", False), 0]
                ui_dict["Y-Z Plane Symmetric"] = [component_dict.get("yz_plane_symmetric", False), 0]
                ui_dict["Dynamic Pressure Ratio"] = [component_dict.get("dynamic_pressure_ratio", 0), 0]
                ui_dict["Exposed Root Chord Offset"] = [component_dict.get("exposed_root_chord_offset", 0), 0]
            # special handling
            ui_dict.setdefault("wing_type", wing_type_label_for_ui(component_dict))
            segments = ui_dict.pop("segments", {})
            if isinstance(segments, dict):
                ui_dict["sections"] = [wing_segment_to_ui(segment) for segment in segments.values()]
            else:
                ui_dict["sections"] = [wing_segment_to_ui(segment) for segment in segments] if isinstance(segments, list) else []

            control_surfaces = ui_dict.get("control_surfaces", [])
            if isinstance(control_surfaces, dict):
                ui_dict["control_surfaces"] = [
                    wing_control_surface_to_ui(control_surface)
                    for control_surface in control_surfaces.values()
                ]
            elif isinstance(control_surfaces, list):
                ui_dict["control_surfaces"] = [
                    wing_control_surface_to_ui(control_surface)
                    for control_surface in control_surfaces
                ]
            else:
                ui_dict["control_surfaces"] = []

            ui_dict.setdefault("cabins", [])
            ui_dict.setdefault("side_cabins", [])
        
        return ui_dict
    
    ui_structure = [[] for _ in range(7)]
    ui_structure[0] = None
    
    if "booms" in vehicle_dict and vehicle_dict["booms"]:
        ui_structure[1] = [to_ui_format(b, BoomFrame) for b in vehicle_dict["booms"].values()]
    
    if "cargo_bays" in vehicle_dict and vehicle_dict["cargo_bays"]:
        ui_structure[2] = [to_ui_format(c, CargoBayFrame) for c in vehicle_dict["cargo_bays"].values()]
    
    if "fuselages" in vehicle_dict and vehicle_dict["fuselages"]:
        ui_structure[3] = [to_ui_format(f, FuselageFrame) for f in vehicle_dict["fuselages"].values()]
    
    if "landing_gears" in vehicle_dict and vehicle_dict["landing_gears"]:
        ui_structure[4] = [to_ui_format(l, LandingGearFrame) for l in vehicle_dict["landing_gears"].values()]
    
    if "powertrains" in vehicle_dict and vehicle_dict["powertrains"]:
        ui_structure[5] = [to_ui_format(p, PowertrainFrame) for p in vehicle_dict["powertrains"].values()]
    elif "networks" in vehicle_dict and vehicle_dict["networks"]:
        for network in vehicle_dict["networks"].values():
            if not isinstance(network, dict):
                continue
            network_tag = network.get("tag", "Fuel").title()
            propulsors = network.get("propulsors", {})
            if propulsors:
                for propulsor in propulsors.values():
                    ui_structure[5].append({
                        "name": propulsor.get("tag", network_tag),
                        "energy network selected": network_tag,
                        "powertrain": {
                            "distributor data": [],
                            "source data": [],
                            "propulsor data": [],
                            "converter data": [],
                            "connections": []
                        }
                    })
            else:
                ui_structure[5].append({
                    "name": network_tag,
                    "energy network selected": network_tag,
                    "powertrain": {
                        "distributor data": [],
                        "source data": [],
                        "propulsor data": [],
                        "converter data": [],
                        "connections": []
                    }
                })

    if "wings" in vehicle_dict and vehicle_dict["wings"]:
        ui_structure[6] = [to_ui_format(w, WingsFrame) for w in vehicle_dict["wings"].values()]
    
    return ui_structure


def write_to_json():
    data = {
        "rcaide_vehicle": add_default_unit_arguments(
            make_json_safe(build_dict_base(vehicle))
        ),
        "config_data": config_data,
        "analysis_data": analysis_data,
        "mission_data": mission_data,
        "propulsor_names": propulsor_names
    }

    data_str = json.dumps(data, indent=4)
    return data_str


def read_from_json(data_str):
    global rcaide_vehicle, vehicle, config_data, analysis_data, mission_data, propulsor_names

    data = json.loads(data_str, object_pairs_hook=OrderedDict)
    rcaide_vehicle_dict = data["rcaide_vehicle"]
    rcaide_vehicle_clean = strip_unit_arguments(rcaide_vehicle_dict)
    repair_local_file_paths(rcaide_vehicle_clean)

    vehicle = RCAIDE.Vehicle()
    if isinstance(rcaide_vehicle_clean, OrderedDict):
        vehicle.update(read_RCAIDE_json_dict(rcaide_vehicle_clean))
        restore_wing_components(vehicle)
        restore_airfoil_components(vehicle)
        restore_nacelle_components(vehicle)
        restore_propulsor_components(vehicle)
    
    # If geometry_data exists, use it directly (it's already in UI format)
    if "geometry_data" in data and data["geometry_data"]:
        rcaide_vehicle = data["geometry_data"]
    else:
        # Fallback: convert rcaide_vehicle_dict to UI structure
        rcaide_vehicle = vehicle_dict_to_ui_list_structure(rcaide_vehicle_clean)
        rcaide_vehicle[0] = vehicle_to_ui_format(vehicle)

    config_data = data["config_data"]
    analysis_data = data["analysis_data"]
    mission_data = data["mission_data"]
    propulsor_names = data["propulsor_names"]
