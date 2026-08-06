"""Small geometry adapters used by the GUI's VTK viewer."""

import numpy as np

from RCAIDE.Framework.Core import Data
from RCAIDE.Library.Plots.Geometry.generate_3d_fuselage_points import (
    generate_3d_fuselage_points,
)
from RCAIDE.Library.Plots.Geometry.plot_3d_rotor import (
    generate_vtk_object,
    write_azimuthal_cell_values,
)


def generate_fuselage_points_for_viewer(fuselage, tessellation=24):
    """Return a renderable fuselage mesh, including for segment-free models.

    RCAIDE's standard generator correctly represents explicitly segmented
    fuselages. With fewer than two segments it returns a point array that
    cannot form surface cells. Learner Mode deliberately has no fuselage
    segments, so the viewer uses a smooth analytic body based only on overall
    length, width, and height. This changes visualization only; it does not add
    segments to the vehicle model.
    """
    segments = getattr(fuselage, "segments", ())
    if len(segments) >= 2:
        return generate_3d_fuselage_points(fuselage, tessellation)

    tessellation = max(8, int(tessellation))
    station_count = 13
    fractions = np.linspace(0.0, 1.0, station_count)
    theta = np.linspace(0.0, 2.0 * np.pi, tessellation, endpoint=False)

    length = max(0.01, float(fuselage.lengths.total))
    width = max(0.01, float(fuselage.width))
    height = max(
        0.01,
        float(getattr(fuselage.heights, "maximum", 0.0) or width),
    )
    origin = np.asarray(fuselage.origin[0], dtype=float)

    points = np.zeros((station_count, tessellation, 3))
    for index, fraction in enumerate(fractions):
        # The exponent gives a recognizable aircraft-like body: a rounded nose,
        # broad middle, and tapered tail without exposing station geometry.
        radius_scale = np.sin(np.pi * fraction) ** 0.6
        points[index, :, 0] = origin[0] + fraction * length
        points[index, :, 1] = origin[1] + 0.5 * width * radius_scale * np.cos(theta)
        points[index, :, 2] = origin[2] + 0.5 * height * radius_scale * np.sin(theta)

    geometry = Data()
    geometry.PTS = points
    return geometry


def learner_component_callout_data(vehicle):
    """Return learner callouts with part anchors and world-space text positions."""
    if not bool(getattr(vehicle, "learner_mode", False)):
        return []

    callouts = []
    wing_labels = {
        "main_wing": "Main Wing\n(makes lift)",
        "horizontal_stabilizer": "Horizontal Stabilizer\n(pitch stability)",
        "vertical_stabilizer": "Vertical Stabilizer\n(directional stability)",
    }

    for wing in getattr(vehicle, "wings", ()):
        component = str(getattr(wing, "tag", ""))
        label = wing_labels.get(component)
        if not label:
            continue
        origin = np.asarray(wing.origin[0], dtype=float)
        root_chord = float(getattr(wing.chords, "root", 0.0) or 0.0)
        span = float(getattr(wing.spans, "projected", 0.0) or 0.0)
        point = origin.copy()
        point[0] += 0.30 * root_chord
        if bool(getattr(wing, "vertical", False)):
            point[2] += 0.55 * span
            label_point = point + np.array([0.45 * root_chord, 0.0, 0.30 * span])
        else:
            semispan = span / (2.0 if bool(getattr(wing, "xz_plane_symmetric", False)) else 1.0)
            point[1] -= 0.55 * semispan
            label_point = point + np.array([0.10 * root_chord, -0.20 * semispan, 0.14 * span])
        callouts.append({
            "component": component,
            "anchor": point.tolist(),
            "label_position": label_point.tolist(),
            "text": label,
        })

    for fuselage in getattr(vehicle, "fuselages", ()):
        if str(getattr(fuselage, "tag", "")) != "fuselage":
            continue
        origin = np.asarray(fuselage.origin[0], dtype=float)
        length = float(getattr(fuselage.lengths, "total", 0.0) or 0.0)
        height = float(getattr(fuselage.heights, "maximum", 0.0) or 0.0)
        point = origin + np.array([0.52 * length, 0.0, 0.55 * height])
        label_point = point + np.array([-0.06 * length, 0.16 * length, 0.22 * max(height, 0.1)])
        callouts.append({
            "component": "fuselage",
            "anchor": point.tolist(),
            "label_position": label_point.tolist(),
            "text": "Fuselage\n(aircraft body)",
        })

    return callouts


def learner_component_label_data(vehicle):
    """Compatibility wrapper returning the original points-and-labels shape."""
    callouts = learner_component_callout_data(vehicle)
    return (
        [callout["anchor"] for callout in callouts],
        [callout["text"] for callout in callouts],
    )
