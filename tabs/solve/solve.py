# RCAIDE_GUI/tabs/solve/solve.py
# 
# Created: Oct 2024, Laboratory for Electric Aircraft Design and Sustainabiltiy

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ---------------------------------------------------------------------------------------------------------------------- 
from RCAIDE.Framework.Core import Units,  Data 
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QHeaderView, QLabel, QScrollArea
from PyQt6.QtCore import Qt, QSize
import pyqtgraph as pg

# numpy imports 
import numpy as np
import matplotlib.cm as cm

# gui imports 
from tabs import TabWidget
from .plots.create_plot_widgets import create_plot_widgets
from .plots import  *  
import values

# ----------------------------------------------------------------------------------------------------------------------
#  SolveWidget
# ----------------------------------------------------------------------------------------------------------------------  

class SolveWidget(TabWidget):
    def __init__(self):
        super(SolveWidget, self).__init__()

        base_layout = QHBoxLayout()
        tree_layout = QVBoxLayout()
        main_layout = QVBoxLayout()

        # Create and add a label to the main_layout
        status_label = QLabel("Mission Plots")
        status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        status_label.setFixedHeight(24)
        status_label.setStyleSheet("""
        QLabel {
            color: #9fb8ff;
            background: transparent;
            padding-left: 6px;
            font-size: 18px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        """)

        main_layout.addWidget(status_label)

        solve_button = QPushButton("Simulate Mission")
        solve_button.setFixedHeight(36)
        solve_button.setCursor(Qt.CursorShape.PointingHandCursor)

        solve_button.setStyleSheet("""
        QPushButton {
            /* Bold blue surface */
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #1b4f8a,
                stop:1 #133a66
            );

            border: 1.6px solid #5fb0ff;
            border-radius: 10px;

            /* Inner glow + depth */
            box-shadow:
                inset 0 0 0 1px rgba(255, 255, 255, 0.10),
                inset 0 8px 14px rgba(255, 255, 255, 0.08),
                0 0 0 1px rgba(95, 176, 255, 0.35);

            padding: 7px 20px;

            /* Text */
            color: #d9ecff;
            font-size: 13.5px;
            font-weight: 700;
            letter-spacing: 0.35px;
        }

        /* Hover = high confidence */
        QPushButton:hover {
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #2a6fb5,
                stop:1 #1b4f8a
            );

            border-color: #8ccaff;
            color: #ffffff;

            box-shadow:
                inset 0 0 0 1px rgba(255, 255, 255, 0.18),
                0 0 8px rgba(95, 176, 255, 0.45);
        }

        /* Pressed = command issued */
        QPushButton:pressed {
            background-color: #0f2e4d;
            border-color: #4da3ff;

            box-shadow:
                inset 0 3px 8px rgba(0, 0, 0, 0.55);
        }
        """)

        solve_button.clicked.connect(self.run_solve)

        # Create a scroll area for the plot widgets
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        # scroll_area.setFixedSize(1500, 900)  # Set a designated scroll area size

        # Create a container widget for the plots
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)

        plot_size = QSize(700, 400)  # Set a fixed plot size
        show_legend = True
        create_plot_widgets(self,plot_layout,plot_size,show_legend) 

        scroll_area.setWidget(plot_container)

        # Add the scroll area to the main_layout
        main_layout.addWidget(scroll_area)

        # Tree layout (on the left)
        self.tree = QTreeWidget()
        self.init_tree()
        tree_layout.addWidget(solve_button)
        tree_layout.addWidget(self.tree)

        # Add layouts to the base_layout
        base_layout.addLayout(tree_layout, 3)
        base_layout.addLayout(main_layout, 7)
        self.setLayout(base_layout)

    def init_tree(self):
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Plot Options", "Enabled"])

        header = self.tree.header()
        assert header is not None
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)

        for category, options in self.plot_options.items():
            category_item = QTreeWidgetItem([category])
            self.tree.addTopLevelItem(category_item)

            for option in options:
                option_item = QTreeWidgetItem([option])
                option_item.setCheckState(
                    1, Qt.CheckState.Checked)  # Initially checked

                category_item.addChild(option_item)

    def run_solve(self):
        mission = values.rcaide_mission
        print("Commencing Mission Simulation")
        results = mission.evaluate()
        print("Completed Mission Simulation")
        
        # WE NEED TO MAKE THESE OPTIONS  
        plot_parameters                  = Data()      
        plot_parameters.line_width       = 5 
        plot_parameters.line_style       = '-'
        plot_parameters.line_colors      = cm.viridis(np.linspace(0.2,1,len(results.segments)))
        plot_parameters.marker_size      = 8
        plot_parameters.legend_font_size = 12
        plot_parameters.axis_font_size   = 14
        plot_parameters.title_font_size  = 18    
        plot_parameters.styles           = {"color": "white", "font-size": "18px"}  
        plot_parameters.markers          = ['o', 's', '^', 'X', 'd', 'v', 'P', '>','.', ',', 'o', 'v', '^', '<',\
                                            '>', '1', '2', '3', '4', '8', 's', 'p', '*', 'h'\
                                             , 'H', '+', 'x', 'D', 'd', '|', '_'] 
        plot_parameters.color            = 'black'
        plot_parameters.show_grid        = True
        plot_parameters.save_figure      = False
         
        
        # REPEAT FOR OTHER PLOTS 
        plot_aircraft_velocities_flag = True 
        if plot_aircraft_velocities_flag == True:
            plot_aircraft_velocities(self, results, plot_parameters)

    plot_options = {
        "Aerodynamics": [
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
    
# ---------------------------------------
# SolveWidget Theming and Layout Polish
# ---------------------------------------
# --- Apply dark theme to SolveWidget ---
def _apply_solve_theme(self):
    self.setStyleSheet("""
        QWidget {
            background-color: #0e141b;
            color: #d6e1ff;
            font-family: "Segoe UI", "Inter", sans-serif;
            font-size: 12px;
        }
                       
        QLabel {
            color: #d6e1ff;
        }
        QPushButton {
            background-color: #141c26;
            border: 1px solid #223044;
            border-radius: 6px;
            padding: 6px 12px;
            color: #9fb8ff;
        }
                       
        QPushButton:hover {
            background-color: #1b2635;
            border-color: #4da3ff;
        }
                       
        QPushButton:pressed {
            background-color: #223044;
        }

        QTreeWidget {
            background-color: #10161d;
            border: 1px solid #1f2a36;
            border-radius: 6px;
        }

        QTreeWidget::item {
            padding: 6px;
        }

        QTreeWidget::item:selected {
            background-color: #1c2633;
            color: #4da3ff;
        }

        QHeaderView::section {
            background-color: #0e141b;
            color: #9fb8ff;
            border: none;
            padding: 6px;
        }

        QScrollArea {
            border: none;
        }
                       
        QCheckBox {
            spacing: 8px;
        }

        QComboBox, QDoubleSpinBox {
            background-color: #141c26;
            border: 1px solid #223044;
            border-radius: 4px;
            padding: 4px;
        }
    """)

# --- Layout Polish ---
def _polish_solve_layout(self):
    layout = self.layout()
    if layout is None:
        return

    layout.setContentsMargins(14, 14, 14, 14)
    layout.setSpacing(14)

    # Left column (tree + solve button)
    if layout.count() >= 1:
        left = layout.itemAt(0).layout()
        if left:
            left.setSpacing(10)

    # Center column (plots)
    if layout.count() >= 2:
        center = layout.itemAt(1).layout()
        if center:
            center.setSpacing(12)

    # Right column (settings, if present)
    if layout.count() >= 3:
        right = layout.itemAt(2).layout()
        if right:
            right.setSpacing(12)

# --------------------------------------------------------------------------------------------------
# Graph Coloring and Styling
# --------------------------------------------------------------------------------------------------
def _apply_solve_graph_skin(self):
    """
    Apply a dark theme and styling to all pyqtgraph PlotWidgets within the SolveWidget.
    This includes background color, grid lines, axis colors, and frame styling.
    """

    for attr_name in dir(self):
        widget = getattr(self, attr_name)

        # Only affect graph containers (not plot logic or data)
        if not isinstance(widget, pg.PlotWidget):
            continue

        # Dark graph canvas
        widget.setBackground("#0e141b")
        plot_item = widget.getPlotItem()

        # Subtle grid for readability
        plot_item.showGrid(x=True, y=True, alpha=0.15)

        # Axis line + label coloring
        for axis_name in ("left", "bottom"):
            axis = plot_item.getAxis(axis_name)
            axis.setPen(pg.mkPen("#4da3ff"))
            axis.setTextPen(pg.mkPen("#9fb8ff"))

        # Frame around the graph viewport
        plot_item.getViewBox().setBorder(pg.mkPen("#1f2a36"))

# ==================================================================================================
# Plot Settings (Appearance, Save, Visibility)
# ==================================================================================================
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QDoubleSpinBox,
    QFileDialog, QColorDialog
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg
import pyqtgraph.exporters as pg_exporters

def init_plot_settings_panel(self):

    # Main vertical layout for the settings panel
    layout = QVBoxLayout()
    layout.setSpacing(8)

    # Helper function to create bold section labels
    def header(text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-weight: bold; color: white;")
        return lbl

    # Line appearance section
    layout.addWidget(header("Line Appearance"))

    # Control for adjusting line width
    layout.addWidget(QLabel("Line Width"))
    self.line_width_spin = QDoubleSpinBox()
    self.line_width_spin.setRange(0.5, 10.0)
    self.line_width_spin.setValue(2.0)
    layout.addWidget(self.line_width_spin)

    # Control for selecting line style (solid, dashed, dotted)
    layout.addWidget(QLabel("Line Style"))
    self.line_style_combo = QComboBox()
    self.line_style_combo.addItems(["Solid", "Dashed", "Dotted"])
    layout.addWidget(self.line_style_combo)

    # Button to open a color picker for the line color
    self.line_color_button = QPushButton("Select Line Color")
    layout.addWidget(self.line_color_button)

    # Marker controls section
    layout.addWidget(header("Markers"))

    # Toggle to show or hide markers on the lines
    self.marker_check = QCheckBox("Show Markers")
    layout.addWidget(self.marker_check)

    # Dropdown to select marker symbol style
    layout.addWidget(QLabel("Marker Style"))
    self.marker_style_combo = QComboBox()
    self.marker_style_combo.addItems(['o', 's', '^', 'd', 'x', '+', '*'])
    layout.addWidget(self.marker_style_combo)

    # Control for adjusting marker size
    layout.addWidget(QLabel("Marker Size"))
    self.marker_size_spin = QDoubleSpinBox()
    self.marker_size_spin.setRange(3, 20)
    self.marker_size_spin.setValue(8)
    layout.addWidget(self.marker_size_spin)

    # Axis-related controls
    layout.addWidget(header("Axes"))

    # Toggle to automatically scale axes based on data
    self.autoscale_check = QCheckBox("Autoscale Axes")
    self.autoscale_check.setChecked(True)
    layout.addWidget(self.autoscale_check)

    # Control for axis label and tick font size
    layout.addWidget(QLabel("Axis Font Size"))
    self.axis_font_spin = QDoubleSpinBox()
    self.axis_font_spin.setRange(8, 24)
    self.axis_font_spin.setValue(14)
    layout.addWidget(self.axis_font_spin)

    # Grid and legend controls
    layout.addWidget(header("Grid / Legend"))

    # Toggle to show or hide the grid
    self.grid_check = QCheckBox("Show Grid")
    self.grid_check.setChecked(True)
    layout.addWidget(self.grid_check)

    # Button to open a color picker for the grid color
    self.grid_color_button = QPushButton("Select Grid Color")
    layout.addWidget(self.grid_color_button)

    # Toggle to show or hide the legend
    self.legend_check = QCheckBox("Show Legend")
    self.legend_check.setChecked(True)
    layout.addWidget(self.legend_check)

    # Export section
    layout.addWidget(header("Export"))

    # Button to save the currently visible plot(s)
    self.save_plot_button = QPushButton("Save Visible Plot")
    self.save_plot_button.clicked.connect(self.save_current_plot)
    layout.addWidget(self.save_plot_button)

    # Push everything up and keep the panel compact
    layout.addStretch()

    # Attach the layout to the settings panel widget
    self.settings_panel.setLayout(layout)

    # Default values used when applying plot settings
    self.selected_line_color = None
    self.selected_grid_color = (150, 150, 150)

    # Wire UI changes to re-apply plot appearance settings
    self.line_width_spin.valueChanged.connect(self.apply_plot_settings)
    self.marker_size_spin.valueChanged.connect(self.apply_plot_settings)
    self.axis_font_spin.valueChanged.connect(self.apply_plot_settings)

    self.line_style_combo.currentIndexChanged.connect(self.apply_plot_settings)
    self.marker_style_combo.currentIndexChanged.connect(self.apply_plot_settings)

    self.marker_check.stateChanged.connect(self.apply_plot_settings)
    self.autoscale_check.stateChanged.connect(self.apply_plot_settings)
    self.grid_check.stateChanged.connect(self.apply_plot_settings)
    self.legend_check.stateChanged.connect(self.apply_plot_settings)

    # Open color picker dialogs for line and grid colors
    self.line_color_button.clicked.connect(self.select_line_color)
    self.grid_color_button.clicked.connect(self.select_grid_color)

# --- Line Color Selection ---
def select_line_color(self):
    # Open a color picker dialog for selecting the line color
    color = QColorDialog.getColor()

    # Only apply the color if the user selected a valid one
    if color.isValid():
        # Store the selected line color (as a hex string)
        self.selected_line_color = color.name()

        # Re-apply plot appearance settings using the new color
        self.apply_plot_settings()

# --- Grid Color Selection ---
def select_grid_color(self):
    # Open a color picker dialog for selecting the grid color
    color = QColorDialog.getColor()

    # Only apply the color if the user selected a valid one
    if color.isValid():
        # Store the selected grid color as an RGB tuple
        self.selected_grid_color = color.getRgb()[:3]

        # Re-apply plot appearance settings using the new color
        self.apply_plot_settings()

# --------------------------------------------------------------------------------------------------
#  Apply Plot Settings
# --------------------------------------------------------------------------------------------------
def apply_plot_settings(self):

    # Find all PlotWidget instances attached to this widget
    plots = [
        getattr(self, name) for name in dir(self)
        if isinstance(getattr(self, name), pg.PlotWidget)
    ]

    for plot in plots:

        # Show or hide grid lines based on the checkbox state
        plot.showGrid(
            x=self.grid_check.isChecked(),
            y=self.grid_check.isChecked(),
            alpha=0.3
        )

        # Update axis line color to match selected grid color
        plot.getAxis("bottom").setPen(self.selected_grid_color)
        plot.getAxis("left").setPen(self.selected_grid_color)

        # Autoscale axes to fit the data when enabled
        if self.autoscale_check.isChecked():
            viewbox = plot.getPlotItem().getViewBox()
            viewbox.enableAutoRange(x=True, y=True)
            viewbox.autoRange()

        # Update axis tick label font size
        font = pg.QtGui.QFont()
        font.setPointSizeF(self.axis_font_spin.value())
        plot.getAxis("bottom").setTickFont(font)
        plot.getAxis("left").setTickFont(font)

        # Show or hide the legend
        if self.legend_check.isChecked():
            if not plot.plotItem.legend:
                plot.addLegend()
            plot.plotItem.legend.show()
        else:
            if plot.plotItem.legend:
                plot.plotItem.legend.hide()

        # Apply line and marker settings to each curve in the plot
        for curve in plot.listDataItems():

            # Get the existing pen for the curve
            old_pen = curve.opts["pen"]

            # Determine line style from dropdown selection
            style = self.line_style_combo.currentText()
            if style == "Dashed":
                pen_style = Qt.PenStyle.DashLine
            elif style == "Dotted":
                pen_style = Qt.PenStyle.DotLine
            else:
                pen_style = Qt.PenStyle.SolidLine

            # Use selected color if provided, otherwise keep existing color
            color = self.selected_line_color or old_pen.color()

            # Create a new pen with updated style and width
            new_pen = pg.mkPen(
                color=color,
                width=self.line_width_spin.value(),
                style=pen_style
            )

            # Apply the new pen to the curve
            curve.setPen(new_pen)

            # Show or hide markers on the curve
            if self.marker_check.isChecked():
                curve.setSymbol(self.marker_style_combo.currentText())
                curve.setSymbolSize(self.marker_size_spin.value())
                curve.setSymbolBrush(new_pen.color())
                curve.setSymbolPen(new_pen)
            else:
                curve.setSymbol(None)

# --------------------------------------------------------------------------------------------------
#  Save Visible Plot
# --------------------------------------------------------------------------------------------------
def save_current_plot(self):
    from PyQt6.QtWidgets import QFileDialog, QApplication
    from PyQt6.QtGui import QPixmap

    # Find the widget that contains the plot layouts
    plot_container = None
    for child in self.findChildren(QWidget):
        # Heuristic: look for a widget with a layout holding multiple plots
        if child.layout() and child.layout().count() >= 4:
            plot_container = child
            break

    # Exit if no plot container was found
    if plot_container is None:
        return

    # Open a file dialog to choose where to save the image
    file_path, _ = QFileDialog.getSaveFileName(
        self,
        "Save Mission Plots",
        "mission_plots.png",
        "PNG Files (*.png)"
    )
    if not file_path:
        return

    # Ensure all plots are fully rendered before capturing
    plot_container.repaint()
    QApplication.processEvents()

    # Render the entire plot container into a single pixmap
    pixmap = QPixmap(plot_container.size())
    plot_container.render(pixmap)

    # Save the captured image to disk
    pixmap.save(file_path, "PNG")

# --------------------------------------------------------------------------------------------------
#  Plot Visibility Toggle (Tree)
# --------------------------------------------------------------------------------------------------
def toggle_plot_visibility(self, item, column):

    # Ignore category items; only act on leaf (actual plot) items
    if item.childCount() > 0:
        return

    # Determine whether the plot should be visible based on the checkbox
    visible = item.checkState(1) == Qt.CheckState.Checked

    # Convert the tree item text into a key used to match plot widget names
    plot_key = item.text(0).lower().replace(" ", "_")

    # Toggle visibility for matching PlotWidget instances
    for name in dir(self):
        widget = getattr(self, name)
        if isinstance(widget, pg.PlotWidget) and plot_key in name.lower():
            widget.setVisible(visible)

def init_plot_options_panel(self):
    # Create the container widget for plot options
    panel = QWidget()

    # Vertical layout for the panel
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(8)

    # Panel title
    title = QLabel("Plot Options")
    title.setStyleSheet("font-weight: bold; color: white;")
    layout.addWidget(title)

    # Add the plot visibility tree if it exists
    if hasattr(self, "tree"):
        layout.addWidget(self.tree)

    # Push content to the top
    layout.addStretch()

    return panel

#------------------------------------------------
# Patch SolveWidget to integrate new features 
#------------------------------------------------
# Prevents "stacked patch" recursion if the module is reloaded/imported twice.
if not getattr(SolveWidget, "_LEADS_PATCHED", False):
    SolveWidget._LEADS_PATCHED = True
    _SOLVEWIDGET_BASE_INIT = SolveWidget.__init__

    def _solvewidget_init(self, *args, **kwargs):
        # Run the original SolveWidget initialization
        _SOLVEWIDGET_BASE_INIT(self, *args, **kwargs)

        # Apply Solve tab UI theme + spacing + plot skin
        _apply_solve_theme(self)
        _polish_solve_layout(self)
        _apply_solve_graph_skin(self)

        # Create the plot settings panel (fixed width)
        self.settings_panel = QWidget()
        self.settings_panel.setFixedWidth(280)

        # Add the settings panel as a 3rd column in the root layout
        layout = self.layout()
        if layout is not None:
            layout.addWidget(self.settings_panel)

            # Reorder columns so: [settings_panel | plots | plot_options(tree)]
            if layout.count() >= 3:
                left_item   = layout.takeAt(0)  # tree
                center_item = layout.takeAt(0)  # graphs
                right_item  = layout.takeAt(0)  # settings

                layout.addItem(right_item)      # settings on left
                layout.addItem(center_item)     # graphs in middle
                layout.addItem(left_item)       # plot options tree on right

                # Middle expands; sides stay compact
                layout.setStretch(0, 1)
                layout.setStretch(1, 4)
                layout.setStretch(2, 2)

        # Build the settings UI into the panel
        init_plot_settings_panel(self)

        # Wire the tree checkbox to visibility toggles
        if hasattr(self, "tree"):
            self.tree.itemChanged.connect(self.toggle_plot_visibility)

    # Replace SolveWidget.__init__ with the extended version
    SolveWidget.__init__ = _solvewidget_init

    # Attach helper methods to SolveWidget 
    SolveWidget.apply_plot_settings      = apply_plot_settings
    SolveWidget.save_current_plot        = save_current_plot
    SolveWidget.toggle_plot_visibility   = toggle_plot_visibility
    SolveWidget.select_line_color        = select_line_color
    SolveWidget.select_grid_color        = select_grid_color
    SolveWidget.init_plot_options_panel  = init_plot_options_panel  # optional utility

def get_widget() -> QWidget:
    # Factory used by the tab system to construct the SolveWidget
    return SolveWidget()
