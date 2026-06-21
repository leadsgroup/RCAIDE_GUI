# RCAIDE_GUI/tabs/multi_disciplinary/analysis_registry.py

import rcaide_io
import numpy as np
import traceback
from copy import deepcopy
from RCAIDE.Framework.Core import Units


# ──────────────────────────────────────────────────────────────────────────────
#  Runner functions
# ──────────────────────────────────────────────────────────────────────────────

def run_tofl(params, config_tag):
    from RCAIDE.Library.Methods.Performance import estimate_take_off_field_length
    analyses = rcaide_io.rcaide_analyses[config_tag]
    return estimate_take_off_field_length(
        analyses=analyses,
        altitude=params["Altitude (m)"],
        delta_isa=params["Delta ISA (K)"],
        compute_2nd_seg_climb=params.get("Compute 2nd Seg. Climb", False),
    )


def run_lfl(params, config_tag):
    from RCAIDE.Library.Methods.Performance import estimate_landing_field_length
    analyses = rcaide_io.rcaide_analyses[config_tag]
    return estimate_landing_field_length(
        analyses=analyses,
        altitude=params["Altitude (m)"],
        delta_isa=params["Delta ISA (K)"],
    )


def run_stall_speed(params, config_tag):
    from RCAIDE.Library.Methods.Performance import estimate_stall_speed
    return estimate_stall_speed(
        vehicle_mass=params["Vehicle Mass (kg)"],
        reference_area=params["Reference Area (m²)"],
        altitude=params["Altitude (m)"],
        maximum_lift_coefficient=params["Max CL"],
    )


def run_vn_diagram(params, config_tag):
    from RCAIDE.Library.Methods.Performance import generate_V_n_diagram
    analyses = rcaide_io.rcaide_analyses[config_tag]
    return generate_V_n_diagram(
        analyses=analyses,
        altitude=params["Altitude (m)"],
        delta_ISA=params["Delta ISA (K)"],
    )


def run_payload_range(params, config_tag):
    from RCAIDE.Library.Methods.Performance import compute_payload_range_diagram
    mission = deepcopy(rcaide_io.rcaide_mission)
    return compute_payload_range_diagram(
        mission=mission,
        cruise_segment_tag=params["Cruise Segment Tag"],
        fuel_reserve_percentage=params["Fuel Reserve (%)"] / 100.0,
    )


def run_aero_polars(params, config_tag):
    from RCAIDE.Library.Methods.Performance import aircraft_aerodynamic_analysis
    analyses = rcaide_io.rcaide_analyses[config_tag]
    n_pts = int(params["Number of Points"])
    aoa_min = params["AoA Min (deg)"] * Units.degrees
    aoa_max = params["AoA Max (deg)"] * Units.degrees
    mach = params["Mach Number"]
    altitude = params["Altitude (m)"]
    aoa_array = np.atleast_2d(np.linspace(aoa_min, aoa_max, n_pts)).T
    mach_array = np.ones_like(aoa_array) * mach
    return aircraft_aerodynamic_analysis(
        analyses=analyses,
        angle_of_attacks=aoa_array,
        mach_numbers=mach_array,
        altitude=altitude,
    )


def run_load_trim(params, config_tag):
    from RCAIDE.Library.Methods.Performance import compute_load_and_trim_diagram
    mission = deepcopy(rcaide_io.rcaide_mission)
    return compute_load_and_trim_diagram(
        mission=mission,
        cruise_segment_tag=params["Cruise Segment Tag"],
        discretization=int(params["Discretization"]),
    )


# ──────────────────────────────────────────────────────────────────────────────
#  Formatter functions  →  list of (label, value_str, unit_str)
# ──────────────────────────────────────────────────────────────────────────────

def format_tofl(result):
    if isinstance(result, tuple):
        tofl, gradient = result
        return [
            ("Take-Off Field Length", f"{tofl:.1f}", "m"),
            ("2nd Segment Climb Gradient", f"{gradient:.4f}", ""),
        ]
    return [("Take-Off Field Length", f"{result:.1f}", "m")]


def format_lfl(result):
    return [("Landing Field Length", f"{result:.1f}", "m")]


def format_stall_speed(result):
    return [("Stall Speed", f"{result:.2f}", "m/s"),
            ("Stall Speed", f"{result / Units.knots:.2f}", "kts")]


