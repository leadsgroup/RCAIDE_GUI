import RCAIDE
from RCAIDE.Framework.Core import Units
from RCAIDE.Library.Plots.Geometry.generate_3d_wing_points      import *
from RCAIDE.Library.Plots.Geometry.generate_3d_fuselage_points  import *
from RCAIDE.Library.Plots.Geometry.generate_3d_fuel_tank_points import *
from RCAIDE.Library.Plots.Geometry.plot_3d_rotor                import generate_3d_blade_points
from RCAIDE.Library.Plots.Geometry.generate_3d_nacelle_points   import *
from RCAIDE.Library.Methods.Geometry.Planform                   import  fuselage_planform, wing_planform, bwb_wing_planform , compute_fuel_volume  
from RCAIDE.Library.Methods.Geometry.LOPA                       import  compute_layout_of_passenger_accommodations 
 
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QHeaderView, QLabel, QToolBar, QColorDialog, QSpacerItem, QSizePolicy, QFrame, QLineEdit
from PyQt6.QtCore import Qt
from tabs import TabWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from tabs.visualize_geometry import vehicle
from PyQt6.QtGui import QIcon

import matplotlib.colors as mcolors 
import vtk
import values
import os
from copy import deepcopy 

class CustomInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
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
            title.setStyleSheet("font-size: 11pt;")
            self.layout.addWidget(title)

            # Set Transparency
            opacity_row = QHBoxLayout()
            opacity_label = QLabel("Transparency:")
            opacity_label.setStyleSheet("font-size: 9pt;")
            opacity_input = QLineEdit("1.00")
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
            color_label.setStyleSheet("color: white; font-size: 9pt;")
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
                # Reset to default value
                controls["opacity_input"].setText("1.00")
                if part_name == "Fuselage":
                    controls["color_buttom"].setStyleSheet("background-color: #648eee; border: 1px solid #888;")
                else:
                    controls["color_buttom"].setStyleSheet("background-color: #d3d3d3; border: 1px solid #888;")

class CustomPanInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
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
    def __init__(self):
        super(VisualizeGeometryWidget, self).__init__()

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

        self.wing_actors = []
        self.fuselage_actors = []
        self.nacelle_actors = [] 
        self.rotor_actors  = []
        self.boom_actors = []
        self.fuel_tank_actors = []     

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

        # Creating VTK widget container
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        # self.vtkWidget.setStyleSheet("background-color: darkgrey;")  # Set the background color
        
        self.colorbar_widget = None
        graph_layout.addWidget(self.colorbar())
        graph_layout.addWidget(self.vtkWidget)

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
            "Fuselages": self.fuselage_actors,
            "Wings": self.wing_actors,
            "Nacelles": self.nacelle_actors, 
            "Rotors": self.rotor_actors, 
            "Booms": self.boom_actors, 
            "Fuel Tanks": self.fuel_tank_actors, 
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
        return self.colorbar_widget

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

        wing_color                  = 'grey'  
        fuselage_color              = 'grey'  
        nacelle_color               = 'grey' 
        boom_color                  = 'grey' 
        fuel_tank_color             = 'orange'  
        rotor_color                 = 'black'      
        wing_opacity                = 0.5  
        fuselage_opacity            = 0.5 
        nacelle_opacity             = 1.0 
        fuel_tank_opacity           = 0.5 
        rotor_opacity               = 1.0  
        number_of_airfoil_points    = 101 
        tessellation                = 96 
        boom_opacity                = 1.0
        camera_eye_x  = -1 
        camera_eye_y  = -1 
        camera_eye_z  = 0.35  
        
        fuel_tank_rgb_color         = mcolors.to_rgb(fuel_tank_color)     
        wing_rgb_color              = mcolors.to_rgb(wing_color)
        fuselage_rgb_color          = mcolors.to_rgb(fuselage_color) 
        nacelle_rgb_color           = mcolors.to_rgb(nacelle_color) 
        rotor_rgb_color             = mcolors.to_rgb(rotor_color)
        boom_rgb_color              = mcolors.to_rgb(boom_color)
        
        
        self.renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.render_window_interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

        # Number of points for airfoil
        geometry =  deepcopy(values.vehicle)
        
        # -------------------------------------------------------------------------
        # Run Geoemtry Analysis Functions
        # -------------------------------------------------------------------------   
        for wing in geometry.wings:  
            if isinstance(wing, RCAIDE.Library.Components.Wings.Blended_Wing_Body): 
                bwb_wing_planform(wing) 
            else: 
                wing_planform(wing)  
                         
        compute_fuel_volume(geometry)

        for fuselage in  geometry.fuselages:               
            compute_layout_of_passenger_accommodations(fuselage)
            fuselage_planform(fuselage) 
    
        # -------------------------------------------------------------------------  
        # Plot wings
        # -------------------------------------------------------------------------
    
        for wing in geometry.wings:
            n_segments = len(wing.segments)
            dim        = n_segments if n_segments > 0 else 2
            GEOM       = generate_3d_wing_points(wing, number_of_airfoil_points, dim)
            make_object(self.renderer,self.wing_actors, GEOM,wing_rgb_color,wing_opacity)
            if wing.yz_plane_symmetric: 
                GEOM.PTS[:, :, 0] = -GEOM.PTS[:, :, 0]
                make_object(self.renderer, self.wing_actors,GEOM,wing_rgb_color,wing_opacity)
            if wing.xz_plane_symmetric: 
                GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                make_object(self.renderer,self.wing_actors, GEOM,wing_rgb_color,wing_opacity)
            if wing.xy_plane_symmetric: 
                GEOM.PTS[:, :, 2] = -GEOM.PTS[:, :, 2]
                make_object(self.renderer,self.wing_actors, GEOM,wing_rgb_color,wing_opacity)
    
        # -------------------------------------------------------------------------  
        # Plot fuselage
        # -------------------------------------------------------------------------  
        for fuselage in geometry.fuselages:
            GEOM = generate_3d_fuselage_points(fuselage, tessellation)
            make_object(self.renderer, self.fuselage_actors,GEOM, fuselage_rgb_color,fuselage_opacity)
            
        # -------------------------------------------------------------------------  
        # Plot boom
        # -------------------------------------------------------------------------  
        for boom in geometry.booms:
            GEOM = generate_3d_fuselage_points(boom, tessellation)
            make_object(self.renderer, self.boom_actors, GEOM, boom_rgb_color,boom_opacity)
    
        # -------------------------------------------------------------------------  
        # Plot Nacelle, Rotors and Fuel Tanks 
        # ------------------------------------------------------------------------- 
        for network in geometry.networks:     
            for propulsor in network.propulsors: 
                if 'nacelle' in propulsor: 
                    if propulsor.nacelle !=  None: 
                        if type(propulsor.nacelle) == RCAIDE.Library.Components.Nacelles.Stack_Nacelle: 
                            GEOM = generate_3d_stack_nacelle_points(propulsor.nacelle,tessellation = tessellation,number_of_airfoil_points = number_of_airfoil_points)
                        elif type(propulsor.nacelle) == RCAIDE.Library.Components.Nacelles.Body_of_Revolution_Nacelle: 
                            GEOM = generate_3d_BOR_nacelle_points(propulsor.nacelle,tessellation = tessellation,number_of_airfoil_points = number_of_airfoil_points)
                        else:
                            GEOM= generate_3d_basic_nacelle_points(propulsor.nacelle,tessellation = tessellation,number_of_airfoil_points = number_of_airfoil_points)
                        make_object(self.renderer,self.nacelle_actors,  GEOM, nacelle_rgb_color,nacelle_opacity)
                        
                if 'rotor' in propulsor:  
                    rot       = propulsor.rotor
                    rot_x     = rot.orientation_euler_angles[0]
                    rot_y     = rot.orientation_euler_angles[1]
                    rot_z     = rot.orientation_euler_angles[2]
                    num_B     = int(rot.number_of_blades) 
                    if rot.radius_distribution is None:
                        make_actuator_disc(self.renderer, rot.hub_radius, rot.tip_radius, rot.origin, rot_x,rot_y,rot_z, rotor_rgb_color,rotor_opacity) 
                    else:
                        dim       = len(rot.radius_distribution) 
                        for i in range(num_B):
                            GEOM = generate_3d_blade_points(rot,number_of_airfoil_points,dim,i)
                            make_object(self.renderer,self.rotor_actors,  GEOM, rotor_rgb_color,rotor_opacity) 
    
                if 'propeller' in propulsor:
                    prop      = propulsor.propeller
                    rot_x     = prop.orientation_euler_angles[0]
                    rot_y     = np.pi / 2 +  prop.orientation_euler_angles[1]
                    rot_z     = prop.orientation_euler_angles[2]
                    num_B     = int(prop.number_of_blades) 
                    if prop.radius_distribution is None:
                        make_actuator_disc(self.renderer, prop.hub_radius, prop.tip_radius, prop.origin, rot_x,rot_y,rot_z,rotor_rgb_color,rotor_opacity) 
                    else:
                        dim       = len(prop.radius_distribution)
                        for i in range(num_B):
                            GEOM = generate_3d_blade_points(prop,number_of_airfoil_points,dim,i) 
                            make_object(self.renderer,self.rotor_actors, GEOM, rotor_rgb_color,rotor_opacity) 
    
            for fuel_line in network.fuel_lines:        
                for fuel_tank in fuel_line.fuel_tanks:   
                    if fuel_tank.wing_tag != None:
                        wing = geometry.wings[fuel_tank.wing_tag]
                        
                        if issubclass(type(fuel_tank), RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Non_Integral_Tank):
                            GEOM  = generate_non_integral_fuel_tank_points(fuel_tank,tessellation ) 
                            make_object(self.renderer,self.fuel_tank_actors, GEOM,  fuel_tank_rgb_color, fuel_tank_opacity) 
        
                            if wing.xz_plane_symmetric: 
                                GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1] 
                                make_object(self.renderer,self.fuel_tank_actors, GEOM,  fuel_tank_rgb_color, fuel_tank_opacity)
                            
                        if type(fuel_tank) == RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Integral_Tank: 
                            segment_list = [] 
                            segment_tags = list(wing.segments.keys())     
                            for i in range(len(wing.segments) - 1):
                                seg =  wing.segments[segment_tags[i]]
                                next_seg =  wing.segments[segment_tags[i+1]]
                                if seg.has_fuel_tank:
                                    if seg.tag not in segment_list:
                                        segment_list.append(seg.tag)
                                    if next_seg.tag not in segment_list:
                                        segment_list.append(next_seg.tag) 
    
                            if len(wing.segments)>0:
                                dim =  len(segment_list)
                            else:
                                dim = 2 
    
                            if  len(segment_list) == 0 and len(wing.segments) > 0:
                                raise AttributeError('Fuel tank defined on segmented wing but no segments have "tank" attribute = True') 
                            else:   
                                GEOM = generate_integral_wing_tank_points(wing,5,dim,segment_list)
                                make_object(self.renderer, self.fuel_tank_actors,GEOM, fuel_tank_rgb_color, fuel_tank_opacity)  
                                if wing.xz_plane_symmetric:
                                    GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1] 
                                    make_object(self.renderer,self.fuel_tank_actors, GEOM,fuel_tank_rgb_color, fuel_tank_opacity) 
    
                    elif fuel_tank.fuselage_tag != None:
                        fuselage = geometry.fuselages[fuel_tank.fuselage_tag]
                        if type(fuel_tank) == RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Integral_Tank:  
                            segment_list = [] 
                            segment_tags = list(fuselage.segments.keys())     
                            for i in range(len(fuselage.segments) - 1):
                                seg =  fuselage.segments[segment_tags[i]]
                                next_seg =  fuselage.segments[segment_tags[i+1]]
                                if seg.has_fuel_tank: 
                                    segment_list.append(seg.tag)
                                    if next_seg.tag not in segment_list:
                                        segment_list.append(next_seg.tag)  
    
                            GEOM  = generate_integral_fuel_tank_points(fuselage,fuel_tank, segment_list,tessellation )
                            make_object(self.renderer,self.fuel_tank_actors, GEOM,  fuel_tank_rgb_color, fuel_tank_opacity) 
    
                    elif issubclass(type(fuel_tank), RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Non_Integral_Tank):
                        GEOM  = generate_non_integral_fuel_tank_points(fuel_tank,tessellation ) 
                        make_object(self.renderer,self.fuel_tank_actors, GEOM,  fuel_tank_rgb_color, fuel_tank_opacity) 
    
                        if wing.xz_plane_symmetric: 
                            GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1] 
                            make_object(self.renderer, self.fuel_tank_actors, GEOM,  fuel_tank_rgb_color, fuel_tank_opacity)         
                        
        # Set camera and background
        camera = vtk.vtkCamera()
        camera.SetPosition(camera_eye_x, camera_eye_y, camera_eye_z)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 0, 1)

        self.renderer.SetActiveCamera(camera)
        self.renderer.ResetCamera()
        self.renderer.SetBackground(1.0, 1.0, 1.0)  # Background color

        # Use the custom interactor style
        custom_style = CustomInteractorStyle()
        self.render_window_interactor.SetInteractorStyle(custom_style)

        # Start the VTK interactor
        self.render_window_interactor.Initialize()
        self.render_window_interactor.Start()
        self.get_camera=self.renderer.GetActiveCamera()
        self.update_toolbar()
        if values.vehicle.wings:
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

