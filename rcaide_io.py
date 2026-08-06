import RCAIDE
import json
import os
import importlib
import numpy as np
import types as _types_module
from collections import OrderedDict
from RCAIDE.Input_Output.load import read_RCAIDE_json_dict
from RCAIDE.Framework.Core import Data, DataOrdered

from utilities import APP_DATA
_AIRCRAFT_DIR = os.path.join(APP_DATA, "aircraft")
_AIRFOIL_DIR  = os.path.join(APP_DATA, "airfoils")


# ----------------------------------------------------------------------------------------------------------------------
#  Utility helpers
# ----------------------------------------------------------------------------------------------------------------------

def is_mapping(value):
    return hasattr(value, "items") and hasattr(value, "__setitem__")


def has_key(value, key):
    return hasattr(value, "keys") and key in value.keys()


def is_unit_argument_pair(value):
    return (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[1], int)
        and not isinstance(value[1], bool)
    )


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


def strip_unit_arguments(value):
    if is_mapping(value):
        clean = OrderedDict()
        for key, item in value.items():
            clean[key] = strip_unit_arguments(item)
        return clean
    if is_unit_argument_pair(value):
        inner = value[0]
        # A flat list of scalars is raw data (e.g. [0, 1] for galley locations),
        # not a nested unit pair — return it directly to avoid double-stripping.
        if isinstance(inner, list) and not any(is_mapping(x) or isinstance(x, list) for x in inner):
            return inner
        return strip_unit_arguments(inner)
    if isinstance(value, list):
        return [strip_unit_arguments(item) for item in value]
    return value


def add_default_unit_arguments(value):
    if is_mapping(value):
        wrapped = OrderedDict()
        for key, item in value.items():
            wrapped[key] = add_default_unit_arguments(item)
        return wrapped
    if is_unit_argument_pair(value):
        return value
    if isinstance(value, str):
        return value  # strings stay plain to match export_rcaide_data format
    if isinstance(value, list):
        safe_items = [make_json_safe(item) for item in value]
        if all(is_mapping(item) for item in safe_items):
            return [add_default_unit_arguments(item) for item in safe_items]
        return [safe_items, 0]
    if isinstance(value, tuple):
        return [make_json_safe(value), 0]
    return [value, 0]


# ----------------------------------------------------------------------------------------------------------------------
#  Local file-path repair (airfoil coordinate files)
# ----------------------------------------------------------------------------------------------------------------------

def repair_local_file_paths(value, source_dir=None):
    if is_mapping(value):
        for key, item in value.items():
            if key == "coordinate_file" and isinstance(item, str):
                value[key] = repair_airfoil_path(item, source_dir)
            else:
                repair_local_file_paths(item, source_dir)
    elif isinstance(value, list):
        for item in value:
            repair_local_file_paths(item, source_dir)


def repair_airfoil_path(path, source_dir=None):
    if not path:
        return path
    basename = os.path.basename(path)
    if source_dir:
        candidate = os.path.join(source_dir, basename)
        if os.path.exists(candidate):
            return candidate
    for search_dir in (_AIRCRAFT_DIR, _AIRFOIL_DIR):
        candidate = os.path.join(search_dir, basename)
        if os.path.exists(candidate):
            return candidate
    return basename if basename else path


# ----------------------------------------------------------------------------------------------------------------------
#  Type-aware class resolution
# ----------------------------------------------------------------------------------------------------------------------

def _class_for_type_string(type_str):
    """
    Return the Python class for a fully-qualified '__type__' string.

    Handles nested classes (e.g. 'RCAIDE.Library.Components.Wings.Wing.Container')
    by trying progressively shorter module prefixes until the import succeeds and
    the remaining parts resolve as class attributes on the module.
    """
    if not type_str or not isinstance(type_str, str):
        return None
    parts = type_str.split('.')
    for i in range(len(parts) - 1, 0, -1):
        module_path = '.'.join(parts[:i])
        attr_chain  = parts[i:]
        try:
            mod = importlib.import_module(module_path)
            obj = mod
            for attr in attr_chain:
                obj = getattr(obj, attr)
            if isinstance(obj, type):
                return obj
        except Exception:
            continue
    return None


def _type_str(data):
    """Extract the __type__ string from a Data object or plain dict, if present."""
    if hasattr(data, 'get'):
        return data.get('__type__') or ''
    return getattr(data, '__type__', '') or ''


# ----------------------------------------------------------------------------------------------------------------------
#  Generic typed-component maker
# ----------------------------------------------------------------------------------------------------------------------

def _make_typed_component(data, fallback_cls=None):
    """
    Instantiate the correct RCAIDE class from *data*.

    Resolution order
    ----------------
    1. Already the right type → return as-is (if fallback_cls given).
    2. '__type__' field present → import class and call cls(); update from data.
    3. fallback_cls given       → call fallback_cls(); update from data.
    4. Return data unchanged.
    """
    if fallback_cls is not None and isinstance(data, fallback_cls):
        return data

    ts = _type_str(data)
    if ts:
        cls = _class_for_type_string(ts)
        if cls is not None and cls is not Data and cls is not DataOrdered:
            if not (getattr(cls, '__module__', '') or '').startswith('RCAIDE.Framework.Core'):
                try:
                    obj = cls()
                    obj.update(data)
                    return obj
                except Exception:
                    pass

    if fallback_cls is not None:
        try:
            obj = fallback_cls()
            obj.update(data)
            return obj
        except Exception:
            pass

    return data



# ----------------------------------------------------------------------------------------------------------------------
#  Vehicle-container restoration  (single table-driven function)
# ----------------------------------------------------------------------------------------------------------------------

# Each entry: (container_key, base_class, root_map_attr, _unused)
# Class selection is driven by __type__; base_class is the graceful fallback.
# To add a new top-level component type, append one row here.
_VEHICLE_CONTAINER_TABLE = [
    ('fuselages',     RCAIDE.Library.Components.Fuselages.Fuselage,           '_component_root_map',      None),
    ('booms',         RCAIDE.Library.Components.Booms.Boom,                   '_component_root_map',      None),
    ('landing_gears', RCAIDE.Library.Components.Landing_Gear.Landing_Gear,    '_component_root_map',      None),
    ('cargo_bays',    RCAIDE.Library.Components.Cargo_Bays.Cargo_Bay,         '_component_root_map',      None),
    ('wings',         RCAIDE.Library.Components.Wings.Wing,                   '_component_root_map',      None),
    ('nacelles',      RCAIDE.Library.Components.Nacelles.Nacelle,             '_component_root_map',      None),
    ('networks',      RCAIDE.Framework.Networks.Network,                       '_energy_network_root_map', None),
]


def restore_vehicle_components(vehicle_obj):
    """
    Single-pass restoration of all typed vehicle-level component containers.

    Iterates _VEHICLE_CONTAINER_TABLE so that every top-level container
    (fuselages, wings, networks, etc.) is rebuilt with correctly-typed RCAIDE
    instances.  Class selection is driven entirely by the __type__ field written
    by export_rcaide_data / write_to_json.  If __type__ is absent or cannot be
    resolved, the entry's base class is used as a graceful fallback.
    """
    for container_key, base_cls, map_attr, _ in _VEHICLE_CONTAINER_TABLE:
        if not has_key(vehicle_obj, container_key) or not is_mapping(vehicle_obj[container_key]):
            continue

        container_cls = getattr(base_cls, 'Container', None)
        if container_cls is None:
            continue

        restored = container_cls()
        for _key, item in list(vehicle_obj[container_key].items()):
            if not is_mapping(item):
                continue
            restored.append(_make_typed_component(item, base_cls))

        vehicle_obj[container_key] = restored
        root_map = getattr(vehicle_obj, map_attr, None)
        if root_map is not None:
            root_map[base_cls] = restored


# ----------------------------------------------------------------------------------------------------------------------
#  Airfoil restoration  (walks the full tree — kept separate because airfoils
#  are embedded as attributes of wings/nacelles, not top-level containers)
# ----------------------------------------------------------------------------------------------------------------------

