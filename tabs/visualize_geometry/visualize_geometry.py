# RCAIDE_GUI/tabs/visualize_geometry/core_3d_viewer.py

# RCAIDE Imports
import RCAIDE
from RCAIDE.Framework.Core import Units
from RCAIDE.Library.Components.Airfoils import Airfoil
from RCAIDE.Library.Plots.Geometry.generate_3d_wing_points      import *
from RCAIDE.Library.Plots.Geometry.generate_3d_fuselage_points  import *
from RCAIDE.Library.Plots.Geometry.generate_3d_fuel_tank_points import *
from RCAIDE.Library.Plots.Geometry.generate_3d_nacelle_points   import *
from RCAIDE.Library.Components                                   import Component
from RCAIDE.Library.Plots.Geometry.generate_3d_cargo_bay_points import generate_3d_cargo_bay_points
from RCAIDE.Library.Plots.Geometry.generate_3d_lopa_points      import generate_3d_lopa_points
from RCAIDE.Library.Plots.Geometry.generate_3d_torus_points     import generate_3d_torus_points
from RCAIDE.Library.Plots.Geometry.generate_3d_cabin_points     import generate_3d_cabin_points
from RCAIDE.Library.Plots.Geometry.generate_3d_cuboid_points    import generate_3d_cuboid_points
from RCAIDE.Library.Plots.Geometry.generate_3d_propulsor_points import generate_3d_propulsor_points
from RCAIDE.Library.Plots.Geometry.plot_3d_rotor                import generate_3d_blade_points, generate_vtk_object
from RCAIDE.Library.Plots.Geometry.plot_3d_vehicle              import add_lopa_seats
from RCAIDE.Library.Methods.Geometry.Planform                   import fuselage_planform, wing_planform, compute_fuel_volume
from RCAIDE.Library.Methods.Geometry.LOPA                       import compute_layout_of_passenger_accommodations
# Learner fuselages may have no user-defined cross-section segments.  The
# shared helper supports both those simple bodies and fully segmented aircraft.
from tabs.visualize_geometry.geometry_helper_functions import (
    generate_fuselage_points_for_viewer,
    learner_component_callout_data,
)
from vtkmodules.vtkRenderingCore import vtkBillboardTextActor3D

# PyQt imports
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QHeaderView, QLabel, QToolBar, QColorDialog, QSpacerItem, QSizePolicy, QFrame, QLineEdit, QScrollArea
from PyQt6.QtCore import Qt
from tabs import TabWidget
from pyvistaqt import QtInteractor
from PyQt6.QtGui import QIcon

# Python imports
import matplotlib.colors as mcolors
import pyvista as pv
import numpy as np
import rcaide_io
import os
from copy import deepcopy
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera

# ------------------------------------------------------------------------------
# make_object
# ------------------------------------------------------------------------------
class CustomInteractorStyle(vtkInteractorStyleTrackballCamera):
    def __init__(self, parent=None):
        super().__init__()
        self.AddObserver("KeyPressEvent", self.on_key_press)  # type: ignore

    def on_key_press(self, obj, event):
        key = self.GetInteractor().GetKeySym()
        camera = self.GetInteractor().GetRenderWindow(
        ).GetRenderers().GetFirstRenderer().GetActiveCamera()

        # Example custom camera controls
        if key == "Down":
            camera.Pitch(10)  # Pitch up by 10 degrees
        elif key == "Up":
            camera.Pitch(-10)  # Pitch down by 10 degrees
        elif key == "Left":
            camera.Yaw(-10)  # Yaw left by 10 degrees
        elif key == "Right":
            camera.Yaw(10)  # Yaw right by 10 degrees

        self.GetInteractor().GetRenderWindow().Render()  # Render the changes

_DEFAULT_OPACITY = {
    "Fuselages":    0.5,
    "Wings":        0.5,
    "Nacelles":     1.0,
    "Propulsors":   0.5,
    "Booms":        1.0,
    "Fuel Tanks":   0.5,
    "Cargo Bays":   0.6,
    "Landing Gear": 1.0,
    "Cabins":       0.75,
    "Systems":      0.8,
}

