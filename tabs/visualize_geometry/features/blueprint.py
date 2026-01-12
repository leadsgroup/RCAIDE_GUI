# ==========================
# BLUEPRINT UPLOAD SYSTEM
# ==========================
# Loads 2D blueprint images (top/side/front) as textured planes around the model.
# Click a blueprint to select it (highlights with an outline).

from PyQt6.QtWidgets import QPushButton, QFileDialog, QMenu
from PyQt6.QtCore import QTimer
import vtk, os
from tabs.visualize_geometry.visualize_geometry import VisualizeGeometryWidget

class BlueprintManager:
    # Manages blueprint images (load, show, click-to-select).
    def __init__(self, widget):
        # parent widget (VisualizeGeometryWidget)
        self.widget = widget

        # vtk renderer (may change after solve)
        self.renderer = getattr(widget, "renderer", None)

        # blueprint actors by view key: "top" / "side" / "front"
        self.actors = {}

        # outline actors (only one should be visible at a time)
        self.outlines = {}

        # currently selected view key
        self.selected_view = None

        # current settings (sliders can change these)
        self.opacity = 0.5
        self.scale = 1.0

        # per-view transform objects (used for scaling)
        self.base_transforms = {}

        # picker for selecting actors by clicking
        self.picker = vtk.vtkPropPicker()

        # observer id so we only attach click handling once
        self._pick_obs_id = None

    def _rw(self):
        # get render window
        try:
            return self.widget.vtkWidget.GetRenderWindow()
        except Exception:
            return None

    def _iren(self):
        # get interactor (mouse events)
        rw = self._rw()
        try:
            return rw.GetInteractor() if rw is not None else None
        except Exception:
            return None

    def _store_camera(self):
        # save camera so loading blueprints doesn't change the view
        if self.renderer is None:
            return None

        cam = self.renderer.GetActiveCamera()
        if cam is None:
            return None

        return {
            "pos": cam.GetPosition(),
            "focal": cam.GetFocalPoint(),
            "viewup": cam.GetViewUp(),
            "clipping": cam.GetClippingRange(),
        }

    def _restore_camera(self, state):
        # restore camera after adding actor
        if self.renderer is None or not state:
            return

        cam = self.renderer.GetActiveCamera()
        if cam is None:
            return

        cam.SetPosition(*state["pos"])
        cam.SetFocalPoint(*state["focal"])
        cam.SetViewUp(*state["viewup"])
        cam.SetClippingRange(*state["clipping"])

        try:
            self.renderer.ResetCameraClippingRange()
        except Exception:
            pass

    def _read_image_as_texture(self, file_name):
        # choose png vs jpeg reader
        ext = os.path.splitext(file_name)[1].lower()
        reader = vtk.vtkJPEGReader() if ext in [".jpg", ".jpeg"] else vtk.vtkPNGReader()

        # read image
        reader.SetFileName(file_name)
        reader.Update()

        # make texture
        texture = vtk.vtkTexture()
        texture.SetInputConnection(reader.GetOutputPort())

        # texture options for nicer display
        texture.InterpolateOn()
        texture.RepeatOff()
        texture.EdgeClampOn()

        return texture, reader.GetOutput()

    def _model_bounds(self):
        # compute visible bounds (fallback if empty scene)
        if self.renderer is None:
            b = (-1, 1, -1, 1, -1, 1)
        else:
            b = self.renderer.ComputeVisiblePropBounds() or (-1, 1, -1, 1, -1, 1)

        # center of model bounds
        cx = (b[0] + b[1]) / 2
        cy = (b[2] + b[3]) / 2
        cz = (b[4] + b[5]) / 2

        # sizes of bounds (avoid zeros)
        sx = (b[1] - b[0]) or 1
        sy = (b[3] - b[2]) or 1
        sz = (b[5] - b[4]) or 1

        # base scale for spacing
        base = max(sx, sy, sz)

        return b, (cx, cy, cz), (sx, sy, sz), base

    def _make_outline(self, actor):
        # build a wireframe cube around actor bounds
        cube = vtk.vtkCubeSource()
        cube.SetBounds(actor.GetBounds())

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(cube.GetOutputPort())

        outline = vtk.vtkActor()
        outline.SetMapper(mapper)

        # outline styling
        outline.GetProperty().SetColor(0.2, 0.6, 1.0)
        outline.GetProperty().SetLineWidth(3)
        outline.GetProperty().LightingOff()
        outline.GetProperty().SetRepresentationToWireframe()

        return outline

    def _update_outline(self, view):
        # keep outline matching the actor after transform changes
        if view not in self.actors or view not in self.outlines:
            return

        actor = self.actors[view]
        outline = self.outlines[view]

        try:
            cube = outline.GetMapper().GetInputConnection(0, 0).GetProducer()
            cube.SetBounds(actor.GetBounds())
        except Exception:
            pass

    def _highlight_selected(self, view):
        # renderer required
        if self.renderer is None:
            return

        # remove all existing outlines
        for o in list(self.outlines.values()):
            try:
                self.renderer.RemoveActor(o)
            except Exception:
                pass

        # add outline for selected blueprint
        if view in self.actors:
            outline = self._make_outline(self.actors[view])
            self.renderer.AddActor(outline)
            self.outlines[view] = outline

        # render now
        rw = self._rw()
        if rw is not None:
            try:
                rw.Render()
            except Exception:
                pass

    def enable_picking(self):
        # refresh renderer reference
        self.renderer = getattr(self.widget, "renderer", None)

        # need interactor
        iren = self._iren()
        if iren is None:
            return

        # only attach once
        if self._pick_obs_id is not None:
            return

        # attach click handler
        try:
            self._pick_obs_id = iren.AddObserver("LeftButtonPressEvent", self._on_click, 1.0)
        except Exception:
            self._pick_obs_id = None

    def _on_click(self, obj, event):
        # refresh renderer reference
        self.renderer = getattr(self.widget, "renderer", None)
        if self.renderer is None:
            return

        # get mouse position
        try:
            x, y = obj.GetEventPosition()
        except Exception:
            return

        # pick an actor
        try:
            self.picker.Pick(x, y, 0, self.renderer)
            picked = self.picker.GetActor()
        except Exception:
            return

        # ignore empty clicks
        if not picked:
            return

        # match picked actor to a blueprint view
        for v, a in self.actors.items():
            if a == picked:
                self.selected_view = v
                self._highlight_selected(v)

                # let widget sync sliders if it has helper
                if hasattr(self.widget, "_reset_blueprint_sliders"):
                    try:
                        self.widget._reset_blueprint_sliders()
                    except Exception:
                        pass
                break

    def load_image(self, view):
        # refresh renderer reference
        self.renderer = getattr(self.widget, "renderer", None)
        if self.renderer is None:
            return

        # ask user for file
        file_name, _ = QFileDialog.getOpenFileName(
            self.widget,
            f"Select {view.capitalize()} Blueprint",
            "",
            "Image Files (*.png *.jpg *.jpeg)"
        )
        if not file_name:
            return

        # keep camera stable
        cam_state = self._store_camera()

        # load texture + image data
        texture, img_data = self._read_image_as_texture(file_name)

        # get image size
        iw, ih, _ = img_data.GetDimensions()
        if iw == 0 or ih == 0:
            return

        # preserve aspect ratio
        aspect = iw / ih

        # get model placement info
        b, (cx, cy, cz), (sx, sy, sz), base = self._model_bounds()

        # place blueprint a bit outside the model
        spacing = 0.25 * base

        # choose blueprint plane size
        bp_width = 0.9 * sx
        bp_height = bp_width / aspect

        # build plane geometry
        plane = vtk.vtkPlaneSource()

        # place plane for "top"
        if view == "top":
            z = b[4] - spacing
            plane.SetOrigin(cx - bp_width / 2, cy - bp_height / 2, z)
            plane.SetPoint1(cx + bp_width / 2, cy - bp_height / 2, z)
            plane.SetPoint2(cx - bp_width / 2, cy + bp_height / 2, z)

        # place plane for "side"
        elif view == "side":
            y = b[3] + spacing
            plane.SetOrigin(cx - bp_width / 2, y, cz - bp_height / 2)
            plane.SetPoint1(cx + bp_width / 2, y, cz - bp_height / 2)
            plane.SetPoint2(cx - bp_width / 2, y, cz + bp_height / 2)

        # place plane for "front"
        elif view == "front":
            x = b[1] + spacing
            plane.SetOrigin(x, cy - bp_width / 2, cz - bp_height / 2)
            plane.SetPoint1(x, cy + bp_width / 2, cz - bp_height / 2)
            plane.SetPoint2(x, cy - bp_width / 2, cz + bp_height / 2)

        # unknown view key
        else:
            return

        # map plane geometry
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(plane.GetOutputPort())

        # create actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.SetTexture(texture)

        # basic styling
        actor.GetProperty().SetOpacity(self.opacity)
        actor.GetProperty().LightingOff()
        actor.SetPickable(True)

        # remove existing actor for this view
        if view in self.actors:
            try:
                self.renderer.RemoveActor(self.actors[view])
            except Exception:
                pass

        # add actor to scene
        self.renderer.AddActor(actor)
        self.actors[view] = actor

        # create stored transform (used by scale slider)
        self.base_transforms[view] = vtk.vtkTransform()
        actor.SetUserTransform(self.base_transforms[view])

        # select this view
        self.selected_view = view
        self._highlight_selected(view)

        # restore camera
        self._restore_camera(cam_state)

        # let widget sync sliders if it has helper
        if hasattr(self.widget, "_reset_blueprint_sliders"):
            try:
                self.widget._reset_blueprint_sliders()
            except Exception:
                pass

        # render now
        rw = self._rw()
        if rw is not None:
            try:
                rw.Render()
            except Exception:
                pass

    def update_opacity(self, value):
        # slider gives 0..100, convert to 0..1
        self.opacity = value / 100.0

        # update selected actor only
        if self.selected_view in self.actors:
            try:
                self.actors[self.selected_view].GetProperty().SetOpacity(self.opacity)
                self._rw().Render()
            except Exception:
                pass

    def update_scale(self, value):
        # slider gives 0..100, convert to 0..1
        self.scale = value / 100.0

        # update selected actor only
        if self.selected_view in self.actors:
            try:
                transform = self.base_transforms[self.selected_view]
                transform.Identity()
                transform.Scale(self.scale, self.scale, self.scale)

                self.actors[self.selected_view].SetUserTransform(transform)
                self._update_outline(self.selected_view)

                self._rw().Render()
            except Exception:
                pass

    def clear_all(self):
        # nothing to clear if renderer missing
        if self.renderer is None:
            return

        # remove blueprint actors
        for a in list(self.actors.values()):
            try:
                self.renderer.RemoveActor(a)
            except Exception:
                pass

        # remove outlines
        for o in list(self.outlines.values()):
            try:
                self.renderer.RemoveActor(o)
            except Exception:
                pass

        # reset state
        self.actors.clear()
        self.outlines.clear()
        self.selected_view = None

        # render now
        rw = self._rw()
        if rw is not None:
            try:
                rw.Render()
            except Exception:
                pass

