"""Pure classroom-level calculations shared by learner-mode tabs."""

from __future__ import annotations

from math import exp, sqrt


# Shared assumptions are deliberately visible and centralized.  These values
# support trend-based classroom activities; they are not certification inputs.
GRAVITY = 9.80665
SEA_LEVEL_DENSITY = 1.225
ASSUMED_MAX_LIFT_COEFFICIENT = 1.5
ASSUMED_EMPTY_WEIGHT_FRACTION = 0.60
ASSUMED_PERSON_MASS_KG = 85.0


def classroom_metrics(data):
    """Compute transparent first-order aircraft metrics from learner inputs.

    The equations intentionally trade fidelity for readability.  They are used
    to teach relationships such as weight versus wing area and speed versus
    stall margin; the RCAIDE mission solver remains responsible for simulation.
    """
    vehicle = data["vehicle"]
    wing = data["wing"]
    stabilizers = data["stabilizers"]
    mission = data["mission"]

    mass = float(vehicle["max_takeoff_weight_kg"])
    area = float(vehicle["reference_area_m2"])
    span = float(wing["span_m"])
    altitude = float(mission["altitude_m"])
    speed = float(mission["speed_m_s"])
    distance = float(mission["distance_km"])
    # Use a simple exponential atmosphere so altitude visibly affects the stall
    # estimate without exposing a full atmosphere model in learner activities.
    density = SEA_LEVEL_DENSITY * exp(-altitude / 8500.0)

    # Wing loading compares supported mass with available lifting area, while
    # aspect ratio describes whether the wing is short/broad or long/narrow.
    wing_loading = mass / area
    aspect_ratio = span ** 2 / area
    # Rearrange the introductory lift equation at the assumed maximum lift
    # coefficient to estimate the lowest sustainable speed.
    stall_speed = sqrt(
        2.0 * mass * GRAVITY
        / (density * area * ASSUMED_MAX_LIFT_COEFFICIENT)
    )
    cruise_hours = distance / (speed * 3.6)
    horizontal_tail_ratio = float(stabilizers["horizontal_area_m2"]) / area
    vertical_tail_ratio = float(stabilizers["vertical_area_m2"]) / area

    # These broad teaching bands flag unusual choices and suggest design trends;
    # they are not regulatory limits or a certified stability assessment.
    warnings = []
    if speed < 1.3 * stall_speed:
        warnings.append("Cruise speed is too close to the estimated stall speed.")
    if wing_loading > 120:
        warnings.append("High wing loading: this aircraft may need to fly faster.")
    elif wing_loading < 25:
        warnings.append("Very low wing loading: expect a slow, glider-like aircraft.")
    if not 0.15 <= horizontal_tail_ratio <= 0.35:
        warnings.append("Horizontal-tail area is unusual for a basic conventional aircraft.")
    if not 0.07 <= vertical_tail_ratio <= 0.20:
        warnings.append("Vertical-tail area is unusual for a basic conventional aircraft.")

    return {
        "wing_loading_kg_m2": wing_loading,
        "aspect_ratio": aspect_ratio,
        "stall_speed_m_s": stall_speed,
        "cruise_time_hours": cruise_hours,
        "lift_required_n": mass * GRAVITY,
        "air_density_kg_m3": density,
        "horizontal_tail_ratio": horizontal_tail_ratio,
        "vertical_tail_ratio": vertical_tail_ratio,
        "cruise_stall_margin": speed / stall_speed,
        "warnings": warnings,
    }


