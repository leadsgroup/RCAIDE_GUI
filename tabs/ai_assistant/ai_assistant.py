"""Native, context-aware RCAIDE AI assistant dock."""

from __future__ import annotations

import json
import os
import traceback

from PyQt6.QtCore import QObject, QSize, QThread, QTimer, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QIcon, QKeyEvent, QPixmap
from PyQt6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import rcaide_io
from agent_service.context import build_agent_context
from agent_service.provider import ProviderError, generate_reply

from .chat_widgets import (
    AttachmentError,
    ILLINOIS_LOGO_PATH,
    LEADS_LOGO_PATH,
    MessageCard,
    ThinkingCard,
    prepare_attachment,
)


class _MessageInput(QPlainTextEdit):
    """Composer that sends on Enter and inserts a newline on Shift+Enter."""

    submitted = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent):
        # Emit a signal instead of calling the dock directly so the widget stays reusable.
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (
            event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self.submitted.emit()
            return
        super().keyPressEvent(event)


class _AssistantWorker(QObject):
    """Run the blocking provider request outside the Qt interface thread."""

    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, messages, context, configuration):
        super().__init__()
        self.messages = messages
        self.context = context
        self.configuration = configuration

    def run(self):
        """Send one request and translate completion/failure into Qt signals."""
        try:
            self.finished.emit(generate_reply(self.messages, self.context, self.configuration))
        except ProviderError as exc:
            self.failed.emit(str(exc))
        except Exception:
            self.failed.emit(traceback.format_exc())


