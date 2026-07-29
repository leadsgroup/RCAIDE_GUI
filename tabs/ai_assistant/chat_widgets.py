"""Reusable ChatGPT-style widgets and attachment preparation."""

from __future__ import annotations

import base64
import math
from pathlib import Path

from PyQt6.QtCore import QBuffer, QIODevice, QTimer, Qt
from PyQt6.QtGui import (
    QFont,
    QImage,
    QPixmap,
    QTextBlockFormat,
    QTextCursor,
    QTextDocument,
    QTextOption,
)
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


# Resolve shared branding assets independently of the process working directory.
_ROOT = Path(__file__).resolve().parents[2]
LEADS_LOGO_PATH = _ROOT / "app_data" / "images" / "leads_logo.png"
ILLINOIS_LOGO_PATH = _ROOT / "app_data" / "images" / "illinois_block_i.png"
# Only formats that can be safely extracted or encoded by this module are listed.
TEXT_EXTENSIONS = {
    ".txt", ".md", ".json", ".csv", ".tsv", ".log", ".py", ".yaml", ".yml",
    ".xml", ".ini", ".toml", ".dat",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
# Separate disk, extracted-text, and encoded-image limits bound request size.
MAX_TEXT_FILE_BYTES = 1_000_000
MAX_TEXT_CHARACTERS = 12_000
MAX_IMAGE_BYTES = 1_500_000


class AttachmentError(ValueError):
    """Report attachment validation failures with user-readable messages."""

    pass


def _encode_image(path: Path) -> dict:
    """Resize and encode an image as a model-compatible data URL block."""
    # Reject very large source files before asking Qt to decode them.
    if path.stat().st_size > 12_000_000:
        raise AttachmentError("Images must be smaller than 12 MB.")
    image = QImage(str(path))
    if image.isNull():
        raise AttachmentError(f"Could not read image: {path.name}")
    # Downscale while preserving aspect ratio to control tokens and memory.
    if image.width() > 1280 or image.height() > 1280:
        image = image.scaled(
            1280,
            1280,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def encoded(fmt: bytes, quality: int = -1) -> bytes:
        """Encode the in-memory QImage without creating a temporary file."""
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, fmt.decode("ascii"), quality)
        return bytes(buffer.data())

    # Prefer lossless PNG, then use JPEG compression if the payload is too large.
    payload = encoded(b"PNG")
    mime = "image/png"
    if len(payload) > MAX_IMAGE_BYTES:
        payload = encoded(b"JPEG", 82)
        mime = "image/jpeg"
    if len(payload) > MAX_IMAGE_BYTES:
        raise AttachmentError("The compressed image is still too large to attach.")
    # Embedding avoids sending local paths that the hosted service cannot access.
    data_url = f"data:{mime};base64,{base64.b64encode(payload).decode('ascii')}"
    return {
        "name": path.name,
        "kind": "image",
        "prompt_text": f"Attached image: {path.name}",
        "image_block": {
            "type": "image_url",
            "image_url": {"url": data_url, "detail": "auto"},
        },
    }


def _read_text(path: Path) -> dict:
    """Read a bounded text/data file into a fenced model prompt section."""
    size = path.stat().st_size
    if size > MAX_TEXT_FILE_BYTES:
        raise AttachmentError("Text and data files must be smaller than 1 MB.")
    raw = path.read_bytes()
    # Replace invalid UTF-8 bytes rather than failing the complete user message.
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")
    # Keep the beginning of the file and tell the model when content was omitted.
    truncated = len(text) > MAX_TEXT_CHARACTERS
    text = text[:MAX_TEXT_CHARACTERS]
    note = "\n[File truncated for the model.]" if truncated else ""
    return {
        "name": path.name,
        "kind": "text",
        "prompt_text": (
            f"Attached file `{path.name}`:\n\n"
            f"```{path.suffix.lstrip('.')}\n{text}\n```{note}"
        ),
        "image_block": None,
    }


def prepare_attachment(file_path: str) -> dict:
    """Validate a selected path and route it to text or image preparation."""
    path = Path(file_path)
    if not path.is_file():
        raise AttachmentError("The selected attachment does not exist.")
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return _encode_image(path)
    if suffix in TEXT_EXTENSIONS:
        return _read_text(path)
    # PDF parsing is intentionally not implied when no extraction library exists.
    if suffix == ".pdf":
        raise AttachmentError(
            "PDF extraction is not installed. Export the relevant page as an image "
            "or attach the text instead."
        )
    raise AttachmentError(
        "Unsupported file type. Attach JSON, CSV, text, source, log, YAML, or an image."
    )


class AutoHeightMarkdown(QTextBrowser):
    """Read-only Markdown view that grows inside the conversation scroll area."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # The outer conversation provides scrolling, so each message body grows
        # to its document height and disables its own scroll bars.
        self.setOpenExternalLinks(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.document().setDocumentMargin(2)
        # Wrap long engineering paths and values instead of widening the drawer.
        text_options = self.document().defaultTextOption()
        text_options.setAlignment(Qt.AlignmentFlag.AlignLeft)
        text_options.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.document().setDefaultTextOption(text_options)
        body_font = QFont("Segoe UI")
        body_font.setPointSizeF(10.5)
        self.document().setDefaultFont(body_font)
        # GitHub-style Markdown is themed to match the RCAIDE dark interface.
        self.document().setDefaultStyleSheet("""
            body { color: #dce9ef; font-family: 'Segoe UI'; font-size: 11pt; text-align: left; }
            p { margin-top: 2px; margin-bottom: 11px; line-height: 150%; text-align: left; }
            h1 { color: #8de4dc; font-size: 18pt; margin-top: 8px; margin-bottom: 10px; }
            h2 { color: #8de4dc; font-size: 15pt; margin-top: 8px; margin-bottom: 9px; }
            h3 { color: #9edce8; font-size: 13pt; margin-top: 7px; margin-bottom: 8px; }
            h4 { color: #a9d9e5; font-size: 11.5pt; margin-top: 6px; margin-bottom: 6px; }
            ul, ol { margin-top: 5px; margin-bottom: 12px; margin-left: 12px; padding-left: 10px; }
            li { margin-bottom: 6px; line-height: 145%; text-align: left; }
            pre { background-color: #051019; color: #c9e6ef; border: 1px solid #244653;
                  padding: 9px; margin-top: 6px; margin-bottom: 10px; }
            code { color: #9be3d8; background-color: #0b222d; }
            blockquote { color: #a8bec8; border-left: 3px solid #3b7d85;
                         margin-left: 4px; padding-left: 10px; }
            table { border-collapse: collapse; margin-top: 6px; margin-bottom: 10px; }
            th { color: #8de4dc; background-color: #102b37; font-weight: 700;
                 border: 1px solid #315365; padding: 6px; }
            td { border: 1px solid #294957; padding: 6px; }
            a { color: #6fc8ee; text-decoration: none; }
        """)
        # Recalculate widget height whenever Markdown changes the document layout.
        self.document().documentLayout().documentSizeChanged.connect(
            lambda _size: self._sync_height()
        )
        self.setStyleSheet("""
            QTextBrowser {
                background: transparent;
                color: #dce9ef;
                border: none;
                padding: 1px;
                font-family: "Segoe UI";
                font-size: 13px;
                selection-background-color: #256780;
            }
        """)

    def set_markdown(self, markdown: str):
        """Render GitHub-flavored Markdown and resize to fit its content."""
        self.document().setMarkdown(markdown, QTextDocument.MarkdownFeature.MarkdownDialectGitHub)
        self._apply_readable_block_spacing()
        QTimer.singleShot(0, self._sync_height)

    def _apply_readable_block_spacing(self):
        """Qt Markdown ignores several CSS list margins; apply them to blocks."""
        block = self.document().begin()
        while block.isValid():
            block_format = block.blockFormat()
            block_format.setAlignment(Qt.AlignmentFlag.AlignLeft)
            block_format.setLineHeight(
                138,
                QTextBlockFormat.LineHeightTypes.ProportionalHeight.value,
            )
            if block_format.headingLevel() > 0:
                block_format.setTopMargin(8)
                block_format.setBottomMargin(7)
            elif block.textList() is not None:
                block_format.setTopMargin(1)
                block_format.setBottomMargin(4)
            elif block.text().strip():
                block_format.setBottomMargin(9)
            cursor = QTextCursor(block)
            cursor.setBlockFormat(block_format)
            block = block.next()

    def resizeEvent(self, event):
        # Reflow Markdown to the newly available message-card width.
        super().resizeEvent(event)
        self.document().setTextWidth(max(40, self.viewport().width()))
        self._sync_height()

    def _sync_height(self):
        """Match widget height to the complete rendered Markdown document."""
        height = max(24, math.ceil(self.document().size().height()) + 4)
        if self.height() != height:
            self.setFixedHeight(height)


class MessageCard(QWidget):
    """One assistant or user message with avatar, label, attachments, and Markdown."""

    def __init__(
        self,
        role: str,
        markdown: str = "",
        attachment_names: list[str] | None = None,
        error: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.role = role
        # User, assistant, and error cards share structure but use distinct colors.
        self.setObjectName("assistantMessage" if role == "assistant" else "userMessage")
        background = "#081a25" if role == "assistant" else "#0d2735"
        border = "#183b4b" if role == "assistant" else "#245269"
        if error:
            background, border = "#29171d", "#7d3544"
        self.setStyleSheet(f"""
            QWidget#{self.objectName()} {{
                background-color: {background};
                border: 1px solid {border};
                border-radius: 12px;
            }}
            QLabel {{ background: transparent; border: none; }}
        """)

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 10, 14, 11)
        row.setSpacing(11)

        # Assistant messages use the LEADS logo; user messages use a compact badge.
        avatar = QLabel()
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if role == "assistant":
            pixmap = QPixmap(str(LEADS_LOGO_PATH)).scaled(
                34, 28,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            avatar.setPixmap(pixmap)
            avatar.setStyleSheet("background:#07131c; border:1px solid #2b857f; border-radius:18px;")
            speaker = "RCAIDE AI"
        else:
            avatar.setText("YOU")
            avatar.setStyleSheet(
                "background:#174d64; color:#dff8ff; border:1px solid #3d829a; "
                "border-radius:18px; font-size:9px; font-weight:800;"
            )
            speaker = "You"
        row.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)

        body = QVBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(3)

        name = QLabel("Assistant error" if error else speaker)
        name.setStyleSheet(
            "color:#ff9caa; font-size:11px; font-weight:800;" if error else
            ("color:#73d9d0; font-size:11px; font-weight:800;" if role == "assistant" else
             "color:#a9d9ea; font-size:11px; font-weight:800;")
        )
        body.addWidget(name)

        # Display filenames only; extracted contents remain in model history.
        if attachment_names:
            attachments = QLabel("  |  ".join(f"Attached: {name}" for name in attachment_names))
            attachments.setWordWrap(True)
            attachments.setStyleSheet(
                "color:#83c9d0; background:#0b202b; border:1px solid #23505d; "
                "border-radius:7px; padding:5px 7px; font-size:10px;"
            )
            body.addWidget(attachments)

        # The same Markdown widget supports normal replies and typewriter updates.
        self.content = AutoHeightMarkdown()
        body.addWidget(self.content)
        row.addLayout(body, 1)
        self.set_markdown(markdown)

    def set_markdown(self, markdown: str):
        """Replace this card's rendered message content."""
        self.content.set_markdown(markdown)


class ThinkingCard(MessageCard):
    """Temporary assistant card with a timer-driven dot animation."""

    def __init__(self, parent=None):
        super().__init__("assistant", "Thinking", parent=parent)
        self._frame = 0
        self._timer = QTimer(self)
        self._timer.setInterval(320)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        # Cycle through zero to three dots without creating new widgets.
        self._frame = (self._frame + 1) % 4
        dots = "." * self._frame
        self.set_markdown(f"*Thinking{dots}*")

    def stop(self):
        """Stop timer callbacks before the card is removed from the layout."""
        self._timer.stop()
