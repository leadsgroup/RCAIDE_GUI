# RCAIDE_GUI/tabs/visualize_geometry/core_3d_viewer.py

# RCAIDE imports
import RCAIDE
from RCAIDE.Framework.Core import Units
from RCAIDE.Library.Components.Airfoils import Airfoil
from RCAIDE.Library.Plots.Geometry.generate_3d_wing_points      import *
from RCAIDE.Library.Plots.Geometry.generate_3d_fuselage_points  import *
from RCAIDE.Library.Plots.Geometry.generate_3d_fuel_tank_points import *
from RCAIDE.Library.Plots.Geometry.plot_3d_rotor                import generate_3d_blade_points
from RCAIDE.Library.Plots.Geometry.generate_3d_nacelle_points   import *
from RCAIDE.Library.Methods.Geometry.Planform                   import  fuselage_planform, wing_planform , compute_fuel_volume  
from RCAIDE.Library.Methods.Geometry.LOPA                       import  compute_layout_of_passenger_accommodations 
 
 # RCAIDE-GUI imports
from tabs import TabWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from RCAIDE_GUI.tabs.visualize_geometry import geometry_helper_functions

# PyQt imports
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QHeaderView, QLabel, QToolBar, QColorDialog, QSpacerItem, QSizePolicy, QFrame, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# python imports
import matplotlib.colors as mcolors 
import vtk
import values
import os
from copy import deepcopy 

# ------------------------------------------------------------------------------
# make_object
# ------------------------------------------------------------------------------
def make_object(renderer, actor_group,  GEOM,  rgb_color, opacity): 

    actor = geometry_helper_functions.generate_vtk_object(GEOM.PTS)

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
    
    transform = vtk.vtkTransform()
    transform.RotateX(rot_x/Units.degrees)  
    transform.RotateY(rot_y/Units.degrees)  
    transform.RotateZ(rot_z/Units.degrees)  
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