class AIAssistantDock(QDockWidget):
    """ChatGPT-style drawer that reads the current in-memory RCAIDE project."""

    def __init__(self, parent=None):
        super().__init__("RCAIDE AI Agent", parent)
        self.setObjectName("rcaideAiAssistantDock")
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.setMinimumWidth(480)
        self.resize(560, 720)

        # Conversation history is model-facing; attachments belong only to the
        # next unsent message. Remaining fields track asynchronous UI objects.
        self.messages: list[dict[str, object]] = []
        self.attachments: list[dict] = []
        self._thread = None
        self._worker = None
        self._thinking_card = None
        self._typing_timer = None
        self._typing_card = None

        # Build one self-contained panel so the drawer can move between dock areas.
        panel = QWidget()
        panel.setObjectName("assistantPanel")
        panel.setStyleSheet("""
            QWidget#assistantPanel { background-color: #06131d; }
            QLabel { color: #d9e8ee; }
            QPlainTextEdit {
                color: #e1edf2;
                background: transparent;
                border: none;
                padding: 7px 3px;
                selection-background-color: #256780;
            }
            QPushButton {
                color: #dcebf1;
                background-color: #102a38;
                border: 1px solid #285267;
                border-radius: 8px;
                padding: 7px 10px;
            }
            QPushButton:hover { background-color: #17445a; border-color: #3b7890; }
            QPushButton:disabled { color: #647984; border-color: #233b47; }
            QPushButton#sendButton {
                color: #031216;
                background-color: #65d9d0;
                border-color: #65d9d0;
                font-weight: 800;
            }
            QPushButton#clearButton, QPushButton#attachButton {
                background: transparent;
                border-color: #274857;
            }
            QPushButton#illinoisCreditLogo {
                background: #13294b;
                border: 1px solid #344f73;
                border-radius: 7px;
                padding: 0;
            }
            QPushButton#illinoisCreditLogo:hover { border-color: #ff5f05; }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 10)
        layout.setSpacing(9)

        # Header: LEADS identity, assistant title, and conversation reset.
        header = QFrame()
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(2, 0, 2, 0)
        logo = QLabel()
        logo.setFixedSize(46, 38)
        logo.setPixmap(
            QPixmap(str(LEADS_LOGO_PATH)).scaled(
                44,
                36,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        header_row.addWidget(logo)
        heading = QVBoxLayout()
        heading.setSpacing(0)
        title = QLabel("RCAIDE AI Agent")
        title.setStyleSheet("font-size:17px; font-weight:800; color:#73d9d0;")
        subtitle = QLabel("Aircraft design copilot")
        subtitle.setStyleSheet("font-size:10px; color:#7f9ba8;")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header_row.addLayout(heading, 1)
        clear_button = QPushButton("Clear")
        clear_button.setObjectName("clearButton")
        clear_button.clicked.connect(self.clear_chat)
        header_row.addWidget(clear_button)
        layout.addWidget(header)

        # This compact label shows which project state the next prompt will read.
        self.context_label = QLabel()
        self.context_label.setWordWrap(True)
        self.context_label.setStyleSheet("color:#86a1ae; font-size:10px; padding:0 3px;")
        layout.addWidget(self.context_label)

        # Quick actions are normal prompts, so they use the same request pipeline.
        quick_row = QHBoxLayout()
        quick_row.setSpacing(6)
        for text, prompt in (
            ("Check setup", "Inspect my current RCAIDE setup and list the most important issues."),
            ("Explain field", "Help me understand a parameter in my current aircraft setup."),
            ("Debug run", "Diagnose the latest mission failure or unexpected result."),
        ):
            button = QPushButton(text)
            button.clicked.connect(lambda _, value=prompt: self.ask(value))
            quick_row.addWidget(button)
        layout.addLayout(quick_row)

        # Message cards live in a vertically scrolling, transparent host widget.
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_scroll.setStyleSheet("QScrollArea { background:transparent; border:none; }")
        self.chat_host = QWidget()
        self.chat_host.setStyleSheet("background:transparent;")
        self.chat_layout = QVBoxLayout(self.chat_host)
        self.chat_layout.setContentsMargins(2, 4, 4, 4)
        self.chat_layout.setSpacing(10)
        self.chat_layout.addStretch(1)
        self.chat_scroll.setWidget(self.chat_host)
        layout.addWidget(self.chat_scroll, 1)

        # Composer contains attachment chips, multiline input, and send actions.
        composer = QFrame()
        composer.setObjectName("composer")
        composer.setStyleSheet("""
            QFrame#composer {
                background:#091c27;
                border:1px solid #285064;
                border-radius:13px;
            }
        """)
        composer_layout = QVBoxLayout(composer)
        composer_layout.setContentsMargins(8, 5, 8, 7)
        composer_layout.setSpacing(3)
        self.attachment_row = QHBoxLayout()
        self.attachment_row.setSpacing(5)
        composer_layout.addLayout(self.attachment_row)

        self.input = _MessageInput()
        self.input.setPlaceholderText(
            "Message RCAIDE AI...\nEnter sends - Shift+Enter adds a line"
        )
        self.input.setMaximumHeight(105)
        self.input.setMinimumHeight(58)
        self.input.submitted.connect(self.send_current_message)
        composer_layout.addWidget(self.input)

        action_row = QHBoxLayout()
        self.attach_button = QPushButton("+ Attach")
        self.attach_button.setObjectName("attachButton")
        self.attach_button.setToolTip("Attach text, data, source code, logs, or an image")
        self.attach_button.clicked.connect(self.choose_attachments)
        action_row.addWidget(self.attach_button)
        attachment_hint = QLabel("Images, CSV, JSON, text, code")
        attachment_hint.setStyleSheet("color:#6f8995; font-size:9px;")
        action_row.addWidget(attachment_hint)
        action_row.addStretch()
        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("sendButton")
        self.send_button.clicked.connect(self.send_current_message)
        action_row.addWidget(self.send_button)
        composer_layout.addLayout(action_row)
        layout.addWidget(composer)

        self.status_label = QLabel("AI suggestions can be inaccurate; verify engineering decisions.")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color:#667f8b; font-size:9px; padding:0 3px;")
        layout.addWidget(self.status_label)

        # Keep official institutional attribution visible and directly linked.
        credits = QFrame()
        credits.setObjectName("assistantCredits")
        credits.setStyleSheet("""
            QFrame#assistantCredits {
                background:#081a25;
                border:1px solid #1d3b4a;
                border-radius:8px;
            }
        """)
        credit_row = QHBoxLayout(credits)
        credit_row.setContentsMargins(7, 5, 8, 5)
        credit_row.setSpacing(8)
        illinois_logo = QPushButton()
        illinois_logo.setObjectName("illinoisCreditLogo")
        illinois_logo.setFixedSize(38, 38)
        illinois_logo.setIcon(QIcon(str(ILLINOIS_LOGO_PATH)))
        illinois_logo.setIconSize(QSize(34, 34))
        illinois_logo.setToolTip("Open The Grainger College of Engineering")
        illinois_logo.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://grainger.illinois.edu"))
        )
        credit_row.addWidget(illinois_logo)
        credit_text = QLabel(
            'Developed at <a style="color:#ff8a3d; text-decoration:none;" '
            'href="https://grainger.illinois.edu">UIUC</a><br>'
            'Directed by <a style="color:#79d8e5; text-decoration:none;" '
            'href="https://www.leadsresearchgroup.com">L.E.A.D.S.</a>'
        )
        credit_text.setOpenExternalLinks(True)
        credit_text.setToolTip("Open official University of Illinois pages")
        credit_text.setStyleSheet(
            "color:#7893a0; font-size:9px; background:transparent; border:none;"
        )
        credit_row.addWidget(credit_text, 1)
        layout.addWidget(credits)

        self.setWidget(panel)
        self.visibilityChanged.connect(self._on_visibility_changed)
        self.refresh_context_label()
        self._show_welcome()

    def _show_welcome(self):
        """Reset the visible transcript to the initial scoped welcome message."""
        self._clear_cards()
        self._add_card(MessageCard(
            "assistant",
            "### Hey, welcome to RCAIDE.\n\n"
            "I am your personal AI chatbot, here to help you navigate the application. "
            "Feel free to ask me anything related to **aircraft design, engineering, "
            "RCAIDE, or the GUI**.",
        ))

    def _on_visibility_changed(self, visible: bool):
        """Refresh state and focus the composer whenever the drawer opens."""
        if visible:
            self.refresh_context_label()
            self.input.setFocus()

    def refresh_context_label(self):
        """Show a lightweight overview without building the full model context."""
        try:
            project = json.loads(rcaide_io.write_to_json())
            vehicle = project.get("rcaide_vehicle", {})
            tag = vehicle.get("tag", "Untitled vehicle") if isinstance(vehicle, dict) else "Vehicle"
            analyses = len(project.get("analysis_data", []))
            missions = len(project.get("mission_data", []))
            result_status = (
                "results ready" if getattr(rcaide_io, "rcaide_results", None) is not None
                else "no results"
            )
            self.context_label.setText(
                f"Live context: {tag}  |  {analyses} analyses  |  "
                f"{missions} missions  |  {result_status}"
            )
        except Exception as exc:
            self.context_label.setText(f"Current GUI context could not be read: {exc}")

    def _current_context(self, query: str = ""):
        """Capture authoritative in-memory RCAIDE state for one request."""
        # write_to_json provides the current editable project; runtime result and
        # error objects are read separately because they are not saved in JSON.
        project = json.loads(rcaide_io.write_to_json())
        error_trace = getattr(rcaide_io, "last_agent_error", "")
        results = getattr(rcaide_io, "rcaide_results", None)
        performance_result = getattr(rcaide_io, "last_performance_result", None)
        # The context service sanitizes, ranks, and bounds these large objects.
        context = build_agent_context(
            project,
            error_trace,
            results=results,
            performance_result=performance_result,
            query=query,
        )
        # Add desktop-only runtime facts after the serializable project summary.
        segments = getattr(results, "segments", None) if results is not None else None
        window = self.parent()
        tabs = getattr(window, "tabs", None)
        active_tab = ""
        if tabs is not None and tabs.currentIndex() >= 0:
            active_tab = tabs.tabText(tabs.currentIndex())
        context["runtime"] = {
            "active_gui_tab": active_tab,
            "current_project_file": os.path.basename(
                getattr(rcaide_io, "current_file_path", "")
            ),
            "mission_results_available": results is not None,
            "mission_result_segment_count": len(segments) if segments is not None else 0,
            "performance_result_available": performance_result is not None,
            "performance_result_label": getattr(rcaide_io, "last_performance_label", ""),
            "mission_run_status_is_authoritative": True,
        }
        if results is not None:
            # Explicit run-state instructions prevent the model from confusing a
            # configured mission with a completed mission result object.
            mission_summary = context.get("mission_results", {})
            context["runtime"]["mission_run_instruction"] = (
                "A completed mission result object is loaded. Do not say the mission has "
                "not been run. Answer result questions from mission_results."
            )
            context["runtime"]["mission_result_series_available"] = any(
                segment.get("series")
                for segment in mission_summary.get("segments", [])
                if isinstance(segment, dict)
            )
        return context

    def ask(self, prompt: str):
        """Submit a predefined quick-action prompt through the normal composer."""
        self.input.setPlainText(prompt)
        self.send_current_message()

    def choose_attachments(self):
        """Select and preprocess up to three supported files for the next turn."""
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Attach files for RCAIDE AI",
            "",
            "Supported files (*.txt *.md *.json *.csv *.tsv *.log *.py *.yaml *.yml "
            "*.xml *.ini *.toml *.dat *.png *.jpg *.jpeg *.webp *.bmp);;All files (*)",
        )
        for path in paths:
            if len(self.attachments) >= 3:
                QMessageBox.information(self, "Attachment limit", "Attach up to three files per message.")
                break
            try:
                self.attachments.append(prepare_attachment(path))
            except (AttachmentError, OSError) as exc:
                QMessageBox.warning(self, "Could not attach file", str(exc))
        self._refresh_attachment_chips()

    def _refresh_attachment_chips(self):
        """Rebuild removable attachment labels from the pending file list."""
        # Qt widgets are deleted later to avoid destroying them during a signal.
        while self.attachment_row.count():
            item = self.attachment_row.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for index, attachment in enumerate(self.attachments):
            chip = QPushButton(f"{attachment['name']}  x")
            chip.setToolTip("Remove attachment")
            chip.setStyleSheet(
                "background:#123644; color:#9ddde1; border:1px solid #2b6873; "
                "border-radius:7px; padding:4px 7px; font-size:9px;"
            )
            chip.clicked.connect(lambda _, value=index: self._remove_attachment(value))
            self.attachment_row.addWidget(chip)
        self.attachment_row.addStretch(1)

    def _remove_attachment(self, index: int):
        """Remove one pending attachment and redraw its chips."""
        if 0 <= index < len(self.attachments):
            self.attachments.pop(index)
            self._refresh_attachment_chips()

    @staticmethod
    def _model_content(prompt: str, attachments: list[dict]):
        """Combine prompt text, extracted file text, and optional image blocks."""
        text_parts = [prompt or "Please analyze the attached file(s)."]
        image_blocks = []
        for attachment in attachments:
            text_parts.append(attachment["prompt_text"])
            if attachment.get("image_block"):
                image_blocks.append(attachment["image_block"])
        text = "\n\n".join(text_parts)
        # The provider accepts a block list only when the turn contains images.
        if image_blocks:
            return [{"type": "text", "text": text}, *image_blocks]
        return text

    def send_current_message(self):
        """Capture the turn, build live context, and start the provider worker."""
        content = self.input.toPlainText().strip()
        # Prevent empty prompts, duplicate requests, and overlapping animations.
        if (not content and not self.attachments) or self._thread is not None or self._typing_timer is not None:
            return

        # Snapshot pending files before clearing the composer for immediate feedback.
        selected_attachments = list(self.attachments)
        attachment_names = [item["name"] for item in selected_attachments]
        display_content = content or "*Please analyze the attached file(s).*"
        self.input.clear()
        self.attachments.clear()
        self._refresh_attachment_chips()

        # Model history may contain extracted data/images; the visible card shows
        # only the user's prompt and safe attachment names.
        model_content = self._model_content(content, selected_attachments)
        self.messages.append({"role": "user", "content": model_content})
        self._add_card(MessageCard("user", display_content, attachment_names))

        # Attachment names help the context builder rank related project fields.
        context_query = " ".join([content, *attachment_names]).strip()
        try:
            context = self._current_context(context_query)
        except Exception as exc:
            self._add_card(MessageCard(
                "assistant", f"I could not read the current GUI state: {exc}", error=True
            ))
            return

        # urllib is synchronous, so move it to QThread to keep PyQt responsive.
        self._set_busy(True)
        self._thread = QThread(self)
        self._worker = _AssistantWorker(list(self.messages), context, {})
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_reply)
        self._worker.failed.connect(self._on_failure)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_worker)
        self._thread.start()

    def _on_reply(self, reply: str):
        """Store a successful answer and reveal it progressively."""
        self.messages.append({"role": "assistant", "content": reply})
        self._hide_thinking()
        self._start_typewriter(reply)
        self.refresh_context_label()

    def _on_failure(self, error: str):
        """Render provider failures as assistant error cards."""
        self._hide_thinking()
        self._add_card(MessageCard("assistant", error, error=True))
        self._set_busy(False)

    def _cleanup_worker(self):
        """Release QObject/QThread instances after their event loop exits."""
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
        if self._thread is not None:
            self._thread.deleteLater()
            self._thread = None

    def _set_busy(self, busy: bool):
        """Enable or disable composer controls and update request feedback."""
        self.send_button.setEnabled(not busy)
        self.attach_button.setEnabled(not busy)
        self.input.setEnabled(not busy)
        if busy:
            self._show_thinking()
        else:
            self._hide_thinking()
        self.status_label.setText(
            "RCAIDE AI is reading the live project..." if busy
            else "AI suggestions can be inaccurate; verify engineering decisions."
        )

    def _show_thinking(self):
        """Display one animated thinking card while awaiting the backend."""
        self._hide_thinking()
        self._thinking_card = ThinkingCard()
        self._add_card(self._thinking_card)

    def _hide_thinking(self):
        """Stop and remove the current thinking animation if present."""
        if self._thinking_card is not None:
            self._thinking_card.stop()
            self.chat_layout.removeWidget(self._thinking_card)
            self._thinking_card.deleteLater()
            self._thinking_card = None

    def _start_typewriter(self, reply: str):
        """Reveal a complete backend response in smooth Markdown chunks."""
        self._typing_card = MessageCard("assistant", "")
        self._add_card(self._typing_card)
        state = {"position": 0}
        # Longer answers reveal more characters per tick to limit total duration.
        chunk = max(2, min(16, max(1, len(reply) // 180)))
        timer = QTimer(self)
        timer.setInterval(14)

        def reveal():
            # Re-render partial Markdown and keep the newest content visible.
            state["position"] = min(len(reply), state["position"] + chunk)
            self._typing_card.set_markdown(reply[:state["position"]])
            self._scroll_bottom()
            if state["position"] >= len(reply):
                timer.stop()
                timer.deleteLater()
                self._typing_timer = None
                self._typing_card = None
                self._set_busy(False)
                self.input.setFocus()

        timer.timeout.connect(reveal)
        self._typing_timer = timer
        timer.start()

    def _add_card(self, card: QWidget):
        """Insert a message before the stretch item at the transcript bottom."""
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, card)
        self._scroll_bottom()

    def _scroll_bottom(self):
        """Scroll after Qt completes the pending message-card layout."""
        QTimer.singleShot(
            0,
            lambda: self.chat_scroll.verticalScrollBar().setValue(
                self.chat_scroll.verticalScrollBar().maximum()
            ),
        )

    def _clear_cards(self):
        """Delete visible cards and stop any animation owned by them."""
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                if isinstance(widget, ThinkingCard):
                    widget.stop()
                widget.deleteLater()
        self._thinking_card = None

    def clear_chat(self):
        """Clear history and pending files only when no request is active."""
        if self._thread is not None or self._typing_timer is not None:
            return
        self.messages.clear()
        self.attachments.clear()
        self._refresh_attachment_chips()
        self._show_welcome()