def make_object(renderer, actor_group,  GEOM,  rgb_color, opacity): 

    actor = vehicle.generate_vtk_object(GEOM.PTS)

    # Set color of fuselage
    mapper = actor.GetMapper()
    mapper.ScalarVisibilityOff()
    prop = actor.GetProperty()
    prop.SetColor(rgb_color[0] * 1.2, rgb_color[1] * 1.2, rgb_color[2] * 1.2)  # slightly brighter
    prop.SetDiffuse(0.8)
    prop.SetAmbient(0.4)      # adds base light even in dark areas
    prop.SetSpecular(0.3)     # gives a soft highlight
    prop.SetSpecularPower(20)
    prop.SetOpacity(opacity)
    renderer.AddActor(actor)
    actor_group.append(actor) 
    return

def make_actuator_disc(renderer, inner_radius, outer_radius, origin, rot_x,rot_y,rot_z, rgb_color, opacity): 
    
    disk_source = vtk.vtkDiskSource()
    disk_source.SetInnerRadius(inner_radius)
    disk_source.SetOuterRadius(outer_radius)
    disk_source.SetRadialResolution(50)
    disk_source.SetCircumferentialResolution(50) 
    
    # 2. Define a rotation using vtkTransform
    transform = vtk.vtkTransform()
    transform.RotateX(rot_x/Units.degrees)  
    transform.RotateY(rot_y/Units.degrees)  
    transform.RotateZ(rot_z/Units.degrees)  

    # 3. Apply the transformation with vtkTransformPolyDataFilter
    transformFilter = vtk.vtkTransformPolyDataFilter()
    transformFilter.SetTransform(transform)
    transformFilter.SetInputConnection(disk_source.GetOutputPort()) 
  
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(transformFilter.GetOutputPort())
    
    actor = vtk.vtkActor()
    actor.SetMapper(mapper) 
    actor.GetProperty().SetColor(rgb_color[0], rgb_color[1], rgb_color[2])  
    actor.GetProperty().SetDiffuse(1.0)  
    actor.GetProperty().SetSpecular(0.0) 
    actor.GetProperty().SetOpacity(opacity)
    actor.SetPosition( origin[0][0],  origin[0][1],  origin[0][2]) 
    renderer.AddActor(actor)
    return


# ==========================
# ===== PATCHES ADDED BELOW (no edits above) =====
# ==========================