def restore_airfoil_components(value):
    if is_mapping(value):
        for key, item in list(value.items()):
            if key == "airfoil" and _is_serialized_airfoil(item):
                value[key] = _make_typed_component(item, RCAIDE.Library.Components.Airfoils.Airfoil)
            else:
                restore_airfoil_components(item)
    elif isinstance(value, list):
        for item in value:
            restore_airfoil_components(item)


def _is_serialized_airfoil(value):
    return is_mapping(value) and (
        has_key(value, "coordinate_file") or has_key(value, "NACA_4_Series_code")
    )


# ----------------------------------------------------------------------------------------------------------------------
#  Generic sub-component restoration  (Fan, Combustor, Fuel_Line, etc.)
# ----------------------------------------------------------------------------------------------------------------------

_SKIP_KEYS = frozenset({'__type__', '_component_root_map', '_energy_network_root_map'})


def restore_typed_subcomponents(obj):
    """
    Recursively replace raw DataOrdered objects with properly-typed RCAIDE instances.

    Runs after restore_vehicle_components so that all nested sub-components
    (Fan, Combustor, Fuel_Line, Compressor, …) whose types are recorded in the
    __type__ field are also correctly typed.  Only objects that are still the
    raw DataOrdered produced by read_RCAIDE_json_dict are touched; already-typed
    objects are left unchanged.
    """
    if not is_mapping(obj):
        return

    for key in list(obj.keys()):
        if key in _SKIP_KEYS:
            continue
        child = obj[key]
        if not is_mapping(child):
            continue

        restore_typed_subcomponents(child)   # depth-first

        if type(child) is not DataOrdered:   # already typed → skip
            continue

        ts = child.get('__type__') if hasattr(child, 'get') else None
        if not ts or not isinstance(ts, str):
            continue

        cls = _class_for_type_string(ts)
        if cls is None or cls is Data or cls is DataOrdered:
            continue
        if (getattr(cls, '__module__', '') or '').startswith('RCAIDE.Framework.Core'):
            continue

        try:
            new_obj = cls()
            for k, v in child.items():
                if k != '__type__':
                    new_obj[k] = v
            obj[key] = new_obj
        except Exception:
            pass


# ----------------------------------------------------------------------------------------------------------------------
#  JSON serialisation (write side)
# ----------------------------------------------------------------------------------------------------------------------

def _build_dict_r_with_types(v):
    """Serialise a RCAIDE value to a plain Python structure, recording __type__ for containers."""
    tv = type(v)
    if tv is type or tv is _types_module.FunctionType:
        return None
    if tv in (str, bool) or tv is type(None):
        return v
    if tv in (float, int):
        return v
    if tv in (np.ndarray, np.float64):
        return v.tolist()
    if tv is list:
        return v

    try:
        keys = v.keys()
    except AttributeError:
        return None if callable(tv) else None

    ret = {}
    module   = getattr(tv, '__module__', '') or ''
    qualname = getattr(tv, '__qualname__', '') or ''
    if module and qualname and not qualname.startswith('<'):
        ret['__type__'] = f"{module}.{qualname}"

    _skip = ('_component_root_map', '_energy_network_root_map', '_base', '_diff', 'vehicle')
    for k in keys:
        if k in _skip:
            continue
        ret[k] = _build_dict_r_with_types(v[k])
    return ret


def _build_dict_base_with_types(base):
    """Top-level serialisation: like RCAIDE.Input_Output.save.build_dict_base but includes __type__."""
    _skip = ('_component_root_map', '_energy_network_root_map', '_base', '_diff', 'vehicle')
    base_dict = {}
    for k in base.keys():
        if k in _skip:
            continue
        base_dict[k] = _build_dict_r_with_types(base[k])
    return base_dict


_WING_TYPE_LABELS = {
    'Main_Wing':         'Main Wing',
    'Horizontal_Tail':   'Horizontal Tail',
    'Vertical_Tail':     'Vertical Tail',
    'Blended_Wing_Body': 'Blended Wing Body',
}

_FUSELAGE_SEGMENT_TYPE_LABELS = {
    'Circle_Segment':            'Circle Segment',
    'Ellipse_Segment':           'Ellipse Segment',
    'Rounded_Rectangle_Segment': 'Rounded Rectangle Segment',
    'Super_Ellipse_Segment':     'Super Ellipse Segment',
    'Segment':                   'Segment',
}

_BOOM_SEGMENT_TYPE_LABELS = _FUSELAGE_SEGMENT_TYPE_LABELS
_NACELLE_SEGMENT_TYPE_LABELS = _FUSELAGE_SEGMENT_TYPE_LABELS


def boom_segment_type_label_for_ui(segment_dict):
    """Derive the GUI boom segment label from __type__, falling back to Ellipse Segment."""
    type_str = segment_dict.get('__type__', '')
    class_name = type_str.rsplit('.', 1)[-1] if type_str else ''
    return _BOOM_SEGMENT_TYPE_LABELS.get(class_name, 'Ellipse Segment')


def nacelle_segment_type_label_for_ui(segment_dict):
    """Derive the GUI nacelle segment label from __type__, falling back to Segment."""
    type_str = segment_dict.get('__type__', '')
    class_name = type_str.rsplit('.', 1)[-1] if type_str else ''
    return _NACELLE_SEGMENT_TYPE_LABELS.get(class_name, 'Segment')


def wing_type_label_for_ui(component_dict):
    """Derive the GUI wing-type label from __type__, falling back to 'Wing'."""
    type_str = component_dict.get('__type__', '')
    class_name = type_str.rsplit('.', 1)[-1] if type_str else ''
    return _WING_TYPE_LABELS.get(class_name, 'Wing')


def fuselage_segment_type_label_for_ui(segment_dict):
    """Derive the GUI fuselage segment label from __type__, falling back to Segment."""
    type_str = segment_dict.get('__type__', '')
    class_name = type_str.rsplit('.', 1)[-1] if type_str else ''
    return _FUSELAGE_SEGMENT_TYPE_LABELS.get(class_name, 'Segment')


# ----------------------------------------------------------------------------------------------------------------------
#  Global state
# ----------------------------------------------------------------------------------------------------------------------

def new_rcaide_vehicle_data():
    return [[] for _ in range(7)]


rcaide_vehicle    = new_rcaide_vehicle_data()
propulsor_names   = [[]]
vehicle           = RCAIDE.Vehicle()
current_file_path = ""   # path of the last loaded or saved JSON file

config_data     = []
rcaide_configs  = RCAIDE.Library.Components.Configs.Config.Container()   # type: ignore

analysis_data   = []
rcaide_analyses = RCAIDE.Framework.Analyses.Analysis.Container()         # type: ignore

mission_data    = []
rcaide_mission  = RCAIDE.Framework.Mission.Sequential_Segments()
learner_data    = {}
learner_comparison_data = []
# Learner form defaults may exist before an RCAIDE vehicle does.  This flag
# distinguishes a prefilled worksheet from a vehicle explicitly built by Save.
learner_vehicle_built = False
# Last in-memory mission output. Set by the Solve tab after mission.evaluate()
# and browsed by the Results Viewer so users can inspect values without rerunning.
rcaide_results  = None
# Last raw result from the Performance tab. Set after each analysis run so the
# Results Viewer can browse it (stability derivatives, polar arrays, etc.).
last_performance_result = None
last_performance_label  = ""


# ----------------------------------------------------------------------------------------------------------------------
#  Vehicle → UI conversion helpers
# ----------------------------------------------------------------------------------------------------------------------

def vehicle_to_ui_format(vehicle_obj):
    """Convert a RCAIDE vehicle object to UI format for display in frames."""
    from RCAIDE.Input_Output.save import build_dict_base
    from tabs.geometry.frames import VehicleFrame

    vehicle_dict = make_json_safe(build_dict_base(vehicle_obj))
    ui_dict = {"name": getattr(vehicle_obj, "tag", "")}

    for ui_label, units, rcaide_path in VehicleFrame.data_units_labels:
        try:
            value = vehicle_dict
            for key in rcaide_path.split("."):
                value = value[key]
            ui_dict[ui_label] = [value, 0]
        except (KeyError, TypeError):
            ui_dict[ui_label] = [0, 0]

    return ui_dict


