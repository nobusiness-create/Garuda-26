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

# ============================================================
# NAVIGATION
# ============================================================

from navigation.navigation_core import (
    a_star,
    calculate_path_risk,
    calculate_path_distance,
    drone_position,
)

# ============================================================
# FLIGHT CONTROL
# ============================================================

from navigation.flight_control import (
    adaptive_flight_controller,
)


# ============================================================
# CURRENT SIMULATED PERCEPTION
#
# This is the same validated concealed-survivor scenario
# we've been using throughout the integration.
# ============================================================

perception = {
    "id": 7,

    # RGB
    "visual_confidence": 0.88,

    # Thermal
    "thermal_confidence": 0.79,
    "fused_confidence": 0.82,
    "fusion_status": "FUSED_UWB_CONCEALED",

    # Audio
    "audio_distress": True,
    "audio_score": 0.236,
    "audio_status": "MEDIUM",
    "audio_cue": "AUDIO_DISTRESS_CUE",

    # UWB
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
# 1. SURVIVOR ASSESSMENT
# ============================================================

assessment = assess_survivor(
    perception
)

survivor_probability = float(
    assessment[
        "assessment_confidence"
    ]
)


# ============================================================
# 2. TARGET POSITION
#
# Simulation transform:
# drone = (2,2)
# heading = 0°
# scale = 1 m/cell
# ============================================================

relative_position = (
    perception[
        "uwb_relative_position"
    ]
)

target_x = round(
    drone_position[0]
    + relative_position["x_m"]
)

target_y = round(
    drone_position[1]
    + relative_position["y_m"]
)

target = (
    target_x,
    target_y,
)


# ============================================================
# 3. NAVIGATION PATH
# ============================================================

path = a_star(
    drone_position,
    target,
    risk_aware=True,
)

if path is None:

    print(
        "ERROR: No navigation path found."
    )

    raise SystemExit(1)


path_distance = (
    calculate_path_distance(
        path
    )
)

path_risk, fire_cells, flood_cells = (
    calculate_path_risk(
        path
    )
)


# ============================================================
# 4. CONVERT NAVIGATION RISK → OBSTACLE LEVEL
#
# This is only a prototype mapping.
#
# 0 risk   → 0.0
# 5 risk   → 0.3
# 10 risk  → 0.6
# 100 risk → 1.0
# ============================================================

if path_risk <= 0:
    obstacle_level = 0.0

elif path_risk <= 5:
    obstacle_level = 0.3

elif path_risk <= 10:
    obstacle_level = 0.6

else:
    obstacle_level = 1.0


# ============================================================
# 5. SIMULATED VEHICLE STATE
#
# These values will eventually come from MAVLink.
# ============================================================

battery_percent = 75.0
current_speed = 3.0
current_altitude = 20.0


# ============================================================
# 6. ADAPTIVE FLIGHT CONTROL
# ============================================================

flight = adaptive_flight_controller(
    survivor_probability=survivor_probability,
    obstacle_level=obstacle_level,
    battery_percent=battery_percent,
    current_speed=current_speed,
    current_altitude=current_altitude,
)


# ============================================================
# 7. DISPLAY
# ============================================================

print("\n" + "=" * 78)
print("AI → NAVIGATION → ADAPTIVE FLIGHT CONTROL")
print("=" * 78)

print("\nSURVIVOR ASSESSMENT")
print("-" * 78)

print(
    f"Target type          : "
    f"{assessment['target_type']}"
)

print(
    f"Survivor probability : "
    f"{survivor_probability:.3f}"
)

print(
    f"Evidence level       : "
    f"{assessment['evidence_level']}"
)

print(
    f"Evidence              : "
    f"{assessment['evidence']}"
)


print("\nNAVIGATION")
print("-" * 78)

print(
    f"Drone position       : "
    f"{drone_position}"
)

print(
    f"Target position      : "
    f"{target}"
)

print(
    f"Path distance        : "
    f"{path_distance:.2f} cells"
)

print(
    f"Path risk            : "
    f"{path_risk:.2f}"
)

print(
    f"Fire cells           : "
    f"{fire_cells}"
)

print(
    f"Flood cells          : "
    f"{flood_cells}"
)

print(
    f"Obstacle level       : "
    f"{obstacle_level:.2f}"
)


print("\nCURRENT VEHICLE STATE")
print("-" * 78)

print(
    f"Battery              : "
    f"{battery_percent:.1f}%"
)

print(
    f"Current speed        : "
    f"{current_speed:.2f} m/s"
)

print(
    f"Current altitude     : "
    f"{current_altitude:.2f} m"
)


print("\nADAPTIVE SPEED CONTROL")
print("-" * 78)

print(
    f"Target speed         : "
    f"{flight['speed']['target_speed_mps']:.2f} m/s"
)

print(
    f"Action               : "
    f"{flight['speed']['action']}"
)


print("\nADAPTIVE ALTITUDE CONTROL")
print("-" * 78)

print(
    f"Target altitude      : "
    f"{flight['altitude']['target_altitude_m']:.2f} m"
)

print(
    f"Action               : "
    f"{flight['altitude']['action']}"
)


print("\nMISSION DECISION")
print("-" * 78)

print(
    f"Overall action       : "
    f"{flight['mission_action']}"
)

print("\n✓ Survivor assessment connected")
print("✓ Navigation connected")
print("✓ Adaptive speed connected")
print("✓ Adaptive altitude connected")
print("✓ Flight-control decision generated")

print("=" * 78)
