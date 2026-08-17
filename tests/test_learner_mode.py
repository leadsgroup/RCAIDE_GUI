"""Regression tests for the isolated, RCAIDE-backed Learner Mode workflow.

The suite covers both numerical behavior and Qt presentation contracts.  Qt is
forced off-screen so these tests can run in CI without opening native windows.
"""

import os
import json

# This must be set before importing any Qt-backed learner modules.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
import rcaide_io

from tabs.learner.learner import (
    DEFAULT_LEARNER_DATA,
    apply_learner_setup,
    build_learner_mission,
    build_learner_vehicle,
    initialize_unbuilt_learner_workspace,
    learner_mission_form_data,
)
from tabs.visualize_geometry.geometry_helper_functions import (
    generate_fuselage_points_for_viewer,
    learner_component_callout_data,
    learner_component_label_data,
)
from tabs.learner.learning_tools import (
    classroom_loading,
    classroom_metrics,
    evaluate_challenges,
)


# -----------------------------------------------------------------------------
# Learner vehicle and mission construction
# -----------------------------------------------------------------------------
# These tests protect the compact learner data contract and confirm that it is
# converted into valid RCAIDE objects without exposing component segments.

def test_default_learner_vehicle_has_unsegmented_geometry():
    """The default builder creates one body and three complete simple wings."""
    vehicle = build_learner_vehicle(DEFAULT_LEARNER_DATA)

    # Check both the component inventory and the simple geometry values that
    # downstream visualization and analysis code expect.
    wings = list(vehicle.wings)
    fuselages = list(vehicle.fuselages)
    assert len(wings) == 3
    assert len(fuselages) == 1
    assert [wing.tag for wing in wings] == [
        "main_wing",
        "horizontal_stabilizer",
        "vertical_stabilizer",
    ]
    assert all(len(wing.segments) == 0 for wing in wings)
    assert wings[0].xz_plane_symmetric is True
    assert wings[1].xz_plane_symmetric is True
    assert wings[2].vertical is True
    assert wings[1].areas.reference == pytest.approx(3.6)
    assert wings[1].spans.projected == pytest.approx(3.8)
    assert wings[2].areas.reference == pytest.approx(1.9)
    assert wings[2].spans.projected == pytest.approx(1.7)
    assert len(fuselages[0].segments) == 0
    # Whole-aircraft and low-fidelity engine inputs survive object conversion.
    assert vehicle.tag == "Classroom Explorer"
    assert vehicle.number_of_passengers == 4
    assert vehicle.low_fidelity_engine.sfc_kg_per_n_hr == pytest.approx(0.06)


def test_learner_defaults_do_not_build_aircraft_before_save():
    """Entering Learner Mode pre-fills forms but leaves every model view empty."""
    from PyQt6.QtWidgets import QApplication, QLabel
    from tabs.learner.learner_tabs import LearnFlightWidget

    app = QApplication.instance() or QApplication([])
    clean = initialize_unbuilt_learner_workspace(DEFAULT_LEARNER_DATA)

    # Form defaults exist, but every runtime RCAIDE container stays empty.
    assert clean["vehicle"]["name"] == "Classroom Explorer"
    assert rcaide_io.learner_vehicle_built is False
    assert len(rcaide_io.vehicle.wings) == 0
    assert len(rcaide_io.vehicle.fuselages) == 0
    assert not rcaide_io.rcaide_configs
    assert not rcaide_io.rcaide_analyses
    assert rcaide_io.mission_data == []
    assert len(rcaide_io.rcaide_mission.segments) == 0
    # Dependent tabs show instructions rather than detached arrows or models.
    forces = LearnFlightWidget()
    forces.load_from_values()
    assert forces.canvas._grids == []
    assert forces.controls.isEnabled() is False
    assert "Build and save" in forces.result.text()
    forces.deleteLater()
    app.processEvents()

    # Keep following tests independent from this intentionally blank state.
    apply_learner_setup(DEFAULT_LEARNER_DATA)