_NETWORK_TYPE_LABEL = {
    'Fuel':      'Fuel',
    'Electric':  'Electric',
    'Hybrid':    'Hybrid',
    'Hydrogen':  'Hydrogen',
    'Fuel_Cell': 'Fuel Cell',
}

# Maps RCAIDE propulsor class name → GUI type string (used by PropulsorFrame dispatch)
_PROPULSOR_TYPE_LABEL = {
    'Turbofan':                             'Turbofan',
    'Turbojet':                             'Turbojet',
    'Turboprop':                            'Turboprop',
    'Electric_Rotor':                       'Electric Rotor',
    'Electric_Ducted_Fan':                  'Electric Ducted Fan',
    'Internal_Combustion_Engine':           'Internal Combustion Engine',
    'Constant_Speed_Internal_Combustion_Engine': 'Constant Speed Internal Combustion Engine',
}

# Field specs as (label, rcaide_path) pairs — None path means heading/spacer, skip when reading.
# These mirror the BasePropulsorWidget field_specs exactly (COMMON + type-specific).
_COMMON_FIELDS = [
    ('Origin',                  'origin'),
    ('Active',                  'active'),
    ('Wing Mounted',            'wing_mounted'),
    ('Sea Level Static Thrust', 'sealevel_static_thrust'),
    ('Diameter',                'diameter'),
    ('Length',                  'length'),
    ('Height',                  'height'),
    ('X-Z Plane Symmetric',     'xz_plane_symmetric'),
    ('X-Y Plane Symmetric',     'xy_plane_symmetric'),
    ('Y-Z Plane Symmetric',     'yz_plane_symmetric'),
]
_ENGINE_FIELDS = [
    ('Engine Sea Level Power',                  'engine.sea_level_power'),
    ('Engine Flat Rate Altitude',               'engine.flat_rate_altitude'),
    ('Engine Rated Speed',                      'engine.rated_speed'),
    ('Engine Power Specific Fuel Consumption',  'engine.power_specific_fuel_consumption'),
]
_PROPELLER_FIELDS = [
    ('Propeller Number of Blades',          'propeller.number_of_blades'),
    ('Propeller Tip Radius',                'propeller.tip_radius'),
    ('Propeller Hub Radius',                'propeller.hub_radius'),
    ('Propeller Blade Pitch Command',       'propeller.blade_pitch_command'),
    ('Propeller Blade Solidity',            'propeller.blade_solidity'),
    ('Propeller Induced Power Factor',      'propeller.induced_power_factor'),
    ('Propeller Profile Drag Coefficient',  'propeller.profile_drag_coefficient'),
    ('Propeller Clockwise Rotation',        'propeller.clockwise_rotation'),
    ('Propeller Ducted',                    'propeller.ducted'),
]
_MOTOR_FIELDS = [
    ('Motor Diameter',      'motor.diameter'),
    ('Motor Length',        'motor.length'),
    ('Motor Resistance',    'motor.resistance'),
    ('Motor No Load Current','motor.no_load_current'),
    ('Motor Speed Constant','motor.speed_constant'),
    ('Motor Efficiency',    'motor.efficiency'),
]
_ESC_FIELDS = [
    ('ESC Bus Voltage', 'electronic_speed_controller.bus_voltage'),
    ('ESC Efficiency',  'electronic_speed_controller.efficiency'),
]
_ROTOR_FIELDS = [
    ('Rotor Number of Blades',          'rotor.number_of_blades'),
    ('Rotor Tip Radius',                'rotor.tip_radius'),
    ('Rotor Hub Radius',                'rotor.hub_radius'),
    ('Rotor Blade Pitch Command',       'rotor.blade_pitch_command'),
    ('Rotor Blade Solidity',            'rotor.blade_solidity'),
    ('Rotor Induced Power Factor',      'rotor.induced_power_factor'),
    ('Rotor Profile Drag Coefficient',  'rotor.profile_drag_coefficient'),
    ('Rotor Clockwise Rotation',        'rotor.clockwise_rotation'),
    ('Rotor Ducted',                    'rotor.ducted'),
]
_DUCTED_FAN_FIELDS = [
    ('Ducted Fan Number of Radial Stations', 'ducted_fan.number_of_radial_stations'),
    ('Ducted Fan Number of Rotor Blades',    'ducted_fan.number_of_rotor_blades'),
    ('Ducted Fan Tip Radius',                'ducted_fan.tip_radius'),
    ('Ducted Fan Hub Radius',                'ducted_fan.hub_radius'),
    ('Ducted Fan Exit Radius',               'ducted_fan.exit_radius'),
    ('Ducted Fan Blade Clearance',           'ducted_fan.blade_clearance'),
    ('Ducted Fan Length',                    'ducted_fan.length'),
    ('Ducted Fan Effectiveness',             'ducted_fan.fan_effectiveness'),
]
_TURBOJET_COMPONENT_FIELDS = [
    ('Inlet Nozzle Polytropic Efficiency',  'inlet_nozzle.polytropic_efficiency'),
    ('Inlet Nozzle Pressure Ratio',         'inlet_nozzle.pressure_ratio'),
    ('LPC Polytropic Efficiency',           'low_pressure_compressor.polytropic_efficiency'),
    ('LPC Pressure Ratio',                  'low_pressure_compressor.pressure_ratio'),
    ('HPC Polytropic Efficiency',           'high_pressure_compressor.polytropic_efficiency'),
    ('HPC Pressure Ratio',                  'high_pressure_compressor.pressure_ratio'),
    ('LPT Mechanical Efficiency',           'low_pressure_turbine.mechanical_efficiency'),
    ('LPT Polytropic Efficiency',           'low_pressure_turbine.polytropic_efficiency'),
    ('HPT Mechanical Efficiency',           'high_pressure_turbine.mechanical_efficiency'),
    ('HPT Polytropic Efficiency',           'high_pressure_turbine.polytropic_efficiency'),
    ('Combustor Pressure Loss Coeff',       'combustor.alphac'),
    ('Combustor Turbine Inlet Temp',        'combustor.turbine_inlet_temperature'),
    ('Afterburner Pressure Loss Coeff',     'afterburner.alphac'),
    ('Afterburner Turbine Inlet Temp',      'afterburner.turbine_inlet_temperature'),
    ('Core Nozzle Polytropic Efficiency',   'core_nozzle.polytropic_efficiency'),
    ('Core Nozzle Pressure Ratio',          'core_nozzle.pressure_ratio'),
]
_TURBOPROP_COMPONENT_FIELDS = [
    ('Design Altitude',                 'design_altitude'),
    ('Gearbox Gear Ratio',              'gearbox.gear_ratio'),
    ('Gearbox Efficiency',              'gearbox.efficiency'),
    ('Design Mach Number',              'design_mach_number'),
    ('Design Freestream Velocity',      'design_freestream_velocity'),
    ('Compressor Polytropic Efficiency','compressor.polytropic_efficiency'),
    ('Compressor Pressure Ratio',       'compressor.pressure_ratio'),
    ('Turbine Mechanical Efficiency',   'turbine.mechanical_efficiency'),
    ('Turbine Polytropic Efficiency',   'turbine.polytropic_efficiency'),
    ('Combustor Pressure Loss Coeff',   'combustor.alphac'),
    ('Combustor Turbine Inlet Temp',    'combustor.turbine_inlet_temperature'),
] + _PROPELLER_FIELDS

# Full field specs per propulsor type (matching BasePropulsorWidget.field_specs exactly)
_PROPULSOR_FIELDS = {
    'Electric Rotor':
        _COMMON_FIELDS + _MOTOR_FIELDS + _ROTOR_FIELDS + _ESC_FIELDS,
    'Electric Ducted Fan':
        _COMMON_FIELDS + _MOTOR_FIELDS + _DUCTED_FAN_FIELDS + _ESC_FIELDS,
    'Internal Combustion Engine':
        _COMMON_FIELDS + _ENGINE_FIELDS + _PROPELLER_FIELDS,
    'Constant Speed Internal Combustion Engine':
        _COMMON_FIELDS + _ENGINE_FIELDS + _PROPELLER_FIELDS,
    'Turbojet': [
        ('Design Altitude',     'design_altitude'),
        ('Design Mach Number',  'design_mach_number'),
    ] + _COMMON_FIELDS + _TURBOJET_COMPONENT_FIELDS,
    'Turboprop': _COMMON_FIELDS + _TURBOPROP_COMPONENT_FIELDS,
}