def format_vn_diagram(result):
    rows = [
        ("Vs1 (positive)", f"{result.Vs1.positive:.1f}", "KEAS"),
        ("Vs1 (negative)", f"{result.Vs1.negative:.1f}", "KEAS"),
        ("Va (positive)", f"{result.Va.positive:.1f}", "KEAS"),
        ("Va (negative)", f"{result.Va.negative:.1f}", "KEAS"),
        ("Vc (cruise)", f"{result.Vc:.1f}", "KEAS"),
        ("Vd (dive)", f"{result.Vd:.1f}", "KEAS"),
        ("n+ (limit)", f"{max(result.load_factors.positive):.2f}", ""),
        ("n- (limit)", f"{min(result.load_factors.negative):.2f}", ""),
    ]
    return rows


def format_payload_range(result):
    r = result.range
    return [
        ("Max Payload Range", f"{r[1] / Units.nmi:.0f}", "nmi"),
        ("Ferry Range", f"{r[-1] / Units.nmi:.0f}", "nmi"),
    ]


def format_aero_polars(result):
    cl = np.asarray(result.lift_coefficient).flatten()
    cd = np.asarray(result.drag_coefficient).flatten()
    ld = cl / np.where(cd == 0, np.inf, cd)
    idx = np.argmax(ld)
    return [
        ("CL max", f"{cl.max():.4f}", ""),
        ("CD at CL max", f"{cd[cl.argmax()]:.5f}", ""),
        ("L/D max", f"{ld[idx]:.2f}", ""),
        ("CL at L/D max", f"{cl[idx]:.4f}", ""),
    ]


def format_load_trim(result):
    rows = [("MTOW", f"{result.MTOW:.0f}", "kg")]
    if hasattr(result, "MLW"):
        rows.append(("MLW", f"{result.MLW:.0f}", "kg"))
    return rows


# ──────────────────────────────────────────────────────────────────────────────
#  Plotter functions  →  create pyqtgraph widgets via new_plot_widget callback
# ──────────────────────────────────────────────────────────────────────────────

def plot_vn_diagram(result, new_plot_widget):
    import pyqtgraph as pg
    w = new_plot_widget("V-n Diagram", "Load Factor (n)", "Airspeed (KEAS)")
    pos_pen = pg.mkPen(color=(80, 160, 255), width=2)
    neg_pen = pg.mkPen(color=(80, 160, 255), width=2)
    w.plot(result.airspeeds.positive, result.load_factors.positive,
           pen=pos_pen, name="Maneuvering Envelope")
    w.plot(result.airspeeds.negative, result.load_factors.negative,
           pen=neg_pen)

    gust_pos = result.gust_load_factors.positive
    gust_neg = result.gust_load_factors.negative
    Vc = result.Vc
    Vd = result.Vd

    cruise_pen = pg.mkPen(color=(255, 80, 80), width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine)
    w.plot([0, Vc, 1.05 * Vd],
           [1, gust_pos[2], gust_pos[len(gust_pos) - 3]],
           pen=cruise_pen, name="Cruise Gust")

    dive_pen = pg.mkPen(color=(80, 220, 80), width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine)
    w.plot([0, Vd, 1.05 * Vd],
           [1, gust_pos[3], gust_pos[len(gust_pos) - 2]],
           pen=dive_pen, name="Dive Gust")

    w.plot([0, Vc, 1.05 * Vd],
           [1, gust_neg[2], gust_neg[len(gust_neg) - 3]],
           pen=cruise_pen)
    w.plot([0, Vd, 1.05 * Vd],
           [1, gust_neg[3], gust_neg[len(gust_neg) - 2]],
           pen=dive_pen)
    return [w]


def plot_payload_range(result, new_plot_widget):
    import pyqtgraph as pg
    w1 = new_plot_widget("Payload vs Range", "Payload (lbs)", "Range (nmi)")
    pen = pg.mkPen(color=(80, 160, 255), width=2)
    w1.plot(np.asarray(result.range).flatten() / Units.nmi,
            np.asarray(result.payload).flatten() / Units.lbm,
            pen=pen, name="Payload")

    w2 = new_plot_widget("OEW + Payload vs Range", "OEW + Payload (lbs)", "Range (nmi)")
    w2.plot(np.asarray(result.range).flatten() / Units.nmi,
            np.asarray(result.oew_plus_payload).flatten() / Units.lbm,
            pen=pen, name="OEW + Payload")
    return [w1, w2]


