"""Interactive, plain-language activity tabs for Learner Mode."""

from __future__ import annotations

from copy import deepcopy
from math import sqrt, tan

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import rcaide_io
import RCAIDE
from tabs import TabWidget
from tabs.learner.learner import (
    DEFAULT_LEARNER_DATA,
    _merged_learner_data,
    apply_learner_setup,
    build_learner_vehicle,
)
from tabs.learner.model_view import AircraftModelViewport, style_learner_page
from tabs.visualize_geometry.geometry_helper_functions import learner_component_callout_data
from tabs.learner.learning_tools import (
    ASSUMED_PERSON_MASS_KG,
    classroom_loading,
    classroom_metrics,
    describe_design,
    evaluate_challenges,
)


def _active_data():
    """Return a complete copy of the learner design currently in use."""
    return _merged_learner_data(getattr(rcaide_io, "learner_data", DEFAULT_LEARNER_DATA))


def _title(layout, heading, subtitle):
    """Add the shared learner-page eyebrow, heading, and introductory text."""
    eyebrow = QLabel("RCAIDE  •  SIMPLIFIED WORKFLOW")
    eyebrow.setObjectName("eyebrow")
    label = QLabel(heading)
    label.setObjectName("pageTitle")
    detail = QLabel(subtitle)
    detail.setWordWrap(True)
    detail.setObjectName("subtitle")
    layout.addWidget(eyebrow)
    layout.addWidget(label)
    layout.addWidget(detail)


def _open_tab(widget, tab_name):
    """Move to a sibling workflow tab without coupling to the main window."""
    parent = widget.parentWidget()
    while parent is not None and not isinstance(parent, QTabWidget):
        parent = parent.parentWidget()
    if parent is None:
        return
    for index in range(parent.count()):
        if parent.tabText(index) == tab_name:
            parent.setCurrentIndex(index)
            return


def _info_card(title, value="", explanation=""):
    """Create a reusable result card whose value and explanation can be updated."""
    box = QGroupBox(title)
    layout = QVBoxLayout(box)
    value_label = QLabel(value)
    value_label.setObjectName("value")
    value_label.setWordWrap(True)
    value_label.setObjectName("metricValue")
    detail = QLabel(explanation)
    detail.setWordWrap(True)
    detail.setObjectName("muted")
    layout.addWidget(value_label)
    layout.addWidget(detail)
    box.value_label = value_label
    box.detail_label = detail
    return box


def _draw_plane(painter, center, scale=1.0, color="#e5edf6"):
    """Draw a friendly top-view airplane without external image assets."""
    x, y = center.x(), center.y()
    painter.setPen(QPen(QColor("#22364b"), 2))
    painter.setBrush(QColor(color))
    body = QPolygonF([
        QPointF(x - 44 * scale, y), QPointF(x - 22 * scale, y - 8 * scale),
        QPointF(x + 37 * scale, y - 5 * scale), QPointF(x + 52 * scale, y),
        QPointF(x + 37 * scale, y + 5 * scale), QPointF(x - 22 * scale, y + 8 * scale),
    ])
    wing = QPolygonF([
        QPointF(x - 5 * scale, y), QPointF(x + 14 * scale, y - 43 * scale),
        QPointF(x + 27 * scale, y - 42 * scale), QPointF(x + 18 * scale, y),
        QPointF(x + 27 * scale, y + 42 * scale), QPointF(x + 14 * scale, y + 43 * scale),
    ])
    tail = QPolygonF([
        QPointF(x - 31 * scale, y), QPointF(x - 39 * scale, y - 19 * scale),
        QPointF(x - 29 * scale, y - 18 * scale), QPointF(x - 21 * scale, y),
        QPointF(x - 29 * scale, y + 18 * scale), QPointF(x - 39 * scale, y + 19 * scale),
    ])
    painter.drawPolygon(wing)
    painter.drawPolygon(tail)
    painter.drawPolygon(body)


def _draw_side_plane(painter, center, scale=1.0):
    """Draw a simple side-view airplane for the animated flight path."""
    x, y = center.x(), center.y()
    painter.setPen(QPen(QColor("#22364b"), 2))
    painter.setBrush(QColor("#ffffff"))
    painter.drawEllipse(QRectF(x - 43 * scale, y - 8 * scale, 86 * scale, 16 * scale))
    wing = QPolygonF([
        QPointF(x - 5 * scale, y), QPointF(x + 20 * scale, y + 22 * scale),
        QPointF(x + 31 * scale, y + 21 * scale), QPointF(x + 14 * scale, y),
    ])
    tail = QPolygonF([
        QPointF(x - 31 * scale, y - 4 * scale), QPointF(x - 39 * scale, y - 24 * scale),
        QPointF(x - 27 * scale, y - 22 * scale), QPointF(x - 18 * scale, y - 3 * scale),
    ])
    painter.drawPolygon(wing)
    painter.drawPolygon(tail)
    painter.setBrush(QColor("#78cfff"))
    painter.drawEllipse(QRectF(x + 23 * scale, y - 5 * scale, 11 * scale, 6 * scale))


