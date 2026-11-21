# tests/test_analyses.py
#
# Regression tests for RCAIDE_GUI: JSON loading and analysis runner pipeline.
# Runners are called directly after building state via rcaide_io; missions are built by the Mission tab (offscreen Qt).
#
# Run with:  pytest tests/test_analyses.py -v
#            pytest tests/test_analyses.py -v -k "cessna"  (single aircraft)
#
# Pattern mirrors RCAIDE VnV/test_digital_hangar.py and test_tutorials.py:
#   load JSON → populate rcaide_io globals → call runner → check result shape/type.

import os
import sys
import json
import time

import pytest
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Make sure RCAIDE_GUI root is on the path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PyQt6.QtWidgets import QApplication
QT_APP = QApplication.instance() or QApplication(sys.argv)

import rcaide_io
import RCAIDE
from utilities import APP_DATA

AIRCRAFT_DIR = os.path.join(APP_DATA, 'aircraft')

# ---------------------------------------------------------------------------
# Helper: find all aircraft JSON files
# ---------------------------------------------------------------------------

def _aircraft_jsons():
    return sorted(
        f for f in os.listdir(AIRCRAFT_DIR)
        if f.endswith('.json')
    )


# ---------------------------------------------------------------------------
# Helper: load a JSON file into rcaide_io globals
# ---------------------------------------------------------------------------

def load_aircraft(filename):
    """Populate rcaide_io globals from an aircraft JSON file."""
    path = os.path.join(AIRCRAFT_DIR, filename)
    with open(path) as fh:
        data_str = fh.read()
    rcaide_io.read_from_json(data_str, source_dir=AIRCRAFT_DIR)


# ---------------------------------------------------------------------------
# Helper: build rcaide_mission with the GUI Mission tab (offscreen Qt)
# ---------------------------------------------------------------------------

def build_mission():
    """Build rcaide_io.rcaide_mission from rcaide_io.mission_data the way the GUI does, through the Mission tab."""
    from tabs.mission.mission import MissionWidget
    MissionWidget().load_from_values()
    return rcaide_io.rcaide_mission


# ---------------------------------------------------------------------------
# Helper: first config tag in rcaide_io.rcaide_analyses
# ---------------------------------------------------------------------------

def first_config_tag():
    analyses = getattr(rcaide_io, 'rcaide_analyses', None)
    if not analyses:
        pytest.skip('No analyses available — JSON may lack analysis_data.')
    return next(iter(analyses))


# ===========================================================================
# 1. JSON loading — parametrize over every aircraft file
# ===========================================================================

@pytest.mark.parametrize('filename', _aircraft_jsons())
def test_json_load(filename):
    """Every aircraft JSON must load without error and populate core state."""
    t0 = time.time()
    load_aircraft(filename)
    elapsed = time.time() - t0

    assert rcaide_io.vehicle is not None, 'vehicle not populated'
    assert rcaide_io.rcaide_configs is not None, 'configs not populated'
    assert len(rcaide_io.rcaide_configs) > 0, 'config list is empty'

    print(f'  {filename}: {len(rcaide_io.rcaide_configs)} configs, {elapsed:.2f}s')


# ===========================================================================
# 2. Stall speed — no state needed, pure arithmetic
# ===========================================================================

def test_stall_speed():
    """Stall speed must be a positive scalar in m/s."""
    from tabs.performance.analysis_registry import run_stall_speed
    result = run_stall_speed(
        {
            'Vehicle Mass (kg)':   1156.0,
            'Reference Area (m²)': 16.2,
            'Altitude (m)':        0.0,
            'Max CL':              1.5,
        },
        _config_tag=None,
    )
    assert isinstance(result, (int, float, np.floating)), 'result should be a scalar'
    assert result > 0, 'stall speed must be positive'
    print(f'  Stall speed: {result:.2f} m/s')


# ===========================================================================
# 3. Take-off field length
# ===========================================================================

