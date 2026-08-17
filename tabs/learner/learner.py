"""Guided, low-fidelity aircraft setup for middle- and high-school learners."""

from __future__ import annotations

from copy import deepcopy
from math import radians

import RCAIDE
from RCAIDE.Framework.Core import Data
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

import rcaide_io
from tabs import TabWidget
from tabs.learner.model_view import style_learner_page


# This compact schema is the learner-facing source of truth.  It intentionally
# omits the detailed component segments, propulsion network, configurations,
# and analyses that Advanced Mode asks the user to define explicitly.
DEFAULT_LEARNER_DATA = {
    "vehicle": {
        "name": "Classroom Explorer",
        "max_takeoff_weight_kg": 1100.0,
        "reference_area_m2": 16.2,
        "passengers": 4,
    },
    "wing": {
        "span_m": 11.0,
        "root_chord_m": 1.8,
        "tip_chord_m": 1.1,
        "sweep_deg": 3.0,
    },
    "fuselage": {
        "length_m": 8.3,
        "width_m": 1.2,
        "height_m": 1.4,
    },
    "stabilizers": {
        "horizontal_area_m2": 3.6,
        "horizontal_span_m": 3.8,
        "vertical_area_m2": 1.9,
        "vertical_height_m": 1.7,
    },
    "engine": {
        "sfc_kg_per_n_hr": 0.06,
    },
    "mission": {
        "altitude_m": 3000.0,
        "speed_m_s": 70.0,
        "distance_km": 250.0,
    },
}


def _merged_learner_data(raw):
    """Return a complete learner dictionary while accepting older partial saves."""
    # Start from a deep copy so filling missing keys never mutates the defaults.
    result = deepcopy(DEFAULT_LEARNER_DATA)
    if not isinstance(raw, dict):
        return result
    for section, defaults in result.items():
        values = raw.get(section, {})
        if isinstance(values, dict):
            defaults.update({key: value for key, value in values.items() if key in defaults})
    return result


