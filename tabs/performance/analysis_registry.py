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
    vehicle  = getattr(rcaide_io, "vehicle", None)

    specified = params.get("Takeoff Weight (kg)", 0.0)
    if specified and specified > 0:
        vehicle.mass_properties.takeoff = specified
    elif vehicle is None or getattr(vehicle.mass_properties, "takeoff", None) is None:
        raise ValueError("Takeoff weight not defined in vehicle. Enter one in the parameters or define it in the aircraft file.")

    return estimate_take_off_field_length(
        analyses=analyses,
        altitude=params["Altitude (m)"],
        delta_isa=params["Delta ISA (K)"],
        compute_2nd_seg_climb=params.get("Compute 2nd Seg. Climb", False),
    )


def run_lfl(params, config_tag):
    from RCAIDE.Library.Methods.Performance import estimate_landing_field_length
    analyses = rcaide_io.rcaide_analyses[config_tag]
    vehicle  = getattr(rcaide_io, "vehicle", None)

    specified = params.get("Landing Weight (kg)", 0.0)
    if specified and specified > 0:
        vehicle.mass_properties.landing = specified
    elif vehicle is None or getattr(vehicle.mass_properties, "landing", None) is None:
        raise ValueError("Landing weight not defined in vehicle. Enter one in the parameters or define it in the aircraft file.")

    return estimate_landing_field_length(
        analyses=analyses,
        altitude=params["Altitude (m)"],
        delta_isa=params["Delta ISA (K)"],
    )


def run_stall_speed(params, _config_tag):
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
    vehicle  = getattr(rcaide_io, "vehicle", None)

    def _check(value, name):
        if value is None:
            raise ValueError(f"{name} not defined in vehicle — V-n diagram cannot be computed.")

    mp = getattr(vehicle, "mass_properties",   None) if vehicle else None
    fe = getattr(vehicle, "flight_envelope",   None) if vehicle else None
    _check(getattr(mp, "max_takeoff",              None), "vehicle.mass_properties.max_takeoff")
    _check(getattr(fe, "FAR_part_number",          None), "vehicle.flight_envelope.FAR_part_number")
    _check(getattr(fe, "design_mach_number",       None), "vehicle.flight_envelope.design_mach_number")
    _check(getattr(fe, "positive_limit_load",      None), "vehicle.flight_envelope.positive_limit_load")
    _check(getattr(fe, "negative_limit_load",      None), "vehicle.flight_envelope.negative_limit_load")
    _check(getattr(fe, "category",                 None), "vehicle.flight_envelope.category")
    _check(getattr(fe, "minimum_lift_coefficient", None), "vehicle.flight_envelope.minimum_lift_coefficient")
    _check(getattr(fe, "maximum_lift_coefficient", None), "vehicle.flight_envelope.maximum_lift_coefficient")

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
    cl = np.asarray(result.aerodynamics.coefficients.lift.total).flatten()
    cd = np.asarray(result.aerodynamics.coefficients.drag.total).flatten()
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

