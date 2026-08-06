"""Lightweight interactive views of the active RCAIDE learner aircraft.

The learner activity tabs intentionally share this software renderer instead of
opening several VTK windows.  Its surfaces come from the same RCAIDE geometry
generators used by Visualize Geometry, so the picture always represents the
aircraft that the learner built.
"""

from __future__ import annotations

from copy import deepcopy
from math import cos, radians, sin

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QPixmap, QPolygonF
from PyQt6.QtWidgets import QSizePolicy, QWidget

import RCAIDE
from RCAIDE.Library.Methods.Geometry.Planform import fuselage_planform, wing_planform
from RCAIDE.Library.Plots.Geometry.generate_3d_wing_points import generate_3d_wing_points

import rcaide_io
from tabs.visualize_geometry.geometry_helper_functions import generate_fuselage_points_for_viewer


# Component tags come from the learner vehicle builder.  Keeping the palette
# keyed by those tags gives every activity a consistent visual language.
COMPONENT_COLORS = {
    "main_wing": QColor("#55b9ee"),
    "horizontal_stabilizer": QColor("#68d6c4"),
    "vertical_stabilizer": QColor("#68d6c4"),
    "fuselage": QColor("#e7eef6"),
}


def aircraft_surface_grids(vehicle=None):
    """Return named surface grids generated from an RCAIDE vehicle."""
    # Planform utilities may populate derived values on components, so work on
    # a copy instead of mutating the shared active aircraft during painting.
    geometry = deepcopy(vehicle if vehicle is not None else rcaide_io.vehicle)
    grids = []
    for wing in geometry.wings:
        wing_planform(wing)
        # Activity previews use a lighter display tessellation than the full VG
        # tab while preserving the exact dimensions and component positions.
        points = generate_3d_wing_points(wing, 11, plot_centerline=False).PTS
        grids.append((wing.tag, points.copy()))
        # RCAIDE stores many symmetric components as one physical half. Mirror
        # the sampled grid so the software preview shows the complete surface.
        if getattr(wing, "xz_plane_symmetric", False):
            reflected = points.copy()
            reflected[:, :, 1] *= -1
            grids.append((wing.tag, reflected))
        if getattr(wing, "xy_plane_symmetric", False):
            reflected = points.copy()
            reflected[:, :, 2] *= -1
            grids.append((wing.tag, reflected))
    for fuselage in geometry.fuselages:
        fuselage_planform(fuselage)
        grids.append(("fuselage", generate_fuselage_points_for_viewer(fuselage, 12).PTS.copy()))
    return grids