def build_learner_vehicle(data):
    """Build a valid conceptual RCAIDE vehicle with unsegmented geometry."""
    # Normalize first so builders can safely read every expected learner field,
    # including when an older saved file lacks a newly introduced section.
    data = _merged_learner_data(data)
    vehicle_data = data["vehicle"]
    wing_data = data["wing"]
    fuselage_data = data["fuselage"]
    stabilizer_data = data["stabilizers"]
    engine_data = data["engine"]

    # Populate the high-level RCAIDE vehicle properties directly from the four
    # whole-aircraft choices shown at the top of Learner Setup.
    vehicle = RCAIDE.Vehicle()
    vehicle.tag = str(vehicle_data["name"]).strip() or DEFAULT_LEARNER_DATA["vehicle"]["name"]
    vehicle.mass_properties.max_takeoff = float(vehicle_data["max_takeoff_weight_kg"])
    vehicle.mass_properties.takeoff = float(vehicle_data["max_takeoff_weight_kg"])
    # Learner mode does not expose a full weights-analysis setup.  Supply a
    # transparent conceptual mass breakdown so RCAIDE can still evaluate the
    # aircraft with its normal mission machinery.
    vehicle.mass_properties.operating_empty = 0.60 * vehicle.mass_properties.max_takeoff
    vehicle.mass_properties.max_zero_fuel = 0.90 * vehicle.mass_properties.max_takeoff
    vehicle.mass_properties.landing = 0.95 * vehicle.mass_properties.max_takeoff
    vehicle.reference_area = float(vehicle_data["reference_area_m2"])
    vehicle.number_of_passengers = int(vehicle_data["passengers"])

    fuselage_length = float(fuselage_data["length_m"])
    fuselage_height = float(fuselage_data["height_m"])

    # Learner Mode represents the main wing as one trapezoid.  Derived values
    # such as taper and aspect ratio keep the RCAIDE component internally useful
    # without exposing section-by-section geometry to the learner.
    wing = RCAIDE.Library.Components.Wings.Main_Wing()
    wing.tag = "main_wing"
    wing.areas.reference = vehicle.reference_area
    wing.spans.projected = float(wing_data["span_m"])
    wing.chords.root = float(wing_data["root_chord_m"])
    wing.chords.tip = float(wing_data["tip_chord_m"])
    wing.chords.mean_aerodynamic = (wing.chords.root + wing.chords.tip) / 2.0
    wing.taper = wing.chords.tip / wing.chords.root
    wing.aspect_ratio = wing.spans.projected ** 2 / wing.areas.reference
    wing.sweeps.quarter_chord = radians(float(wing_data["sweep_deg"]))
    wing.thickness_to_chord = 0.12
    wing.origin = [[0.38 * fuselage_length, 0.0, 0.0]]
    wing.xz_plane_symmetric = True
    wing.xy_plane_symmetric = False
    vehicle.append_component(wing)

    # Learners size only the main wing. A conventional tail is derived from it
    # so the result still looks and behaves conceptually like a complete plane.
    # Tail position, taper, sweep, and thickness are sensible hidden defaults;
    # learners control only the overall area and span/height of each stabilizer.
    horizontal_tail = RCAIDE.Library.Components.Wings.Horizontal_Tail()
    horizontal_tail.tag = "horizontal_stabilizer"
    horizontal_tail.areas.reference = float(stabilizer_data["horizontal_area_m2"])
    horizontal_tail.spans.projected = float(stabilizer_data["horizontal_span_m"])
    horizontal_tail.aspect_ratio = (
        horizontal_tail.spans.projected ** 2 / horizontal_tail.areas.reference
    )
    horizontal_tail.taper = 0.60
    horizontal_tail.sweeps.quarter_chord = radians(10.0)
    horizontal_tail.thickness_to_chord = 0.10
    horizontal_tail.origin = [[
        0.78 * fuselage_length,
        0.0,
        0.20 * fuselage_height,
    ]]
    horizontal_tail.xz_plane_symmetric = True
    horizontal_tail.xy_plane_symmetric = False
    vehicle.append_component(horizontal_tail)

    vertical_tail = RCAIDE.Library.Components.Wings.Vertical_Tail()
    vertical_tail.tag = "vertical_stabilizer"
    vertical_tail.areas.reference = float(stabilizer_data["vertical_area_m2"])
    vertical_tail.spans.projected = float(stabilizer_data["vertical_height_m"])
    vertical_tail.aspect_ratio = (
        vertical_tail.spans.projected ** 2 / vertical_tail.areas.reference
    )
    vertical_tail.taper = 0.55
    vertical_tail.sweeps.quarter_chord = radians(25.0)
    vertical_tail.thickness_to_chord = 0.10
    vertical_tail.origin = [[
        0.75 * fuselage_length,
        0.0,
        0.10 * fuselage_height,
    ]]
    vertical_tail.vertical = True
    vertical_tail.xz_plane_symmetric = False
    vertical_tail.xy_plane_symmetric = False
    vehicle.append_component(vertical_tail)

    # The fuselage is intentionally unsegmented.  Nose, cabin, and tail lengths
    # are simple proportions used to give geometry and analyses a complete body.
    fuselage = RCAIDE.Library.Components.Fuselages.Fuselage()
    fuselage.tag = "fuselage"
    fuselage.lengths.total = fuselage_length
    fuselage.lengths.nose = 0.20 * fuselage.lengths.total
    fuselage.lengths.tail = 0.25 * fuselage.lengths.total
    fuselage.lengths.cabin = 0.55 * fuselage.lengths.total
    fuselage.width = float(fuselage_data["width_m"])
    fuselage.heights.maximum = fuselage_height
    fuselage.effective_diameter = (fuselage.width + fuselage.heights.maximum) / 2.0
    vehicle.append_component(fuselage)

    # This intentionally is not a detailed thermodynamic engine network.  The
    # learner model records only the one quantity its low-fidelity equations use.
    vehicle.learner_mode = True
    vehicle.low_fidelity_engine = Data()
    vehicle.low_fidelity_engine.tag = "simple_engine"
    vehicle.low_fidelity_engine.sfc_kg_per_n_hr = float(engine_data["sfc_kg_per_n_hr"])
    return vehicle