def classroom_loading(data, passengers, cargo_kg, fuel_kg):
    """Estimate loaded mass and an illustrative longitudinal balance point."""
    # Learner Setup does not define a detailed weight breakdown, so empty mass
    # and per-person mass come from the explicit assumptions above.
    mtow = float(data["vehicle"]["max_takeoff_weight_kg"])
    empty = ASSUMED_EMPTY_WEIGHT_FRACTION * mtow
    people = int(passengers) * ASSUMED_PERSON_MASS_KG
    total = empty + people + float(cargo_kg) + float(fuel_kg)
    # Stations are fractions of fuselage length, used for an introductory
    # balance illustration rather than a certifiable aerodynamic CG.
    moment = empty * 0.40 + people * 0.48 + float(cargo_kg) * 0.65 + float(fuel_kg) * 0.42
    balance = moment / total if total else 0.0
    # Report the most important loading problem first: excess total mass takes
    # priority over the illustrative nose/tail balance classification.
    if total > mtow:
        status = "Over maximum takeoff weight"
    elif balance < 0.35:
        status = "Nose heavy"
    elif balance > 0.52:
        status = "Tail heavy"
    else:
        status = "Balanced loading zone"
    return {
        "empty_mass_kg": empty,
        "people_mass_kg": people,
        "total_mass_kg": total,
        "remaining_mass_kg": mtow - total,
        "balance_fraction": balance,
        "status": status,
    }


# Each challenge contains a display name, learner-facing goal, pure pass rule,
# and actionable retry hint.  Keeping rules data-driven avoids duplicating the
# challenge UI for every lesson.
CHALLENGES = (
    (
        "Family Vacation",
        "Make room for four people and travel at least 500 kilometers.",
        lambda d, m: d["vehicle"]["passengers"] >= 4 and d["mission"]["distance_km"] >= 500,
        "Add enough seats for four people and choose a trip of 500 km or more.",
    ),
    (
        "Slow and Steady",
        "Build a plane that can stay up without needing lots of speed.",
        lambda d, m: m["wing_loading_kg_m2"] <= 70,
        "Try a larger wing or make the airplane lighter.",
    ),
    (
        "Long-Wing Explorer",
        "Use a long, narrow wing like a glider or soaring bird.",
        lambda d, m: m["aspect_ratio"] >= 8,
        "Increase the wingtip-to-wingtip span without making the wing area much larger.",
    ),
    (
        "Comfortable Cruise",
        "Choose a travel speed with a comfortable cushion above the too-slow danger zone.",
        lambda d, m: m["cruise_stall_margin"] >= 1.3,
        "Choose a faster travel speed, make the wing larger, or make the airplane lighter.",
    ),
    (
        "Steady Tail",
        "Give the plane enough horizontal and upright tail surface to help it point steadily.",
        lambda d, m: (
            0.15 <= m["horizontal_tail_ratio"] <= 0.35
            and 0.07 <= m["vertical_tail_ratio"] <= 0.20
        ),
        "Try a horizontal tail about one-fifth of the main wing and an upright tail about one-tenth.",
    ),
)


def evaluate_challenges(data):
    """Evaluate every guided design challenge against one metric snapshot."""
    # Calculate the shared metrics once so all challenge rules judge the same
    # version of the aircraft inputs.
    metrics = classroom_metrics(data)
    return [
        {
            "name": name,
            "description": description,
            "passed": bool(rule(data, metrics)),
            "tip": tip,
        }
        for name, description, rule, tip in CHALLENGES
    ]


def describe_design(data):
    """Turn classroom metrics into a short, child-friendly design story."""
    metrics = classroom_metrics(data)
    # Add a modest margin above estimated stall speed before calling a speed
    # comfortable; this is a teaching heuristic rather than an operating limit.
    safe_speed_kmh = metrics["stall_speed_m_s"] * 3.6 * 1.2
    # Choose one memorable personality from the strongest visible design trend.
    if metrics["wing_loading_kg_m2"] < 45:
        personality = "Gentle, slow flyer"
    elif safe_speed_kmh > 170:
        personality = "Fast flyer"
    elif metrics["aspect_ratio"] >= 9:
        personality = "Long-wing explorer"
    else:
        personality = "Everyday trainer"

    # "Best for" connects capacity, range, and wing loading to a relatable use.
    if data["vehicle"]["passengers"] >= 6:
        best_for = "Carrying a group"
    elif data["mission"]["distance_km"] >= 500:
        best_for = "Long trips"
    elif metrics["wing_loading_kg_m2"] < 55:
        best_for = "Slow sightseeing"
    else:
        best_for = "Learning to fly"
    return {
        "comfortable_speed_kmh": safe_speed_kmh,
        "trip_minutes": metrics["cruise_time_hours"] * 60,
        "personality": personality,
        "best_for": best_for,
    }