def test_default_learner_mission_is_one_straight_cruise():
    """The hidden RCAIDE mission contains one production-style cruise segment."""
    from tabs.learner.learner import LEARNER_CRUISE_CONTROL_POINTS

    mission = build_learner_mission(DEFAULT_LEARNER_DATA)
    segments = list(mission.segments)

    assert len(segments) == 1
    assert segments[0].tag == "cruise"
    assert segments[0].altitude == pytest.approx(3000.0)
    assert segments[0].air_speed == pytest.approx(70.0)
    assert segments[0].distance == pytest.approx(250_000.0)
    assert (
        segments[0].state.numerics.number_of_control_points
        == LEARNER_CRUISE_CONTROL_POINTS
    )


# -----------------------------------------------------------------------------
# Geometry generation and model annotations
# -----------------------------------------------------------------------------
# Learner geometry is simple, but viewers must still receive valid surfaces and
# labels anchored to the aircraft's actual model-space coordinates.

def test_unsegmented_learner_fuselage_has_renderable_fallback_points():
    """Simple bodies without stations still produce a valid viewer surface."""
    fuselage = list(build_learner_vehicle(DEFAULT_LEARNER_DATA).fuselages)[0]
    geometry = generate_fuselage_points_for_viewer(fuselage, tessellation=24)

    assert len(fuselage.segments) == 0
    assert geometry.PTS.shape == (13, 24, 3)
    assert geometry.PTS.shape[0] >= 2


def test_learner_visualization_labels_all_basic_aircraft_components():
    """Callout data identifies the four components taught in Learner Mode."""
    vehicle = build_learner_vehicle(DEFAULT_LEARNER_DATA)
    points, labels = learner_component_label_data(vehicle)
    callouts = learner_component_callout_data(vehicle)

    # Labels and callouts cover the same four fundamental component categories.
    assert len(points) == 4
    assert labels == [
        "Main Wing\n(makes lift)",
        "Horizontal Stabilizer\n(pitch stability)",
        "Vertical Stabilizer\n(directional stability)",
        "Fuselage\n(aircraft body)",
    ]
    assert all(len(point) == 3 for point in points)
    assert all(callout["anchor"] != callout["label_position"] for callout in callouts)
    assert {callout["component"] for callout in callouts} == {
        "main_wing", "horizontal_stabilizer", "vertical_stabilizer", "fuselage"
    }


def test_learner_callouts_are_yellow_background_free_and_movable():
    """VTK labels use the requested style and remain grouped with the aircraft."""
    import pyvista as pv
    from tabs.visualize_geometry.visualize_geometry import add_learner_component_callouts

    plotter = pv.Plotter(off_screen=True)
    actors = []
    callouts = learner_component_callout_data(build_learner_vehicle(DEFAULT_LEARNER_DATA))
    add_learner_component_callouts(plotter, plotter.renderer, actors, callouts)

    assert len(actors) == 12  # line, anchor dot, and billboard text for four parts
    # Each component contributes a line, anchor dot, and billboard text actor.
    text_actors = actors[2::3]
    assert all(actor.GetTextProperty().GetColor() == (1.0, 0.84, 0.0) for actor in text_actors)
    assert all(actor.GetTextProperty().GetBackgroundOpacity() == 0.0 for actor in text_actors)
    # Moving the managed actor group must also move its text label.
    before = text_actors[0].GetPosition()
    for actor in actors:
        x, y, z = actor.GetPosition()
        actor.SetPosition(x + 1.0, y + 2.0, z + 3.0)
    after = text_actors[0].GetPosition()
    assert after == pytest.approx((before[0] + 1, before[1] + 2, before[2] + 3))
    plotter.close()


def test_activity_model_view_uses_the_built_rcaide_geometry():
    """Changing a learner input changes the actual previewed RCAIDE surface."""
    from copy import deepcopy
    from tabs.learner.model_view import aircraft_surface_grids

    # Compare vehicles that differ only in span to prove this is real geometry,
    # not a generic airplane diagram.
    normal = aircraft_surface_grids(build_learner_vehicle(DEFAULT_LEARNER_DATA))
    wide_data = deepcopy(DEFAULT_LEARNER_DATA)
    wide_data["wing"]["span_m"] = 18.0
    wide = aircraft_surface_grids(build_learner_vehicle(wide_data))

    assert {name for name, _ in normal} == {
        "main_wing", "horizontal_stabilizer", "vertical_stabilizer", "fuselage"
    }
    normal_wing = [points for name, points in normal if name == "main_wing"]
    wide_wing = [points for name, points in wide if name == "main_wing"]
    normal_span = max(points[:, :, 1].max() for points in normal_wing) - min(
        points[:, :, 1].min() for points in normal_wing
    )
    wide_span = max(points[:, :, 1].max() for points in wide_wing) - min(
        points[:, :, 1].min() for points in wide_wing
    )
    assert wide_span > normal_span


