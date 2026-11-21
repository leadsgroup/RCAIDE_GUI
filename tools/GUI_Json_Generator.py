# RCAIDE_GUI/tools/GUI_Json_Generator.py
#
# Regenerates the aircraft JSON files in app_data/aircraft from the RCAIDE aircraft scripts.
#
# Usage:
#   python tools/GUI_Json_Generator.py                                # all aircraft in main()
#   python tools/GUI_Json_Generator.py Boeing_737_800 Stopped_Rotor   # selected aircraft
#   python tools/GUI_Json_Generator.py --aircraft-dir /path/to/Aircraft

# ----------------------------------------------------------------------
#   Imports
# ----------------------------------------------------------------------

import RCAIDE
from RCAIDE.Framework.Core import Units
from RCAIDE.Input_Output import export_data

import numpy as np
import json
import os
import shutil
import importlib
import traceback
import argparse
import sys


# ----------------------------------------------------------------------
#   Aircraft registry: maps list name -> (folder, module_name)
# ----------------------------------------------------------------------
AIRCRAFT_REGISTRY = {
    'Concorde':             ('Concorde',    'Concorde'),# CHECKED BY MATTHEW
    'Boeing_737_800':       ('Boeing_737',  'Boeing_737_800'),# CHECKED BY MATTHEW
    'Boeing_787':           ('Boeing_787',  'Boeing_787'), # CHECKED BY MATTHEW 
    'ATR_72':               ('ATR_72',      'ATR_72'), # CHECKED BY MATTHEW
    'Navion':               ('Navion',      'Navion'),# CHECKED BY MATTHEW 
    'Electric_Twin_Otter':  ('Twin_Otter',  'Electric_Twin_Otter'),# CHECKED BY MATTHEW
    'Airbus_A220_100':      ('Airbus_A220',     'Airbus_A220_100'),# CHECKED BY MATTHEW
    'Airbus_A320':          ('Airbus_A320',     'Airbus_A320'),# CHECKED BY MATTHEW
    'Boeing_777_200er':     ('Boeing_777',      'Boeing_777_200er'),# CHECKED BY MATTHEW
    'Boeing_747_100':       ('Boeing_747_100',  'Boeing_747_100'), # CHECKED BY MATTHEW
    'CRJ_700':              ('CRJ_700',         'CRJ_700'),# CHECKED BY MATTHEW
    'Cessna_172':           ('Cessna',           'Cessna_172'),# CHECKED BY MATTHEW
    'Twin_Otter':           ('Twin_Otter',       'Twin_Otter'),# FUTURE RELEASE
    'DHC8_100':             ('DHC8-100',         'DHC8_100'),# CHECKED BY MATTHEW
    'Embraer_E190':         ('Embraer_190',      'Embraer_190'),# CHECKED BY MATTHEW
    'Lockheed_C5a':         ('C5a',              'Lockheed_C5a'),# FUTURE RELEASE
    'Tecnam_P2012':         ('Tecnam_P2012',     'Tecnam_P2012'),# FUTURE RELEASE
    'BWB':                  ('Blended_Wing_Body','BWB'),# CHECKED BY MATTHEW
    'BWB_Hydrogen':         ('Blended_Wing_Body','BWB_2050_LH2_NC'),# CHECKED BY MATTHEW
    'ATR_72_Electric':      ('ATR_72',           'ATR_72_all_electric'),# CHECKED BY MATTHEW
    'ATR_72_Parallel_Hybrid': ('ATR_72',         'ATR_72_cryo_parallel_hybrid_electric'),# CHECKED BY MATTHEW
    'Lockheed_F22':         ('Lockheed_F22',     'Lockheed_F22'),# FUTURE RELEASE    
    'Stopped_Rotor':        ('Stopped_Rotor',    'Stopped_Rotor'),# CHECKED BY MATTHEW
    'Tilt_Stopped_Rotor_V_Tail': ('Tilt_Stopped_Rotor', 'Tilt_Stopped_Rotor_V_Tail'),# TO DO  
    'Tiltrotor':            ('Tiltrotor',        'Tiltrotor'),# CHECKED BY MATTHEW  
}

# GUI repository root (this file lives in RCAIDE_GUI/tools)
_GUI_ROOT     = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
_GUI_APP_DATA = os.path.join(_GUI_ROOT, 'app_data', 'aircraft')

# Default location of the aircraft scripts: RESEARCH/Aircraft next to the RCAIDE_GUI checkout
_DEFAULT_AIRCRAFT_DIR = os.path.normpath(os.path.join(_GUI_ROOT, '..', 'RESEARCH', 'Aircraft'))


def main():
    parser = argparse.ArgumentParser(description='Regenerate the GUI aircraft JSON files.')
    parser.add_argument('aircraft', nargs='*', help='aircraft names to regenerate (default: all in main())')
    parser.add_argument('--aircraft-dir', default=_DEFAULT_AIRCRAFT_DIR, help='folder holding the RCAIDE aircraft scripts')
    args = parser.parse_args()

    aircraft_list = [
        'Concorde',
        'Boeing_737_800',
        'Boeing_787',
        'ATR_72',
        'Navion',
        'Electric_Twin_Otter',
        'Airbus_A220_100',
        'Airbus_A320',
        'Boeing_777_200er',
        'Boeing_747_100', 
        'CRJ_700',
        'Cessna_172',
        #'Twin_Otter',
        'DHC8_100',
        'Embraer_E190',
        #'Lockheed_C5a',
        #'Tecnam_P2012',
        'BWB',
        'BWB_Hydrogen',
        'ATR_72_Electric',
        'ATR_72_Parallel_Hybrid',
        #'Lockheed_F22', 
        'Stopped_Rotor',
        #'Tilt_Stopped_Rotor_V_Tail',
        'Tiltrotor', 
    ]
    if args.aircraft:
        aircraft_list = args.aircraft

    succeeded = []
    failed    = []

    for aircraft_name in aircraft_list:
        print(f"\n{'='*60}")
        print(f"  Processing: {aircraft_name}")
        print(f"{'='*60}")

        try:
            process_aircraft(aircraft_name, args.aircraft_dir)
            succeeded.append(aircraft_name)
        except Exception:
            traceback.print_exc()
            failed.append(aircraft_name)
            print(f"  FAILED: {aircraft_name}")

    print(f"\n{'='*60}")
    print(f"  Summary")
    print(f"{'='*60}")
    print(f"  Succeeded: {succeeded}")
    print(f"  Failed:    {failed}")


