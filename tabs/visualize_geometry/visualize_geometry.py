import RCAIDE
from RCAIDE.Framework.Core import Units
from RCAIDE.Library.Plots.Geometry.generate_3d_wing_points      import *
from RCAIDE.Library.Plots.Geometry.generate_3d_fuselage_points  import *
from RCAIDE.Library.Plots.Geometry.generate_3d_fuel_tank_points import *
from RCAIDE.Library.Plots.Geometry.plot_3d_rotor                import generate_3d_blade_points
from RCAIDE.Library.Plots.Geometry.generate_3d_nacelle_points   import *
from RCAIDE.Library.Methods.Geometry.Planform                   import  fuselage_planform, wing_planform, bwb_wing_planform , compute_fuel_volume  
from RCAIDE.Library.Methods.Geometry.LOPA                       import  compute_layout_of_passenger_accommodations 

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QHeaderView, QLabel
from tabs import TabWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
from tabs.visualize_geometry import vehicle
import matplotlib.colors as mcolors 
from copy import deepcopy
import values


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


class VisualizeGeometryWidget(TabWidget):
    def __init__(self):
        super(VisualizeGeometryWidget, self).__init__()

        base_layout = QHBoxLayout()
        tree_layout = QVBoxLayout()
        main_layout = QVBoxLayout()

        # self.label = QLabel("Click Display Button to View VTK")
        # main_layout.addWidget(self.label)

        solve_button = QPushButton("Display")
        solve_button.clicked.connect(self.run_solve)

        self.tree = QTreeWidget()
        self.init_tree()
        tree_layout.addWidget(solve_button)
        tree_layout.addWidget(self.tree)

        # base_layout.addLayout(tree_layout, 3)
        base_layout.addLayout(main_layout)

        # Creating VTK widget container
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        # self.vtkWidget.setStyleSheet("background-color: darkgrey;")  # Set the background color
        main_layout.addWidget(self.vtkWidget)

        base_widget = QWidget()
        base_widget.setLayout(base_layout)

        self.setLayout(base_layout)

        # Store selected option
        self.selected_option = None

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

        renderer.SetActiveCamera(camera)
        renderer.ResetCamera()
        renderer.SetBackground(1.0, 1.0, 1.0)  # Background color

        # Use the custom interactor style
        custom_style = CustomInteractorStyle()
        render_window_interactor.SetInteractorStyle(custom_style)

        # Start the VTK interactor
        render_window_interactor.Initialize()
        render_window_interactor.Start()

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