# -----------------------------------------------------------------------------
# Transparent learner calculations
# -----------------------------------------------------------------------------
# These checks lock down the readable classroom equations and qualitative rules
# used by activities; they remain separate from the RCAIDE mission solver.

def test_classroom_metrics_connect_geometry_to_flight_results():
    """First-order teaching metrics preserve their documented relationships."""
    metrics = classroom_metrics(DEFAULT_LEARNER_DATA)

    # Verify direct formulas instead of merely checking that values exist.
    assert metrics["wing_loading_kg_m2"] == pytest.approx(1100 / 16.2)
    assert metrics["aspect_ratio"] == pytest.approx(11 ** 2 / 16.2)
    assert metrics["cruise_time_hours"] == pytest.approx(250 / (70 * 3.6))
    assert metrics["stall_speed_m_s"] > 0
    assert metrics["lift_required_n"] == pytest.approx(1100 * 9.80665)


def test_classroom_loading_reports_weight_and_balance_status():
    """Loading combines empty mass, people, cargo, and fuel before status checks."""
    loading = classroom_loading(
        DEFAULT_LEARNER_DATA,
        passengers=4,
        cargo_kg=60,
        fuel_kg=132,
    )

    # This scenario deliberately exceeds the allowed mass, testing both the
    # arithmetic and status-priority rule.
    assert loading["total_mass_kg"] == pytest.approx(1192)
    assert loading["remaining_mass_kg"] == pytest.approx(-92)
    assert loading["status"] == "Over maximum takeoff weight"


def test_default_design_challenges_have_clear_pass_and_retry_results():
    """The example aircraft demonstrates both completed and retryable challenges."""
    results = evaluate_challenges(DEFAULT_LEARNER_DATA)

    assert len(results) == 5
    assert any(result["passed"] for result in results)
    assert any(not result["passed"] for result in results)


# -----------------------------------------------------------------------------
# Learner activity widgets and animation
# -----------------------------------------------------------------------------
# This broad integration scenario covers activities together because they share
# rcaide_io state and the lightweight AircraftModelViewport renderer.

