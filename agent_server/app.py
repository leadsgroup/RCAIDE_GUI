"""Public API deployed once for all RCAIDE GUI users."""

from __future__ import annotations

import json
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from .model import ModelError, complete


# Describe one chat message exactly as the desktop GUI sends it.
class Message(BaseModel):
    """Validated conversational message accepted from the desktop client."""

    role: Literal["user", "assistant"]
    content: str | list[dict[str, Any]]

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str | list[dict[str, Any]]):
        # Normal messages are plain strings with a bounded length.
        if isinstance(value, str):
            if not value.strip() or len(value) > 20_000:
                raise ValueError("Message text must contain 1 to 20,000 characters.")
            return value

        # Messages with attachments arrive as text and image content blocks.
        if not 1 <= len(value) <= 4:
            raise ValueError("A multimodal message must contain 1 to 4 content blocks.")
        image_count = 0
        for block in value:
            block_type = block.get("type")
            if block_type == "text":
                # Extracted file text is allowed, but it must remain bounded.
                text = block.get("text")
                if not isinstance(text, str) or not text.strip() or len(text) > 40_000:
                    raise ValueError("Invalid text attachment content.")
            elif block_type == "image_url":
                # Images are embedded data URLs rather than local file paths.
                image_count += 1
                image = block.get("image_url")
                url = image.get("url", "") if isinstance(image, dict) else ""
                if not isinstance(url, str) or not url.startswith("data:image/"):
                    raise ValueError("Only embedded image attachments are accepted.")
                if len(url) > 2_100_000:
                    raise ValueError("An attached image is too large.")
            else:
                raise ValueError("Unsupported message content block.")
        if image_count > 3:
            raise ValueError("Attach no more than three images.")
        return value


# Describe the complete payload sent to POST /api/chat.
class ChatRequest(BaseModel):
    """Bounded chat history plus the sanitized live RCAIDE context."""

    messages: list[Message] = Field(min_length=1, max_length=30)
    context: dict[str, Any]

    @field_validator("messages")
    @classmethod
    def require_user_message(cls, value: list[Message]):
        # A request must end with a question for the model to answer.
        if value[-1].role != "user":
            raise ValueError("The final message must be from the user.")
        return value


# Disable public documentation pages because this API is application-facing.
app = FastAPI(title="RCAIDE Assistant", docs_url=None, redoc_url=None)


@app.get("/health")
def health():
    """Allow desktop bootstrap and cloud monitors to verify readiness."""
    # The GUI checks this before it starts sending chat requests.
    return {"status": "ok"}


@app.post("/api/chat")
def chat(body: ChatRequest, request: Request):
    """Validate a desktop request, invoke the model, and return its text."""
    # Reject accidental calls that do not identify themselves as the RCAIDE GUI.
    # This marker is not a replacement for production authentication.
    if request.headers.get("X-RCAIDE-Client") != "RCAIDE-GUI":
        raise HTTPException(status_code=400, detail="Unsupported client.")

    # Bound project and attachment data before using model tokens or memory.
    if len(json.dumps(body.context, separators=(",", ":"))) > 250_000:
        raise HTTPException(status_code=413, detail="Project context is too large.")
    if len(body.model_dump_json()) > 6_500_000:
        raise HTTPException(status_code=413, detail="The chat request is too large.")

    try:
        # The model adapter adds the trusted prompt and calls GitHub Models.
        answer = complete([message.model_dump() for message in body.messages], body.context)
    except ModelError as exc:
        # Convert provider failures into a clear service error for the desktop.
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # PyQt reads this field and renders it as the assistant's next message.
    return {"message": answer}
