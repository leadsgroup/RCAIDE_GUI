# =========================================
# AIRCRAFT DRAG (Move Entire Model)
# =========================================
# Adds a "✈️ Drag Aircraft" toggle button to the toolbar.
# When enabled, lets the user click and drag to move the entire aircraft model.

import vtk
from PyQt6.QtWidgets import QPushButton
from tabs.visualize_geometry.visualize_geometry import VisualizeGeometryWidget

class DragAircraftInteractor(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, widget, actors):
        super().__init__()

        # widget gives us access to renderer + vtkWidget
        self.widget = widget

        # actors is a dict of lists (group name -> [vtkActor, ...])
        self.actors = actors

        # drag state
        self.is_dragging = False
        self.last_pos = None

        # depth lock (keeps drag from jumping in/out of screen)
        self._drag_dz = None

        # picker lets us lock drag depth at the clicked point
        self._picker = vtk.vtkCellPicker()
        self._picker.SetTolerance(0.0005)

        # hook mouse events
        self.AddObserver("LeftButtonPressEvent", self.left_down)
        self.AddObserver("LeftButtonReleaseEvent", self.left_up)
        self.AddObserver("MouseMoveEvent", self.mouse_move)

    def left_down(self, obj, event):
        # start dragging
        self.is_dragging = True

        # record starting mouse position
        iren = self.GetInteractor()
        self.last_pos = iren.GetEventPosition()

        # choose a fixed screen-depth for the drag (dz)
        r = self.widget.renderer
        x, y = self.last_pos

        # if we clicked the model, use that picked point for depth
        if self._picker.Pick(x, y, 0, r):
            p = self._picker.GetPickPosition()

            r.SetWorldPoint(p[0], p[1], p[2], 1.0)
            r.WorldToDisplay()
            self._drag_dz = r.GetDisplayPoint()[2]

        # otherwise use camera focal point for depth
        else:
            cam = r.GetActiveCamera()
            fp = cam.GetFocalPoint()

            r.SetWorldPoint(fp[0], fp[1], fp[2], 1.0)
            r.WorldToDisplay()
            self._drag_dz = r.GetDisplayPoint()[2]

    def left_up(self, obj, event):
        # stop dragging
        self.is_dragging = False
        self.last_pos = None
        self._drag_dz = None

    def mouse_move(self, obj, event):
        # only drag when active
        if not self.is_dragging or self.last_pos is None or self._drag_dz is None:
            return

        # current mouse position
        iren = self.GetInteractor()
        x, y = iren.GetEventPosition()

        # pixel delta since last frame
        dx = x - self.last_pos[0]
        dy = y - self.last_pos[1]
        self.last_pos = (x, y)

        r = self.widget.renderer
        dz = self._drag_dz

        # screen -> world for current mouse position
        r.SetDisplayPoint(x, y, dz)
        r.DisplayToWorld()
        wx, wy, wz, _ = r.GetWorldPoint()

        # screen -> world for previous mouse position
        r.SetDisplayPoint(x - dx, y - dy, dz)
        r.DisplayToWorld()
        wx2, wy2, wz2, _ = r.GetWorldPoint()

        # world delta to apply to every actor
        ddx, ddy, ddz = (wx - wx2, wy - wy2, wz - wz2)

        # move every actor by the same world delta
        for group in self.actors.values():
            for actor in group:
                ax, ay, az = actor.GetPosition()
                actor.SetPosition(ax + ddx, ay + ddy, az + ddz)

        # redraw
        iren.GetRenderWindow().Render()


def add_drag_button(self):
    # need toolbar + renderer
    if not getattr(self, "toolbar", None) or getattr(self, "renderer", None) is None:
        return

    # don’t add the button twice
    if getattr(self, "_drag_button_loaded", False):
        return
    self._drag_button_loaded = True

    # toolbar toggle button
    btn = QPushButton("✈️ Drag Aircraft")
    btn.setCheckable(True)

    self.toolbar.addSeparator()
    self.toolbar.addWidget(btn)

    # interactor (where we swap interaction styles)
    iren = self.render_window_interactor

    # keep references so they don’t get garbage collected
    self._drag_style = None
    self._drag_prev_style = None

    def _flatten(container, out):
        # accept dicts, lists, and single actor objects
        if container is None:
            return

        if isinstance(container, dict):
            for v in container.values():
                _flatten(v, out)
            return

        if isinstance(container, (list, tuple, set)):
            for v in container:
                _flatten(v, out)
            return

        # actor-like object
        if hasattr(container, "GetPosition"):
            out.append(container)

    def _collect_aircraft_actors():
        # grab actor containers from the widget (whatever exists)
        groups = {
            "Fuselages": getattr(self, "fuselage_actors", None),
            "Wings": getattr(self, "wing_actors", None),
            "Rotors": getattr(self, "rotor_actors", None),
            "Booms": getattr(self, "boom_actors", None),
            "Fuel Tanks": getattr(self, "fuel_tank_actors", None),
        }

        # flatten each container into a simple list
        flat = {}
        for name, container in groups.items():
            lst = []
            _flatten(container, lst)
            flat[name] = lst

        return flat
    
    def toggle_drag(active):
        if active:
            # save current interaction style
            self._drag_prev_style = iren.GetInteractorStyle()

            # create style once, then reuse it
            if self._drag_style is None:
                self._drag_style = DragAircraftInteractor(self, _collect_aircraft_actors())
            else:
                self._drag_style.actors = _collect_aircraft_actors()

            # make sure the style knows which renderer to use
            self._drag_style.SetDefaultRenderer(self.renderer)

            # enable drag style
            iren.SetInteractorStyle(self._drag_style)

        else:
            # restore previous style
            if self._drag_prev_style is not None:
                iren.SetInteractorStyle(self._drag_prev_style)
        # redraw
        self.vtkWidget.GetRenderWindow().Render()

    # toggle on/off from toolbar
    btn.toggled.connect(toggle_drag)

# patch run_solve to add drag button after solve
def _patch_drag():
    # patch once
    if getattr(VisualizeGeometryWidget, "_drag_patched", False):
        return

    old = VisualizeGeometryWidget.run_solve

    def wrapped(self, *args, **kwargs):
        old(self, *args, **kwargs)
        add_drag_button(self)

    VisualizeGeometryWidget.run_solve = wrapped
    VisualizeGeometryWidget._drag_patched = True

# Activate Patch
_patch_drag()