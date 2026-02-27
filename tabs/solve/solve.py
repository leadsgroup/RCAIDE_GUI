# RCAIDE_GUI/tabs/solve/solve.py
# 
# Created: Oct 2024, Laboratory for Electric Aircraft Design and Sustainabiltiy

# ----------------------------------------------------------------------------------------------------------------------
#  IMPORT
# ---------------------------------------------------------------------------------------------------------------------- 
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QPushButton, QTreeWidgetItem, QHeaderView, QLabel, QScrollArea, QProgressDialog, QMessageBox
from PyQt6.QtCore import Qt, QSize, QObject, QThread, QTimer, pyqtSignal
import pyqtgraph as pg

# numpy imports 
import numpy as np
import re
import traceback
import os
from datetime import datetime

# gui imports 
from tabs import TabWidget
from .plots.create_plot_widgets import create_plot_widgets


class _SolveWorker(QObject):
    finished = pyqtSignal(object, str)
    failed = pyqtSignal(str)

    def __init__(self, mission):
        super().__init__()
        self._mission = mission

    def run(self):
        try:
            # Let solver output stream directly to terminal so native progress bar rendering is preserved.
            results = self._mission.evaluate()
            self.finished.emit(results, "")
        except Exception:
            self.failed.emit(traceback.format_exc())

