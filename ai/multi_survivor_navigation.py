import sys
from pathlib import Path

# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ============================================================
# AI
# ============================================================

from survivor_assessment import assess_survivor
from navigation_integration import (
    assessment_to_navigation_record,
)

# ============================================================
# NAVIGATION
# ============================================================

from navigation.navigation_core import (
    drone_position,
    prioritize_survivors,
    a_star,
    calculate_path_distance,
    calculate_path_risk,
    occupancy_grid,
    risk_map,
    MAP_WIDTH,
    MAP_HEIGHT,
    DEBRIS,
    FIRE,
    FLOOD,
)


# ============================================================
# HELPER: DERIVE NAVIGATION METADATA
#
# These are engineering heuristics for the prototype.
# They are NOT medical diagnoses.
# ============================================================

def derive_condition(assessment):
    """
    Estimate rescue urgency from sensor evidence.

    Prototype heuristic only.
    """

    audio_distress = bool(
        assessment.get("audio_distress", False)
    )

    uwb_breathing = float(
        assessment.get("uwb_breathing", 0.0) or 0.0
    )

    uwb_micro = float(
        assessment.get("uwb_micro_motion", 0.0) or 0.0
    )

    if audio_distress and (
        uwb_breathing >= 0.75
        or uwb_micro >= 0.80
    ):
        return "CRITICAL"

    if (
        uwb_breathing >= 0.60
        or uwb_micro >= 0.65
    ):
        return "SERIOUS"

    if (
        uwb_breathing >= 0.40
        or uwb_micro >= 0.45
    ):
        return "MODERATE"

    return "STABLE"


def derive_hazard(location):
    """
    Derive target-cell hazard from the navigation risk map.
    """

    if location is None:
        return "HIGH"

    x, y = location

    if not (
        0 <= x < MAP_WIDTH
        and 0 <= y < MAP_HEIGHT
    ):
        return "HIGH"

    cell_risk = float(
        risk_map[y][x]
    )

    if (
        occupancy_grid[y][x] == FIRE
        or cell_risk >= 10
    ):
        return "HIGH"

    if (
        occupancy_grid[y][x] == FLOOD
        or cell_risk >= 5
    ):
        return "MEDIUM"

    return "LOW"


def derive_accessibility(location):
    """
    Estimate accessibility using the existing occupancy map.

    Prototype:
        blocked/debris -> INACCESSIBLE
        otherwise      -> ACCESSIBLE
    """

    if location is None:
        return "INACCESSIBLE"

    x, y = location

    if not (
        0 <= x < MAP_WIDTH
        and 0 <= y < MAP_HEIGHT
    ):
        return "INACCESSIBLE"

    if occupancy_grid[y][x] == DEBRIS:
        return "INACCESSIBLE"

    return "ACCESSIBLE"


# ============================================================
# CREATE FINAL NAVIGATION RECORD
# ============================================================

def build_navigation_record(
    perception,
    survivor_id,
    drone_grid=(2, 2),
    drone_heading_deg=0.0,
    meters_per_cell=1.0,
):

    assessment = assess_survivor(
        perception
    )

    record = assessment_to_navigation_record(
        assessment,
        survivor_id=survivor_id,
        drone_grid=drone_grid,
        drone_heading_deg=drone_heading_deg,
        meters_per_cell=meters_per_cell,
        perception=perception,
    )

    location = record.get(
        "location"
    )

    record["condition"] = (
        derive_condition(
            perception
        )
    )

    record["hazard"] = (
        derive_hazard(
            location
        )
    )

    record["accessibility"] = (
        derive_accessibility(
            location
        )
    )

    record["assessment"] = assessment

    return record


# ============================================================
# THREE SIMULATED SURVIVORS
#
# These represent different sensor situations.
# The coordinates are still simulation transforms.
# ============================================================

PERCEPTIONS = [
    (
        "S1",
        {
            "id": 101,

            "visual_confidence": 0.92,
            "thermal_confidence": 0.86,
            "fused_confidence": 0.89,
            "fusion_status": "FUSED_UWB_CONCEALED",

            "audio_distress": False,
            "audio_score": 0.02,
            "audio_status": "LOW",
            "audio_cue": None,

            "uwb_detected": True,
            "uwb_confidence": 0.91,
            "uwb_range_m": 8.0,
            "uwb_angle_deg": -20.0,
            "uwb_micro_motion": 0.86,
            "uwb_breathing": 0.81,
            "uwb_signal_quality": 0.92,
            "uwb_concealed": True,

            "uwb_relative_position": {
                "x_m": 7.52,
                "y_m": -2.74,
            },

            "uwb_target_type": "CONCEALED_SURVIVOR",
        },
    ),

    (
        "S2",
        {
            "id": 102,

            "visual_confidence": 0.88,
            "thermal_confidence": 0.80,
            "fused_confidence": 0.84,
            "fusion_status": "FUSED_UWB_CONCEALED",

            "audio_distress": True,
            "audio_score": 0.236,
            "audio_status": "MEDIUM",
            "audio_cue": "AUDIO_DISTRESS_CUE",

            "uwb_detected": True,
            "uwb_confidence": 0.87,
            "uwb_range_m": 6.8,
            "uwb_angle_deg": 14.0,
            "uwb_micro_motion": 0.91,
            "uwb_breathing": 0.84,
            "uwb_signal_quality": 0.89,
            "uwb_concealed": True,

            "uwb_relative_position": {
                "x_m": 6.6,
                "y_m": 1.65,
            },

            "uwb_target_type": "CONCEALED_SURVIVOR",
        },
    ),

    (
        "S3",
        {
            "id": 103,

            "visual_confidence": 0.74,
            "thermal_confidence": 0.68,
            "fused_confidence": 0.71,
            "fusion_status": "FUSED_UWB_CONCEALED",

            "audio_distress": False,
            "audio_score": 0.01,
            "audio_status": "LOW",
            "audio_cue": None,

            "uwb_detected": True,
            "uwb_confidence": 0.68,
            "uwb_range_m": 11.0,
            "uwb_angle_deg": 38.0,
            "uwb_micro_motion": 0.58,
            "uwb_breathing": 0.49,
            "uwb_signal_quality": 0.80,
            "uwb_concealed": True,

            "uwb_relative_position": {
                "x_m": 8.66,
                "y_m": 6.77,
            },

            "uwb_target_type": "CONCEALED_SURVIVOR",
        },
    ),
]


