"""Build small, useful model context from an RCAIDE GUI project file."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any

import numpy as np


# Hard limits prevent deeply nested RCAIDE objects from overwhelming the model.
MAX_CONTEXT_DEPTH = 7
MAX_COLLECTION_ITEMS = 30
MAX_STRING_LENGTH = 4_000
# Any field whose name suggests a credential is redacted before transmission.
SENSITIVE_KEY_PARTS = ("password", "secret", "token", "api_key", "authorization")
# Common conversational words do not help rank engineering parameter paths.
QUERY_STOP_WORDS = {
    "about", "actual", "agent", "all", "are", "can", "current", "data", "does",
    "from", "give", "have", "list", "much", "parameter", "parameters", "please",
    "project", "result", "results", "rcaide", "setup", "show", "tell", "that", "the",
    "this", "user", "value", "values", "vehicle", "what", "when", "where", "which",
    "with", "would",
}
# Expand user-friendly vocabulary into terms commonly used by RCAIDE fields.
QUERY_ALIASES = {
    "airspeed": {"velocity", "freestream"},
    "tas": {"velocity", "freestream"},
    "speed": {"velocity", "mach"},
    "weight": {"mass", "weights"},
    "range": {"aircraft_range"},
    "aoa": {"alpha", "angle"},
    "geometry": {"span", "spans", "chord", "chords", "area", "areas", "sweep", "length", "width", "height", "diameter"},
    "dimension": {"length", "width", "height", "diameter", "span", "chord"},
    "dimensions": {"length", "width", "height", "diameter", "span", "chord"},
    "engine": {"propulsor", "turbofan", "thrust", "bypass"},
    "engines": {"propulsor", "turbofan", "thrust", "bypass"},
    "passenger": {"passengers", "seats"},
    "capacity": {"passengers", "seats", "payload", "fuel"},
}

# Base weights keep important aircraft-level values visible in broad summaries.
_IMPORTANT_PARAMETER_NAMES = {
    "max_takeoff": 18, "operating_empty": 18, "max_fuel": 18,
    "max_payload": 17, "max_zero_fuel": 17, "reference_area": 17,
    "number_of_passengers": 16, "spans": 15, "span": 15,
    "aspect_ratio": 15, "bypass_ratio": 15, "design_thrust": 15,
    "sealevel_static_thrust": 15, "length": 13, "width": 13,
    "height": 13, "root": 12, "tip": 12, "mean_aerodynamic": 12,
    "quarter_chord": 12, "pressure_ratio": 11, "diameter": 11,
}


@dataclass(frozen=True)
class Diagnostic:
    """One stable preflight issue that can be serialized for the model."""

    severity: str
    code: str
    message: str
    path: str | None = None


def _mapping(value: Any) -> dict[str, Any]:
    """Treat unexpected non-dictionary project sections as empty mappings."""
    return value if isinstance(value, dict) else {}


def _collection_size(value: Any) -> int:
    """Return a safe component count for either dictionaries or lists."""
    if isinstance(value, (dict, list)):
        return len(value)
    return 0


def inspect_project(project: dict[str, Any]) -> dict[str, Any]:
    """Return a stable overview and actionable preflight diagnostics."""
    diagnostics: list[Diagnostic] = []
    vehicle = _mapping(project.get("rcaide_vehicle"))
    analyses = project.get("analysis_data", [])
    missions = project.get("mission_data", [])

    # Check only high-confidence setup problems; detailed reasoning is left to
    # the model after it receives real parameters and active analysis state.
    if not vehicle:
        diagnostics.append(Diagnostic(
            "error", "vehicle_missing",
            "The project does not contain an rcaide_vehicle definition.",
            "rcaide_vehicle",
        ))

    tag = vehicle.get("tag")
    if vehicle and (not isinstance(tag, str) or not tag.strip()):
        diagnostics.append(Diagnostic(
            "warning", "vehicle_tag_missing",
            "Give the vehicle a non-empty tag so configurations and results are easier to identify.",
            "rcaide_vehicle.tag",
        ))

    if not isinstance(analyses, list):
        diagnostics.append(Diagnostic(
            "error", "analyses_invalid",
            "analysis_data must be a list.", "analysis_data",
        ))
        analyses = []
    elif not analyses:
        diagnostics.append(Diagnostic(
            "warning", "analyses_missing",
            "No analyses are configured. Add the analyses required by each mission segment before simulation.",
            "analysis_data",
        ))

    if not isinstance(missions, list):
        diagnostics.append(Diagnostic(
            "error", "mission_invalid",
            "mission_data must be a list.", "mission_data",
        ))
        missions = []
    elif not missions:
        diagnostics.append(Diagnostic(
            "warning", "mission_missing",
            "No mission is defined. Add and save at least one mission segment before simulation.",
            "mission_data",
        ))

    # Component counts give the assistant a fast overview without walking the
    # entire serialized vehicle for every general question.
    components = {
        "wings": _collection_size(vehicle.get("wings")),
        "fuselages": _collection_size(vehicle.get("fuselages")),
        "booms": _collection_size(vehicle.get("booms")),
        "networks": _collection_size(vehicle.get("networks")),
        "nacelles": _collection_size(vehicle.get("nacelles")),
        "landing_gears": _collection_size(vehicle.get("landing_gears")),
    }
    if vehicle and not components["wings"]:
        diagnostics.append(Diagnostic(
            "warning", "wings_missing",
            "No wing components were found; aerodynamic and mission analyses may be incomplete.",
            "rcaide_vehicle.wings",
        ))

    return {
        "vehicle_tag": tag or "Untitled vehicle",
        "components": components,
        "configuration_count": _collection_size(project.get("config_data", [])),
        "analysis_count": len(analyses),
        "mission_count": len(missions),
        "diagnostics": [asdict(item) for item in diagnostics],
    }


def _redact_string(value: str) -> str:
    """Remove personal home directories and absolute local paths from text."""
    home = str(Path.home())
    if home:
        value = re.sub(re.escape(home), "<user-home>", value, flags=re.IGNORECASE)
    value = re.sub(r"[A-Za-z]:\\[^\s\"']+", "<local-path>", value)
    value = re.sub(r"/(?:home|Users)/[^\s/]+", "/<user-home>", value)
    return value


def compact_value(value: Any, depth: int = 0) -> Any:
    """Bound project data before it is sent to a hosted model."""
    # Stop recursive object graphs at a predictable depth.
    if depth >= MAX_CONTEXT_DEPTH:
        return "<nested data omitted>"
    if isinstance(value, dict):
        items = list(value.items())
        result = {}
        for key, child in items[:MAX_COLLECTION_ITEMS]:
            key_text = str(key)
            # Preserve the field name so the model knows data was intentionally
            # removed without exposing the sensitive value.
            if any(part in key_text.lower() for part in SENSITIVE_KEY_PARTS):
                result[key_text] = "<sensitive value omitted>"
            else:
                result[key_text] = compact_value(child, depth + 1)
        if len(items) > MAX_COLLECTION_ITEMS:
            result["<omitted>"] = f"{len(items) - MAX_COLLECTION_ITEMS} fields"
        return result
    if isinstance(value, list):
        result = [compact_value(child, depth + 1) for child in value[:MAX_COLLECTION_ITEMS]]
        if len(value) > MAX_COLLECTION_ITEMS:
            result.append(f"<{len(value) - MAX_COLLECTION_ITEMS} items omitted>")
        return result
    if isinstance(value, str):
        # Redact local paths before applying the string-length limit.
        value = _redact_string(value)
        return value[:MAX_STRING_LENGTH] + ("..." if len(value) > MAX_STRING_LENGTH else "")
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)[:MAX_STRING_LENGTH]


def _query_terms(query: str) -> set[str]:
    """Convert a natural-language question into parameter-search terms."""
    terms = {
        word for word in re.findall(r"[a-z0-9_]+", query.lower())
        if len(word) >= 3 and word not in QUERY_STOP_WORDS
    }
    # Aliases let questions such as "engine size" match propulsor fields.
    expanded = set(terms)
    for term in terms:
        expanded.update(QUERY_ALIASES.get(term, set()))
    return expanded


def find_project_parameters(
    project: dict[str, Any], query: str, limit: int = 24
) -> list[dict[str, Any]]:
    """Find concrete saved GUI values whose paths match the user's wording."""
    terms = _query_terms(query)
    if not terms:
        return []

    matches: list[tuple[int, str, Any]] = []
    visited = 0

    def walk(value: Any, path: str, depth: int = 0):
        nonlocal visited
        # Protect against unexpectedly large or cyclic-looking serialized data.
        if visited >= 30_000 or depth > 12:
            return
        visited += 1
        if isinstance(value, dict):
            for key, child in value.items():
                key_text = str(key)
                if key_text == "__type__" or any(
                    part in key_text.lower() for part in SENSITIVE_KEY_PARTS
                ):
                    continue
                walk(child, f"{path}.{key_text}" if path else key_text, depth + 1)
            return
        if isinstance(value, list) and (
            len(value) > 12 or any(isinstance(child, (dict, list)) for child in value)
        ):
            for index, child in enumerate(value[:40]):
                walk(child, f"{path}[{index}]", depth + 1)
            return

        # A path receives one point for each expanded query term it contains.
        path_lower = path.lower()
        score = sum(1 for term in terms if term in path_lower)
        if score:
            # RCAIDE JSON wraps saved values as [value, unit-argument]. The
            # default unit argument is 0, so expose the actual editable value.
            actual_value = (
                value[0]
                if isinstance(value, list) and len(value) == 2 and value[1] == 0
                else value
            )
            matches.append((score, path, compact_value(actual_value)))

    walk(project, "")
    # Prefer more term matches, then shorter and more readable parameter paths.
    matches.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    return [
        {"path": path, "value": value}
        for _score, path, value in matches[:limit]
    ]