def _arrow(painter, start, end, color, label):
    """Draw a labeled force arrow while keeping its text inside the canvas."""
    pen = QPen(QColor(color), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawLine(start, end)
    dx, dy = end.x() - start.x(), end.y() - start.y()
    length = max(1.0, sqrt(dx * dx + dy * dy))
    ux, uy = dx / length, dy / length
    left = QPointF(end.x() - 13 * ux + 7 * uy, end.y() - 13 * uy - 7 * ux)
    right = QPointF(end.x() - 13 * ux - 7 * uy, end.y() - 13 * uy + 7 * ux)
    painter.drawLine(end, left)
    painter.drawLine(end, right)
    painter.setPen(QColor(color))
    painter.setFont(QFont("", 11, QFont.Weight.Bold))
    label_width = painter.fontMetrics().horizontalAdvance(label)
    if abs(dx) >= abs(dy):
        label_x = end.x() + 9 if dx >= 0 else end.x() - label_width - 9
        label_y = end.y() - 8
    else:
        label_x = end.x() + 9
        label_y = end.y() + (5 if dy < 0 else 17)
    device_width = painter.device().width() if painter.device() is not None else 10_000
    device_height = painter.device().height() if painter.device() is not None else 10_000
    label_x = max(8.0, min(float(label_x), device_width - label_width - 8.0))
    label_y = max(18.0, min(float(label_y), device_height - 8.0))
    painter.drawText(QPointF(label_x, label_y), label)


class ForceExperimentCanvas(AircraftModelViewport):
    """Fixed aircraft view that overlays the four basic flight forces."""
    def __init__(self):
        super().__init__(
            caption="YOUR AIRCRAFT  •  FIXED TEACHING VIEW",
            interactive=False,
        )
        self.speed = 55
        self.engine_push = 55
        self.load = 55
        self.wing_angle = 3
        self.zoom = 0.62
        self.setMinimumHeight(360)

    def _vertical_balance(self):
        """Return a teaching-scale lift-minus-load score, not a certified force."""
        return self.speed + self.wing_angle * 3 - self.load

    def _forward_balance(self):
        """Return a teaching-scale thrust-minus-drag score."""
        return self.engine_push - int(self.speed * 0.76)

    def model_offset(self):
        # Translate the cached aircraft layer rather than rebuilding its mesh.
        # This makes the response both visible and inexpensive while sliders move.
        forward = max(-18.0, min(18.0, self._forward_balance() * 0.22))
        vertical = max(-18.0, min(18.0, -self._vertical_balance() * 0.22))
        return QPointF(forward, vertical)

    def model_screen_rotation(self):
        # Positive wing angle and excess lift raise the nose on the screen.
        attitude = -self.wing_angle * 0.55 - self._vertical_balance() * 0.10
        return max(-10.0, min(10.0, attitude))

    def paint_overlay(self, painter):
        # Forces belong to the saved aircraft.  Do not leave detached arrows
        # and labels floating in an otherwise empty teaching canvas.
        if not self._grids:
            return
        center = self._projected_center
        vertical_clearance = min(self.height() * 0.19, 105.0)
        horizontal_clearance = min(self.width() * 0.25, 205.0)
        lift = 28 + max(0, self.speed + self.wing_angle * 3) * 0.48
        weight = 28 + self.load * 0.48
        thrust = 28 + self.engine_push * 0.48
        drag = 24 + self.speed * 0.39
        _arrow(
            painter, center + QPointF(0, -vertical_clearance),
            center + QPointF(0, -vertical_clearance - lift), "#058ec4", "Wing lift",
        )
        _arrow(
            painter, center + QPointF(0, vertical_clearance),
            center + QPointF(0, vertical_clearance + weight), "#ce8512", "Gravity",
        )
        _arrow(
            painter, center + QPointF(horizontal_clearance, 0),
            center + QPointF(horizontal_clearance + thrust, 0), "#159862", "Engine thrust",
        )
        _arrow(
            painter, center + QPointF(-horizontal_clearance, 0),
            center + QPointF(-horizontal_clearance - drag, 0), "#d65353", "Air resistance",
        )

        vertical = self._vertical_balance()
        forward = self._forward_balance()
        vertical_story = "CLIMBING" if vertical > 12 else "SINKING" if vertical < -12 else "LEVEL"
        speed_story = "SPEEDING UP" if forward > 12 else "SLOWING DOWN" if forward < -8 else "STEADY SPEED"
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(7, 25, 39, 220))
        badge_width = 235
        painter.drawRoundedRect(self.width() - badge_width - 18, 14, badge_width, 58, 7, 7)
        painter.setPen(QColor("#ddecf5"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        painter.drawText(
            self.width() - badge_width, 38,
            f"AIRCRAFT RESPONSE   {vertical_story}",
        )
        painter.setPen(QColor("#58c5ef"))
        painter.drawText(self.width() - badge_width, 59, speed_story)


class LearnFlightWidget(TabWidget):
    """Interactive four-forces lesson driven by simple qualitative controls."""
    def __init__(self):
        super().__init__()
        style_learner_page(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)
        _title(layout, "How Planes Fly", "Move the controls and watch the four pushes on an airplane change.")
        body = QHBoxLayout()
        body.setSpacing(12)
        self.canvas = ForceExperimentCanvas()
        body.addWidget(self.canvas, 3)
        controls = QGroupBox("FLIGHT CONDITIONS")
        self.controls = controls
        form = QFormLayout(controls)
        self.speed = self._slider(10, 100, 55)
        self.push = self._slider(10, 100, 55)
        self.load = self._slider(10, 100, 55)
        self.wing_angle = self._slider(-5, 15, 3)
        form.addRow("How fast through the air?", self.speed)
        form.addRow("How hard does the engine push?", self.push)
        form.addRow("How many people and bags?", self.load)
        form.addRow("Wing angle to the air?", self.wing_angle)
        body.addWidget(controls, 2)
        layout.addLayout(body)
        self.result = QLabel()
        self.result.setWordWrap(True)
        self.result.setStyleSheet("font-size:16px; padding:16px; background:#0c2233; border:1px solid #28475d; border-radius:8px;")
        layout.addWidget(self.result)
        for slider in (self.speed, self.push, self.load, self.wing_angle):
            slider.valueChanged.connect(self._update_experiment)
        self.load_from_values()

    def load_from_values(self):
        """Show the saved aircraft, or lock the lesson until one has been built."""
        built = bool(getattr(rcaide_io, "learner_vehicle_built", False))
        self.canvas.set_vehicle(rcaide_io.vehicle if built else RCAIDE.Vehicle())
        self.controls.setEnabled(built)
        if built:
            self._update_experiment()
        else:
            self.result.setText(
                "Build and save an aircraft in Learner Setup to explore its forces."
            )

    def update_layout(self):
        self.load_from_values()

    @staticmethod
    def _slider(low, high, value):
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(low, high)
        slider.setValue(value)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider.setTickInterval(15)
        return slider

    def _update_experiment(self):
        """Apply slider values to the canvas and narrate the resulting motion."""
        if not getattr(rcaide_io, "learner_vehicle_built", False):
            self.canvas.update()
            self.result.setText(
                "Build and save an aircraft in Learner Setup to explore its forces."
            )
            return
        self.canvas.speed = self.speed.value()
        self.canvas.engine_push = self.push.value()
        self.canvas.load = self.load.value()
        self.canvas.wing_angle = self.wing_angle.value()
        self.canvas.update()
        vertical = (
            self.speed.value()
            + self.wing_angle.value() * 3
            - self.load.value()
        )
        forward = self.push.value() - int(self.speed.value() * 0.76)
        if vertical < -12:
            up_down = "Gravity wins, so the airplane starts sinking. Try more speed, a little more wing angle, or less load."
        elif vertical > 12:
            up_down = "The wing push wins, so the airplane tilts upward and can climb."
        else:
            up_down = "Wing push and gravity are close to balanced, which helps level flight."
        if forward < -8:
            ahead = "Air resistance is slowing it down. Add engine push."
        elif forward > 12:
            ahead = "The engine wins, so the airplane speeds up."
        else:
            ahead = "Engine push and air resistance are close to balanced, so speed stays steady."
        self.result.setText(f"<b>What happens?</b> {up_down}<br>{ahead}")


class FlightSimulationCanvas(AircraftModelViewport):
    """Animate the saved aircraft along a fixed five-stage teaching route."""
    def __init__(self):
        super().__init__(
            caption="LIVE MODEL  •  ORIENTATION LOCKED FOR FLIGHT",
            interactive=False,
        )
        self.yaw = 90.0
        self.pitch = 6.0
        self.zoom = 0.30
        self.progress = 0.0
        self.safe_ratio = 1.0
        self.finished = False
        self.setMinimumHeight(360)

    @staticmethod
    def phase_for_progress(progress):
        """Map normalized route progress to stage, landing-gear state, and pitch."""
        progress = max(0.0, min(1.0, float(progress)))
        if progress < 0.12:
            return "TAKEOFF", True, 0.0
        if progress < 0.30:
            return "CLIMB", False, -10.0
        if progress < 0.68:
            return "CRUISE", False, 0.0
        if progress < 0.88:
            return "DESCENT", False, 7.0
        return "LANDING", True, 0.0

    def _route_dimensions(self):
        return (
            self.width() * 0.12,
            self.width() * 0.88,
            self.height() * 0.78,
            self.height() * 0.32,
        )

    def flight_path_point(self, progress=None):
        """Return the screen position on the takeoff-to-landing route."""
        progress = self.progress if progress is None else progress
        progress = max(0.0, min(1.0, float(progress)))
        left, right, ground_y, cruise_y = self._route_dimensions()
        x = left + progress * (right - left)
        if progress < 0.12:
            y = ground_y
        elif progress < 0.30:
            amount = (progress - 0.12) / 0.18
            smooth = amount * amount * (3.0 - 2.0 * amount)
            y = ground_y + (cruise_y - ground_y) * smooth
        elif progress < 0.68:
            y = cruise_y
        elif progress < 0.88:
            amount = (progress - 0.68) / 0.20
            smooth = amount * amount * (3.0 - 2.0 * amount)
            y = cruise_y + (ground_y - cruise_y) * smooth
        else:
            y = ground_y
        return QPointF(x, y)

    def _draw_background(self, painter):
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#dff3ff"))
        gradient.setColorAt(0.75, QColor("#f4f9fc"))
        gradient.setColorAt(1, QColor("#dbe9df"))
        painter.fillRect(self.rect(), gradient)
        left, right, ground_y, cruise_y = self._route_dimensions()

        # Departure and arrival runways.
        painter.setPen(QPen(QColor("#526977"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(left - 34, ground_y), QPointF(left + self.width() * 0.12, ground_y))
        painter.drawLine(QPointF(right - self.width() * 0.12, ground_y), QPointF(right + 34, ground_y))
        painter.setPen(QPen(QColor("#ffffff"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(left - 34, ground_y), QPointF(left + self.width() * 0.12, ground_y))
        painter.drawLine(QPointF(right - self.width() * 0.12, ground_y), QPointF(right + 34, ground_y))

        path = QPainterPath(self.flight_path_point(0.0))
        path.lineTo(self.flight_path_point(0.12))
        path.cubicTo(
            self.flight_path_point(0.17), self.flight_path_point(0.25),
            self.flight_path_point(0.30),
        )
        path.lineTo(self.flight_path_point(0.68))
        path.cubicTo(
            self.flight_path_point(0.73), self.flight_path_point(0.83),
            self.flight_path_point(0.88),
        )
        path.lineTo(self.flight_path_point(1.0))
        painter.setPen(QPen(QColor(255, 255, 255, 210), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawPath(path)
        painter.setPen(QPen(QColor("#477d9a"), 2, Qt.PenStyle.DashLine))
        painter.drawPath(path)

        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        painter.setPen(QColor("#496779"))
        painter.drawText(16, 24, self.caption)
        stage_labels = (
            (0.04, ground_y + 31, "TAKEOFF"),
            (0.19, (ground_y + cruise_y) / 2, "CLIMB"),
            (0.47, cruise_y - 19, "CRUISE"),
            (0.77, (ground_y + cruise_y) / 2, "DESCENT"),
            (0.92, ground_y + 31, "LANDING"),
        )
        for fraction, y, label in stage_labels:
            painter.drawText(int(left + fraction * (right - left) - 22), int(y), label)

    def model_offset(self):
        """Move the cached aircraft model along the route without rebuilding it."""
        point = self.flight_path_point()
        base = QPointF(self._model_rect().center())
        _, gear_down, _ = self.phase_for_progress(self.progress)
        if gear_down and not self._base_model_bounds.isNull():
            # The route line represents the runway during takeoff and landing.
            # Lift the model so its wheels, rather than its center, sit on it.
            _, _, main_wheel, nose_wheel = self._landing_gear_geometry()
            lowest_wheel = max(main_wheel.y(), nose_wheel.y())
            point -= QPointF(0, lowest_wheel)
        if self.safe_ratio < 1.0 and self.progress > 0.14:
            point += QPointF(0, min(self.height() * 0.18, (self.progress - 0.14) * self.height() * 0.55))
        return point - base

    def model_screen_rotation(self):
        return self.phase_for_progress(self.progress)[2]

    def _landing_gear_geometry(self):
        """Return gear attachment and wheel points relative to model center."""
        bounds = self._base_model_bounds
        center = QPointF(self._model_rect().center())
        left = bounds.left() - center.x()
        width = bounds.width()
        underside = bounds.bottom() - center.y()
        gear_drop = max(10.0, min(17.0, self.width() * 0.015))
        main_attach = QPointF(left + width * 0.43, underside - 3.0)
        nose_attach = QPointF(left + width * 0.77, underside - 2.0)
        main_wheel = QPointF(main_attach.x() - 2.0, underside + gear_drop)
        nose_wheel = QPointF(nose_attach.x() + 1.0, underside + gear_drop)
        return main_attach, nose_attach, main_wheel, nose_wheel

    def paint_overlay(self, painter):
        """Draw landing gear, stage status, and mission progress over the model."""
        stage, gear_down, attitude = self.phase_for_progress(self.progress)
        # Landing gear is deployed for runway operations and retracted in the air.
        if gear_down:
            painter.save()
            painter.translate(self._projected_center)
            painter.rotate(attitude)
            main_attach, nose_attach, main_wheel, nose_wheel = self._landing_gear_geometry()
            painter.setPen(QPen(QColor("#263f50"), 2))
            painter.drawLine(main_attach, main_wheel)
            painter.drawLine(nose_attach, nose_wheel)
            painter.setBrush(QColor("#263f50"))
            painter.drawEllipse(main_wheel, 4, 4)
            painter.drawEllipse(nose_wheel, 3, 3)
            painter.restore()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(7, 25, 39, 220))
        painter.drawRoundedRect(self.width() - 205, 14, 187, 55, 7, 7)
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        painter.setPen(QColor("#ddecf5"))
        painter.drawText(self.width() - 190, 37, f"FLIGHT STAGE   {stage}")
        painter.setPen(QColor("#58c5ef" if not gear_down else "#e1a93b"))
        painter.drawText(
            self.width() - 190, 58,
            "LANDING GEAR DOWN" if gear_down else "LANDING GEAR RETRACTED",
        )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#1686b8" if self.safe_ratio >= 1.0 else "#d48232"))
        width = max(8, int((self.width() - 84) * self.progress))
        painter.drawRoundedRect(42, self.height() - 15, width, 5, 2, 2)


class TestFlightWidget(TabWidget):
    """Run a lightweight visual flight lesson using speed and load margins."""
    def __init__(self):
        super().__init__()
        style_learner_page(self)
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self._step_simulation)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)
        _title(
            layout,
            "Run Mission",
            "Run a complete trip from takeoff through climb, cruise, descent, and landing.",
        )
        content = QHBoxLayout()
        self.canvas = FlightSimulationCanvas()
        content.addWidget(self.canvas, 3)
        controls = QGroupBox("TEST SETTINGS")
        form = QFormLayout(controls)
        self.speed = QSlider(Qt.Orientation.Horizontal)
        self.speed.setRange(50, 600)
        self.load = QSlider(Qt.Orientation.Horizontal)
        self.load.setRange(40, 100)
        self.load.setValue(100)
        self.speed_label = QLabel()
        self.load_label = QLabel()
        form.addRow("Travel speed", self.speed)
        form.addRow("", self.speed_label)
        form.addRow("Passengers, cargo, and fuel", self.load)
        form.addRow("", self.load_label)
        self.start_button = QPushButton("▶  RUN COMPLETE FLIGHT")
        self.start_button.setProperty("primary", True)
        self.start_button.clicked.connect(self.start_simulation)
        form.addRow(self.start_button)
        content.addWidget(controls, 2)
        layout.addLayout(content)

        cards = QGridLayout()
        self.air_card = _info_card("Will it stay up?")
        self.time_card = _info_card("How long is the trip?")
        self.speed_card = _info_card("A comfortable minimum speed")
        cards.addWidget(self.air_card, 0, 0)
        cards.addWidget(self.time_card, 0, 1)
        cards.addWidget(self.speed_card, 0, 2)
        layout.addLayout(cards)
        self.why = QLabel()
        self.why.setWordWrap(True)
        self.why.setStyleSheet("font-size:15px; padding:14px; background:#0c2233; border:1px solid #28475d; border-radius:8px;")
        layout.addWidget(self.why)
        self.speed.valueChanged.connect(self._recalculate)
        self.load.valueChanged.connect(self._recalculate)
        self.load_from_values()

    def load_from_values(self):
        data = _active_data()
        cruise_kmh = int(float(data["mission"]["speed_m_s"]) * 3.6)
        self.speed.setValue(max(self.speed.minimum(), min(cruise_kmh, self.speed.maximum())))
        self.load.setValue(100)
        self.canvas.progress = 0
        self.canvas.set_vehicle()
        self._recalculate()

    def _flight_numbers(self):
        """Calculate comfortable speed, safety ratio, and approximate trip time."""
        data = _active_data()
        metrics = classroom_metrics(data)
        load_fraction = self.load.value() / 100.0
        comfortable = metrics["stall_speed_m_s"] * 3.6 * 1.2 * sqrt(load_fraction)
        chosen = float(self.speed.value())
        ratio = chosen / comfortable
        trip_minutes = float(data["mission"]["distance_km"]) / chosen * 60
        return comfortable, ratio, trip_minutes

    def _recalculate(self):
        """Refresh the learner-facing outcome whenever speed or load changes."""
        comfortable, ratio, minutes = self._flight_numbers()
        self.canvas.safe_ratio = ratio
        self.canvas.update()
        self.speed_label.setText(f"{self.speed.value()} km/h")
        self.load_label.setText(f"{self.load.value()}% of the plane's allowed load")
        self.speed_card.value_label.setText(f"About {comfortable:.0f} km/h")
        self.speed_card.detail_label.setText("Below this, the wing may not push enough air downward.")
        self.time_card.value_label.setText(f"About {minutes:.0f} minutes")
        self.time_card.detail_label.setText("Faster travel shortens the trip, but creates more air resistance.")
        if ratio < 0.85:
            self.air_card.value_label.setText("No — too slow")
            self.air_card.detail_label.setText("The plane will sink before reaching the goal.")
            self.why.setText("Try this: increase speed, carry less, or return to Vehicle Setup and make a larger wing.")
        elif ratio < 1.0:
            self.air_card.value_label.setText("Almost")
            self.air_card.detail_label.setText("There is not enough safety cushion for a comfortable flight.")
            self.why.setText("The wing is close to making enough upward push, but a gust could make the plane sink.")
        elif ratio > 2.4:
            self.air_card.value_label.setText("Yes — very fast")
            self.air_card.detail_label.setText("It stays up, but pushing through the air this fast wastes energy.")
            self.why.setText("Try slowing down while staying above the comfortable minimum speed.")
        else:
            self.air_card.value_label.setText("Yes — good flight")
            self.air_card.detail_label.setText("The wing has a comfortable speed cushion.")
            self.why.setText("The airplane should complete this simplified mission.")

    def start_simulation(self):
        """Reset the route, lock its controls, and start the animation timer."""
        self.timer.stop()
        self.canvas.progress = 0.0
        self.canvas.finished = False
        self._recalculate()
        self.start_button.setText("FLIGHT IN PROGRESS…")
        self.start_button.setEnabled(False)
        self.speed.setEnabled(False)
        self.load.setEnabled(False)
        self.timer.start()

    def _step_simulation(self):
        """Advance one animation frame and stop at success or loss of lift."""
        self.canvas.progress = min(1.0, self.canvas.progress + 0.012)
        self.canvas.update()
        if self.canvas.safe_ratio < 1.0 and self.canvas.progress >= 0.32:
            self.timer.stop()
            self.start_button.setText("PLANE SANK — TRY AGAIN")
            self.start_button.setEnabled(True)
            self.speed.setEnabled(True)
            self.load.setEnabled(True)
            self._record_result(False)
            return
        if self.canvas.progress >= 1.0:
            self.timer.stop()
            self.start_button.setText("✓  GOAL REACHED — FLY AGAIN")
            self.start_button.setEnabled(True)
            self.speed.setEnabled(True)
            self.load.setEnabled(True)
            self._record_result(True)

    def _record_result(self, success):
        """Store a compact result record for other learner activities."""
        comfortable, ratio, minutes = self._flight_numbers()
        rcaide_io.learner_last_run = {
            "success": bool(success),
            "aircraft": _active_data()["vehicle"]["name"],
            "speed_kmh": self.speed.value(),
            "load_percent": self.load.value(),
            "minimum_speed_kmh": comfortable,
            "trip_minutes": minutes,
            "speed_margin": ratio,
        }

    def update_layout(self):
        self._recalculate()


class LearnerMissionWidget(TabWidget):
    """The three mission choices needed for the learner cruise."""

    def __init__(self):
        super().__init__()
        style_learner_page(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)
        _title(
            layout,
            "Mission Setup",
            "Define one straightforward cruise. The run still shows takeoff and landing so the complete trip is easy to follow.",
        )
        content = QHBoxLayout()
        content.setSpacing(12)
        form_box = QGroupBox("CRUISE CONDITIONS")
        form = QFormLayout(form_box)
        self.altitude = self._field(0, 25_000, " m", 0)
        self.speed = self._field(10, 500, " m/s", 1)
        self.distance = self._field(1, 20_000, " km", 1)
        form.addRow("Cruise altitude", self.altitude)
        form.addRow("Cruise speed", self.speed)
        form.addRow("Cruise distance", self.distance)
        content.addWidget(form_box, 2)
        self.preview = AircraftModelViewport(
            caption="CURRENT VEHICLE  •  FIXED REVIEW VIEW",
            interactive=False,
        )
        self.preview.setMinimumHeight(330)
        content.addWidget(self.preview, 3)
        layout.addLayout(content)
        explanation = QLabel(
            "Cruise altitude is how high the aircraft flies, cruise speed is how fast it travels, "
            "and distance controls how long the trip lasts."
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet(
            "font-size:15px; color:#62c4ef; padding:14px; background:#0c2233; "
            "border:1px solid #28475d; border-radius:8px;"
        )
        layout.addWidget(explanation)
        cards = QGridLayout()
        self.time_card = _info_card("PLANNED TRIP TIME")
        self.speed_card = _info_card("CRUISE SPEED")
        self.altitude_card = _info_card("CRUISE ALTITUDE")
        cards.addWidget(self.time_card, 0, 0)
        cards.addWidget(self.speed_card, 0, 1)
        cards.addWidget(self.altitude_card, 0, 2)
        layout.addLayout(cards)
        actions = QHBoxLayout()
        actions.addStretch()
        save = QPushButton("Save Mission and Continue")
        save.setProperty("primary", True)
        save.clicked.connect(self.save_and_continue)
        actions.addWidget(save)
        layout.addLayout(actions)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        for field in (self.altitude, self.speed, self.distance):
            field.valueChanged.connect(self._update_summary)
        self.load_from_values()

    @staticmethod
    def _field(low, high, suffix, decimals):
        field = QDoubleSpinBox()
        field.setRange(low, high)
        field.setDecimals(decimals)
        field.setSuffix(suffix)
        return field

    def load_from_values(self):
        mission_data = _active_data()["mission"]
        self.altitude.setValue(float(mission_data["altitude_m"]))
        self.speed.setValue(float(mission_data["speed_m_s"]))
        self.distance.setValue(float(mission_data["distance_km"]))
        self.preview.set_vehicle()
        self._update_summary()

    def _update_summary(self):
        """Explain how the chosen speed and distance determine trip duration."""
        trip_minutes = self.distance.value() / (self.speed.value() * 3.6) * 60.0
        self.time_card.value_label.setText(f"About {trip_minutes:.0f} minutes")
        self.time_card.detail_label.setText(f"For {self.distance.value():.0f} km")
        self.speed_card.value_label.setText(f"{self.speed.value() * 3.6:.0f} km/h")
        self.speed_card.detail_label.setText("The aircraft holds this speed during cruise.")
        self.altitude_card.value_label.setText(f"{self.altitude.value():.0f} m")
        self.altitude_card.detail_label.setText("Height above sea level during cruise.")

    def save_mission(self):
        """Save the three cruise choices and rebuild the hidden RCAIDE mission."""
        data = _active_data()
        data["mission"].update({
            "altitude_m": self.altitude.value(),
            "speed_m_s": self.speed.value(),
            "distance_km": self.distance.value(),
        })
        apply_learner_setup(data)
        rcaide_io.learner_last_run = None
        trip_minutes = self.distance.value() / (self.speed.value() * 3.6) * 60.0
        self.status.setText(
            f"Mission saved. Planned cruise time is about {trip_minutes:.0f} minutes."
        )

    def save_and_continue(self):
        self.save_mission()
        _open_tab(self, "Run Mission")

    def update_layout(self):
        self.load_from_values()


class LearnerResultsWidget(TabWidget):
    """Present the latest learner flight result as plain-language outcome cards."""
    """Plain-language summary of the most recent learner mission run."""

    def __init__(self):
        super().__init__()
        style_learner_page(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)
        _title(layout, "Results Viewer", "Review the latest mission run without advanced engineering output tables.")
        content = QHBoxLayout()
        content.setSpacing(12)
        self.preview = AircraftModelViewport(
            caption="MISSION VEHICLE  •  FIXED REVIEW VIEW",
            interactive=False,
        )
        self.preview.setMinimumHeight(330)
        content.addWidget(self.preview, 3)
        cards = QVBoxLayout()
        self.outcome = _info_card("MISSION OUTCOME")
        self.trip = _info_card("TRIP TIME")
        self.speed_result = _info_card("SPEED CHECK")
        cards.addWidget(self.outcome)
        cards.addWidget(self.trip)
        cards.addWidget(self.speed_result)
        content.addLayout(cards, 2)
        layout.addLayout(content)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet(
            "font-size:16px; padding:16px; background:#0c2233; "
            "border:1px solid #28475d; border-radius:8px;"
        )
        layout.addWidget(self.summary)
        actions = QHBoxLayout()
        vehicle_button = QPushButton("Adjust Vehicle")
        mission_button = QPushButton("Adjust Mission")
        run_button = QPushButton("Run Again")
        run_button.setProperty("primary", True)
        vehicle_button.clicked.connect(lambda: _open_tab(self, "Vehicle Setup"))
        mission_button.clicked.connect(lambda: _open_tab(self, "Mission Setup"))
        run_button.clicked.connect(lambda: _open_tab(self, "Run Mission"))
        actions.addWidget(vehicle_button)
        actions.addWidget(mission_button)
        actions.addStretch()
        actions.addWidget(run_button)
        layout.addLayout(actions)
        layout.addStretch()
        self.load_from_values()

    def load_from_values(self):
        self.preview.set_vehicle()
        result = getattr(rcaide_io, "learner_last_run", None)
        if not result:
            self.outcome.value_label.setText("No run yet")
            self.outcome.detail_label.setText("Open Run Mission and fly the current aircraft.")
            self.trip.value_label.setText("—")
            self.trip.detail_label.setText("Trip time appears after a run.")
            self.speed_result.value_label.setText("—")
            self.speed_result.detail_label.setText("The speed check appears after a run.")
            self.summary.setText("Results are kept simple: outcome, trip time, and whether the selected speed provided enough lift.")
            return
        success = bool(result["success"])
        self.outcome.value_label.setText("Mission completed" if success else "Mission not completed")
        self.outcome.detail_label.setText(result["aircraft"])
        self.trip.value_label.setText(f'About {result["trip_minutes"]:.0f} minutes')
        self.trip.detail_label.setText(f'At {result["speed_kmh"]:.0f} km/h')
        self.speed_result.value_label.setText(
            "Comfortable margin" if result["speed_margin"] >= 1.0 else "Too slow"
        )
        self.speed_result.detail_label.setText(
            f'Minimum comfortable speed was about {result["minimum_speed_kmh"]:.0f} km/h.'
        )
        self.summary.setText(
            "The aircraft reached the destination." if success else
            "The aircraft could not maintain the simplified flight. Increase speed, reduce load, or enlarge the wing."
        )

    def update_layout(self):
        self.load_from_values()


class CompareDesignsWidget(TabWidget):
    """Keep up to three learner designs for side-by-side comparison."""
    def __init__(self):
        super().__init__()
        style_learner_page(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)
        _title(layout, "Design Showdown", "Save different airplanes and discover what each design is good at.")
        intro = QLabel("Tip: give each airplane a different name in Vehicle Setup before adding it here.")
        intro.setStyleSheet("color:#b9d7f5;")
        layout.addWidget(intro)
        actions = QHBoxLayout()
        save = QPushButton("Add This Airplane")
        save.setProperty("primary", True)
        remove = QPushButton("Remove Selected Airplane")
        save.clicked.connect(self.save_current)
        remove.clicked.connect(self.remove_selected)
        actions.addWidget(save)
        actions.addWidget(remove)
        actions.addStretch()
        layout.addLayout(actions)
        showcase = QHBoxLayout()
        self.preview = AircraftModelViewport(
            caption="LEFT DRAG: ROTATE  •  RIGHT DRAG: MOVE  •  WHEEL: ZOOM  •  DOUBLE-CLICK: RESET",
            interactive=True,
        )
        self.preview.setMinimumHeight(245)
        showcase.addWidget(self.preview, 3)
        self.selection_story = _info_card(
            "DESIGN PROFILE",
            "Current aircraft",
            "Select a saved design to inspect its real geometry and strengths.",
        )
        showcase.addWidget(self.selection_story, 2)
        layout.addLayout(showcase)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Airplane", "People", "Comfortable speed", "Trip time", "Personality", "Best for"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.currentCellChanged.connect(self._show_selected_design)
        layout.addWidget(self.table, 1)
        self.lesson = QLabel(
            "There is no single best airplane. A large wing may help slow flight, while a smaller wing may suit a faster airplane."
        )
        self.lesson.setWordWrap(True)
        self.lesson.setStyleSheet("font-size:15px; padding:12px; background:#0c2233; border:1px solid #28475d; border-radius:8px;")
        layout.addWidget(self.lesson)
        self.load_from_values()

    def save_current(self):
        """Store a copy of the current compact learner design."""
        saved = getattr(rcaide_io, "learner_comparison_data", [])
        if len(saved) >= 3:
            QMessageBox.information(self, "Three airplanes saved", "Remove one before adding another.")
            return
        saved.append(deepcopy(_active_data()))
        rcaide_io.learner_comparison_data = saved
        self.load_from_values()

    def remove_selected(self):
        row = self.table.currentRow()
        saved = getattr(rcaide_io, "learner_comparison_data", [])
        if 0 <= row < len(saved):
            saved.pop(row)
            self.load_from_values()

    def load_from_values(self):
        saved = getattr(rcaide_io, "learner_comparison_data", [])
        self.table.setRowCount(len(saved))
        for row, raw in enumerate(saved):
            data = _merged_learner_data(raw)
            story = describe_design(data)
            values = (
                data["vehicle"]["name"],
                str(data["vehicle"]["passengers"]),
                f'{story["comfortable_speed_kmh"]:.0f} km/h',
                f'{story["trip_minutes"]:.0f} min',
                story["personality"],
                story["best_for"],
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, column, item)
        if saved:
            row = min(max(self.table.currentRow(), 0), len(saved) - 1)
            self.table.selectRow(row)
            self._show_selected_design(row, 0, -1, -1)
        else:
            self.preview.set_vehicle()
            self.selection_story.value_label.setText(_active_data()["vehicle"]["name"])
            self.selection_story.detail_label.setText("Add this aircraft to begin a side-by-side design study.")

    def _show_selected_design(self, row, column=0, previous_row=-1, previous_column=-1):
        """Rebuild and preview the selected design from its saved inputs."""
        saved = getattr(rcaide_io, "learner_comparison_data", [])
        if not 0 <= row < len(saved):
            return
        data = _merged_learner_data(saved[row])
        story = describe_design(data)
        self.preview.set_vehicle(build_learner_vehicle(data))
        self.selection_story.value_label.setText(data["vehicle"]["name"])
        self.selection_story.detail_label.setText(
            f'{story["personality"]}. Best for {story["best_for"].lower()}. '
            f'Comfortable flight starts near {story["comfortable_speed_kmh"]:.0f} km/h.'
        )

    def update_layout(self):
        self.load_from_values()


class BalancePicture(AircraftModelViewport):
    """Fixed side view with an illustrative center-of-gravity safety band."""
    def __init__(self):
        super().__init__(
            caption="LOADED AIRCRAFT  •  FIXED SIDE VIEW",
            interactive=False,
        )
        self.balance = 0.45
        self.safe = True
        self.yaw = 90
        self.pitch = 6
        self.setMinimumHeight(275)

    def paint_overlay(self, painter):
        left, right, y = 70, self.width() - 70, self.height() - 38
        painter.setPen(QPen(QColor("#7f9bad"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(left, y, right, y)
        safe_left = left + 0.35 * (right - left)
        safe_right = left + 0.52 * (right - left)
        painter.setPen(QPen(QColor("#1db477"), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(safe_left, y), QPointF(safe_right, y))
        x = left + self.balance * (right - left)
        painter.setBrush(QColor("#1db477" if self.safe else "#d95353"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(x, y), 12, 12)
        painter.setPen(QColor("#48677b"))
        painter.drawText(left - 25, y - 15, "NOSE")
        painter.drawText(right - 15, y - 15, "TAIL")
        painter.drawText(int(safe_left), y + 23, "STEADY ZONE")


class LoadingWidget(TabWidget):
    """Explore passenger, cargo, fuel, total-mass, and balance tradeoffs."""
    def __init__(self):
        super().__init__()
        style_learner_page(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)
        _title(
            layout,
            "Pack the Plane",
            "Choose the passengers, cargo, and fuel, then check the aircraft's weight and balance.",
        )
        controls = QGroupBox("LOAD MANIFEST")
        form = QFormLayout(controls)
        self.passengers = QSpinBox()
        self.cargo = QSpinBox()
        self.cargo.setRange(0, 1000)
        self.cargo.setSuffix(" kg")
        self.fuel = QSpinBox()
        self.fuel.setRange(0, 100000)
        self.fuel.setSuffix(" kg")
        form.addRow("People aboard", self.passengers)
        form.addRow("Cargo", self.cargo)
        form.addRow("Fuel", self.fuel)
        main = QHBoxLayout()
        main.addWidget(controls, 2)
        self.balance_picture = BalancePicture()
        main.addWidget(self.balance_picture, 3)
        layout.addLayout(main)
        self.results = QLabel()
        self.results.setWordWrap(True)
        layout.addWidget(self.results)
        self.explain = QLabel()
        self.explain.setWordWrap(True)
        self.explain.setObjectName("muted")
        self.explain.setStyleSheet(
            "font-size:14px; color:#62c4ef; padding:10px 4px;"
        )
        layout.addWidget(self.explain)
        layout.addStretch()
        for field in (self.passengers, self.cargo, self.fuel):
            field.valueChanged.connect(self._update_results)
        self.load_from_values()

    def load_from_values(self):
        data = _active_data()
        seats = int(data["vehicle"]["passengers"])
        maximum = int(data["vehicle"]["max_takeoff_weight_kg"])
        self.passengers.setRange(0, max(1, seats))
        self.passengers.setValue(seats)
        self.cargo.setValue(10 * seats)
        self.fuel.setMaximum(maximum)
        self.fuel.setValue(int(0.05 * maximum))
        self.balance_picture.set_vehicle()
        self._update_results()

    def _update_results(self):
        """Recalculate loading status and explain its connection to fuel burn."""
        data = _active_data()
        cargo_kg = self.cargo.value()
        result = classroom_loading(data, self.passengers.value(), cargo_kg, self.fuel.value())
        maximum = float(data["vehicle"]["max_takeoff_weight_kg"])
        over = max(0.0, -result["remaining_mass_kg"])
        steady = result["status"] == "Balanced loading zone"
        self.balance_picture.balance = result["balance_fraction"]
        self.balance_picture.safe = steady and over == 0
        self.balance_picture.update()
        if over > 0:
            headline = f"Too heavy by {over:.0f} kg"
            advice = "Remove some cargo, fuel, or passengers before flying."
            color = "#ff9d9d"
        elif not steady:
            headline = "The load is out of balance"
            advice = "Move weight toward the green steady zone."
            color = "#ffd87a"
        else:
            headline = "Ready to fly"
            advice = f'You can still add about {result["remaining_mass_kg"]:.0f} kg.'
            color = "#8ff0b5"
        self.results.setText(
            f'<span style="font-size:23px; font-weight:700;">{headline}</span><br>'
            f'The packed airplane weighs about {result["total_mass_kg"]:.0f} kg. '
            f'This design allows up to {maximum:.0f} kg.<br>{advice}'
        )
        self.results.setStyleSheet(f"font-size:16px; padding:14px; color:{color}; background:#0c2233; border:1px solid #28475d; border-radius:8px;")
        without_cargo = max(1.0, result["total_mass_kg"] - cargo_kg)
        added_weight_percent = 100.0 * cargo_kg / without_cargo
        self.explain.setText(
            "<b>Cargo and fuel burn:</b> "
            f"This cargo adds {cargo_kg:.0f} kg, or about {added_weight_percent:.0f}% "
            "to the otherwise loaded aircraft. More weight requires more lift; "
            "making more lift creates additional drag, so the engine must burn more fuel. "
            "Fuel also has weight, so carrying extra fuel creates a smaller additional penalty. "
            f"This activity assumes {ASSUMED_PERSON_MASS_KG:.0f} kg per passenger; exact fuel burn "
            "depends on the aircraft, speed, altitude, and trip length."
        )

    def update_layout(self):
        self._update_results()


class DesignChallengesWidget(TabWidget):
    """Evaluate the current learner aircraft against guided design missions."""
    def __init__(self):
        super().__init__()
        style_learner_page(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)
        _title(layout, "Missions", "Build an airplane for each mission. The app explains what to try next.")
        body = QHBoxLayout()
        self.list = QListWidget()
        self.list.currentRowChanged.connect(self._show_selected)
        body.addWidget(self.list, 1)
        right = QVBoxLayout()
        self.preview = AircraftModelViewport(
            caption="MISSION AIRCRAFT  •  CURRENT BUILD",
            interactive=False,
        )
        self.preview.setMinimumHeight(300)
        right.addWidget(self.preview, 3)
        self.detail = QLabel()
        self.detail.setWordWrap(True)
        self.detail.setAlignment(Qt.AlignmentFlag.AlignTop)
        right.addWidget(self.detail, 2)
        builder = QPushButton("Open Vehicle Setup")
        builder.setProperty("primary", True)
        builder.clicked.connect(self._open_builder)
        right.addWidget(builder)
        right.addStretch()
        body.addLayout(right, 2)
        layout.addLayout(body)
        self._results = []
        self.load_from_values()

    def load_from_values(self):
        selected = max(0, self.list.currentRow())
        self._results = evaluate_challenges(_active_data())
        self.preview.set_vehicle()
        self.list.clear()
        for result in self._results:
            self.list.addItem(f'{"✓ Complete" if result["passed"] else "○ Try it"} — {result["name"]}')
        if self._results:
            self.list.setCurrentRow(min(selected, len(self._results) - 1))

    def _show_selected(self, row):
        """Explain why the selected mission passes or what to change next."""
        if not 0 <= row < len(self._results):
            return
        result = self._results[row]
        if result["passed"]:
            outcome = "<span style='color:#8ff0b5'><b>Mission complete!</b></span> Try changing one choice and see whether it still passes."
        else:
            outcome = f"<span style='color:#ffd87a'><b>Not yet.</b></span> {result['tip']}"
        self.detail.setText(
            f"<span style='font-size:22px; font-weight:700'>{result['name']}</span><br><br>"
            f"{result['description']}<br><br>{outcome}"
        )
        self.detail.setStyleSheet("font-size:16px; padding:18px; background:#0c2233; border:1px solid #28475d; border-radius:8px;")

    def _open_builder(self):
        parent = self.parentWidget()
        while parent is not None and not isinstance(parent, QTabWidget):
            parent = parent.parentWidget()
        if parent is not None:
            for index in range(parent.count()):
                if parent.tabText(index) == "Vehicle Setup":
                    parent.setCurrentIndex(index)
                    break

    def update_layout(self):
        self.load_from_values()


# Dictionary definitions deliberately avoid unexplained engineering notation.
GLOSSARY = {
    "Air resistance": "The push of air against a moving object. Engineers often call it drag.",
    "Balance point": "The point where an airplane would balance. Loading too far toward the nose or tail can make control difficult.",
    "Chord": "The distance from the front edge to the back edge of a wing.",
    "Drag": "Another name for air resistance that slows an airplane down.",
    "Fuselage": "The main body of an airplane, carrying people, bags, and equipment.",
    "Horizontal stabilizer": "The smaller tail wing that helps stop unwanted nose-up or nose-down motion.",
    "Lift": "The upward aerodynamic push made mainly by the wings.",
    "Maximum takeoff weight": "The heaviest the entire packed airplane is allowed to be when it starts flying.",
    "Reference area": "The main wing area used when comparing airplanes and estimating flight behavior.",
    "SFC": "A fuel-efficiency score for an engine. A lower number means less fuel is needed for the same push.",
    "Span": "The distance from one wingtip to the other.",
    "Stall": "When a wing cannot make enough upward push because the airplane is too slow or the airflow separates.",
    "Sweep": "How far a wing or tail angles backward when viewed from above.",
    "Thrust": "The forward push produced by an engine or propeller.",
    "Vertical stabilizer": "The upright tail surface that helps keep the airplane pointing forward.",
    "Weight": "The downward pull of gravity on the airplane and everything inside it.",
    "Wing loading": "A comparison of airplane weight with wing size. A larger wing usually makes slow flight easier.",
}


# A selected concept points to the aircraft surface where it is easiest to
# understand. The callout text remains the dictionary term, not an internal
# component name.
DICTIONARY_MODEL_TERMS = {
    "Air resistance": "fuselage",
    "Balance point": "fuselage",
    "Chord": "main_wing",
    "Drag": "fuselage",
    "Fuselage": "fuselage",
    "Horizontal stabilizer": "horizontal_stabilizer",
    "Lift": "main_wing",
    "Maximum takeoff weight": "fuselage",
    "Reference area": "main_wing",
    "SFC": "fuselage",
    "Span": "main_wing",
    "Stall": "main_wing",
    "Sweep": "main_wing",
    "Thrust": "fuselage",
    "Vertical stabilizer": "vertical_stabilizer",
    "Weight": "fuselage",
    "Wing loading": "main_wing",
}


def _dictionary_geometry_guides(word, vehicle):
    """Return exact model-space teaching marks for geometric terms."""
    # Geometric terms use measurement guides anchored to the actual saved wing,
    # rather than generic diagram coordinates.
    main_wing = next(
        (
            wing
            for wing in getattr(vehicle, "wings", ())
            if str(getattr(wing, "tag", "")) == "main_wing"
        ),
        None,
    )
    if main_wing is None:
        return []
    origin = [float(value) for value in main_wing.origin[0]]
    span = float(getattr(main_wing.spans, "projected", 0.0) or 0.0)
    semispan = span / 2.0 if bool(getattr(main_wing, "xz_plane_symmetric", False)) else span
    root = float(getattr(main_wing.chords, "root", 0.0) or 0.0)
    tip = float(getattr(main_wing.chords, "tip", root) or root)
    sweep = float(getattr(main_wing.sweeps, "leading_edge", 0.0) or 0.0)

    def point(x, y, z=0.025):
        return [origin[0] + x, origin[1] + y, origin[2] + z]

    chord_y = -0.32 * semispan
    chord_x = abs(chord_y) * tan(sweep)
    local_chord = root + (tip - root) * 0.32
    chord = {
        "start": point(chord_x, chord_y),
        "end": point(chord_x + local_chord, chord_y),
        "text": "chord",
    }
    span_guide = {
        "start": point(0.24 * root, -semispan),
        "end": point(0.24 * root, semispan),
        "text": "span",
    }
    sweep_guide = {
        "start": point(0.0, 0.0),
        "end": point(semispan * tan(sweep), -semispan),
        "text": "sweep",
    }
    if word == "Chord":
        return [chord]
    if word == "Span":
        return [span_guide]
    if word == "Sweep":
        return [sweep_guide]
    if word in {"Reference area", "Wing loading"}:
        chord["text"] = "wing length"
        span_guide["text"] = "wing width"
        return [chord, span_guide]
    return []


class WordsHelpWidget(TabWidget):
    """Connect aviation vocabulary to the saved aircraft's actual geometry."""
    def __init__(self):
        super().__init__()
        style_learner_page(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)
        _title(
            layout,
            "Dictionary",
            "Select an aviation term to see its meaning and where it acts on the aircraft.",
        )
        body = QHBoxLayout()
        self.words = QListWidget()
        self.words.currentTextChanged.connect(self._show_word)
        self.definition = QLabel()
        self.definition.setWordWrap(True)
        self.definition.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.definition.setStyleSheet("font-size:17px; padding:20px; background:#0c2233; border:1px solid #28475d; border-radius:8px;")
        self.preview = AircraftModelViewport(
            caption="LEFT DRAG: ROTATE  •  RIGHT DRAG: MOVE  •  WHEEL: ZOOM  •  DOUBLE-CLICK: RESET",
            interactive=True,
        )
        self.preview.setMinimumHeight(360)
        self._model_callouts = []
        body.addWidget(self.words, 1)
        body.addWidget(self.definition, 2)
        body.addWidget(self.preview, 3)
        layout.addLayout(body, 1)
        for word in GLOSSARY:
            self.words.addItem(word)
        self.load_from_values()
        if self.words.count():
            self.words.setCurrentRow(0)

    def load_from_values(self):
        self.preview.set_vehicle()
        self._model_callouts = learner_component_callout_data(rcaide_io.vehicle)
        current = self.words.currentItem()
        if current is not None:
            self._show_word(current.text())

    def update_layout(self):
        self.load_from_values()

    def _show_word(self, word):
        """Display one definition and highlight its relevant model geometry."""
        if not word:
            return
        self.definition.setText(
            f"<span style='font-size:24px; font-weight:700'>{word}</span>"
            f"<br><br>{GLOSSARY[word]}"
        )
        component = DICTIONARY_MODEL_TERMS.get(word)
        # The selected word is already visible in the definition panel. Keep
        # the model itself clean: use only component highlighting and, where
        # helpful, a geometry measurement mark without a floating text label.
        self.preview.set_callouts([], None)
        self.preview.set_guides(_dictionary_geometry_guides(word, rcaide_io.vehicle))
        self.preview.set_highlight(component)