# ----------------------------------------------------------------------------------------------------------------------
#  SolveWidget
# ----------------------------------------------------------------------------------------------------------------------  
class SolveWidget(TabWidget):
    # Maps each tree option label to the corresponding SolveWidget renderer method.
    _PLOT_OPTION_RENDERERS = {
        "Plot Aircraft Velocities": "_render_aircraft_velocities",
        "Plot Aerodynamic Coefficients": "_render_aerodynamic_coefficients_pg",
        "Plot Aerodynamic Forces": "_render_aerodynamic_forces_pg",
        "Plot Drag Components": "_render_drag_components_pg",
        "Plot Lift Distribution": "_render_lift_distribution_pg",
        "Plot Rotor Conditions": "_render_rotor_conditions_pg",
        "Plot Altitude SFC Weight": "_render_altitude_sfc_weight_pg",
        "Plot Propulsor Throttles": "_render_propulsor_throttles_pg",
        "Plot Flight Conditions": "_render_flight_conditions_pg",
        "Plot Flight Trajectory": "_render_flight_trajectory_pg",
        "Plot Flight Forces and Moments": "_render_flight_forces_moments_pg",
        "Plot Longitudinal Stability": "_render_longitudinal_stability_pg",
        "Plot Lateral Stability": "_render_lateral_stability_pg",
    }
    # Aliases for options that intentionally reuse an existing renderer.
    _PLOT_OPTION_ALIASES = {
        "Plot Rotor Disc Inflow": "Plot Rotor Conditions",
        "Plot Rotor Disc Performance": "Plot Rotor Conditions",
        "Plot Rotor Performance": "Plot Rotor Conditions",
        "Plot Disc and Power Loading": "Plot Rotor Conditions",
        "Plot Fuel Consumption": "Plot Altitude SFC Weight",
    }
    # Drag-coefficient components plotted in the drag breakdown chart.
    _DRAG_COMPONENTS = (
        ("CDpar", ("parasite", "total")),
        ("CDind", ("induced", "total")),
        ("CDcomp", ("compressible", "total")),
        ("CDmisc", ("miscellaneous", "total")),
        ("CDwave", ("wave", "total")),
        ("CDcool", ("cooling", "total")),
        ("CDform", ("form", "total")),
        ("CD", ("total",)),
    )

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
        # Custom state used by background solve execution + loading dialog.
        self.solve_button = solve_button
        self.loading_dialog = None
        self._solve_thread = None
        self._solve_worker = None
        self._is_rendering_plots = False
        self._plot_render_timer = QTimer(self)
        self._plot_render_timer.setSingleShot(True)
        self._plot_render_timer.timeout.connect(self._render_from_latest_results)
        self._last_skipped_signature = None

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
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # scroll_area.setFixedSize(1500, 900)  # Set a designated scroll area size

        # Create a container widget for the plots
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.plot_layout = plot_layout
        self._dynamic_plot_widgets = []

        plot_size = QSize(620, 400)  # Slightly narrower to avoid lateral scrolling
        show_legend = True
        create_plot_widgets(self,plot_layout,plot_size,show_legend) 
        self._base_plot_widgets = [
            self.aircraft_TAS_plot,
            self.aircraft_EAS_plot,
            self.aircraft_Mach_plot,
            self.aircraft_CAS_plot,
        ]

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
        # Two columns: option name + check state.
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Plot Options", "Enabled"])

        # Size first column to fit option text.
        header = self.tree.header()
        assert header is not None
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)

        # Add category rows and child plot options.
        for category, options in self.plot_options.items():
            category_item = QTreeWidgetItem([category])
            self.tree.addTopLevelItem(category_item)

            for option in options:
                option_item = QTreeWidgetItem([option])
                option_item.setCheckState(
                    1, Qt.CheckState.Checked)  # Initially checked

                category_item.addChild(option_item)

    def run_solve(self):
        # Use local imports to avoid extra startup/circular import issues.
        import values
        from tabs.mission.widgets.mission_analysis_widget import MissionAnalysisWidget
        from tabs.mission.widgets.mission_segment_widget import MissionSegmentWidget

        # Read mission built in Mission tab.
        mission = getattr(values, "rcaide_mission", None)
        if mission is None:
            raise RuntimeError("No mission defined.")

        # Read saved aircraft configs, or build them from geometry if missing.
        configs = getattr(values, "rcaide_configs", None)
        if not isinstance(configs, dict) or not configs:
            try:
                from tabs.aircraft_configs.aircraft_configs import build_rcaide_configs_from_geometry
                # Save generated configs so other tabs can reuse them.
                values.rcaide_configs = build_rcaide_configs_from_geometry()
                configs = values.rcaide_configs
            except Exception as e:
                # Stop with clear user guidance if configs cannot be created.
                raise RuntimeError(
                    "No RCAIDE aircraft configs available.\n"
                    "Go to Aircraft Configurations tab and press 'Save Configuration'."
                ) from e

        # If mission has no segments, rebuild it from saved mission_data.
        if not getattr(mission, "segments", []):
            if values.mission_data:
                # Ensure analyses exist before rebuilding segments.
                if not getattr(values, "rcaide_analyses", None):
                    MissionAnalysisWidget().save_analyses()

                # Recreate mission and append each saved segment.
                import RCAIDE
                mission = RCAIDE.Framework.Mission.Sequential_Segments()
                for seg_data in values.mission_data:
                    seg = MissionSegmentWidget()
                    seg.load_data(seg_data)
                    _, rcaide_segment = seg.get_data()
                    mission.append_segment(rcaide_segment)

                # Save rebuilt mission back to shared state.
                values.rcaide_mission = mission
            else:
                # No mission to run.
                raise RuntimeError("No mission segments available. Save the mission first.")

        # Ignore click if a solve is already running.
        if self._solve_thread is not None and self._solve_thread.isRunning():
            return

        # Start solve with loading popup.
        print("Commencing Mission Simulation")
        self._set_loading_state(True)
        self._start_solve_worker(mission)

    def _start_solve_worker(self, mission):
        # Create worker thread so UI does not freeze during solve.
        self._solve_thread = QThread(self)
        self._solve_worker = _SolveWorker(mission)
        self._solve_worker.moveToThread(self._solve_thread)

        # Wire start/success/failure/cleanup signals.
        self._solve_thread.started.connect(self._solve_worker.run)
        self._solve_worker.finished.connect(self._on_solve_finished)
        self._solve_worker.failed.connect(self._on_solve_failed)
        self._solve_worker.finished.connect(self._solve_thread.quit)
        self._solve_worker.failed.connect(self._solve_thread.quit)
        self._solve_thread.finished.connect(self._cleanup_solve_worker)
        self._solve_thread.start()

    def _cleanup_solve_worker(self):
        # Safely release worker objects after thread exits.
        if self._solve_worker is not None:
            self._solve_worker.deleteLater()
            self._solve_worker = None
        if self._solve_thread is not None:
            self._solve_thread.deleteLater()
            self._solve_thread = None

    def _set_loading_state(self, is_loading):
        # Lock solve controls while mission is running.
        self.solve_button.setEnabled(not is_loading)
        self.tree.setEnabled(not is_loading)

        if is_loading:
            # Show modal loading popup.
            dialog = QProgressDialog("Running mission simulation...", "", 0, 0, self)
            dialog.setWindowTitle("Simulating Mission")
            dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
            dialog.setCancelButton(None)
            dialog.setMinimumDuration(0)
            dialog.setAutoClose(False)
            dialog.setAutoReset(False)
            dialog.show()
            self.loading_dialog = dialog
            return

        if self.loading_dialog is not None:
            # Hide loading popup when solve completes/fails.
            self.loading_dialog.close()
            self.loading_dialog.deleteLater()
            self.loading_dialog = None

    def _on_solve_finished(self, results, output):
        import values
        # Parse and print solver warnings (if any).
        warnings = _summarize_solve_output(output)
        if warnings and not _warnings_already_reported(output):
            print("Mission completed with solver warnings:")
            for warning in warnings:
                print(f"- {warning}")

        # Store results and refresh plots.
        print("Completed Mission Simulation")
        values.rcaide_results = results
        self.render_solve_plots(results)
        self._set_loading_state(False)

    def _on_solve_failed(self, error_message):
        # Restore UI state and surface error details.
        self._set_loading_state(False)
        print("Mission simulation failed.")
        print(error_message)
        QMessageBox.critical(self, "Mission Simulation Failed", error_message)

    def render_solve_plots(self, results):
        # Main render entry point: rebuild plots from current checked options.
        if self._is_rendering_plots:
            return
        self._is_rendering_plots = True
        self.setUpdatesEnabled(False)
        try:
            self.clear_plot_widgets()
            self.clear_dynamic_plot_widgets()
            for widget in self._base_plot_widgets:
                widget.setVisible(False)
            plot_parameters = self._build_plot_parameters(results)

            rendered = set()
            skipped = []
            for option in self._collect_checked_plot_options():
                key, renderer = self._resolve_plot_renderer(option)
                if key in rendered:
                    continue
                # Option exists in the tree but no renderer is wired for it.
                if renderer is None:
                    skipped.append(f"{option}: no renderer")
                    continue
                start_idx = len(self._dynamic_plot_widgets)
                try:
                    # Each renderer can raise RuntimeError when its required
                    # result fields are missing. We treat that as a per-plot
                    # skip so the rest of the selected plots still render.
                    renderer(results, plot_parameters)
                    self._remove_empty_dynamic_plots(start_idx)
                    rendered.add(key)
                except Exception as exc:
                    # Roll back widgets created by this renderer and record
                    # the reason so the user knows why this plot was skipped.
                    self._clear_dynamic_widgets_from(start_idx)
                    skipped.append(f"{option}: {exc}")

            self._log_skipped_plot_entries(skipped)
            if hasattr(self, "apply_plot_settings"):
                self.apply_plot_settings()
        finally:
            self.setUpdatesEnabled(True)
            self._is_rendering_plots = False

    def clear_plot_widgets(self):
        # Clear data items from all plot widgets (keeps widgets alive).
        for widget in self.findChildren(pg.PlotWidget):
            widget.clear()

    def _collect_checked_plot_options(self):
        # Return a list of plot options that are currently checked.
        checked_options = []
        for i in range(self.tree.topLevelItemCount()):
            category_item = self.tree.topLevelItem(i)
            # Skip invalid category rows.
            if category_item is None:
                continue
            for j in range(category_item.childCount()):
                option_item = category_item.child(j)
                # Keep only checked child options.
                if option_item is not None and option_item.checkState(1) == Qt.CheckState.Checked:
                    checked_options.append(option_item.text(0))
        return checked_options

    def _resolve_plot_renderer(self, option):
        # Map a tree option name to the renderer method that draws it.
        key = self._PLOT_OPTION_ALIASES.get(option, option)
        method_name = self._PLOT_OPTION_RENDERERS.get(key)
        # No renderer is registered for this option.
        if method_name is None:
            return key, None
        return key, getattr(self, method_name, None)

    def _clear_dynamic_widgets_from(self, start_idx):
        # Remove dynamic plots created after a given index.
        to_remove = self._dynamic_plot_widgets[start_idx:]
        self._dynamic_plot_widgets = self._dynamic_plot_widgets[:start_idx]
        self._delete_plot_widgets(to_remove)

    def _log_skipped_plot_entries(self, skipped):
        # Print skipped-plot reasons, but only when the list changes.
        if skipped:
            signature = tuple(sorted(skipped))
            # Avoid printing the same skip messages over and over.
            if signature != self._last_skipped_signature:
                print("Some selected plots were skipped:")
                for entry in skipped[:8]:
                    print(f"- {entry}")
            self._last_skipped_signature = signature
        else:
            # Clear last signature when nothing is skipped.
            self._last_skipped_signature = None

    def _schedule_plot_render(self):
        # Debounce rapid checkbox changes into one redraw.
        self._plot_render_timer.start(80)

    def _render_from_latest_results(self):
        # Rebuild plots from the latest saved mission results.
        import values
        results = getattr(values, "rcaide_results", None)
        # Only render when results exist.
        if results is not None:
            self.render_solve_plots(results)

    def clear_dynamic_plot_widgets(self):
        # Delete all dynamic plots from the layout.
        self._delete_plot_widgets(self._dynamic_plot_widgets)
        self._dynamic_plot_widgets = []

    def _delete_plot_widgets(self, widgets):
        # Remove widgets from layout and free them safely.
        for widget in widgets:
            self.plot_layout.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()

    def _new_plot_widget(self, title, y_label, x_label="Time (min)", show_legend=True):
        # Create one new plot widget and add it to the dynamic list.
        widget = pg.PlotWidget()
        widget.setFixedSize(QSize(620, 380))
        widget.setBackground("#0e141b")
        plot_item = widget.getPlotItem()
        plot_item.showGrid(x=True, y=True, alpha=0.15)
        for axis_name in ("left", "bottom"):
            axis = plot_item.getAxis(axis_name)
            axis.setPen(pg.mkPen("#4da3ff"))
            axis.setTextPen(pg.mkPen("#9fb8ff"))
        plot_item.getViewBox().setBorder(pg.mkPen("#1f2a36"))
        widget.setLabel("left", y_label, color="white", size="18px")
        widget.setLabel("bottom", x_label, color="white", size="18px")
        widget.setTitle(title, color="#9fb8ff", size="14pt")
        # Add legend only when legend toggle is enabled.
        if hasattr(self, "legend_check") and self.legend_check.isChecked():
            legend = widget.addLegend(offset=(10, 10))
            # Style legend when it was created.
            if legend is not None:
                legend.setBrush(pg.mkBrush(8, 12, 18, 180))
                legend.setPen(pg.mkPen(120, 150, 210, 140))
            self._position_plot_legend(widget)
        self.plot_layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._dynamic_plot_widgets.append(widget)
        return widget

    def _position_plot_legend(self, plot_widget):
        # Keep legend fixed in the top-right corner.
        legend = plot_widget.plotItem.legend
        # Nothing to place if legend is missing.
        if legend is None:
            return
        try:
            legend.setParentItem(plot_widget.getPlotItem().getViewBox())
            legend.anchor(itemPos=(1, 0), parentPos=(1, 0), offset=(-10, 10))
            legend.setBrush(pg.mkBrush(8, 12, 18, 180))
            legend.setPen(pg.mkPen(120, 150, 210, 140))
        except Exception:
            # Ignore legend anchor/styling errors to avoid breaking plotting.
            pass

    def _segment_style(self, i, plot_parameters):
        # Build color and marker style for one mission segment.
        rgba = plot_parameters.line_colors[i] * 255.0
        line_color = (int(rgba[0]), int(rgba[1]), int(rgba[2]))
        pen = pg.mkPen(color=line_color, width=plot_parameters.line_width)
        symbol = plot_parameters.markers[0] if plot_parameters.markers else 'o'
        return pen, line_color, symbol

    def _has_attr_chain(self, obj, chain):
        # Check whether all nested attributes exist on an object.
        cur = obj
        for name in chain:
            # Stop early when any part of the path is missing.
            if not hasattr(cur, name):
                return False
            cur = getattr(cur, name)
        return True

    def _units(self):
        # Return shared RCAIDE unit conversions.
        from RCAIDE.Framework.Core import Units
        return Units

    def _plot_time_series(self, widget, results, plot_parameters, y_fn):
        # Plot one time-series curve per mission segment.
        for segment, time, pen, brush, symbol, tag in self._iter_segments_with_style(results, plot_parameters):
            y = np.asarray(y_fn(segment)).reshape(-1)
            widget.plot(time, y, pen=pen, symbol=symbol, symbolBrush=brush, symbolSize=plot_parameters.marker_size, name=tag)

    def _iter_segments_with_style(self, results, plot_parameters):
        # Yield segment data plus plotting style and label.
        U = self._units()
        for i, segment in enumerate(results.segments):
            time = segment.conditions.frames.inertial.time[:, 0] / U.min
            pen, brush, symbol = self._segment_style(i, plot_parameters)
            yield segment, time, pen, brush, symbol, segment.tag.replace("_", " ")

    def _render_time_series_group(self, results, plot_parameters, specs, x_label="Time (min)"):
        # Create and fill a group of time-series plots.
        for title, y_label, y_fn, show_legend in specs:
            widget = self._new_plot_widget(title, y_label, x_label=x_label, show_legend=show_legend)
            self._plot_time_series(widget, results, plot_parameters, y_fn)

    def _render_aircraft_velocities(self, results, plot_parameters):
        # Fill the base aircraft-velocity plots.
        from .plots.mission import plot_aircraft_velocities
        for widget in self._base_plot_widgets:
            widget.setVisible(True)
        plot_aircraft_velocities(self, results, plot_parameters)

    def _render_aerodynamic_coefficients_pg(self, results, plot_parameters):
        # Plot AoA, L/D, CL, and CD.
        U = self._units()
        self._render_time_series_group(results, plot_parameters, [
            ("Aerodynamic Coefficients: AoA", "AoA (deg)", lambda s: s.conditions.aerodynamics.angles.alpha[:, 0] / U.deg, True),
            ("Aerodynamic Coefficients: L/D", "L/D", lambda s: s.conditions.aerodynamics.coefficients.lift.total[:, 0] / np.clip(s.conditions.aerodynamics.coefficients.drag.total[:, 0], 1e-9, None), False),
            ("Aerodynamic Coefficients: CL", "CL", lambda s: s.conditions.aerodynamics.coefficients.lift.total[:, 0], False),
            ("Aerodynamic Coefficients: CD", "CD", lambda s: s.conditions.aerodynamics.coefficients.drag.total[:, 0], False),
        ])

    def _render_aerodynamic_forces_pg(self, results, plot_parameters):
        # Plot aerodynamic power, thrust, lift, and drag.
        self._render_time_series_group(results, plot_parameters, [
            ("Aerodynamic Forces: Power", "Power (MW)", lambda s: s.conditions.energy.power[:, 0] / 1e6, True),
            ("Aerodynamic Forces: Thrust", "Thrust (kN)", lambda s: s.conditions.frames.body.thrust_force_vector[:, 0] / 1000.0, False),
            ("Aerodynamic Forces: Lift", "Lift (kN)", lambda s: -s.conditions.frames.wind.force_vector[:, 2] / 1000.0, False),
            ("Aerodynamic Forces: Drag", "Drag (kN)", lambda s: -s.conditions.frames.wind.force_vector[:, 0] / 1000.0, False),
        ])

    def _render_drag_components_pg(self, results, plot_parameters):
        # Plot drag breakdown components.
        U = self._units()
        widget = self._new_plot_widget("Drag Components", "Drag Coefficient", show_legend=True)
        for i, segment in enumerate(results.segments):
            time = segment.conditions.frames.inertial.time[:, 0] / U.min
            drag = segment.conditions.aerodynamics.coefficients.drag
            cd_total = np.asarray(drag.total[:, 0]).reshape(-1)
            pen, brush, symbol = self._segment_style(i, plot_parameters)
            for name, chain in self._DRAG_COMPONENTS:
                value = drag
                try:
                    for key in chain:
                        value = getattr(value, key)
                    arr_np = np.asarray(value)
                    arr = arr_np[:, 0].reshape(-1) if arr_np.ndim > 1 else arr_np.reshape(-1)
                except Exception:
                    # Missing drag component: plot zeros for that component.
                    arr = np.zeros_like(cd_total)
                label = name if i == 0 else None
                widget.plot(time, arr, pen=pen, symbol=symbol, symbolBrush=brush, symbolSize=plot_parameters.marker_size, name=label)

    def _render_lift_distribution_pg(self, results, plot_parameters):
        # Plot final spanwise lift distribution for each segment.
        if not self._has_attr_chain(
            results.segments[0].conditions,
            ["aerodynamics", "coefficients", "lift", "inviscid", "spanwise"]
        ):
            # This plot needs spanwise lift data; skip when not available.
            raise RuntimeError("no spanwise lift data")
        widget = self._new_plot_widget("Lift Distribution", "Spanwise Lift Coefficient", "Span Index", show_legend=True)
        for i, segment in enumerate(results.segments):
            spanwise = np.asarray(segment.conditions.aerodynamics.coefficients.lift.inviscid.spanwise)
            y = np.asarray(spanwise[-1]).reshape(-1)
            x = np.arange(y.size)
            pen, brush, symbol = self._segment_style(i, plot_parameters)
            tag = segment.tag.replace("_", " ")
            widget.plot(x, y, pen=pen, symbol=symbol, symbolBrush=brush, symbolSize=plot_parameters.marker_size, name=tag)

    def _render_rotor_conditions_pg(self, results, plot_parameters):
        # Plot rotor disc loading and power loading.
        U = self._units()
        seg0 = results.segments[0]
        if not self._has_attr_chain(seg0.conditions, ["energy", "converters"]):
            # This plot needs converter data; skip when not available.
            raise RuntimeError("no rotor converter data")
        dl = self._new_plot_widget("Rotor Conditions: Disc Loading", "Disc Loading", show_legend=True)
        pl = self._new_plot_widget("Rotor Conditions: Power Loading", "Power Loading", show_legend=False)
        for i, segment in enumerate(results.segments):
            converters = segment.conditions.energy.converters
            if hasattr(converters, "keys"):
                tag = next(iter(converters.keys()))
                conv = converters[tag]
            else:
                tags = [name for name in dir(converters) if not name.startswith("_")]
                tag = tags[0]
                conv = getattr(converters, tag)
            if not hasattr(conv, "disc_loading") or not hasattr(conv, "power_loading"):
                # Skip when converter metrics are incomplete.
                raise RuntimeError("no disc/power loading data")
            time = segment.conditions.frames.inertial.time[:, 0] / U.min
            pen, brush, symbol = self._segment_style(i, plot_parameters)
            name = segment.tag.replace("_", " ")
            dl.plot(time, np.asarray(conv.disc_loading[:, 0]).reshape(-1), pen=pen, symbol=symbol, symbolBrush=brush, symbolSize=plot_parameters.marker_size, name=name)
            pl.plot(time, np.asarray(conv.power_loading[:, 0]).reshape(-1), pen=pen, symbol=symbol, symbolBrush=brush, symbolSize=plot_parameters.marker_size, name=name)

    def _render_altitude_sfc_weight_pg(self, results, plot_parameters):
        # Plot weight, fuel burn, SFC, and fuel flow.
        U = self._units()
        seg0 = results.segments[0]
        if not self._has_attr_chain(seg0.conditions, ["weights", "total_mass"]):
            # Skip when weight history is missing.
            raise RuntimeError("no total_mass data")
        if not self._has_attr_chain(seg0.conditions, ["weights", "vehicle_mass_rate"]):
            # Skip when mass-rate (fuel flow) is missing.
            raise RuntimeError("no vehicle_mass_rate data")
        if not self._has_attr_chain(seg0.conditions, ["energy", "cumulative_fuel_consumption"]):
            # Skip when cumulative fuel-burn data is missing.
            raise RuntimeError("no cumulative_fuel_consumption data")
        self._render_time_series_group(results, plot_parameters, [
            ("Weight", "Weight (lbf)", lambda s: (s.conditions.weights.total_mass[:, 0] * 9.81) / U.lbf, True),
            ("Fuel Burn", "Fuel Burn (lb)", lambda s: s.conditions.energy.cumulative_fuel_consumption[:, 0] / U.lb, False),
            ("SFC", "SFC", lambda s: ((s.conditions.weights.vehicle_mass_rate[:, 0] / U.lb) / np.clip(np.abs(s.conditions.frames.body.thrust_force_vector[:, 0]) / U.lbf, 1e-9, None)), False),
            ("Fuel Flow", "mdot (lb/s)", lambda s: s.conditions.weights.vehicle_mass_rate[:, 0] / U.lb, False),
        ])

    def _render_propulsor_throttles_pg(self, results, plot_parameters):
        # Plot throttle traces for each propulsor.
        U = self._units()
        widget = self._new_plot_widget("Propulsor Throttles", "Throttle", show_legend=True)
        for i, segment in enumerate(results.segments):
            time = segment.conditions.frames.inertial.time[:, 0] / U.min
            pen, brush, symbol = self._segment_style(i, plot_parameters)
            for prop_tag, prop_data in segment.conditions.energy.propulsors.items():
                y = np.asarray(prop_data.throttle[:, 0]).reshape(-1)
                label = f"{segment.tag.replace('_', ' ')}: {prop_tag}"
                widget.plot(time, y, pen=pen, symbol=symbol, symbolBrush=brush, symbolSize=plot_parameters.marker_size, name=label)

    def _render_flight_conditions_pg(self, results, plot_parameters):
        # Plot altitude, airspeed, and range.
        U = self._units()
        self._render_time_series_group(results, plot_parameters, [
            ("Flight Conditions: Altitude", "Altitude (ft)", lambda s: s.conditions.freestream.altitude[:, 0] / U.feet, True),
            ("Flight Conditions: Airspeed", "Airspeed (mph)", lambda s: s.conditions.freestream.velocity[:, 0] / U["mph"], False),
            ("Flight Conditions: Range", "Range (nmi)", lambda s: s.conditions.frames.inertial.aircraft_range[:, 0] / U.nmi, False),
        ])

    def _render_flight_trajectory_pg(self, results, plot_parameters):
        # Plot trajectory as range-time, XY, and altitude-time.
        U = self._units()
        tr = self._new_plot_widget("Flight Trajectory: Range vs Time", "Range (nmi)", show_legend=True)
        xy = self._new_plot_widget("Flight Trajectory: Y vs X", "Y", "X", show_legend=False)
        alt = self._new_plot_widget("Flight Trajectory: Altitude", "Altitude (m)", show_legend=False)
        for segment, time, pen, brush, symbol, tag in self._iter_segments_with_style(results, plot_parameters):
            rng = segment.conditions.frames.inertial.aircraft_range[:, 0] / U.nmi
            x = segment.conditions.frames.inertial.position_vector[:, 0]
            y = segment.conditions.frames.inertial.position_vector[:, 1]
            z = -segment.conditions.frames.inertial.position_vector[:, 2]
            tr.plot(time, np.asarray(rng).reshape(-1), pen=pen, symbol=symbol, symbolBrush=brush, symbolSize=plot_parameters.marker_size, name=tag)
            xy.plot(np.asarray(x).reshape(-1), np.asarray(y).reshape(-1), pen=pen, symbol=symbol, symbolBrush=brush, symbolSize=plot_parameters.marker_size, name=tag)
            alt.plot(time, np.asarray(z).reshape(-1), pen=pen, symbol=symbol, symbolBrush=brush, symbolSize=plot_parameters.marker_size, name=tag)

    def _render_flight_forces_moments_pg(self, results, plot_parameters):
        # Plot wind-axis forces and moments.
        self._render_time_series_group(results, plot_parameters, [
            ("X Force", "X (N)", lambda s: s.conditions.frames.wind.total_force_vector[:, 0], True),
            ("Y Force", "Y (N)", lambda s: s.conditions.frames.wind.total_force_vector[:, 1], False),
            ("Z Force", "Z (N)", lambda s: s.conditions.frames.wind.total_force_vector[:, 2], False),
            ("Roll Moment", "L", lambda s: s.conditions.frames.wind.total_moment_vector[:, 0], False),
            ("Pitch Moment", "M", lambda s: s.conditions.frames.wind.total_moment_vector[:, 1], False),
            ("Yaw Moment", "N", lambda s: s.conditions.frames.wind.total_moment_vector[:, 2], False),
        ])

    def _render_longitudinal_stability_pg(self, results, plot_parameters):
        # Plot longitudinal stability metrics.
        U = self._units()
        self._render_time_series_group(results, plot_parameters, [
            ("Longitudinal: Cm", "Cm", lambda s: s.conditions.static_stability.coefficients.M[:, 0], True),
            ("Longitudinal: Static Margin", "SM", lambda s: s.conditions.static_stability.static_margin[:, 0], False),
            ("Longitudinal: Elevator", "delta_e (deg)", lambda s: s.conditions.control_surfaces.elevator.deflection[:, 0] / U.deg, False),
        ])

    def _render_lateral_stability_pg(self, results, plot_parameters):
        # Plot lateral-directional stability metrics.
        U = self._units()
        self._render_time_series_group(results, plot_parameters, [
            ("Lateral: Bank Angle", "phi (deg)", lambda s: -s.conditions.aerodynamics.angles.phi[:, 0] / U.deg, True),
            ("Lateral: Aileron", "delta_a (deg)", lambda s: s.conditions.control_surfaces.aileron.deflection[:, 0] / U.deg, False),
            ("Lateral: Rudder", "delta_r (deg)", lambda s: s.conditions.control_surfaces.rudder.deflection[:, 0] / U.deg, False),
        ])

    def _remove_empty_dynamic_plots(self, start_index=0):
        # Remove new dynamic plots that ended up with no curves.
        kept = []
        removed = []
        for idx, widget in enumerate(self._dynamic_plot_widgets):
            # Keep old plots and any plot that has data items.
            if idx < start_index or widget.listDataItems():
                kept.append(widget)
            else:
                removed.append(widget)
        self._dynamic_plot_widgets = kept
        self._delete_plot_widgets(removed)

    def _build_plot_parameters(self, results):
        from RCAIDE.Framework.Core import Data
        # Build shared style settings passed into plot functions.
        plot_parameters = Data()
        plot_parameters.line_width = 5
        plot_parameters.line_style = '-'
        # Keep mission lines white.
        plot_parameters.line_colors = np.tile(np.array([1.0, 1.0, 1.0, 1.0]), (len(results.segments), 1))
        plot_parameters.marker_size = 8
        plot_parameters.legend_font_size = 12
        plot_parameters.axis_font_size = 14
        plot_parameters.title_font_size = 18
        plot_parameters.styles = {"color": "white", "font-size": "18px"}
        plot_parameters.markers = ['o']
        plot_parameters.color = 'white'
        plot_parameters.show_grid = True
        plot_parameters.save_figure = False
        return plot_parameters
    
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