def add_blueprint_menu(self):
    # don’t add twice
    if getattr(self, "_blueprint_menu_loaded", False):
        return
    self._blueprint_menu_loaded = True

    # create the manager (stores state on the widget)
    self.blueprint_manager = BlueprintManager(self)

    def _add_menu():
        # toolbar must exist
        if not getattr(self, "toolbar", None):
            return

        # button + menu
        btn = QPushButton("📐 Blueprint")
        menu = QMenu(btn)

        # load actions
        menu.addAction("Load Top View", lambda: self.blueprint_manager.load_image("top"))
        menu.addAction("Load Side View", lambda: self.blueprint_manager.load_image("side"))
        menu.addAction("Load Front View", lambda: self.blueprint_manager.load_image("front"))

        # clear action
        menu.addSeparator()
        menu.addAction("🧹 Clear All Blueprints", lambda: self.blueprint_manager.clear_all())

        # attach menu to button
        btn.setMenu(menu)
        self.toolbar.addWidget(btn)

        # enable click selection
        self.blueprint_manager.enable_picking()

        # keep toolbar visible on top
        try:
            self.toolbar.raise_()
        except Exception:
            pass

    # add the menu after Qt finishes building the toolbar
    QTimer.singleShot(0, _add_menu)

# Activate Patch
def _patch_run_solve_for_blueprints():
    # patch run_solve to add blueprint menu after solve
    if getattr(VisualizeGeometryWidget, "_blueprint_patched", False):
        return

    base = VisualizeGeometryWidget.run_solve

    def wrapped(self, *args, **kwargs):
        base(self, *args, **kwargs)
        add_blueprint_menu(self)

    VisualizeGeometryWidget.run_solve = wrapped
    VisualizeGeometryWidget._blueprint_patched = True

