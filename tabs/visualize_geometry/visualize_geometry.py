import RCAIDE
from RCAIDE.Library.Plots import  * 
from RCAIDE.Library.Methods.Geometry.Planform           import  fuselage_planform, wing_planform, bwb_wing_planform , compute_fuel_volume  
from RCAIDE.Library.Methods.Geometry.LOPA               import  compute_layout_of_passenger_accommodations 

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QHeaderView, QLabel
from tabs import TabWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
from tabs.visualize_geometry import vehicle

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
        renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(renderer)
        render_window_interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

        # Number of points for airfoil
        number_of_airfoil_points = 155
        
        
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
            dim = n_segments if n_segments > 0 else 2
            GEOM = generate_3d_wing_points(wing, number_of_airfoil_points, dim)
            actor = vehicle.generate_vtk_object(GEOM.PTS)

            # Set color for wings (main and vertical)
            mapper = actor.GetMapper()
            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
            actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set wing color to Light Grey
            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
            actor.GetProperty().SetOpacity(1.0)
            renderer.AddActor(actor)

            if wing.symmetric:
                if wing.vertical:
                    GEOM.PTS[:, :, 2] = -GEOM.PTS[:, :, 2]
                else:
                    GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                actor = vehicle.generate_vtk_object(GEOM.PTS)

                # Set color for wings (symmetric)
                mapper = actor.GetMapper()
                mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
                # Set symmetric wing color to Light Grey
                actor.GetProperty().SetColor(0.827, 0.827, 0.827)
                actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
                actor.GetProperty().SetOpacity(1.0)
                renderer.AddActor(actor)
        
        # -------------------------------------------------------------------------  
        # Plot fuselage
        # -------------------------------------------------------------------------  
        for fuselage in geometry.fuselages:
            GEOM = generate_3d_fuselage_points(fuselage, tessellation=200)
            actor = vehicle.generate_vtk_object(GEOM.PTS)

            # Set color of fuselage
            mapper = actor.GetMapper()
            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
            # Set fuselage color to Cornflower Blue
            actor.GetProperty().SetColor(0.392, 0.584, 0.929)
            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
            actor.GetProperty().SetOpacity(1.0)
            renderer.AddActor(actor)
    
        # -------------------------------------------------------------------------  
        # Plot Nacelle
        # -------------------------------------------------------------------------   
        for nacelle in geometry.nacelles:
            GEOM = generate_3d_BOR_nacelle_points(nacelle, tessellation=200)
            actor = vehicle.generate_vtk_object(GEOM.PTS)

            # Set color of fuselage
            mapper = actor.GetMapper()
            mapper.ScalarVisibilityOff()
            actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set wing color to Light Grey
            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
            actor.GetProperty().SetOpacity(1.0)
            renderer.AddActor(actor)
    
        # -------------------------------------------------------------------------  
        # Plot Nacelle, Rotors and Fuel Tanks 
        # ------------------------------------------------------------------------- 
        number_of_airfoil_points = 11
        for network in geometry.networks:     
            for propulsor in network.propulsors:  
                number_of_airfoil_points = 21
                tessellation             = 24
                if 'nacelle' in propulsor: 
                    if propulsor.nacelle !=  None: 
                        if type(propulsor.nacelle) == RCAIDE.Library.Components.Nacelles.Stack_Nacelle: 
                            GEOM = generate_3d_stack_nacelle_points(propulsor.nacelle,tessellation,number_of_airfoil_points)
                        elif type(propulsor.nacelle) == RCAIDE.Library.Components.Nacelles.Body_of_Revolution_Nacelle: 
                            GEOM = generate_3d_BOR_nacelle_points(propulsor.nacelle,tessellation,number_of_airfoil_points)
                        else:
                            GEOM= generate_3d_basic_nacelle_points(propulsor.nacelle,tessellation,number_of_airfoil_points)
                        actor = vehicle.generate_vtk_object(GEOM.PTS)
            
                        # Set color of fuselage
                        mapper = actor.GetMapper()
                        mapper.ScalarVisibilityOff()
                        actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set wing color to Light Grey
                        actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                        actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
                        actor.GetProperty().SetOpacity(1.0)
                        renderer.AddActor(actor) 
                                                     
                if 'rotor' in propulsor:  
                    num_B     = propulsor.rotor.number_of_blades  
                    dim       = len(propulsor.rotor.radius_distribution)
                
                    for i in range(num_B):
                        GEOM = generate_3d_blade_points(propulsor.rotor,number_of_airfoil_points,dim,i)
                        actor = vehicle.generate_vtk_object(GEOM.PTS)
                    
                        # Set color of fuselage
                        mapper = actor.GetMapper()
                        mapper.ScalarVisibilityOff()
                        actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set wing color to Light Grey
                        actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                        actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
                        renderer.AddActor(actor)                         
                        
                if 'propeller' in propulsor:
                    num_B     = propulsor.propeller.number_of_blades  
                    dim       = len(propulsor.propeller.radius_distribution)
                
                    for i in range(num_B):
                        GEOM = generate_3d_blade_points(propulsor.propeller,number_of_airfoil_points,dim,i)
                        actor = vehicle.generate_vtk_object(GEOM.PTS)
                    
                        # Set color of fuselage
                        mapper = actor.GetMapper()
                        mapper.ScalarVisibilityOff()
                        actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set wing color to Light Grey
                        actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                        actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
                        actor.GetProperty().SetOpacity(1.0) 
                        renderer.AddActor(actor)     
                     
            for fuel_line in network.fuel_lines:        
                for fuel_tank in fuel_line.fuel_tanks:   
                    if fuel_tank.wing_tag != None:
                        wing = values.vehicle.wings[fuel_tank.wing_tag]
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
                                number_of_airfoil_points = 5
                                GEOM = generate_integral_wing_tank_points(wing,number_of_airfoil_points,dim,segment_list)
        
                                actor = vehicle.generate_vtk_object(GEOM.PTS)
                            
                                # Set color of fuselage
                                mapper = actor.GetMapper()
                                mapper.ScalarVisibilityOff()
                                actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set wing color to Light Grey
                                actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                                actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
                                actor.GetProperty().SetOpacity(1.0)
                                renderer.AddActor(actor)
                                
                        
                                if wing.symmetric:
                                    GEOM2 =  deepcopy(GEOM)
                                    GEOM2.YA1 *= -1
                                    GEOM2.YA2 *= -1
                                    GEOM2.YB1 *= -1
                                    GEOM2.YB2 *= -1
    
                                    actor = vehicle.generate_vtk_object(GEOM2.PTS)
                                
                                    # Set color of fuselage
                                    mapper = actor.GetMapper()
                                    mapper.ScalarVisibilityOff()
                                    actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set wing color to Light Grey
                                    actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                                    actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
                                    actor.GetProperty().SetOpacity(1.0)
                                    renderer.AddActor(actor)
                                    
                    elif fuel_tank.fuselage_tag != None:
                        fuselage = values.vehicle.fuselages[fuel_tank.fuselage_tag]
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
                                
                            GEOM  = generate_integral_fuel_tank_points(fuselage,fuel_tank, segment_list,tessellation = 24 )
                            actor = vehicle.generate_vtk_object(GEOM.PTS)
                    
                            # Set color of fuselage
                            mapper = actor.GetMapper()
                            mapper.ScalarVisibilityOff()
                            actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set wing color to Light Grey
                            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
                            actor.GetProperty().SetOpacity(1.0)
                            renderer.AddActor(actor)
                       
                    elif type(fuel_tank) == RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Non_Integral_Tank:
                        GEOM  = generate_non_integral_fuel_tank_points(fuel_tank,tessellation = 24 )  
                        actor = vehicle.generate_vtk_object(GEOM.PTS)
                    
                        # Set color of fuselage
                        mapper = actor.GetMapper()
                        mapper.ScalarVisibilityOff()
                        actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set wing color to Light Grey
                        actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                        actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
                        actor.GetProperty().SetOpacity(1.0)
                        renderer.AddActor(actor)
                        
                
                        if wing.symmetric:
                            GEOM2 =  deepcopy(GEOM)
                            GEOM2.YA1 *= -1
                            GEOM2.YA2 *= -1
                            GEOM2.YB1 *= -1
                            GEOM2.YB2 *= -1

                            actor = vehicle.generate_vtk_object(GEOM2.PTS)
                        
                            # Set color of fuselage
                            mapper = actor.GetMapper()
                            mapper.ScalarVisibilityOff()
                            actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set wing color to Light Grey
                            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
                            actor.GetProperty().SetOpacity(1.0)
                            renderer.AddActor(actor)       

        # Set camera and background
        camera = vtk.vtkCamera()
        camera.SetPosition(1, 1, 1)
        camera.SetFocalPoint(0, 0, 0)

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