def _summarize_solve_output(output):
    # Return empty list if solver produced no output
    if not output:
        return []

    # Store extracted warning messages
    warnings = []

    # Split solver output into individual lines
    lines = output.splitlines()
    idx = 0

    # Iterate through all output lines
    while idx < len(lines):
        line = lines[idx].strip()

        # Capture non-converged segment warnings
        if "Segment did not converge" in line:
            warnings.append(line)
            idx += 1
            continue

        # Capture multi-line error messages
        if line.startswith("Error Message:"):
            idx += 1
            msg_lines = []

            # Collect error message details until solver moves on
            while idx < len(lines):
                nxt = lines[idx].strip()
                if not nxt or nxt.startswith("Solving"):
                    break
                msg_lines.append(nxt)
                idx += 1

            # Store the full error message as one warning
            if msg_lines:
                warnings.append("Error: " + " ".join(msg_lines))
            continue

        # Move to the next line
        idx += 1

    # Return all detected solver warnings
    return warnings


def _warnings_already_reported(output):
    # Return False if there is no solver output
    if not output:
        return False

    # Check if warnings already appeared in solver output
    return (
        "Segment did not converge" in output
        or "Error Message:" in output
        or "Error:" in output
    )
    
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
    self.marker_check.setChecked(True)
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
    self.save_plot_button = QPushButton("Save Plots")
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

    # Collect all plot widgets (base + dynamic + fallback attribute scan)
    plots = []
    if hasattr(self, "_base_plot_widgets"):
        plots.extend([p for p in self._base_plot_widgets if isinstance(p, pg.PlotWidget)])
    if hasattr(self, "_dynamic_plot_widgets"):
        plots.extend([p for p in self._dynamic_plot_widgets if isinstance(p, pg.PlotWidget)])
    plots.extend([
        getattr(self, name) for name in dir(self)
        if isinstance(getattr(self, name), pg.PlotWidget)
    ])

    # De-duplicate while preserving order.
    seen = set()
    unique_plots = []
    for plot in plots:
        pid = id(plot)
        if pid in seen:
            continue
        seen.add(pid)
        unique_plots.append(plot)

    for plot in unique_plots:

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
            if hasattr(self, "_position_plot_legend"):
                self._position_plot_legend(plot)
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

            # Sanitize marker symbol first so setPen can't fail on stale invalid symbols.
            if self.marker_check.isChecked():
                symbol_map = {
                    '^': 't1',
                    'v': 't',
                    '<': 't3',
                    '>': 't2',
                    # pyqtgraph uses "star" (not "*") for star markers.
                    '*': 'star',
                }
                valid_symbols = {'o', 's', 't', 't1', 't2', 't3', 'd', '+', 'x', 'p', 'h', 'star', '|', '_'}
                selected = self.marker_style_combo.currentText()
                marker_symbol = symbol_map.get(selected, selected)
                if marker_symbol not in valid_symbols:
                    marker_symbol = 'o'
                curve.setSymbol(marker_symbol)
                curve.setSymbolSize(self.marker_size_spin.value())
                curve.setSymbolBrush(new_pen.color())
                curve.setSymbolPen(new_pen)
            else:
                curve.setSymbol(None)

            # Apply the new pen to the curve
            curve.setPen(new_pen)

