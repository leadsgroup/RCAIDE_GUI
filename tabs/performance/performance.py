# RCAIDE_GUI/tabs/multi_disciplinary/multi_disciplinary.py
#
# Created: Jun 2026, Laboratory for Emerging Aircraft Design and Systems

# ──────────────────────────────────────────────────────────────────────────────
#  Imports
# ──────────────────────────────────────────────────────────────────────────────
import rcaide_io
from tabs import TabWidget
from .analysis_registry import ANALYSIS_REGISTRY
from .results_tracker import ResultsTrackerWidget

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox, QLineEdit,
    QScrollArea, QSplitter, QFrame, QProgressDialog, QMessageBox,
    QColorDialog, QFileDialog, QApplication,
)
from PyQt6.QtCore import Qt, QSize, QObject, QThread, pyqtSignal
import pyqtgraph as pg

import numpy as np
import re
import os
import traceback
from datetime import datetime


# ──────────────────────────────────────────────────────────────────────────────
#  Background worker
# ──────────────────────────────────────────────────────────────────────────────
class _AnalysisWorker(QObject):
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, runner, params, config_tag):
        super().__init__()
        self._runner = runner
        self._params = params
        self._config_tag = config_tag

    def run(self):
        try:
            result = self._runner(self._params, self._config_tag)
            self.finished.emit(result)
        except Exception:
            self.failed.emit(traceback.format_exc())


