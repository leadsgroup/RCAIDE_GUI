# =====================================
# RENDER SAFETY + CAMERA VIEW STABILITY
# =====================================
# Patches to improve stability of camera view functions 

import functools
import types
import vtk
from tabs.visualize_geometry.visualize_geometry import VisualizeGeometryWidget

_DEFAULT_BOUNDS = (-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
# --- helpers: unwrap / window / interactor ---
def _unwrap(func):
    # Walk through __wrapped__ to get the original function (prevents wrapper stacking confusion)
    f = func
    seen = set()
    while hasattr(f, "__wrapped__") and f not in seen:
        seen.add(f)
        f = f.__wrapped__
    return f

def _rw(self):
    # Get the VTK RenderWindow safely (can be missing during tab rebuilds)
    try:
        return self.vtkWidget.GetRenderWindow()
    except Exception:
        return None

def _iren(self):
    # Get the RenderWindowInteractor safely
    rw = _rw(self)
    try:
        return rw.GetInteractor() if rw is not None else None
    except Exception:
        return None

# --- helpers: bounds + camera focusing ---
def _safe_bounds(self):
    # Return scene bounds if there are visible actors; otherwise return a stable default bounds box
    r = getattr(self, "renderer", None)
    if r is None:
        return _DEFAULT_BOUNDS
    try:
        if r.VisibleActorCount() > 0:
            b = r.ComputeVisiblePropBounds()
            if b and len(b) == 6:
                return b
    except Exception:
        pass
    return _DEFAULT_BOUNDS

def _reset_camera_focus_to_center_safe(self):
    # Move camera focal point to the center of visible bounds (prevents “orbiting off into space”)
    r = getattr(self, "renderer", None)
    if r is None:
        return
    b = self._safe_bounds()
    cx = (b[0] + b[1]) * 0.5
    cy = (b[2] + b[3]) * 0.5
    cz = (b[4] + b[5]) * 0.5
    cam = r.GetActiveCamera()
    if cam is not None:
        cam.SetFocalPoint(cx, cy, cz)

def _set_view_function_safe(self, Position, Viewup):
    # Set camera position + up-vector safely, then reset camera and re-center focus
    r = getattr(self, "renderer", None)
    if r is None:
        return

    cam = getattr(self, "get_camera", None) or r.GetActiveCamera()
    self.get_camera = cam
    if cam is None:
        return
    
    cam.SetFocalPoint(0, 0, 0)
    cam.SetPosition(*Position)
    cam.SetViewUp(*Viewup)

    try:
        r.ResetCamera()
        cam.Zoom(1.5)
    except Exception:
        pass

    try:
        self.reset_camera_focus_to_center()
    except Exception:
        pass

    rw = _rw(self)
    if rw is not None:
        try:
            rw.Render()
        except Exception:
            pass

# --- safe camera view commands (use bounds-based offsets) ---
def _front_function_safe(self):
    # Front view: offset along -X by half the model width
    if getattr(self, "renderer", None) is None:
        return
    b = self._safe_bounds()
    self.set_view_function((-(b[1] - b[0]) * 0.5, 0, 0), (0, 0, 1))

def _side_function_safe(self):
    # Side view: offset along -Y by full model height
    if getattr(self, "renderer", None) is None:
        return
    b = self._safe_bounds()
    self.set_view_function((0, -(b[3] - b[2]), 0), (0, 0, 1))

def _top_function_safe(self):
    # Top view: offset along +Z by full model height; set Y-up
    if getattr(self, "renderer", None) is None:
        return
    b = self._safe_bounds()
    self.set_view_function((0, 0, (b[3] - b[2])), (0, 1, 0))

def _isometric_function_safe(self):
    # Isometric view: offset equally in -X/-Y/+Z based on depth bounds
    if getattr(self, "renderer", None) is None:
        return
    b = self._safe_bounds()
    self.set_view_function((-b[5], -b[5], b[5]), (0, 0, 1))

# --- attach safe methods onto the widget (overrides are intentional) ---
VisualizeGeometryWidget._safe_bounds = _safe_bounds
VisualizeGeometryWidget.reset_camera_focus_to_center = _reset_camera_focus_to_center_safe
VisualizeGeometryWidget.set_view_function = _set_view_function_safe
VisualizeGeometryWidget.front_function = _front_function_safe
VisualizeGeometryWidget.side_function = _side_function_safe
VisualizeGeometryWidget.top_function = _top_function_safe
VisualizeGeometryWidget.isometric_function = _isometric_function_safe

# --- RUN_SOLVE NON-BLOCKING (PREVENT GUI LOCK)---
if not getattr(VisualizeGeometryWidget, "_run_solve_nonblocking_patched", False):
    # Grab the original run_solve (even if it has already been wrapped elsewhere)
    _base_run_solve = _unwrap(VisualizeGeometryWidget.run_solve)

    @functools.wraps(_base_run_solve)
    def _run_solve_nonblocking(self, *args, **kwargs):
        iren = _iren(self)
        old_start = None

        # Temporarily disable iren.Start() so VTK does not take over the event loop
        if iren is not None:
            try:
                old_start = iren.Start

                def _noop_start(_self_iren):
                    return None

                iren.Start = types.MethodType(_noop_start, iren)
            except Exception:
                old_start = None

        try:
            _base_run_solve(self, *args, **kwargs)
        finally:
            # Restore iren.Start() no matter what happens inside run_solve
            if iren is not None and old_start is not None:
                try:
                    iren.Start = old_start
                except Exception:
                    pass

        # Re-apply expected background styling and force a redraw
        try:
            r = getattr(self, "renderer", None)
            if r is not None:
                r.SetBackground(0.05, 0.09, 0.15)
                r.SetBackground2(0.12, 0.18, 0.28)
                r.GradientBackgroundOn()
            rw = _rw(self)
            if rw is not None:
                rw.Render()
        except Exception:
            pass

        # Keep toolbar visible after solve
        try:
            self.toolbar.raise_()
        except Exception:
            pass

    # Preserve reference to the original function for future unwrap() calls
    _run_solve_nonblocking.__wrapped__ = _base_run_solve
    VisualizeGeometryWidget.run_solve = _run_solve_nonblocking
    VisualizeGeometryWidget._run_solve_nonblocking_patched = True

# =======================================
# AUTO-ROTATE CAMERA (360° ORBIT)
# =======================================
# Toolbar toggle that orbits the camera around its current focal point.

import math
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QPushButton

def add_360_view(self):
    # Requires toolbar + renderer + VTK widget
    if not getattr(self, "toolbar", None) or getattr(self, "renderer", None) is None:
        return
    if not getattr(self, "vtkWidget", None):
        return

    # Don’t add twice (update_toolbar can be called multiple times)
    if getattr(self, "view360_button", None) is not None:
        return

    btn = QPushButton("360° View")
    btn.setCheckable(True)
    self.toolbar.addSeparator()
    self.toolbar.addWidget(btn)
    self.view360_button = btn

    # Timer drives the orbit animation
    timer = QTimer(self)
    timer.setInterval(25)
    self._view360_timer = timer

    # Orbit state (center, distance, up vector, angle, basis directions)
    state = {"c": None, "d": None, "up": None, "theta": 0.0, "dir0": None, "t": None}

    def _norm(x, y, z):
        # Normalize a vector and return (unit_vector, magnitude)
        n = (x*x + y*y + z*z) ** 0.5
        if n <= 1e-12:
            return (0.0, 0.0, 0.0), 0.0
        return (x/n, y/n, z/n), n

    def _cross(ax, ay, az, bx, by, bz):
        # Cross product a × b
        return (ay*bz - az*by, az*bx - ax*bz, ax*by - ay*bx)

    def init_orbit():
        # Capture focal point / camera position and build orbit basis
        r = getattr(self, "renderer", None)
        if r is None:
            return
        cam = r.GetActiveCamera()
        if cam is None:
            return

        c = cam.GetFocalPoint()
        p = cam.GetPosition()

        # dir0 is the direction from focal point to camera, dist is the radius
        (dir0, dist) = _norm(p[0] - c[0], p[1] - c[1], p[2] - c[2])

        # If the camera is sitting on the focal point, estimate a usable distance
        if dist <= 1e-6:
            b = r.ComputeVisiblePropBounds()
            if b and len(b) == 6 and b[1] != b[0]:
                size = max(b[1] - b[0], b[3] - b[2], b[5] - b[4])
                dist = max(1e-3, size * 3.5)
                dir0 = (1.0, 0.0, 0.0)
            else:
                return

        # Normalize up vector (fallback to Z-up if invalid)
        up_raw = cam.GetViewUp()
        (up, upn) = _norm(up_raw[0], up_raw[1], up_raw[2])
        if upn <= 1e-12:
            up = (0.0, 0.0, 1.0)

        # Build a tangent direction for rotation: t = up × dir0
        tx, ty, tz = _cross(up[0], up[1], up[2], dir0[0], dir0[1], dir0[2])
        (t, tn) = _norm(tx, ty, tz)

        # Fallback if up is parallel to dir0
        if tn <= 1e-12:
            tx, ty, tz = _cross(up[0], up[1], up[2], 1.0, 0.0, 0.0)
            (t, tn) = _norm(tx, ty, tz)
            if tn <= 1e-12:
                tx, ty, tz = _cross(up[0], up[1], up[2], 0.0, 1.0, 0.0)
                (t, _) = _norm(tx, ty, tz)

        # Save orbit basis
        state["c"] = (c[0], c[1], c[2])
        state["d"] = dist
        state["up"] = up
        state["dir0"] = dir0
        state["t"] = t
        state["theta"] = 0.0

        # Render once so the first orbit frame looks correct
        try:
            r.ResetCameraClippingRange()
            self.vtkWidget.GetRenderWindow().Render()
        except Exception:
            pass

    def tick():
        # Move camera along the orbit and redraw
        r = getattr(self, "renderer", None)
        if r is None:
            return
        cam = r.GetActiveCamera()
        if cam is None or state["c"] is None:
            return

        # Step the angle (1.5° per tick)
        state["theta"] += math.radians(1.5)
        if state["theta"] >= 2.0 * math.pi:
            state["theta"] -= 2.0 * math.pi

        ct = math.cos(state["theta"])
        st = math.sin(state["theta"])

        # dir_new = dir0*cos(theta) + t*sin(theta)
        dir0 = state["dir0"]
        t = state["t"]
        dir_new = (
            dir0[0] * ct + t[0] * st,
            dir0[1] * ct + t[1] * st,
            dir0[2] * ct + t[2] * st,
        )

        # Position = center + dir_new * radius
        c = state["c"]
        d = state["d"]
        pos = (c[0] + dir_new[0] * d, c[1] + dir_new[1] * d, c[2] + dir_new[2] * d)

        cam.SetPosition(pos[0], pos[1], pos[2])
        cam.SetFocalPoint(c[0], c[1], c[2])
        cam.SetViewUp(state["up"][0], state["up"][1], state["up"][2])

        try:
            r.ResetCameraClippingRange()
            self.vtkWidget.GetRenderWindow().Render()
        except Exception:
            pass

    # Timer callback for orbit animation
    timer.timeout.connect(tick)

    def on_toggle(checked):
        # Start/stop orbit
        if checked:
            init_orbit()
            timer.start()
        else:
            timer.stop()

    btn.toggled.connect(on_toggle)

# Activate Patch
def _patch_update_toolbar_for_360_view():
    # Patch update_toolbar once to add the 360° button
    if getattr(VisualizeGeometryWidget, "_view360_update_toolbar_patched", False):
        return

    old_update_toolbar = VisualizeGeometryWidget.update_toolbar

    def wrapped_update_toolbar(self, *args, **kwargs):
        old_update_toolbar(self, *args, **kwargs)
        add_360_view(self)

    VisualizeGeometryWidget.update_toolbar = wrapped_update_toolbar
    VisualizeGeometryWidget._view360_update_toolbar_patched = True

_patch_update_toolbar_for_360_view()