# Four points expose RCAIDE's real mission history without making the learner
# wait for the full control-point count used by more detailed analyses.
LEARNER_CRUISE_CONTROL_POINTS = 4


def build_learner_mission(data):
    """Build the learner cruise with RCAIDE's production cruise segment.

    A complete propulsion network cannot be defined from SFC alone.  RCAIDE
    therefore solves the level-flight aerodynamic states without propulsion;
    learner engine output and fuel burn are derived afterward from RCAIDE drag.
    """
    data = _merged_learner_data(data)
    mission_data = data["mission"]
    # Use the same distance-based cruise segment as the normal mission tool so
    # the result contains genuine time, range, and condition arrays.  Horizontal
    # force remains unsolved because SFC alone cannot define a propulsor.
    segment_type = (
        RCAIDE.Framework.Mission.Segments.Cruise
        .Constant_Speed_Constant_Altitude
    )
    segment = segment_type()
    segment.tag = "cruise"
    segment.altitude = float(mission_data["altitude_m"])
    segment.air_speed = float(mission_data["speed_m_s"])
    # Learner data stores distance in kilometers; RCAIDE expects SI meters.
    segment.distance = float(mission_data["distance_km"]) * 1000.0
    # Solve vertical equilibrium and pitch attitude.  Horizontal force is read
    # from aerodynamic drag afterward to estimate required engine push.
    segment.flight_dynamics.force_x = False
    segment.flight_dynamics.force_z = True
    segment.assigned_control_variables.pitch_angle.active = True
    # Set RCAIDE's actual numerical setting, rather than only the form field,
    # so the returned time history contains four solver-generated samples.
    segment.state.numerics.number_of_control_points = LEARNER_CRUISE_CONTROL_POINTS

    # Attach the hidden learner analysis stack when it has already been built.
    analyses = getattr(rcaide_io, "rcaide_analyses", None)
    if analyses:
        base = analyses.get("base") if hasattr(analyses, "get") else None
        if base is None:
            try:
                base = next(iter(analyses.values()))
            except (AttributeError, StopIteration):
                base = None
        if base is not None:
            segment.analyses.extend(base)

    # Keep the standard mission container even though Learner Mode permits only
    # one segment. This lets the shared solver and plotters consume it normally.
    mission = RCAIDE.Framework.Mission.Sequential_Segments()
    mission.tag = "learner_cruise"
    mission.append_segment(segment)
    return mission


def learner_mission_form_data(data):
    """Create the standard Mission Setup form record for the learner cruise."""
    # Keep the regular Mission editor's dictionary format so the simplified
    # cruise can be displayed there without maintaining a second data model.
    mission = _merged_learner_data(data)["mission"]
    return [{
        "Segment Name": "cruise",
        "top dropdown": 1,
        "nested dropdown": "Constant Speed-Constant Altitude",
        "config": "base",
        "Control Points": LEARNER_CRUISE_CONTROL_POINTS,
        "Solver": "root",
        "Altitude": [float(mission["altitude_m"]), 0],
        "Air Speed": [float(mission["speed_m_s"]), 0],
        "Distance": [float(mission["distance_km"]) * 1000.0, 0],
        "True Course Angle": [0.0, 0],
        "flight forces": {
            # Retain the standard cruise form semantics so this record also
            # opens correctly in the full Mission editor.  The learner's
            # no-propulsion evaluation segment disables X-force solving when
            # it is built internally.
            "Forces in X axis": [True, 0],
            "Moments about X axis": [False, 0],
            "Forces in Y axis": [False, 0],
            "Moments about Y axis": [False, 0],
            "Forces in Z axis": [True, 0],
            "Moments about Z axis": [False, 0],
        },
        "flight controls": {
            "Pitch Angle": [True, 0],
            "Bank Angle": [False, 0],
            "Angle of Attack": [False, 0],
            "Velocity": [False, 0],
            "Acceleration": [False, 0],
            "Altitude": [False, 0],
            "Elevator Deflection": [False, 0],
            "Rudder Deflection": [False, 0],
            "Flap Deflection": [False, 0],
            "Slat Deflection": [False, 0],
            "Aileron Deflection": [False, 0],
            "Throttle": [False, 0],
            "Thrust Vector Angle": [False, 0],
            "assigned_propulsors": [],
        },
    }]