def _network_type_for_ui(network_dict):
    type_str = network_dict.get('__type__', '')
    class_name = type_str.rsplit('.', 1)[-1] if type_str else ''
    return _NETWORK_TYPE_LABEL.get(class_name, 'Fuel')


_NACELLE_TYPE_LABEL = {
    'Nacelle':                    'Generic Nacelle',
    'Body_of_Revolution_Nacelle': 'Body of Revolution',
    'Stack_Nacelle':              'Stack Nacelle',
}


def _nacelle_seg_to_ui(segment):
    """Convert a raw RCAIDE nacelle segment dict to the NacelleSectionWidget data format."""
    return {
        "Segment Name":       segment.get("tag", ""),
        "Percent X Location": [segment.get("percent_x_location", 0), 0],
        "Percent Z Location": [segment.get("percent_z_location", 0), 0],
        "Height":             [segment.get("height", 0), 0],
        "Width":              [segment.get("width", 0), 0],
        "segment_type":       nacelle_segment_type_label_for_ui(segment),
    }


def _nacelle_dict_to_ui(nacelle):
    """Convert a stripped RCAIDE nacelle dict to the TurbofanWidget nacelle_data format."""
    def g(d, key, default=0):
        val = d.get(key, default) if isinstance(d, dict) else default
        return [val, 0]

    type_str = nacelle.get('__type__', '')
    class_name = type_str.rsplit('.', 1)[-1] if type_str else ''
    nacelle_type = _NACELLE_TYPE_LABEL.get(class_name, 'Body of Revolution')

    areas = nacelle.get('areas', {})
    if not isinstance(areas, dict):
        areas = {}

    sections_raw = nacelle.get('segments', {})
    if isinstance(sections_raw, dict):
        sections = [_nacelle_seg_to_ui(s) for s in sections_raw.values() if isinstance(s, dict)]
    elif isinstance(sections_raw, list):
        sections = [_nacelle_seg_to_ui(s) for s in sections_raw if isinstance(s, dict)]
    else:
        sections = []

    return {
        'Nacelle Type':   nacelle_type,
        'Nacelle Length': g(nacelle, 'length'),
        'Inlet Diameter': g(nacelle, 'inlet_diameter'),
        'Diameter':       g(nacelle, 'diameter'),
        'Nacelle Origin': [nacelle.get('origin', [[0, 0, 0]]), 0],
        'Wetted Area':    g(areas, 'wetted'),
        'Flow Through':   [nacelle.get('flow_through', False), 0],
        'Airfoil Type':   'None (Auto)',
        'sections':       sections,
    }


def _propulsor_dict_to_ui(p):
    """Convert a RCAIDE propulsor JSON dict to the GUI widget format for any propulsor type."""
    def g(d, *keys):
        for k in keys[:-1]:
            d = d.get(k, {}) if isinstance(d, dict) else {}
        val = d.get(keys[-1], 0) if isinstance(d, dict) else 0
        return [val, 0]

    type_str = p.get('__type__', '')
    class_name = type_str.rsplit('.', 1)[-1] if type_str else ''
    propulsor_type = _PROPULSOR_TYPE_LABEL.get(class_name, 'Turbofan')

    if propulsor_type == 'Turbofan':
        result = {
            'Propulsor Tag':                      p.get('tag', ''),
            'Propulsor Type':                     'Turbofan',
            'Origin':                             g(p, 'origin'),
            'Engine Length':                      g(p, 'length'),
            'Diameter':                           g(p, 'diameter'),
            'Bypass Ratio':                       g(p, 'bypass_ratio'),
            'Design Altitude':                    g(p, 'design_altitude'),
            'Design Mach Number':                 g(p, 'design_mach_number'),
            'Design Thrust':                      g(p, 'design_thrust'),
            'Fan Polytropic Efficiency':          g(p, 'fan', 'polytropic_efficiency'),
            'Fan Pressure Ratio':                 g(p, 'fan', 'pressure_ratio'),
            'Inlet Nozzle Polytropic Efficiency': g(p, 'inlet_nozzle', 'polytropic_efficiency'),
            'Inlet Nozzle Pressure Ratio':        g(p, 'inlet_nozzle', 'pressure_ratio'),
            'LPC Polytropic Efficiency':          g(p, 'low_pressure_compressor', 'polytropic_efficiency'),
            'LPC Pressure Ratio':                 g(p, 'low_pressure_compressor', 'pressure_ratio'),
            'HPC Polytropic Efficiency':          g(p, 'high_pressure_compressor', 'polytropic_efficiency'),
            'HPC Pressure Ratio':                 g(p, 'high_pressure_compressor', 'pressure_ratio'),
            'LPT Mechanical Efficiency':          g(p, 'low_pressure_turbine', 'mechanical_efficiency'),
            'LPT Polytropic Efficiency':          g(p, 'low_pressure_turbine', 'polytropic_efficiency'),
            'HPT Mechanical Efficiency':          g(p, 'high_pressure_turbine', 'mechanical_efficiency'),
            'HPT Polytropic Efficiency':          g(p, 'high_pressure_turbine', 'polytropic_efficiency'),
            'Combustor Efficiency':               g(p, 'combustor', 'efficiency'),
            'Combustor Pressure Loss Coeff':      g(p, 'combustor', 'alphac'),
            'Combustor Turbine Inlet Temp':       g(p, 'combustor', 'turbine_inlet_temperature'),
            'Combustor Pressure Ratio':           g(p, 'combustor', 'pressure_ratio'),
            'Core Nozzle Polytropic Efficiency':  g(p, 'core_nozzle', 'polytropic_efficiency'),
            'Core Nozzle Pressure Ratio':         g(p, 'core_nozzle', 'pressure_ratio'),
            'Fan Nozzle Polytropic Efficiency':   g(p, 'fan_nozzle', 'polytropic_efficiency'),
            'Fan Nozzle Pressure Ratio':          g(p, 'fan_nozzle', 'pressure_ratio'),
        }
        nacelle = p.get('nacelle')
        if isinstance(nacelle, dict):
            result['nacelle_data'] = _nacelle_dict_to_ui(nacelle)
        return result

    # Generic extraction for all BasePropulsorWidget subclasses
    field_specs = _PROPULSOR_FIELDS.get(propulsor_type, _COMMON_FIELDS)
    result = {
        'Propulsor Tag':  p.get('tag', ''),
        'Propulsor Type': propulsor_type,
    }
    for label, path in field_specs:
        parts = path.split('.')
        result[label] = g(p, *parts)
    return result


_DISTRIBUTOR_TYPE_LABEL = {
    'Fuel_Line':      'Fuel Line',
    'Electrical_Bus': 'Electrical Bus',
    'Coolant_Line':   'Coolant Line',
}

_BATTERY_TYPE_LABEL = {
    'Lithium_Ion_NMC':        'Lithium Ion NMC',
    'Lithium_Ion_LFP':        'Lithium Ion LFP',
    'Lithium_Sulfur':         'Lithium Sulfur',
    'Aluminum_Air':           'Aluminum Air',
    'Lithium_Air':            'Lithium Air',
    'Generic_Battery_Module': 'Generic',
}