class AircraftModelViewport(QWidget):
    """Mouse-rotatable orthographic view of the real active aircraft surfaces."""

    def __init__(
        self,
        vehicle=None,
        caption="DRAG TO ROTATE  •  SCROLL TO ZOOM",
        interactive=True,
        parent=None,
    ):
        super().__init__(parent)
        self.caption = caption
        self.interactive = bool(interactive)
        # Standard learner presentation: nose right, tail left, with the upper
        # wing and stabilizers visible. Activity tabs keep this view locked.
        self.yaw = 135.0
        self.pitch = 24.0
        self.zoom = 1.0
        self.highlight = None
        # Mouse state is separate from camera state so locked activity views can
        # reuse the same renderer without accepting rotation or pan gestures.
        self._last_mouse = None
        self._drag_mode = None
        self._interaction_timer = QTimer(self)
        self._interaction_timer.setSingleShot(True)
        self._interaction_timer.setInterval(16)
        self._interaction_timer.timeout.connect(self.update)
        self.pan_offset = QPointF()
        self.callouts = []
        self.guides = []
        self.selected_callout = None
        self._grids = []
        # Geometry revisions and camera values form a cache key for the raster
        # model layer. Overlays can then animate without remeshing every frame.
        self._geometry_revision = 0
        self._model_cache_key = None
        self._model_cache = None
        self._projected_center = QPointF()
        self._base_model_bounds = QRectF()
        self.setMinimumSize(320, 230)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(
            Qt.CursorShape.OpenHandCursor if self.interactive else Qt.CursorShape.ArrowCursor
        )
        self.set_vehicle(vehicle)

    def set_interactive(self, enabled):
        """Enable or disable mouse camera controls and update the cursor."""
        self.interactive = bool(enabled)
        self._last_mouse = None
        self.setCursor(
            Qt.CursorShape.OpenHandCursor if self.interactive else Qt.CursorShape.ArrowCursor
        )

    def set_vehicle(self, vehicle=None):
        """Regenerate preview grids from a vehicle and invalidate the model cache."""
        try:
            self._grids = aircraft_surface_grids(vehicle)
        except Exception:
            self._grids = []
        self._geometry_revision += 1
        self._model_cache_key = None
        self.pan_offset = QPointF()
        self.update()

    def set_highlight(self, component):
        """Emphasize one component tag while fading all other surfaces."""
        self.highlight = component
        self._model_cache_key = None
        self.update()

    def set_callouts(self, callouts, selected_component=None):
        """Set model-attached component labels and their optional selection."""
        self.callouts = list(callouts or [])
        self.selected_callout = selected_component
        self.update()

    def set_guides(self, guides):
        """Show model-attached teaching lines such as chord and wingspan."""
        self.guides = list(guides or [])
        self.update()

    def mousePressEvent(self, event):
        """Start rotation with left drag or movement with right/Shift drag."""
        if not self.interactive:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_mouse = event.position()
            self._drag_mode = (
                "move"
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier
                else "rotate"
            )
            self._model_cache_key = None
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif event.button() == Qt.MouseButton.RightButton:
            self._last_mouse = event.position()
            self._drag_mode = "move"
            self.setCursor(Qt.CursorShape.SizeAllCursor)

    def mouseMoveEvent(self, event):
        """Update camera angles or pan offset, throttling repaints to one timer."""
        if not self.interactive or self._last_mouse is None:
            return
        delta = event.position() - self._last_mouse
        if self._drag_mode == "move":
            self.pan_offset += delta
        else:
            self.yaw += delta.x() * 0.45
            self.pitch = max(-70.0, min(70.0, self.pitch - delta.y() * 0.35))
        self._last_mouse = event.position()
        if not self._interaction_timer.isActive():
            self._interaction_timer.start()

    def mouseReleaseEvent(self, event):
        """Finish the gesture and rebuild one antialiased cached model layer."""
        if not self.interactive:
            return
        self._last_mouse = None
        self._drag_mode = None
        self._interaction_timer.stop()
        self._model_cache_key = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.update()

    def mouseDoubleClickEvent(self, event):
        """Restore the standard learner camera and centered model position."""
        if not self.interactive:
            return
        self.yaw = 135.0
        self.pitch = 24.0
        self.zoom = 1.0
        self.pan_offset = QPointF()
        self._model_cache_key = None
        self.update()

    def wheelEvent(self, event):
        """Zoom within limits that keep the aircraft usable and recoverable."""
        if not self.interactive:
            return
        self.zoom = max(0.55, min(2.4, self.zoom * (1.12 if event.angleDelta().y() > 0 else 0.89)))
        self.update()

    def _rotate(self, point):
        """Transform one model point into horizontal, depth, and vertical axes."""
        x, y, z = map(float, point)
        ca, sa = cos(radians(self.yaw)), sin(radians(self.yaw))
        ce, se = cos(radians(self.pitch)), sin(radians(self.pitch))
        # Camera basis: horizontal screen axis, view depth, vertical screen axis.
        horizontal = -sa * x + ca * y
        depth = -ce * ca * x - ce * sa * y - se * z
        vertical = -se * ca * x - se * sa * y + ce * z
        return horizontal, depth, vertical

    def _scene_polygons(self):
        """Convert surface grids to depth-tagged quadrilaterals for painting."""
        cells = []
        rotated_points = []
        for name, grid in self._grids:
            transformed = [[self._rotate(point) for point in row] for row in grid]
            rotated_points.extend(point for row in transformed for point in row)
            rows, columns = len(transformed), len(transformed[0])
            wrap_columns = name == "fuselage"
            column_count = columns if wrap_columns else columns - 1
            for row in range(rows - 1):
                for column in range(column_count):
                    nxt = (column + 1) % columns
                    quad = (
                        transformed[row][column], transformed[row + 1][column],
                        transformed[row + 1][nxt], transformed[row][nxt],
                    )
                    # Average view depth supports a lightweight painter's
                    # algorithm: farther cells are drawn before nearer cells.
                    depth = sum(point[1] for point in quad) / 4.0
                    cells.append((depth, name, quad))
        return cells, rotated_points

    def _model_rect(self):
        return self.rect().adjusted(28, 42, -28, -28)

    def _screen_transform(self, points):
        """Create an orthographic fit-to-window projector for rotated points."""
        model_rect = self._model_rect()
        if not points:
            return lambda point: QPointF(model_rect.center())
        xs = [point[0] for point in points]
        zs = [point[2] for point in points]
        span_x = max(max(xs) - min(xs), 0.01)
        span_z = max(max(zs) - min(zs), 0.01)
        scale = min(model_rect.width() / span_x, model_rect.height() / span_z) * 0.78 * self.zoom
        center_x = (max(xs) + min(xs)) / 2.0
        center_z = (max(zs) + min(zs)) / 2.0
        screen_center = model_rect.center()
        self._projected_center = QPointF(screen_center)
        return lambda point: QPointF(
            screen_center.x() + (point[0] - center_x) * scale,
            screen_center.y() - (point[2] - center_z) * scale,
        )

    def model_offset(self):
        """Screen-space model motion; subclasses can animate without remeshing."""
        return QPointF(self.pan_offset)

    def model_screen_rotation(self):
        """Optional cheap 2-D attitude change applied to the cached model."""
        return 0.0

    def _model_layer(self):
        """Return a cached transparent pixmap containing the aircraft surfaces."""
        key = (
            self.width(), self.height(), round(self.yaw, 2), round(self.pitch, 2),
            round(self.zoom, 3), self.highlight, self._geometry_revision,
            self._last_mouse is not None,
        )
        # Reuse the expensive surface raster until geometry or camera changes.
        if key == self._model_cache_key and self._model_cache is not None:
            return self._model_cache

        layer = QPixmap(self.size())
        layer.fill(Qt.GlobalColor.transparent)
        model_painter = QPainter(layer)
        # Disable antialiasing only during active drag for responsive motion;
        # mouse release immediately produces a polished cached replacement.
        dragging = self._last_mouse is not None
        model_painter.setRenderHint(QPainter.RenderHint.Antialiasing, not dragging)
        cells, points = self._scene_polygons()
        project = self._screen_transform(points)
        self._base_projector = project
        base_center = QPointF(self._projected_center)
        if points:
            projected = [project(point) for point in points]
            xs = [point.x() for point in projected]
            ys = [point.y() for point in projected]
            self._base_model_bounds = QRectF(
                QPointF(min(xs), min(ys)), QPointF(max(xs), max(ys))
            ).normalized()
        else:
            self._base_model_bounds = QRectF()
        for depth, name, quad in sorted(cells, key=lambda item: item[0], reverse=True):
            color = QColor(COMPONENT_COLORS.get(name, QColor("#b8c9d8")))
            if self.highlight and name != self.highlight:
                color.setAlpha(52)
            else:
                shade = max(0.72, min(1.12, 0.92 + depth * 0.012))
                color.setRed(min(255, int(color.red() * shade)))
                color.setGreen(min(255, int(color.green() * shade)))
                color.setBlue(min(255, int(color.blue() * shade)))
                color.setAlpha(238)
            model_painter.setBrush(color)
            # Keep component seams visible even during an interactive drag.
            # Antialiasing alone is reduced while moving for responsiveness.
            model_painter.setPen(QPen(QColor(28, 58, 78, 72), 0.75))
            model_painter.drawPolygon(QPolygonF([project(point) for point in quad]))
        model_painter.end()
        self._model_cache_key = key
        self._model_cache = (layer, base_center, bool(cells))
        return self._model_cache

    def _callout_screen_point(self, world_point, base_center, offset, attitude):
        """Project an annotation point through camera, motion, and 2-D attitude."""
        point = self._base_projector(world_point)
        relative = point - base_center
        angle = radians(attitude)
        rotated = QPointF(
            cos(angle) * relative.x() - sin(angle) * relative.y(),
            sin(angle) * relative.x() + cos(angle) * relative.y(),
        )
        return base_center + offset + rotated

    def _draw_callouts(self, painter, base_center, offset, attitude):
        """Draw leader lines and labels that remain attached as the model moves."""
        if not self.callouts or not hasattr(self, "_base_projector"):
            return
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        left_offset = -min(175.0, self.width() * 0.30)
        right_offset = min(70.0, self.width() * 0.14)
        # Stable component slots reduce overlap and make labels predictable
        # while their leader lines still terminate on actual geometry points.
        arranged_offsets = {
            "vertical_stabilizer": QPointF(left_offset, -145.0),
            "horizontal_stabilizer": QPointF(left_offset, -65.0),
            "main_wing": QPointF(left_offset, 105.0),
            "fuselage": QPointF(right_offset, 45.0),
        }
        for callout in self.callouts:
            component = callout.get("component")
            selected = self.selected_callout == component
            anchor = self._callout_screen_point(callout["anchor"], base_center, offset, attitude)
            if component in arranged_offsets:
                label = base_center + offset + arranged_offsets[component]
            else:
                label = self._callout_screen_point(
                    callout["label_position"], base_center, offset, attitude
                )
            text = str(callout.get("text", "")).replace("\n", " — ")
            text_width = min(210, max(105, painter.fontMetrics().horizontalAdvance(text) + 10))
            label.setX(max(8.0, min(label.x(), self.width() - text_width - 8.0)))
            label.setY(max(28.0, min(label.y(), self.height() - 24.0)))
            color = QColor("#b77a00" if selected else "#214b60")
            painter.setPen(QPen(color, 2.2 if selected else 1.2))
            painter.drawLine(anchor, label)
            painter.setBrush(QColor("#f2b632" if selected else "#2e829f"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(anchor, 4.5 if selected else 3.2, 4.5 if selected else 3.2)
            painter.setPen(color)
            painter.drawText(
                QRectF(label.x() + 5, label.y() - 13, text_width, 30),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                text,
            )

    def _draw_guides(self, painter, base_center, offset, attitude):
        """Draw model-space measurement guides such as chord, span, and sweep."""
        if not self.guides or not hasattr(self, "_base_projector"):
            return
        for guide in self.guides:
            start = self._callout_screen_point(
                guide["start"], base_center, offset, attitude
            )
            end = self._callout_screen_point(
                guide["end"], base_center, offset, attitude
            )
            color = QColor("#e6a900")
            painter.setPen(QPen(color, 3.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(start, end)
            direction = end - start
            length = max(1.0, (direction.x() ** 2 + direction.y() ** 2) ** 0.5)
            normal = QPointF(-direction.y() / length * 6.0, direction.x() / length * 6.0)
            painter.drawLine(start - normal, start + normal)
            painter.drawLine(end - normal, end + normal)

    def _draw_background(self, painter):
        """Paint the shared light technical-grid backdrop used by activities."""
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#eef5fa"))
        gradient.setColorAt(1, QColor("#dceaf3"))
        painter.fillRect(self.rect(), gradient)
        painter.setPen(QPen(QColor(41, 72, 94, 22), 1))
        spacing = 36
        for x in range(0, self.width(), spacing):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), spacing):
            painter.drawLine(0, y, self.width(), y)

    def paintEvent(self, event):
        """Compose background, cached model, guides, callouts, and activity overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_background(painter)
        layer, base_center, has_model = self._model_layer()
        offset = self.model_offset()
        self._projected_center = base_center + offset
        attitude = self.model_screen_rotation()
        if attitude:
            painter.save()
            painter.translate(self._projected_center)
            painter.rotate(attitude)
            painter.translate(-base_center)
            painter.drawPixmap(0, 0, layer)
            painter.restore()
        else:
            painter.drawPixmap(int(offset.x()), int(offset.y()), layer)
        self._draw_guides(painter, base_center, offset, attitude)
        self._draw_callouts(painter, base_center, offset, attitude)
        if not has_model:
            painter.setPen(QColor("#496779"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Build and save an aircraft in Learner Setup to see it here")
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        painter.setPen(QColor("#48677b"))
        painter.drawText(16, 24, self.caption)
        self.paint_overlay(painter)

    def paint_overlay(self, painter):
        """Hook for activity-specific annotations."""


# Shared styling keeps independently constructed learner tabs visually
# consistent without changing the application's Advanced Mode stylesheet.
LEARNER_QSS = """
QWidget[learnerPage="true"] { background: #071927; color: #edf6fc; }
QFrame#heroCard, QFrame#surfaceCard, QGroupBox {
    background: #0c2233; border: 1px solid #28475d; border-radius: 9px;
}
QGroupBox { margin-top: 14px; padding: 18px 12px 12px 12px; font-weight: 600; color: #dcebf5; }
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 5px; color: #91aabd; }
QLabel#pageTitle { color: #f4f9fc; font-size: 25px; font-weight: 700; }
QLabel#eyebrow { color: #58c5ef; font-size: 11px; font-weight: 700; }
QLabel#subtitle { color: #a9c0d0; font-size: 14px; }
QLabel#metricValue { color: #f4f9fc; font-size: 21px; font-weight: 700; }
QLabel#muted { color: #9db5c6; }
QPushButton { min-height: 32px; padding: 2px 15px; border: 1px solid #547086; border-radius: 6px; }
QPushButton[primary="true"] { background: #1784b8; border-color: #32a6d9; color: white; font-weight: 700; }
QPushButton:hover { border-color: #63c8ef; }
QLineEdit, QSpinBox, QDoubleSpinBox {
    min-height: 31px; background: #263548; border: 1px solid #38556a;
    border-radius: 5px; padding: 0 8px;
}
QListWidget, QTableWidget { background: #091d2c; border: 1px solid #28475d; border-radius: 7px; gridline-color: #203c50; }
QHeaderView::section { background: #142b3d; color: #bcd0dd; border: none; border-right: 1px solid #28475d; padding: 8px; font-weight: 600; }
"""


def style_learner_page(widget):
    """Mark a widget as a learner page and apply the scoped learner stylesheet."""
    widget.setProperty("learnerPage", True)
    widget.setStyleSheet(LEARNER_QSS)
