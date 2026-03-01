from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QLineEdit,
    QGroupBox, QRadioButton
)

from tabs.mission.widgets.flight_controls_widget import FlightControlsWidget
from tabs.mission.widgets.mission_segment_helper import (
    segment_data_fields,
    segment_rcaide_classes,
)
from utilities import Units, set_data, convert_name
import values
import RCAIDE
from widgets import DataEntryWidget


class MissionSegmentWidget(QWidget):
    def __init__(self):
        super().__init__()

        # ============================================================
        # Root Layout
        # ============================================================
        self.segment_layout = QVBoxLayout()
        self.segment_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.segment_layout)

        # Runtime widgets
        self.subsegment_entry_widget = None
        self.dof_entry_widget = None
        self.flight_controls_widget = None
        self._suppress_defaults = False

        # Dropdowns
        self.top_dropdown = QComboBox()
        self.nested_dropdown = QComboBox()
        self.config_selector = QComboBox()

        # ============================================================
        # Group 1 — Specify Segment Settings
        # ============================================================
        self.settings_group = QGroupBox("Segment Settings")
        self.settings_group.setStyleSheet(self._box_style())
        self.settings_layout = QVBoxLayout(self.settings_group) 
        
        cp_row = QHBoxLayout()
        cp_row.addWidget(QLabel("Number of Control Points:"))
        self.ctrl_points = QLineEdit("16")
        self.ctrl_points.setFixedWidth(70)
        self.ctrl_points.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cp_row.addWidget(self.ctrl_points)
        cp_row.addStretch(1)
        self.settings_layout.addLayout(cp_row)

        solver_row = QHBoxLayout()
        solver_row.addWidget(QLabel("Mission Solver:"))
        self.solver_root = QRadioButton("Root Solver")
        self.solver_opt = QRadioButton("Optimize Solver")
        self.solver_root.setChecked(True)
        solver_row.addWidget(self.solver_root)
        solver_row.addWidget(self.solver_opt)
        solver_row.addStretch(1)
        self.settings_layout.addLayout(solver_row)

        self.segment_layout.addWidget(self.settings_group)

        # ============================================================
        # Group 2 — Specify Segment Details
        # ============================================================
        self.details_group = QGroupBox("Mission Profile")
        self.details_group.setStyleSheet(self._box_style())
        self.details_layout = QVBoxLayout(self.details_group)

        self.details_layout.addWidget(QLabel("Segment Name:"))
        self.segment_name_input = QLineEdit()
        self.details_layout.addWidget(self.segment_name_input)

        self.details_layout.addWidget(QLabel("Segment Classification:"))
        self.top_dropdown.addItems([
            "Climb", "Cruise", "Descent", "Ground",
            "Single_Point", "Vertical Flight"
        ])
        self.details_layout.addWidget(self.top_dropdown)

        self.details_layout.addWidget(QLabel("Segment Type:"))
        self.populate_nested_dropdown(0)
        self.details_layout.addWidget(self.nested_dropdown)

        self.details_layout.addWidget(QLabel("Vehicle Configuration:"))
        config_names = [
            c.get("config name", "")
            for c in values.config_data
            if isinstance(c, dict)
        ]
        self.details_layout.addWidget(QLabel("Segment Details:"))
        if not config_names:
            cfg_container = getattr(values, "rcaide_configs", None)
            if isinstance(cfg_container, dict):
                config_names = list(cfg_container.keys())
        self.config_selector.addItems([n for n in config_names if n])
        self.details_layout.addWidget(self.config_selector)

        self.segment_layout.addWidget(self.details_group)

        # ============================================================
        # Group 3 — Degrees of Freedom
        # ============================================================
        self.dof_group = QGroupBox("Select Degrees of Freedom")
        self.dof_group.setStyleSheet(self._box_style())
        dof_layout = QVBoxLayout(self.dof_group)

        dof_fields = [
            ("Forces in X axis", Units.Boolean, "flight_dynamics.force_x"),
            ("Moments about X axis", Units.Boolean, "flight_dynamics.moment_x"),
            ("Forces in Y axis", Units.Boolean, "flight_dynamics.force_y"),
            ("Moments about Y axis", Units.Boolean, "flight_dynamics.moment_y"),
            ("Forces in Z axis", Units.Boolean, "flight_dynamics.force_z"),
            ("Moments about Z axis", Units.Boolean, "flight_dynamics.moment_z"),
        ]

        self.dof_entry_widget = DataEntryWidget(dof_fields)
        dof_layout.addWidget(self.dof_entry_widget)
        self.segment_layout.addWidget(self.dof_group)

        # ============================================================
        # Group 4 — Flight Controls
        # ============================================================
        self.fc_group = QGroupBox("Select Flight Controls")
        self.fc_group.setStyleSheet(self._box_style())
        fc_layout = QVBoxLayout(self.fc_group)

        self.flight_controls_widget = FlightControlsWidget()
        fc_layout.addWidget(self.flight_controls_widget)
        self.segment_layout.addWidget(self.fc_group)

        # ============================================================
        # Signals
        # ============================================================
        self.top_dropdown.currentIndexChanged.connect(
            self._on_top_dropdown_change
        )
        self.nested_dropdown.currentIndexChanged.connect(
            self.update_subsegment_fields
        )
        self.segment_name_input.textChanged.connect(
            self._on_segment_name_change
        )

        self._apply_defaults()

    # ============================================================
    # Styling
    # ============================================================
    def _box_style(self):
        return """
        QGroupBox {
            color:#cfe0ff;
            font-weight:600;
            border:1px solid #2d3a4e;
            border-radius:6px;
            padding:20px;
            margin-bottom:20px;
        }
        """

    # ============================================================
    # Dropdown Logic
    # ============================================================
    def populate_nested_dropdown(self, index):
        # Clear old subsegment options
        self.nested_dropdown.clear()

        # Populate subsegments for the selected segment type
        self.nested_dropdown.addItems(
            list(segment_data_fields[index].keys())
        )

    def _on_top_dropdown_change(self, idx):
        # Update available subsegments when segment type changes
        self.populate_nested_dropdown(idx)

        # Rebuild the subsegment-specific input fields
        self.update_subsegment_fields()

    # ============================================================
    # Subsegment Handling
    # ============================================================
    def update_subsegment_fields(self):
        # Remove the previous subsegment input widget if it exists
        if self.subsegment_entry_widget:
            self.subsegment_entry_widget.setParent(None)
            self.subsegment_entry_widget = None

        # Get the selected segment type and subsegment
        top = self.top_dropdown.currentIndex()
        sub = self.nested_dropdown.currentText()

        # Do nothing if no subsegment is selected
        if not sub:
            return

        # Create input fields for the selected subsegment
        self.subsegment_entry_widget = DataEntryWidget(
            segment_data_fields[top][sub]
        )

        # Add the subsegment fields to the UI
        self.details_layout.addWidget(self.subsegment_entry_widget)
        
        # Re-apply DOF and control defaults once subsegment exists
        if self.dof_entry_widget and self.flight_controls_widget:
            self._apply_defaults()

    def _default_config_key(self, top_text, sub_text, name_text):
        # Normalize all inputs so comparisons are consistent
        top = convert_name(top_text)
        name = convert_name(name_text)

        # Hard-map RCAIDE mission_setup tags to correct configs
        if name:
            tag_map = {
                "takeoff_ground_run": "takeoff",
                "takeoff_climb": "takeoff",
                "inital_climb": "cutback",
                "initial_climb": "cutback",
                "climb_to_cruise_1": "cutback",
                "climb_to_cruise_4": "cruise",
                "cruise": "cruise",
                "descent_1": "cruise",
                "approach": "landing",
                "final_approach": "landing",
                "level_off_touchdown": "landing",
                "landing": "reverse_thrust" if top == "ground" else "landing",
            }
            if name in tag_map:
                return tag_map[name]

        # Fallback to base config if nothing matched
        return "base"


    def _apply_config_default(self, config_key):
        # Do nothing if no configuration data exists
        if not values.config_data:
            return

        # Select the configuration matching the inferred key
        for idx, cfg in enumerate(values.config_data):
            if convert_name(cfg.get("config name", "")) == config_key:
                self.config_selector.setCurrentIndex(idx)
                break

    def _on_segment_name_change(self, _):
        # Avoid changing defaults while loading saved data
        if self._suppress_defaults:
            return

        # Recompute the correct aircraft configuration
        config_key = self._default_config_key(
            self.top_dropdown.currentText(),
            self.nested_dropdown.currentText(),
            self.segment_name_input.text(),
        )

        # Apply the inferred configuration
        self._apply_config_default(config_key)


    def _apply_defaults(self):
        # Skip defaults when restoring saved missions
        if self._suppress_defaults:
            return

        # Read current UI values
        top_text = self.top_dropdown.currentText()
        sub_text = self.nested_dropdown.currentText()
        name_text = self.segment_name_input.text()

        # Ground segments cannot be trimmed
        needs_trim = convert_name(top_text) != "ground"

        dof_defaults = {}

        # Enable only the forces needed for longitudinal trim
        for label, _, _ in self.dof_entry_widget.data_units_labels:
            dof_defaults[label] = (
                label in {"Forces in X axis", "Forces in Z axis"} and needs_trim,
                0,
            )

        # Apply DOF defaults to the UI
        self.dof_entry_widget.load_data(dof_defaults)

        # Ensure trim has at least throttle and body angle
        self.flight_controls_widget.set_defaults(
            throttle=needs_trim,
            body_angle=needs_trim,
        )

        # Select the correct aircraft configuration
        self._apply_config_default(
            self._default_config_key(top_text, sub_text, name_text)
        )

    # ============================================================
    # Save / Load
    # ============================================================
    def get_data(self):
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
        data.update(self.subsegment_entry_widget.get_values())
        return data, self.create_rcaide_segment()

    def load_data(self, data):
        self._suppress_defaults = True

        self.segment_name_input.setText(data["Segment Name"])
        self.top_dropdown.setCurrentIndex(data["top dropdown"])
        self.populate_nested_dropdown(data["top dropdown"])
        self.nested_dropdown.setCurrentText(data["nested dropdown"])
        self.config_selector.setCurrentIndex(data["config"])
        self.ctrl_points.setText(str(data.get("Control Points", 16)))

        if data.get("Solver", "root") == "root":
            self.solver_root.setChecked(True)
        else:
            self.solver_opt.setChecked(True)

        self.update_subsegment_fields()
        self.subsegment_entry_widget.load_data(data)
        self.dof_entry_widget.load_data(data["flight forces"])
        self.flight_controls_widget.load_data(data["flight controls"])

        self._suppress_defaults = False

    # ============================================================
    # RCAIDE Segment Creation
    # ============================================================
    def create_rcaide_segment(self):
        top = self.top_dropdown.currentIndex()
        sub = self.nested_dropdown.currentText()

        seg = segment_rcaide_classes[top][sub]()
        seg.tag = self.segment_name_input.text()

        if hasattr(seg, "state") and hasattr(seg.state, "numerics"):
            solver = (
                "root_finder"
                if self.solver_root.isChecked()
                else "optimize"
            )
            # Force cruise to use root_finder for better trim convergence
            if top == 1:
                solver = "root_finder"
            if hasattr(seg.state.numerics, "solver"):
                seg.state.numerics.solver.type = solver

        vals_si = self.subsegment_entry_widget.get_values_si()
        for label, _, rcaide_label in (
            self.subsegment_entry_widget.data_units_labels
        ):
            set_data(seg, rcaide_label, vals_si[label][0])

        dof_vals = self.dof_entry_widget.get_values()
        for label, _, rcaide_label in (
            self.dof_entry_widget.data_units_labels
        ):
            set_data(seg, rcaide_label, dof_vals[label][0])

        cfg = convert_name(self.config_selector.currentText())
        analyses = values.rcaide_analyses.get(cfg)
        if analyses is None or (hasattr(analyses, "__len__") and len(analyses) == 0):
            fallback = None
            for candidate in values.rcaide_analyses.values():
                if hasattr(candidate, "__len__") and len(candidate) > 0:
                    fallback = candidate
                    break
            if fallback is not None:
                analyses = fallback
            else:
                raise RuntimeError(
                    "No RCAIDE analyses available. "
                    "Go to Mission tab and press 'Save Analyses'."
                )

        seg.analyses.extend(analyses)
        self.flight_controls_widget.set_control_variables(seg)
        seg.control_points = int(self.ctrl_points.text())

        return seg