def test_additional_learner_tabs_construct_and_refresh():
    """Exercise activity widgets, model motion, labels, loading, and animation."""
    from PyQt6.QtCore import QPointF
    from PyQt6.QtWidgets import QApplication, QGroupBox, QLabel
    from tabs.learner.learner_tabs import (
        CompareDesignsWidget,
        DesignChallengesWidget,
        LearnFlightWidget,
        LoadingWidget,
        TestFlightWidget,
        WordsHelpWidget,
    )
    from tabs.learner.model_view import AircraftModelViewport

    # Build a real learner aircraft before creating geometry-dependent tabs.
    app = QApplication.instance() or QApplication([])
    apply_learner_setup(DEFAULT_LEARNER_DATA)
    rcaide_io.learner_comparison_data = []
    widgets = [
        LearnFlightWidget(), TestFlightWidget(), CompareDesignsWidget(),
        LoadingWidget(), DesignChallengesWidget(), WordsHelpWidget(),
    ]
    for widget in widgets:
        widget.update_layout()

    assert widgets[1].start_button.text().startswith("▶")
    # A deliberately slow run should animate and stop with a readable failure.
    widgets[1].speed.setValue(50)
    assert "too slow" in widgets[1].air_card.value_label.text().lower()
    widgets[1].start_simulation()
    for _ in range(70):
        widgets[1]._step_simulation()
    widgets[1].timer.stop()
    assert widgets[1].canvas.progress > 0
    assert "sank" in widgets[1].start_button.text().lower()
    # Comparison, loading, challenge, and dictionary panels all read the same
    # current aircraft without exposing advanced jargon.
    widgets[2].save_current()
    assert widgets[2].table.rowCount() == 1
    assert widgets[2].table.columnCount() == 6
    assert 0.0 < widgets[3].balance_picture.balance < 1.0
    loading_text = " ".join(
        label.text() for label in widgets[3].findChildren(QLabel)
    ).lower()
    assert "cargo" in loading_text
    assert "fuel burn" in loading_text
    assert "school" not in loading_text
    assert "classroom" not in loading_text
    assert widgets[4].list.count() == 5
    assert widgets[5].words.count() >= 10
    assert all(widget.property("learnerPage") for widget in widgets)
    assert all(widget.findChildren(AircraftModelViewport) for widget in widgets)
    # Teaching views stay camera-locked; inspection views allow manipulation.
    assert widgets[0].canvas.interactive is False
    assert widgets[1].canvas.interactive is False
    assert widgets[3].balance_picture.interactive is False
    assert widgets[2].preview.interactive is True
    assert widgets[4].preview.interactive is False
    assert widgets[5].preview.interactive is True
    assert widgets[5].preview._grids
    assert not hasattr(widgets[5], "search")
    assert len(widgets[5]._model_callouts) == 4
    # Geometry terms create measurement guides rather than duplicate labels.
    widgets[5]._show_word("Span")
    assert widgets[5].preview.highlight == "main_wing"
    assert widgets[5].preview.selected_callout is None
    assert widgets[5].preview.callouts == []
    assert widgets[5].preview.guides[0]["text"] == "span"
    widgets[5]._show_word("Chord")
    assert widgets[5].preview.guides[0]["text"] == "chord"
    assert widgets[5].preview._interaction_timer.interval() == 16
    # Force controls move and tilt the cached teaching aircraft immediately.
    teaching_canvas = widgets[0].canvas
    original_position = teaching_canvas.model_offset()
    original_attitude = teaching_canvas.model_screen_rotation()
    widgets[0].push.setValue(100)
    assert teaching_canvas.model_offset().x() > original_position.x()
    widgets[0].wing_angle.setValue(15)
    assert teaching_canvas.model_screen_rotation() < original_attitude
    # Verify wheel contact, caching, stage attitude, gear schedule, and route.
    flight_canvas = widgets[1].canvas
    flight_canvas.resize(640, 360)
    flight_canvas.progress = 0.0
    cached_model = flight_canvas._model_layer()
    start_offset = flight_canvas.model_offset()
    _, _, main_wheel, nose_wheel = flight_canvas._landing_gear_geometry()
    model_center = QPointF(flight_canvas._model_rect().center()) + start_offset
    runway_y = flight_canvas.flight_path_point(0.0).y()
    assert model_center.y() + main_wheel.y() == pytest.approx(runway_y)
    assert model_center.y() + nose_wheel.y() == pytest.approx(runway_y)
    flight_canvas.progress = 0.5
    assert flight_canvas._model_layer() is cached_model
    assert flight_canvas.model_offset() != start_offset
    assert flight_canvas.yaw == pytest.approx(90.0)
    assert widgets[4].preview.yaw == pytest.approx(135.0)
    assert flight_canvas.phase_for_progress(0.0) == ("TAKEOFF", True, 0.0)
    assert flight_canvas.phase_for_progress(0.2)[0:2] == ("CLIMB", False)
    assert flight_canvas.phase_for_progress(0.5)[0:2] == ("CRUISE", False)
    assert flight_canvas.phase_for_progress(0.78)[0:2] == ("DESCENT", False)
    assert flight_canvas.phase_for_progress(0.95)[0:2] == ("LANDING", True)
    assert flight_canvas.flight_path_point(0.5).y() < flight_canvas.flight_path_point(0.0).y()
    # Guard visible learner copy against unexplained engineering abbreviations.
    visible_words = " ".join(
        child.text()
        for widget in widgets
        for widget_type in (QLabel, QGroupBox)
        for child in widget.findChildren(widget_type)
        if hasattr(child, "text")
    ).lower()
    assert "clmax" not in visible_words
    assert "mtow" not in visible_words
    assert "dictionary" in visible_words
    # Release widgets so timers and rendering resources cannot leak to tests.
    for widget in widgets:
        widget.deleteLater()
    app.processEvents()


