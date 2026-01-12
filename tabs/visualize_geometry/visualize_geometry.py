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
        # print(geometry.networks)
        for network in geometry.networks:
            print(network.tag)     
            for propulsor in network.propulsors: 
                print(propulsor.tag)
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

# =====================================
# RENDER SAFETY + CAMERA VIEW STABILITY
# =====================================
import functools
import types
import vtk

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

# =================================
# BACKGROUND MENU (with checkmarks)
# =================================
# UI widgets used to build the small background mode menu
from PyQt6.QtWidgets import QPushButton, QMenu, QColorDialog
from PyQt6.QtGui import QAction, QColor

class BackgroundManager:
    """Manage background mode and menu checkmarks (dark / light / custom)."""
    def __init__(self, widget):
        # keep a reference to the widget so we can access renderer & window
        self.widget = widget
        self.current_mode = "dark"  # default

    @property
    def renderer(self):
        # return the renderer if it exists, else None
        return getattr(self.widget, "renderer", None)

    @property
    def window(self):
        # return the render window so we can call Render()
        try:
            return self.widget.vtkWidget.GetRenderWindow()
        except Exception:
            return None

    def _set_mode(self, mode: str):
        """Set renderer background and update menu checkmarks."""
        r = self.renderer
        w = self.window
        if r is None or w is None:
            return

        if mode == "dark":
            r.GradientBackgroundOn()
            r.SetBackground(0.05, 0.08, 0.15)
            r.SetBackground2(0.12, 0.18, 0.28)

        elif mode == "light":
            r.GradientBackgroundOn()
            r.SetBackground(0.85, 0.90, 0.98)
            r.SetBackground2(1.0, 1.0, 1.0)

        elif mode == "custom":
            # Custom color is handled by set_custom_color() which calls _set_mode("custom")
            pass

        # update menu checkmarks if actions exist
        actions = getattr(self.widget, "_bg_actions", None) or {}
        for m, act in actions.items():
            act.setCheckable(True)
            act.setChecked(m == mode)

        # remember mode and force a redraw
        self.current_mode = mode
        w.Render()

    def set_dark_mode(self):
        # switch to dark mode
        self._set_mode("dark")

    def set_light_mode(self):
        # switch to light mode
        self._set_mode("light")

    def set_custom_color(self):
        # set a single custom background color chosen by the user
        r = self.renderer
        w = self.window
        if r is None or w is None:
            return

        # ask user for a color (default is dark)
        color = QColorDialog.getColor(QColor(20, 20, 20), self.widget, "Choose Background Color")
        if not color.isValid():
            return

        # turn off gradient and apply the chosen color
        r.GradientBackgroundOff()
        r.SetBackground(color.redF(), color.greenF(), color.blueF())

        # mark "custom" in the menu and redraw
        actions = getattr(self.widget, "_bg_actions", None) or {}
        for m, act in actions.items():
            act.setCheckable(True)
            act.setChecked(m == "custom")

        self.current_mode = "custom"
        w.Render()

def _add_background_menu(self):
    """Add Background menu once to the toolbar."""
    # require toolbar
    if not hasattr(self, "toolbar") or self.toolbar is None:
        return

    # Prevent duplicates
    if getattr(self, "_background_menu_added", False):
        return
    self._background_menu_added = True

    # create or reuse a small helper that talks to the renderer
    if not hasattr(self, "bg_manager") or self.bg_manager is None:
        self.bg_manager = BackgroundManager(self)

    # add a simple button to the toolbar
    btn = QPushButton("🌄 Background")
    self.toolbar.addSeparator()
    self.toolbar.addWidget(btn)

    # create a menu to hold actions
    menu = QMenu(btn)

    # actions for each mode
    act_dark = QAction("Dark Mode", menu)   # dark gradient
    act_light = QAction("Light Mode", menu) # light gradient
    act_custom = QAction("Custom Color…", menu) # pick solid color

    # wire actions to the manager
    act_dark.triggered.connect(self.bg_manager.set_dark_mode)
    act_light.triggered.connect(self.bg_manager.set_light_mode)
    act_custom.triggered.connect(self.bg_manager.set_custom_color)

    # keep actions on the widget so we can update checkmarks later
    # stored under `self._bg_actions` for easy access from the manager
    self._bg_actions = {"dark": act_dark, "light": act_light, "custom": act_custom}

    # make each action checkable and add it to the menu
    for act in self._bg_actions.values():
        act.setCheckable(True)
        menu.addAction(act)

    # attach the menu to the toolbar button
    btn.setMenu(menu)

    # set default mode now so the UI matches renderer
    self.bg_manager.set_dark_mode()

# Activate Patch
def _patch_update_toolbar_for_background_menu():
    """Wrap update_toolbar once so the background menu is added."""
    # don't apply more than once
    if getattr(VisualizeGeometryWidget, "_bg_update_toolbar_patched", False):
        return

    old_update_toolbar = VisualizeGeometryWidget.update_toolbar

    def wrapped_update_toolbar(self, *args, **kwargs):
        # keep original toolbar behavior
        old_update_toolbar(self, *args, **kwargs)
        # then ensure the background menu is attached (won't duplicate)
        _add_background_menu(self)  # idempotent

    VisualizeGeometryWidget.update_toolbar = wrapped_update_toolbar
    VisualizeGeometryWidget._bg_update_toolbar_patched = True