def prepare_learner_rcaide_workflow(data):
    """Create the hidden base config, analyses, and mission learner tabs need."""
    clean = _merged_learner_data(data)
    vehicle = rcaide_io.vehicle

    # Learner Mode has one vehicle configuration.  Advanced configuration
    # choices remain hidden because they are unnecessary for steady cruise.
    configs = RCAIDE.Library.Components.Configs.Config.Container()
    base_config = RCAIDE.Library.Components.Configs.Config(vehicle)
    base_config.tag = "base"
    configs.append(base_config)

    # Build the smallest RCAIDE analysis collection required for geometry,
    # atmosphere, weights, energy bookkeeping, and aerodynamic cruise solving.
    analyses = RCAIDE.Framework.Analyses.Vehicle()
    analyses.tag = "base"
    analyses.vehicle = base_config

    aerodynamics = RCAIDE.Framework.Analyses.Aerodynamics.Vortex_Lattice_Method()
    aerodynamics.vehicle = base_config
    # Direct, modest-resolution VLM is more predictable for the compact learner
    # cruise than training a surrogate model.
    aerodynamics.settings.use_surrogate = False
    aerodynamics.settings.number_of_spanwise_vortices = 8
    aerodynamics.settings.number_of_chordwise_vortices = 4
    analyses.append(aerodynamics)

    analyses.append(RCAIDE.Framework.Analyses.Atmospheric.US_Standard_1976())
    analyses.append(RCAIDE.Framework.Analyses.Planets.Earth())

    weights = RCAIDE.Framework.Analyses.Weights.Conventional_General_Aviation()
    weights.vehicle = base_config
    weights.settings.run_weights_analysis = False
    weights.settings.overwrite_operating_empty_weight = False
    analyses.append(weights)

    geometry = RCAIDE.Framework.Analyses.Geometry.Geometry()
    geometry.vehicle = base_config
    analyses.append(geometry)

    energy = RCAIDE.Framework.Analyses.Energy.Energy()
    energy.vehicle = base_config
    analyses.append(energy)

    rcaide_io.config_data = [{"name": "base"}]
    rcaide_io.rcaide_configs = configs
    # Runtime analyses contain NumPy state and are rebuilt automatically for
    # learner mode; do not place them in the JSON-oriented form-data list.
    rcaide_io.analysis_data = []
    rcaide_io.rcaide_analyses = {"base": analyses}
    rcaide_io.mission_data = learner_mission_form_data(clean)
    rcaide_io.rcaide_mission = build_learner_mission(clean)
    rcaide_io.rcaide_results = None
    return clean


def initialize_unbuilt_learner_workspace(data=None):
    """Prefill learner inputs without constructing an aircraft or mission."""
    # Entering Learner Mode must show form defaults but no aircraft.  Reset all
    # runtime RCAIDE containers so visualization and force arrows remain empty
    # until Save Vehicle explicitly calls apply_learner_setup().
    clean = _merged_learner_data(data or DEFAULT_LEARNER_DATA)
    rcaide_io.learner_data = clean
    rcaide_io.learner_vehicle_built = False
    rcaide_io.vehicle = RCAIDE.Vehicle()
    rcaide_io.rcaide_vehicle = rcaide_io.new_rcaide_vehicle_data()
    rcaide_io.propulsor_names = [[]]
    rcaide_io.config_data = []
    rcaide_io.rcaide_configs = RCAIDE.Library.Components.Configs.Config.Container()
    rcaide_io.analysis_data = []
    rcaide_io.rcaide_analyses = RCAIDE.Framework.Analyses.Analysis.Container()
    rcaide_io.mission_data = []
    rcaide_io.rcaide_mission = RCAIDE.Framework.Mission.Sequential_Segments()
    rcaide_io.rcaide_results = None
    return clean


