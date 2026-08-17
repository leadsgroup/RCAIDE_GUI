"""Learner-facing views of the normal RCAIDE mission workflow.

These widgets deliberately inherit the production Mission, Solve, and Results
tabs.  Learner mode changes presentation and supplies hidden defaults; it does
not maintain a second simulation tool.
"""

from __future__ import annotations

from copy import deepcopy

import numpy as np
from RCAIDE.Framework.Core import Data
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QWidget

import rcaide_io
from tabs.mission.mission import MissionWidget
from tabs.results_viewer.results_viewer import ResultsViewerWidget
from tabs.run_mission.run_mission import SolveWidget

from .learner import (
    DEFAULT_LEARNER_DATA,
    LEARNER_CRUISE_CONTROL_POINTS,
    _merged_learner_data,
    build_learner_mission,
    prepare_learner_rcaide_workflow,
)


class LearnerMissionSetupWidget(MissionWidget):
    """The normal mission editor restricted to one understandable cruise."""

    def __init__(self):
        super().__init__()
        # Preserve the production MissionWidget layout and data handling while
        # removing actions that would create a multi-segment advanced mission.
        self.add_segment_btn.setVisible(False)
        self.disable_btn.setVisible(False)
        self.clear_btn.setVisible(False)
        self.save_btn.setText("Save Cruise Mission")
        self.mission_name_input.setText("Learner Cruise")
        self.mission_name_input.setReadOnly(True)
        self.profile_widget.animate_single_phase = True

        self.segment_notice.setText(
            "One straight, level cruise is used. Choose how high, how fast, and "
            "how far it flies; RCAIDE supplies the advanced solver settings automatically."
        )
        self.segment_notice.setVisible(True)

    @staticmethod
    def _plain_label(label, text):
        """Replace engineering wording while retaining the original form widget."""
        label.setText(text)
        label.setStyleSheet("color:#dbe7ff;")

    def _simplify_segment(self, segment):
        """Lock one cruise segment and translate its visible controls for learners."""
        # Solver settings, degrees of freedom, and control assignments still
        # exist in the underlying segment but are supplied automatically.
        segment.settings_group.setVisible(False)
        segment.dof_group.setVisible(False)
        segment.fc_group.setVisible(False)

        # Prevent the base widget's name-change callback from selecting a
        # different configuration while applying the fixed learner values.
        segment._suppress_defaults = True
        segment.segment_name_input.setText("Cruise")
        segment._suppress_defaults = False
        segment.segment_name_input.setReadOnly(True)
        segment.top_dropdown.setCurrentText("Cruise")
        segment.top_dropdown.setEnabled(False)
        segment.nested_dropdown.setCurrentText("Constant Speed-Constant Altitude")
        segment.nested_dropdown.setEnabled(False)
        segment.config_selector.setCurrentText("base")
        segment.config_selector.setVisible(False)

        # Relabel in place so base MissionWidget serialization and signal wiring
        # continue to operate on the same controls.
        for label in segment.details_group.findChildren(QLabel):
            text = label.text()
            if text == "Segment Name:":
                self._plain_label(label, "Flight part:")
            elif text == "Segment Classification:":
                self._plain_label(label, "Type of flight:")
            elif text == "Segment Type:":
                self._plain_label(label, "How it flies:")
            elif text in {"Vehicle Configuration:", "Segment Details:"}:
                label.setVisible(False)
            elif text == "Altitude:":
                self._plain_label(label, "How high will it fly?")
            elif text == "Air Speed:":
                self._plain_label(label, "How fast will it fly?")
            elif text == "Distance:":
                self._plain_label(label, "How far will it travel?")
            elif text == "True Course Angle:":
                self._plain_label(label, "Direction of travel:")

        # Explain why the three editable cruise inputs affect the calculation.
        explanation = QLabel(
            "Height tells RCAIDE which air density to use. Speed changes how much "
            "air flows over the wing. Distance determines how long the engine must "
            "keep pushing and therefore affects fuel use."
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet(
            "background:#0c2233; border:1px solid #28475d; border-radius:6px; "
            "padding:8px; color:#63c8ff; font-size:13px;"
        )
        field_index = segment.details_layout.indexOf(
            segment.subsegment_entry_widget
        )
        segment.details_layout.insertWidget(max(field_index, 0), explanation)
        segment.details_group.setTitle("Cruise Conditions")

    def load_from_values(self):
        """Load the standard mission editor in its restricted learner state."""
        # Do not create mission content before the learner has explicitly saved
        # an aircraft; downstream tabs use this empty state as their lock signal.
        if not getattr(rcaide_io, "learner_vehicle_built", False):
            rcaide_io.mission_data = []
            super().load_from_values()
            self.save_btn.setEnabled(False)
            self.segment_notice.setText(
                "Build and save an aircraft in Learner Setup before planning its cruise."
            )
            self.segment_notice.setVisible(True)
            return

        self.save_btn.setEnabled(True)
        if not getattr(rcaide_io, "rcaide_analyses", None):
            prepare_learner_rcaide_workflow(
                getattr(rcaide_io, "learner_data", DEFAULT_LEARNER_DATA)
            )
        super().load_from_values()
        for segment in self.segment_widgets:
            self._simplify_segment(segment)
        # MissionWidget builds the standard multi-point cruise while loading.
        # Learner mode runs its restricted production-style cruise segment.
        rcaide_io.rcaide_mission = build_learner_mission(
            getattr(rcaide_io, "learner_data", DEFAULT_LEARNER_DATA)
        )
        self.refresh_mission_overview()

    def save_all_data(self):
        """Save learner cruise fields to both the form record and RCAIDE workflow."""
        if (not getattr(rcaide_io, "learner_vehicle_built", False) or
                not self.segment_widgets):
            return
        segment = self.segment_widgets[0]
        # Retain the regular Mission Setup record for compatibility with shared
        # UI code, then enforce the hidden learner-cruise defaults.
        form_data = segment.get_form_data()
        form_data["Segment Name"] = "cruise"
        form_data["config"] = "base"
        form_data["Control Points"] = LEARNER_CRUISE_CONTROL_POINTS
        form_data["flight forces"]["Forces in X axis"] = [True, 0]
        form_data["flight forces"]["Forces in Z axis"] = [True, 0]
        form_data["flight controls"]["Pitch Angle"] = [True, 0]

        # Store learner data in stable SI units regardless of which display unit
        # the learner selected in the inherited Mission editor.
        values_si = segment.subsegment_entry_widget.get_values_si()
        data = _merged_learner_data(
            deepcopy(getattr(rcaide_io, "learner_data", DEFAULT_LEARNER_DATA))
        )
        data["mission"]["altitude_m"] = float(values_si["Altitude"][0])
        data["mission"]["speed_m_s"] = float(values_si["Air Speed"][0])
        data["mission"]["distance_km"] = float(values_si["Distance"][0]) / 1000.0
        rcaide_io.learner_data = data
        prepare_learner_rcaide_workflow(data)
        rcaide_io.mission_data = [form_data]
        self._notify("Cruise mission saved for RCAIDE")
        self.refresh_mission_overview()


def _first_numeric(value):
    """Reduce an RCAIDE scalar or array to one finite teaching-summary value."""
    try:
        array = np.asarray(value, dtype=float)
        return float(np.nanmean(array)) if array.size else 0.0
    except (TypeError, ValueError):
        return 0.0


def add_learner_low_fidelity_engine_results(results):
    """Complete engine result arrays from RCAIDE drag at every control point.

    The learner supplies SFC rather than a compressor, turbine, motor, or
    propeller model. RCAIDE therefore solves the aerodynamic cruise first. In
    steady flight the required thrust equals solved drag; multiplying that
    thrust by solved airspeed supplies the corresponding low-fidelity power.
    These arrays are stored in RCAIDE's normal result locations so the inherited
    production plot renderer can be used without learner-specific graph data.
    """
    if results is None or not getattr(results, "segments", None):
        return results

    data = _merged_learner_data(
        getattr(rcaide_io, "learner_data", DEFAULT_LEARNER_DATA)
    )
    # SFC is stored as kilograms of fuel per newton of thrust per hour.
    sfc = float(data["engine"]["sfc_kg_per_n_hr"])

    # RCAIDE segment containers normally expose values(), while lightweight
    # test or compatibility containers may only be directly iterable.
    try:
        segments = results.segments.values()
    except AttributeError:
        segments = results.segments

    for segment in segments:
        try:
            conditions = segment.conditions
            # Wind-axis X force is negative drag. Its magnitude is the thrust
            # required to maintain constant speed at each solved point.
            wind_force = np.asarray(
                conditions.frames.wind.force_vector, dtype=float
            )
            speed = np.asarray(
                conditions.freestream.velocity, dtype=float
            ).reshape(-1)
            thrust = np.abs(wind_force[:, 0]).reshape(-1)
        except (AttributeError, IndexError, TypeError, ValueError):
            continue

        point_count = thrust.size
        # RCAIDE normally returns one speed for every force sample. Broadcast a
        # scalar speed defensively so result arrays always remain aligned.
        if speed.size == 1 and point_count > 1:
            speed = np.full(point_count, speed[0], dtype=float)
        elif speed.size != point_count:
            speed = np.resize(speed, point_count)

        # Populate exactly the fields used by the normal RCAIDE force and
        # energy plots. Y/Z thrust are zero for this straight-cruise model.
        thrust_vector = np.zeros((point_count, 3), dtype=float)
        thrust_vector[:, 0] = thrust
        conditions.frames.body.thrust_force_vector = thrust_vector
        # Mechanical power follows P = F * V at every RCAIDE control point.
        conditions.energy.power = (thrust * speed).reshape(-1, 1)
        # Convert the hourly SFC relation into RCAIDE's kg/s mass-flow field.
        conditions.weights.vehicle_mass_rate = (
            thrust * sfc / 3600.0
        ).reshape(-1, 1)

    return results


def add_learner_fuel_summary(results):
    """Attach plain-language trip metrics based on RCAIDE's solved drag."""
    if results is None or not getattr(results, "segments", None):
        return results
    # The no-propulsion segment reports aerodynamic wind-axis force.  Its
    # horizontal magnitude is the forward thrust needed for steady cruise.
    try:
        segment = next(iter(results.segments.values()))
        force = segment.conditions.frames.wind.force_vector
        required_thrust = abs(_first_numeric(np.asarray(force)[:, 0]))
    except (AttributeError, IndexError, TypeError):
        required_thrust = 0.0

    data = _merged_learner_data(
        getattr(rcaide_io, "learner_data", DEFAULT_LEARNER_DATA)
    )
    mission = data["mission"]
    hours = mission["distance_km"] / max(mission["speed_m_s"] * 3.6, 1e-9)
    sfc = float(data["engine"]["sfc_kg_per_n_hr"])

    # Low-fidelity fuel use follows the deliberately visible relationship:
    # fuel mass = required thrust × SFC × time.
    summary = Data()
    summary.tag = "learner_summary"
    summary.trip_distance_km = float(mission["distance_km"])
    summary.trip_time_hours = float(hours)
    summary.rcaide_required_thrust_n = float(required_thrust)
    summary.engine_sfc_kg_per_n_hr = sfc
    summary.estimated_fuel_burn_kg = float(required_thrust * sfc * hours)
    summary.explanation = (
        "RCAIDE solves the cruise aerodynamics. Required thrust equals the solved "
        "drag; fuel burn is required thrust multiplied by SFC and trip time."
    )
    results.learner_summary = summary
    return results


class LearnerSolveWidget(SolveWidget):
    """The normal RCAIDE solver with only learner-relevant plots exposed."""

    # Renderer keys must remain the production names because SolveWidget uses
    # them for dispatch; only their displayed labels are translated.
    _VISIBLE_PLOTS = {
        "Plot Aerodynamic Forces",
        "Plot Flight Conditions",
    }
    _LEARNER_PLOT_LABELS = {
        "Plot Aerodynamic Forces": "Engine push, lift, and drag",
        "Plot Flight Conditions": "Cruise speed and altitude",
    }
    # Titles are generated by production plot renderers and serve as stable keys
    # for the explanation card placed beside each learner graph.
    _GRAPH_EXPLANATIONS = {
        "Aerodynamic Forces: Power": (
            "ENGINE POWER\nHow quickly the engine supplies energy. It is calculated "
            "from the required forward push multiplied by cruise speed."
        ),
        "Aerodynamic Forces: Thrust": (
            "FORWARD PUSH\nThrust pushes the airplane forward. In steady cruise, "
            "the required forward push equals RCAIDE's solved air resistance."
        ),
        "Aerodynamic Forces: Lift": (
            "UPWARD PUSH\nLift is made by the wing. In level cruise it should be "
            "close to the airplane's downward weight."
        ),
        "Aerodynamic Forces: Drag": (
            "AIR RESISTANCE\nDrag pushes backward. The engine must provide about "
            "the same amount of forward push to hold a steady speed."
        ),
        "Flight Conditions: Altitude": (
            "FLYING HEIGHT\nThis shows the cruise height you selected. Air becomes "
            "thinner as altitude increases."
        ),
        "Flight Conditions: Airspeed": (
            "SPEED THROUGH THE AIR\nThis is how fast the airplane moves relative "
            "to the surrounding air, not its speed over the ground."
        ),
        "Flight Conditions: Range": (
            "DISTANCE TRAVELED\nThis shows how far the cruise covers. A longer trip "
            "keeps the engine working longer and normally burns more fuel."
        ),
    }

    def __init__(self):
        super().__init__()
        # Hide advanced plot styling controls while retaining the real solver,
        # selection tree, plotting pipeline, and background worker.
        self.solve_button.setText("Calculate My Cruise")
        self.settings_panel.setVisible(False)
        self.tree.setHeaderLabels(["Results to show", "Show"])
        self._learner_plot_rows = {}
        self.run_help = QLabel(
            "RCAIDE checks whether the wing can support the airplane at the chosen "
            "speed and altitude. Press Calculate My Cruise, then use the result "
            "graphs to see the forces and flight condition."
        )
        self.run_help.setWordWrap(True)
        self.run_help.setStyleSheet(
            "background:#0c2233; border:1px solid #28475d; border-radius:7px; "
            "padding:10px; color:#b9d7f5; font-size:13px;"
        )
        root_layout = self.layout()
        controls_column = root_layout.itemAt(0).layout() if root_layout is not None else None
        if controls_column is not None:
            controls_column.insertWidget(0, self.run_help)

        self.result_summary = QLabel(
            "Save the aircraft and cruise mission, then calculate the cruise here."
        )
        self.result_summary.setWordWrap(True)
        self.result_summary.setStyleSheet(
            "background:#10283a; border:1px solid #31566f; border-radius:7px; "
            "padding:12px; color:#dcebf5; font-size:14px;"
        )
        plot_column = root_layout.itemAt(1).layout() if root_layout is not None else None
        if plot_column is not None:
            plot_column.insertWidget(0, self.result_summary)

        # Filter rather than rebuild the production tree so renderer mapping and
        # checkbox behavior stay synchronized with SolveWidget.
        for i in range(self.tree.topLevelItemCount()):
            category = self.tree.topLevelItem(i)
            any_visible = False
            for j in range(category.childCount()):
                item = category.child(j)
                internal_name = item.text(0)
                visible = internal_name in self._VISIBLE_PLOTS
                item.setHidden(not visible)
                item.setCheckState(
                    1, Qt.CheckState.Checked if visible else Qt.CheckState.Unchecked
                )
                if visible:
                    item.setData(0, Qt.ItemDataRole.UserRole, internal_name)
                    item.setText(0, self._LEARNER_PLOT_LABELS[internal_name])
                any_visible = any_visible or visible
            category.setHidden(not any_visible)
            if any_visible:
                category.setText(
                    0,
                    "Forces" if category.text(0) == "Aerodynamics" else "Your cruise",
                )

    def _new_plot_widget(self, title, y_label, x_label="Time (min)", show_legend=True):
        """Place a plain-language explanation directly beside each learner plot."""
        # Let SolveWidget create and register the pyqtgraph widget first, then
        # reparent it into a row with its learner explanation card.
        plot = super()._new_plot_widget(title, y_label, x_label, show_legend)
        self.plot_layout.removeWidget(plot)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 4, 0, 4)
        row_layout.setSpacing(14)
        row_layout.addWidget(plot, 0, Qt.AlignmentFlag.AlignTop)

        explanation = QLabel(
            self._GRAPH_EXPLANATIONS.get(
                title,
                "WHAT THIS SHOWS\nThis graph shows one result from the RCAIDE cruise calculation.",
            )
        )
        explanation.setWordWrap(True)
        explanation.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        explanation.setMinimumWidth(230)
        explanation.setMaximumWidth(300)
        explanation.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding
        )
        explanation.setStyleSheet(
            "background:#10283a; border:1px solid #31566f; border-radius:8px; "
            "padding:14px; color:#b9dff7; font-size:13px;"
        )
        row_layout.addWidget(explanation, 0, Qt.AlignmentFlag.AlignTop)
        self.plot_layout.addWidget(row, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._learner_plot_rows[plot] = row
        return plot

    def _delete_plot_widgets(self, widgets):
        """Delete learner plot rows without leaving empty explanation cards."""
        # Production cleanup knows only about plot widgets. Track wrapper rows
        # separately so refreshing checkboxes cannot leave empty cards behind.
        ordinary = []
        for plot in widgets:
            row = self._learner_plot_rows.pop(plot, None)
            if row is None:
                ordinary.append(plot)
                continue
            self.plot_layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
        if ordinary:
            super()._delete_plot_widgets(ordinary)

    def _collect_checked_plot_options(self):
        """Translate visible learner labels back to production renderer keys."""
        checked = []
        for i in range(self.tree.topLevelItemCount()):
            category = self.tree.topLevelItem(i)
            for j in range(category.childCount()):
                item = category.child(j)
                if item.checkState(1) == Qt.CheckState.Checked:
                    checked.append(
                        item.data(0, Qt.ItemDataRole.UserRole) or item.text(0)
                    )
        return checked

    def run_solve(self):
        """Run the inherited RCAIDE solver after ensuring hidden defaults exist."""
        if not getattr(rcaide_io, "learner_vehicle_built", False):
            return
        # Rebuild the hidden defaults in case the learner edited mission fields
        # and opened this tab without explicitly pressing Save.
        if (not getattr(rcaide_io, "rcaide_mission", None) or
                not getattr(rcaide_io, "rcaide_analyses", None) or
                not getattr(rcaide_io, "rcaide_configs", None)):
            prepare_learner_rcaide_workflow(
                getattr(rcaide_io, "learner_data", DEFAULT_LEARNER_DATA)
            )
        super().run_solve()

    def _on_solve_finished(self, results, output):
        """Preserve production result handling and add a learner fuel narrative."""
        # Fill simplified engine channels before the inherited completion
        # handler renders the normal RCAIDE power and force plots.
        results = add_learner_low_fidelity_engine_results(results)
        # Attach the learner explanation without replacing the solver results.
        results = add_learner_fuel_summary(results)
        super()._on_solve_finished(results, output)
        summary = results.learner_summary
        self.result_summary.setText(
            f"Cruise calculated. The airplane needs about "
            f"{summary.rcaide_required_thrust_n:.0f} newtons of engine push "
            f"(newtons measure force) to "
            f"match air resistance. The {summary.trip_distance_km:.0f} km trip "
            f"takes about {summary.trip_time_hours:.2f} hours and is estimated to "
            f"use {summary.estimated_fuel_burn_kg:.1f} kg of fuel. More drag, a "
            "longer trip, or a thirstier engine increases fuel use."
        )
        self.solve_button.setText("Calculate Cruise Again")

    def load_from_values(self):
        """Reset button and guidance state when the learner opens this tab."""
        self.solve_button.setText("Calculate My Cruise")
        built = bool(getattr(rcaide_io, "learner_vehicle_built", False))
        self.solve_button.setEnabled(built)
        self.solve_button.setToolTip(
            "" if built else "Save the aircraft in Learner Setup first."
        )
        self.result_summary.setText(
            "Save the aircraft and cruise mission, then calculate the cruise here."
            if built else
            "Build and save an aircraft in Learner Setup before calculating a cruise."
        )


class LearnerResultsViewerWidget(ResultsViewerWidget):
    """The normal results browser focused on the latest mission result."""

    def __init__(self):
        super().__init__()
        # This optional wrapper remains compatible with the production results
        # browser but pins its source to the latest learner mission.
        self.source_combo.setCurrentText(self._SRC_MISSION)
        self.source_combo.setEnabled(False)
        self.source_detail_label.setVisible(False)
        for label in self.findChildren(QLabel):
            if label.text() == "Source:":
                label.setText("RCAIDE mission results")

        # Keep inspection and plotting, but remove controls intended mainly for
        # exporting/debugging advanced result objects.
        for widget in (
            self.copy_path_button,
            self.copy_value_button,
            self.export_selected_button,
            self.export_all_button,
            self.path_input,
            self.inspect_button,
        ):
            widget.setVisible(False)
        self.search_input.setPlaceholderText(
            "Filter results: lift, drag, speed, fuel burn..."
        )
