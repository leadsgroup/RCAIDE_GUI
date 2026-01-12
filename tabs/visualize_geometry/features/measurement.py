# ===========================
# MEASUREMENT TOOL SECTION
# ===========================
# - Adds a lightweight "distance measurement" tool to the VG toolbar.
# - User workflow:
#   1) Toggle 📏 Measure ON
#   2) Click two points in the scene
#   3) A line + endpoint markers + distance label are created
#   4) Use ↩ Undo to remove the most recent measurement, 🧹 Clear to remove all

import math
import vtk
from PyQt6.QtWidgets import QPushButton
from tabs.visualize_geometry.visualize_geometry import VisualizeGeometryWidget

def add_measure_tool(self):
    """
    Injects Measure / Undo / Clear controls into the existing toolbar and wires
    VTK click-picking to create measurement annotations.

    Safe to call repeatedly; will not duplicate buttons for a live widget instance.
    """
    # --- Preconditions ---
    # Need a toolbar (to add buttons), a renderer (to place VTK actors), and a VTK widget (render window/interactor).
    if not getattr(self, "toolbar", None) or getattr(self, "renderer", None) is None:
        return
    if not getattr(self, "vtkWidget", None):
        return

    # --- Idempotency guard ---
    # update_toolbar can be called multiple times; if buttons already exist and are valid, do nothing.
    btn_existing = getattr(self, "measure_button", None)
    if btn_existing is not None:
        try:
            _ = btn_existing.isChecked()  # if this works, button is still alive
            return
        except Exception:
            # Button object was destroyed (e.g., UI rebuild); drop refs so we recreate below.
            self.measure_button = None

    # --- UI controls ---
    btn = QPushButton("📏 Measure")
    btn.setCheckable(True)  # toggle on/off click observer

    undo = QPushButton("↩ Undo")   # remove last completed measurement
    clr = QPushButton("🧹 Clear")  # remove all measurements

    # Add them to the existing toolbar
    self.toolbar.addSeparator()
    self.toolbar.addWidget(btn)
    self.toolbar.addWidget(undo)
    self.toolbar.addWidget(clr)

    # Keep references on the widget so we can detect duplicates and wire events once.
    self.measure_button = btn
    self.measure_undo_button = undo
    self.measure_clear_button = clr

    # --- Persistent tool state ---
    # State is stored on the widget instance, not in globals, so multiple VG widgets won't conflict.
    if not hasattr(self, "_measure_state") or self._measure_state is None:
        self._measure_state = {
            "picker": vtk.vtkCellPicker(),  # screen -> world pick
            "pts": [],                      # in-progress points: [(p, dot_actor), ...]
            "temp_dots": [],                # actors created before a measurement is finalized
            "measures": [],                 # completed measurements: [{"line":..., "txt":..., "d1":..., "d2":...}, ...]
            "obs": None,                    # VTK observer id for LeftButtonPressEvent
        }
        self._measure_state["picker"].SetTolerance(0.0005)

    st = self._measure_state

    # --- Small helpers (render window / interactor) ---
    def _rw():
        """Safely get the RenderWindow."""
        try:
            return self.vtkWidget.GetRenderWindow()
        except Exception:
            return None

    def _iren():
        """
        Safely get the interactor.
        Prefer an existing attribute if your widget sets it; otherwise pull from RenderWindow.
        """
        iren = getattr(self, "render_window_interactor", None)
        if iren is not None:
            return iren
        rw = _rw()
        return rw.GetInteractor() if rw is not None else None

    # --- Scale helpers (dot radius relative to scene size) ---
    def _scene_diag():
        """
        Estimate a characteristic scene size so dot radius scales with the model.
        Falls back to 1.0 if bounds are missing/invalid.
        """
        try:
            b = self.renderer.ComputeVisiblePropBounds()
        except Exception:
            b = None

        if not b or len(b) != 6:
            return 1.0

        dx = (b[1] - b[0])
        dy = (b[3] - b[2])
        dz = (b[5] - b[4])
        s = max(dx, dy, dz)
        return s if s > 0 else 1.0

    # --- VTK actor constructors ---
    def _make_dot(p, color):
        """Create a small sphere marker at world point p."""
        r = 0.0075 * _scene_diag()

        s = vtk.vtkSphereSource()
        s.SetRadius(r)

        m = vtk.vtkPolyDataMapper()
        m.SetInputConnection(s.GetOutputPort())

        a = vtk.vtkActor()
        a.SetMapper(m)
        a.SetPosition(p[0], p[1], p[2])
        a.GetProperty().SetColor(color[0], color[1], color[2])
        a.GetProperty().LightingOff()

        self.renderer.AddActor(a)
        return a

    def _make_line(p1, p2):
        """Create a line actor between p1 and p2."""
        l = vtk.vtkLineSource()
        l.SetPoint1(p1)
        l.SetPoint2(p2)

        m = vtk.vtkPolyDataMapper()
        m.SetInputConnection(l.GetOutputPort())

        a = vtk.vtkActor()
        a.SetMapper(m)

        prop = a.GetProperty()
        prop.SetColor(1.0, 1.0, 0.0)
        prop.SetLineWidth(3.5)
        prop.LightingOff()

        self.renderer.AddActor(a)
        return a

    def _make_label(p1, p2, L):
        """Create a 2D text label anchored in world-space at the midpoint."""
        mid = (
            (p1[0] + p2[0]) * 0.5,
            (p1[1] + p2[1]) * 0.5,
            (p1[2] + p2[2]) * 0.5,
        )
        txt = f"{L:.3f} m"

        coord = vtk.vtkCoordinate()
        coord.SetCoordinateSystemToWorld()
        coord.SetValue(mid[0], mid[1], mid[2])

        t = vtk.vtkTextActor()
        t.SetInput(txt)

        tp = t.GetTextProperty()
        tp.SetFontSize(26)
        tp.SetBold(True)
        tp.SetColor(0.4, 1.0, 1.0)
        tp.SetShadow(True)
        tp.SetShadowOffset(2, -2)
        tp.SetJustificationToCentered()
        tp.SetVerticalJustificationToCentered()

        # Anchor the 2D text actor to a world coordinate
        t.GetPositionCoordinate().SetReferenceCoordinate(coord)
        t.GetPositionCoordinate().SetCoordinateSystemToWorld()

        self.renderer.AddActor2D(t)
        return t

    # --- Render + cleanup helpers ---
    def _render():
        """Request a render, safely."""
        rw = _rw()
        if rw is None:
            return
        try:
            rw.Render()
        except Exception:
            pass

    def _remove_temp():
        """
        Remove any in-progress markers (first click / partial measurement)
        and reset the in-progress points list.
        """
        for d in st["temp_dots"]:
            try:
                self.renderer.RemoveActor(d)
            except Exception:
                pass
        st["temp_dots"].clear()
        st["pts"].clear()

    # --- Main click handler ---
    def _on_click(_obj, _evt):
        """
        If Measure is enabled:
        - pick a world point
        - drop a dot
        - after 2 points: create line + label and commit as a measurement
        """
        if not btn.isChecked():
            return

        iren = _iren()
        if iren is None:
            return

        x, y = iren.GetEventPosition()

        # vtkCellPicker.Pick returns truthy when it hits something in the renderer
        if not st["picker"].Pick(x, y, 0, self.renderer):
            return

        p = st["picker"].GetPickPosition()

        # Color convention: first point cyan-ish, second point red-ish
        color = (0.0, 0.7, 1.0) if len(st["pts"]) == 0 else (1.0, 0.2, 0.2)
        dot = _make_dot(p, color)

        st["pts"].append(((p[0], p[1], p[2]), dot))
        st["temp_dots"].append(dot)

        # If we have two points, finalize measurement
        if len(st["pts"]) == 2:
            (p1, d1), (p2, d2) = st["pts"]

            L = math.dist(p1, p2)
            line = _make_line(p1, p2)
            label = _make_label(p1, p2, L)

            st["measures"].append({"line": line, "txt": label, "d1": d1, "d2": d2})

            # Reset in-progress state so next pair starts fresh
            st["pts"].clear()
            st["temp_dots"].clear()
            _render()

    # --- Toggle wiring (observer attach/detach) ---
    def _toggle(on: bool):
        """
        Turn measurement mode on/off by adding/removing a VTK observer.
        Also cleans up partial state when turning off.
        """
        iren = _iren()
        if iren is None:
            btn.setChecked(False)
            return

        if on:
            # Add observer once; keep id so we can remove it later
            if st["obs"] is None:
                st["obs"] = iren.AddObserver("LeftButtonPressEvent", _on_click, 1.0)
        else:
            # Remove observer and clear any partial click state
            if st["obs"] is not None:
                try:
                    iren.RemoveObserver(st["obs"])
                except Exception:
                    pass
                st["obs"] = None
            _remove_temp()

        _render()

    # --- Clear/Undo actions ---
    def _do_clear():
        """Remove all measurements + any in-progress markers."""
        _remove_temp()

        for m in st["measures"]:
            # Line
            try:
                self.renderer.RemoveActor(m["line"])
            except Exception:
                pass

            # Endpoints
            try:
                self.renderer.RemoveActor(m["d1"])
                self.renderer.RemoveActor(m["d2"])
            except Exception:
                pass

            # Label (Actor2D)
            try:
                self.renderer.RemoveActor2D(m["txt"])
            except Exception:
                # Fallback if someone added it as a 3D actor in other variants
                try:
                    self.renderer.RemoveActor(m["txt"])
                except Exception:
                    pass

        st["measures"].clear()
        _render()

    def _do_undo():
        """Remove the most recent completed measurement."""
        _remove_temp()

        if not st["measures"]:
            return

        m = st["measures"].pop()

        try:
            self.renderer.RemoveActor(m["line"])
        except Exception:
            pass

        try:
            self.renderer.RemoveActor(m["d1"])
            self.renderer.RemoveActor(m["d2"])
        except Exception:
            pass

        try:
            self.renderer.RemoveActor2D(m["txt"])
        except Exception:
            try:
                self.renderer.RemoveActor(m["txt"])
            except Exception:
                pass

        _render()

    # --- Qt signal hookups ---
    btn.toggled.connect(_toggle)
    clr.clicked.connect(_do_clear)
    undo.clicked.connect(_do_undo)

# Activate Patch
def _patch_update_toolbar_for_measure_tool():
    """
    - Wrap VisualizeGeometryWidget.update_toolbar so the measure tool is injected
      after the toolbar is created/refreshed.
    - Does not touch run_solve or any other global patches.
    """
    # Guard so we only patch the class once per process
    if getattr(VisualizeGeometryWidget, "_measure_update_toolbar_patched", False):
        return

    old_update_toolbar = VisualizeGeometryWidget.update_toolbar

    def wrapped_update_toolbar(self, *args, **kwargs):
        # 1) Build the toolbar using the original implementation
        old_update_toolbar(self, *args, **kwargs)
        # 2) Add measurement controls (idempotent per widget instance)
        add_measure_tool(self)

    VisualizeGeometryWidget.update_toolbar = wrapped_update_toolbar
    VisualizeGeometryWidget._measure_update_toolbar_patched = True

# Activate patch at import time so any subsequently created VG widget gets the tool.
_patch_update_toolbar_for_measure_tool()