def apply_learner_setup(data):
    """Replace the active conceptual vehicle and mission with learner inputs."""
    # Convert the compact learner record into both RCAIDE's live object model
    # and the legacy UI list structure consumed by existing geometry widgets.
    clean = _merged_learner_data(data)
    vehicle = build_learner_vehicle(clean)
    rcaide_io.vehicle = vehicle
    vehicle_dict = rcaide_io.make_json_safe(
        rcaide_io._build_dict_base_with_types(vehicle)
    )
    rcaide_io.rcaide_vehicle = rcaide_io.vehicle_dict_to_ui_list_structure(vehicle_dict)
    rcaide_io.rcaide_vehicle[0] = rcaide_io.vehicle_to_ui_format(vehicle)
    rcaide_io.learner_data = clean
    rcaide_io.learner_vehicle_built = True
    # A newly built learner aircraft must not inherit configurations or analyses
    # that belonged to a previously loaded, unrelated advanced aircraft.
    rcaide_io.propulsor_names = [[]]
    return prepare_learner_rcaide_workflow(clean)


class LearnerSetupWidget(TabWidget):
    """One-page, plain-language aircraft worksheet."""

    setup_saved = pyqtSignal()

    def __init__(self):
        super().__init__()
        style_learner_page(self)
        # Map (schema section, key) to its editor widget.  This lets the generic
        # values/load helpers synchronize the form without field-specific code.
        self._fields = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(22, 18, 22, 18)
        outer.setSpacing(10)
        eyebrow = QLabel("RCAIDE  •  SIMPLIFIED WORKFLOW")
        eyebrow.setObjectName("eyebrow")
        outer.addWidget(eyebrow)
        title = QLabel("Learner Setup")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Build a basic airplane by choosing its overall size and shape. Save it "
            "when you are ready to view it and plan a cruise."
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("subtitle")
        outer.addWidget(title)
        outer.addWidget(subtitle)

        note = QLabel(
            "You choose the big design ideas. RCAIDE fills in the smaller engineering "
            "details needed for a learning model. The result demonstrates aircraft "
            "design trends; it is not a certified real-aircraft design."
        )
        note.setWordWrap(True)
        note.setStyleSheet(
            "background:#0c2233; border:1px solid #28475d; border-radius:8px; "
            "padding:11px; color:#bcd0dd;"
        )
        outer.addWidget(note)

        # Cards use a responsive two-column grid inside a scroll area so the
        # complete setup remains usable on smaller classroom displays.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        cards = QGridLayout(content)
        cards.setSpacing(12)
        cards.addWidget(self._vehicle_card(), 0, 0)
        cards.addWidget(self._wing_card(), 0, 1)
        cards.addWidget(self._fuselage_card(), 1, 0)
        cards.addWidget(self._stabilizers_card(), 1, 1)
        cards.addWidget(self._engine_card(), 2, 0, 1, 2)
        cards.setColumnStretch(0, 1)
        cards.setColumnStretch(1, 1)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        self.feedback = QLabel()
        self.feedback.setWordWrap(True)
        self.feedback.setStyleSheet("color:#b9d7f5; padding:4px;")
        outer.addWidget(self.feedback)

        actions = QHBoxLayout()
        reset = QPushButton("Reset Example Aircraft")
        save = QPushButton("Save Vehicle")
        save.setProperty("primary", True)
        reset.clicked.connect(self.reset_defaults)
        save.clicked.connect(self.save_setup)
        actions.addWidget(reset)
        actions.addStretch()
        actions.addWidget(save)
        outer.addLayout(actions)

        self._connect_feedback()
        self.load_from_values()

    @staticmethod
    def _card(title, explanation):
        # Keep learner section headings inside the card instead of using the
        # native QGroupBox title, which visually collides with the border.
        box = QGroupBox()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(16, 14, 16, 14)
        section_title = QLabel(title.upper())
        section_title.setObjectName("learnerSectionTitle")
        section_title.setStyleSheet(
            "color:#a9cce5; font-size:14px; font-weight:700; padding:0 0 5px 2px;"
        )
        layout.addWidget(section_title)
        help_label = QLabel(explanation)
        help_label.setObjectName("learnerConceptExplanation")
        help_label.setWordWrap(True)
        help_label.setStyleSheet(
            "color:#62c4ef; font-size:14px; font-weight:500;"
        )
        layout.addWidget(help_label)
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        layout.addLayout(form)
        return box, form

    def _double(self, section, key, minimum, maximum, suffix, decimals=2):
        """Create and register a bounded numeric field for one schema value."""
        field = QDoubleSpinBox()
        field.setRange(minimum, maximum)
        field.setDecimals(decimals)
        field.setSuffix(f" {suffix}" if suffix else "")
        field.setSingleStep(1.0 if maximum > 100 else 0.1)
        self._fields[(section, key)] = field
        return field

    def _vehicle_card(self):
        box, form = self._card(
            "1. The whole airplane",
            "Give the airplane a name, choose the most it is allowed to weigh when "
            "fully loaded, set its total wing area, and decide how many passengers fit. "
            "A heavier airplane usually needs more lift and more fuel.",
        )
        name = QLineEdit()
        self._fields[("vehicle", "name")] = name
        form.addRow("Aircraft name", name)
        form.addRow(
            "Heaviest allowed packed airplane",
            self._double("vehicle", "max_takeoff_weight_kg", 100, 1_000_000, "kg", 0),
        )
        form.addRow(
            "Total main-wing area",
            self._double("vehicle", "reference_area_m2", 1, 2_000, "m²", 1),
        )
        passengers = QSpinBox()
        passengers.setRange(0, 1000)
        self._fields[("vehicle", "passengers")] = passengers
        form.addRow("Passengers", passengers)
        return box

    def _wing_card(self):
        box, form = self._card(
            "2. Main wing — one simple shape",
            "The main wing creates the lift that holds the airplane up. Span is the "
            "full wingtip-to-wingtip distance, wing width is called chord, and sweep "
            "angles the wing backward. These choices change lift and air resistance.",
        )
        form.addRow("Wingtip-to-wingtip span", self._double("wing", "span_m", 1, 150, "m"))
        form.addRow("Wing width near the body", self._double("wing", "root_chord_m", 0.1, 30, "m"))
        form.addRow("Wing width near the tip", self._double("wing", "tip_chord_m", 0.1, 30, "m"))
        form.addRow("Backward sweep", self._double("wing", "sweep_deg", 0, 70, "degrees", 1))
        return box

    def _fuselage_card(self):
        box, form = self._card(
            "3. Fuselage — one simple body",
            "The fuselage is the airplane's main body and carries people and cargo. "
            "Choose only its total length, width, and height. A larger body provides "
            "more room but usually creates more air resistance.",
        )
        form.addRow("Body length", self._double("fuselage", "length_m", 1, 150, "m"))
        form.addRow("Widest width", self._double("fuselage", "width_m", 0.2, 20, "m"))
        form.addRow("Tallest height", self._double("fuselage", "height_m", 0.2, 20, "m"))
        return box

    def _stabilizers_card(self):
        box, form = self._card(
            "4. Tail stabilizers",
            "The horizontal tail helps stop the nose from pitching too far up or down. "
            "The upright vertical tail helps keep the nose pointing forward instead "
            "of sliding sideways. RCAIDE places both at the rear automatically.",
        )
        form.addRow(
            "Horizontal-tail area",
            self._double("stabilizers", "horizontal_area_m2", 0.2, 500, "m²", 1),
        )
        form.addRow(
            "Horizontal-tail span",
            self._double("stabilizers", "horizontal_span_m", 0.5, 80, "m", 1),
        )
        form.addRow(
            "Vertical-tail area",
            self._double("stabilizers", "vertical_area_m2", 0.2, 500, "m²", 1),
        )
        form.addRow(
            "Vertical-tail height",
            self._double("stabilizers", "vertical_height_m", 0.5, 40, "m", 1),
        )
        return box

    def _engine_card(self):
        box, form = self._card(
            "5. Low-fidelity engine",
            "This simple engine uses one fuel-use number. A lower number means it "
            "needs less fuel to make the same forward push. Fuel burned depends on "
            "this number, the push needed to overcome drag, and how long the trip lasts.",
        )
        form.addRow(
            "Engine fuel-use score (lower is better)",
            self._double("engine", "sfc_kg_per_n_hr", 0.001, 2.0, "kg/(N·h)", 3),
        )
        return box

    def _mission_card(self):
        box, form = self._card(
            "6. Straight cruise mission",
            "The airplane is already in the air and flies straight, level, and "
            "at constant speed. Takeoff, turns, climbs, and landing are left out.",
        )
        form.addRow("Cruise altitude", self._double("mission", "altitude_m", 0, 25_000, "m", 0))
        form.addRow("Cruise speed", self._double("mission", "speed_m_s", 10, 500, "m/s", 1))
        form.addRow("Cruise distance", self._double("mission", "distance_km", 1, 20_000, "km", 1))
        return box

    def _connect_feedback(self):
        """Refresh the design summary whenever a numeric choice changes."""
        for field in self._fields.values():
            signal = getattr(field, "valueChanged", None)
            if signal is not None:
                signal.connect(self._update_feedback)

    def values(self):
        # Preserve the separate Mission Setup choices when rebuilding only the
        # aircraft fields shown on this tab.
        data = _merged_learner_data(
            getattr(rcaide_io, "learner_data", DEFAULT_LEARNER_DATA)
        )
        for (section, key), field in self._fields.items():
            if isinstance(field, QLineEdit):
                value = field.text().strip()
            else:
                value = field.value()
            data[section][key] = value
        return data

    def _set_values(self, data):
        """Load a normalized learner record into every registered form field."""
        data = _merged_learner_data(data)
        for (section, key), field in self._fields.items():
            value = data[section][key]
            if isinstance(field, QLineEdit):
                field.setText(str(value))
            else:
                field.setValue(value)
        self._update_feedback()

    def _update_feedback(self):
        """Translate a few design ratios into a short qualitative snapshot."""
        data = self.values()
        vehicle = data["vehicle"]
        wing = data["wing"]
        mission = data["mission"]
        wing_loading = vehicle["max_takeoff_weight_kg"] / vehicle["reference_area_m2"]
        aspect_ratio = wing["span_m"] ** 2 / vehicle["reference_area_m2"]
        hours = mission["distance_km"] / (mission["speed_m_s"] * 3.6)
        speed_story = "suited to gentler, slower flight" if wing_loading < 70 else "suited to a quicker everyday flight"
        wing_story = "long and narrow" if aspect_ratio >= 8 else "short and broad"
        self.feedback.setText(
            f"DESIGN SNAPSHOT  •  This aircraft is {speed_story}, has a {wing_story} wing, "
            f"and its planned trip takes about {hours:.1f} hours."
        )

    def reset_defaults(self):
        """Restore the example inputs without building the aircraft yet."""
        self._set_values(DEFAULT_LEARNER_DATA)

    def load_from_values(self):
        """Refresh the form from the learner workspace stored in rcaide_io."""
        self._set_values(getattr(rcaide_io, "learner_data", DEFAULT_LEARNER_DATA))

    def save_setup(self):
        """Validate the form, build the RCAIDE workflow, and notify other tabs."""
        data = self.values()
        # A name is required because RCAIDE uses it as the vehicle tag shown in
        # saved files and other learner tabs.
        if not data["vehicle"]["name"]:
            QMessageBox.warning(self, "Aircraft needs a name", "Give your aircraft a name first.")
            return
        # An inverse-taper wing is valid, but prompt because it is an unusual
        # accidental choice for a learner's first conventional aircraft.
        if data["wing"]["tip_chord_m"] > data["wing"]["root_chord_m"]:
            answer = QMessageBox.question(
                self,
                "Unusual wing shape",
                "The tip chord is larger than the root chord. That is possible, "
                "but unusual for a first design. Build it anyway?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        # Build only after validation succeeds.  setup_saved refreshes geometry,
        # forces, mission setup, and the solver through the main application.
        apply_learner_setup(data)
        rcaide_io.learner_last_run = None
        self._update_feedback()
        self.setup_saved.emit()
        QMessageBox.information(
            self,
            "Learner aircraft built",
            "Your one-wing, one-fuselage aircraft and straight cruise mission are ready.",
        )


def get_widget() -> QWidget:
    """Return the learner setup tab using the same factory pattern as other tabs."""
    return LearnerSetupWidget()
