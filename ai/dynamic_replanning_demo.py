import sys
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from navigation.navigation_core import (
    a_star,
    calculate_path_distance,
    calculate_path_risk,
    occupancy_grid,
    risk_map,
    MAP_WIDTH,
    MAP_HEIGHT,
    FIRE,
    DEBRIS,
    FLOOD,
    drone_position,
)

# ============================================================
# DYNAMIC REPLANNING DEMO
# ============================================================

TARGET = (9, 4)

print("\n" + "=" * 78)
print("DYNAMIC RISK-AWARE REPLANNING DEMO")
print("=" * 78)

print("\nINITIAL MISSION")
print("-" * 78)

print(f"Drone position : {drone_position}")
print(f"Target         : {TARGET}")

initial_path = a_star(
    drone_position,
    TARGET,
    risk_aware=True,
)

if initial_path is None:
    raise RuntimeError(
        "Initial route could not be generated."
    )

initial_distance = calculate_path_distance(
    initial_path
)

initial_risk, initial_fire, initial_flood = (
    calculate_path_risk(initial_path)
)

print(
    f"Initial path distance : "
    f"{initial_distance:.2f}"
)

print(
    f"Initial path risk     : "
    f"{initial_risk:.2f}"
)

print(
    f"Initial fire cells    : "
    f"{initial_fire}"
)

print(
    f"Initial flood cells   : "
    f"{initial_flood}"
)

print(
    f"Initial path cells    : "
    f"{len(initial_path)}"
)


# ============================================================
# FIND AN INTERNAL ROUTE CELL TO HAZARD
#
# We deliberately choose a cell that is currently on the
# generated route and convert it into a fire hazard.
# ============================================================

route_candidates = [
    cell
    for cell in initial_path[2:-2]
    if occupancy_grid[
        cell[1],
        cell[0]
    ] not in (
        DEBRIS,
        FIRE,
        FLOOD,
    )
]

if not route_candidates:
    raise RuntimeError(
        "Could not find a suitable route cell "
        "for the dynamic hazard simulation."
    )

hazard_cell = route_candidates[
    len(route_candidates) // 2
]


# ============================================================
# DYNAMIC HAZARD DETECTED
# ============================================================

print("\nDYNAMIC EVENT")
print("-" * 78)

print(
    f"⚠ NEW FIRE HAZARD DETECTED "
    f"at {hazard_cell}"
)

x, y = hazard_cell

occupancy_grid[y][x] = FIRE
risk_map[y][x] = 10.0


# ============================================================
# REPLAN
# ============================================================

print("\nREPLANNING")
print("-" * 78)

replanned_path = a_star(
    drone_position,
    TARGET,
    risk_aware=True,
)

if replanned_path is None:

    print(
        "❌ NO SAFE ROUTE AFTER HAZARD UPDATE"
    )

    raise SystemExit(1)


replanned_distance = (
    calculate_path_distance(
        replanned_path
    )
)

replanned_risk, replanned_fire, replanned_flood = (
    calculate_path_risk(
        replanned_path
    )
)


print(
    f"Replanned path distance : "
    f"{replanned_distance:.2f}"
)

print(
    f"Replanned path risk     : "
    f"{replanned_risk:.2f}"
)

print(
    f"Replanned fire cells    : "
    f"{replanned_fire}"
)

print(
    f"Replanned flood cells   : "
    f"{replanned_flood}"
)

print(
    f"Replanned path cells    : "
    f"{len(replanned_path)}"
)


# ============================================================
# VERIFY HAZARD AVOIDANCE
# ============================================================

hazard_in_initial = (
    hazard_cell in initial_path
)

hazard_in_replanned = (
    hazard_cell in replanned_path
)


print("\nREPLANNING RESULT")
print("-" * 78)

print(
    f"Hazard was on original route : "
    f"{hazard_in_initial}"
)

print(
    f"Hazard remains on new route  : "
    f"{hazard_in_replanned}"
)

if (
    hazard_in_initial
    and not hazard_in_replanned
):

    print(
        "\n✓ DYNAMIC HAZARD AVOIDED"
    )

    print(
        "✓ RISK MAP UPDATED"
    )

    print(
        "✓ A* REPLANNED THE ROUTE"
    )

else:

    print(
        "\n⚠ Route did not change as expected."
    )

print(
    f"\nOriginal route   : {initial_path}"
)

print(
    f"Replanned route  : {replanned_path}"
)

print("=" * 78)