def _distributor_dict_to_ui(fl, container_key='fuel_lines'):
    """Convert a RCAIDE Fuel_Line/Bus/Coolant_Line JSON dict to distributor GUI format."""
    assigned_raw = fl.get('assigned_propulsors', [])
    if is_unit_argument_pair(assigned_raw):
        assigned_raw = assigned_raw[0]
    if assigned_raw and isinstance(assigned_raw[0], list):
        assigned_propulsors = list(assigned_raw[0])
    else:
        assigned_propulsors = [x for x in assigned_raw if isinstance(x, str)]

    # Fuel tanks from fuel_tanks container
    tanks = fl.get('fuel_tanks', {})
    assigned_sources = (
        [k for k in tanks.keys() if k != '__type__']
        if isinstance(tanks, dict) else []
    )
    # Battery modules from battery_modules container (electrical buses)
    batteries = fl.get('battery_modules', {})
    if isinstance(batteries, dict):
        assigned_sources += [k for k in batteries.keys() if k != '__type__']

    type_str = fl.get('__type__', '')
    class_name = type_str.rsplit('.', 1)[-1] if type_str else ''
    dist_type = _DISTRIBUTOR_TYPE_LABEL.get(class_name, {
        'fuel_lines': 'Fuel Line',
        'busses': 'Electrical Bus',
        'coolant_lines': 'Coolant Line',
    }.get(container_key, 'Fuel Line'))

    result = {
        'distributor name':    fl.get('tag', ''),
        'distributor_type':    dist_type,
        'assigned_propulsors': assigned_propulsors,
        'assigned_sources':    assigned_sources,
    }
    # Preserve bus-specific fields when loading an electrical bus
    if dist_type == 'Electrical Bus':
        result['Efficiency']        = [fl.get('efficiency',        1.0), 0]
        result['Voltage']           = [fl.get('voltage',           0.0), 0]
        result['Power Split Ratio'] = [fl.get('power_split_ratio', 1.0), 0]
        result['Charging C-Rate']   = [fl.get('charging_c_rate',   1.0), 0]
    return result


_FUEL_TANK_TYPE_LABEL = {
    'Fuel_Tank':         'Fuel Tank',
    'Non_Integral_Tank': 'Non-Integral Tank',
    'Integral_Tank':     'Integral Tank',
    'Cryogenic_Tank':    'Cryogenic Tank',
}

_FUEL_TYPE_LABEL = {
    'Jet_A1':             'Jet A1',
    'Jet_A':              'Jet A',
    'JP7':                'JP7',
    'Aviation_Gasoline':  'Aviation Gasoline',
    'Liquid_Hydrogen':    'Liquid Hydrogen',
    'Liquid_Natural_Gas': 'Liquid Natural Gas',
}


def _fuel_tank_dict_to_ui(tank):
    """Convert a RCAIDE Fuel_Tank JSON dict to FuelTankWidget GUI format."""
    def g(d, key, default=0):
        """Return value from dict, preserving [value, unit_index] pairs as-is."""
        val = d.get(key, default) if isinstance(d, dict) else default
        # If already a [value, unit_index] pair (list/tuple of length 2 with int tail), pass through
        if isinstance(val, (list, tuple)) and len(val) == 2 and isinstance(val[-1], int):
            return val
        return [val, 0]

    type_str   = tank.get('__type__', '') if isinstance(tank, dict) else ''
    class_name = type_str.rsplit('.', 1)[-1] if type_str else ''
    tank_type  = _FUEL_TANK_TYPE_LABEL.get(class_name, 'Fuel Tank')

    fuel      = tank.get('fuel', {}) if isinstance(tank, dict) else {}
    fuel_type_str   = fuel.get('__type__', '') if isinstance(fuel, dict) else ''
    fuel_class_name = fuel_type_str.rsplit('.', 1)[-1] if fuel_type_str else ''
    fuel_type       = _FUEL_TYPE_LABEL.get(fuel_class_name, 'Jet A1')

    fuel_props = fuel.get('mass_properties', {}) if isinstance(fuel, dict) else {}
    vol_props  = tank.get('volume_properties', fuel.get('volume_properties', {}))

    lengths   = tank.get('lengths',   {}) if isinstance(tank, dict) else {}
    widths    = tank.get('widths',    {}) if isinstance(tank, dict) else {}
    heights   = tank.get('heights',   {}) if isinstance(tank, dict) else {}
    diameters = tank.get('diameters', {}) if isinstance(tank, dict) else {}

    transverse_raw = tank.get('transverse_tank', False)
    transverse_val = transverse_raw[0] if isinstance(transverse_raw, (list, tuple)) else transverse_raw

    return {
        'Source Name':               tank.get('tag', ''),
        'source_type':               'Fuel Tank',
        'tank_type':                 tank_type,
        'fuel_type':                 fuel_type,
        'Fuel Tank Origin':          g(tank,       'origin',            [[[0, 0, 0]], 0]),
        'Fuel Origin':               g(fuel,       'origin',            [[[0, 0, 0]], 0]),
        'Center of Gravity':         g(fuel_props, 'center_of_gravity', [[[0, 0, 0]], 0]),
        'Mass':                      g(fuel_props, 'mass',              0),
        'Internal Volume':           g(vol_props,  'net_volume',        0),
        'wing_tag':                  tank.get('wing_tag', '') or '',
        'geometry_type':             tank.get('geometry_type', 'cylindrical'),
        'transverse_tank':           [transverse_val, 0],
        'External Length':           g(lengths,   'external', 0),
        'External Width':            g(widths,    'external', 0),
        'External Height':           g(heights,   'external', 0),
        'External Diameter':         g(diameters, 'external', 0),
        'Design Altitude':           g(tank,  'design_altitude',               0),
        'Design Inlet Temperature':  g(tank,  'design_inlet_temperature',      0),
        'Ullage Volume Fraction':    g(tank,  'ullage_volume_fraction',         0.07),
        'Safety Factor':             g(tank,  'safety_factor',                  1.6),
        'Pressure Factor':           g(tank,  'pressure_factor',                5),
        'Accessories Weight Factor': g(tank,  'tank_accesories_weight_factor',  1.5),
    }


def _battery_module_dict_to_ui(module):
    """Convert a RCAIDE battery module JSON dict to BatteryModuleWidget GUI format."""
    def g(d, *keys):
        for k in keys[:-1]:
            d = d.get(k, {}) if isinstance(d, dict) else {}
        val = d.get(keys[-1], 0) if isinstance(d, dict) else 0
        return [val, 0]

    type_str = module.get('__type__', '')
    class_name = type_str.rsplit('.', 1)[-1] if type_str else ''
    chemistry = _BATTERY_TYPE_LABEL.get(class_name, 'Lithium Ion NMC')

    return {
        'Source Name':          module.get('tag', ''),
        'source_type':          'Battery Module',
        'Chemistry':            chemistry,
        'Capacity':             [module.get('capacity',  0.0), 0],
        'Length':               [module.get('length',    0.0), 0],
        'Width':                [module.get('width',     0.0), 0],
        'Height':               [module.get('height',    0.0), 0],
        'Series Cells':         g(module, 'electrical_configuration', 'series'),
        'Parallel Cells':       g(module, 'electrical_configuration', 'parallel'),
        'Normal Cell Count':    g(module, 'geometric_configuration',  'normal_count'),
        'Parallel Cell Count':  g(module, 'geometric_configuration',  'parallel_count'),
        'Stacking Rows':        g(module, 'geometric_configuration',  'stacking_rows'),
    }


_SYSTEM_TYPE_LABEL = {
    'Avionics':               'Avionics',
    'Auxiliary_Power_Unit':   'Auxiliary Power Unit',
    'Cabin_Loads':            'Cabin Loads',
    'Electrical':             'Electrical',
    'Environmental_Controls': 'Environmental Controls',
    'Flight_Controls':        'Flight Controls',
    'Furnishings':            'Furnishings',
    'Hydraulics':             'Hydraulics',
    'Ice_Protection':         'Ice Protection',
    'Instruments':            'Instruments',
    'Water_Tank':             'Water Tank',
}


def _system_dict_to_ui(sys_dict):
    """Convert one RCAIDE system JSON dict to the SystemWidget data format."""
    type_str = sys_dict.get('__type__', '')
    class_name = type_str.rsplit('.', 1)[-1] if type_str else ''
    sys_type = _SYSTEM_TYPE_LABEL.get(class_name, 'Avionics')
    return {
        'System Type':      sys_type,
        'System Name':      sys_dict.get('tag', ''),
        'Origin':           [sys_dict.get('origin',           [[0, 0, 0]]), 0],
        'Power Draw':       [sys_dict.get('power_draw',       0.0),         0],
        'Uninstalled Mass': [sys_dict.get('uninstalled_mass', 0.0),         0],
    }