_patch_update_toolbar_for_background_menu()
# patch applied above so the background menu is ready when toolbars are built

# ===================================
# Gridline Overlay Toggle
# ===================================
# Simple grid overlay system:

from PyQt6.QtWidgets import QCheckBox
import vtk

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
    self.grid_checkbox.setStyleSheet("color:white;font-size:10pt;")

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

# =====================================
# AXES GIZMO
# =====================================
import vtk

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

# ===========================
# MEASUREMENT TOOL SECTION
# ===========================
# Purpose:
# - Adds a lightweight "distance measurement" tool to the VG toolbar.
# - User workflow:
#   1) Toggle 📏 Measure ON
#   2) Click two points in the scene
#   3) A line + endpoint markers + distance label are created
#   4) Use ↩ Undo to remove the most recent measurement, 🧹 Clear to remove all

# Design notes:
# - Uses a vtkCellPicker to pick world-space points on visible geometry.
# - Stores all state on `self._measure_state` so the tool is resilient across toolbar rebuilds.
# - Patch wraps VisualizeGeometryWidget.update_toolbar() so the buttons are re-added whenever
#   the toolbar is rebuilt/refreshed (without editing code above this patch section).

import math
import vtk
from PyQt6.QtWidgets import QPushButton


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

# ===========================
# SCREENSHOT EXPORT SECTION
# ===========================
# Adds "📷 Export View" to the toolbar and saves the current VTK view to PNG/JPG.

import datetime
import vtk
from PyQt6.QtWidgets import QPushButton, QFileDialog, QMessageBox

def add_screenshot_button(self):
    # --- need toolbar + vtkWidget ---
    if not getattr(self, "toolbar", None) or not getattr(self, "vtkWidget", None):
        return

    # --- prevents adding the button twice ---
    if getattr(self, "screenshot_button", None) is not None:
        return

    # --- add button to toolbar ---
    btn = QPushButton("📷 Export View")
    self.toolbar.addSeparator()
    self.toolbar.addWidget(btn)
    self.screenshot_button = btn

    def save_screenshot():
        # --- choose filename (default timestamp) ---
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_name = f"screenshot_{ts}.png"

        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot As",
            default_name,
            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;All Files (*)",
        )
        if not path:
            return

        # --- add extension if missing ---
        lower = path.lower()
        if not (lower.endswith(".png") or lower.endswith(".jpg") or lower.endswith(".jpeg")):
            path += ".jpg" if "JPEG" in selected_filter else ".png"

        # --- grab current render window image ---
        rw = self.vtkWidget.GetRenderWindow()
        w2i = vtk.vtkWindowToImageFilter()
        w2i.SetInput(rw)
        w2i.ReadFrontBufferOff()
        w2i.SetInputBufferTypeToRGBA()
        w2i.Update()

        # --- pick writer based on extension ---
        if path.lower().endswith((".jpg", ".jpeg")):
            writer = vtk.vtkJPEGWriter()
        else:
            writer = vtk.vtkPNGWriter()

        # --- write file ---
        writer.SetFileName(path)
        writer.SetInputConnection(w2i.GetOutputPort())

        try:
            writer.Write()
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not save screenshot:\n{e}")
            return

        QMessageBox.information(self, "Export Successful", f"Saved:\n{path}")

    # --- connect click ---
    btn.clicked.connect(save_screenshot)

# Activate Patch
def _patch_update_toolbar_for_screenshot():
    # --- patch update_toolbar to add screenshot button ---
    if getattr(VisualizeGeometryWidget, "_screenshot_update_toolbar_patched", False):
        return

    old_update_toolbar = VisualizeGeometryWidget.update_toolbar

    def wrapped_update_toolbar(self, *args, **kwargs):
        old_update_toolbar(self, *args, **kwargs)
        add_screenshot_button(self)

    VisualizeGeometryWidget.update_toolbar = wrapped_update_toolbar
    VisualizeGeometryWidget._screenshot_update_toolbar_patched = True

_patch_update_toolbar_for_screenshot()

# ==========================
# BLUEPRINT UPLOAD SYSTEM
# ==========================
# Loads 2D blueprint images (top/side/front) as textured planes around the model.
# Click a blueprint to select it (highlights with an outline).

from PyQt6.QtWidgets import QPushButton, QFileDialog, QMenu
from PyQt6.QtCore import QTimer
import vtk, os

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

# ===========================
# BLUEPRINT ADJUSTOR DROPDOWN
# ===========================
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

# =========================================
# AIRCRAFT DRAG (Move Entire Model)
# =========================================
# Adds a "✈️ Drag Aircraft" toggle button to the toolbar.
# When enabled, lets the user click and drag to move the entire aircraft model.
import vtk
from PyQt6.QtWidgets import QPushButton

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
            "Nacelles": getattr(self, "nacelle_actors", None),
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