# Safe bounds helper (prevents NoneType/empty-scene crashes)
def _safe_bounds(self):
    if self.renderer is None:
        return (-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
    try:
        if self.renderer.VisibleActorCount() > 0:
            return self.renderer.ComputeVisiblePropBounds()
    except Exception:
        pass
    return (-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)

# Safer camera center
def _reset_camera_focus_to_center_safe(self):
    if self.renderer is None:
        return
    b = self._safe_bounds()
    cx = (b[0] + b[1]) / 2.0
    cy = (b[2] + b[3]) / 2.0
    cz = (b[4] + b[5]) / 2.0
    cam = self.renderer.GetActiveCamera()
    if cam:
        cam.SetFocalPoint(cx, cy, cz)

# Safer view setter
def _set_view_function_safe(self, Position, Viewup):
    if self.renderer is None:
        return
    if self.get_camera is None:
        self.get_camera = self.renderer.GetActiveCamera()
        if self.get_camera is None:
            return
    self.get_camera.SetFocalPoint(0, 0, 0)
    self.get_camera.SetPosition(*Position)
    self.get_camera.SetViewUp(*Viewup)
    self.renderer.ResetCamera()
    self.get_camera.Zoom(1.5)
    self.reset_camera_focus_to_center()
    self.vtkWidget.GetRenderWindow().Render()

def _front_function_safe(self):
    if self.renderer is None:
        return
    b = self._safe_bounds()
    self.set_view_function((-(b[1]-b[0])/2.0, 0, 0), (0, 0, 1))

def _side_function_safe(self):
    if self.renderer is None:
        return
    b = self._safe_bounds()
    self.set_view_function((0, -(b[3]-b[2]), 0), (0, 0, 1))

def _top_function_safe(self):
    if self.renderer is None:
        return
    b = self._safe_bounds()
    self.set_view_function((0, 0, (b[3]-b[2])), (0, 1, 0))

def _isometric_function_safe(self):
    if self.renderer is None:
        return
    b = self._safe_bounds()
    self.set_view_function((-b[5], -b[5], b[5]), (0, 0, 1))

# Replace the methods on the class (without touching the original definitions above)
VisualizeGeometryWidget._safe_bounds = _safe_bounds
VisualizeGeometryWidget.reset_camera_focus_to_center = _reset_camera_focus_to_center_safe
VisualizeGeometryWidget.set_view_function = _set_view_function_safe
VisualizeGeometryWidget.front_function = _front_function_safe
VisualizeGeometryWidget.side_function = _side_function_safe
VisualizeGeometryWidget.top_function = _top_function_safe
VisualizeGeometryWidget.isometric_function = _isometric_function_safe

# Patched run_solve: identical flow, but non-blocking and dark background.
# (We re-implement only the tail section after actors are added.)
_orig_run_solve = VisualizeGeometryWidget.run_solve

def _run_solve_dark(self):
    # ---- Run the original up to (but not including) the blocking/white-bg tail ----
    # We basically re-execute your method body, but with a corrected ending.
    # For clarity and stability, we copy your logic with minimal changes.
    wing_color                  = 'grey'  
    fuselage_color              = 'grey'  
    nacelle_color               = 'grey' 
    boom_color                  = 'grey' 
    fuel_tank_color             = 'orange'  
    rotor_color                 = 'black'      
    wing_opacity                = 0.5  
    fuselage_opacity            = 0.5 
    nacelle_opacity             = 1.0 
    fuel_tank_opacity           = 0.5 
    rotor_opacity               = 1.0  
    number_of_airfoil_points    = 101 
    tessellation                = 96 
    boom_opacity                = 1.0
    camera_eye_x  = -1 
    camera_eye_y  = -1 
    camera_eye_z  = 0.35  
    
    fuel_tank_rgb_color         = mcolors.to_rgb(fuel_tank_color)     
    wing_rgb_color              = mcolors.to_rgb(wing_color)
    fuselage_rgb_color          = mcolors.to_rgb(fuselage_color) 
    nacelle_rgb_color           = mcolors.to_rgb(nacelle_color) 
    rotor_rgb_color             = mcolors.to_rgb(rotor_color)
    boom_rgb_color              = mcolors.to_rgb(boom_color)

    # fresh renderer every time
    self.renderer = vtk.vtkRenderer()
    self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
    # Recommended on some GPUs to avoid flicker/blank
    try:
        self.vtkWidget.GetRenderWindow().SetMultiSamples(0)
    except Exception:
        pass

    self.render_window_interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

    geometry = deepcopy(values.vehicle)

    # Geometry setup
    for wing in geometry.wings:  
        if isinstance(wing, RCAIDE.Library.Components.Wings.Blended_Wing_Body): 
            bwb_wing_planform(wing) 
        else: 
            wing_planform(wing)  
    compute_fuel_volume(geometry)
    for fuselage in geometry.fuselages:
        compute_layout_of_passenger_accommodations(fuselage)
        fuselage_planform(fuselage)

    # Wings
    for wing in geometry.wings:
        n_segments = len(wing.segments)
        dim        = n_segments if n_segments > 0 else 2
        GEOM       = generate_3d_wing_points(wing, number_of_airfoil_points, dim)
        make_object(self.renderer, self.wing_actors, GEOM, wing_rgb_color, wing_opacity)
        if wing.yz_plane_symmetric:
            GEOM.PTS[:, :, 0] = -GEOM.PTS[:, :, 0]
            make_object(self.renderer, self.wing_actors, GEOM, wing_rgb_color, wing_opacity)
        if wing.xz_plane_symmetric:
            GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
            make_object(self.renderer, self.wing_actors, GEOM, wing_rgb_color, wing_opacity)
        if wing.xy_plane_symmetric:
            GEOM.PTS[:, :, 2] = -GEOM.PTS[:, :, 2]
            make_object(self.renderer, self.wing_actors, GEOM, wing_rgb_color, wing_opacity)

    # Fuselages
    for fuselage in geometry.fuselages:
        GEOM = generate_3d_fuselage_points(fuselage, tessellation)
        make_object(self.renderer, self.fuselage_actors, GEOM, fuselage_rgb_color, fuselage_opacity)

    # Booms
    for boom in geometry.booms:
        GEOM = generate_3d_fuselage_points(boom, tessellation)
        make_object(self.renderer, self.boom_actors, GEOM, boom_rgb_color, boom_opacity)

    # Nacelles/Rotors/Propellers/Fuel tanks
    for network in geometry.networks:
        for propulsor in network.propulsors:
            if 'nacelle' in propulsor:
                if propulsor.nacelle is not None:
                    if type(propulsor.nacelle) == RCAIDE.Library.Components.Nacelles.Stack_Nacelle:
                        GEOM = generate_3d_stack_nacelle_points(propulsor.nacelle, tessellation=tessellation, number_of_airfoil_points=number_of_airfoil_points)
                    elif type(propulsor.nacelle) == RCAIDE.Library.Components.Nacelles.Body_of_Revolution_Nacelle:
                        GEOM = generate_3d_BOR_nacelle_points(propulsor.nacelle, tessellation=tessellation, number_of_airfoil_points=number_of_airfoil_points)
                    else:
                        GEOM = generate_3d_basic_nacelle_points(propulsor.nacelle, tessellation=tessellation, number_of_airfoil_points=number_of_airfoil_points)
                    make_object(self.renderer, self.nacelle_actors, GEOM, nacelle_rgb_color, nacelle_opacity)

            if 'rotor' in propulsor:
                rot   = propulsor.rotor
                rot_x = rot.orientation_euler_angles[0]
                rot_y = rot.orientation_euler_angles[1]
                rot_z = rot.orientation_euler_angles[2]
                num_B = int(rot.number_of_blades)
                if rot.radius_distribution is None:
                    make_actuator_disc(self.renderer, rot.hub_radius, rot.tip_radius, rot.origin, rot_x, rot_y, rot_z, rotor_rgb_color, rotor_opacity)
                else:
                    dim = len(rot.radius_distribution)
                    for i in range(num_B):
                        GEOM = generate_3d_blade_points(rot, number_of_airfoil_points, dim, i)
                        make_object(self.renderer, self.rotor_actors, GEOM, rotor_rgb_color, rotor_opacity)

            if 'propeller' in propulsor:
                prop  = propulsor.propeller
                rot_x = prop.orientation_euler_angles[0]
                rot_y = np.pi / 2 + prop.orientation_euler_angles[1]
                rot_z = prop.orientation_euler_angles[2]
                num_B = int(prop.number_of_blades)
                if prop.radius_distribution is None:
                    make_actuator_disc(self.renderer, prop.hub_radius, prop.tip_radius, prop.origin, rot_x, rot_y, rot_z, rotor_rgb_color, rotor_opacity)
                else:
                    dim = len(prop.radius_distribution)
                    for i in range(num_B):
                        GEOM = generate_3d_blade_points(prop, number_of_airfoil_points, dim, i)
                        make_object(self.renderer, self.rotor_actors, GEOM, rotor_rgb_color, rotor_opacity)

        for fuel_line in network.fuel_lines:
            for fuel_tank in fuel_line.fuel_tanks:
                if fuel_tank.wing_tag is not None:
                    wing = geometry.wings[fuel_tank.wing_tag]
                    if issubclass(type(fuel_tank), RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Non_Integral_Tank):
                        GEOM = generate_non_integral_fuel_tank_points(fuel_tank, tessellation)
                        make_object(self.renderer, self.fuel_tank_actors, GEOM, fuel_tank_rgb_color, fuel_tank_opacity)
                        if wing.xz_plane_symmetric:
                            GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                            make_object(self.renderer, self.fuel_tank_actors, GEOM, fuel_tank_rgb_color, fuel_tank_opacity)
                    if type(fuel_tank) == RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Integral_Tank:
                        segment_list = []
                        segment_tags = list(wing.segments.keys())
                        for i in range(len(wing.segments)-1):
                            seg = wing.segments[segment_tags[i]]
                            next_seg = wing.segments[segment_tags[i+1]]
                            if seg.has_fuel_tank:
                                if seg.tag not in segment_list:
                                    segment_list.append(seg.tag)
                                if next_seg.tag not in segment_list:
                                    segment_list.append(next_seg.tag)
                        dim = len(segment_list) if len(wing.segments) > 0 else 2
                        if len(segment_list) == 0 and len(wing.segments) > 0:
                            raise AttributeError('Fuel tank defined on segmented wing but no segments have "tank" attribute = True')
                        else:
                            GEOM = generate_integral_wing_tank_points(wing, 5, dim, segment_list)
                            make_object(self.renderer, self.fuel_tank_actors, GEOM, fuel_tank_rgb_color, fuel_tank_opacity)
                            if wing.xz_plane_symmetric:
                                GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                                make_object(self.renderer, self.fuel_tank_actors, GEOM, fuel_tank_rgb_color, fuel_tank_opacity)
                elif fuel_tank.fuselage_tag is not None:
                    fuselage = geometry.fuselages[fuel_tank.fuselage_tag]
                    if type(fuel_tank) == RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Integral_Tank:
                        segment_list = []
                        segment_tags = list(fuselage.segments.keys())
                        for i in range(len(fuselage.segments)-1):
                            seg = fuselage.segments[segment_tags[i]]
                            next_seg = fuselage.segments[segment_tags[i+1]]
                            if seg.has_fuel_tank:
                                segment_list.append(seg.tag)
                                if next_seg.tag not in segment_list:
                                    segment_list.append(next_seg.tag)
                        GEOM = generate_integral_fuel_tank_points(fuselage, fuel_tank, segment_list, tessellation)
                        make_object(self.renderer, self.fuel_tank_actors, GEOM, fuel_tank_rgb_color, fuel_tank_opacity)
                elif issubclass(type(fuel_tank), RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Non_Integral_Tank):
                    GEOM = generate_non_integral_fuel_tank_points(fuel_tank, tessellation)
                    make_object(self.renderer, self.fuel_tank_actors, GEOM, fuel_tank_rgb_color, fuel_tank_opacity)
                    try:
                        if wing.xz_plane_symmetric:
                            GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                            make_object(self.renderer, self.fuel_tank_actors, GEOM, fuel_tank_rgb_color, fuel_tank_opacity)
                    except Exception:
                        pass  # wing may not be defined in this branch

    # ---- Patched tail: dark background + non-blocking render ----
    camera = vtk.vtkCamera()
    camera.SetPosition(camera_eye_x, camera_eye_y, camera_eye_z)
    camera.SetFocalPoint(0, 0, 0)
    camera.SetViewUp(0, 0, 1)

    self.renderer.SetActiveCamera(camera)
    self.renderer.ResetCamera()

    # Dark gradient background (was white)
    self.renderer.SetBackground(0.05, 0.09, 0.15)
    self.renderer.SetBackground2(0.12, 0.18, 0.28)
    try:
        self.renderer.GradientBackgroundOn()
        self.renderer.UseFXAAOn()
    except Exception:
        pass

    custom_style = CustomInteractorStyle()
    self.render_window_interactor.SetInteractorStyle(custom_style)

    self.render_window_interactor.Initialize()
    # IMPORTANT: Do NOT call .Start(); it blocks the Qt loop (causing “stuck previous tab”)
    self.vtkWidget.GetRenderWindow().Render()

    self.get_camera = self.renderer.GetActiveCamera()
    self.update_toolbar()
    try:
        if values.vehicle.wings:
            self.colorbar_widget.update_parts(self.part_actors)
    except Exception:
        pass

    # Safe isometric only if we have something to show
    if self.renderer and self.renderer.VisibleActorCount() > 0:
        self.isometric_function()

# Override the original run_solve with the patched, non-blocking dark version
VisualizeGeometryWidget.run_solve = _run_solve_dark

# =================================
# BACKGROUND MENU (with checkmarks)
# =================================
from PyQt6.QtWidgets import QPushButton, QMenu, QColorDialog, QCheckBox
from PyQt6.QtGui import QAction, QColor
import vtk

class BackgroundManager:
    """Controls the renderer background and updates checkmarks."""
    def __init__(self, widget):
        self.widget = widget
        self.renderer = widget.renderer
        self.window = widget.vtkWidget.GetRenderWindow()
        self.current_mode = None  # "dark", "light", or "custom"

    def _update_checkmarks(self, selected):
        """Update all checkmarks when user switches background mode."""
        for mode, action in self.widget._bg_actions.items():
            action.setCheckable(True)
            action.setChecked(mode == selected)
        self.current_mode = selected

    def set_dark_mode(self):
        self.renderer.GradientBackgroundOn()
        self.renderer.SetBackground(0.05, 0.08, 0.15)
        self.renderer.SetBackground2(0.12, 0.18, 0.28)
        self.window.Render()
        self._update_checkmarks("dark")

    def set_light_mode(self):
        self.renderer.GradientBackgroundOn()
        self.renderer.SetBackground(0.85, 0.90, 0.98)
        self.renderer.SetBackground2(1.0, 1.0, 1.0)
        self.window.Render()
        self._update_checkmarks("light")

    def set_custom_color(self):
        color = QColorDialog.getColor(QColor(20, 20, 20), self.widget, "Choose Background Color")
        if not color.isValid():
            return
        self.renderer.GradientBackgroundOff()
        self.renderer.SetBackground(color.redF(), color.greenF(), color.blueF())
        self.window.Render()
        self._update_checkmarks("custom")


def _add_background_menu(self):
    """Adds background color dropdown with checkmarks."""
    if getattr(self, "_background_menu_added", False):
        return
    self._background_menu_added = True

    btn = QPushButton("🌄 Background")
    self.toolbar.addSeparator()
    self.toolbar.addWidget(btn)

    # Initialize manager and menu
    self.bg_manager = BackgroundManager(self)
    menu = QMenu(btn)
    self._bg_actions = {}

    # Actions with checkmarks
    act_dark = QAction("Dark Mode", menu, triggered=self.bg_manager.set_dark_mode)
    act_light = QAction("Light Mode", menu, triggered=self.bg_manager.set_light_mode)
    act_custom = QAction("Custom Color…", menu, triggered=self.bg_manager.set_custom_color)

    self._bg_actions = {"dark": act_dark, "light": act_light, "custom": act_custom}
    for act in self._bg_actions.values():
        act.setCheckable(True)
        menu.addAction(act)

    # Set default to dark mode
    self.bg_manager._update_checkmarks("dark")
    self.bg_manager.set_dark_mode()

    btn.setMenu(menu)


def _patch_background_menu():
    """Attach background menu to VisualizeGeometryWidget.run_solve."""
    if getattr(VisualizeGeometryWidget, "_background_menu_patched", False):
        return
    old = VisualizeGeometryWidget.run_solve

    def wrapped(self):
        old(self)
        _add_background_menu(self)

    VisualizeGeometryWidget.run_solve = wrapped
    VisualizeGeometryWidget._background_menu_patched = True

_patch_background_menu()

# ===================================
# FULLSCREEN GRIDLINE OVERLAY SYSTEM 
# ===================================
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QCheckBox
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox
import vtk

def add_fullscreen_grid(renderer, theme="dark", divisions=12):
    """Draw a fullscreen 2D grid overlay matching the current theme."""
    if not renderer or not renderer.GetRenderWindow():
        return None
    win = renderer.GetRenderWindow()
    w, h = win.GetActualSize()
    if w == 0 or h == 0:
        return None

    # Grid color and opacity based on background theme
    color, opacity = ((0.6, 0.7, 0.9), 0.25) if theme == "dark" else ((0.25, 0.25, 0.25), 0.35)
    step = min(w, h) / divisions

    pts, lines = vtk.vtkPoints(), vtk.vtkCellArray()
    pid = 0

    for i in range(int(w / step) + 1):
        x = i * step
        pts.InsertNextPoint(x, 0, 0)
        pts.InsertNextPoint(x, h, 0)
        lines.InsertNextCell(2)
        lines.InsertCellPoint(pid)
        lines.InsertCellPoint(pid + 1)
        pid += 2

    for j in range(int(h / step) + 1):
        y = j * step
        pts.InsertNextPoint(0, y, 0)
        pts.InsertNextPoint(w, y, 0)
        lines.InsertNextCell(2)
        lines.InsertCellPoint(pid)
        lines.InsertCellPoint(pid + 1)
        pid += 2

    grid = vtk.vtkPolyData()
    grid.SetPoints(pts)
    grid.SetLines(lines)
    mapper = vtk.vtkPolyDataMapper2D()
    mapper.SetInputData(grid)
    actor = vtk.vtkActor2D()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(color)
    actor.GetProperty().SetOpacity(opacity)

    overlay = vtk.vtkRenderer()
    overlay.SetLayer(1)
    overlay.InteractiveOff()
    overlay.AddActor(actor)
    overlay.SetBackgroundAlpha(0.0)
    win.SetNumberOfLayers(2)
    win.AddRenderer(overlay)
    win.Render()
    return overlay


_old_run_solve = VisualizeGeometryWidget.run_solve

def _run_solve_with_gridlines(self):
    """Adds gridline overlay toggle to the toolbar."""
    _old_run_solve(self)
    win = self.renderer.GetRenderWindow()
    self.current_theme = getattr(self, "current_theme", "dark")

    # --- GRID TOGGLE ---
    if not hasattr(self, "grid_checkbox"):
        self.grid_checkbox = QCheckBox("Show Gridlines")
        self.grid_checkbox.setChecked(False)
        self.grid_checkbox.setStyleSheet("color:white;font-size:10pt;")
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.grid_checkbox)

        def toggle_grid(state):
            # Remove existing grid if toggled off
            if hasattr(self, "overlay_grid") and self.overlay_grid:
                win.RemoveRenderer(self.overlay_grid)
                self.overlay_grid = None
            # Add new grid overlay if toggled on
            if state == 2:
                self.overlay_grid = add_fullscreen_grid(self.renderer, theme=self.current_theme)
            win.Render()

        self.grid_checkbox.stateChanged.connect(toggle_grid)

        # Auto-resize grid when window size changes
        def on_resize(obj, event):
            if getattr(self, "overlay_grid", None) and self.grid_checkbox.isChecked():
                win.RemoveRenderer(self.overlay_grid)
                self.overlay_grid = add_fullscreen_grid(self.renderer, theme=self.current_theme)
        win.AddObserver("WindowResizeEvent", on_resize)

    win.Render()