def plot_vn_diagram(result, new_plot_widget, new_mpl_widget=None):
    import pyqtgraph as pg

    # RCAIDE parula palette anchors (matches rcaide_colormap.py)
    BLUE  = (  5, 104, 223)   # royal blue  – maneuvering envelope boundary
    TEAL  = ( 19, 169, 200)   # cyan/teal   – cruise gust
    GREEN = ( 94, 201,  98)   # green       – dive gust
    DASH  = pg.QtCore.Qt.PenStyle.DashLine

    w = new_plot_widget("V-n Diagram", "Load Factor (n)", "Airspeed (KEAS)")

    vs_pos = np.asarray(result.airspeeds.positive).flatten()
    lf_pos = np.asarray(result.load_factors.positive).flatten()
    vs_neg = np.asarray(result.airspeeds.negative).flatten()
    lf_neg = np.asarray(result.load_factors.negative).flatten()

    # ── Shaded maneuvering envelope (fill to n = 0, matching ax.fill in RCAIDE) ─
    for vs, lf in [(vs_pos, lf_pos), (vs_neg, lf_neg)]:
        filled = pg.PlotCurveItem(
            x=vs, y=lf,
            pen=pg.mkPen(color=BLUE, width=2),
            fillLevel=0,
            brush=pg.mkBrush(*BLUE, 55),
        )
        w.addItem(filled)

    # Legend proxy for the filled envelope (PlotCurveItem doesn't auto-register)
    legend = w.getPlotItem().legend
    if legend is not None:
        proxy = pg.PlotDataItem(pen=pg.mkPen(color=BLUE, width=2))
        legend.addItem(proxy, "Maneuvering Envelope")

    # ── Gust lines ───────────────────────────────────────────────────────────────
    gust_pos = np.asarray(result.gust_load_factors.positive).flatten()
    gust_neg = np.asarray(result.gust_load_factors.negative).flatten()
    Vc = float(result.Vc)
    Vd = float(result.Vd)

    try:
        cruise_lbl = f"Cruise Gust  {round(float(result.gust_data.airspeeds.cruise_gust))} fps"
        dive_lbl   = f"Dive Gust  {round(float(result.gust_data.airspeeds.dive_gust))} fps"
    except Exception:
        cruise_lbl, dive_lbl = "Cruise Gust", "Dive Gust"

    cruise_pen = pg.mkPen(color=TEAL,  width=1.5, style=DASH)
    dive_pen   = pg.mkPen(color=GREEN, width=1.5, style=DASH)

    w.plot([0, Vc, 1.05*Vd], [1, gust_pos[2], gust_pos[-3]], pen=cruise_pen, name=cruise_lbl)
    w.plot([0, Vd, 1.05*Vd], [1, gust_pos[3], gust_pos[-2]], pen=dive_pen,   name=dive_lbl)
    w.plot([0, Vc, 1.05*Vd], [1, gust_neg[2], gust_neg[-3]], pen=cruise_pen)
    w.plot([0, Vd, 1.05*Vd], [1, gust_neg[3], gust_neg[-2]], pen=dive_pen)

    return [w]


def plot_payload_range(result, new_plot_widget, new_mpl_widget=None):
    import pyqtgraph as pg
    w1 = new_plot_widget("Payload vs Range", "Payload (lbs)", "Range (nmi)")
    pen = pg.mkPen(color=(255, 255, 255), width=2)
    w1.plot(np.asarray(result.range).flatten() / Units.nmi,
            np.asarray(result.payload).flatten() / Units.lbm,
            pen=pen, name="Payload")

    w2 = new_plot_widget("OEW + Payload vs Range", "OEW + Payload (lbs)", "Range (nmi)")
    w2.plot(np.asarray(result.range).flatten() / Units.nmi,
            np.asarray(result.oew_plus_payload).flatten() / Units.lbm,
            pen=pen, name="OEW + Payload")
    return [w1, w2]


def plot_aero_polars(result, new_plot_widget, new_mpl_widget=None):
    import pyqtgraph as pg

    WHITE = (255, 255, 255)

    alpha_deg = np.asarray(result.aerodynamics.angles.alpha).flatten() / Units.degrees
    cl        = np.asarray(result.aerodynamics.coefficients.lift.total).flatten()
    cd        = np.asarray(result.aerodynamics.coefficients.drag.total).flatten()
    cm        = np.asarray(result.static_stability.coefficients.M).flatten()
    pen       = pg.mkPen(color=WHITE, width=2)

    w1 = new_plot_widget("Lift Coefficient vs AoA", "CL", "Angle of Attack (deg)")
    w1.plot(alpha_deg, cl, pen=pen, name="CL")

    w2 = new_plot_widget("Drag Coefficient vs AoA", "CD", "Angle of Attack (deg)")
    w2.plot(alpha_deg, cd, pen=pen, name="CD")

    w3 = new_plot_widget("Drag Polar", "CL", "CD")
    w3.plot(cd, cl, pen=pen, name="CL vs CD")

    w4 = new_plot_widget("Moment Coefficient vs AoA", "CM", "Angle of Attack (deg)")
    w4.plot(alpha_deg, cm, pen=pen, name="CM")
    return [w1, w2, w3, w4]


