from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QHeaderView, QLabel
from PyQt6.QtCore import Qt
from tabs import TabWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
from tabs.visualize_geometry import concorde, b737  # Import both VTK visualizers


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
            
            # Set color to red
            mapper = actor.GetMapper()
            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
            actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set wing color to purple
            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
            renderer.AddActor(actor)

            if wing.symmetric:
                if wing.vertical:
                    GEOM.PTS[:, :, 2] = -GEOM.PTS[:, :, 2]
                else:
                    GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                actor = concorde.generate_vtk_object(GEOM.PTS)
                
                    
                # Set color to red for the symmetric part
                mapper = actor.GetMapper()
                mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
                actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set symmetric wing color to red
                actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
                renderer.AddActor(actor)

        # Plot fuselage
        for fuselage in vehicle.fuselages:
            GEOM = concorde.generate_3d_fuselage_points(fuselage, tessellation=24)
            actor = concorde.generate_vtk_object(GEOM.PTS)
            
            # Set color to green
            mapper = actor.GetMapper()
            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
            actor.GetProperty().SetColor(0.392, 0.584, 0.929)  # Set fuselage color to black
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

            # Set color to Light Gray
            mapper = actor.GetMapper()
            mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
            actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set wing color to Light Gray
            actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
            actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
            renderer.AddActor(actor)

            if wing.symmetric:
                if wing.vertical:
                    GEOM.PTS[:, :, 2] = -GEOM.PTS[:, :, 2]
                else:
                    GEOM.PTS[:, :, 1] = -GEOM.PTS[:, :, 1]
                actor = b737.generate_vtk_object(GEOM.PTS)

                # Set color to Light Gray for the symmetric part
                mapper = actor.GetMapper()
                mapper.ScalarVisibilityOff()  # Disable scalar visibility if color is set directly
                actor.GetProperty().SetColor(0.827, 0.827, 0.827)  # Set symmetric wing color to Light Gray
                actor.GetProperty().SetDiffuse(1.0)  # Set diffuse reflection
                actor.GetProperty().SetSpecular(0.0)  # Set specular reflection
                renderer.AddActor(actor)

        # Plot fuselage
        for fuselage in vehicle.fuselages:
            GEOM = b737.generate_3d_fuselage_points(fuselage, tessellation=24)
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