VisualizeGeometryWidget.run_solve = _run_solve_with_gridlines


# =====================================
# AXES GIZMO (with Transparent Border)
# =====================================
import vtk

def add_orientation_gizmo(renderer, render_window):
    try:
        axes = vtk.vtkAxesActor()
        for a in [
            axes.GetXAxisCaptionActor2D(),
            axes.GetYAxisCaptionActor2D(),
            axes.GetZAxisCaptionActor2D(),
        ]:
            a.GetTextActor().GetTextProperty().SetFontSize(14)
            a.GetTextActor().GetTextProperty().SetColor(1, 1, 1)

        # make a simple transparent square border
        border = vtk.vtkCubeSource()
        border.SetXLength(1.2)
        border.SetYLength(1.2)
        border.SetZLength(1.2)
        border_mapper = vtk.vtkPolyDataMapper()
        border_mapper.SetInputConnection(border.GetOutputPort())
        border_actor = vtk.vtkActor()
        border_actor.SetMapper(border_mapper)
        border_actor.GetProperty().SetColor(0.8, 0.8, 0.8)
        border_actor.GetProperty().SetOpacity(0.1)
        border_actor.GetProperty().SetRepresentationToWireframe()

        assembly = vtk.vtkPropAssembly()
        assembly.AddPart(border_actor)
        assembly.AddPart(axes)

        widget = vtk.vtkOrientationMarkerWidget()
        interactor = render_window.GetInteractor()
        widget.SetOrientationMarker(assembly)
        widget.SetViewport(0.0, 0.0, 0.18, 0.28)
        widget.SetInteractor(interactor)
        if not interactor.GetInitialized():
            interactor.Initialize()
        widget.EnabledOn()
        widget.InteractiveOff()
        render_window.Render()

        renderer._axes_widget = widget
    except Exception:
        pass