class ColorBar(QWidget):
    def __init__(self, parts_dict, color_changed):
        super().__init__()
        self.setFixedWidth(180)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 5, 5, 0)
        self.layout.setSpacing(10)
        self.setLayout(self.layout)

        self.part_controls = {}
        self.color_changed = color_changed

        for index, part_name in enumerate(parts_dict):
            # Set colorbar label
            title = QLabel(part_name)
            self.layout.addWidget(title)

            # Set Transparency
            opacity_row = QHBoxLayout()
            opacity_label = QLabel("Transparency:")
            default_opacity = _DEFAULT_OPACITY.get(part_name, 1.0)
            opacity_input = QLineEdit(f"{default_opacity:.2f}")
            opacity_input.setFixedWidth(50)
            opacity_input.setStyleSheet("background-color: white; color: black;")
            opacity_input.editingFinished.connect(
                lambda name=part_name, box=opacity_input: self.opacity_changed(name, box)
            )
            opacity_row.addWidget(opacity_label)
            opacity_row.addWidget(opacity_input)
            self.layout.addLayout(opacity_row)

            # Set color
            color_row = QHBoxLayout()
            color_label = QLabel("Color:")
            color_label.setStyleSheet("color: white;")
            color_buttom = QPushButton()
            color_buttom.setFixedSize(30, 20)
            color_buttom.setStyleSheet("background-color: #d3d3d3; border: 1px solid #888;")
            color_buttom.clicked.connect(lambda _, name=part_name: self.pick_color(name))
            color_row.addWidget(color_label)
            color_row.addWidget(color_buttom)
            self.layout.addLayout(color_row)

            #Put all buttom and opacity variable in part_controls make it easy to find
            self.part_controls[part_name] = {
                "opacity_input": opacity_input,
                "color_buttom": color_buttom
            }

            #add separate line
            if index < len(parts_dict)-1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFrameShadow(QFrame.Shadow.Sunken)
                self.layout.addWidget(line)

        # Spacer to push everything up
        self.layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    def pick_color(self, part_name):
        color = QColorDialog.getColor(options=QColorDialog.ColorDialogOption.ShowAlphaChannel)
        buttom = self.part_controls[part_name]["color_buttom"]
        buttom.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #888;")
        self.color_changed(part_name, color=color)

    def opacity_changed(self, part_name, edit_val):
        if edit_val:
            val = float(edit_val.text())
            val = max(0.0, min(1.0, val))
        else:
            val = 1.0
        edit_val.setText(f"{val:.2f}")
        self.color_changed(part_name, opacity=val)

    def update_parts(self, new_parts_dict):
        # After load the geometry, upload the color buttom and opacity value
        for part_name, actors in new_parts_dict.items():
            enabled = bool(actors)
            controls = self.part_controls.get(part_name, {})
            if controls:
                # Make the function work
                controls["opacity_input"].setEnabled(enabled)
                controls["color_buttom"].setEnabled(enabled)
                # Reset to per-component default
                controls["opacity_input"].setText(f"{_DEFAULT_OPACITY.get(part_name, 1.0):.2f}")
                if part_name == "Fuselage":
                    controls["color_buttom"].setStyleSheet("background-color: #648eee; border: 1px solid #888;")
                else:
                    controls["color_buttom"].setStyleSheet("background-color: #d3d3d3; border: 1px solid #888;")

class CustomPanInteractorStyle(vtkInteractorStyleTrackballCamera):
    def __init__(self, parent=None):
        super().__init__()
        self.AddObserver("MouseMoveEvent", self.on_mouse_move)  # moniter the mouse move
        self.AddObserver("LeftButtonPressEvent", self.on_left_button_down)
        self.AddObserver("LeftButtonReleaseEvent", self.on_left_button_up)
        self.is_panning = False
        self.last_x = None
        self.last_y = None

    def on_left_button_down(self, obj, event):
        interactor = self.GetInteractor()
        self.last_x, self.last_y = interactor.GetEventPosition()
        self.is_panning = True
        self.OnLeftButtonDown()

    def on_left_button_up(self, obj, event):
        self.is_panning = False
        self.OnLeftButtonUp()

    def on_mouse_move(self, obj, event):
        if not self.is_panning:
            return

        interactor = self.GetInteractor()
        current_x, current_y = interactor.GetEventPosition()

        dx = current_x - self.last_x
        dy = current_y - self.last_y

        renderer = self.GetDefaultRenderer()
        camera = renderer.GetActiveCamera()

        step_size = 0.02  
        focal_point = list(camera.GetFocalPoint())

        focal_point[0] -= dx * step_size  
        focal_point[1] += dy * step_size  

        camera.SetFocalPoint(focal_point)

        self.last_x = current_x
        self.last_y = current_y

        interactor.GetRenderWindow().Render()  