def _parameter_unit(path: str) -> str:
    """Infer the SI unit used by common RCAIDE saved parameter paths."""
    lower = path.lower()
    leaf = lower.rsplit(".", 1)[-1]
    if "ratio" in leaf or leaf in {"taper", "efficiency", "mach_number"}:
        return "dimensionless"
    if "mass_flow" in lower:
        return "kg/s"
    if "mass" in leaf or "weight" in leaf or "payload" in leaf or (
        lower.startswith("rcaide_vehicle.mass_properties.") and leaf in {"fuel", "cargo"}
    ) or leaf in {
        "max_takeoff", "operating_empty", "max_fuel", "max_cargo", "max_zero_fuel"
    }:
        return "kg"
    if "area" in leaf or ".areas." in lower:
        return "m^2"
    if "volume" in leaf or "capacity" in leaf and "fuel" in lower:
        return "m^3"
    if "thrust" in leaf or leaf == "force":
        return "N"
    if "power" in leaf:
        return "W"
    if "temperature" in leaf:
        return "K"
    if "pressure" in leaf:
        return "Pa"
    if any(word in lower for word in ("angle", ".sweep", ".twist", "dihedral", ".alpha")):
        return "rad"
    if any(word in leaf for word in ("speed", "velocity")):
        return "m/s"
    if leaf in {"span", "projected", "root", "tip", "mean_aerodynamic"} or any(
        group in lower for group in (".lengths.", ".heights.")
    ) or (
        leaf == "total" and any(group in lower for group in (".spans.", ".lengths."))
    ) or any(
        word in leaf for word in ("length", "width", "height", "diameter", "chord")
    ):
        return "m"
    return ""


