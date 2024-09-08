from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QHeaderView, QLabel
from PyQt6.QtCore import Qt
import pyqtgraph as pg  # PyQtGraph for plotting
import numpy as np  # NumPy for generating data

from tabs import TabWidget


class SolveWidget(TabWidget):
    def __init__(self):
        super(SolveWidget, self).__init__()

        base_layout = QHBoxLayout()
        tree_layout = QVBoxLayout()
        main_layout = QVBoxLayout()

        # Create and add a label to the main_layout
        main_layout.addWidget(QLabel("Click Solve Button to View Plots"))

        # Create the Solve button
        solve_button = QPushButton("Solve")
        solve_button.clicked.connect(self.run_solve)

        # Create two PlotWidgets from PyQtGraph
        self.plot_widget_sine = pg.PlotWidget()  # For sine wave
        self.plot_widget_cosine = pg.PlotWidget()  # For cosine wave

        # Add legends to both plot widgets
        self.plot_widget_sine.addLegend()
        self.plot_widget_cosine.addLegend()

        # Generate some data (sine and cosine waves)
        self.x = np.linspace(0, 10, 100)
        self.y_sin = np.sin(self.x)
        self.y_cos = np.cos(self.x)

        # Initially, plot widgets are hidden
        self.plot_sine = None
        self.plot_cosine = None

        # Add the two PlotWidgets to the main_layout
        main_layout.addWidget(self.plot_widget_sine)
        main_layout.addWidget(self.plot_widget_cosine)

        # Tree layout (on the left)
        self.tree = QTreeWidget()
        self.init_tree()
        tree_layout.addWidget(solve_button)
        tree_layout.addWidget(self.tree)

        # Add layouts to the base_layout
        base_layout.addLayout(tree_layout, 3)
        base_layout.addLayout(main_layout, 7)

        base_widget = QWidget()
        base_widget.setLayout(base_layout)

        self.setLayout(base_layout)

    def init_tree(self):
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Plot Options", "Enabled"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

        for category, options in self.plot_options.items():
            category_item = QTreeWidgetItem([category])
            self.tree.addTopLevelItem(category_item)

            for option in options:
                option_item = QTreeWidgetItem([option])
                option_item.setCheckState(1, Qt.CheckState.Checked)  # Initially checked

                category_item.addChild(option_item)

                # Add callback to hide/show the sine and cosine waves based on specific plot options
                if option == "Plot Airfoil Boundary Layer Properties":
                    self.toggle_sine_plot(option_item)  # Ensure sine wave starts checked and plotted
                elif option == "Plot Airfoil Polar Files":
                    self.toggle_cosine_plot(option_item)  # Ensure cosine wave starts checked and plotted

                self.tree.itemChanged.connect(self.handle_item_change)

    def handle_item_change(self, item, column):
        """Handles toggling both the sine and cosine plots based on their respective plot options."""
        if item.text(0) == "Plot Airfoil Boundary Layer Properties":
            self.toggle_sine_plot(item)
        elif item.text(0) == "Plot Airfoil Polar Files":
            self.toggle_cosine_plot(item)

    def toggle_sine_plot(self, item):
        if item.checkState(1) == Qt.CheckState.Checked:
            if not self.plot_sine:  # Plot if it's not already plotted
                self.plot_sine = self.plot_widget_sine.plot(self.x, self.y_sin, pen='r', name="Sine Wave")
            self.plot_widget_sine.show()  # Show the sine wave plot when checked
        else:
            if self.plot_sine:
                self.plot_widget_sine.clear()  # Clear the sine wave plot when unchecked
                self.plot_sine = None  # Reset the plot_sine reference
            self.plot_widget_sine.hide()   # Hide the plot widget when unchecked

    def toggle_cosine_plot(self, item):
        if item.checkState(1) == Qt.CheckState.Checked:
            if not self.plot_cosine:  # Plot if it's not already plotted
                self.plot_cosine = self.plot_widget_cosine.plot(self.x, self.y_cos, pen='b', name="Cosine Wave")
            self.plot_widget_cosine.show()  # Show the cosine wave plot when checked
        else:
            if self.plot_cosine:
                self.plot_widget_cosine.clear()  # Clear the cosine wave plot when unchecked
                self.plot_cosine = None  # Reset the plot_cosine reference
            self.plot_widget_cosine.hide()   # Hide the plot widget when unchecked

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