class VisualizeGeometryWidget(TabWidget):
    def __init__(self, show_lopa=True, show_fuel_tanks=True, show_cargo_bays=True, start_interactor=True):
        super(VisualizeGeometryWidget, self).__init__()
        self._show_lopa        = show_lopa
        self._show_fuel_tanks  = show_fuel_tanks
        self._show_cargo_bays  = show_cargo_bays
        # Embedded previews should not start their own VTK event loop.
        self._start_interactor = start_interactor

        base_layout = QHBoxLayout()
        tree_layout = QVBoxLayout()
        main_layout = QVBoxLayout()
        graph_layout = QHBoxLayout()

        # self.label = QLabel("Click Display Button to View VTK")
        # main_layout.addWidget(self.label)

        self.render_window_interactor = None
        self.renderer = None
        self.get_camera = None
        self.pen_style = False

        self.wing_actors         = []
        self.fuselage_actors     = []
        self.nacelle_actors      = []
        self.propulsor_actors    = []
        self.boom_actors         = []
        self.fuel_tank_actors    = []
        self.cargo_bay_actors    = []
        self.landing_gear_actors = []
        self.cabin_actors        = []
        self.system_actors       = []
        # Keep learner annotations in their own actor group so scene refreshes
        # can remove lines, anchor dots, and text without touching geometry.
        self.learner_label_actors = []

        solve_button = QPushButton("Display")
        solve_button.clicked.connect(self.run_solve)

        self.tree = QTreeWidget()
        self.init_tree()
        tree_layout.addWidget(solve_button)
        tree_layout.addWidget(self.tree)

        # base_layout.addLayout(tree_layout, 3)
        base_layout.addLayout(main_layout)

        # add toolbar 
        main_layout.addWidget(self.add_toolbar())

        # Creating PyVista Qt widget
        self.plotter = QtInteractor(self)
        self.vtkWidget = self.plotter  # alias so feature files keep working

        self.colorbar_widget = None
        graph_layout.addWidget(self.colorbar())
        graph_layout.addWidget(self.plotter)

        graph_widget = QWidget()
        graph_widget.setLayout(graph_layout)
        main_layout.addWidget(graph_widget)

        base_widget = QWidget()
        base_widget.setLayout(base_layout)

        self.setLayout(base_layout)

        # Store selected option
        self.selected_option = None
        
    def colorbar(self):
        self.part_actors = {
            "Fuselages":    self.fuselage_actors,
            "Wings":        self.wing_actors,
            "Nacelles":     self.nacelle_actors,
            "Propulsors":   self.propulsor_actors,
            "Booms":        self.boom_actors,
            "Fuel Tanks":   self.fuel_tank_actors,
            "Cargo Bays":   self.cargo_bay_actors,
            "Landing Gear": self.landing_gear_actors,
            "Cabins":       self.cabin_actors,
            "Systems":      self.system_actors,
        }

        def color_changed(part_name, color=None, opacity=None):
            for actor in self.part_actors.get(part_name, []):
                temp = actor.GetProperty()
                if color:
                    temp.SetColor(color.redF(), color.greenF(), color.blueF())
                    temp.SetOpacity(color.alphaF())
                if opacity is not None:
                    temp.SetOpacity(opacity)
            self.vtkWidget.GetRenderWindow().Render()

        self.colorbar_widget = ColorBar(self.part_actors, color_changed)
        self.colorbar_widget.setFixedWidth(180)

        scroll = QScrollArea()
        scroll.setWidget(self.colorbar_widget)
        scroll.setWidgetResizable(False)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setFixedWidth(200)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.colorbar_scroll = scroll
        return scroll

    def add_toolbar(self):
        self.toolbar = QToolBar("Tools")

        current_dir = os.path.dirname(os.path.abspath(__file__))

        self.pan_button = QPushButton("Pan")
        self.pan_button.setToolTip("Pan Mode")

        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_in_button.setToolTip("Zoom In")

        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_out_button.setToolTip("Zoom Out")

        self.front_button = QPushButton("Front")
        self.front_button.setToolTip("Front")

        self.side_button = QPushButton("Side")
        self.side_button.setToolTip("Side")

        self.top_button = QPushButton("Top")
        self.top_button.setToolTip("Top")

        self.isometric_button = QPushButton("Isometric")
        self.isometric_button.setToolTip("Isometric")

        # Add buttons to toolbar
        self.toolbar.addWidget(self.pan_button)
        self.toolbar.addWidget(self.zoom_in_button)
        self.toolbar.addWidget(self.zoom_out_button)
        self.toolbar.addWidget(self.front_button)
        self.toolbar.addWidget(self.side_button)
        self.toolbar.addWidget(self.top_button)
        self.toolbar.addWidget(self.isometric_button)

        return self.toolbar
    
    def enable_pan_mode(self):
        if self.pen_style:
            custom_style = CustomInteractorStyle()
            self.render_window_interactor.SetInteractorStyle(custom_style)
            self.reset_camera_focus_to_center()
            self.pen_style = False
        else:
            pan_style = CustomPanInteractorStyle()
            pan_style.SetDefaultRenderer(self.renderer)
            self.render_window_interactor.SetInteractorStyle(pan_style)
            self.pen_style = True
        self.render_window_interactor.Initialize()
        self.render_window_interactor.Render()
    
    def reset_camera_focus_to_center(self):
        # Gets the boundaries of all objects in the scene
        bounds = self.renderer.ComputeVisiblePropBounds() 

        center_x = (bounds[0] + bounds[1]) / 2
        center_y = (bounds[2] + bounds[3]) / 2
        center_z = (bounds[4] + bounds[5]) / 2

        camera = self.renderer.GetActiveCamera()
        camera.SetFocalPoint(center_x, center_y, center_z) 

    def zoom_in(self):
        self.get_camera.Zoom(1.2) 
        self.vtkWidget.GetRenderWindow().Render()

    def zoom_out(self):
        self.get_camera.Zoom(0.8)  
        self.vtkWidget.GetRenderWindow().Render()

    def set_view_function(self, Postion, Videup): 
        self.get_camera.SetFocalPoint(0, 0, 0)
        self.get_camera.SetPosition(*Postion) 
        self.get_camera.SetViewUp(*Videup)
        self.renderer.ResetCamera() 
        self.get_camera.Zoom(1.5)  
        self.reset_camera_focus_to_center()
        self.vtkWidget.GetRenderWindow().Render()

    def front_function(self):
        bounds = self.renderer.ComputeVisiblePropBounds()
        self.set_view_function((-(bounds[1]-bounds[0])/2, 0, 0),(0, 0, 1))

    def side_function(self):
        bounds = self.renderer.ComputeVisiblePropBounds()
        self.set_view_function((0, -(bounds[3]-bounds[2]), 0),(0, 0, 1))

    def top_function(self):
        bounds = self.renderer.ComputeVisiblePropBounds()
        self.set_view_function((0, 0, (bounds[3]-bounds[2])),(0, 1, 0))
    
    def isometric_function(self):
        bounds = self.renderer.ComputeVisiblePropBounds()
        self.set_view_function((-bounds[5], -bounds[5], bounds[5]),(0, 0, 1))

    def init_tree(self):
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["Plot Options"])

        header = self.tree.header()
        assert header is not None
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)

        for category, options in self.plot_options.items():
            category_item = QTreeWidgetItem([category])
            self.tree.addTopLevelItem(category_item)
            for option in options:
                option_item = QTreeWidgetItem([option])
                category_item.addChild(option_item)

        # Connect signal for item selection
        self.tree.itemClicked.connect(self.on_item_clicked)

    def on_item_clicked(self, item, column):
        # Ensure only one selection at a time
        parent = item.parent()
        if parent:
            for i in range(parent.childCount()):
                parent.child(i).setSelected(False)
        item.setSelected(True)
        self.selected_option = item.text(0)       
     
    def run_solve(self):
        wing_color           = 'grey'
        fuselage_color       = 'grey'
        nacelle_color        = 'grey'
        propulsor_color      = 'grey'
        boom_color           = 'grey'
        fuel_tank_color      = 'orange'
        rotor_color          = 'black'
        cargo_bay_color      = 'blue'
        battery_color        = 'green'
        landing_gear_color   = 'grey'
        cabin_color          = 'grey'
        systems_color        = 'black'
        wing_opacity         = 0.5
        fuselage_opacity     = 0.5
        nacelle_opacity      = 0.5
        propulsor_opacity    = 0.5
        fuel_tank_opacity    = 0.5
        rotor_opacity        = 0.6
        boom_opacity         = 1.0
        cargo_bay_opacity    = 0.6
        battery_opacity      = 1.0
        landing_gear_opacity = 1.0
        cabin_opacity        = 0.75
        systems_opacity      = 0.8
        lopa_opacity         = 1.0
        number_of_airfoil_points = 101
        tessellation         = 96
        camera_eye_x         = -1
        camera_eye_y         = -1
        camera_eye_z         = 0.35

        fuel_tank_rgb_color    = mcolors.to_rgb(fuel_tank_color)
        wing_rgb_color         = mcolors.to_rgb(wing_color)
        fuselage_rgb_color     = mcolors.to_rgb(fuselage_color)
        nacelle_rgb_color      = mcolors.to_rgb(nacelle_color)
        propulsor_rgb_color    = mcolors.to_rgb(propulsor_color)
        rotor_rgb_color        = mcolors.to_rgb(rotor_color)
        boom_rgb_color         = mcolors.to_rgb(boom_color)
        cargo_bay_rgb_color    = mcolors.to_rgb(cargo_bay_color)
        battery_rgb_color      = mcolors.to_rgb(battery_color)
        landing_gear_rgb_color = mcolors.to_rgb(landing_gear_color)
        cabin_rgb_color        = mcolors.to_rgb(cabin_color)
        system_rgb_color       = mcolors.to_rgb(systems_color)

        # Clear previous scene and actor lists
        if self.renderer is not None:
            self.renderer.RemoveAllViewProps()
        self.wing_actors.clear()
        self.fuselage_actors.clear()
        self.nacelle_actors.clear()
        self.propulsor_actors.clear()
        self.propulsor_actors.clear()
        self.boom_actors.clear()
        self.fuel_tank_actors.clear()
        self.cargo_bay_actors.clear()
        self.landing_gear_actors.clear()
        self.cabin_actors.clear()
        self.system_actors.clear()
        # Remove stale references before rebuilding learner callouts for the
        # newly displayed vehicle.
        self.learner_label_actors.clear()

        self.renderer = self.plotter.renderer
        self.render_window_interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

        # Number of points for airfoil
        geometry =  deepcopy(rcaide_io.vehicle)

        # -------------------------------------------------------------------------
        # Run Geoemtry Analysis Functions
        # -------------------------------------------------------------------------
        for wing in geometry.wings:
            if isinstance(wing, RCAIDE.Library.Components.Wings.Blended_Wing_Body):
                wing_planform(wing)
                if len(wing.cabins) > 0:
                    compute_layout_of_passenger_accommodations(wing)
            else:
                wing_planform(wing)

        if self._show_fuel_tanks:
            compute_fuel_volume(geometry)

        for fuselage in geometry.fuselages:
            if len(fuselage.cabins) > 0:
                compute_layout_of_passenger_accommodations(fuselage)
            fuselage_planform(fuselage)
    
        # -------------------------------------------------------------------------  
        # Plot wings
        # -------------------------------------------------------------------------
        for wing in geometry.wings:
            GEOM = generate_3d_wing_points(wing, number_of_airfoil_points, plot_centerline=False)
            make_object(self.plotter, self.wing_actors, GEOM, wing_rgb_color, wing_opacity)
            if wing.yz_plane_symmetric:
                GEOM.PTS[:, :, 0] = -GEOM.PTS[:, :, 0]
                make_object(self.plotter, self.wing_actors, GEOM, wing_rgb_color, wing_opacity)
            if wing.xz_plane_symmetric:
                GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                make_object(self.plotter, self.wing_actors, GEOM, wing_rgb_color, wing_opacity)
            if wing.xy_plane_symmetric:
                GEOM.PTS[:, :, 2] = -GEOM.PTS[:, :, 2]
                make_object(self.plotter, self.wing_actors, GEOM, wing_rgb_color, wing_opacity)
            if isinstance(wing, RCAIDE.Library.Components.Wings.Blended_Wing_Body):
                if self._show_lopa:
                    if len(wing.cabins) > 0 and len(list(wing.cabins.values())[0].segments_bounding_cabin) > 1:
                        lopa_geom = generate_3d_lopa_points(wing)
                        add_lopa_seats(self.plotter, lopa_geom, lopa_opacity)
                if len(wing.cabins) > 0:
                    GEOM = generate_3d_cabin_points(wing, number_of_airfoil_points, plot_centerline=False)
                    make_object(self.plotter, self.cabin_actors, GEOM, cabin_rgb_color, cabin_opacity)
                    GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                    make_object(self.plotter, self.cabin_actors, GEOM, cabin_rgb_color, cabin_opacity)

        # -------------------------------------------------------------------------
        # Plot fuselage
        # -------------------------------------------------------------------------
        for fuselage in geometry.fuselages:
            # Unlike RCAIDE's segmented-only generator, this wrapper also
            # creates a smooth fallback body for learner fuselages with no
            # cross-section stations.
            GEOM = generate_fuselage_points_for_viewer(fuselage, tessellation)
            make_object(self.plotter, self.fuselage_actors, GEOM, fuselage_rgb_color, fuselage_opacity)
            if len(fuselage.cabins) > 0 and len(list(fuselage.cabins.values())[0].segments_bounding_cabin) > 1:
                GEOM = generate_3d_cabin_points(fuselage, number_of_airfoil_points, plot_centerline=False)
                make_object(self.plotter, self.cabin_actors, GEOM, cabin_rgb_color, cabin_opacity)
            if self._show_lopa:
                lopa_geom = generate_3d_lopa_points(fuselage)
                add_lopa_seats(self.plotter, lopa_geom, lopa_opacity)

        # -------------------------------------------------------------------------
        # Plot cargo bays
        # -------------------------------------------------------------------------
        if self._show_cargo_bays:
            for cargo_bay in geometry.cargo_bays:
                GEOM = generate_3d_cargo_bay_points(cargo_bay)
                make_object(self.plotter, self.cargo_bay_actors, GEOM, cargo_bay_rgb_color, cargo_bay_opacity)

        # -------------------------------------------------------------------------
        # Plot boom
        # -------------------------------------------------------------------------
        for boom in geometry.booms:
            GEOM = generate_3d_fuselage_points(boom, tessellation)
            make_object(self.plotter, self.boom_actors, GEOM, boom_rgb_color, boom_opacity)
    
        # -------------------------------------------------------------------------
        # Plot systems — check both vehicle-level and per-network containers
        # -------------------------------------------------------------------------
        _all_systems = list(geometry.systems) + [s for net in geometry.networks for s in net.systems]
        for system in _all_systems:
            if isinstance(system, Component):
                GEOM = generate_3d_cuboid_points(system)
                make_object(self.plotter, self.system_actors, GEOM, system_rgb_color, systems_opacity)

        # -------------------------------------------------------------------------
        # Plot landing gear
        # -------------------------------------------------------------------------
        for landing_gear in geometry.landing_gears:
            N_t = landing_gear.number_of_gear_types_in_tandem
            N_w = landing_gear.number_of_wheels_in_gear_type
            D            = landing_gear.tire_diameter
            d            = landing_gear.rim_diameter
            w            = landing_gear.tire_width
            strut_length = landing_gear.strut_length
            gear_origin  = landing_gear.origin[0]

            longitudinal_spacing = landing_gear.longitudinal_wheel_spacing * (N_t - 1) if N_t > 1 else 0
            total_wheel_x_span   = D * (N_t - 1) + longitudinal_spacing
            wheel_x_offsets      = np.linspace(-total_wheel_x_span / 2, total_wheel_x_span / 2, N_t) if N_t > 1 else np.array([0.0])

            total_wheel_y_span   = w * (N_w - 1) + landing_gear.lateral_wheel_spacing * (N_w - 1) if N_w > 1 else 0
            wheel_y_offsets      = np.linspace(-total_wheel_y_span / 2, total_wheel_y_span / 2, N_w) if N_w > 1 else np.array([0.0])

            for i in range(N_t):
                for j in range(N_w):
                    wheel_origin = [
                        gear_origin[0] + wheel_x_offsets[i],
                        gear_origin[1] + wheel_y_offsets[j],
                        gear_origin[2] - strut_length,
                    ]
                    pts = generate_3d_torus_points(wheel_origin, D, d, w, tessellation=24)
                    make_pts_object(self.plotter, self.landing_gear_actors, pts, landing_gear_rgb_color, landing_gear_opacity)
                    if landing_gear.xz_plane_symmetric:
                        wheel_origin[1] = -wheel_origin[1]
                        pts = generate_3d_torus_points(wheel_origin, D, d, w, tessellation=24)
                        make_pts_object(self.plotter, self.landing_gear_actors, pts, landing_gear_rgb_color, landing_gear_opacity)

        # -------------------------------------------------------------------------
        # Plot top-level nacelles (not attached to a propulsor)
        # -------------------------------------------------------------------------
        for nacelle in geometry.nacelles:
            if type(nacelle) == RCAIDE.Library.Components.Nacelles.Stack_Nacelle:
                GEOM = generate_3d_stack_nacelle_points(nacelle, tessellation=tessellation, number_of_airfoil_points=number_of_airfoil_points)
            elif type(nacelle) == RCAIDE.Library.Components.Nacelles.Body_of_Revolution_Nacelle:
                GEOM = generate_3d_BOR_nacelle_points(nacelle, tessellation=tessellation, number_of_airfoil_points=number_of_airfoil_points)
            else:
                GEOM = generate_3d_basic_nacelle_points(nacelle, tessellation=tessellation, number_of_airfoil_points=number_of_airfoil_points)
            make_object(self.plotter, self.nacelle_actors, GEOM, nacelle_rgb_color, nacelle_opacity)

        # -------------------------------------------------------------------------
        # Plot Nacelles, Rotors and Fuel Tanks (network-attached)
        # -------------------------------------------------------------------------
        for network in geometry.networks:
            for propulsor in network.propulsors:   

                if isinstance(propulsor, (RCAIDE.Library.Components.Powertrain.Propulsors.Turbofan,
                                        RCAIDE.Library.Components.Powertrain.Propulsors.Turbojet,
                                        RCAIDE.Library.Components.Powertrain.Propulsors.Turboprop)):
                    try:
                        if propulsor.length > 0 and propulsor.diameter > 0:
                            GEOM = generate_3d_propulsor_points(propulsor, tessellation)
                            make_object(self.plotter, self.propulsor_actors, GEOM, propulsor_rgb_color, propulsor_opacity)
                    except Exception:
                        pass

                if getattr(propulsor, "nacelle", None) is not None: 
                    if propulsor.nacelle !=  None: 
                        
                        if type(propulsor.nacelle) == RCAIDE.Library.Components.Nacelles.Stack_Nacelle: 
                            GEOM = generate_3d_stack_nacelle_points(propulsor.nacelle,tessellation = tessellation,number_of_airfoil_points = number_of_airfoil_points)
                        elif type(propulsor.nacelle) == RCAIDE.Library.Components.Nacelles.Body_of_Revolution_Nacelle: 
                            GEOM = generate_3d_BOR_nacelle_points(propulsor.nacelle,tessellation = tessellation,number_of_airfoil_points = number_of_airfoil_points)
                        else:
                            GEOM= generate_3d_basic_nacelle_points(propulsor.nacelle,tessellation = tessellation,number_of_airfoil_points = number_of_airfoil_points)
                        make_object(self.plotter,self.nacelle_actors,  GEOM, nacelle_rgb_color,nacelle_opacity)
                        
                if 'rotor' in propulsor:
                    rot   = propulsor.rotor
                    rot_x = rot.orientation_euler_angles[0]
                    rot_y = rot.orientation_euler_angles[1]
                    rot_z = rot.orientation_euler_angles[2]
                    num_B = int(rot.number_of_blades)
                    if rot.radius_distribution is None:
                        make_actuator_disc(self.plotter, rot.hub_radius, rot.tip_radius, rot.origin, rot_x, rot_y, rot_z, rotor_rgb_color, rotor_opacity)
                    else:
                        rot_y += np.pi / 2
                        dim = len(rot.radius_distribution)
                        for i in range(num_B):
                            GEOM = generate_3d_blade_points(rot, number_of_airfoil_points, dim, i)
                            make_object(self.plotter, self.propulsor_actors, GEOM, rotor_rgb_color, rotor_opacity)

                if 'propeller' in propulsor:
                    prop  = propulsor.propeller
                    rot_x = prop.orientation_euler_angles[0]
                    rot_y = prop.orientation_euler_angles[1]
                    rot_z = prop.orientation_euler_angles[2]
                    num_B = int(prop.number_of_blades)
                    if prop.radius_distribution is None:
                        make_actuator_disc(self.plotter, prop.hub_radius, prop.tip_radius, prop.origin, rot_x, rot_y, rot_z, rotor_rgb_color, rotor_opacity)
                    else:
                        dim = len(prop.radius_distribution)
                        for i in range(num_B):
                            GEOM = generate_3d_blade_points(prop, number_of_airfoil_points, dim, i)
                            make_object(self.plotter, self.propulsor_actors, GEOM, rotor_rgb_color, rotor_opacity)
    
            if self._show_fuel_tanks:
                _Cryo        = RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Cryogenic_Tank
                _NonIntegral = RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Non_Integral_Tank
                _Integral    = RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Integral_Tank
                for fuel_line in network.fuel_lines:
                    for fuel_tank in fuel_line.fuel_tanks:
                        if fuel_tank.wing_tag is not None:
                            wing = geometry.wings[fuel_tank.wing_tag]

                            if issubclass(type(fuel_tank), _NonIntegral):
                                if issubclass(type(fuel_tank), _Cryo) and getattr(fuel_tank, 'geometry_type', None) == 'conformal' and getattr(fuel_tank, 'transverse_tank', False):
                                    seg_bounds = fuel_tank.transverse_tank_chord_bounds
                                    GEOM = generate_aft_integral_wing_tank_points(wing, 5, seg_bounds, fuel_tank)
                                    make_object(self.plotter, self.fuel_tank_actors, GEOM, fuel_tank_rgb_color, fuel_tank_opacity)
                                elif issubclass(type(fuel_tank), _Cryo) and getattr(fuel_tank, 'geometry_type', None) == 'conformal':
                                    seg_bounds = fuel_tank.segments_bounding_tank
                                    GEOM = generate_integral_wing_tank_points(wing, number_of_airfoil_points, seg_bounds, fuel_tank)
                                    make_object(self.plotter, self.fuel_tank_actors, GEOM, fuel_tank_rgb_color, fuel_tank_opacity)
                                    if wing.xz_plane_symmetric:
                                        GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                                        make_object(self.plotter, self.fuel_tank_actors, GEOM, fuel_tank_rgb_color, fuel_tank_opacity)
                                else:
                                    GEOM = generate_non_integral_fuel_tank_points(fuel_tank, tessellation)
                                    make_object(self.plotter, self.fuel_tank_actors, GEOM, fuel_tank_rgb_color, fuel_tank_opacity)
                                    if wing.xz_plane_symmetric:
                                        GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                                        make_object(self.plotter, self.fuel_tank_actors, GEOM, fuel_tank_rgb_color, fuel_tank_opacity)

                            if type(fuel_tank) == _Integral:
                                seg_bounds = fuel_tank.segments_bounding_tank
                                GEOM = generate_integral_wing_tank_points(wing, number_of_airfoil_points, seg_bounds, fuel_tank, plot_centerline=False)
                                make_object(self.plotter, self.fuel_tank_actors, GEOM, fuel_tank_rgb_color, fuel_tank_opacity)
                                if wing.xz_plane_symmetric:
                                    GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                                    make_object(self.plotter, self.fuel_tank_actors, GEOM, fuel_tank_rgb_color, fuel_tank_opacity)

                        elif fuel_tank.fuselage_tag is not None:
                            fuselage = geometry.fuselages[fuel_tank.fuselage_tag]
                            if type(fuel_tank) == _Integral:
                                seg_bounds = fuel_tank.segments_bounding_tank
                                GEOM = generate_integral_fuel_tank_points(fuselage, fuel_tank, seg_bounds, tessellation)
                                make_object(self.plotter, self.fuel_tank_actors, GEOM, fuel_tank_rgb_color, fuel_tank_opacity)

                        elif issubclass(type(fuel_tank), _NonIntegral):
                            GEOM = generate_non_integral_fuel_tank_points(fuel_tank, tessellation)
                            make_object(self.plotter, self.fuel_tank_actors, GEOM, fuel_tank_rgb_color, fuel_tank_opacity)

            for bus in network.busses:
                for battery in bus.battery_modules:
                    GEOM = generate_3d_cuboid_points(battery)
                    make_object(self.plotter, self.system_actors, GEOM, battery_rgb_color, battery_opacity)

        # learner_component_callout_data returns an empty list for non-learner
        # vehicles.  This keeps the shared Visualize Geometry tab unchanged and
        # uncluttered in Advanced Mode.
        callouts = learner_component_callout_data(geometry)
        if callouts:
            add_learner_component_callouts(
                self.plotter,
                self.renderer,
                self.learner_label_actors,
                callouts,
            )

        # Set camera and background
        cam = self.renderer.GetActiveCamera()
        cam.SetPosition(camera_eye_x, camera_eye_y, camera_eye_z)
        cam.SetFocalPoint(0, 0, 0)
        cam.SetViewUp(0, 0, 1)
        self.renderer.ResetCamera()
        self.renderer.SetBackground(1.0, 1.0, 1.0)

        # Use the custom interactor style
        custom_style = CustomInteractorStyle()
        self.render_window_interactor.SetInteractorStyle(custom_style)

        # self.vtkWidget.show()
        # Start the VTK interactor
        self.render_window_interactor.Initialize()
        # Skip Start() for embedded previews.
        # Full visualization starts VTK; embedded previews only render.
        if self._start_interactor:
            self.render_window_interactor.Start()
        self.get_camera=self.renderer.GetActiveCamera()
        self.update_toolbar()
        if rcaide_io.vehicle.wings:
            self.colorbar_widget.update_parts(self.part_actors)
        self.isometric_function()

    def update_toolbar(self):
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.pan_button.clicked.connect(self.enable_pan_mode)
        self.front_button.clicked.connect(self.front_function)
        self.top_button.clicked.connect(self.top_function)
        self.side_button.clicked.connect(self.side_function)
        self.isometric_button.clicked.connect(self.isometric_function)        
        
    def update_layout(self):
        self.run_solve()

    plot_options = {
        "Pre Built": [
            "Concorde",
        ],
    }