class Core3DViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Setup VTK Window
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        layout.addWidget(self.vtkWidget)
        
        self.renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.render_window_interactor = self.vtkWidget.GetRenderWindow().GetInteractor()
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.render_window_interactor.SetInteractorStyle(style)
        self.wing_actors = []
        self.fuselage_actors = []
        self.boom_actors = []
        self.nacelle_actors = []
        self.rotor_actors = []
        self.fuel_tank_actors = []
        self.part_actors = [] # General list if needed

        self.render_window_interactor.Initialize()

    def clear_scene(self):
        """Wipes the 3D canvas clean before drawing a new airplane."""
        self.renderer.RemoveAllViewProps()
        self.wing_actors.clear()
        self.fuselage_actors.clear()
        self.boom_actors.clear()
        self.nacelle_actors.clear()
        self.rotor_actors.clear()
        self.fuel_tank_actors.clear()
        self.part_actors.clear()

    def run_solve(self):
        """Calculates and draws the geometry based on values.vehicle"""
        
        self.clear_scene()

        wing_color          = 'grey'  
        fuselage_color      = 'grey'  
        nacelle_color       = 'grey' 
        boom_color          = 'grey' 
        fuel_tank_color     = 'orange'  
        rotor_color         = 'black'      
        wing_opacity        = 0.5  
        fuselage_opacity    = 0.5 
        nacelle_opacity     = 1.0 
        fuel_tank_opacity   = 0.5 
        rotor_opacity       = 1.0  
        number_of_airfoil_points    = 101 
        tessellation        = 96 
        boom_opacity        = 1.0
        camera_eye_x  = -1 
        camera_eye_y  = -1 
        camera_eye_z  = 0.35  
        
        fuel_tank_rgb_color = mcolors.to_rgb(fuel_tank_color)     
        wing_rgb_color      = mcolors.to_rgb(wing_color)
        fuselage_rgb_color  = mcolors.to_rgb(fuselage_color) 
        nacelle_rgb_color   = mcolors.to_rgb(nacelle_color) 
        rotor_rgb_color     = mcolors.to_rgb(rotor_color)
        boom_rgb_color      = mcolors.to_rgb(boom_color)

        if not values.vehicle:
            return # Don't try to draw if there's no vehicle
            
        geometry = deepcopy(values.vehicle)

    
        for wing in geometry.wings:   
            try: wing_planform(wing)
            except: pass # Bypass if not fully defined yet in GUI
                             
        try: compute_fuel_volume(geometry)
        except: pass

        for fuselage in geometry.fuselages:               
            try:
                compute_layout_of_passenger_accommodations(fuselage)
                fuselage_planform(fuselage) 
            except: pass

        for wing in geometry.wings:
            n_segments = len(wing.segments)
            dim        = n_segments if n_segments > 0 else 2
            try:
                GEOM       = generate_3d_wing_points(wing, number_of_airfoil_points, dim)
                make_object(self.renderer, self.wing_actors, GEOM, wing_rgb_color, wing_opacity)
                if wing.yz_plane_symmetric: 
                    GEOM.PTS[:, :, 0] = -GEOM.PTS[:, :, 0]
                    make_object(self.renderer, self.wing_actors,GEOM,wing_rgb_color,wing_opacity)
                if wing.xz_plane_symmetric: 
                    GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                    make_object(self.renderer,self.wing_actors, GEOM,wing_rgb_color,wing_opacity)
                if wing.xy_plane_symmetric: 
                    GEOM.PTS[:, :, 2] = -GEOM.PTS[:, :, 2]
                    make_object(self.renderer,self.wing_actors, GEOM,wing_rgb_color,wing_opacity)
            except Exception as e:
                print(f"Skipping a wing due to incomplete data: {e}")
    

        for fuselage in geometry.fuselages:
            try:
                GEOM = generate_3d_fuselage_points(fuselage, tessellation)
                make_object(self.renderer, self.fuselage_actors,GEOM, fuselage_rgb_color,fuselage_opacity)
            except: pass

        for boom in geometry.booms:
            try:
                GEOM = generate_3d_fuselage_points(boom, tessellation)
                make_object(self.renderer, self.boom_actors, GEOM, boom_rgb_color,boom_opacity)
            except: pass

        for nacelle in geometry.nacelles:
            try:
                GEOM = generate_3d_BOR_nacelle_points(nacelle, tessellation=tessellation, number_of_airfoil_points=number_of_airfoil_points)
                make_object(self.renderer, self.nacelle_actors, GEOM, nacelle_rgb_color, nacelle_opacity)
            except: pass
        
        for network in geometry.networks: 
            for propulsor in network.propulsors:  
                if 'nacelle' in propulsor and propulsor.nacelle != None: 
                    try:
                        if type(propulsor.nacelle) == RCAIDE.Library.Components.Nacelles.Stack_Nacelle: 
                            GEOM = generate_3d_stack_nacelle_points(propulsor.nacelle,tessellation = tessellation,number_of_airfoil_points = number_of_airfoil_points)
                        elif type(propulsor.nacelle) == RCAIDE.Library.Components.Nacelles.Body_of_Revolution_Nacelle: 
                            GEOM = generate_3d_BOR_nacelle_points(propulsor.nacelle,tessellation = tessellation,number_of_airfoil_points = number_of_airfoil_points)
                        else:
                            GEOM= generate_3d_basic_nacelle_points(propulsor.nacelle,tessellation = tessellation,number_of_airfoil_points = number_of_airfoil_points)
                        make_object(self.renderer,self.nacelle_actors,  GEOM, nacelle_rgb_color,nacelle_opacity)
                    except: pass
                        
                if 'rotor' in propulsor:  
                    try:
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
                    except: pass
    
                if 'propeller' in propulsor:
                    try:
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
                    except: pass
    
            for fuel_line in network.fuel_lines:        
                for fuel_tank in fuel_line.fuel_tanks:   
                    try:
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
        
                                if len(wing.segments)>0: dim =  len(segment_list)
                                else: dim = 2 
        
                                if  len(segment_list) == 0 and len(wing.segments) > 0:
                                    print('Fuel tank defined on segmented wing but no segments have "tank" attribute = True') 
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
                    except: pass

        # Set camera and background
        camera = vtk.vtkCamera()
        camera.SetPosition(camera_eye_x, camera_eye_y, camera_eye_z)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 0, 1)

        self.renderer.SetActiveCamera(camera)
        self.renderer.ResetCamera()
        self.renderer.SetBackground(0.1, 0.1, 0.15)  # A nice dark theme background

        self.vtkWidget.GetRenderWindow().Render()