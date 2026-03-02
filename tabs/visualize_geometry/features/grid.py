# ===================================
# Gridline Overlay Toggle
# ===================================
# Simple grid overlay system for VTK render window, with a checkbox toggle in the toolbar

from PyQt6.QtWidgets import QCheckBox
import vtk
from tabs.visualize_geometry.visualize_geometry import VisualizeGeometryWidget

def add_fullscreen_grid(renderer, divisions=12):
    """Create a layer-1 overlay renderer that draws a 2D grid across the window.

    Returns the overlay renderer or None.
    """
    # If renderer or window isn't available, do nothing
    if renderer is None or not hasattr(renderer, "GetRenderWindow"):
        return None
    win = renderer.GetRenderWindow()
    if win is None:
        return None

    # Get window size; if zero, don't draw
    w, h = win.GetActualSize()
    if not w or not h:
        return None

    # Simple grid color and opacity
    color, opacity = (0.6, 0.7, 0.9), 0.25

    # Determine spacing between grid lines
    step = max(1.0, min(w, h) / float(max(1, divisions)))

    # Build points and line cells for the grid
    pts = vtk.vtkPoints()
    lines = vtk.vtkCellArray()
    pid = 0

    # Add vertical grid lines
    for i in range(int(w / step) + 1):
        x = i * step
        pts.InsertNextPoint(x, 0, 0)
        pts.InsertNextPoint(x, h, 0)
        lines.InsertNextCell(2)
        lines.InsertCellPoint(pid)
        lines.InsertCellPoint(pid + 1)
        pid += 2

    # Add horizontal grid lines
    for j in range(int(h / step) + 1):
        y = j * step
        pts.InsertNextPoint(0, y, 0)
        pts.InsertNextPoint(w, y, 0)
        lines.InsertNextCell(2)
        lines.InsertCellPoint(pid)
        lines.InsertCellPoint(pid + 1)
        pid += 2

    # Make polydata and a 2D mapper/actor
    grid = vtk.vtkPolyData()
    grid.SetPoints(pts)
    grid.SetLines(lines)

    mapper = vtk.vtkPolyDataMapper2D()
    mapper.SetInputData(grid)

    actor = vtk.vtkActor2D()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(color)
    actor.GetProperty().SetOpacity(opacity)

    # Overlay renderer (non-interactive)
    overlay = vtk.vtkRenderer()
    overlay.SetLayer(1)
    overlay.InteractiveOff()
    overlay.AddActor(actor)
    overlay.SetBackgroundAlpha(0.0)

    # Ensure base layer + overlay layer
    try:
        win.SetNumberOfLayers(2)
    except Exception:
        pass

    win.AddRenderer(overlay)
    return overlay

def _remove_grid_overlay(self):
    """Remove overlay renderer if present."""
    r = getattr(self, "renderer", None)
    if r is None or not hasattr(r, "GetRenderWindow"):
        self.overlay_grid = None
        return

    win = r.GetRenderWindow()
    overlay = getattr(self, "overlay_grid", None)
    if overlay is None or win is None:
        self.overlay_grid = None
        return

    try:
        win.RemoveRenderer(overlay)
    except Exception:
        pass

    self.overlay_grid = None

def _rebuild_grid_overlay_if_enabled(self):
    """Toggle/rebuild grid overlay based on checkbox state."""
    r = getattr(self, "renderer", None)
    if r is None:
        return

    cb = getattr(self, "grid_checkbox", None)
    if cb is None:
        return

    # Remove if disabled
    if not cb.isChecked():
        _remove_grid_overlay(self)
        try:
            r.GetRenderWindow().Render()
        except Exception:
            pass
        return

    # Rebuild (remake to match current window size)
    _remove_grid_overlay(self)
    self.overlay_grid = add_fullscreen_grid(r, divisions=12)

    try:
        r.GetRenderWindow().Render()
    except Exception:
        pass

def _add_gridline_toggle(self):
    """Add the gridlines checkbox once; safe to call repeatedly."""
    if not hasattr(self, "toolbar") or self.toolbar is None:
        return
    if getattr(self, "_gridline_toggle_added", False):
        return
    if getattr(self, "renderer", None) is None:
        return

    self._gridline_toggle_added = True

    # Checkbox UI
    self.grid_checkbox = QCheckBox("Show Gridlines")
    self.grid_checkbox.setChecked(False)
    self.grid_checkbox.setStyleSheet("""
    QCheckBox {
        color: white;
        font-size: 10pt;
        border: 1px solid white;
        padding: 2px;
    }
    """)

    self.toolbar.addSeparator()
    self.toolbar.addWidget(self.grid_checkbox)

    # Toggle behavior
    self.grid_checkbox.stateChanged.connect(lambda _s: _rebuild_grid_overlay_if_enabled(self))

    # Resize observer (install once)
    if not getattr(self, "_grid_resize_observer_added", False):
        self._grid_resize_observer_added = True
        try:
            win = self.renderer.GetRenderWindow()

            def on_resize(_o, _e):
                _rebuild_grid_overlay_if_enabled(self)

            win.AddObserver("WindowResizeEvent", on_resize)
        except Exception:
            pass

# Activate Patch
def _patch_update_toolbar_for_gridlines():
    """Patch update_toolbar once (no run_solve wrapper stacking)."""
    if getattr(VisualizeGeometryWidget, "_grid_update_toolbar_patched", False):
        return

    old_update_toolbar = VisualizeGeometryWidget.update_toolbar

    def wrapped_update_toolbar(self, *args, **kwargs):
        old_update_toolbar(self, *args, **kwargs)
        _add_gridline_toggle(self)

    VisualizeGeometryWidget.update_toolbar = wrapped_update_toolbar
    VisualizeGeometryWidget._grid_update_toolbar_patched = True

_patch_update_toolbar_for_gridlines()