def get_widget() -> QWidget:
    return VisualizeGeometryWidget()

def _add_mesh(plotter, actor_group, mesh, rgb_color, opacity):
    bright = tuple(min(1.0, c * 1.2) for c in rgb_color)
    actor = plotter.add_mesh(mesh, color=bright, opacity=opacity,
                             show_scalar_bar=False, smooth_shading=True)
    prop = actor.GetProperty()
    prop.SetDiffuse(0.8)
    prop.SetAmbient(0.4)
    prop.SetSpecular(0.3)
    prop.SetSpecularPower(20)
    actor_group.append(actor)
    return

def make_object(plotter, actor_group, GEOM, rgb_color, opacity):
    _add_mesh(plotter, actor_group, generate_vtk_object(GEOM.PTS), rgb_color, opacity)

def make_pts_object(plotter, actor_group, pts, rgb_color, opacity):
    _add_mesh(plotter, actor_group, generate_vtk_object(pts), rgb_color, opacity)

def make_actuator_disc(plotter, inner_radius, outer_radius, origin, rot_x, rot_y, rot_z, rgb_color, opacity):
    disc = pv.Disc(
        center=(0, 0, 0),
        normal=(1, 0, 0),
        inner=inner_radius,
        outer=outer_radius,
        r_res=50,
        c_res=50,
    )
    disc.rotate_x(rot_x / Units.degrees, inplace=True)
    disc.rotate_y(rot_y / Units.degrees, inplace=True)
    disc.rotate_z(rot_z / Units.degrees, inplace=True)
    disc.translate([origin[0][0], origin[0][1], origin[0][2]], inplace=True)

    actor = plotter.add_mesh(disc, color=rgb_color, opacity=opacity, show_scalar_bar=False)
    prop = actor.GetProperty()
    prop.SetDiffuse(1.0)
    prop.SetSpecular(0.0)
    return