_patch_run_solve_for_blueprints()

# ================================
# BLUEPRINT ADJUSTOR DROPDOWN
# ================================
# Adds an "Adjustor" button to the toolbar that opens a dropdown menu
# with sliders to adjust the opacity and size of the selected blueprint.

from PyQt6.QtWidgets import (
    QPushButton, QWidget, QMenu, QLabel,
    QSlider, QVBoxLayout, QWidgetAction
)
from PyQt6.QtCore import Qt, QTimer

def add_blueprint_adjustor_dropdown(self):
    # don’t add this twice
    if getattr(self, "_blueprint_adjustor_loaded", False):
        return
    self._blueprint_adjustor_loaded = True

    # create the button that opens the dropdown
    adjustor_btn = QPushButton("Adjustor")
    adjustor_btn.setFlat(True)

    # style the button to match the toolbar
    adjustor_btn.setStyleSheet("""
        QPushButton {
            color: #a8c7ff;
            background-color: transparent;
            border: 1px solid #3a3f47;
            border-radius: 4px;
            padding: 5px 10px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: rgba(74,144,226,25);
            border: 1px solid #4a90e2;
            color: #b7dcff;
        }
        QPushButton:pressed {
            background-color: rgba(74,144,226,60);
            color: #d9e9ff;
        }
    """)
    # menu that shows when you click the button
    menu = QMenu(adjustor_btn)

    # menu styling
    menu.setStyleSheet("""
        QMenu {
            background-color: #2b2e35;
            color: #dcdfe4;
            border: 1px solid #4a90e2;
            padding: 8px 10px 10px 10px;
        }
    """)

    # widget that holds the sliders inside the menu
    content = QWidget()

    # vertical layout for title + sliders
    layout = QVBoxLayout(content)
    layout.setContentsMargins(10, 12, 10, 10)
    layout.setSpacing(10)

    # shows which blueprint is currently selected
    title = QLabel("Active Blueprint: None")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setWordWrap(False)

    # title styling
    title.setStyleSheet("""
        font-weight: bold;
        color: #b7dcff;
        font-size: 13px;
        padding: 4px 2px 6px 2px;
    """)
    layout.addWidget(title)

    # transparency header
    t_label = QLabel("Transparency")
    t_label.setStyleSheet("font-weight:bold;color:#b7dcff;font-size:12px;")
    layout.addWidget(t_label)

    # transparency slider (0..100)
    t_slider = QSlider(Qt.Orientation.Horizontal)
    t_slider.setRange(0, 100)
    t_slider.setValue(50)
    layout.addWidget(t_slider)

    # size header
    s_label = QLabel("Size")
    s_label.setStyleSheet("font-weight:bold;color:#b7dcff;font-size:12px;")
    layout.addWidget(s_label)

    # size slider (50..200)
    s_slider = QSlider(Qt.Orientation.Horizontal)
    s_slider.setRange(50, 200)
    s_slider.setValue(100)
    layout.addWidget(s_slider)

    def bind_blueprint_manager():
        # BlueprintManager is created later, so retry until it exists
        if not hasattr(self, "blueprint_manager"):
            QTimer.singleShot(300, bind_blueprint_manager)
            return

        bm = self.blueprint_manager

        # store slider values per view ("top"/"side"/"front")
        bm._view_states = {}

        def refresh_label():
            # update the “Active Blueprint” label
            active = getattr(bm, "selected_view", None) or "None"
            title.setText(f"Active Blueprint: {active.capitalize()}")

        def on_opacity_change(val):
            # if a blueprint is selected, apply opacity and save the slider value
            if bm.selected_view:
                bm.update_opacity(val)
                bm._view_states.setdefault(bm.selected_view, {})["opacity"] = val

        def on_scale_change(val):
            # if a blueprint is selected, apply scale and save the slider value
            if bm.selected_view:
                bm.update_scale(val)
                bm._view_states.setdefault(bm.selected_view, {})["scale"] = val

        # slider -> blueprint updates
        t_slider.valueChanged.connect(on_opacity_change)
        s_slider.valueChanged.connect(on_scale_change)

        # when you load a blueprint, update label + restore stored slider values
        old_load = bm.load_image

        def wrapped_load_image(view):
            old_load(view)
            bm.selected_view = view
            refresh_label()

            state = bm._view_states.get(view, {"opacity": 50, "scale": 100})
            t_slider.setValue(state["opacity"])
            s_slider.setValue(state["scale"])

        bm.load_image = wrapped_load_image
        # when you click a blueprint, update label + restore stored slider values
        old_click = bm._on_click

        def wrapped_click(obj, event):
            old_click(obj, event)
            refresh_label()

            if bm.selected_view:
                state = bm._view_states.get(bm.selected_view, {"opacity": 50, "scale": 100})
                t_slider.setValue(state["opacity"])
                s_slider.setValue(state["scale"])

        bm._on_click = wrapped_click

        refresh_label()

    # start binding (will retry until blueprint_manager exists)
    bind_blueprint_manager()

    # put the content widget inside the menu
    widget_action = QWidgetAction(menu)
    widget_action.setDefaultWidget(content)
    menu.addAction(widget_action)

    # attach the menu to the button
    adjustor_btn.setMenu(menu)

    def insert_adjustor_button():
        # put Adjustor next to the "📐 Blueprint" button in the toolbar
        for act in self.toolbar.actions():
            w = self.toolbar.widgetForAction(act)
            if hasattr(w, "text") and "Blueprint" in w.text():
                idx = self.toolbar.actions().index(act)

                if idx < len(self.toolbar.actions()) - 1:
                    self.toolbar.insertWidget(self.toolbar.actions()[idx + 1], adjustor_btn)
                else:
                    self.toolbar.addWidget(adjustor_btn)
                return

        # retry if toolbar isn’t ready yet
        QTimer.singleShot(500, insert_adjustor_button)

    insert_adjustor_button()

# patch run_solve once so adjustor gets added after solve builds UI
if not hasattr(VisualizeGeometryWidget, "_blueprint_adjustor_patched"):
    base_run = VisualizeGeometryWidget.run_solve

    def wrapped_run(self):
        base_run(self)
        add_blueprint_adjustor_dropdown(self)

    VisualizeGeometryWidget.run_solve = wrapped_run
    VisualizeGeometryWidget._blueprint_adjustor_patched = True