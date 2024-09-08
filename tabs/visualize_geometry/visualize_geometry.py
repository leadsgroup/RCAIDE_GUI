import RCAIDE
from RCAIDE.Framework.Core import Units , Data        
from RCAIDE.Library.Methods.Propulsors.Turbofan_Propulsor                      import design_turbofan
from RCAIDE.Library.Methods.Stability.Center_of_Gravity                        import compute_component_centers_of_gravity 
from RCAIDE.Library.Plots.Geometry.plot_3d_fuselage                            import generate_3d_fuselage_points   
from RCAIDE.Library.Methods.Propulsors.Turbojet_Propulsor                      import design_turbojet   
from RCAIDE.Framework.Networks.Electric                                        import Electric 
from RCAIDE.Library.Methods.Geometry.Planform                                  import segment_properties,wing_segmented_planform    
from RCAIDE.Library.Methods.Energy.Sources.Batteries.Common                    import initialize_from_circuit_configuration 
from RCAIDE.Library.Methods.Weights.Correlation_Buildups.Propulsion            import nasa_motor
from RCAIDE.Library.Methods.Propulsors.Converters.DC_Motor                     import design_motor
from RCAIDE.Library.Methods.Propulsors.Converters.Rotor                        import design_propeller ,design_lift_rotor 
from RCAIDE.Library.Methods.Weights.Physics_Based_Buildups.Electric            import compute_weight , converge_weight 
from RCAIDE.Library.Plots                                                      import *       
from RCAIDE.Library.Plots                                                      import *  
from RCAIDE.Library.Plots     import *     


from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QHeaderView, QLabel
from PyQt6.QtCore import Qt
from tabs import TabWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
from tabs.visualize_geometry import concorde, b737, b777, atr72, evtol # Import both VTK visualizers


class CustomInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, parent=None):
        super().__init__()
        self.AddObserver("KeyPressEvent", self.on_key_press)

    def on_key_press(self, obj, event):
        key = self.GetInteractor().GetKeySym()
        camera = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer().GetActiveCamera()

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

        self.label = QLabel("Click Display Button to View VTK")
        main_layout.addWidget(self.label)

        solve_button = QPushButton("Display")
        solve_button.clicked.connect(self.run_solve)

        self.tree = QTreeWidget()
        self.init_tree()
        tree_layout.addWidget(solve_button)
        tree_layout.addWidget(self.tree)

        base_layout.addLayout(tree_layout, 3)
        base_layout.addLayout(main_layout, 7)

        # Creating VTK widget container
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        #self.vtkWidget.setStyleSheet("background-color: darkgrey;")  # Set the background color
        main_layout.addWidget(self.vtkWidget)

        base_widget = QWidget()
        base_widget.setLayout(base_layout)

        self.setLayout(base_layout)

        # Store selected option
        self.selected_option = None

    def init_tree(self):
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["Plot Options"])
        self.tree.header().setSectionResizeMode(
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
        # Check if an option is selected
        if self.selected_option:
            if self.selected_option == "Concorde":
                self.display_concorde_vtk()  # Display Concorde VTK graph
            elif self.selected_option == "Boeing 737":
                self.display_boeing737_vtk()  # Display Boeing 737 VTK graph    
            elif self.selected_option == "Boeing 777":
                self.display_boeing777_vtk()
            elif self.selected_option == "ATR 72":
                self.display_atr72_vtk()
            elif self.selected_option == "Default EVTOL":
                self.display_evtol_vtk()
            else:
                self.label.setText("Please select an option")

    def display_concorde_vtk(self):
        # Create a VTK renderer and set it to the QVTK widget
        renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(renderer)
        render_window_interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

        # Set up the Concorde vehicle visualization
        vehicle = concorde.Concorde_vehicle_setup()

        # Number of points for airfoil
        number_of_airfoil_points = 21

        # Plot wings
        for wing in vehicle.wings:
            n_segments = len(wing.Segments)
            dim = n_segments if n_segments > 0 else 2
            GEOM = concorde.generate_3d_wing_points(wing, number_of_airfoil_points, dim)
            actor = concorde.generate_vtk_object(GEOM.PTS)
            
            # Set color for wings (main and vertical)
            mapper = actor.GetMapper()
            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
            actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set wing color to Light Grey
            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
            renderer.AddActor(actor)

            if wing.symmetric:
                if wing.vertical:
                    GEOM.PTS[:, :, 2] = -GEOM.PTS[:, :, 2]
                else:
                    GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                actor = concorde.generate_vtk_object(GEOM.PTS)
                
                    
                # Set color for wings (symmetric)
                mapper = actor.GetMapper()
                mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
                actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set symmetric wing color to Light Grey
                actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
                renderer.AddActor(actor)

        # Plot fuselage
        for fuselage in vehicle.fuselages:
            GEOM = concorde.generate_3d_fuselage_points(fuselage, tessellation=30)
            actor = concorde.generate_vtk_object(GEOM.PTS)
            
            # Set color of fuselage
            mapper = actor.GetMapper()
            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
            actor.GetProperty().SetColor(0.392, 0.584, 0.929)  # Set fuselage color to Cornflower Blue
            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
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

    def display_boeing737_vtk(self):
        # Create a VTK renderer and set it to the QVTK widget
        renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(renderer)
        render_window_interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

        # Set up the Boeing 737 vehicle visualization
        vehicle = b737.B737_vehicle_setup()

        # Number of points for airfoil
        number_of_airfoil_points = 21

        # Plot wings
        for wing in vehicle.wings:
            n_segments = len(wing.Segments)
            dim = n_segments if n_segments > 0 else 2
            GEOM = b737.generate_3d_wing_points(wing, number_of_airfoil_points, dim)
            actor = b737.generate_vtk_object(GEOM.PTS)

            # Set color of wings (main and vertical)
            mapper = actor.GetMapper()
            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
            actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set wing color to Light Grey
            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
            renderer.AddActor(actor)

            if wing.symmetric:
                if wing.vertical:
                    GEOM.PTS[:, :, 2] = -GEOM.PTS[:, :, 2]
                else:
                    GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                actor = b737.generate_vtk_object(GEOM.PTS)

                # Set color for wings (symmetric)
                mapper = actor.GetMapper()
                mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
                actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set symmetric wing color to Light Grey
                actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
                renderer.AddActor(actor)

        # Plot fuselage
        for fuselage in vehicle.fuselages:
            GEOM = b737.generate_3d_fuselage_points(fuselage, tessellation=30)
            actor = b737.generate_vtk_object(GEOM.PTS)

            # Set color to Cornflower Blue
            mapper = actor.GetMapper()
            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
            actor.GetProperty().SetColor(0.392, 0.584, 0.929)  # Set fuselage color to Cornflower Blue
            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
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

    def display_boeing777_vtk(self):
        # Create a VTK renderer and set it to the QVTK widget
        renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(renderer)
        render_window_interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

        # Set up the Boeing 737 vehicle visualization
        vehicle = b777.B777_vehicle_setup()

        # Number of points for airfoil
        number_of_airfoil_points = 21

        # Plot wings
        for wing in vehicle.wings:
            n_segments = len(wing.Segments)
            dim = n_segments if n_segments > 0 else 2
            GEOM = b737.generate_3d_wing_points(wing, number_of_airfoil_points, dim)
            actor = b737.generate_vtk_object(GEOM.PTS)

            # Set color for wings (main and vertical)
            mapper = actor.GetMapper()
            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
            actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set wing color to Light Grey
            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
            renderer.AddActor(actor)

            if wing.symmetric:
                if wing.vertical:
                    GEOM.PTS[:, :, 2] = -GEOM.PTS[:, :, 2]
                else:
                    GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                actor = b777.generate_vtk_object(GEOM.PTS)

                # Set color for wings (symmetric)
                mapper = actor.GetMapper()
                mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
                actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set symmetric wing color to Light Grey
                actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
                renderer.AddActor(actor)

        # Plot fuselage
        for fuselage in vehicle.fuselages:
            GEOM = b777.generate_3d_fuselage_points(fuselage, tessellation=30)
            actor = b777.generate_vtk_object(GEOM.PTS)

            # Set color for fuselage
            mapper = actor.GetMapper()
            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
            actor.GetProperty().SetColor(0.392, 0.584, 0.929)  # Set fuselage color to Cornflower Blue
            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
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


    def display_atr72_vtk(self):
        # Create a VTK renderer and set it to the QVTK widget
        renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(renderer)
        render_window_interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

        # Set up the Boeing 737 vehicle visualization
        vehicle = atr72.ATR_72_vehicle_setup()

        # Number of points for airfoil
        number_of_airfoil_points = 21

        # Plot wings
        for wing in vehicle.wings:
            n_segments = len(wing.Segments)
            dim = n_segments if n_segments > 0 else 2
            GEOM = atr72.generate_3d_wing_points(wing, number_of_airfoil_points, dim)
            actor = atr72.generate_vtk_object(GEOM.PTS)

            # Set color for wings (main and vertical)
            mapper = actor.GetMapper()
            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
            actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set wing color to Light Grey
            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
            renderer.AddActor(actor)

            if wing.symmetric:
                if wing.vertical:
                    GEOM.PTS[:, :, 2] = -GEOM.PTS[:, :, 2]
                else:
                    GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                actor = b777.generate_vtk_object(GEOM.PTS)

                # Set color for wings (symmetric)
                mapper = actor.GetMapper()
                mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
                actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set symmetric wing color to Light Grey
                actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
                renderer.AddActor(actor)

        # Plot fuselage
        for fuselage in vehicle.fuselages:
            GEOM = atr72.generate_3d_fuselage_points(fuselage, tessellation=30)
            actor = atr72.generate_vtk_object(GEOM.PTS)

            # Set color for fuselage
            mapper = actor.GetMapper()
            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
            actor.GetProperty().SetColor(0.392, 0.584, 0.929)  # Set fuselage color to Cornflower Blue
            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
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
   
    def display_evtol_vtk(self):
        # Create a VTK renderer and set it to the QVTK widget
        renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(renderer)
        render_window_interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

        # Set up the Boeing 737 vehicle visualization
        vehicle = evtol.EVTOL_vehicle_setup()

        # Number of points for airfoil
        number_of_airfoil_points = 21

        # Plot wings
        for wing in vehicle.wings:
            n_segments = len(wing.Segments)
            dim = n_segments if n_segments > 0 else 2
            GEOM = evtol.generate_3d_wing_points(wing, number_of_airfoil_points, dim)
            actor = evtol.generate_vtk_object(GEOM.PTS)

            # Set color for wings (main and vertical)
            mapper = actor.GetMapper()
            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
            actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set wing color to Light Grey
            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
            renderer.AddActor(actor)

            if wing.symmetric:
                if wing.vertical:
                    GEOM.PTS[:, :, 2] = -GEOM.PTS[:, :, 2]
                else:
                    GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                actor = b777.generate_vtk_object(GEOM.PTS)

                # Set color for wings (symmetric)
                mapper = actor.GetMapper()
                mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
                actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set symmetric wing color to Light Grey
                actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
                renderer.AddActor(actor)

        # Plot fuselage
        for fuselage in vehicle.fuselages:
            GEOM = evtol.generate_3d_fuselage_points(fuselage, tessellation=24)
            actor = evtol.generate_vtk_object(GEOM.PTS)

            # Set color of fuselage
            mapper = actor.GetMapper()
            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
            actor.GetProperty().SetColor(0.25, 0.25, 0.25)  # Set fuselage color to Dark Grey
            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
            renderer.AddActor(actor)

        # -------------------------------------------------------------------------
        # PLOT BOOMS
        # ------------------------------------------------------------------------- 
        for boom in vehicle.booms:
            GEOM = evtol.generate_3d_fuselage_points(boom,tessellation = 24 )
            actor = evtol.generate_vtk_object(GEOM.PTS)
            
            # Set color of booms
            mapper = actor.GetMapper()
            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
            actor.GetProperty().SetColor(0.392, 0.584, 0.929)  # Set boom color to Cornflower Blue
            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection            
            renderer.AddActor(actor)            
            
        # -------------------------------------------------------------------------
        # PLOT ROTORS
        # ------------------------------------------------------------------------- 
        number_of_airfoil_points = 11
        for network in vehicle.networks:
        
            if 'busses' in network:  
                for bus in network.busses:
                    for propulsor in bus.propulsors: 
                        number_of_airfoil_points = 21
                        tessellation             = 24
                        if 'nacelle' in propulsor:

                            nacelle = propulsor.nacelle                        
                            if type(nacelle) == RCAIDE.Library.Components.Nacelles.Stack_Nacelle: 
                                GEOM = evtol.generate_3d_stack_nacelle_points(nacelle,tessellation,number_of_airfoil_points)
                            elif type(nacelle) == RCAIDE.Library.Components.Nacelles.Body_of_Revolution_Nacelle: 
                                GEOM = evtol.generate_3d_BOR_nacelle_points(nacelle,tessellation,number_of_airfoil_points)
                            else:
                                GEOM = evtol.generate_3d_basic_nacelle_points(nacelle,tessellation,number_of_airfoil_points) 
                            actor = evtol.generate_vtk_object(GEOM.PTS)

                            # Set color of nacelles
                            mapper = actor.GetMapper()
                            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
                            actor.GetProperty().SetColor(0.392, 0.584, 0.929)  # Set fuselage color to Cornflower Blue
                            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection                            
                            renderer.AddActor(actor)
                            
                        if 'rotor' in propulsor: 
                            num_B     = propulsor.rotor.number_of_blades  
                            dim       = len(propulsor.rotor.radius_distribution) 
                            for i in range(num_B):
                                GEOM = evtol.generate_3d_blade_points(propulsor.rotor,number_of_airfoil_points,dim,i) 
                                actor = evtol.generate_vtk_object(GEOM.PTS[0])

                                # Set color of rotors
                                mapper = actor.GetMapper()
                                mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
                                actor.GetProperty().SetColor(0.392, 0.584, 0.929)  # Set fuselage color to Cornflower Blue
                                actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                                actor.GetProperty().SetSpecular(0.0)  # Set specular reflection                                
                                renderer.AddActor(actor)  
                                
                        if 'propeller' in propulsor:
                            num_B     = propulsor.propeller.number_of_blades  
                            dim       = len(propulsor.propeller.radius_distribution) 
                            for i in range(num_B):
                                GEOM = evtol.generate_3d_blade_points(propulsor.propeller,number_of_airfoil_points,dim,i)
                                actor = evtol.generate_vtk_object(GEOM.PTS[0])

                                # Set color of propellers
                                mapper = actor.GetMapper()
                                mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
                                actor.GetProperty().SetColor(0.392, 0.584, 0.929)  # Set fuselage color to Cornflower Blue
                                actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                                actor.GetProperty().SetSpecular(0.0)  # Set specular reflection                                
                                renderer.AddActor(actor)   
         
            if 'fuel_lines' in network:  
                for fuel_line in network.fuel_lines:
                    for propulsor in fuel_line.propulsors: 
                        number_of_airfoil_points = 21
                        tessellation             = 24
                        if 'nacelle' in propulsor:
                            nacelle = propulsor.nacelle
                            if type(nacelle) == RCAIDE.Library.Components.Nacelles.Stack_Nacelle: 
                                GEOM = evtol.generate_3d_stack_nacelle_points(nacelle,tessellation,number_of_airfoil_points)
                            elif type(nacelle) == RCAIDE.Library.Components.Nacelles.Body_of_Revolution_Nacelle: 
                                GEOM = evtol.generate_3d_BOR_nacelle_points(nacelle,tessellation,number_of_airfoil_points)
                            else:
                                GEOM = evtol.generate_3d_basic_nacelle_points(nacelle,tessellation,number_of_airfoil_points)
                            actor = evtol.generate_vtk_object(GEOM.PTS)

                            # Set color of nacelles
                            mapper = actor.GetMapper()
                            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
                            actor.GetProperty().SetColor(0.392, 0.584, 0.929)  # Set fuselage color to Cornflower Blue
                            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection                            
                            renderer.AddActor(actor) 

                        if 'rotor' in propulsor: 
                            num_B     = propulsor.rotor.number_of_blades  
                            dim       = len(propulsor.rotor.radius_distribution) 
                            for i in range(num_B):
                                GEOM = evtol.generate_3d_blade_points(propulsor.rotor,number_of_airfoil_points,dim,i)
                                actor = evtol.generate_vtk_object(GEOM.PTS[0])

                                # Set color of rotors
                                mapper = actor.GetMapper()
                                mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
                                actor.GetProperty().SetColor(0.392, 0.584, 0.929)  # Set fuselage color to Cornflower Blue
                                actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                                actor.GetProperty().SetSpecular(0.0)  # Set specular reflection                                
                                renderer.AddActor(actor) 

                        if 'propeller' in propulsor:
                            num_B     = propulsor.propeller.number_of_blades  
                            dim       = len(propulsor.propeller.radius_distribution) 
                            for i in range(num_B):
                                GEOM = evtol.generate_3d_blade_points(propulsor.propeller,number_of_airfoil_points,dim,i)
                                actor = evtol.generate_vtk_object(GEOM.PTS[0])

                                # Set color of propellers
                                mapper = actor.GetMapper()
                                mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
                                actor.GetProperty().SetColor(0.392, 0.584, 0.929)  # Set fuselage color to Cornflower Blue
                                actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                                actor.GetProperty().SetSpecular(0.0)  # Set specular reflection                                
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
   
    plot_options = {
        "Pre Built": [
            "Concorde",
            "Boeing 737",
            "Boeing 777",
            "ATR 72",
            "Default EVTOL"
        ],
        "Custom": [
            "EX1",
            "EX2",
            "EX3",
        ],
    }


def get_widget() -> QWidget:
    return VisualizeGeometryWidget()