# -----------------------------------------------------------------------------
# Persistence and experience-mode isolation
# -----------------------------------------------------------------------------
# Learner metadata belongs in learner saves, while Advanced Mode must recover
# the exact tabs and live RCAIDE objects it had before a mode switch.

def test_saved_design_comparisons_are_in_normal_json_output():
    """Learner comparison records survive a learner-inclusive JSON save."""
    apply_learner_setup(DEFAULT_LEARNER_DATA)
    rcaide_io.learner_comparison_data = [DEFAULT_LEARNER_DATA]

    # Serialize compact inputs, not derived model meshes or widget state.
    saved = json.loads(rcaide_io.write_to_json())

    assert len(saved["learner_comparison_data"]) == 1
    assert saved["learner_comparison_data"][0]["vehicle"]["name"] == "Classroom Explorer"


def test_simplified_mission_and_results_tabs_share_the_latest_run():
    """Legacy learner activity widgets exchange mission and result summaries."""
    from PyQt6.QtWidgets import QApplication
    from tabs.learner.learner_tabs import LearnerMissionWidget, LearnerResultsWidget

    app = QApplication.instance() or QApplication([])
    apply_learner_setup(DEFAULT_LEARNER_DATA)
    mission = LearnerMissionWidget()
    mission.distance.setValue(360)
    mission.speed.setValue(60)
    mission.save_mission()
    assert rcaide_io.learner_data["mission"]["distance_km"] == pytest.approx(360)
    assert "100 minutes" in mission.status.text()

    # Mimic a completed flight and confirm the results tab reads shared state.
    rcaide_io.learner_last_run = {
        "success": True,
        "aircraft": "Classroom Explorer",
        "speed_kmh": 216,
        "load_percent": 100,
        "minimum_speed_kmh": 130,
        "trip_minutes": 100,
        "speed_margin": 1.4,
    }
    results = LearnerResultsWidget()
    assert results.outcome.value_label.text() == "Mission completed"
    assert "100 minutes" in results.trip.value_label.text()
    mission.deleteLater()
    results.deleteLater()
    app.processEvents()


def test_advanced_json_export_omits_learner_workspace_metadata():
    """Advanced saves do not acquire learner-only workspace records."""
    apply_learner_setup(DEFAULT_LEARNER_DATA)
    saved = json.loads(rcaide_io.write_to_json(include_learner=False))

    assert "learner_data" not in saved
    assert "learner_comparison_data" not in saved


def test_mode_switch_restores_original_advanced_tabs_state_and_objects(monkeypatch):
    """A learner visit cannot replace Advanced Mode tabs or RCAIDE objects."""
    import RCAIDE
    from PyQt6.QtWidgets import QApplication
    import main
    from tabs import TabWidget

    class _GeometryStub(TabWidget):
        pass

    # Stub heavyweight geometry tabs so this test isolates mode/state behavior.
    monkeypatch.setattr(main.visualize_geometry, "get_widget", _GeometryStub)
    monkeypatch.setattr(main.geometry, "get_widget", _GeometryStub)
    ADVANCED_STATE_FIELDS = main.ADVANCED_STATE_FIELDS
    ADVANCED_TAB_NAMES = main.ADVANCED_TAB_NAMES
    LEARNER_TAB_NAMES = main.LEARNER_TAB_NAMES

    app = QApplication.instance() or QApplication([])
    window = main.App()
    rcaide_io.vehicle = RCAIDE.Vehicle()
    rcaide_io.rcaide_results = object()
    window.advanced_tabs.setCurrentIndex(5)
    # Identity matters because advanced widgets retain references to containers.
    original = {field: getattr(rcaide_io, field) for field in ADVANCED_STATE_FIELDS}

    rcaide_io.learner_vehicle_built = False
    window.set_experience_mode("learner")
    assert rcaide_io.learner_vehicle_built is False
    assert len(rcaide_io.vehicle.wings) == 0
    assert window.learner_tabs.currentIndex() == 0
    assert tuple(
        window.learner_tabs.tabText(i) for i in range(window.learner_tabs.count())
    ) == LEARNER_TAB_NAMES

    # Returning must restore both interface order and original object identity.
    window.set_experience_mode("advanced")
    assert tuple(
        window.advanced_tabs.tabText(i) for i in range(window.advanced_tabs.count())
    ) == ADVANCED_TAB_NAMES
    assert window.tabs is window.advanced_tabs
    assert window.advanced_tabs.currentIndex() == 5
    for field, value in original.items():
        assert getattr(rcaide_io, field) is value

    window.shutdown_vtk()