def summarize_vehicle_parameters(
    project: dict[str, Any], query: str = "", limit: int = 90
) -> dict[str, Any]:
    """Build a bounded inventory of actual editable Vehicle Setup values."""
    vehicle = project.get("rcaide_vehicle", {})
    if not isinstance(vehicle, dict):
        return {"count_included": 0, "parameters": []}
    terms = _query_terms(query)
    candidates: list[tuple[int, str, Any, str]] = []
    total = 0

    def add(path: str, value: Any):
        nonlocal total
        # The inventory contains scalar editable values, not nested containers.
        if value is None or isinstance(value, (dict, list)):
            return
        if not isinstance(value, (str, bool, int, float)):
            return
        total += 1
        lower = path.lower()
        leaf = lower.rsplit(".", 1)[-1]
        # Combine general aircraft importance with relevance to this question.
        score = _IMPORTANT_PARAMETER_NAMES.get(leaf, 0)
        score += sum(30 for term in terms if term in lower)
        # Favor aircraft-level mass and primary geometry over inherited defaults
        # and highly repetitive component/segment fields.
        if lower.startswith("rcaide_vehicle.mass_properties."):
            score += 18
        elif ".mass_properties." in lower:
            score -= 22
        if ".wings." in lower and any(
            group in lower for group in (".spans.", ".chords.", ".areas.", ".sweeps.")
        ):
            score += 10
        if ".fuselages." in lower and any(
            group in lower for group in (".lengths.", ".heights.")
        ):
            score += 10
        if any(term in lower for term in (".lengths.total", ".heights.maximum")):
            score += 18
        if ".segments." in lower:
            score -= 18
        if ".moments_of_inertia." in lower:
            score -= 24
        if value not in (0, 0.0, False, ""):
            score += 3
        else:
            score -= 8
        score -= min(8, path.count("."))
        candidates.append((score, path, compact_value(value), _parameter_unit(path)))

    def walk(value: Any, path: str, depth: int = 0):
        # Traverse farther than compact_value because this pass emits only a
        # small ranked scalar inventory rather than the full nested structure.
        if depth > 15:
            return
        if isinstance(value, dict):
            for key, child in value.items():
                key_text = str(key)
                if key_text == "__type__" or any(
                    part in key_text.lower() for part in SENSITIVE_KEY_PARTS
                ):
                    continue
                walk(child, f"{path}.{key_text}", depth + 1)
            return
        # Every editable value in RCAIDE JSON is normally stored as [SI value, 0].
        if isinstance(value, list) and len(value) == 2 and value[1] == 0:
            inner = value[0]
            if isinstance(inner, list) and len(inner) <= 6 and not any(
                isinstance(item, (dict, list)) for item in inner
            ):
                total_before = len(candidates)
                for index, child in enumerate(inner):
                    add(f"{path}[{index}]", child)
                if len(candidates) == total_before:
                    add(path, inner)
            else:
                add(path, inner)
            return
        if isinstance(value, list):
            for index, child in enumerate(value[:50]):
                walk(child, f"{path}[{index}]", depth + 1)
            return
        add(path, value)

    walk(vehicle, "rcaide_vehicle")
    candidates.sort(key=lambda item: (-item[0], item[1]))
    category_counts: dict[str, int] = {}

    def category(path: str) -> str:
        lower = path.lower()
        if lower.startswith("rcaide_vehicle.mass_properties."):
            return "vehicle_mass"
        if ".wings.main_wing." in lower:
            return "main_wing"
        if ".wings." in lower:
            return "other_wings"
        if ".fuselages." in lower:
            return "fuselage"
        if ".propulsors." in lower:
            return "propulsor"
        if "passenger" in lower or "seat" in lower or ".cabins." in lower:
            return "payload_cabin"
        return lower.split(".")[1] if "." in lower else "vehicle"

    # Balance categories so one large component cannot consume the whole budget.
    balanced: list[tuple[int, str, Any, str]] = []
    deferred: list[tuple[int, str, Any, str]] = []
    per_category_limit = max(12, limit // 6)
    for candidate in candidates:
        group = category(candidate[1])
        if category_counts.get(group, 0) < per_category_limit:
            balanced.append(candidate)
            category_counts[group] = category_counts.get(group, 0) + 1
        else:
            deferred.append(candidate)
        if len(balanced) >= limit:
            break
    if len(balanced) < limit:
        balanced.extend(deferred[:limit - len(balanced)])
    parameters = [
        {"path": path, "value": value, **({"unit": unit} if unit and not isinstance(value, bool) else {})}
        for _score, path, value, unit in balanced[:limit]
    ]
    return {
        "total_scalar_parameters_found": total,
        "count_included": len(parameters),
        "parameters": parameters,
        "note": (
            "Values are read from the current in-memory Vehicle Setup. Units shown are "
            "RCAIDE internal SI units; fields without a unit are labels, flags, counts, or dimensionless."
        ),
    }


def _child(value: Any, name: str, default=None):
    """Read a field from either a dictionary-like object or an attribute."""
    if isinstance(value, Mapping) or (
        hasattr(value, "get") and callable(getattr(value, "get"))
    ):
        try:
            return value.get(name, default)
        except Exception:
            pass
    return getattr(value, name, default)


def _nested(value: Any, path: str):
    """Follow a dotted path through RCAIDE Data objects and mappings."""
    current = value
    for part in path.split("."):
        current = _child(current, part, None)
        if current is None:
            return None
    return current


def _numeric_summary(
    value: Any,
    unit: str,
    include_values: bool = False,
    scale: float = 1.0,
    max_values: int = 30,
) -> dict[str, Any] | None:
    """Convert a numerical result array into bounded descriptive statistics."""
    try:
        array = np.asarray(value, dtype=float) * scale
    except (TypeError, ValueError):
        return None
    if array.size == 0:
        return None
    flat = array.reshape(-1)
    finite = flat[np.isfinite(flat)]
    if finite.size == 0:
        return None

    # First/last and extrema answer most result questions without full arrays.
    summary: dict[str, Any] = {
        "unit": unit,
        "shape": list(array.shape),
        "count": int(flat.size),
        "first": float(flat[0]),
        "last": float(flat[-1]),
        "minimum": float(np.min(finite)),
        "maximum": float(np.max(finite)),
    }
    if include_values:
        # Query-relevant series receive representative values for deeper analysis.
        if flat.size <= max_values:
            indices = np.arange(flat.size)
        else:
            indices = np.linspace(0, flat.size - 1, max_values, dtype=int)
        summary["sample_indices"] = indices.tolist()
        summary["sample_values"] = [float(flat[index]) for index in indices]
        summary["sampling_note"] = (
            "All values" if flat.size <= max_values
            else f"{max_values} evenly spaced values from {flat.size} total"
        )
    return summary


# Known RCAIDE result paths and the units/scales exposed to the assistant.
_MISSION_SERIES = (
    ("time", "conditions.frames.inertial.time", "s", 1.0),
    ("true_airspeed", "conditions.freestream.velocity", "m/s", 1.0),
    ("true_airspeed_knots", "conditions.freestream.velocity", "knots", 1 / 0.514444),
    ("altitude", "conditions.freestream.altitude", "m", 1.0),
    ("mach_number", "conditions.freestream.mach_number", "Mach", 1.0),
    ("aircraft_range", "conditions.frames.inertial.aircraft_range", "m", 1.0),
    ("angle_of_attack", "conditions.aerodynamics.angles.alpha", "rad", 1.0),
    ("lift_coefficient", "conditions.aerodynamics.coefficients.lift.total", "dimensionless", 1.0),
    ("drag_coefficient", "conditions.aerodynamics.coefficients.drag.total", "dimensionless", 1.0),
    ("total_mass", "conditions.weights.total_mass", "kg", 1.0),
    ("power", "conditions.energy.power", "W", 1.0),
)


def summarize_mission_results(results: Any, query: str = "") -> dict[str, Any] | None:
    """Expose bounded, numerical mission outputs instead of only an exists flag."""
    if results is None:
        return None
    segments_value = _child(results, "segments", None)
    if segments_value is None:
        return None
    try:
        segments = list(segments_value.values()) if isinstance(segments_value, Mapping) else list(segments_value)
    except (TypeError, AttributeError):
        return None

    terms = _query_terms(query)
    output_segments = []
    # Bound the number of segments while retaining numerical summaries for each.
    for index, segment in enumerate(segments[:12]):
        tag = _child(segment, "tag", f"segment_{index + 1}")
        series_output = {}
        for label, path, unit, scale in _MISSION_SERIES:
            value = _nested(segment, path)
            if value is None:
                continue
            searchable = f"{label} {path}".lower()
            # Include samples only when the question targets this particular series.
            include_values = bool(terms and any(term in searchable for term in terms))
            summary = _numeric_summary(value, unit, include_values, scale)
            if summary is not None:
                series_output[label] = summary
        output_segments.append({"index": index, "tag": str(tag), "series": series_output})

    return {
        "segment_count": len(segments),
        "segments_included": len(output_segments),
        "segments": output_segments,
        "note": "Series include real computed values. Long arrays are sampled only when relevant to the question.",
    }


def build_agent_context(
    project: dict[str, Any],
    error_trace: str = "",
    *,
    results: Any = None,
    performance_result: Any = None,
    query: str = "",
) -> dict[str, Any]:
    """Assemble the complete sanitized snapshot sent with one user question."""
    # Keep both a compact project excerpt and targeted inventories: broad
    # questions need structure, while numerical questions need exact values.
    context = {
        "user_query": compact_value(query),
        "inspection": inspect_project(project),
        "project": compact_value(project),
        "query_parameter_matches": find_project_parameters(project, query),
        "vehicle_parameter_inventory": summarize_vehicle_parameters(project, query),
        # These verified semantics prevent plausible but incorrect diagnoses of
        # inherited/default RCAIDE fields.
        "rcaide_field_semantics": {
            "passenger_count": (
                "Vehicle-level number_of_passengers is used by payload, systems, and most "
                "weight methods. Fuselage.number_of_passengers defaults to 1 and is not a "
                "required duplicate of the vehicle count; cabin passenger fields distribute payload."
            ),
            "landing_gear_dimensions": (
                "Landing-gear geometry, noise, and weight methods use strut_length. The inherited "
                "generic length field may remain zero and should not be flagged by itself."
            ),
            "zero_values": (
                "A zero is not automatically an error; it may be a default, derived field, unused "
                "component property, or disabled feature. Claim an effect only when the active method consumes it."
            ),
        },
        # Identity facts and official links keep attribution answers consistent.
        "rcaide_identity": {
            "project": "RCAIDE-LEADS",
            "organization": "Laboratory for Electric Aircraft Design and Sustainability (LEADS)",
            "institution": "University of Illinois Urbana-Champaign (UIUC)",
            "director": "Professor Matthew Clarke",
            "official_links": {
                "LEADS": "https://www.leadsresearchgroup.com",
                "UIUC_Grainger_Engineering": "https://grainger.illinois.edu",
                "Dr_Matthew_Clarke": "https://grainger.illinois.edu/about/directory/faculty/maclarke",
            },
            "relationship": (
                "The RCAIDE-LEADS version used by this GUI is developed and maintained by "
                "LEADS, with contributions from the broader open-source aerospace community."
            ),
        },
        # Only the tail of a traceback is retained because it usually contains
        # the exception and most relevant stack frames.
        "latest_error": compact_value(error_trace[-MAX_STRING_LENGTH:]),
    }
    # Result objects are summarized separately because they are not stored in
    # the normal project JSON and may contain very large NumPy arrays.
    mission_results = summarize_mission_results(results, query)
    if mission_results is not None:
        context["mission_results"] = mission_results
    if performance_result is not None:
        # Individual Performance-tab calculations use the same bounded context.
        context["performance_result"] = compact_value(performance_result)
    return context