if not hasattr(VisualizeGeometryWidget, "_gizmo_patched"):
    _orig_run_solve = VisualizeGeometryWidget.run_solve

    def _run_solve_with_gizmo(self):
        _orig_run_solve(self)
        add_orientation_gizmo(self.renderer, self.vtkWidget.GetRenderWindow())

    VisualizeGeometryWidget.run_solve = _run_solve_with_gizmo
    VisualizeGeometryWidget._gizmo_patched = True

# ======================================= 
# AUTO-ROTATE CAMERA (360° Orbit, Faster)
# =======================================
import math, vtk
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QPushButton

def add_360_view(self):
    if hasattr(self, "view360_button"):
        return

    btn = QPushButton("360° View")
    btn.setCheckable(True)
    self.toolbar.addSeparator()
    self.toolbar.addWidget(btn)

    timer = QTimer()
    timer.setInterval(25)   # faster refresh (~40 FPS)
    angle = {"a": 0}
    state = {"center": None, "dist": None}

    def init_camera():
        b = self.renderer.ComputeVisiblePropBounds()
        if not b or b[0] == b[1]:
            return
        c = [(b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2]
        size = max(b[1]-b[0], b[3]-b[2], b[5]-b[4])
        d = size * 3.5
        cam = self.renderer.GetActiveCamera()
        pos = cam.GetPosition()
        if not state["center"]:
            cam.SetPosition(c[0] + d, c[1], c[2])
            cam.SetFocalPoint(*c)
            cam.SetViewUp(0, 0, 1)
            cam.SetClippingRange(0.1, d * 10)
            self.vtkWidget.GetRenderWindow().Render()
            state["center"], state["dist"] = c, d
            angle["a"] = 0
        else:
            state["center"], state["dist"] = c, state["dist"] or d

    def update():
        if not state["center"]:
            return
        cam = self.renderer.GetActiveCamera()
        c, d = state["center"], state["dist"]
        angle["a"] += 1.5  # ⚡ rotate faster (~5 sec per full revolution)
        if angle["a"] >= 360:
            angle["a"] = 0
        r = math.radians(angle["a"])
        cam.SetPosition(c[0] + d * math.cos(r), c[1] - d * math.sin(r), c[2])
        cam.SetFocalPoint(*c)
        cam.SetViewUp(0, 0, 1)
        cam.SetClippingRange(0.1, d * 10)
        self.vtkWidget.GetRenderWindow().Render()

    timer.timeout.connect(update)
    btn.toggled.connect(lambda checked: (init_camera(), timer.start()) if checked else timer.stop())

if not hasattr(VisualizeGeometryWidget, "_view360_patched"):
    old = VisualizeGeometryWidget.run_solve
    def _run_solve(self):
        old(self)
        add_360_view(self)
    VisualizeGeometryWidget.run_solve = _run_solve
    VisualizeGeometryWidget._view360_patched = True

# ===========================
#  MEASUREMENT TOOL SECTION 
# ===========================
import vtk, math
from PyQt6.QtWidgets import QPushButton

def add_measure_tool(self):
    if getattr(self, "_measure_tool_loaded", False):
        return
    self._measure_tool_loaded = True

    # --- Toolbar Buttons ---
    btn = QPushButton("📏 Measure"); btn.setCheckable(True)
    undo = QPushButton("↩ Undo")
    clr  = QPushButton("🧹 Clear")
    self.toolbar.addSeparator()
    for w in (btn, undo, clr):
        self.toolbar.addWidget(w)

    picker = vtk.vtkCellPicker()
    picker.SetTolerance(0.0005)
    pts, temp_dots, measures = [], [], []
    self._measure_obs = None

    def scene_diag():
        b = self.renderer.ComputeVisiblePropBounds()
        return max(b[1]-b[0], b[3]-b[2], b[5]-b[4]) or 1.0

    # --- Dots ---
    def make_dot(p, color):
        r = 0.0075 * scene_diag()
        s = vtk.vtkSphereSource(); s.SetRadius(r)
        m = vtk.vtkPolyDataMapper(); m.SetInputConnection(s.GetOutputPort())
        a = vtk.vtkActor(); a.SetMapper(m); a.SetPosition(*p)
        a.GetProperty().SetColor(*color)
        a.GetProperty().SetLighting(False)
        self.renderer.AddActor(a)
        return a

    # --- Yellow lines ---
    def make_line(p1, p2):
        l = vtk.vtkLineSource(); l.SetPoint1(p1); l.SetPoint2(p2)
        m = vtk.vtkPolyDataMapper(); m.SetInputConnection(l.GetOutputPort())
        a = vtk.vtkActor(); a.SetMapper(m)
        prop = a.GetProperty()
        prop.SetColor(1.0, 1.0, 0.0)
        prop.SetLineWidth(3.5)
        prop.SetDiffuse(0.0)
        prop.SetAmbient(1.0)
        prop.SetSpecular(0.0)
        prop.SetLighting(False)
        self.renderer.AddActor(a)
        return a

    # --- Perfectly visible overlay label ---
    def make_label(p1, p2, L):
        """2D overlay cyan label that stays visible no matter what."""
        mid = (
            (p1[0] + p2[0]) / 2,
            (p1[1] + p2[1]) / 2,
            (p1[2] + p2[2]) / 2,
        )
        txt = f"{L:.3f} m"

        coord = vtk.vtkCoordinate()
        coord.SetCoordinateSystemToWorld()
        coord.SetValue(*mid)

        text_actor = vtk.vtkTextActor()
        text_actor.SetInput(txt)
        tp = text_actor.GetTextProperty()
        tp.SetFontSize(26)
        tp.SetBold(True)
        tp.SetColor(0.4, 1.0, 1.0)  # glowing sky cyan (readable on grey)
        tp.SetOpacity(1.0)
        tp.SetShadow(True)
        tp.SetShadowOffset(2, -2)
        tp.SetJustificationToCentered()
        tp.SetVerticalJustificationToCentered()
        text_actor.GetPositionCoordinate().SetReferenceCoordinate(coord)
        text_actor.GetPositionCoordinate().SetCoordinateSystemToWorld()
        self.renderer.AddActor2D(text_actor)
        return text_actor

    # --- On click ---
    def on_click(_obj, _evt):
        if not btn.isChecked():
            return
        x, y = self.render_window_interactor.GetEventPosition()
        if not picker.Pick(x, y, 0, self.renderer):
            return
        p = picker.GetPickPosition()
        color = (0, 0.7, 1) if len(pts) == 0 else (1, 0.2, 0.2)
        dot = make_dot(p, color)
        pts.append((p, dot))
        temp_dots.append(dot)

        if len(pts) == 2:
            (p1, d1), (p2, d2) = pts
            L = math.dist(p1, p2)
            line = make_line(p1, p2)
            txt = make_label(p1, p2, L)
            measures.append({'line': line, 'txt': txt, 'd1': d1, 'd2': d2})
            pts.clear(); temp_dots.clear()
            self.vtkWidget.GetRenderWindow().Render()

    # --- Toggle ---
    def toggle(on):
        rw = self.vtkWidget.GetRenderWindow()
        if on:
            if self._measure_obs is None:
                self._measure_obs = self.render_window_interactor.AddObserver(
                    "LeftButtonPressEvent", on_click, 1.0)
        else:
            if self._measure_obs is not None:
                self.render_window_interactor.RemoveObserver(self._measure_obs)
                self._measure_obs = None
        rw.Render()

    # --- Clear / Undo ---
    def do_clear():
        for m in measures:
            for key in ('line', 'txt', 'd1', 'd2'):
                self.renderer.RemoveActor(m[key])
        for d in temp_dots:
            self.renderer.RemoveActor(d)
        measures.clear(); temp_dots.clear(); pts.clear()
        self.vtkWidget.GetRenderWindow().Render()

    def do_undo():
        if not measures:
            return
        m = measures.pop()
        for key in ('line', 'txt', 'd1', 'd2'):
            self.renderer.RemoveActor(m[key])
        self.vtkWidget.GetRenderWindow().Render()

    btn.toggled.connect(toggle)
    clr.clicked.connect(do_clear)
    undo.clicked.connect(do_undo)


def _patch_measure():
    if getattr(VisualizeGeometryWidget, "_measure_patched", False):
        return
    old = VisualizeGeometryWidget.run_solve
    def wrapped(self):
        old(self)
        add_measure_tool(self)
    VisualizeGeometryWidget.run_solve = wrapped
    VisualizeGeometryWidget._measure_patched = True

_patch_measure()

# ==========================
# SCREENSHOT EXPORT SECTION (with Save Dialog)
# ==========================
import vtk, datetime
from PyQt6.QtWidgets import QPushButton, QFileDialog, QMessageBox

def add_screenshot_button(self):
    if getattr(self, "_screenshot_loaded", False):
        return
    self._screenshot_loaded = True

    btn = QPushButton("📷 Export View")
    self.toolbar.addSeparator()
    self.toolbar.addWidget(btn)

    def save_screenshot():
        # --- Open save dialog ---
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_name = f"screenshot_{timestamp}.png"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot As",
            default_name,
            "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
        )
        if not filepath:
            return  # user canceled

        # --- Capture VTK render window ---
        w2i = vtk.vtkWindowToImageFilter()
        w2i.SetInput(self.vtkWidget.GetRenderWindow())
        w2i.Update()

        # --- Choose writer based on extension ---
        ext = filepath.split('.')[-1].lower()
        if ext == "jpg" or ext == "jpeg":
            writer = vtk.vtkJPEGWriter()
        else:
            writer = vtk.vtkPNGWriter()

        writer.SetFileName(filepath)
        writer.SetInputConnection(w2i.GetOutputPort())
        writer.Write()

        # --- Confirmation popup ---
        msg = QMessageBox()
        msg.setWindowTitle("Export Successful")
        msg.setText(f"✅ Screenshot saved as:\n{filepath}")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    btn.clicked.connect(save_screenshot)