def plot_aero_polars(result, new_plot_widget):
    import pyqtgraph as pg
    alpha_deg = np.asarray(result.alpha).flatten() / Units.degrees
    cl = np.asarray(result.lift_coefficient).flatten()
    cd = np.asarray(result.drag_coefficient).flatten()
    cm = np.asarray(result.moment_coefficient).flatten()
    pen = pg.mkPen(color=(80, 160, 255), width=2)

    w1 = new_plot_widget("Lift Coefficient vs AoA", "CL", "Angle of Attack (deg)")
    w1.plot(alpha_deg, cl, pen=pen, name="CL")

    w2 = new_plot_widget("Drag Coefficient vs AoA", "CD", "Angle of Attack (deg)")
    w2.plot(alpha_deg, cd, pen=pen, name="CD")

    w3 = new_plot_widget("Drag Polar", "CL", "CD")
    w3.plot(cd, cl, pen=pen, name="CL vs CD")

    w4 = new_plot_widget("Moment Coefficient vs AoA", "CM", "Angle of Attack (deg)")
    w4.plot(alpha_deg, cm, pen=pen, name="CM")
    return [w1, w2, w3, w4]


def plot_load_trim(result, new_plot_widget):
    import pyqtgraph as pg
    w = new_plot_widget("Loading Diagram", "Mass (kg)", "CG / LEMAC (%)")
    loading = result.loading_results
    cg = np.asarray(loading.CG_percent_of_LEMAC_location).flatten() * 100
    mass = np.asarray(loading.mass).flatten()
    pen = pg.mkPen(color=(80, 160, 255), width=2)
    w.plot(cg, mass, pen=pen, name="Loading Envelope")

    mtow_pen = pg.mkPen(color=(80, 220, 80), width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine)
    cg_range = [cg.min(), cg.max()]
    w.plot(cg_range, [result.MTOW, result.MTOW], pen=mtow_pen, name="MTOW")
    if hasattr(result, "MLW"):
        mlw_pen = pg.mkPen(color=(255, 200, 80), width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine)
        w.plot(cg_range, [result.MLW, result.MLW], pen=mlw_pen, name="MLW")
    return [w]


# ──────────────────────────────────────────────────────────────────────────────
#  Registry
# ──────────────────────────────────────────────────────────────────────────────

ANALYSIS_REGISTRY = {
    "Take-Off Field Length": {
        "parameters": [
            ("Altitude (m)", "float", 0.0),
            ("Delta ISA (K)", "float", 0.0),
            ("Compute 2nd Seg. Climb", "bool", True),
        ],
        "requires_mission": False,
        "requires_analyses": True,
        "runner": run_tofl,
        "plotter": None,
        "formatter": format_tofl,
    },
    "Landing Field Length": {
        "parameters": [
            ("Altitude (m)", "float", 0.0),
            ("Delta ISA (K)", "float", 0.0),
        ],
        "requires_mission": False,
        "requires_analyses": True,
        "runner": run_lfl,
        "plotter": None,
        "formatter": format_lfl,
    },
    "Stall Speed": {
        "parameters": [
            ("Vehicle Mass (kg)", "float", 0.0),
            ("Reference Area (m²)", "float", 0.0),
            ("Altitude (m)", "float", 0.0),
            ("Max CL", "float", 1.5),
        ],
        "requires_mission": False,
        "requires_analyses": False,
        "runner": run_stall_speed,
        "plotter": None,
        "formatter": format_stall_speed,
    },
    "V-n Diagram": {
        "parameters": [
            ("Altitude (m)", "float", 0.0),
            ("Delta ISA (K)", "float", 0.0),
        ],
        "requires_mission": False,
        "requires_analyses": True,
        "runner": run_vn_diagram,
        "plotter": plot_vn_diagram,
        "formatter": format_vn_diagram,
    },
    "Payload-Range Diagram": {
        "parameters": [
            ("Cruise Segment Tag", "text", "cruise"),
            ("Fuel Reserve (%)", "float", 5.0),
        ],
        "requires_mission": True,
        "requires_analyses": True,
        "runner": run_payload_range,
        "plotter": plot_payload_range,
        "formatter": format_payload_range,
    },
    "Aerodynamic Polars": {
        "parameters": [
            ("AoA Min (deg)", "float", -5.0),
            ("AoA Max (deg)", "float", 15.0),
            ("Number of Points", "int", 21),
            ("Mach Number", "float", 0.3),
            ("Altitude (m)", "float", 0.0),
        ],
        "requires_mission": False,
        "requires_analyses": True,
        "runner": run_aero_polars,
        "plotter": plot_aero_polars,
        "formatter": format_aero_polars,
    },
    "Load & Trim Diagram": {
        "parameters": [
            ("Cruise Segment Tag", "text", "cruise"),
            ("Discretization", "int", 5),
        ],
        "requires_mission": True,
        "requires_analyses": True,
        "runner": run_load_trim,
        "plotter": plot_load_trim,
        "formatter": format_load_trim,
    },
}
