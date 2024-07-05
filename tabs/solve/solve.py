from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QHeaderView
from PyQt6.QtCore import Qt


class SolveWidget(QWidget):
    def __init__(self):
        super(SolveWidget, self).__init__()

        base_layout = QHBoxLayout()
        tree_layout = QVBoxLayout()
        main_layout = QVBoxLayout()

        solve_button = QPushButton("Solve")
        solve_button.clicked.connect(self.run_solve)

        self.tree = QTreeWidget()
        self.init_tree()
        tree_layout.addWidget(self.tree)

        base_layout.addLayout(tree_layout, 3)
        base_layout.addLayout(main_layout, 7)

        base_widget = QWidget()
        base_widget.setLayout(base_layout)

        self.setLayout(base_layout)

    def init_tree(self):
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Plot Options", "Enabled"])
        self.tree.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)
        for category, options in self.plot_options.items():
            category_item = QTreeWidgetItem([category])
            self.tree.addTopLevelItem(category_item)
            for option in options:
                option_item = QTreeWidgetItem([option])
                option_item.setCheckState(1, Qt.CheckState.Checked)
                category_item.addChild(option_item)

    def run_solve(self):
        pass

    plot_options = {
        "Geometry": [
            "Plot 3D Vehicle",
            "Plot 3D Energy Network",
            "Generate 3D Vehicle Geometry Data",
            "Plot 3D Rotor",
            "Generate 3D Blade Points",
            "Plot 3D Nacelle",
            "Generate 3D Basic Nacelle Points",
            "Generate 3D BOR Nacelle Points",
            "Generate 3D Stack Nacelle Points",
            "Plot 3D Wing",
            "Generate 3D Wing Points",
            "Plot 3D Vehicle VLM Panelization",
            "Plot Airfoil",
            "Plot Rotor",
        ],
        "Aerodynamics": [
            "Plot Airfoil Boundary Layer Properties",
            "Plot Airfoil Polar Files",
            "Plot Airfoil Polars",
            "Plot Airfoil Surface Forces",
            "Plot Aerodynamic Coefficients",
            "Plot Aerodynamic Forces",
            "Plot Drag Components",
            "Plot Lift Distribution",
            "Plot Rotor Disc Inflow",
            "Plot Rotor Disc Performance",
            "Plot Rotor Performance",
            "Plot Disc and Power Loading",
            "Plot Rotor Conditions",
        ],
        "Energy": [
            "Plot Fuel Consumption",
            "Plot Altitude SFC Weight",
            "Plot Propulsor Throttles",
        ],
        "Mission": [
            "Plot Aircraft Velocities",
            "Plot Flight Conditions",
            "Plot Flight Trajectory",
        ],
        "Stability": [
            "Plot Flight Forces and Moments",
            "Plot Longitudinal Stability",
            "Plot Lateral Stability",
        ],
    }


def get_widget() -> QWidget:
    return SolveWidget()