def _patch_screenshot():
    if getattr(VisualizeGeometryWidget, "_screenshot_patched", False):
        return
    old = VisualizeGeometryWidget.run_solve

    def wrapped(self):
        old(self)
        add_screenshot_button(self)

    VisualizeGeometryWidget.run_solve = wrapped
    VisualizeGeometryWidget._screenshot_patched = True

_patch_screenshot()

# =======================
# BLUEPRINT UPLOAD SYSTEM
# =======================

from PyQt6.QtWidgets import QPushButton, QFileDialog, QMenu
from PyQt6.QtCore import Qt, QTimer
import vtk, os


class BlueprintManager:
    def __init__(self, widget):
        self.widget = widget
        self.renderer = widget.renderer
        self.actors = {}
        self.outlines = {}
        self.selected_view = None
        self.opacity = 0.5
        self.scale = 1.0
        self.base_transforms = {}
        self.picker = vtk.vtkPropPicker()

    # --- Preserve camera state ---
    def _store_camera(self):
        cam = self.renderer.GetActiveCamera()
        return {
            "pos": cam.GetPosition(),
            "focal": cam.GetFocalPoint(),
            "viewup": cam.GetViewUp(),
            "clipping": cam.GetClippingRange(),
        }

    def _restore_camera(self, state):
        if not state:
            return
        cam = self.renderer.GetActiveCamera()
        cam.SetPosition(*state["pos"])
        cam.SetFocalPoint(*state["focal"])
        cam.SetViewUp(*state["viewup"])
        cam.SetClippingRange(*state["clipping"])
        self.renderer.ResetCameraClippingRange()

    # --- Read texture ---
    def _read_image_as_texture(self, file_name):
        ext = os.path.splitext(file_name)[1].lower()
        reader = vtk.vtkJPEGReader() if ext in [".jpg", ".jpeg"] else vtk.vtkPNGReader()
        reader.SetFileName(file_name)
        reader.Update()
        texture = vtk.vtkTexture()
        texture.SetInputConnection(reader.GetOutputPort())
        texture.InterpolateOn()
        texture.RepeatOff()
        texture.EdgeClampOn()
        return texture, reader.GetOutput()

    # --- Model bounds ---
    def _model_bounds(self):
        b = self.renderer.ComputeVisiblePropBounds()
        cx, cy, cz = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2
        sx, sy, sz = (b[1] - b[0]) or 1, (b[3] - b[2]) or 1, (b[5] - b[4]) or 1
        return b, (cx, cy, cz), (sx, sy, sz), max(sx, sy, sz)

    # --- Outline (wireframe cube) ---
    def _make_outline(self, actor):
        bounds = actor.GetBounds()
        cube = vtk.vtkCubeSource()
        cube.SetBounds(bounds)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(cube.GetOutputPort())

        outline = vtk.vtkActor()
        outline.SetMapper(mapper)
        outline.GetProperty().SetColor(0.2, 0.6, 1.0)
        outline.GetProperty().SetLineWidth(3)
        outline.GetProperty().LightingOff()
        outline.GetProperty().SetRepresentationToWireframe()
        return outline

    def _update_outline(self, view):
        if view not in self.actors or view not in self.outlines:
            return
        actor = self.actors[view]
        outline = self.outlines[view]
        bounds = actor.GetBounds()
        cube = outline.GetMapper().GetInputConnection(0, 0).GetProducer()
        cube.SetBounds(bounds)

    # --- Highlight selected ---
    def _highlight_selected(self, view):
        for o in list(self.outlines.values()):
            if o:
                self.renderer.RemoveActor(o)
        if view in self.actors:
            outline = self._make_outline(self.actors[view])
            self.renderer.AddActor(outline)
            self.outlines[view] = outline
        self.widget.vtkWidget.GetRenderWindow().Render()

    # --- Load blueprint ---
    def load_image(self, view):
        file_name, _ = QFileDialog.getOpenFileName(
            self.widget, f"Select {view.capitalize()} Blueprint", "",
            "Image Files (*.png *.jpg *.jpeg)"
        )
        if not file_name:
            return

        cam_state = self._store_camera()
        texture, img_data = self._read_image_as_texture(file_name)
        iw, ih, _ = img_data.GetDimensions()
        if iw == 0 or ih == 0:
            return
        aspect = iw / ih

        b, (cx, cy, cz), (sx, sy, sz), base = self._model_bounds()
        spacing = 0.25 * base
        bp_width = 0.9 * sx
        bp_height = bp_width / aspect

        plane = vtk.vtkPlaneSource()
        if view == "top":
            z = b[4] - spacing
            plane.SetOrigin(cx - bp_width / 2, cy - bp_height / 2, z)
            plane.SetPoint1(cx + bp_width / 2, cy - bp_height / 2, z)
            plane.SetPoint2(cx - bp_width / 2, cy + bp_height / 2, z)
        elif view == "side":
            y = b[3] + spacing
            plane.SetOrigin(cx - bp_width / 2, y, cz - bp_height / 2)
            plane.SetPoint1(cx + bp_width / 2, y, cz - bp_height / 2)
            plane.SetPoint2(cx - bp_width / 2, y, cz + bp_height / 2)
        elif view == "front":
            x = b[1] + spacing
            plane.SetOrigin(x, cy - bp_width / 2, cz - bp_height / 2)
            plane.SetPoint1(x, cy + bp_width / 2, cz - bp_height / 2)
            plane.SetPoint2(x, cy - bp_width / 2, cz + bp_height / 2)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(plane.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.SetTexture(texture)
        actor.GetProperty().SetOpacity(self.opacity)
        actor.GetProperty().LightingOff()
        actor.SetPickable(True)

        # Remove old view actor
        if view in self.actors:
            self.renderer.RemoveActor(self.actors[view])
        self.renderer.AddActor(actor)
        self.actors[view] = actor
        self.base_transforms[view] = vtk.vtkTransform()
        actor.SetUserTransform(self.base_transforms[view])

        self.selected_view = view
        self._highlight_selected(view)
        self._restore_camera(cam_state)

        if hasattr(self.widget, "_reset_blueprint_sliders"):
            self.widget._reset_blueprint_sliders()

        self.widget.vtkWidget.GetRenderWindow().Render()

    # --- Picking ---
    def enable_picking(self):
        interactor = self.widget.vtkWidget.GetRenderWindow().GetInteractor()
        interactor.AddObserver("LeftButtonPressEvent", self._on_click)

    def _on_click(self, obj, event):
        x, y = obj.GetEventPosition()
        self.picker.Pick(x, y, 0, self.renderer)
        picked = self.picker.GetActor()
        if not picked:
            return
        for v, a in self.actors.items():
            if a == picked:
                self.selected_view = v
                self._highlight_selected(v)
                if hasattr(self.widget, "_reset_blueprint_sliders"):
                    self.widget._reset_blueprint_sliders()
                break

    # --- Transparency ---
    def update_opacity(self, value):
        self.opacity = value / 100.0
        if self.selected_view in self.actors:
            self.actors[self.selected_view].GetProperty().SetOpacity(self.opacity)
            self.widget.vtkWidget.GetRenderWindow().Render()

    # --- Scale (no camera shift) ---
    def update_scale(self, value):
        self.scale = value / 100.0
        if self.selected_view in self.actors:
            actor = self.actors[self.selected_view]
            transform = self.base_transforms[self.selected_view]
            transform.Identity()
            transform.Scale(self.scale, self.scale, self.scale)
            actor.SetUserTransform(transform)
            self._update_outline(self.selected_view)
            self.widget.vtkWidget.GetRenderWindow().Render()

    # --- Clear ---
    def clear_all(self):
        for a in self.actors.values():
            self.renderer.RemoveActor(a)
        for o in self.outlines.values():
            self.renderer.RemoveActor(o)
        self.actors.clear()
        self.outlines.clear()
        self.selected_view = None
        self.widget.vtkWidget.GetRenderWindow().Render()


# --- Toolbar Integration ---
def add_blueprint_menu(self):
    if getattr(self, "_blueprint_menu_loaded", False):
        return
    self._blueprint_menu_loaded = True
    self.blueprint_manager = BlueprintManager(self)

    def _add_menu():
        btn = QPushButton("📐 Blueprint")
        menu = QMenu(btn)
        menu.addAction("Load Top View", lambda: self.blueprint_manager.load_image("top"))
        menu.addAction("Load Side View", lambda: self.blueprint_manager.load_image("side"))
        menu.addAction("Load Front View", lambda: self.blueprint_manager.load_image("front"))
        menu.addSeparator()
        menu.addAction("🧹 Clear All Blueprints", lambda: self.blueprint_manager.clear_all())
        btn.setMenu(menu)
        self.toolbar.addWidget(btn)
        self.blueprint_manager.enable_picking()
        self.toolbar.raise_()

    QTimer.singleShot(500, _add_menu)


if not hasattr(VisualizeGeometryWidget, "_blueprint_patched"):
    old_run = VisualizeGeometryWidget.run_solve

    def wrapped_run(self):
        old_run(self)
        add_blueprint_menu(self)

    VisualizeGeometryWidget.run_solve = wrapped_run
    VisualizeGeometryWidget._blueprint_patched = True

# ===========================
# BLUEPRINT ADJUSTOR DROPDOWN 
# ===========================

from PyQt6.QtWidgets import QPushButton, QWidget, QMenu, QLabel, QSlider, QVBoxLayout, QWidgetAction
from PyQt6.QtCore import Qt, QTimer


def add_blueprint_adjustor_dropdown(self):
    """Adds 'Adjustor ▼' after '📐 Blueprint', synced with per-blueprint slider states."""
    if getattr(self, "_blueprint_adjustor_loaded", False):
        return
    self._blueprint_adjustor_loaded = True

    # --- Adjustor button setup ---
    adjustor_btn = QPushButton("Adjustor")
    adjustor_btn.setFlat(True)
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

    # === Dropdown menu ===
    menu = QMenu(adjustor_btn)
    menu.setStyleSheet("""
        QMenu {
            background-color: #2b2e35;
            color: #dcdfe4;
            border: 1px solid #4a90e2;
            padding: 8px 10px 10px 10px;
        }
    """)

    # === Dropdown content ===
    content = QWidget()
    layout = QVBoxLayout(content)
    layout.setContentsMargins(10, 12, 10, 10)
    layout.setSpacing(10)

    # --- Title (centered one-line label) ---
    title = QLabel("Active Blueprint: None")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setWordWrap(False)
    title.setStyleSheet("""
        font-weight:bold;
        color:#b7dcff;
        font-size:13px;
        padding: 4px 2px 6px 2px;
    """)
    layout.addWidget(title)

    # Transparency slider
    t_label = QLabel("Transparency")
    t_label.setStyleSheet("font-weight:bold;color:#b7dcff;font-size:12px;")
    layout.addWidget(t_label)
    t_slider = QSlider(Qt.Orientation.Horizontal)
    t_slider.setRange(0, 100)
    t_slider.setValue(50)
    layout.addWidget(t_slider)

    # Size slider
    s_label = QLabel("Size")
    s_label.setStyleSheet("font-weight:bold;color:#b7dcff;font-size:12px;")
    layout.addWidget(s_label)
    s_slider = QSlider(Qt.Orientation.Horizontal)
    s_slider.setRange(50, 200)
    s_slider.setValue(100)
    layout.addWidget(s_slider)

    # --- Bind sliders + per-blueprint state tracking ---
    def bind_blueprint_manager():
        if not hasattr(self, "blueprint_manager"):
            QTimer.singleShot(300, bind_blueprint_manager)
            return

        bm = self.blueprint_manager
        bm._view_states = {}  # {view: {"opacity": val, "scale": val}}

        def refresh_label():
            active = getattr(bm, "selected_view", None) or "None"
            title.setText(f"Active Blueprint: {active.capitalize()}")

        # --- When sliders move, update both blueprint and stored state ---
        def on_opacity_change(val):
            if bm.selected_view:
                bm.update_opacity(val)
                bm._view_states.setdefault(bm.selected_view, {})["opacity"] = val

        def on_scale_change(val):
            if bm.selected_view:
                bm.update_scale(val)
                bm._view_states.setdefault(bm.selected_view, {})["scale"] = val

        t_slider.valueChanged.connect(on_opacity_change)
        s_slider.valueChanged.connect(on_scale_change)

        # --- Update sliders when switching or loading new blueprints ---
        old_load = bm.load_image
        def wrapped_load_image(view):
            old_load(view)
            bm.selected_view = view
            refresh_label()
            # restore or set default
            state = bm._view_states.get(view, {"opacity": 50, "scale": 100})
            t_slider.setValue(state.get("opacity", 50))
            s_slider.setValue(state.get("scale", 100))
        bm.load_image = wrapped_load_image

        # --- Update label and sliders when blueprint clicked ---
        old_click = bm._on_click
        def wrapped_click(obj, event):
            old_click(obj, event)
            refresh_label()
            if bm.selected_view:
                state = bm._view_states.get(bm.selected_view, {"opacity": 50, "scale": 100})
                t_slider.setValue(state.get("opacity", 50))
                s_slider.setValue(state.get("scale", 100))
        bm._on_click = wrapped_click

        refresh_label()

    bind_blueprint_manager()

    # --- Embed content ---
    widget_action = QWidgetAction(menu)
    widget_action.setDefaultWidget(content)
    menu.addAction(widget_action)
    adjustor_btn.setMenu(menu)

    # --- Toolbar insertion ---
    def insert_adjustor_button():
        for act in self.toolbar.actions():
            w = self.toolbar.widgetForAction(act)
            if hasattr(w, "text") and "Blueprint" in w.text():
                idx = self.toolbar.actions().index(act)
                if idx < len(self.toolbar.actions()) - 1:
                    self.toolbar.insertWidget(self.toolbar.actions()[idx + 1], adjustor_btn)
                else:
                    self.toolbar.addWidget(adjustor_btn)
                return
        QTimer.singleShot(500, insert_adjustor_button)

    insert_adjustor_button()


# --- Patch VisualizeGeometryWidget for Adjustor ---
if not hasattr(VisualizeGeometryWidget, "_blueprint_adjustor_patched"):
    _base_run_solve = getattr(VisualizeGeometryWidget, "run_solve", None)

    def safe_wrapped_run(self):
        if hasattr(VisualizeGeometryWidget, "_original_run_solve"):
            VisualizeGeometryWidget._original_run_solve(self)
        else:
            _base_run_solve(self)
        add_blueprint_adjustor_dropdown(self)

    if not hasattr(VisualizeGeometryWidget, "_original_run_solve"):
        VisualizeGeometryWidget._original_run_solve = _base_run_solve

    VisualizeGeometryWidget.run_solve = safe_wrapped_run
    VisualizeGeometryWidget._blueprint_adjustor_patched = True

# =========================================
# AIRCRAFT DRAG SECTION (Move Entire Model)
# =========================================
import vtk
from PyQt6.QtWidgets import QPushButton

class DragAircraftInteractor(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, widget, actors):
        super().__init__()
        self.widget = widget
        self.actors = actors
        self.is_dragging = False
        self.last_pos = None
        self.AddObserver("LeftButtonPressEvent", self.left_down)
        self.AddObserver("LeftButtonReleaseEvent", self.left_up)
        self.AddObserver("MouseMoveEvent", self.mouse_move)

    def left_down(self, obj, event):
        self.is_dragging = True
        self.last_pos = self.GetInteractor().GetEventPosition()
        self.OnLeftButtonDown()

    def left_up(self, obj, event):
        self.is_dragging = False
        self.OnLeftButtonUp()

    def mouse_move(self, obj, event):
        if not self.is_dragging or not self.last_pos:
            return
        interactor = self.GetInteractor()
        x, y = interactor.GetEventPosition()
        dx = x - self.last_pos[0]
        dy = y - self.last_pos[1]
        self.last_pos = (x, y)

        camera = self.widget.renderer.GetActiveCamera()
        fp = camera.GetFocalPoint()
        pos = camera.GetPosition()
        renderer = self.widget.renderer
        renderer.SetWorldPoint(fp[0], fp[1], fp[2], 1.0)
        renderer.WorldToDisplay()
        d_z = renderer.GetDisplayPoint()[2]

        # Convert pixel delta to world delta
        renderer.SetDisplayPoint(x, y, d_z)
        renderer.DisplayToWorld()
        world_pt = renderer.GetWorldPoint()
        wx, wy, wz, _ = world_pt
        renderer.SetDisplayPoint(x - dx, y - dy, d_z)
        renderer.DisplayToWorld()
        world_pt2 = renderer.GetWorldPoint()
        wx2, wy2, wz2, _ = world_pt2

        # Compute translation delta
        delta = (wx - wx2, wy - wy2, wz - wz2)
        for group in self.actors.values():
            for actor in group:
                ax, ay, az = actor.GetPosition()
                actor.SetPosition(ax + delta[0], ay + delta[1], az + delta[2])

        interactor.GetRenderWindow().Render()


def add_drag_button(self):
    if getattr(self, "_drag_button_loaded", False):
        return
    self._drag_button_loaded = True

    btn = QPushButton("✈️ Drag Aircraft")
    btn.setCheckable(True)
    self.toolbar.addSeparator()
    self.toolbar.addWidget(btn)

    normal_style = CustomInteractorStyle()
    drag_style = None

    def toggle_drag(active):
        nonlocal drag_style
        if active:
            all_actors = {
                "Fuselages": self.fuselage_actors,
                "Wings": self.wing_actors,
                "Nacelles": self.nacelle_actors,
                "Rotors": self.rotor_actors,
                "Booms": self.boom_actors,
                "Fuel Tanks": self.fuel_tank_actors,
            }
            drag_style = DragAircraftInteractor(self, all_actors)
            drag_style.SetDefaultRenderer(self.renderer)
            self.render_window_interactor.SetInteractorStyle(drag_style)
        else:
            self.render_window_interactor.SetInteractorStyle(normal_style)
        self.vtkWidget.GetRenderWindow().Render()

    btn.toggled.connect(toggle_drag)


def _patch_drag():
    if getattr(VisualizeGeometryWidget, "_drag_patched", False):
        return
    old = VisualizeGeometryWidget.run_solve

    def wrapped(self):
        old(self)
        add_drag_button(self)

    VisualizeGeometryWidget.run_solve = wrapped
    VisualizeGeometryWidget._drag_patched = True

_patch_drag()