# ──────────────────────────────────────────────────────────────────────────────
#  Main widget
# ──────────────────────────────────────────────────────────────────────────────
class MultiDisciplinaryWidget(TabWidget):

    def __init__(self):
        super().__init__()

        self._analysis_thread = None
        self._analysis_worker = None
        self._dynamic_plot_widgets = []
        self._param_widgets = {}
        self._current_result = None

        base_layout = QHBoxLayout(self)
        base_layout.setContentsMargins(14, 14, 14, 14)
        base_layout.setSpacing(14)

        # ── Left panel: analysis setup (scrollable) ─────────────────────
        left_scroll = QScrollArea()
        left_scroll.setFixedWidth(280)
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # Run button (at the top)
        self.run_button = QPushButton("Run Analysis")
        self.run_button.setFixedHeight(36)
        self.run_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_button.setStyleSheet("""
        QPushButton {
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #1b4f8a, stop:1 #133a66
            );
            border: 1.6px solid #5fb0ff;
            border-radius: 10px;
            padding: 7px 20px;
            color: #d9ecff;
            font-size: 13.5px;
            font-weight: 700;
            letter-spacing: 0.35px;
        }
        QPushButton:hover {
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #2a6fb5, stop:1 #1b4f8a
            );
            border-color: #8ccaff;
            color: #ffffff;
        }
        QPushButton:pressed {
            background-color: #0f2e4d;
            border-color: #4da3ff;
        }
        """)
        self.run_button.clicked.connect(self._run_analysis)
        left_layout.addWidget(self.run_button)

        left_layout.addWidget(self._divider())

        # Aircraft name
        self.aircraft_label = QLabel("Aircraft: —")
        self.aircraft_label.setStyleSheet("color: #d6e1ff; font-size: 14px; padding: 2px 0;")
        left_layout.addWidget(self.aircraft_label)

        # Configuration dropdown
        left_layout.addWidget(QLabel("Configuration:"))
        self.config_combo = QComboBox()
        self.config_combo.setMinimumHeight(28)
        left_layout.addWidget(self.config_combo)

        # Analysis dropdown
        left_layout.addWidget(QLabel("Analysis:"))
        self.analysis_combo = QComboBox()
        self.analysis_combo.setMinimumHeight(28)
        for name in ANALYSIS_REGISTRY:
            self.analysis_combo.addItem(name)
        self.analysis_combo.currentIndexChanged.connect(self._on_analysis_type_changed)
        left_layout.addWidget(self.analysis_combo)

        # Dynamic parameters label
        params_label = QLabel("Parameters:")
        params_label.setStyleSheet("color: #9fb8ff; font-weight: bold; margin-top: 4px;")
        left_layout.addWidget(params_label)

        # Dynamic parameters container
        self.param_container = QWidget()
        self.param_layout = QVBoxLayout(self.param_container)
        self.param_layout.setContentsMargins(0, 0, 0, 0)
        self.param_layout.setSpacing(6)
        left_layout.addWidget(self.param_container)

        left_layout.addStretch()
        left_scroll.setWidget(left_widget)
        base_layout.addWidget(left_scroll)

        # ── Center area (splitter: plots on top, results on bottom) ───────
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Plot scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        plot_container = QWidget()
        self.plot_layout = QVBoxLayout(plot_container)
        self.plot_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        scroll_area.setWidget(plot_container)
        splitter.addWidget(scroll_area)

        # Results tracker
        self.results_tracker = ResultsTrackerWidget()
        self.results_tracker.setMinimumHeight(150)
        splitter.addWidget(self.results_tracker)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        base_layout.addWidget(splitter, 5)

        # ── Right panel: plot settings (scrollable, full height) ─────────
        right_scroll = QScrollArea()
        right_scroll.setFixedWidth(360)
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_scroll.setFrameShape(QFrame.Shape.NoFrame)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        plot_params_header = QLabel("Plot Parameters")
        plot_params_header.setStyleSheet(
            "color: #9fb8ff; font-size: 18px; font-weight: bold; "
            "padding-bottom: 4px; border-bottom: 1px solid rgba(255,255,255,0.08);"
        )
        right_layout.addWidget(plot_params_header)

        self._build_plot_settings(right_layout)
        right_layout.addStretch()
        right_scroll.setWidget(right_widget)
        base_layout.addWidget(right_scroll)

        # ── Apply theme ──────────────────────────────────────────────────
        self._apply_theme()

        # Build initial parameter fields
        self._on_analysis_type_changed(0)

    # ──────────────────────────────────────────────────────────────────────
    #  TabWidget callbacks
    # ──────────────────────────────────────────────────────────────────────
    def update_layout(self):
        self._refresh_config_dropdown()
        vehicle = getattr(rcaide_io, "vehicle", None)
        tag = getattr(vehicle, "tag", "") if vehicle else ""
        self.aircraft_label.setText(f"Aircraft: {tag}" if tag else "Aircraft: —")
        self._autofill_vehicle_params()

    def load_from_values(self):
        self.update_layout()

    # ──────────────────────────────────────────────────────────────────────
    #  Config dropdown
    # ──────────────────────────────────────────────────────────────────────
    def _refresh_config_dropdown(self):
        self.config_combo.blockSignals(True)
        prev = self.config_combo.currentText()
        self.config_combo.clear()
        configs = getattr(rcaide_io, "rcaide_configs", None)
        if configs:
            for tag, _ in configs.items():
                self.config_combo.addItem(tag)
        idx = self.config_combo.findText(prev)
        if idx >= 0:
            self.config_combo.setCurrentIndex(idx)
        self.config_combo.blockSignals(False)

    # ──────────────────────────────────────────────────────────────────────
    #  Dynamic parameters
    # ──────────────────────────────────────────────────────────────────────
    def _on_analysis_type_changed(self, _index):
        analysis_name = self.analysis_combo.currentText()
        spec = ANALYSIS_REGISTRY.get(analysis_name)
        if spec is None:
            return

        self._clear_layout(self.param_layout)
        self._param_widgets = {}

        for label, widget_type, default in spec["parameters"]:
            row = QHBoxLayout()
            row.setSpacing(8)
            lbl = QLabel(f"{label}:")
            lbl.setFixedWidth(140)
            row.addWidget(lbl)

            if widget_type == "float":
                field = QDoubleSpinBox()
                field.setRange(-1e9, 1e9)
                field.setDecimals(4)
                field.setSingleStep(1.0)
                field.setValue(default)
            elif widget_type == "int":
                field = QSpinBox()
                field.setRange(1, 10000)
                field.setValue(default)
            elif widget_type == "bool":
                field = QCheckBox()
                field.setChecked(default)
            elif widget_type == "text":
                field = QLineEdit(str(default))
            else:
                continue

            row.addWidget(field)
            self.param_layout.addLayout(row)
            self._param_widgets[label] = field

        self._autofill_vehicle_params()

    def _autofill_vehicle_params(self):
        vehicle = getattr(rcaide_io, "vehicle", None)
        if vehicle is None:
            return
        if "Vehicle Mass (kg)" in self._param_widgets:
            mass = getattr(getattr(vehicle, "mass_properties", None), "takeoff", 0.0)
            if mass:
                self._param_widgets["Vehicle Mass (kg)"].setValue(mass)
        if "Reference Area (m²)" in self._param_widgets:
            area = getattr(vehicle, "reference_area", 0.0)
            if area:
                self._param_widgets["Reference Area (m²)"].setValue(area)

    def _collect_params(self):
        params = {}
        for label, widget in self._param_widgets.items():
            if isinstance(widget, QDoubleSpinBox):
                params[label] = widget.value()
            elif isinstance(widget, QSpinBox):
                params[label] = widget.value()
            elif isinstance(widget, QCheckBox):
                params[label] = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                params[label] = widget.text()
        return params

    # ──────────────────────────────────────────────────────────────────────
    #  Validation
    # ──────────────────────────────────────────────────────────────────────
    def _validate_prerequisites(self, spec):
        if spec.get("requires_analyses"):
            config_tag = self.config_combo.currentText()
            if not config_tag:
                return "No configuration selected. Set up configurations in the Configurations Setup tab."
            analyses = getattr(rcaide_io, "rcaide_analyses", None)
            if not analyses or config_tag not in analyses:
                return (f"Analyses not found for configuration '{config_tag}'. "
                        "Save analyses in the Analyses Setup tab first.")

        if spec.get("requires_mission"):
            mission = getattr(rcaide_io, "rcaide_mission", None)
            if mission is None or not getattr(mission, "segments", None):
                return "No mission defined. Build and save a mission in the Mission Setup tab first."
        return None

    # ──────────────────────────────────────────────────────────────────────
    #  Run analysis
    # ──────────────────────────────────────────────────────────────────────
    def _run_analysis(self):
        analysis_name = self.analysis_combo.currentText()
        spec = ANALYSIS_REGISTRY.get(analysis_name)
        if spec is None:
            return

        error = self._validate_prerequisites(spec)
        if error:
            QMessageBox.critical(self, "Cannot Run Analysis", error)
            return

        if self._analysis_thread is not None and self._analysis_thread.isRunning():
            QMessageBox.warning(self, "Busy", "An analysis is already running.")
            return

        config_tag = self.config_combo.currentText()
        params = self._collect_params()

        self.run_button.setEnabled(False)
        self.loading_dialog = QProgressDialog("Running analysis…", None, 0, 0, self)
        self.loading_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.loading_dialog.setMinimumDuration(0)
        self.loading_dialog.setCancelButton(None)
        self.loading_dialog.show()

        self._analysis_worker = _AnalysisWorker(spec["runner"], params, config_tag)
        self._analysis_thread = QThread()
        self._analysis_worker.moveToThread(self._analysis_thread)

        self._analysis_thread.started.connect(self._analysis_worker.run)
        self._analysis_worker.finished.connect(
            lambda result: self._on_analysis_finished(result, spec))
        self._analysis_worker.failed.connect(self._on_analysis_failed)
        self._analysis_worker.finished.connect(self._analysis_thread.quit)
        self._analysis_worker.failed.connect(self._analysis_thread.quit)
        self._analysis_thread.finished.connect(self._cleanup_worker)

        self._analysis_thread.start()

    def _on_analysis_finished(self, result, spec):
        self._current_result = result
        self._set_loading_state(False)

        # Clear old plots
        self._clear_dynamic_plots()

        # Render new plots
        plotter = spec.get("plotter")
        if plotter is not None:
            try:
                plotter(result, self._new_plot_widget)
            except Exception:
                traceback.print_exc()

        # Format and display results
        formatter = spec.get("formatter")
        if formatter is not None:
            try:
                formatted = formatter(result)
                self.results_tracker.update_results(formatted)
            except Exception:
                traceback.print_exc()
                self.results_tracker.update_results(
                    [("Error", "Could not format results", "")])

        self.apply_plot_settings()

    def _on_analysis_failed(self, error_msg):
        self._set_loading_state(False)
        QMessageBox.critical(self, "Analysis Failed", f"Error:\n{error_msg}")

    def _set_loading_state(self, loading):
        self.run_button.setEnabled(not loading)
        if self.loading_dialog is not None:
            self.loading_dialog.close()
            self.loading_dialog = None

    def _cleanup_worker(self):
        if self._analysis_worker is not None:
            self._analysis_worker.deleteLater()
            self._analysis_worker = None
        if self._analysis_thread is not None:
            self._analysis_thread.deleteLater()
            self._analysis_thread = None

    # ──────────────────────────────────────────────────────────────────────
    #  Plot widget creation
    # ──────────────────────────────────────────────────────────────────────
    def _new_plot_widget(self, title, y_label, x_label="", show_legend=True):
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

        if show_legend and self.legend_check.isChecked():
            legend = widget.addLegend(offset=(10, 10))
            if legend:
                legend.setBrush(pg.mkBrush(8, 12, 18, 180))
                legend.setPen(pg.mkPen(120, 150, 210, 140))

        self.plot_layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._dynamic_plot_widgets.append(widget)
        return widget

    def _clear_dynamic_plots(self):
        for w in self._dynamic_plot_widgets:
            self.plot_layout.removeWidget(w)
            w.setParent(None)
            w.deleteLater()
        self._dynamic_plot_widgets.clear()

    # ──────────────────────────────────────────────────────────────────────
    #  Plot settings panel
    # ──────────────────────────────────────────────────────────────────────
    def _build_plot_settings(self, parent_layout):
        def _header(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-weight: bold; color: white; margin-top: 6px;")
            return lbl

        parent_layout.addWidget(_header("Line Appearance"))

        parent_layout.addWidget(QLabel("Line Width"))
        self.line_width_spin = QDoubleSpinBox()
        self.line_width_spin.setRange(0.5, 10.0)
        self.line_width_spin.setValue(2.0)
        parent_layout.addWidget(self.line_width_spin)

        parent_layout.addWidget(QLabel("Line Style"))
        self.line_style_combo = QComboBox()
        self.line_style_combo.addItems(["Solid", "Dashed", "Dotted"])
        parent_layout.addWidget(self.line_style_combo)

        self.line_color_button = QPushButton("Select Line Color")
        parent_layout.addWidget(self.line_color_button)

        parent_layout.addWidget(_header("Markers"))

        self.marker_check = QCheckBox("Show Markers")
        self.marker_check.setChecked(False)
        parent_layout.addWidget(self.marker_check)

        parent_layout.addWidget(QLabel("Marker Style"))
        self.marker_style_combo = QComboBox()
        self.marker_style_combo.addItems(["o", "s", "^", "d", "x", "+", "*"])
        parent_layout.addWidget(self.marker_style_combo)

        parent_layout.addWidget(QLabel("Marker Size"))
        self.marker_size_spin = QDoubleSpinBox()
        self.marker_size_spin.setRange(3, 20)
        self.marker_size_spin.setValue(8)
        parent_layout.addWidget(self.marker_size_spin)

        parent_layout.addWidget(_header("Axes"))

        self.autoscale_check = QCheckBox("Autoscale Axes")
        self.autoscale_check.setChecked(True)
        parent_layout.addWidget(self.autoscale_check)

        parent_layout.addWidget(QLabel("Axis Font Size"))
        self.axis_font_spin = QDoubleSpinBox()
        self.axis_font_spin.setRange(8, 24)
        self.axis_font_spin.setValue(14)
        parent_layout.addWidget(self.axis_font_spin)

        parent_layout.addWidget(_header("Grid / Legend"))

        self.grid_check = QCheckBox("Show Grid")
        self.grid_check.setChecked(True)
        parent_layout.addWidget(self.grid_check)

        self.grid_color_button = QPushButton("Select Grid Color")
        parent_layout.addWidget(self.grid_color_button)

        self.legend_check = QCheckBox("Show Legend")
        self.legend_check.setChecked(True)
        parent_layout.addWidget(self.legend_check)

        parent_layout.addWidget(_header("Export"))

        self.save_plot_button = QPushButton("Save Plots")
        self.save_plot_button.clicked.connect(self.save_current_plot)
        parent_layout.addWidget(self.save_plot_button)

        self.selected_line_color = None
        self.selected_grid_color = (150, 150, 150)

        self.line_width_spin.valueChanged.connect(self.apply_plot_settings)
        self.marker_size_spin.valueChanged.connect(self.apply_plot_settings)
        self.axis_font_spin.valueChanged.connect(self.apply_plot_settings)
        self.line_style_combo.currentIndexChanged.connect(self.apply_plot_settings)
        self.marker_style_combo.currentIndexChanged.connect(self.apply_plot_settings)
        self.marker_check.stateChanged.connect(self.apply_plot_settings)
        self.autoscale_check.stateChanged.connect(self.apply_plot_settings)
        self.grid_check.stateChanged.connect(self.apply_plot_settings)
        self.legend_check.stateChanged.connect(self.apply_plot_settings)
        self.line_color_button.clicked.connect(self._select_line_color)
        self.grid_color_button.clicked.connect(self._select_grid_color)

    def _select_line_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_line_color = color.name()
            self.apply_plot_settings()

    def _select_grid_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_grid_color = color.getRgb()[:3]
            self.apply_plot_settings()

    def apply_plot_settings(self):
        plots = [p for p in self._dynamic_plot_widgets if isinstance(p, pg.PlotWidget)]

        for plot in plots:
            plot.showGrid(
                x=self.grid_check.isChecked(),
                y=self.grid_check.isChecked(),
                alpha=0.3,
            )
            plot.getAxis("bottom").setPen(self.selected_grid_color)
            plot.getAxis("left").setPen(self.selected_grid_color)

            if self.autoscale_check.isChecked():
                vb = plot.getPlotItem().getViewBox()
                vb.enableAutoRange(x=True, y=True)
                vb.autoRange()

            font = pg.QtGui.QFont()
            font.setPointSizeF(self.axis_font_spin.value())
            plot.getAxis("bottom").setTickFont(font)
            plot.getAxis("left").setTickFont(font)

            if self.legend_check.isChecked():
                if not plot.plotItem.legend:
                    plot.addLegend()
                plot.plotItem.legend.show()
            else:
                if plot.plotItem.legend:
                    plot.plotItem.legend.hide()

            for curve in plot.listDataItems():
                old_pen = curve.opts["pen"]
                style_text = self.line_style_combo.currentText()
                if style_text == "Dashed":
                    pen_style = Qt.PenStyle.DashLine
                elif style_text == "Dotted":
                    pen_style = Qt.PenStyle.DotLine
                else:
                    pen_style = Qt.PenStyle.SolidLine

                color = self.selected_line_color or old_pen.color()
                new_pen = pg.mkPen(
                    color=color,
                    width=self.line_width_spin.value(),
                    style=pen_style,
                )

                if self.marker_check.isChecked():
                    symbol_map = {
                        "^": "t1", "v": "t", "<": "t3", ">": "t2", "*": "star",
                    }
                    valid_symbols = {"o", "s", "t", "t1", "t2", "t3", "d", "+",
                                     "x", "p", "h", "star", "|", "_"}
                    selected = self.marker_style_combo.currentText()
                    marker = symbol_map.get(selected, selected)
                    if marker not in valid_symbols:
                        marker = "o"
                    curve.setSymbol(marker)
                    curve.setSymbolSize(self.marker_size_spin.value())
                    curve.setSymbolBrush(new_pen.color())
                    curve.setSymbolPen(new_pen)
                else:
                    curve.setSymbol(None)

                curve.setPen(new_pen)

    # ──────────────────────────────────────────────────────────────────────
    #  Save plots
    # ──────────────────────────────────────────────────────────────────────
    def save_current_plot(self):
        def _has_data(pw):
            for c in pw.listDataItems():
                try:
                    x, y = c.getData()
                except Exception:
                    continue
                if x is not None and y is not None:
                    x, y = np.asarray(x).flatten(), np.asarray(y).flatten()
                    if x.size and y.size and np.isfinite(x).any() and np.isfinite(y).any():
                        return True
            return False

        plots = [p for p in self._dynamic_plot_widgets
                 if isinstance(p, pg.PlotWidget) and p.isVisible() and _has_data(p)]
        if not plots:
            QMessageBox.information(self, "Save Plots", "No visible plots with data to save.")
            return

        parent_dir = QFileDialog.getExistingDirectory(self, "Choose Folder", os.getcwd())
        if not parent_dir:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        export_dir = os.path.join(parent_dir, f"Analysis Plots {timestamp}")
        os.makedirs(export_dir, exist_ok=True)

        def _sanitize(text):
            text = re.sub(r"<[^>]*>", "", str(text)).strip()
            text = re.sub(r"[^A-Za-z0-9._ -]", "_", text)
            return re.sub(r"\s+", "_", text).strip("_") or "plot"

        for idx, plot in enumerate(plots, start=1):
            pi = plot.getPlotItem()
            if pi is None:
                continue

            la, ba = pi.getAxis("left"), pi.getAxis("bottom")
            old = (plot.backgroundBrush(), ba.pen(), la.pen(),
                   ba.textPen(), la.textPen(),
                   pi.getViewBox().border, la.width())

            plot.setBackground("white")
            ba.setPen(pg.mkPen("black"))
            la.setPen(pg.mkPen("black"))
            ba.setTextPen(pg.mkPen("black"))
            la.setTextPen(pg.mkPen("black"))
            la.setStyle(showValues=True, autoExpandTextSpace=True)
            ba.setStyle(showValues=True, autoExpandTextSpace=True)
            la.setWidth(max(int(old[6] or 0), 75))
            pi.getViewBox().setBorder(pg.mkPen("black"))

            plot.repaint()
            QApplication.processEvents()

            title = pi.titleLabel.text if pi.titleLabel else ""
            name = _sanitize(title) if title else f"plot_{idx:02d}"
            plot.grab().save(os.path.join(export_dir, f"{idx:02d}_{name}.png"), "PNG")

            plot.setBackground(old[0])
            ba.setPen(old[1])
            la.setPen(old[2])
            ba.setTextPen(old[3])
            la.setTextPen(old[4])
            pi.getViewBox().setBorder(old[5] if old[5] is not None else pg.mkPen(None))
            if old[6]:
                la.setWidth(old[6])

        QMessageBox.information(self, "Save Plots",
                                f"Saved {len(plots)} plots to:\n{export_dir}")

    # ──────────────────────────────────────────────────────────────────────
    #  Theme
    # ──────────────────────────────────────────────────────────────────────
    def _apply_theme(self):
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
            QComboBox, QDoubleSpinBox, QSpinBox, QLineEdit {
                background-color: #141c26;
                border: 1px solid #223044;
                border-radius: 4px;
                padding: 4px;
                color: #d6e1ff;
            }
            QScrollArea {
                border: none;
            }
            QCheckBox {
                spacing: 8px;
            }
            QSplitter::handle {
                background-color: #223044;
                height: 4px;
            }
        """)

    # ──────────────────────────────────────────────────────────────────────
    #  Helpers
    # ──────────────────────────────────────────────────────────────────────
    @staticmethod
    def _divider():
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #223044;")
        return line

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            elif item.layout() is not None:
                MultiDisciplinaryWidget._clear_layout(item.layout())


def get_widget() -> QWidget:
    return MultiDisciplinaryWidget()
