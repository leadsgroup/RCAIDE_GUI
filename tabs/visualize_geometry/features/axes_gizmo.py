# =====================================
# AXES GIZMO
# =====================================
# Adds a small 3D axes gizmo in the corner of the VTK view

import vtk
from tabs.visualize_geometry.visualize_geometry import VisualizeGeometryWidget

def _bind_gizmo_renderer(widget, renderer):
    # VTK uses different method names depending on the version
    try:
        widget.SetCurrentRenderer(renderer)
    except Exception:
        try:
            widget.SetDefaultRenderer(renderer)
        except Exception:
            pass

def add_orientation_gizmo(self):
    # Need renderer + render window + interactor
    r = getattr(self, "renderer", None)
    if r is None:
        return
    try:
        rw = self.vtkWidget.GetRenderWindow()
    except Exception:
        return
    if rw is None:
        return
    iren = rw.GetInteractor()
    if iren is None:
        return

    # Reuse existing widget so we don’t create duplicates
    widget = getattr(self, "_axes_widget", None) or getattr(iren, "_axes_widget", None)

    if widget is None:
        # Axes + label styling
        axes = vtk.vtkAxesActor()
        for cap in (
            axes.GetXAxisCaptionActor2D(),
            axes.GetYAxisCaptionActor2D(),
            axes.GetZAxisCaptionActor2D(),
        ):
            tp = cap.GetTextActor().GetTextProperty()
            tp.SetFontSize(14)
            tp.SetColor(1.0, 1.0, 1.0)

        # Light wireframe border around the gizmo
        border = vtk.vtkCubeSource()
        border.SetXLength(1.2)
        border.SetYLength(1.2)
        border.SetZLength(1.2)

        border_mapper = vtk.vtkPolyDataMapper()
        border_mapper.SetInputConnection(border.GetOutputPort())

        border_actor = vtk.vtkActor()
        border_actor.SetMapper(border_mapper)
        p = border_actor.GetProperty()
        p.SetColor(0.8, 0.8, 0.8)
        p.SetOpacity(0.1)
        p.SetRepresentationToWireframe()
        p.LightingOff()

        # Combine axes + border into one marker
        assembly = vtk.vtkPropAssembly()
        assembly.AddPart(border_actor)
        assembly.AddPart(axes)

        # Small overlay widget in the corner
        widget = vtk.vtkOrientationMarkerWidget()
        widget.SetOrientationMarker(assembly)
        widget.SetViewport(0.0, 0.0, 0.18, 0.28)
        widget.SetInteractor(iren)

    # Attach to the current renderer (important if renderer was rebuilt)
    _bind_gizmo_renderer(widget, r)

    # Some VTK builds need this before enabling the widget
    try:
        if not iren.GetInitialized():
            iren.Initialize()
    except Exception:
        pass

    # Keep it visible but not clickable
    widget.EnabledOn()
    widget.InteractiveOff()

    # Store in both places so it survives tab switches
    self._axes_widget = widget
    iren._axes_widget = widget

    # Redraw now
    try:
        rw.Render()
    except Exception:
        pass

def _rebind_axes_gizmo_on_show(self):
    # Tab switching can recreate the renderer/interactor, so we reattach the gizmo
    r = getattr(self, "renderer", None)
    if r is None:
        return
    try:
        rw = self.vtkWidget.GetRenderWindow()
    except Exception:
        return
    if rw is None:
        return
    iren = rw.GetInteractor()
    if iren is None:
        return

    # Find existing gizmo widget
    w = getattr(self, "_axes_widget", None) or getattr(iren, "_axes_widget", None)
    if w is None:
        return

    # Reattach to the current interactor/renderer
    try:
        w.SetInteractor(iren)
    except Exception:
        pass
    _bind_gizmo_renderer(w, r)

    # Turn it back on and redraw
    try:
        w.EnabledOn()
        w.InteractiveOff()
        rw.Render()
    except Exception:
        pass

# Activate Patch
def _patch_run_solve_for_axes_gizmo():
    # After run_solve builds the scene, make sure the gizmo exists
    if getattr(VisualizeGeometryWidget, "_axes_gizmo_patched", False):
        return
    base = VisualizeGeometryWidget.run_solve

    def wrapped(self, *args, **kwargs):
        base(self, *args, **kwargs)
        add_orientation_gizmo(self)

    VisualizeGeometryWidget.run_solve = wrapped
    VisualizeGeometryWidget._axes_gizmo_patched = True

# Activate Patch
def _patch_showEvent_for_axes_gizmo_rebind():
    # When the widget becomes visible again, rebind the gizmo
    if getattr(VisualizeGeometryWidget, "_axes_showevent_patched", False):
        return
    old = getattr(VisualizeGeometryWidget, "showEvent", None)

    def wrapped(self, event):
        if old is not None:
            try:
                old(self, event)
            except Exception:
                pass
        _rebind_axes_gizmo_on_show(self)

    VisualizeGeometryWidget.showEvent = wrapped
    VisualizeGeometryWidget._axes_showevent_patched = True

_patch_run_solve_for_axes_gizmo()
_patch_showEvent_for_axes_gizmo_rebind()