def process_aircraft(aircraft_name, aircraft_dir):
    folder_name, module_name = AIRCRAFT_REGISTRY[aircraft_name]
    aircraft_folder = os.path.join(aircraft_dir, folder_name)

    # 1) Import the aircraft module dynamically
    print(f"  [1] Importing {module_name} from {aircraft_folder}")
    mod = _import_aircraft_module(aircraft_folder, module_name)

    # 2) Run vehicle setup, configs, analyses, mission
    print(f"  [2] Building vehicle, configs, analyses, mission")
    vehicle  = mod.vehicle_setup()
    configs  = mod.configs_setup(vehicle)
    analyses = mod.analyses_setup(configs) 
    missions = mod.missions_setup(analyses) 

    # 4) Export to JSON directly into the GUI app_data folder
    os.makedirs(_GUI_APP_DATA, exist_ok=True)
    json_path = os.path.join(_GUI_APP_DATA, aircraft_name)
    print(f"  [4] Exporting JSON to {json_path}.json")
    export_data(vehicle=vehicle,
                configurations=configs,
                analyses=analyses,
                missions=missions,
                filename=json_path)

    json_file = json_path + '.json'

    # 5) Fix airfoil paths and collect referenced files
    print(f"  [5] Fixing airfoil paths in JSON")
    airfoil_files = _fix_airfoil_paths(json_file)

    # 5b) Inject solver_type and control points for each segment (export skips segment state) so the GUI can restore them on load
    print(f"  [5b] Injecting solver types and control points into JSON")
    _inject_solver_types(json_file, missions)

    # 6) Copy the referenced airfoil files next to the JSON
    print(f"  [6] Copying airfoil files to GUI app_data/aircraft/")
    airfoils_dir = os.path.join(aircraft_dir, 'Airfoils')
    for af_filename in airfoil_files:
        src = _find_airfoil_file(airfoils_dir, af_filename)
        if src:
            shutil.copy2(src, os.path.join(_GUI_APP_DATA, af_filename))
            print(f"      Copied airfoil: {af_filename}")
        else:
            print(f"      WARNING: airfoil not found: {af_filename}")

    print(f"  Done: {aircraft_name}")


def _import_aircraft_module(aircraft_folder, module_name):
    module_path = os.path.join(aircraft_folder, f'{module_name}.py')
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    mod = importlib.util.module_from_spec(spec)

    # Aircraft scripts import sibling files (e.g. Electric_Twin_Otter imports Twin_Otter)
    old_cwd = os.getcwd()
    os.chdir(aircraft_folder)
    sys.path.insert(0, aircraft_folder)
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(aircraft_folder)
        os.chdir(old_cwd)

    return mod


def _fix_airfoil_paths(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    airfoil_files = set()

    def _walk_and_fix(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in ('coordinate_file', 'polar_files') and isinstance(value, str):
                    basename = os.path.basename(value)
                    obj[key] = basename
                    airfoil_files.add(basename)
                elif key == 'polar_files' and isinstance(value, list):
                    for i, path in enumerate(value):
                        if isinstance(path, str):
                            basename = os.path.basename(path)
                            value[i] = basename
                            airfoil_files.add(basename)
                else:
                    _walk_and_fix(value)
        elif isinstance(obj, list):
            for item in obj:
                _walk_and_fix(item)

    _walk_and_fix(data)

    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)

    return airfoil_files


def _inject_solver_types(json_file, missions):
    """Add solver_type and control_points to each segment dict using the live RCAIDE mission objects."""
    with open(json_file) as f:
        data = json.load(f)

    tag_to_solver = {}
    tag_to_control_points = {}
    for key in missions.keys():
        mission = missions[key]
        if not hasattr(mission, 'segments'):
            continue
        for seg_tag in mission.segments.keys():
            seg = mission.segments[seg_tag]
            try:
                solver_type = seg.state.numerics.solver.type
            except AttributeError:
                solver_type = 'root_finder'
            tag_to_solver[seg_tag] = solver_type
            tag_to_control_points[seg_tag] = int(seg.state.numerics.number_of_control_points)

    for mission_entry in data.get("mission_data", []):
        if not isinstance(mission_entry, dict):
            continue
        for seg_dict in mission_entry.get("segments", []):
            tag = seg_dict.get("tag", "")
            if tag in tag_to_solver:
                seg_dict["solver_type"]    = tag_to_solver[tag]
                seg_dict["control_points"] = [tag_to_control_points[tag], 0]

    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)


def _find_airfoil_file(airfoils_dir, filename):
    direct = os.path.join(airfoils_dir, filename)
    if os.path.isfile(direct):
        return direct

    polars = os.path.join(airfoils_dir, 'Polars', filename)
    if os.path.isfile(polars):
        return polars

    for root, _, files in os.walk(airfoils_dir):
        if filename in files:
            return os.path.join(root, filename)

    return None


if __name__ == '__main__':
    main()
