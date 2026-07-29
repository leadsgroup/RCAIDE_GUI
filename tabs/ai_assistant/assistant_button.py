"""Hover-reveal launcher for the native RCAIDE AI drawer."""

from __future__ import annotations

import math
from pathlib import Path

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QPushButton


# Resolve the shared LEADS asset relative to the repository, not the launch cwd.
_ROOT = Path(__file__).resolve().parents[2]
_LEADS_LOGO = _ROOT / "app_data" / "images" / "leads_logo.png"


class AIAssistantButton(QPushButton):
    """Logo-only edge button that reveals its caption on hover."""

    # main.py listens for width changes so the floating button stays edge-aligned.
    widthChanged = pyqtSignal()
    COLLAPSED_WIDTH = 58
    EXPANDED_WIDTH = 214

    def __init__(self, parent=None):
        super().__init__(parent)
        # Animation values are normalized from 0.0 (idle) to 1.0 (fully shown).
        self._reveal_progress = 0.0
        self._launch_progress = 0.0
        self._drawer_open = False
        self._logo = QPixmap(str(_LEADS_LOGO))
        self.setFixedSize(self.COLLAPSED_WIDTH, 58)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Open the RCAIDE AI Agent")
        self.setAccessibleName("Open RCAIDE AI Agent")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFlat(True)

        # Hovering expands the button and fades in its text label.
        self._hover_animation = QPropertyAnimation(self, b"revealProgress", self)
        self._hover_animation.setDuration(230)
        self._hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Clicking produces a short pulse without changing the drawer animation.
        self._launch_animation = QPropertyAnimation(self, b"launchProgress", self)
        self._launch_animation.setDuration(500)
        self._launch_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._launch_animation.setStartValue(0.0)
        self._launch_animation.setKeyValueAt(0.4, 1.0)
        self._launch_animation.setEndValue(0.0)

    def sizeHint(self):
        """Advertise the compact size used when the caption is hidden."""
        return QSize(self.COLLAPSED_WIDTH, 58)

    def play_launch_animation(self):
        """Restart the visual pulse shown when the drawer begins opening."""
        self._launch_animation.stop()
        self._launch_animation.start()

    def set_expanded(self, expanded: bool):
        """Reflect drawer visibility in the tooltip and status indicator."""
        self._drawer_open = expanded
        self.setToolTip(
            "Collapse the RCAIDE AI Agent" if expanded
            else "Open the RCAIDE AI Agent"
        )
        self.update()

    def _animate_hover(self, target: float):
        """Animate smoothly from the current width to the requested state."""
        self._hover_animation.stop()
        self._hover_animation.setStartValue(self._reveal_progress)
        self._hover_animation.setEndValue(target)
        self._hover_animation.start()

    def enterEvent(self, event):
        # Reveal the caption when the pointer enters the button.
        self._animate_hover(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        # Collapse back to the logo-only launcher when the pointer leaves.
        self._animate_hover(0.0)
        super().leaveEvent(event)

    def _get_reveal_progress(self):
        return self._reveal_progress

    def _set_reveal_progress(self, value):
        # Interpolate the live width from the normalized animation value.
        self._reveal_progress = float(value)
        width = round(
            self.COLLAPSED_WIDTH
            + (self.EXPANDED_WIDTH - self.COLLAPSED_WIDTH) * self._reveal_progress
        )
        self.setFixedWidth(width)
        # Reposition the floating control after every animation frame.
        self.widthChanged.emit()
        self.update()

    # QPropertyAnimation requires Qt properties rather than plain attributes.
    revealProgress = pyqtProperty(
        float, fget=_get_reveal_progress, fset=_set_reveal_progress
    )

    def _get_launch_progress(self):
        return self._launch_progress

    def _set_launch_progress(self, value):
        # Repainting changes glow intensity and logo scale during the pulse.
        self._launch_progress = float(value)
        self.update()

    launchProgress = pyqtProperty(
        float, fget=_get_launch_progress, fset=_set_launch_progress
    )

    def paintEvent(self, _event):
        """Draw the panel, logo, caption, drawer state, and focus outline."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = QRectF(self.rect()).adjusted(2, 2, -2, -2)

        # Base pill-shaped panel; hover and click both strengthen its border glow.
        panel = QLinearGradient(bounds.topLeft(), bounds.bottomLeft())
        panel.setColorAt(0.0, QColor("#0d3546"))
        panel.setColorAt(1.0, QColor("#061722"))
        glow = 95 + int(95 * self._reveal_progress) + int(50 * self._launch_progress)
        painter.setPen(QPen(QColor(43, 202, 190, min(glow, 230)), 2))
        painter.setBrush(panel)
        painter.drawRoundedRect(bounds, 27, 27)

        # The exact LEADS logo remains visible while the caption stays hidden.
        logo_width = 48 * (1.0 + 0.08 * math.sin(math.pi * self._launch_progress))
        aspect = self._logo.width() / self._logo.height() if self._logo.height() else 1.0
        logo_height = logo_width / aspect
        logo_rect = QRectF(
            self.width() - 53 - (logo_width - 48) / 2,
            (self.height() - logo_height) / 2,
            logo_width,
            logo_height,
        )
        if not self._logo.isNull():
            painter.drawPixmap(logo_rect, self._logo, QRectF(self._logo.rect()))

        # Fade text in only after expansion begins to avoid clipped characters.
        if self._reveal_progress > 0.03:
            painter.save()
            painter.setOpacity(self._reveal_progress)
            text_right = self.width() - 57
            title_font = QFont(self.font())
            title_font.setBold(True)
            title_font.setPixelSize(13)
            painter.setFont(title_font)
            painter.setPen(QColor("#e8fbff"))
            painter.drawText(
                QRectF(15, 8, max(0, text_right - 15), 23),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                "RCAIDE AI AGENT",
            )

            caption_font = QFont(self.font())
            caption_font.setPixelSize(9)
            painter.setFont(caption_font)
            painter.setPen(QColor("#79cfcc"))
            painter.drawText(
                QRectF(15, 29, max(0, text_right - 15), 16),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                "Ask · analyze · debug",
            )
            painter.restore()

        # Small state indicator; the logo itself remains uncluttered.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#63df9d") if self._drawer_open else QColor("#58aeca"))
        painter.drawEllipse(QRectF(self.width() - 12, 8, 5, 5))

        # Keyboard users receive the same visible focus feedback as other controls.
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#dfffff"), 1, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(bounds.adjusted(3, 3, -3, -3), 24, 24)