def _network_dict_to_ui(net_dict):
    """Convert one RCAIDE network JSON dict to the PowertrainFrame GUI data format."""
    net_type = _network_type_for_ui(net_dict)

    propulsor_data = []
    propulsors = net_dict.get('propulsors', {})
    if isinstance(propulsors, dict):
        for k, v in propulsors.items():
            if k == '__type__' or not isinstance(v, dict):
                continue
            propulsor_data.append(_propulsor_dict_to_ui(v))

    distributor_data = []
    source_by_tag = {}
    for container_key in ('fuel_lines', 'busses', 'coolant_lines'):
        container = net_dict.get(container_key, {})
        if not isinstance(container, dict):
            continue
        for k, fl in container.items():
            if k == '__type__' or not isinstance(fl, dict):
                continue
            distributor_data.append(_distributor_dict_to_ui(fl, container_key))

            # Collect fuel tank sources
            tanks = fl.get('fuel_tanks', {})
            if isinstance(tanks, dict):
                for t_key, t_val in tanks.items():
                    if t_key != '__type__' and isinstance(t_val, dict) and t_key not in source_by_tag:
                        source_by_tag[t_key] = ('fuel_tank', t_val)

            # Collect battery module sources (from electrical buses)
            batteries = fl.get('battery_modules', {})
            if isinstance(batteries, dict):
                for b_key, b_val in batteries.items():
                    if b_key != '__type__' and isinstance(b_val, dict) and b_key not in source_by_tag:
                        source_by_tag[b_key] = ('battery', b_val)

    source_data = []
    for kind, v in source_by_tag.values():
        if kind == 'battery':
            source_data.append(_battery_module_dict_to_ui(v))
        else:
            source_data.append(_fuel_tank_dict_to_ui(v))

    system_data = []
    systems_container = net_dict.get('systems', {})
    if isinstance(systems_container, dict):
        for k, sys_val in systems_container.items():
            if k == '__type__' or not isinstance(sys_val, dict):
                continue
            system_data.append(_system_dict_to_ui(sys_val))

    return {
        'energy network selected': net_type,
        'powertrain': {
            'distributor data': distributor_data,
            'source data':      source_data,
            'propulsor data':   propulsor_data,
            'system data':      system_data,
            'converter data':   [],
        }
    }


