"""Thin desktop client for the globally hosted RCAIDE assistant."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_SERVICE_URL = ""


class ProviderError(RuntimeError):
    """Present desktop-service failures through one GUI-friendly error type."""

    pass


# These phrases identify known model contradictions that can be replaced with
# answers generated deterministically from the authoritative local context.
_FALSE_NO_RESULTS_PHRASES = (
    "no mission simulation results",
    "no record of a mission",
    "mission has not been run",
    "mission hasn't been run",
    "no stored mission",
    "results are not yet available",
    "results not saved or loaded",
    "do not see any stored mission",
)
_FALSE_PARAMETER_PHRASES = (
    "not all parameters are fully visible",
    "details are deeply nested and large",
    "project excerpt if available",
    "do not have access to the specific parameter",
    "not explicitly listed in the excerpt",
    "not visible in the project excerpt",
    "values hidden",
    "nested and omitted",
    "exact numeric values are not visible",
    "specific dimension parameters",
)
_UNSUPPORTED_SEMANTIC_DIAGNOSES = (
    "update rcaide_vehicle.fuselages.fuselage.number_of_passengers",
    "change rcaide_vehicle.fuselages.fuselage.number_of_passengers",
    "landing_gears.main_gear.length",
    "zero-length landing gear",
)
_MISSING_IDENTITY_PHRASES = (
    "specific institutional or development team info is not shown",
    "specific institutional information is not shown",
    "developed by a community of researchers and engineers",
)


def _response_text(result: dict[str, Any]) -> str:
    """Extract the assistant message from the FastAPI response envelope."""
    message = result.get("message")
    if isinstance(message, str) and message.strip():
        return message.strip()
    raise ProviderError("The RCAIDE assistant service returned no answer.")


def _messages_with_live_status(
    messages: list[dict[str, Any]], context: dict[str, Any]
) -> list[dict[str, Any]]:
    """Place authoritative GUI state in the latest request as well as server context."""
    # Bound desktop history before adding current-state reminders.
    outgoing = [dict(message) for message in messages[-16:]]
    if not outgoing:
        return outgoing
    # Mission-run state is repeated in the latest turn because it must override
    # assumptions the model may have formed earlier in the conversation.
    runtime = context.get("runtime", {})
    results = context.get("mission_results")
    if runtime.get("mission_results_available") or results:
        segment_count = (
            results.get("segment_count", runtime.get("mission_result_segment_count", 0))
            if isinstance(results, dict) else runtime.get("mission_result_segment_count", 0)
        )
        status = (
            "[AUTHORITATIVE LIVE GUI FACT: A completed mission result object is loaded "
            f"with {segment_count} segment(s). Do not claim the mission was not run. "
            "Use the mission_results values supplied in context.]\n\n"
        )
    else:
        status = "[AUTHORITATIVE LIVE GUI FACT: No completed mission result object is loaded.]\n\n"
    inventory = context.get("vehicle_parameter_inventory", {})
    parameter_snapshot = ""
    identity = context.get("rcaide_identity", {})
    # Keep official attribution near identity questions and preserve the links.
    if isinstance(identity, dict) and identity:
        status += (
            "[RCAIDE IDENTITY: The RCAIDE-LEADS version used by this GUI is developed and "
            "maintained by the Laboratory for Electric Aircraft Design and Sustainability "
            "(LEADS) at UIUC, directed by Professor Matthew Clarke, with broader open-source "
            "community contributions. In identity answers link LEADS to "
            "https://www.leadsresearchgroup.com, UIUC Grainger Engineering to "
            "https://grainger.illinois.edu, and Dr. Matthew Clarke to "
            "https://grainger.illinois.edu/about/directory/faculty/maclarke.]\n\n"
        )
    # The desktop reinforces the same engineering-only scope as the server.
    status += (
        "[SCOPE RULE: Assist only with RCAIDE, this GUI, aircraft/aerospace design, and "
        "engineering topics relevant to work in the application. Greetings are allowed. "
        "For an unrelated request, reply with exactly: I can only assist with anything "
        "related to RCAIDE and the GUI.]\n\n"
    )
    if isinstance(inventory, dict) and inventory.get("parameters"):
        # Remind the model that inventory values are verified, not suggestions.
        status += (
            "[AUTHORITATIVE VEHICLE FACT: Exact current Vehicle Setup values are supplied "
            "in vehicle_parameter_inventory. Quote those numbers and units; do not say "
            "they are hidden by nesting.]\n\n"
        )
        status += (
            "[RCAIDE FIELD SEMANTICS: Vehicle-level number_of_passengers drives payload/weight; "
            "do not require fuselage.number_of_passengers to match it. Landing-gear methods use "
            "strut_length; generic length=0 is not by itself an error. Do not assign causality to "
            "a zero/default unless the active method consumes it.]\n\n"
        )
        status += (
            "[RESPONSE LAYOUT: Use short sections. Use a Markdown table only when it clearly "
            "improves comparison across several items; do not use tables for ordinary explanations, "
            "workflow steps, or short answers. Avoid deeply nested bullet lists.]\n\n"
        )
        # Build a compact cross-section of real Vehicle Setup values. This gives
        # each major aircraft area representation without sending every field.
        snapshot_lines = ["\n\n[CURRENT VEHICLE SETUP VALUES - AUTHORITATIVE]"]
        snapshot_length = len(snapshot_lines[0])
        groups: dict[str, list[dict[str, Any]]] = {
            "mass": [], "wing": [], "fuselage": [], "engine": [], "cabin": [], "other": [],
        }
        for parameter in inventory["parameters"]:
            if not isinstance(parameter, dict):
                continue
            path = str(parameter.get("path", "")).lower()
            if ".moments_of_inertia." in path:
                continue
            if ".segments." in path and parameter.get("value") in (0, 0.0, False, None):
                continue
            # Group paths by engineering area for balanced selection below.
            if path.startswith("rcaide_vehicle.mass_properties."):
                group = "mass"
            elif ".wings.main_wing." in path:
                group = "wing"
            elif ".fuselages." in path:
                group = "fuselage"
            elif ".propulsors." in path:
                group = "engine"
            elif "passenger" in path or "seat" in path or ".cabins." in path:
                group = "cabin"
            else:
                group = "other"
            groups[group].append(parameter)

        # Within each group, prefer the values most useful for design review.
        priorities = {
            "mass": ("max_takeoff", "operating_empty", "max_fuel", "max_payload", "fuel", "payload"),
            "wing": ("spans.projected", "areas.reference", "chords.root", "chords.tip", "mean_aerodynamic", "quarter_chord"),
            "fuselage": ("lengths.total", ".width", "heights.maximum", "lengths.nose", "lengths.tail"),
            "engine": ("sealevel_static_thrust", "design_thrust", "bypass_ratio", "pressure_ratio", ".length", ".diameter"),
            "cabin": ("number_of_passengers", "number_of_seats", "seat"),
            "other": ("reference_area", "number_of_passengers", "length"),
        }

        def priority(parameter: dict[str, Any], group: str):
            path = str(parameter.get("path", "")).lower()
            preferred = priorities[group]
            rank = next((index for index, term in enumerate(preferred) if term in path), len(preferred))
            zero_penalty = parameter.get("value") in (0, 0.0, False, None)
            nested_penalty = ".segments." in path or ".classes." in path
            return (rank, zero_penalty, nested_penalty, len(path))

        for group in groups:
            groups[group].sort(key=lambda item, name=group: priority(item, name))

        # Select values round-robin so mass or detailed geometry cannot crowd
        # every other category out of the limited snapshot.
        ordered: list[dict[str, Any]] = []
        for index in range(12):
            for group in ("mass", "wing", "fuselage", "engine", "cabin", "other"):
                if index < len(groups[group]):
                    ordered.append(groups[group][index])
        for parameter in ordered:
            unit = f" {parameter['unit']}" if parameter.get("unit") else ""
            line = f"{parameter.get('path')} = {parameter.get('value')}{unit}"
            # Keep room for the user's actual question and recent conversation.
            if snapshot_length + len(line) + 1 > 2_150:
                break
            snapshot_lines.append(line)
            snapshot_length += len(line) + 1
        snapshot_lines.append("[END CURRENT VEHICLE SETUP VALUES]")
        parameter_snapshot = "\n".join(snapshot_lines)

    # Prepend status to the current user text and append numerical values. For a
    # multimodal turn, preserve the image blocks exactly as the GUI created them.
    content = outgoing[-1].get("content", "")
    if isinstance(content, list):
        blocks = [dict(block) for block in content]
        for block in blocks:
            if block.get("type") == "text":
                block["text"] = status + str(block.get("text", "")) + parameter_snapshot
                break
        else:
            blocks.insert(0, {"type": "text", "text": status + parameter_snapshot})
        outgoing[-1]["content"] = blocks
    else:
        outgoing[-1]["content"] = status + str(content) + parameter_snapshot
    return outgoing


def _number(value: Any) -> str:
    """Format a context number compactly for deterministic Markdown answers."""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "?"
    return f"{numeric:,.4g}"


def _mission_result_fallback(context: dict[str, Any]) -> str:
    """Give a verified local summary if a model contradicts loaded run state."""
    results = context.get("mission_results", {})
    segments = results.get("segments", []) if isinstance(results, dict) else []
    lines = [
        "### Latest mission results",
        "",
        "A completed mission run **is loaded** in the GUI. Here is the verified numerical summary:",
        "",
    ]
    # Focus the fallback on broadly useful flight and vehicle metrics.
    preferred = (
        ("true_airspeed", "Airspeed"),
        ("altitude", "Altitude"),
        ("mach_number", "Mach"),
        ("total_mass", "Mass"),
        ("aircraft_range", "Range"),
    )
    for index, segment in enumerate(segments[:12]):
        if not isinstance(segment, dict):
            continue
        lines.append(f"#### {segment.get('tag', f'Segment {index + 1}')}")
        series = segment.get("series", {})
        wrote_value = False
        for key, label in preferred:
            summary = series.get(key) if isinstance(series, dict) else None
            if not isinstance(summary, dict):
                continue
            unit = summary.get("unit", "")
            lines.append(
                f"- **{label}:** {_number(summary.get('minimum'))} to "
                f"{_number(summary.get('maximum'))} {unit} "
                f"(start {_number(summary.get('first'))}, end {_number(summary.get('last'))})"
            )
            wrote_value = True
        if not wrote_value:
            lines.append("- The segment exists, but its standard numeric series could not be extracted.")
        lines.append("")
    if not segments:
        lines.append(
            "The result object is present, but its segment arrays could not be serialized. "
            "The mission should not be rerun solely because of this assistant-context issue."
        )
    return "\n".join(lines)


def _vehicle_parameter_fallback(context: dict[str, Any]) -> str:
    """List verified Vehicle Setup values when the model claims they are hidden."""
    inventory = context.get("vehicle_parameter_inventory", {})
    parameters = inventory.get("parameters", []) if isinstance(inventory, dict) else []
    lines = [
        "### Current Vehicle Setup values",
        "",
        "These values were read directly from the vehicle currently loaded in the GUI:",
        "",
    ]
    for parameter in parameters[:45]:
        if not isinstance(parameter, dict):
            continue
        path = str(parameter.get("path", "parameter"))
        label = path.removeprefix("rcaide_vehicle.").replace("_", " ")
        unit = f" {parameter['unit']}" if parameter.get("unit") else ""
        lines.append(f"- **{label}:** `{parameter.get('value')}`{unit}")
    lines.extend((
        "",
        f"Showing {min(45, len(parameters))} of "
        f"{inventory.get('total_scalar_parameters_found', len(parameters))} scalar values. "
        "Ask for a component such as the main wing, fuselage, mass properties, or engines "
        "to retrieve the most relevant matching paths.",
    ))
    return "\n".join(lines)


def _semantic_diagnosis_fallback(context: dict[str, Any]) -> str:
    """Correct known RCAIDE field interpretations using verified semantics."""
    inventory = context.get("vehicle_parameter_inventory", {})
    # Index values by exact JSON path so the correction can quote live data.
    by_path = {
        item.get("path"): item for item in inventory.get("parameters", [])
        if isinstance(item, dict)
    } if isinstance(inventory, dict) else {}
    passengers = by_path.get("rcaide_vehicle.number_of_passengers", {}).get("value", "the vehicle value")
    return (
        "### RCAIDE setup review\n\n"
        "The earlier diagnosis connected two default fields to the mission without evidence. "
        "Those recommendations should **not** be applied as written.\n\n"
        "- **Passenger count:** RCAIDE payload and most weight methods use the vehicle-level "
        f"`number_of_passengers` value ({passengers}). `fuselage.number_of_passengers = 1` is a "
        "fuselage default and is not required to equal the aircraft total. Cabin passenger fields "
        "are used when distributing passenger mass.\n"
        "- **Landing gear:** RCAIDE geometry, noise, and landing-gear weight methods use "
        "`strut_length`. The inherited generic `length = 0` does not establish a zero-length gear "
        "and should not be changed to the strut length without a method-specific reason.\n"
        "- **Fuel and payload:** The loaded current and maximum values are useful consistency checks, "
        "but they are not proof of an unrealistic mission. Compare them with the actual segment mass "
        "history and fuel consumption.\n"
        "- **Geometry and propulsion:** The listed values appear plausible as a basic sanity check, "
        "but diagnosing mission behavior requires comparing the computed segment results, solver "
        "warnings, and the analyses enabled for those segments.\n\n"
        "A safe recommendation is to inspect actual result discontinuities first, then trace each "
        "outlier to a parameter consumed by the active RCAIDE method."
    )


def _rcaide_identity_fallback() -> str:
    """Return the verified LEADS/UIUC attribution with official links."""
    return (
        "### Who develops RCAIDE?\n\n"
        "The **RCAIDE-LEADS** version used by this GUI is developed and maintained by the "
        "[Laboratory for Electric Aircraft Design and Sustainability "
        "(LEADS)](https://www.leadsresearchgroup.com) at "
        "[UIUC Grainger Engineering](https://grainger.illinois.edu), University of Illinois "
        "Urbana-Champaign. LEADS is directed by "
        "[Dr. Matthew Clarke](https://grainger.illinois.edu/about/directory/faculty/maclarke).\n\n"
        "RCAIDE is also an open-source project with contributions from the broader aerospace "
        "research and engineering community."
    )


def _ground_response(answer: str, context: dict[str, Any]) -> str:
    """Replace known contradictions with deterministic context-based answers."""
    runtime = context.get("runtime", {})
    results_loaded = bool(runtime.get("mission_results_available") or context.get("mission_results"))
    normalized = answer.lower()
    # A model response is accepted unless it matches a narrow, tested failure
    # pattern; this avoids rewriting normal engineering explanations.
    if results_loaded and any(phrase in normalized for phrase in _FALSE_NO_RESULTS_PHRASES):
        return _mission_result_fallback(context)
    inventory = context.get("vehicle_parameter_inventory", {})
    if isinstance(inventory, dict) and inventory.get("parameters") and any(
        phrase in normalized for phrase in _FALSE_PARAMETER_PHRASES
    ):
        return _vehicle_parameter_fallback(context)
    if any(phrase in normalized for phrase in _UNSUPPORTED_SEMANTIC_DIAGNOSES):
        return _semantic_diagnosis_fallback(context)
    query = str(context.get("user_query", "")).lower()
    # Identity questions must include both the lab and its director.
    identity_question = "rcaide" in query and any(
        term in query for term in ("who", "built", "develop", "maintain", "direct")
    )
    if identity_question and (
        "leads" not in normalized or "matthew clarke" not in normalized
    ):
        return _rcaide_identity_fallback()
    if any(phrase in normalized for phrase in _MISSING_IDENTITY_PHRASES):
        return _rcaide_identity_fallback()
    return answer


def generate_reply(
    messages: list[dict[str, Any]],
    context: dict[str, Any],
    configuration: dict[str, str] | None = None,
) -> str:
    """Send live GUI context to the RCAIDE-managed online assistant."""
    # Reserved for future per-request options; model configuration stays server-side.
    del configuration
    # bootstrap.py sets this to either the local development API or a hosted URL.
    service_url = os.getenv("RCAIDE_AGENT_SERVICE_URL", DEFAULT_SERVICE_URL).strip().rstrip("/")
    if not service_url:
        startup_error = os.getenv("RCAIDE_AGENT_STARTUP_ERROR", "").strip()
        raise ProviderError(
            startup_error or
            "This development build has no RCAIDE assistant service URL."
        )
    # The service receives both conversation messages and the sanitized context.
    payload = json.dumps({
        "messages": _messages_with_live_status(messages, context),
        "context": context,
    }).encode("utf-8")
    # The client marker identifies the expected desktop caller. A production
    # deployment should add real authentication and rate limiting in front.
    request = Request(
        f"{service_url}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json", "X-RCAIDE-Client": "RCAIDE-GUI"},
        method="POST",
    )
    try:
        # Keep the network call synchronous here; PyQt runs this function in its
        # worker thread so the interface remains responsive.
        with urlopen(request, timeout=120) as response:
            answer = _response_text(json.loads(response.read().decode("utf-8")))
            return _ground_response(answer, context)
    except HTTPError as exc:
        # Include a bounded server detail such as a model 401, 413, or 429.
        detail = exc.read().decode("utf-8", errors="replace")[:1_000]
        raise ProviderError(f"RCAIDE assistant returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        # Translate DNS/refusal failures into actionable desktop wording.
        raise ProviderError(
            "The global RCAIDE assistant is unavailable. Check the internet connection "
            f"or service status. Details: {exc.reason}"
        ) from exc
    except (TimeoutError, json.JSONDecodeError) as exc:
        # Normalize timeouts and malformed service responses for the GUI.
        raise ProviderError(f"RCAIDE assistant request failed: {exc}") from exc