# -----------------------------------------------------------------------------
# Shared production Mission and Run Mission integration
# -----------------------------------------------------------------------------
# Learner Mode restricts inherited widgets rather than creating a second solver.
# These tests protect form compatibility, animation opt-in, relabeling, plotting,
# and loading-dialog lifecycle.

def test_learner_mission_can_load_in_advanced_mission_editor():
    """The compact learner cruise record remains valid production form data."""
    record = learner_mission_form_data(DEFAULT_LEARNER_DATA)[0]
    assert record["top dropdown"] == 1
    assert record["nested dropdown"] == "Constant Speed-Constant Altitude"
    assert record["flight forces"]["Forces in X axis"][0] is True
    assert record["flight forces"]["Forces in Z axis"][0] is True


def test_single_cruise_mission_profile_animates():
    """Single-phase animation is opt-in for learners and unchanged by default."""
    from PyQt6.QtWidgets import QApplication
    from tabs.mission.mission import MissionProfileWidget

    app = QApplication.instance() or QApplication([])
    # Advanced behavior stays still unless learner mode explicitly opts in.
    profile = MissionProfileWidget()
    profile.set_phases([("Cruise", "cruise")])
    start = profile._progress
    profile._advance_animation()
    assert profile._progress == start

    profile.animate_single_phase = True
    profile._advance_animation()
    assert profile._progress > start
    profile.deleteLater()
    app.processEvents()


def test_learner_mission_refreshes_advanced_summary_without_legacy_values_name():
    """The shared mission summary reads current rcaide_io configuration data."""
    from PyQt6.QtWidgets import QApplication
    from tabs.mission.mission import MissionWidget
    from tabs.learner.learner import apply_learner_setup

    app = QApplication.instance() or QApplication([])
    apply_learner_setup(DEFAULT_LEARNER_DATA)
    # Use the production widget directly to catch learner-only dependencies.
    widget = MissionWidget()
    widget.load_from_values()

    assert len(widget.segment_widgets) == 1
    assert widget.summary_table.rowCount() == 1
    assert widget.summary_table.item(0, 0).text().lower() == "cruise"
    widget.deleteLater()
    app.processEvents()


