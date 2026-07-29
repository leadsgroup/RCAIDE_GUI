"""Server-side GitHub Models adapter for the RCAIDE assistant."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .prompt import SYSTEM_PROMPT


class ModelError(RuntimeError):
    """Convert provider and response failures into one backend error type."""

    pass


def _bounded_context_text(context: dict, max_chars: int = 12_000) -> str:
    """Keep diagnostics intact while fitting free-tier model context limits."""
    # Send the complete sanitized context when it already fits the budget.
    text = json.dumps(context, separators=(",", ":"))
    if len(text) <= max_chars:
        return text

    # First reduction: retain every high-value summary and only a project excerpt.
    project_text = json.dumps(context.get("project", {}), separators=(",", ":"))
    reduced = {
        "user_query": context.get("user_query", ""),
        "inspection": context.get("inspection", {}),
        "runtime": context.get("runtime", {}),
        "query_parameter_matches": context.get("query_parameter_matches", []),
        "vehicle_parameter_inventory": context.get("vehicle_parameter_inventory", {}),
        "rcaide_field_semantics": context.get("rcaide_field_semantics", {}),
        "rcaide_identity": context.get("rcaide_identity", {}),
        "mission_results": context.get("mission_results", {}),
        "performance_result": context.get("performance_result", {}),
        "latest_error": str(context.get("latest_error", ""))[-3_000:],
        "project_excerpt": project_text[:1_500],
        "notice": "Project details were shortened to fit the model context window.",
    }
    reduced_text = json.dumps(reduced, separators=(",", ":"))
    if len(reduced_text) <= max_chars:
        return reduced_text

    # Keep valid JSON even if numerical mission data is still unusually large.
    reduced["mission_results"] = {
        "excerpt": json.dumps(context.get("mission_results", {}), separators=(",", ":"))[:6_000],
        "notice": "Mission result context was further shortened for this model.",
    }
    reduced["performance_result"] = {}
    reduced["project_excerpt"] = project_text[:750]
    final_text = json.dumps(reduced, separators=(",", ":"))
    if len(final_text) <= max_chars:
        return final_text

    # Final structured reduction: cap parameter matches and inventory entries.
    mission_text = json.dumps(
        context.get("mission_results", {}), separators=(",", ":")
    )
    final_context = {
        "user_query": context.get("user_query", ""),
        "inspection": context.get("inspection", {}),
        "runtime": context.get("runtime", {}),
        "query_parameter_matches": context.get("query_parameter_matches", [])[:16],
        "vehicle_parameter_inventory": {
            **context.get("vehicle_parameter_inventory", {}),
            "parameters": context.get("vehicle_parameter_inventory", {}).get("parameters", [])[:45],
        },
        "rcaide_field_semantics": context.get("rcaide_field_semantics", {}),
        "rcaide_identity": context.get("rcaide_identity", {}),
        "latest_error": str(context.get("latest_error", ""))[-1_500:],
        "mission_results_excerpt": "",
        "notice": "Only query-relevant values and a mission-results excerpt fit this model request.",
    }
    excerpt_size = min(5_500, len(mission_text))
    # Shrink the mission excerpt gradually while preserving valid JSON.
    while excerpt_size > 500:
        final_context["mission_results_excerpt"] = mission_text[:excerpt_size]
        final_text = json.dumps(final_context, separators=(",", ":"))
        if len(final_text) <= max_chars:
            return final_text
        excerpt_size -= 500
    final_context["mission_results_excerpt"] = mission_text[:500]
    final_text = json.dumps(final_context, separators=(",", ":"))
    # Remove lower-priority matches only if the final payload is still too large.
    while len(final_text) > max_chars and final_context["query_parameter_matches"]:
        final_context["query_parameter_matches"].pop()
        final_text = json.dumps(final_context, separators=(",", ":"))
    if len(final_text) <= max_chars:
        return final_text

    # Always return useful, valid JSON even in an extreme oversized project.
    return json.dumps({
        "inspection": context.get("inspection", {}),
        "notice": "The live context exceeded this model's request limit.",
    }, separators=(",", ":"))


def _bounded_messages(
    messages: list[dict], max_chars: int = 8_000
) -> list[dict]:
    """Retain recent text and current-turn images within the request budget."""
    selected: list[dict] = []
    remaining = max_chars
    # Conversation history is limited separately from the live project context.
    recent = messages[-10:]
    # Walk backward so the newest and most relevant turns are kept first.
    for reverse_index, message in enumerate(reversed(recent)):
        if remaining <= 0:
            break
        content = message.get("content", "")
        if isinstance(content, list):
            blocks: list[dict] = []
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text" and remaining > 0:
                    # Bound extracted attachment text before sending it upstream.
                    text = str(block.get("text", ""))[:min(6_000, remaining)]
                    if text:
                        blocks.append({"type": "text", "text": text})
                        remaining -= len(text)
                elif block.get("type") == "image_url" and reverse_index == 0:
                    # Images are kept only for the current turn to control size.
                    image = block.get("image_url")
                    if isinstance(image, dict):
                        blocks.append({"type": "image_url", "image_url": image})
            if blocks:
                selected.append({"role": message["role"], "content": blocks})
        else:
            text = str(content)
            limit = min(3_000, remaining)
            # Preserve the beginning of the current question and the end of
            # older messages, where their latest conclusion usually appears.
            text = text[:limit] if reverse_index == 0 else text[-limit:]
            if text:
                selected.append({"role": message["role"], "content": text})
                remaining -= len(text)
    # Restore chronological order before the model receives the conversation.
    return list(reversed(selected))


def _model_response_text(result: dict) -> str:
    """Extract text from a GitHub Models chat-completion response."""
    try:
        # GitHub Models follows the standard chat-completions response shape.
        text = result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise ModelError("GitHub Models returned an invalid response.") from exc
    if not text:
        raise ModelError("GitHub Models returned no text content.")
    return text


def complete(messages: list[dict], context: dict) -> str:
    """Build one grounded model request and return its response text."""
    # The credential belongs to the backend and is never sent by the desktop.
    token = os.getenv("GITHUB_MODELS_TOKEN", "").strip()
    if not token:
        raise ModelError("The RCAIDE service is missing its GITHUB_MODELS_TOKEN secret.")

    # Environment variables allow deployment to change providers/models without
    # modifying the desktop integration.
    base_url = os.getenv(
        "GITHUB_MODELS_URL", "https://models.github.ai/inference"
    ).rstrip("/")
    model_name = os.getenv("RCAIDE_GITHUB_MODEL", "openai/gpt-4.1-mini")
    context_text = _bounded_context_text(context)
    runtime = context.get("runtime", {}) if isinstance(context, dict) else {}
    mission_results = context.get("mission_results") if isinstance(context, dict) else None
    # Repeat the authoritative run state next to the system prompt so the model
    # does not confuse a configured mission with a completed simulation.
    if runtime.get("mission_results_available") or mission_results:
        run_status = (
            "\n\nAUTHORITATIVE LIVE RUN STATUS: A completed mission result object is loaded. "
            "Never tell the user that the mission has not been run. Use mission_results "
            "to summarize the actual computed values and state their units."
        )
    else:
        run_status = (
            "\n\nAUTHORITATIVE LIVE RUN STATUS: No completed mission result object is loaded. "
            "A configured mission is not the same as a completed run."
        )

    # Combine trusted instructions, bounded live context, and recent chat turns.
    payload = json.dumps({
        "model": model_name,
        "messages": [{
            "role": "system",
            "content": SYSTEM_PROMPT + run_status + "\n\nCurrent live RCAIDE context (JSON):\n" + context_text,
        }, *_bounded_messages(messages)],
        "max_tokens": 1_200,
    }).encode("utf-8")
    # GitHub Models exposes an OpenAI-compatible chat-completions endpoint.
    request = Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    try:
        # Keep network work server-side and decode the provider's JSON response.
        with urlopen(request, timeout=110) as response:
            result = json.loads(response.read().decode("utf-8"))
        return _model_response_text(result)
    except HTTPError as exc:
        # Preserve a bounded provider message so the GUI can explain 401/429/etc.
        detail = exc.read().decode("utf-8", errors="replace")[:1_000]
        raise ModelError(f"GitHub Models returned HTTP {exc.code}: {detail}") from exc
    except ModelError:
        # Avoid wrapping validation errors that are already user-readable.
        raise
    except (URLError, TimeoutError, TypeError, json.JSONDecodeError) as exc:
        # Normalize transport and malformed-response failures for FastAPI.
        raise ModelError(f"GitHub Models request failed: {exc}") from exc