def add_learner_component_callouts(plotter, renderer, actor_group, callouts):
    """Add world-space learner labels that remain attached during camera motion.

    Every callout creates three VTK props: a leader line, a small anchor sphere,
    and billboard text.  All three are appended to ``actor_group`` so the caller
    can clear or translate the complete annotation as one managed set.
    """
    for callout in callouts:
        # Both points are stored in aircraft coordinates, so camera rotation,
        # pan, zoom, and whole-aircraft dragging transform the line naturally.
        anchor = np.asarray(callout["anchor"], dtype=float)
        label_position = np.asarray(callout["label_position"], dtype=float)
        callout_length = float(np.linalg.norm(label_position - anchor))

        # The leader is decorative rather than interactive and does not trigger
        # a camera reset or an intermediate render while the scene is assembled.
        line_actor = plotter.add_mesh(
            pv.Line(anchor, label_position),
            color="black",
            line_width=2.0,
            render_lines_as_tubes=True,
            lighting=False,
            pickable=False,
            show_scalar_bar=False,
            reset_camera=False,
            render=False,
        )
        actor_group.append(line_actor)

        # Scale the attachment dot with callout length while retaining a minimum
        # visible size for compact learner aircraft.
        anchor_actor = plotter.add_mesh(
            pv.Sphere(radius=max(0.018, callout_length * 0.018), center=anchor),
            color="black",
            lighting=False,
            pickable=False,
            show_scalar_bar=False,
            reset_camera=False,
            render=False,
        )
        actor_group.append(anchor_actor)

        # Billboard text always faces the camera but keeps its world position,
        # making the label readable without detaching it from the aircraft.
        text_actor = vtkBillboardTextActor3D()
        text_actor.SetInput(str(callout["text"]))
        text_actor.SetPosition(*label_position)
        text_property = text_actor.GetTextProperty()
        text_property.SetColor(1.0, 0.84, 0.0)
        text_property.SetFontSize(15)
        text_property.SetFontFamilyToArial()
        text_property.SetBold(False)
        text_property.SetItalic(False)
        text_property.SetShadow(False)
        # Yellow, background-free text matches the requested learner label style
        # and avoids opaque boxes covering the model.
        text_property.SetBackgroundOpacity(0.0)
        renderer.AddActor(text_actor)
        actor_group.append(text_actor)

# ---------------------------------------
# Load Visualize Geometry feature plugins
# ---------------------------------------

from tabs.visualize_geometry.features import camera
from tabs.visualize_geometry.features import grid
from tabs.visualize_geometry.features import axes_gizmo
from tabs.visualize_geometry.features import background
from tabs.visualize_geometry.features import blueprint
from tabs.visualize_geometry.features import measurement
from tabs.visualize_geometry.features import screenshot
from tabs.visualize_geometry.features import drag_aircraft
