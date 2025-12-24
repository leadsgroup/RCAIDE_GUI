from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QLineEdit,
    QGroupBox, QRadioButton
)

from tabs.mission.widgets.flight_controls_widget import FlightControlsWidget
from tabs.mission.widgets.mission_segment_helper import segment_data_fields, segment_rcaide_classes
from utilities import Units, set_data, convert_name
import values
import RCAIDE
from widgets import DataEntryWidget

class MissionSegmentWidget(QWidget):
    def __init__(self):
        super().__init__()

        # --- Main Layout ---
        # Root vertical layout for the entire segment widget
        self.segment_layout = QVBoxLayout()
        self.segment_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.segment_layout)

        # --- Runtime Widgets ---
        # These are created dynamically based on user selections
        self.subsegment_entry_widget = None
        self.dof_entry_widget = None
        self.flight_controls_widget = None

        # --- Dropdowns ---
        # Top-level segment type, nested subsegment type, and aircraft config
        self.top_dropdown = QComboBox()
        self.nested_dropdown = QComboBox()
        self.config_selector = QComboBox()

        # ============================================================
        # Group 1 — Specify Segment Settings
        # ============================================================
        # Container for solver and control-point related settings
        self.settings_group = QGroupBox("Specify Segment Settings")
        self.settings_group.setStyleSheet(self._box_style())
        self.settings_layout = QVBoxLayout(self.settings_group)

        # --- Control Points Row ---
        # Input for number of control points used by the solver
        cp_row = QHBoxLayout()
        cp_row.addWidget(QLabel("Number of Control Points:"))
        self.ctrl_points = QLineEdit("2")
        self.ctrl_points.setFixedWidth(70)
        self.ctrl_points.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cp_row.addWidget(self.ctrl_points)
        cp_row.addStretch(1)
        self.settings_layout.addLayout(cp_row)

        # --- Solver Selection Row ---
        # Choose between root solver and optimization-based solver
        solver_label = QLabel("Mission Solver:")
        solver_row = QHBoxLayout()
        solver_row.addWidget(solver_label)
        self.solver_root = QRadioButton("Root Solver")
        self.solver_opt = QRadioButton("Optimize Solver")
        self.solver_root.setChecked(True)
        solver_row.addWidget(self.solver_root)
        solver_row.addWidget(self.solver_opt)
        solver_row.addStretch(1)

        # Add solver controls to the settings group
        self.settings_layout.addLayout(solver_row)

        # Add settings group to the main segment layout
        self.segment_layout.addWidget(self.settings_group)

        # ============================================================
        # Group 2 — Specify Segment Details
        # ============================================================
        # Container for all segment-identifying inputs
        self.details_group = QGroupBox("Specify Segment Details")
        self.details_group.setStyleSheet(self._box_style())
        self.details_layout = QVBoxLayout(self.details_group)
        self.details_layout.setSpacing(6)
        self.details_layout.setContentsMargins(8, 6, 8, 6)

        # ------------------------------------------------------------
        # Segment Name (FULL WIDTH, STACKED)
        # ------------------------------------------------------------
        # Label and input for the user-defined segment name
        name_lbl = QLabel("Segment Name:")
        self.details_layout.addWidget(name_lbl)
        self.segment_name_input = QLineEdit()
        self.details_layout.addWidget(self.segment_name_input)

        # ------------------------------------------------------------
        # Segment Type (FULL WIDTH, STACKED)
        # ------------------------------------------------------------
        # Primary segment category selector
        stype_lbl = QLabel("Segment Type:")
        self.details_layout.addWidget(stype_lbl)

        # Populate top-level segment type dropdown
        self.top_dropdown.clear()
        self.top_dropdown.addItems([
            "Climb", "Cruise", "Descent", "Ground",
            "Single_Point", "Transition", "Vertical Flight"
        ])
        self.top_dropdown.setFixedHeight(28)
        self.details_layout.addWidget(self.top_dropdown)

        # ------------------------------------------------------------
        # Subsegment Type (FULL WIDTH, STACKED)
        # ------------------------------------------------------------
        # Secondary segment type dependent on the primary selection
        ssub_lbl = QLabel("Subsegment Type:")
        self.details_layout.addWidget(ssub_lbl)

        # Populate subsegment options based on current segment type
        self.populate_nested_dropdown(self.top_dropdown.currentIndex())
        self.nested_dropdown.setFixedHeight(28)
        self.details_layout.addWidget(self.nested_dropdown)

        # ------------------------------------------------------------
        # Aircraft Configuration (FULL WIDTH, STACKED)
        # ------------------------------------------------------------
        # Aircraft configuration selector for this segment
        cfg_lbl = QLabel("Aircraft Configuration:")
        self.details_layout.addWidget(cfg_lbl)

        # Load available configurations from shared values
        self.config_selector.addItems([c["config name"] for c in values.config_data])
        self.config_selector.setFixedHeight(28)
        self.details_layout.addWidget(self.config_selector)

        # Initialize dynamic fields tied to the selected subsegment
        self.update_subsegment_fields()

        # Add the details group to the main segment layout
        self.segment_layout.addWidget(self.details_group)

        # ============================================================
        # Group 3 — Degrees of Freedom Selection
        # ============================================================
        # Container for selecting which degrees of freedom are active
        self.dof_group = QGroupBox("Select Degrees of Freedom")
        self.dof_group.setStyleSheet(self._box_style())
        dof_layout = QVBoxLayout(self.dof_group)

        # List of DOF fields mapped to RCAIDE flight dynamics variables
        dof_fields = [
            ("Forces in X axis", Units.Boolean, "flight_dynamics.force_x"),
            ("Moments about X axis", Units.Boolean, "flight_dynamics.moment_x"),
            ("Forces in Y axis", Units.Boolean, "flight_dynamics.force_y"),
            ("Moments about Y axis", Units.Boolean, "flight_dynamics.moment_y"),
            ("Forces in Z axis", Units.Boolean, "flight_dynamics.force_z"),
            ("Moments about Z axis", Units.Boolean, "flight_dynamics.moment_z"),
        ]

        # Widget that renders DOF checkboxes
        self.dof_entry_widget = DataEntryWidget(dof_fields)
        dof_layout.addWidget(self.dof_entry_widget)
        self.segment_layout.addWidget(self.dof_group)

        # ============================================================
        # Group 4 - Flight Controls
        # ============================================================
        # Container for selecting flight control inputs
        self.fc_group = QGroupBox("Select Flight Controls")
        self.fc_group.setStyleSheet(self._box_style())
        fc_layout = QVBoxLayout(self.fc_group)

        # Widget that handles flight control toggles
        self.flight_controls_widget = FlightControlsWidget()
        fc_layout.addWidget(self.flight_controls_widget)
        self.segment_layout.addWidget(self.fc_group)

        # --- Signals ---
        # Update subsegment options when segment type changes
        self.top_dropdown.currentIndexChanged.connect(self._on_top_dropdown_change)

        # Update dynamic fields when subsegment type changes
        self.nested_dropdown.currentIndexChanged.connect(self.update_subsegment_fields)

    # ============================================================
    # Group box shared styling
    # ============================================================
    def _box_style(self):
        # Common stylesheet applied to all group boxes
        return """
        QGroupBox {
            color:#cfe0ff;
            font-weight:600;
            border:1px solid #2d3a4e;
            border-radius:6px;
            padding:6px;
            margin-bottom:6px;
        }
        """
    # ============================================================
    # Dropdown Handlers
    # ============================================================
    def _on_top_dropdown_change(self, idx):
        # Update available subsegment types
        self.populate_nested_dropdown(idx)

        # Refresh dynamic fields tied to subsegment selection
        self.update_subsegment_fields()

    def populate_nested_dropdown(self, index):
        # Clear existing subsegment options
        self.nested_dropdown.clear()

        # Populate subsegment options based on selected segment type
        self.nested_dropdown.addItems(list(segment_data_fields[index].keys()))

    # ============================================================
    # Update Subsegment Fields
    # ============================================================
    def update_subsegment_fields(self):
        # Remove existing dynamic subsegment fields if present
        if self.subsegment_entry_widget:
            self.subsegment_entry_widget.setParent(None)
            self.subsegment_entry_widget = None

        # Get current segment and subsegment selection
        top = self.top_dropdown.currentIndex()
        sub = self.nested_dropdown.currentText()

        # Exit if no subsegment is selected
        if sub == "":
            return

        # Retrieve field definitions for the selected subsegment
        data_fields = segment_data_fields[top][sub]

        # Create new dynamic data entry widget
        self.subsegment_entry_widget = DataEntryWidget(data_fields)
        self.details_layout.addWidget(self.subsegment_entry_widget)

    # ============================================================
    # Save Data
    # ============================================================
    def get_data(self):
        # Collect all user-defined segment data into a dictionary
        data = {
            "Segment Name": self.segment_name_input.text(),
            "top dropdown": self.top_dropdown.currentIndex(),
            "nested dropdown": self.nested_dropdown.currentText(),
            "config": self.config_selector.currentIndex(),
            "Control Points": int(self.ctrl_points.text()),
            "Solver": "root" if self.solver_root.isChecked() else "optimize",
            "flight forces": self.dof_entry_widget.get_values(),
            "flight controls": self.flight_controls_widget.get_data(),
        }

        # Merge dynamic subsegment-specific fields
        data.update(self.subsegment_entry_widget.get_values())

        # Return raw data and the generated RCAIDE segment
        return data, self.create_rcaide_segment()

    # ============================================================
    # Load Data
    # ============================================================
    def load_data(self, data):
        # Restore segment name
        self.segment_name_input.setText(data["Segment Name"])

        # Restore segment type dropdown
        self.top_dropdown.setCurrentIndex(data["top dropdown"])

        # Repopulate and restore subsegment dropdown
        self.populate_nested_dropdown(data["top dropdown"])
        self.nested_dropdown.setCurrentText(data["nested dropdown"])

        # Restore aircraft configuration selection
        self.config_selector.setCurrentIndex(data["config"])

        # Restore control points (default to 2 if missing)
        self.ctrl_points.setText(str(data.get("Control Points", 2)))

        # Restore solver selection
        if data.get("Solver", "root") == "root":
            self.solver_root.setChecked(True)
        else:
            self.solver_opt.setChecked(True)

        # Rebuild dynamic subsegment fields
        self.update_subsegment_fields()

        # Load saved values into dynamic subsegment fields
        self.subsegment_entry_widget.load_data(data)

        # Load degrees-of-freedom selections
        self.dof_entry_widget.load_data(data["flight forces"])

        # Load flight control selections
        self.flight_controls_widget.load_data(data["flight controls"])

    # ============================================================
    # Rcaide Segment Creation
    # ============================================================
    def create_rcaide_segment(self):
        # Determine selected segment and subsegment types
        top = self.top_dropdown.currentIndex()
        sub = self.nested_dropdown.currentText()

        # Instantiate the corresponding RCAIDE segment class
        seg = segment_rcaide_classes[top][sub]()
        seg.tag = self.segment_name_input.text()

        # --- Apply subsegment parameters (SI units) ---
        vals_si = self.subsegment_entry_widget.get_values_si()
        for label, _, rcaide_label in self.subsegment_entry_widget.data_units_labels:
            set_data(seg, rcaide_label, vals_si[label][0])

        # --- Apply degree-of-freedom settings ---
        dof_vals = self.dof_entry_widget.get_values()
        for label, _, rcaide_label in self.dof_entry_widget.data_units_labels:
            set_data(seg, rcaide_label, dof_vals[label][0])

        # Apply flight control variables to the RCAIDE segment
        self.flight_controls_widget.set_control_variables(seg)

        # Resolve selected aircraft configuration
        cfg = convert_name(self.config_selector.currentText())

        # Retrieve or create analyses container for this configuration
        analyses = values.rcaide_analyses.get(cfg)
        if analyses is None:
            analyses = RCAIDE.Framework.Analyses.Vehicle()
            values.rcaide_analyses[cfg] = analyses

        # Attach analyses to the segment
        seg.analyses.extend(analyses)

        # Set number of control points
        seg.control_points = int(self.ctrl_points.text())

        # Return fully constructed RCAIDE segment
        return seg