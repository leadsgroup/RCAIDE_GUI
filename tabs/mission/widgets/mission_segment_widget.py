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

        # MAIN LAYOUT
        self.segment_layout = QVBoxLayout()
        self.segment_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.segment_layout)

        # Runtime widgets
        self.subsegment_entry_widget = None
        self.dof_entry_widget = None
        self.flight_controls_widget = None

        # Dropdowns
        self.top_dropdown = QComboBox()
        self.nested_dropdown = QComboBox()
        self.config_selector = QComboBox()

        # ============================================================
        # GROUP 1 — Specify Segment Settings
        # ============================================================
        self.settings_group = QGroupBox("Specify Segment Settings")
        self.settings_group.setStyleSheet(self._box_style())
        self.settings_layout = QVBoxLayout(self.settings_group)

        # Control Points Row
        cp_row = QHBoxLayout()
        cp_row.addWidget(QLabel("Number of Control Points:"))
        self.ctrl_points = QLineEdit("2")
        self.ctrl_points.setFixedWidth(70)
        self.ctrl_points.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cp_row.addWidget(self.ctrl_points)
        cp_row.addStretch(1)
        self.settings_layout.addLayout(cp_row)

        # Solver Row
        solver_label = QLabel("Mission Solver:")
        solver_row = QHBoxLayout()
        solver_row.addWidget(solver_label)
        self.solver_root = QRadioButton("Root Solver")
        self.solver_opt = QRadioButton("Optimize Solver")
        self.solver_root.setChecked(True)
        solver_row.addWidget(self.solver_root)
        solver_row.addWidget(self.solver_opt)
        solver_row.addStretch(1)

        self.settings_layout.addLayout(solver_row)
        self.segment_layout.addWidget(self.settings_group)

        # ============================================================
        # GROUP 2 — Specify Segment Details
        # ============================================================
        self.details_group = QGroupBox("Specify Segment Details")
        self.details_group.setStyleSheet(self._box_style())
        self.details_layout = QVBoxLayout(self.details_group)
        self.details_layout.setSpacing(6)
        self.details_layout.setContentsMargins(8, 6, 8, 6)

        # ------------------------------------------------------------
        # Segment Name (FULL WIDTH, STACKED)
        # ------------------------------------------------------------
        name_lbl = QLabel("Segment Name:")
        self.details_layout.addWidget(name_lbl)
        self.segment_name_input = QLineEdit()
        self.details_layout.addWidget(self.segment_name_input)

        # ------------------------------------------------------------
        # Segment Type (FULL WIDTH, STACKED)
        # ------------------------------------------------------------
        stype_lbl = QLabel("Segment Type:")
        self.details_layout.addWidget(stype_lbl)

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
        ssub_lbl = QLabel("Subsegment Type:")
        self.details_layout.addWidget(ssub_lbl)

        self.populate_nested_dropdown(self.top_dropdown.currentIndex())
        self.nested_dropdown.setFixedHeight(28)
        self.details_layout.addWidget(self.nested_dropdown)

        # ------------------------------------------------------------
        # Aircraft Configuration (FULL WIDTH, STACKED)
        # ------------------------------------------------------------
        cfg_lbl = QLabel("Aircraft Configuration:")
        self.details_layout.addWidget(cfg_lbl)

        self.config_selector.addItems([c["config name"] for c in values.config_data])
        self.config_selector.setFixedHeight(28)
        self.details_layout.addWidget(self.config_selector)

        # Dynamic fields placeholder
        self.update_subsegment_fields()
        self.segment_layout.addWidget(self.details_group)

        # ============================================================
        # GROUP 3 — DOF
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
        # GROUP 4 — Flight Controls
        # ============================================================
        self.fc_group = QGroupBox("Select Flight Controls")
        self.fc_group.setStyleSheet(self._box_style())
        fc_layout = QVBoxLayout(self.fc_group)

        self.flight_controls_widget = FlightControlsWidget()
        fc_layout.addWidget(self.flight_controls_widget)
        self.segment_layout.addWidget(self.fc_group)

        # SIGNALS
        self.top_dropdown.currentIndexChanged.connect(self._on_top_dropdown_change)
        self.nested_dropdown.currentIndexChanged.connect(self.update_subsegment_fields)

    # ============================================================
    def _box_style(self):
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
    # DROPDOWN HANDLERS
    # ============================================================
    def _on_top_dropdown_change(self, idx):
        self.populate_nested_dropdown(idx)
        self.update_subsegment_fields()

    def populate_nested_dropdown(self, index):
        self.nested_dropdown.clear()
        self.nested_dropdown.addItems(list(segment_data_fields[index].keys()))

    # ============================================================
    # UPDATE SUBSEGMENT FIELDS
    # ============================================================
    def update_subsegment_fields(self):
        if self.subsegment_entry_widget:
            self.subsegment_entry_widget.setParent(None)
            self.subsegment_entry_widget = None

        top = self.top_dropdown.currentIndex()
        sub = self.nested_dropdown.currentText()

        if sub == "":
            return

        # new dynamic fields
        data_fields = segment_data_fields[top][sub]
        self.subsegment_entry_widget = DataEntryWidget(data_fields)
        self.details_layout.addWidget(self.subsegment_entry_widget)

    # ============================================================
    # SAVE DATA
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

    # ============================================================
    # LOAD DATA
    # ============================================================
    def load_data(self, data):
        self.segment_name_input.setText(data["Segment Name"])
        self.top_dropdown.setCurrentIndex(data["top dropdown"])
        self.populate_nested_dropdown(data["top dropdown"])
        self.nested_dropdown.setCurrentText(data["nested dropdown"])
        self.config_selector.setCurrentIndex(data["config"])
        self.ctrl_points.setText(str(data.get("Control Points", 2)))

        if data.get("Solver", "root") == "root":
            self.solver_root.setChecked(True)
        else:
            self.solver_opt.setChecked(True)

        self.update_subsegment_fields()
        self.subsegment_entry_widget.load_data(data)
        self.dof_entry_widget.load_data(data["flight forces"])
        self.flight_controls_widget.load_data(data["flight controls"])

    # ============================================================
    # RCAIDE CREATION
    # ============================================================
    def create_rcaide_segment(self):
        top = self.top_dropdown.currentIndex()
        sub = self.nested_dropdown.currentText()
        seg = segment_rcaide_classes[top][sub]()
        seg.tag = self.segment_name_input.text()

        vals_si = self.subsegment_entry_widget.get_values_si()
        for label, _, rcaide_label in self.subsegment_entry_widget.data_units_labels:
            set_data(seg, rcaide_label, vals_si[label][0])

        dof_vals = self.dof_entry_widget.get_values()
        for label, _, rcaide_label in self.dof_entry_widget.data_units_labels:
            set_data(seg, rcaide_label, dof_vals[label][0])

        self.flight_controls_widget.set_control_variables(seg)

        cfg = convert_name(self.config_selector.currentText())
        analyses = values.rcaide_analyses.get(cfg)
        if analyses is None:
            analyses = RCAIDE.Framework.Analyses.Vehicle()
            values.rcaide_analyses[cfg] = analyses

        seg.analyses.extend(analyses)
        seg.control_points = int(self.ctrl_points.text())
        return seg
