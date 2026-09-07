import sys
from pathlib import Path

# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

# ============================================================
# AI MODULES
# ============================================================

from survivor_assessment import assess_survivor
from navigation_integration import (
    assessment_to_navigation_record,
)

# ============================================================
# NAVIGATION CORE
# ============================================================

from navigation.navigation_core import (
    drone_position,
    prioritize_survivors,
    a_star,
    calculate_path_distance,
    calculate_path_risk,
)


# ============================================================
# REPRESENTATIVE UNIFIED PERCEPTION
# This is the same validated test scenario used earlier.
# ============================================================

perception = {
    "id": 7,

    # RGB + thermal
    "visual_confidence": 0.88,
    "thermal_confidence": 0.79,
    "fused_confidence": 0.82,
    "fusion_status": "FUSED_UWB_CONCEALED",

    # Audio
    "audio_distress": True,
    "audio_score": 0.236,
    "audio_status": "MEDIUM",
    "audio_cue": "AUDIO_DISTRESS_CUE",

    # UWB radar
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
}


# ============================================================
# 1. AI SURVIVOR ASSESSMENT
# ============================================================

assessment = assess_survivor(
    perception
)


# ============================================================
# 2. CONVERT TO NAVIGATION RECORD
#
# NOTE:
# These are still SIMULATION transform values.
# ============================================================

navigation_record = (
    assessment_to_navigation_record(
        assessment,
        survivor_id="S1",

        drone_grid=(2, 2),
        drone_heading_deg=0.0,
        meters_per_cell=1.0,
    )
)


# ============================================================
# 3. PHASE 6 PRIORITIZATION
# ============================================================

survivors = [
    navigation_record
]

prioritized = prioritize_survivors(
    survivors
)

selected_survivor = prioritized[0]


# ============================================================
# 4. PHASE 3 RISK-AWARE A*
# ============================================================

start = drone_position

goal = tuple(
    selected_survivor["location"]
)

safe_path = a_star(
    start,
    goal,
    risk_aware=True,
)

shortest_path = a_star(
    start,
    goal,
    risk_aware=False,
)


# ============================================================
# 5. RESULTS
# ============================================================

print("\n" + "=" * 75)
print("AI → SURVIVOR PRIORITY → RISK-AWARE NAVIGATION")
print("=" * 75)

print("\n[1] AI SURVIVOR ASSESSMENT")
print("-" * 75)

print(
    f"Target type          : "
    f"{assessment['target_type']}"
)

print(
    f"Assessment confidence: "
    f"{assessment['assessment_confidence']:.3f}"
)

print(
    f"Evidence level       : "
    f"{assessment['evidence_level']}"
)

print(
    f"Evidence              : "
    f"{assessment['evidence']}"
)


print("\n[2] NAVIGATION TARGET")
print("-" * 75)

print(
    f"Survivor ID          : "
    f"{selected_survivor['id']}"
)

print(
    f"Grid location        : "
    f"{selected_survivor['location']}"
)

print(
    f"Detection confidence : "
    f"{selected_survivor['detection_confidence']:.1f}%"
)

print(
    f"Target type          : "
    f"{selected_survivor['target_type']}"
)

print(
    f"Position mode        : "
    f"{selected_survivor['position_mode']}"
)


print("\n[3] PHASE 6 PRIORITY")
print("-" * 75)

print(
    f"Condition score      : "
    f"{selected_survivor['condition_score']:.1f}"
)

print(
    f"Confidence score     : "
    f"{selected_survivor['confidence_score']:.1f}"
)

print(
    f"Accessibility score  : "
    f"{selected_survivor['accessibility_score']:.1f}"
)

print(
    f"Hazard score         : "
    f"{selected_survivor['hazard_score']:.1f}"
)

print(
    f"Distance             : "
    f"{selected_survivor['distance']:.2f}"
)

print(
    f"Distance score       : "
    f"{selected_survivor['distance_score']:.1f}"
)

print(
    f"TOTAL PRIORITY       : "
    f"{selected_survivor['priority_score']:.1f}"
)

print(
    f"FINAL PRIORITY       : "
    f"{selected_survivor['priority']}"
)


print("\n[4] PHASE 3 A*")
print("-" * 75)

print(
    f"Drone position       : "
    f"{start}"
)

print(
    f"Selected target      : "
    f"{goal}"
)

if shortest_path is not None:

    shortest_distance = (
        calculate_path_distance(
            shortest_path
        )
    )

    shortest_risk, _, _ = (
        calculate_path_risk(
            shortest_path
        )
    )

    print(
        f"Shortest path        : "
        f"{shortest_distance:.2f} cells"
    )

    print(
        f"Shortest path risk   : "
        f"{shortest_risk:.2f}"
    )

else:

    print("Shortest path        : NONE")


if safe_path is not None:

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
        f"Risk-aware path      : "
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

else:

    print("Risk-aware path      : NONE")


print("\n[5] FINAL NAVIGATION DECISION")
print("-" * 75)

if safe_path is None:

    print("❌ NO SAFE PATH TO SELECTED SURVIVOR")

else:

    print(
        "✓ SURVIVOR SELECTED BY PRIORITY"
    )

    print(
        "✓ TARGET CONVERTED TO NAVIGATION GRID"
    )

    print(
        "✓ RISK-AWARE A* PATH GENERATED"
    )

    print(
        f"✓ Start              : {start}"
    )

    print(
        f"✓ Goal               : {goal}"
    )

    print(
        f"✓ First waypoint     : {safe_path[0]}"
    )

    if len(safe_path) > 1:
        print(
            f"✓ Next waypoint      : {safe_path[1]}"
        )

    print(
        f"✓ Final waypoint     : "
        f"{safe_path[-1]}"
    )

print("=" * 75)
