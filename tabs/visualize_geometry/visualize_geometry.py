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
import vtk
from tabs.visualize_geometry import vehicle
import matplotlib.colors as mcolors 
from copy import deepcopy
import values
import os

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
            "Wing": self.wing_actors,
            "Fuselage": self.fuselage_actors,
            "Nacelle": self.nacelle_actors
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
        
        
        renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(renderer)
        render_window_interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

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
            make_object(renderer, GEOM,wing_rgb_color,wing_opacity)
            if wing.yz_plane_symmetric: 
                GEOM.PTS[:, :, 0] = -GEOM.PTS[:, :, 0]
                make_object(renderer, GEOM,wing_rgb_color,wing_opacity)
            if wing.xz_plane_symmetric: 
                GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                make_object(renderer, GEOM,wing_rgb_color,wing_opacity)
            if wing.xy_plane_symmetric: 
                GEOM.PTS[:, :, 2] = -GEOM.PTS[:, :, 2]
                make_object(renderer, GEOM,wing_rgb_color,wing_opacity)
    
        # -------------------------------------------------------------------------  
        # Plot fuselage
        # -------------------------------------------------------------------------  
        for fuselage in geometry.fuselages:
            GEOM = generate_3d_fuselage_points(fuselage, tessellation)
            make_object(renderer, GEOM, fuselage_rgb_color,fuselage_opacity)
            
        # -------------------------------------------------------------------------  
        # Plot boom
        # -------------------------------------------------------------------------  
        for boom in geometry.booms:
            GEOM = generate_3d_fuselage_points(boom, tessellation)
            make_object(renderer, GEOM, boom_rgb_color,boom_opacity)
    
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
                        make_object(renderer, GEOM, nacelle_rgb_color,nacelle_opacity)
                        
                if 'rotor' in propulsor:  
                    rot       = propulsor.rotor
                    rot_x     = rot.orientation_euler_angles[0]
                    rot_y     = rot.orientation_euler_angles[1]
                    rot_z     = rot.orientation_euler_angles[2]
                    num_B     = int(rot.number_of_blades) 
                    if rot.radius_distribution is None:
                        make_actuator_disc(renderer, rot.hub_radius, rot.tip_radius, rot.origin, rot_x,rot_y,rot_z, rotor_rgb_color,rotor_opacity) 
                    else:
                        dim       = len(rot.radius_distribution) 
                        for i in range(num_B):
                            GEOM = generate_3d_blade_points(rot,number_of_airfoil_points,dim,i)
                            make_object(renderer, GEOM, rotor_rgb_color,rotor_opacity) 
    
                if 'propeller' in propulsor:
                    prop      = propulsor.propeller
                    rot_x     = prop.orientation_euler_angles[0]
                    rot_y     = np.pi / 2 +  prop.orientation_euler_angles[1]
                    rot_z     = prop.orientation_euler_angles[2]
                    num_B     = int(prop.number_of_blades) 
                    if prop.radius_distribution is None:
                        make_actuator_disc(renderer, prop.hub_radius, prop.tip_radius, prop.origin, rot_x,rot_y,rot_z,rotor_rgb_color,rotor_opacity) 
                    else:
                        dim       = len(prop.radius_distribution)
                        for i in range(num_B):
                            GEOM = generate_3d_blade_points(prop,number_of_airfoil_points,dim,i) 
                            make_object(renderer, GEOM, rotor_rgb_color,rotor_opacity) 
    
            for fuel_line in network.fuel_lines:        
                for fuel_tank in fuel_line.fuel_tanks:   
                    if fuel_tank.wing_tag != None:
                        wing = geometry.wings[fuel_tank.wing_tag]
                        
                        if issubclass(type(fuel_tank), RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Non_Integral_Tank):
                            GEOM  = generate_non_integral_fuel_tank_points(fuel_tank,tessellation ) 
                            make_object(renderer, GEOM,  fuel_tank_rgb_color, fuel_tank_opacity) 
        
                            if wing.xz_plane_symmetric: 
                                GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1] 
                                make_object(renderer, GEOM,  fuel_tank_rgb_color, fuel_tank_opacity)
                            
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
                                make_object(renderer, GEOM, fuel_tank_rgb_color, fuel_tank_opacity)  
                                if wing.xz_plane_symmetric:
                                    GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1] 
                                    make_object(renderer, GEOM,fuel_tank_rgb_color, fuel_tank_opacity) 
    
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
                            make_object(renderer, GEOM,  fuel_tank_rgb_color, fuel_tank_opacity) 
    
                    elif issubclass(type(fuel_tank), RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Non_Integral_Tank):
                        GEOM  = generate_non_integral_fuel_tank_points(fuel_tank,tessellation ) 
                        make_object(renderer, GEOM,  fuel_tank_rgb_color, fuel_tank_opacity) 
    
                        if wing.xz_plane_symmetric: 
                            GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1] 
                            make_object(renderer, GEOM,  fuel_tank_rgb_color, fuel_tank_opacity)         
                        
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

def make_object(renderer, GEOM,  rgb_color, opacity): 

    actor = vehicle.generate_vtk_object(GEOM.PTS)

    # Set color of fuselage
    mapper = actor.GetMapper()
    mapper.ScalarVisibilityOff()
    actor.GetProperty().SetColor(rgb_color[0], rgb_color[1], rgb_color[2])  # Set wing color to Light Grey
    actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
    actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
    actor.GetProperty().SetOpacity(opacity)
    renderer.AddActor(actor)
    
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