def vehicle_dict_to_ui_list_structure(vehicle_dict):
    """Convert a stripped rcaide_vehicle dict to the 7-slot UI structure."""
    from tabs.geometry.frames.booms.boom_frame import BoomFrame
    from tabs.geometry.frames.cargo_bays.cargo_bay_frame import CargoBayFrame
    from tabs.geometry.frames.fuselages.fuselage_frame import FuselageFrame
    from tabs.geometry.frames.landing_gears.landing_gear_frame import LandingGearFrame
    from tabs.geometry.frames.powertrain.powertrain_frame import PowertrainFrame
    from tabs.geometry.frames.wings.wings_frame import WingsFrame

    def wing_segment_to_ui(segment):
        airfoil      = segment.get("airfoil", {}) or {}
        af_type_str  = airfoil.get("__type__", "") if isinstance(airfoil, dict) else ""
        af_class     = af_type_str.rsplit(".", 1)[-1] if af_type_str else ""
        naca_code    = airfoil.get("NACA_4_Series_code", None) if isinstance(airfoil, dict) else None
        coord_file   = airfoil.get("coordinate_file", None)    if isinstance(airfoil, dict) else None

        if af_class == "NACA_4_Series_Airfoil" and naca_code:
            af_ui_type = "NACA 4-Series"
        elif coord_file:
            af_ui_type = "Coordinate File"
        else:
            af_ui_type = None

        return {
            "Segment Name":          segment.get("tag", ""),
            "Percent Span Location": [segment.get("percent_span_location", 0), 0],
            "Twist":                 [segment.get("twist", 0), 0],
            "Root Chord Percent":    [segment.get("root_chord_percent", 0), 0],
            "Thickness to Chord":    [segment.get("thickness_to_chord", 0), 0],
            "Dihedral Outboard":     [segment.get("dihedral_outboard", 0), 0],
            "Quarter Chord Sweep":   [segment.get("sweeps", {}).get("quarter_chord", 0), 0],
            "Has Fuel Tank":         [bool(segment.get("Fuel_Tank")), 0],
            "Has Aft Fuel Tank":     [bool(segment.get("Aft_Fuel_Tank")), 0],
            "Airfoil Type":          af_ui_type,
            "Airfoil Code":          naca_code or "",
            "Airfoil Coordinate File Path": coord_file or "",
        }

    def wing_control_surface_to_ui(cs):
        cs_type = {
            "aileron": 0, "slat": 1, "flap": 2,
            "elevator": 3, "rudder": 4, "spoiler": 5,
        }.get(cs.get("tag", "").lower(), 0)
        return {
            "CS name":            cs.get("tag", ""),
            "CS type":            cs_type,
            "Span Fraction Start":[cs.get("span_fraction_start", 0), 0],
            "Span Fraction End":  [cs.get("span_fraction_end", 0), 0],
            "Deflection":         [cs.get("deflection", 0), 0],
            "Chord Fraction":     [cs.get("chord_fraction", 0), 0],
            "Number of Slots":    [1, 0],
        }

    def fuselage_segment_to_ui(segment):
        return {
            "Segment Name":       segment.get("tag", ""),
            "Percent X Location": [segment.get("percent_x_location", 0), 0],
            "Percent Z Location": [segment.get("percent_z_location", 0), 0],
            "Height":             [segment.get("height", 0), 0],
            "Width":              [segment.get("width", 0), 0],
            "segment_type":       fuselage_segment_type_label_for_ui(segment),
        }

    def boom_segment_to_ui(segment):
        return {
            "Segment Name":       segment.get("tag", ""),
            "Percent X Location": [segment.get("percent_x_location", 0), 0],
            "Percent Z Location": [segment.get("percent_z_location", 0), 0],
            "Height":             [segment.get("height", 0), 0],
            "Width":              [segment.get("width", 0), 0],
            "segment_type":       boom_segment_type_label_for_ui(segment),
        }

    def nacelle_segment_to_ui(segment):
        return {
            "Segment Name":       segment.get("tag", ""),
            "Percent X Location": [segment.get("percent_x_location", 0), 0],
            "Percent Z Location": [segment.get("percent_z_location", 0), 0],
            "Height":             [segment.get("height", 0), 0],
            "Width":              [segment.get("width", 0), 0],
            "segment_type":       nacelle_segment_type_label_for_ui(segment),
        }

    # Preserve nested cabin/class data through GUI load/save.
    def cabin_class_type_label_for_ui(class_dict):
        # Get class type from saved RCAIDE type.
        type_str = class_dict.get('__type__', '')
        class_name = type_str.rsplit('.', 1)[-1] if type_str else ''
        return class_name if class_name in {"Economy", "Business", "First"} else "Economy"

    def cabin_class_to_ui(class_dict):
        # Convert one cabin class to GUI data.
        # RCAIDE may use either spelling.
        seats_abreast = class_dict.get("number_of_seats_abrest", class_dict.get("number_of_seats_abreast", 0))
        number_of_rows = class_dict.get("number_of_rows", 0)
        number_of_seats = class_dict.get("number_of_seats", 0)
        # Fill missing seat count.
        if not number_of_seats and seats_abreast and number_of_rows:
            number_of_seats = seats_abreast * number_of_rows

        ui_class = {
            "class_type":              cabin_class_type_label_for_ui(class_dict),
            "Number of Passengers":    [class_dict.get("number_of_passengers", 0), 0],
            "Number of Seats Abreast": [seats_abreast, 0],
            "Number of Rows":          [number_of_rows, 0],
            "Number of Seats":         [number_of_seats, 0],
            "Seat Width":              [class_dict.get("seat_width", 0), 0],
            "Seat Arm Rest Width":     [class_dict.get("seat_arm_rest_width", 0), 0],
            "Seat Length":             [class_dict.get("seat_length", 0), 0],
            "Seat Pitch":              [class_dict.get("seat_pitch", 0), 0],
            "Aisle Width":             [class_dict.get("aisle_width", 0), 0],
        }

        # Keep hidden RCAIDE fields.
        for key, value in class_dict.items():
            if key not in ui_class and key != "__type__":
                ui_class[key] = make_json_safe(value)
        return ui_class

    def cabin_type_label_for_ui(cabin_dict):
        # Get cabin type from saved RCAIDE type.
        type_str = cabin_dict.get('__type__', '')
        class_name = type_str.rsplit('.', 1)[-1] if type_str else ''
        return "Side" if class_name == "Side_Cabin" else "Regular"

    def cabin_to_ui(cabin_dict):
        # Convert one cabin to GUI data.
        classes = cabin_dict.get("classes", {})
        if isinstance(classes, dict):
            class_list = [cabin_class_to_ui(c) for c in classes.values() if is_mapping(c)]
        elif isinstance(classes, list):
            class_list = [cabin_class_to_ui(c) for c in classes if is_mapping(c)]
        else:
            class_list = []

        ui_cabin = {
            "Cabin Name":                cabin_dict.get("tag", ""),
            "cabin_type":                cabin_type_label_for_ui(cabin_dict),
            "Number of Passengers":      [cabin_dict.get("number_of_passengers", 0), 0],
            "Number of Seats":           [cabin_dict.get("number_of_seats", 0), 0],
            "Type A Door Length":        [cabin_dict.get("type_a_door_length", 0), 0],
            "Galley Lavatory Length":    [cabin_dict.get("galley_lavatory_length", 0), 0],
            "Emergency Exit Seat Pitch": [cabin_dict.get("emergency_exit_seat_pitch", 0), 0],
            "Length":                    [cabin_dict.get("length", 0), 0],
            "Width":                     [cabin_dict.get("width", 0), 0],
            "Height":                    [cabin_dict.get("height", 0), 0],
            "Wide Body":                 [cabin_dict.get("wide_body", False), 0],
            "classes":                   class_list,
        }

        for key, value in cabin_dict.items():
            if key not in ui_cabin and key not in {"__type__", "classes"}:
                ui_cabin[key] = make_json_safe(value)
        return ui_cabin

    def cabins_to_ui(cabins):
        # Convert all cabins to GUI data.
        if isinstance(cabins, dict):
            return [cabin_to_ui(c) for c in cabins.values() if is_mapping(c)]
        if isinstance(cabins, list):
            return [cabin_to_ui(c) for c in cabins if is_mapping(c)]
        return []

    def to_ui_format(component_dict, frame_class):
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

        if frame_class.__name__ == 'WingsFrame':
            if 'Spans Projected' not in ui_dict:
                ui_dict["Spans Projected"]         = [component_dict.get("spans", {}).get("projected", 0), 0]
                ui_dict["Reference Area"]          = [component_dict.get("areas", {}).get("reference", 0), 0]
                ui_dict["Wetted Area"]             = [component_dict.get("areas", {}).get("wetted", 0), 0]
                ui_dict["Root Chord"]              = [component_dict.get("chords", {}).get("root", 0), 0]
                ui_dict["Tip Chord"]               = [component_dict.get("chords", {}).get("tip", 0), 0]
                ui_dict["Mean Aerodynamic Chord"]  = [component_dict.get("chords", {}).get("mean_aerodynamic", 0), 0]
                ui_dict["Quarter Chord Sweep Angle"] = [component_dict.get("sweeps", {}).get("quarter_chord", 0), 0]
                ui_dict["Leading Edge Sweep Angle"]  = [component_dict.get("sweeps", {}).get("leading_edge", 0), 0]
                ui_dict["Root Chord Twist Angle"]  = [component_dict.get("twists", {}).get("root", 0), 0]
                ui_dict["Tip Chord Twist Angle"]   = [component_dict.get("twists", {}).get("tip", 0), 0]
                ui_dict["Taper"]                   = [component_dict.get("taper", 0), 0]
                ui_dict["Dihedral"]                = [component_dict.get("dihedral", 0), 0]
                ui_dict["Aspect Ratio"]            = [component_dict.get("aspect_ratio", 0), 0]
                ui_dict["Thickness to Chord"]      = [component_dict.get("thickness_to_chord", 0), 0]
                ui_dict["Aerodynamic Center"]      = [component_dict.get("aerodynamic_center", [0, 0, 0]), 0]
                ui_dict["Origin"]                  = [component_dict.get("origin", [0, 0, 0]), 0]
                ui_dict["Vertical"]                = [component_dict.get("vertical", False), 0]
                ui_dict["X-Y Plane Symmetric"]     = [component_dict.get("xy_plane_symmetric", False), 0]
                ui_dict["High Lift"]               = [component_dict.get("high_lift", False), 0]
                ui_dict["X-Z Plane Symmetric"]     = [component_dict.get("xz_plane_symmetric", False), 0]
                ui_dict["T-Tail"]                  = [component_dict.get("t_tail", False), 0]
                ui_dict["Y-Z Plane Symmetric"]     = [component_dict.get("yz_plane_symmetric", False), 0]
                ui_dict["Dynamic Pressure Ratio"]  = [component_dict.get("dynamic_pressure_ratio", 0), 0]
                ui_dict["Exposed Root Chord Offset"] = [component_dict.get("exposed_root_chord_offset", 0), 0]

            ui_dict.setdefault("wing_type", wing_type_label_for_ui(component_dict))

            segments = ui_dict.pop("segments", {})
            if isinstance(segments, dict):
                ui_dict["sections"] = [wing_segment_to_ui(s) for s in segments.values() if is_mapping(s)]
            elif isinstance(segments, list):
                ui_dict["sections"] = [wing_segment_to_ui(s) for s in segments if is_mapping(s)]
            else:
                ui_dict["sections"] = []

            control_surfaces = ui_dict.get("control_surfaces", [])
            if isinstance(control_surfaces, dict):
                ui_dict["control_surfaces"] = [wing_control_surface_to_ui(cs) for cs in control_surfaces.values() if is_mapping(cs)]
            elif isinstance(control_surfaces, list):
                ui_dict["control_surfaces"] = [wing_control_surface_to_ui(cs) for cs in control_surfaces if is_mapping(cs)]
            else:
                ui_dict["control_surfaces"] = []

            ui_dict["cabins"] = cabins_to_ui(component_dict.get("cabins", {}))
            ui_dict["side_cabins"] = cabins_to_ui(component_dict.get("side_cabins", {}))

        if frame_class.__name__ == 'BoomFrame':
            segments = component_dict.get("segments", {})
            if isinstance(segments, dict):
                ui_dict["sections"] = [boom_segment_to_ui(s) for s in segments.values() if is_mapping(s)]
            elif isinstance(segments, list):
                ui_dict["sections"] = [boom_segment_to_ui(s) for s in segments if is_mapping(s)]
            else:
                ui_dict["sections"] = []

        if frame_class.__name__ == 'FuselageFrame':
            segments = component_dict.get("segments", {})
            if isinstance(segments, dict):
                ui_dict["segments"] = [fuselage_segment_to_ui(s) for s in segments.values() if is_mapping(s)]
            elif isinstance(segments, list):
                ui_dict["segments"] = [fuselage_segment_to_ui(s) for s in segments if is_mapping(s)]
            else:
                ui_dict["segments"] = []

            # Keep loaded cabins attached.
            ui_dict["cabins"] = cabins_to_ui(component_dict.get("cabins", {}))

        return ui_dict

    ui_structure = [[] for _ in range(7)]
    ui_structure[0] = None

    if "booms" in vehicle_dict and vehicle_dict["booms"]:
        ui_structure[1] = [to_ui_format(b, BoomFrame) for b in vehicle_dict["booms"].values() if is_mapping(b)]

    if "cargo_bays" in vehicle_dict and vehicle_dict["cargo_bays"]:
        ui_structure[2] = [to_ui_format(c, CargoBayFrame) for c in vehicle_dict["cargo_bays"].values() if is_mapping(c)]

    if "fuselages" in vehicle_dict and vehicle_dict["fuselages"]:
        ui_structure[3] = [to_ui_format(f, FuselageFrame) for f in vehicle_dict["fuselages"].values() if is_mapping(f)]

    _LG_TYPE_LABEL = {
        'Landing_Gear':      'General Gear',
        'Nose_Landing_Gear': 'Nose Gear',
        'Main_Landing_Gear': 'Main Gear',
    }

    def _lg_to_ui(lg_dict):
        ui = to_ui_format(lg_dict, LandingGearFrame)
        type_str   = lg_dict.get('__type__', '')
        class_name = type_str.rsplit('.', 1)[-1] if type_str else ''
        ui['landing_gear_type'] = _LG_TYPE_LABEL.get(class_name, 'General Gear')
        return ui

    if "landing_gears" in vehicle_dict and vehicle_dict["landing_gears"]:
        ui_structure[4] = [_lg_to_ui(l) for l in vehicle_dict["landing_gears"].values() if is_mapping(l)]

    if "powertrains" in vehicle_dict and vehicle_dict["powertrains"]:
        ui_structure[5] = [to_ui_format(p, PowertrainFrame) for p in vehicle_dict["powertrains"].values() if is_mapping(p)]
    elif "networks" in vehicle_dict and vehicle_dict["networks"]:
        for k, network in vehicle_dict["networks"].items():
            if k == "__type__" or not is_mapping(network):
                continue
            ui_structure[5].append(_network_dict_to_ui(network))

    if "wings" in vehicle_dict and vehicle_dict["wings"]:
        ui_structure[6] = [to_ui_format(w, WingsFrame) for w in vehicle_dict["wings"].values() if is_mapping(w)]

    return ui_structure