def test_tofl_atr72():
    """TOFL must return a positive length for the ATR-72 takeoff config."""
    from tabs.performance.analysis_registry import run_tofl
    load_aircraft('ATR_72.json')
    result = run_tofl(
        {
            'Altitude (m)':           0.0,
            'Delta ISA (K)':          0.0,
            'Takeoff Weight (kg)':    0.0,   # uses vehicle.mass_properties.takeoff
            'Compute 2nd Seg. Climb': False,
        },
        config_tag='takeoff',
    )
    tofl = result[0] if isinstance(result, tuple) else result
    assert tofl > 0, 'TOFL must be positive'
    print(f'  ATR-72 TOFL: {tofl:.1f} m')


# ===========================================================================
# 4. Landing field length
# ===========================================================================

def test_lfl_atr72():
    """LFL must return a positive length for the ATR-72 landing config."""
    from tabs.performance.analysis_registry import run_lfl
    load_aircraft('ATR_72.json')
    result = run_lfl(
        {
            'Altitude (m)':        0.0,
            'Delta ISA (K)':       0.0,
            'Landing Weight (kg)': 0.0,   # uses vehicle.mass_properties.landing
        },
        config_tag='landing',
    )
    assert result > 0, 'LFL must be positive'
    print(f'  ATR-72 LFL: {result:.1f} m')


# ===========================================================================
# 5. V-n diagram
# ===========================================================================

def test_vn_diagram_cessna_172():
    """V-n diagram must produce finite maneuvering speeds."""
    from tabs.performance.analysis_registry import run_vn_diagram
    load_aircraft('Cessna_172.json')
    result = run_vn_diagram(
        {'Altitude (m)': 0.0, 'Delta ISA (K)': 0.0},
        config_tag='cruise',
    )
    assert hasattr(result, 'Va'), 'result missing Va'
    assert result.Va.positive > 0, 'Va positive must be > 0'
    print(f'  Cessna 172 Va+: {result.Va.positive:.1f} KEAS, Vc: {result.Vc:.1f} KEAS')


# ===========================================================================
# 6. Aerodynamic polars
# ===========================================================================

def test_aero_polars_cessna_172():
    """Aero polars must return non-trivial CL and CD arrays."""
    from tabs.performance.analysis_registry import run_aero_polars
    load_aircraft('Cessna_172.json')
    result = run_aero_polars(
        {
            'AoA Min (deg)':    -5.0,
            'AoA Max (deg)':    10.0,
            'Number of Points':  8,
            'Mach Number':       0.18,
            'Altitude (m)':      0.0,
        },
        config_tag='cruise',
    )
    cl = np.asarray(result.aerodynamics.coefficients.lift.total).flatten()
    cd = np.asarray(result.aerodynamics.coefficients.drag.total).flatten()
    assert cl.shape[0] == 8, 'expected 8 CL points'
    assert cl.max() > 0, 'max CL must be positive'
    assert cd.min() > 0, 'CD must be positive'
    print(f'  Cessna 172 CLmax: {cl.max():.4f}, CDmin: {cd.min():.5f}')


# ===========================================================================
# 7. Payload-range diagram  [SLOW — full mission evaluated multiple times]
# ===========================================================================

@pytest.mark.slow
def test_payload_range_atr72():
    """Payload-range must return non-empty range and payload arrays."""
    from tabs.performance.analysis_registry import run_payload_range
    load_aircraft('ATR_72.json')
    build_mission()
    result = run_payload_range(
        {'Cruise Segment Tag': 'cruise', 'Fuel Reserve (%)': 5.0},
        config_tag='cruise',
    )
    r = np.asarray(result.range).flatten()
    p = np.asarray(result.payload).flatten()
    assert len(r) >= 2, 'range array too short'
    assert r[-1] > 0, 'ferry range must be positive'
    assert p[0] >= p[-1], 'payload should decrease from max-payload to ferry point'
    from RCAIDE.Framework.Core import Units
    print(f'  ATR-72 ferry range: {r[-1]/Units.nmi:.0f} nmi')