def plot_load_trim(result, new_plot_widget, new_mpl_widget=None):
    import pyqtgraph as pg
    from scipy.spatial import ConvexHull
    from scipy.interpolate import RegularGridInterpolator
    from shapely.geometry import Polygon
    import matplotlib.cm as mpl_cm

    SM_MIN    = -10.0
    SM_MAX    = 50.0    # extend: SM>50→blue, SM<-10→red
    SM_STEP   = 5.0
    # RCAIDE parula anchor colors — used for envelope/component lines so they
    # stay visible against the coolwarm_r contour (blue / cream / pink) background
    PARULA_DEEP_BLUE = (53, 42, 135)
    PARULA_CYAN      = (20, 169, 200)
    FIREBRICK        = (178, 34, 34)

    w = new_plot_widget("Loading & Trim Diagram", "Mass (kg)", "CG / LEMAC (%)")

    # ── Build pg.ColorMap from matplotlib coolwarm_r (used for image + cbar) ─
    _n   = 256
    _pos = np.linspace(0.0, 1.0, _n)
    _clr = (mpl_cm.get_cmap('coolwarm_r')(_pos) * 255).astype(np.uint8)
    pg_cmap = pg.ColorMap(_pos, _clr)

    # ── Static margin background + isocurve contour lines ────────────────────
    img = None
    try:
        CG_2d  = np.asarray(result.trim_results.CG_percent_of_LEMAC_location) * 100
        SM_2d  = np.asarray(result.trim_results.static_margin) * 100
        M_2d   = np.asarray(result.trim_results.mass)

        cg_axis   = CG_2d[0, :]    # (n_cg,)   — varies along axis-1
        mass_axis = M_2d[:, 0]     # (n_mass,) — varies along axis-0

        # ImageItem axis-0 = x (CG), axis-1 = y (mass) → transpose SM
        sm_img = SM_2d.T            # (n_cg, n_mass)

        # Upsample onto a fine grid via bilinear interpolation so the contour
        # looks smooth/continuous (like matplotlib's contourf) even though the
        # underlying trim grid is coarse (often just a few CG/mass points).
        if sm_img.shape[0] >= 2 and sm_img.shape[1] >= 2:
            try:
                interp = RegularGridInterpolator(
                    (cg_axis, mass_axis), sm_img,
                    method='linear', bounds_error=False, fill_value=None)
                cg_fine   = np.linspace(cg_axis.min(), cg_axis.max(), 150)
                mass_fine = np.linspace(mass_axis.min(), mass_axis.max(), 150)
                CGf, Mf   = np.meshgrid(cg_fine, mass_fine, indexing='ij')
                sm_fine   = interp(np.stack([CGf.ravel(), Mf.ravel()], axis=-1)) \
                                .reshape(CGf.shape)
                cg_axis, mass_axis, sm_img = cg_fine, mass_fine, sm_fine
            except Exception as ie:
                print(f"[plot_load_trim] upsample skipped: {ie}")

        # Pass raw float data — pyqtgraph clamps outside [SM_MIN, SM_MAX] to the
        # endpoint colors (blue for >50, red for <-10), giving the extend behavior.
        img = pg.ImageItem(sm_img.astype(np.float32))
        img.setRect(float(cg_axis.min()), float(mass_axis.min()),
                    float(cg_axis.max() - cg_axis.min()),
                    float(mass_axis.max() - mass_axis.min()))
        img.setLevels([SM_MIN, SM_MAX])
        img.setColorMap(pg_cmap)
        img.setOpacity(140 / 255.0)
        w.addItem(img)

        # Isocurve lines — parented to image so they share its pixel→scene transform
        levels = np.arange(SM_MIN, SM_MAX + SM_STEP / 2, SM_STEP)
        SM_N   = len(levels)
        for level in levels:
            iso = pg.IsocurveItem(data=sm_img, level=float(level),
                                  pen=pg.mkPen(color=(60, 60, 60, 90), width=0.5))
            iso.setParentItem(img)

        # Contour labels via TextItem — only every other level to avoid clutter
        tol = SM_STEP / 2
        for i, level in enumerate(levels):
            if i % 2 != 0:
                continue
            mask = np.abs(sm_img - level) < tol
            if mask.any():
                xi, yi = np.where(mask)
                cx = float(cg_axis.min()
                           + np.mean(xi) / max(sm_img.shape[0] - 1, 1)
                           * (cg_axis.max() - cg_axis.min()))
                cy = float(mass_axis.min()
                           + np.mean(yi) / max(sm_img.shape[1] - 1, 1)
                           * (mass_axis.max() - mass_axis.min()))
                lbl = pg.TextItem(f'{level:.0f}%', color=(40, 40, 40, 210),
                                  anchor=(0.5, 0.5))
                f = lbl.textItem.font(); f.setPointSize(7); lbl.textItem.setFont(f)
                lbl.setPos(cx, cy)
                w.addItem(lbl)

        # ColorBarItem on the right axis
        try:
            cbar = pg.ColorBarItem(
                values=(SM_MIN, SM_MAX),
                colorMap=pg_cmap,
                label='Static Margin (%)',
                width=15,
                interactive=False,
            )
            cbar.setImageItem(img, insert_in=w.getPlotItem())
        except Exception as ce:
            print(f"[plot_load_trim] colorbar: {ce}")

    except Exception as e:
        import traceback
        print(f"[plot_load_trim] background/contour failed: {e}")
        traceback.print_exc()

    # ── Helper: closed convex hull polygon ───────────────────────────────────
    def _hull_polygon(cg_flat, mass_flat):
        pts = np.hstack([np.atleast_2d(cg_flat).T, np.atleast_2d(mass_flat).T])
        pts = np.unique(pts, axis=0)
        if len(pts) < 3:
            return None, None
        try:
            hull = ConvexHull(pts)
            poly = Polygon(pts[hull.vertices])
            return np.array(poly.exterior.xy[0]), np.array(poly.exterior.xy[1])
        except Exception:
            return None, None

    # ── Overall loading envelope (bold dark outline, visible on all bands) ────
    loading  = result.loading_results
    cg_all   = np.asarray(loading.CG_percent_of_LEMAC_location).flatten() * 100
    mass_all = np.asarray(loading.mass).flatten()
    fill_base = mass_all.min() * 0.98

    x_h, y_h = _hull_polygon(cg_all, mass_all)
    if x_h is not None:
        overall = pg.PlotCurveItem(
            x=x_h, y=y_h,
            pen=pg.mkPen(color=(15, 15, 20), width=2.5),
            fillLevel=fill_base,
            brush=pg.mkBrush(15, 15, 20, 35),
        )
        w.addItem(overall)
        pi = w.getPlotItem()
        if pi.legend:
            pi.legend.addItem(
                pg.PlotDataItem(pen=pg.mkPen(color=(15, 15, 20), width=2.5)),
                "Loading Envelope")

    # ── Component envelopes (fuel / pax / cargo) — RCAIDE parula colors ───────
    _components = [
        (np.s_[:, 0, 0, :], FIREBRICK,        "Fuel Loading"),
        (np.s_[:, :, 0, 0], PARULA_DEEP_BLUE, "Pax. Loading"),
        (np.s_[:, 0, :, 0], PARULA_CYAN,      "Cargo Loading"),
    ]
    for sl, color, label in _components:
        try:
            cg_c = np.asarray(loading.CG_percent_of_LEMAC_location[sl]).flatten() * 100
            m_c  = np.asarray(loading.mass[sl]).flatten()
            x_c, y_c = _hull_polygon(cg_c, m_c)
            if x_c is not None:
                w.plot(x_c, y_c, pen=pg.mkPen(color=color, width=1.5), name=label)
        except Exception:
            pass

    # ── Axis limits matching hull bounds (mirrors reference set_xlim/ylim) ────
    if x_h is not None:
        x_bound = float(max(x_h) - min(x_h))
        w.setXRange(float(min(x_h)) - x_bound / 2,
                    float(max(x_h)) + x_bound / 2, padding=0)
        w.setYRange(float(min(y_h)), float(max(y_h)), padding=0.05)

    # ── MTOW / MLW lines ─────────────────────────────────────────────────────
    x_range = ([float(cg_all.min()) - 2, float(cg_all.max()) + 2]
               if x_h is not None else [0.0, 100.0])
    DARK_GREEN = (0, 140, 0)
    DASH       = pg.QtCore.Qt.PenStyle.DashLine
    DOT        = pg.QtCore.Qt.PenStyle.DotLine
    w.plot(x_range, [result.MTOW, result.MTOW],
           pen=pg.mkPen(color=DARK_GREEN, width=1.5, style=DASH), name="MTOW")
    if hasattr(result, "MLW"):
        w.plot(x_range, [result.MLW, result.MLW],
               pen=pg.mkPen(color=DARK_GREEN, width=1.5, style=DOT), name="MLW")

    return [w]


# ──────────────────────────────────────────────────────────────────────────────
#  Registry
# ──────────────────────────────────────────────────────────────────────────────

ANALYSIS_REGISTRY = {
    "Take-Off Field Length": {
        "parameters": [
            ("Altitude (m)", "float", 0.0),
            ("Delta ISA (K)", "float", 0.0),
            ("Takeoff Weight (kg)", "float", 0.0),
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
            ("Landing Weight (kg)", "float", 0.0),
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
            ("Mach Number", "float", 0.78),
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
            ("Discretization", "int", 3),
        ],
        "requires_mission": True,
        "requires_analyses": True,
        "runner": run_load_trim,
        "plotter": plot_load_trim,
        "formatter": format_load_trim,
    },
}