# ============================================================
# BUILD RECORDS
# ============================================================

navigation_records = []

for survivor_id, perception in PERCEPTIONS:

    record = build_navigation_record(
        perception,
        survivor_id=survivor_id,

        # Simulation only
        drone_grid=(2, 2),
        drone_heading_deg=0.0,
        meters_per_cell=1.0,
    )

    navigation_records.append(
        record
    )


# ============================================================
# VALIDATE NAVIGATION TARGETS
# ============================================================

valid_records = []
invalid_records = []

for record in navigation_records:

    location = record.get("location")

    if location is None:
        invalid_records.append(record)
        continue

    x, y = location

    if not (
        0 <= x < MAP_WIDTH
        and 0 <= y < MAP_HEIGHT
    ):
        invalid_records.append(record)
        continue

    valid_records.append(record)


print("\nNAVIGATION TARGET VALIDATION")
print("-" * 78)

for record in invalid_records:

    print(
        f"⚠ {record['id']} rejected for navigation: "
        f"location={record.get('location')}"
    )

print(
    f"Valid navigation targets   : "
    f"{len(valid_records)}"
)

print(
    f"Invalid/unmapped targets    : "
    f"{len(invalid_records)}"
)


# ============================================================
# PHASE 6 - PRIORITIZATION
# ============================================================

if not valid_records:

    raise RuntimeError(
        "No valid localized survivor targets available."
    )

prioritized = prioritize_survivors(
    valid_records
)


# ============================================================
# DISPLAY PRIORITY QUEUE
# ============================================================

print("\n" + "=" * 78)
print("MULTI-SURVIVOR AI → PRIORITY → NAVIGATION")
print("=" * 78)

print("\nSURVIVOR DETECTIONS")
print("-" * 78)

for survivor in prioritized:

    assessment = survivor[
        "assessment"
    ]

    print(
        f"{survivor['id']}: "
        f"{survivor['target_type']} | "
        f"Grid={survivor['location']} | "
        f"Confidence={survivor['detection_confidence']:.1f}% | "
        f"Condition={survivor['condition']} | "
        f"Hazard={survivor['hazard']} | "
        f"Accessibility={survivor['accessibility']} | "
        f"Evidence={assessment['evidence_level']}"
    )


print("\nPRIORITY QUEUE")
print("-" * 78)

for rank, survivor in enumerate(
    prioritized,
    start=1,
):

    print(
        f"{rank}. "
        f"{survivor['id']} → "
        f"{survivor['priority']} | "
        f"Score={survivor['priority_score']:.1f} | "
        f"Location={survivor['location']}"
    )


# ============================================================
# SELECT HIGHEST PRIORITY
# ============================================================

selected = prioritized[0]

start = drone_position

goal = tuple(
    selected["location"]
)


print("\nSELECTED RESCUE TARGET")
print("-" * 78)

print(
    f"Target               : "
    f"{selected['id']}"
)

print(
    f"Priority             : "
    f"{selected['priority']}"
)

print(
    f"Priority score       : "
    f"{selected['priority_score']:.1f}"
)

print(
    f"Condition            : "
    f"{selected['condition']}"
)

print(
    f"Detection confidence : "
    f"{selected['detection_confidence']:.1f}%"
)

print(
    f"Grid location        : "
    f"{goal}"
)


# ============================================================
# PHASE 3 - A*
# ============================================================

shortest_path = a_star(
    start,
    goal,
    risk_aware=False,
)

safe_path = a_star(
    start,
    goal,
    risk_aware=True,
)


print("\nNAVIGATION")
print("-" * 78)

print(
    f"Drone start          : "
    f"{start}"
)

print(
    f"Target               : "
    f"{goal}"
)


if safe_path is None:

    print(
        "❌ No safe route found."
    )

else:

    safe_distance = (
        calculate_path_distance(
            safe_path
        )
    )

    safe_risk, fire, flood = (
        calculate_path_risk(
            safe_path
        )
    )

    print(
        f"Risk-aware distance  : "
        f"{safe_distance:.2f} cells"
    )

    print(
        f"Risk-aware risk      : "
        f"{safe_risk:.2f}"
    )

    print(
        f"Fire cells           : "
        f"{fire}"
    )

    print(
        f"Flood cells          : "
        f"{flood}"
    )

    print(
        f"Path cells           : "
        f"{len(safe_path)}"
    )

    print(
        f"First waypoint       : "
        f"{safe_path[0]}"
    )

    if len(safe_path) > 1:

        print(
            f"Next waypoint        : "
            f"{safe_path[1]}"
        )

    print(
        f"Final waypoint       : "
        f"{safe_path[-1]}"
    )


print("\n" + "=" * 78)
print("MULTI-SURVIVOR PIPELINE COMPLETE")
print("=" * 78)