# ----------------------------------------------------------------------------------------------------------------------
#  Config serialisation helpers
# ----------------------------------------------------------------------------------------------------------------------

_DIFF_SKIP = frozenset({'_component_root_map', '_energy_network_root_map', '_base', '_diff'})


def _coerce_leaf(new_val, obj, key):
    """Coerce a JSON list back to numpy array when the target attribute is already an ndarray."""
    if isinstance(new_val, list):
        try:
            if isinstance(obj[key], np.ndarray):
                return np.array(new_val)
        except Exception:
            pass
    return new_val


def _apply_diff_to_obj(obj, diff_dict):
    """Walk a stripped diff dict and apply every leaf value to obj via key navigation."""
    for key, value in diff_dict.items():
        if key == '__type__':
            continue
        if isinstance(value, (dict, OrderedDict)):
            try:
                child = obj[key]
                _apply_diff_to_obj(child, value)
            except (KeyError, TypeError, AttributeError):
                pass
        else:
            try:
                obj[key] = _coerce_leaf(value, obj, key)
            except (KeyError, TypeError, AttributeError):
                pass


def _serialise_config_entry(config):
    """Serialize one Config object via store_diff() into a JSON-safe diff entry."""
    config.store_diff()
    diff = config._diff

    diff_raw = {}
    for k in diff.keys():
        if k in _DIFF_SKIP:
            continue
        diff_raw[k] = _build_dict_r_with_types(diff[k])

    diff_serialised = add_default_unit_arguments(make_json_safe(diff_raw))

    tv = type(config)
    module   = getattr(tv, '__module__', '') or ''
    qualname = getattr(tv, '__qualname__', '') or ''

    return {
        "__type__": f"{module}.{qualname}",
        "tag":      config.tag,
        "diff":     diff_serialised,
    }


# ----------------------------------------------------------------------------------------------------------------------
#  Public read / write API
# ----------------------------------------------------------------------------------------------------------------------

def write_to_json(include_learner=True):
    config_entries = []
    for _, config in rcaide_configs.items():
        try:
            config_entries.append(_serialise_config_entry(config))
        except Exception:
            pass

    data = {
        "rcaide_vehicle": add_default_unit_arguments(
            make_json_safe(_build_dict_base_with_types(vehicle))
        ),
        "config_data":   config_entries,
        "analysis_data": analysis_data,
        "mission_data":  mission_data,
    }
    if include_learner:
        data["learner_data"] = learner_data
        data["learner_comparison_data"] = learner_comparison_data
    return json.dumps(data, indent=4)


def _patch_cryogenic_tank_defaults(vehicle):
    """Fill None fields on Cryogenic_Tanks that were missing from old JSONs."""
    from RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks import Cryogenic_Tank as _CryoTank
    default_alt = (getattr(getattr(vehicle, 'flight_envelope', None),
                           'design_cruise_altitude', None) or 0.0)
    _CRYO_DEFAULTS = {
        'design_altitude':           default_alt,
        'design_inlet_temperature':  20.0,    # K — liquid hydrogen boiling point
        'design_heat_flux':          20.0,    # W/m²
        'design_total_heat_transfer': 2000.0, # W
        'ullage_volume_fraction':    0.07,
    }
    for net in getattr(vehicle, 'networks', {}).values():
        for fl in getattr(net, 'fuel_lines', {}).values():
            for tank in getattr(fl, 'fuel_tanks', {}).values():
                if not isinstance(tank, _CryoTank):
                    continue
                for attr, default in _CRYO_DEFAULTS.items():
                    if getattr(tank, attr, None) is None:
                        setattr(tank, attr, default)


def read_from_json(data_str, source_dir=None):
    global rcaide_vehicle, vehicle, rcaide_configs, config_data, analysis_data, mission_data, learner_data, learner_comparison_data, learner_vehicle_built, propulsor_names, rcaide_analyses, rcaide_results
    from RCAIDE.Library.Components.Configs.Config import Config
    from RCAIDE.Input_Output.import_data import analyses_setup as _analyses_setup

    data = json.loads(data_str, object_pairs_hook=OrderedDict)
    rcaide_vehicle_dict  = data["rcaide_vehicle"]
    rcaide_vehicle_clean = strip_unit_arguments(rcaide_vehicle_dict)
    repair_local_file_paths(rcaide_vehicle_clean, source_dir)

    vehicle = RCAIDE.Vehicle()
    if isinstance(rcaide_vehicle_clean, OrderedDict):
        vehicle.update(read_RCAIDE_json_dict(rcaide_vehicle_clean))
        restore_vehicle_components(vehicle)    # rebuilds all top-level containers
        restore_airfoil_components(vehicle)    # fixes embedded airfoil objects
        restore_typed_subcomponents(vehicle)   # fixes Fan, Combustor, Fuel_Line, etc.
        _patch_cryogenic_tank_defaults(vehicle)

    if "geometry_data" in data and data["geometry_data"]:
        rcaide_vehicle = data["geometry_data"]
    else:
        rcaide_vehicle    = vehicle_dict_to_ui_list_structure(rcaide_vehicle_clean)
        rcaide_vehicle[0] = vehicle_to_ui_format(vehicle)

    rcaide_configs = Config.Container()
    for entry in data.get("config_data", []):
        if not isinstance(entry, dict):
            continue
        name = entry.get("tag", "")
        if not name:
            continue
        config = Config(vehicle)
        config.tag = name
        diff_clean = strip_unit_arguments(entry.get("diff", {}))
        _apply_diff_to_obj(config, diff_clean)
        rcaide_configs.append(config)

    config_data   = []
    analysis_data = data.get("analysis_data", [])
    mission_data  = data.get("mission_data",  [])
    learner_data  = data.get("learner_data",  {})
    learner_comparison_data = data.get("learner_comparison_data", [])
    learner_vehicle_built = bool(learner_data)
    # Loaded aircraft files do not include runtime mission results; clear any
    # previous run so the Results Viewer cannot show stale data for a new file.
    rcaide_results = None

    rcaide_analyses = _analyses_setup(analysis_data, rcaide_configs)

    propulsor_names = [[]]
    try:
        for network in vehicle.networks:
            for prop in network.propulsors:
                propulsor_names[0].append(prop.tag)
    except Exception:
        pass