# --------------------------------------------------------------------------------------------------
#  Save Visible Plot
# --------------------------------------------------------------------------------------------------
def save_current_plot(self):
    from PyQt6.QtWidgets import QFileDialog, QApplication

    def _plot_has_real_data(plot_widget):
        # Export only plots that actually contain finite data points.
        for curve in plot_widget.listDataItems():
            try:
                x_data, y_data = curve.getData()
            except Exception:
                continue
            if x_data is None or y_data is None:
                continue
            x = np.asarray(x_data).reshape(-1)
            y = np.asarray(y_data).reshape(-1)
            if x.size == 0 or y.size == 0:
                continue
            if np.isfinite(x).any() and np.isfinite(y).any():
                return True
        return False

    # Collect visible plots in display order.
    plots = []
    if hasattr(self, "_base_plot_widgets"):
        plots.extend([p for p in self._base_plot_widgets if isinstance(p, pg.PlotWidget)])
    if hasattr(self, "_dynamic_plot_widgets"):
        plots.extend([p for p in self._dynamic_plot_widgets if isinstance(p, pg.PlotWidget)])
    plots = [p for p in plots if p.isVisible() and _plot_has_real_data(p)]

    if not plots:
        QMessageBox.information(self, "Save Plots", "No visible plots with data to save.")
        return

    # Choose parent directory where a new plots folder will be created.
    parent_dir = QFileDialog.getExistingDirectory(
        self,
        "Choose Folder to Save Mission Plots",
        os.getcwd(),
    )
    if not parent_dir:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    export_dir = os.path.join(parent_dir, f"Mission Plots {timestamp}")
    os.makedirs(export_dir, exist_ok=True)

    def _sanitize_name(text):
        text = re.sub(r"<[^>]*>", "", str(text)).strip()
        text = re.sub(r"[^A-Za-z0-9._ -]", "_", text)
        text = re.sub(r"\s+", "_", text).strip("_")
        return text or "plot"

    for idx, plot in enumerate(plots, start=1):
        plot_item = plot.getPlotItem()
        if plot_item is None:
            continue

        left_axis = plot_item.getAxis("left")
        bottom_axis = plot_item.getAxis("bottom")

        # Preserve current styling so we can restore after exporting.
        old_bg = plot.backgroundBrush()
        old_bottom_pen = bottom_axis.pen()
        old_left_pen = left_axis.pen()
        old_bottom_text_pen = bottom_axis.textPen()
        old_left_text_pen = left_axis.textPen()
        old_border = plot_item.getViewBox().border
        old_left_show_values = left_axis.style.get("showValues", True)
        old_bottom_show_values = bottom_axis.style.get("showValues", True)
        old_left_width = left_axis.width()

        # Ensure axes/labels remain visible on white export background.
        plot.setBackground("white")
        bottom_axis.setPen(pg.mkPen("black"))
        left_axis.setPen(pg.mkPen("black"))
        bottom_axis.setTextPen(pg.mkPen("black"))
        left_axis.setTextPen(pg.mkPen("black"))
        # Force tick value labels to render and reserve width on the left axis.
        left_axis.setStyle(showValues=True, autoExpandTextSpace=True)
        bottom_axis.setStyle(showValues=True, autoExpandTextSpace=True)
        left_axis.setWidth(max(int(old_left_width or 0), 75))
        plot_item.getViewBox().setBorder(pg.mkPen("black"))

        # Ensure very light curves are visible on white export background.
        curve_state = []
        for curve in plot.listDataItems():
            old_pen = curve.opts.get("pen")
            old_symbol_pen = curve.opts.get("symbolPen")
            old_symbol_brush = curve.opts.get("symbolBrush")
            curve_state.append((curve, old_pen, old_symbol_pen, old_symbol_brush))

            pen_color = old_pen.color() if old_pen is not None else None
            if pen_color is not None and pen_color.lightness() > 220:
                export_pen = pg.mkPen("black", width=old_pen.widthF() if hasattr(old_pen, "widthF") else 2)
                curve.setPen(export_pen)
                if curve.opts.get("symbol") is not None:
                    curve.setSymbolPen(export_pen)
                    curve.setSymbolBrush(pg.mkBrush("black"))

        plot.repaint()
        QApplication.processEvents()

        title = plot_item.titleLabel.text if plot_item.titleLabel else ""
        base_name = _sanitize_name(title) if title else f"plot_{idx:02d}"
        file_path = os.path.join(export_dir, f"{idx:02d}_{base_name}.png")

        # Capture exactly what the user sees in the plot widget.
        plot.grab().save(file_path, "PNG")

        # Restore UI styling.
        plot.setBackground(old_bg)
        bottom_axis.setPen(old_bottom_pen)
        left_axis.setPen(old_left_pen)
        bottom_axis.setTextPen(old_bottom_text_pen)
        left_axis.setTextPen(old_left_text_pen)
        left_axis.setStyle(showValues=old_left_show_values, autoExpandTextSpace=True)
        bottom_axis.setStyle(showValues=old_bottom_show_values, autoExpandTextSpace=True)
        if old_left_width:
            left_axis.setWidth(old_left_width)
        plot_item.getViewBox().setBorder(old_border if old_border is not None else pg.mkPen(None))
        for curve, old_pen, old_symbol_pen, old_symbol_brush in curve_state:
            if old_pen is not None:
                curve.setPen(old_pen)
            curve.setSymbolPen(old_symbol_pen)
            curve.setSymbolBrush(old_symbol_brush)

    QMessageBox.information(self, "Save Plots", f"Saved {len(plots)} plots to:\n{export_dir}")

# --------------------------------------------------------------------------------------------------
#  Plot Visibility Toggle (Tree)
# --------------------------------------------------------------------------------------------------
def toggle_plot_visibility(self, item, column):

    # Ignore category items; only act on leaf (actual plot) items
    if item.childCount() > 0:
        return

    # Re-render selected plots based on current tree state (debounced).
    import values
    results = getattr(values, "rcaide_results", None)
    if results is not None and hasattr(self, "_schedule_plot_render"):
        self._schedule_plot_render()

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