def test_learner_workflow_tabs_are_simplified_real_rcaide_tabs():
    """Learner mission tabs restrict, relabel, and reuse production widgets."""
    from PyQt6.QtWidgets import QApplication, QLabel
    from tabs.learner.rcaide_tabs import (
        LearnerMissionSetupWidget,
        LearnerSolveWidget,
    )
    from tabs.mission.mission import MissionWidget
    from tabs.run_mission.run_mission import SolveWidget

    app = QApplication.instance() or QApplication([])
    apply_learner_setup(DEFAULT_LEARNER_DATA)
    mission = LearnerMissionSetupWidget()
    solve = LearnerSolveWidget()
    mission.load_from_values()

    # Inheritance confirms these are presentation wrappers, not parallel tools.
    assert isinstance(mission, MissionWidget)
    assert isinstance(solve, SolveWidget)
    assert mission.add_segment_btn.isHidden()
    assert not mission.tree.isHidden()
    assert not mission.summary_table.isHidden()
    assert solve.settings_panel.isHidden()
    # Questions replace engineering labels while the familiar layout remains.
    learner_labels = {
        label.text() for label in mission.findChildren(QLabel) if not label.isHidden()
    }
    assert "How high will it fly?" in learner_labels
    assert "How fast will it fly?" in learner_labels
    assert "How far will it travel?" in learner_labels
    assert "Direction of travel:" in learner_labels
    segment = mission.segment_widgets[0]
    assert not segment.segment_name_input.isHidden()
    assert not segment.top_dropdown.isHidden()
    assert not segment.nested_dropdown.isHidden()
    assert "air density" in " ".join(learner_labels).lower()
    # Every graph receives an adjacent explanation whose row cleans up with it.
    lift_plot = solve._new_plot_widget("Aerodynamic Forces: Lift", "Lift (kN)")
    lift_row = solve._learner_plot_rows[lift_plot]
    lift_help = " ".join(
        label.text() for label in lift_row.findChildren(QLabel)
    ).lower()
    assert "upward push" in lift_help
    solve.clear_dynamic_plot_widgets()
    # Only learner-relevant production renderer choices remain visible.
    visible_plot_names = []
    for i in range(solve.tree.topLevelItemCount()):
        category = solve.tree.topLevelItem(i)
        for j in range(category.childCount()):
            child = category.child(j)
            if not child.isHidden():
                visible_plot_names.append(child.text(0))
    assert visible_plot_names == [
        "Engine push, lift, and drag",
        "Cruise speed and altitude",
    ]
    # Exercise both dialog transitions to guard against reentrant cleanup errors.
    solve._set_loading_state(True)
    assert solve.loading_dialog is not None
    solve._set_loading_state(False)
    assert solve.loading_dialog is None
    assert list(rcaide_io.rcaide_configs.keys()) == ["base"]
    assert list(rcaide_io.rcaide_analyses.keys()) == ["base"]

    for widget in (mission, solve):
        widget.deleteLater()
    app.processEvents()


def test_learner_cruise_graphs_use_production_result_arrays():
    """Learner plots use RCAIDE arrays plus pointwise low-fidelity engine data."""
    import numpy as np
    from PyQt6.QtWidgets import QApplication
    from RCAIDE.Framework.Core import Data
    from tabs.learner.rcaide_tabs import (
        LearnerSolveWidget,
        add_learner_low_fidelity_engine_results,
    )

    app = QApplication.instance() or QApplication([])
    apply_learner_setup(DEFAULT_LEARNER_DATA)

    results = Data()
    results.segments = Data()
    cruise = Data()
    cruise.tag = "cruise"
    cruise.conditions = Data()
    cruise.conditions.frames = Data()
    cruise.conditions.frames.wind = Data()
    cruise.conditions.frames.wind.force_vector = np.array([
        [-896.0, 0.0, -10787.0],
        [-900.0, 0.0, -10790.0],
        [-904.0, 0.0, -10793.0],
    ])
    cruise.conditions.frames.body = Data()
    cruise.conditions.frames.inertial = Data()
    cruise.conditions.frames.inertial.time = np.array([[0.0], [1800.0], [3600.0]])
    cruise.conditions.frames.inertial.aircraft_range = np.array(
        [[0.0], [125000.0], [250000.0]]
    )
    cruise.conditions.freestream = Data()
    cruise.conditions.freestream.altitude = np.full((3, 1), 3000.0)
    cruise.conditions.freestream.velocity = np.full((3, 1), 70.0)
    cruise.conditions.energy = Data()
    cruise.conditions.weights = Data()
    results.segments.cruise = cruise

    solve = LearnerSolveWidget()
    add_learner_low_fidelity_engine_results(results)
    assert cruise.conditions.frames.body.thrust_force_vector[:, 0] == pytest.approx(
        [896.0, 900.0, 904.0]
    )
    assert cruise.conditions.energy.power[:, 0] == pytest.approx(
        [62720.0, 63000.0, 63280.0]
    )

    # The inherited production renderer must preserve every RCAIDE time point.
    parameters = solve._build_plot_parameters(results)
    solve._render_aerodynamic_forces_pg(results, parameters)
    power_curve = solve._dynamic_plot_widgets[0].listDataItems()[0]
    x_values, y_values = power_curve.getData()
    assert x_values == pytest.approx([0.0, 30.0, 60.0])
    assert y_values == pytest.approx([0.06272, 0.063, 0.06328])

    solve.deleteLater()
    app.processEvents()