# ===========================================================================
# 8. Load & Trim diagram  [SLOW — full mission evaluated many times]
# ===========================================================================

@pytest.mark.slow
def test_load_trim_cessna_172():
    """Load & Trim must return MTOW and a loading envelope."""
    from tabs.performance.analysis_registry import run_load_trim
    load_aircraft('Cessna_172.json')
    build_mission()
    result = run_load_trim(
        {'Cruise Segment Tag': 'cruise', 'Discretization': 2},
        config_tag='cruise',
    )
    assert hasattr(result, 'MTOW'), 'result missing MTOW'
    assert result.MTOW > 0, 'MTOW must be positive'
    assert hasattr(result, 'loading_results'), 'result missing loading_results'
    print(f'  Cessna 172 MTOW: {result.MTOW:.0f} kg')


def test_load_trim_missing_stability_raises():
    """run_load_trim must raise a clear ValueError when stability is absent."""
    from tabs.performance.analysis_registry import run_load_trim
    from RCAIDE.Framework.Mission.Segments.Cruise.Constant_Speed_Constant_Altitude import (
        Constant_Speed_Constant_Altitude,
    )

    # Build a minimal mission with a cruise segment that has NO stability analysis
    seg = Constant_Speed_Constant_Altitude()
    seg.tag = 'cruise'
    seg.air_speed = 50.0
    seg.altitude  = 1000.0
    seg.distance  = 10000.0

    mission = RCAIDE.Framework.Mission.Sequential_Segments()
    mission.append_segment(seg)   # analyses deliberately empty — no stability
    rcaide_io.rcaide_mission = mission

    with pytest.raises(ValueError, match='Stability'):
        run_load_trim(
            {'Cruise Segment Tag': 'cruise', 'Discretization': 2},
            config_tag='cruise',
        )


# ===========================================================================
# 9. Nominal mission (mission.evaluate())  [SLOW — full mission evaluation]
# ===========================================================================

@pytest.mark.slow
def test_nominal_mission_cessna_172():
    """Full mission simulation must complete and return results for every segment."""
    load_aircraft('Cessna_172.json')
    mission = build_mission()
    assert len(mission.segments) > 0, 'mission has no segments'

    t0 = time.time()
    results = mission.evaluate()
    elapsed = time.time() - t0

    seg_results = list(results.segments.values())
    assert len(seg_results) > 0, 'no segment results returned'

    first_seg = seg_results[0]
    assert hasattr(first_seg.conditions, 'aerodynamics'), 'missing aerodynamics in results'
    print(f'  Cessna 172 mission: {len(seg_results)} segment(s), {elapsed:.1f}s')


# ===========================================================================
# 10. Multi-aircraft nominal missions — parametrized over available aircraft
# ===========================================================================

def _aircraft_with_missions():
    """Return filenames that have at least one mission segment."""
    candidates = []
    for filename in _aircraft_jsons():
        path = os.path.join(AIRCRAFT_DIR, filename)
        try:
            with open(path) as fh:
                d = json.load(fh)
            md = d.get('mission_data', [])
            has_segs = any(
                isinstance(entry, dict) and entry.get('segments')
                for entry in md
            )
            if has_segs:
                candidates.append(filename)
        except Exception:
            pass
    return candidates


@pytest.mark.slow
@pytest.mark.parametrize('filename', _aircraft_with_missions())
def test_nominal_mission(filename):
    """Every aircraft with a defined mission must simulate without crashing."""
    t0 = time.time()
    load_aircraft(filename)
    mission = build_mission()

    if len(mission.segments) == 0:
        pytest.skip(f'{filename}: mission_data present but no segments built')

    results = mission.evaluate()
    elapsed = time.time() - t0

    seg_results = list(results.segments.values())
    assert len(seg_results) > 0
    print(f'  {filename}: {len(seg_results)} segment(s), {elapsed:.1f}s')
