from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QHeaderView, QLabel
from PyQt6.QtCore import Qt

from tabs import TabWidget


class SolveWidget(TabWidget):
    def __init__(self):
        super(SolveWidget, self).__init__()

        base_layout = QHBoxLayout()
        tree_layout = QVBoxLayout()
        main_layout = QVBoxLayout()
        
        main_layout.addWidget(QLabel("Click Solve Button to View Plots"))

        solve_button = QPushButton("Solve")
        # noinspection PyUnresolvedReferences
        solve_button.clicked.connect(self.run_solve)

        self.tree = QTreeWidget()
        self.init_tree()
        tree_layout.addWidget(solve_button)
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
