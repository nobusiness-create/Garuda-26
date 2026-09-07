import sys
import os
import math
import heapq
import matplotlib.pyplot as plt


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# IMPORT ENVIRONMENT
# ============================================================

from phase2.main import (
    occupancy_grid,
    MAP_WIDTH,
    MAP_HEIGHT,
    DEBRIS,
    FIRE,
    FLOOD,
    drone_position
)


# ============================================================
# PHASE 9
# SAFETY & FAIL-SAFE MANAGEMENT
# ============================================================

print("=" * 70)
print("PHASE 9 - SAFETY & FAIL-SAFE MANAGEMENT")
print("=" * 70)


# ============================================================
# MISSION PARAMETERS
# ============================================================

START_POSITION = drone_position

current_position = START_POSITION

BASE_POSITION = START_POSITION

BATTERY_CAPACITY = 100.0

battery_level = BATTERY_CAPACITY

BATTERY_WARNING = 40.0

BATTERY_CRITICAL = 20.0


# ============================================================
# SAFETY STATES
# ============================================================

NORMAL = "NORMAL"

WARNING = "WARNING"

EMERGENCY = "EMERGENCY"

RETURN_TO_BASE = "RETURN TO BASE"

MISSION_ABORT = "MISSION ABORT"


safety_state = NORMAL


# ============================================================
# SENSOR STATUS
# ============================================================

sensor_status = {
    "GPS": True,
    "CAMERA": True,
    "THERMAL": True,
    "IMU": True,
    "OBSTACLE_SENSOR": True
}


# ============================================================
# SIMULATED SURVIVOR
# ============================================================

survivor = {
    "id": "S1",
    "position": (26, 26),
    "priority": "HIGH"
}


TARGET_POSITION = survivor["position"]


# ============================================================
# MISSION VARIABLES
# ============================================================

flight_path = []

safety_events = []

emergency_triggered = False

mission_success = False

total_distance = 0.0

mission_step = 0


# ============================================================
# BLOCKED CELLS
# ============================================================

blocked_cells = {
    DEBRIS,
    FIRE,
    FLOOD
}


# ============================================================
# A* PATH PLANNER
# ============================================================

def calculate_safe_path(start, goal, grid):

    height, width = grid.shape

    directions = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),

        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1)
    ]

    def heuristic(a, b):

        return math.sqrt(
            (a[0] - b[0]) ** 2 +
            (a[1] - b[1]) ** 2
        )

    def movement_cost(current, neighbor):

        x, y = neighbor

        if grid[y, x] in blocked_cells:
            return float("inf")

        if (
            current[0] != neighbor[0]
            and current[1] != neighbor[1]
        ):
            return math.sqrt(2)

        return 1.0

    open_set = []

    heapq.heappush(
        open_set,
        (
            heuristic(start, goal),
            start
        )
    )

    came_from = {}

    g_score = {
        start: 0.0
    }

    while open_set:

        _, current = heapq.heappop(open_set)

        if current == goal:

            path = []

            while current in came_from:

                path.append(current)

                current = came_from[current]

            path.append(start)

            path.reverse()

            return path

        current_x, current_y = current

        for dx, dy in directions:

            nx = current_x + dx
            ny = current_y + dy

            if nx < 0 or nx >= width:
                continue

            if ny < 0 or ny >= height:
                continue

            neighbor = (nx, ny)

            cost = movement_cost(
                current,
                neighbor
            )

            if cost == float("inf"):
                continue

            tentative_g = (
                g_score[current]
                + cost
            )

            if (
                neighbor not in g_score
                or tentative_g < g_score[neighbor]
            ):

                came_from[neighbor] = current

                g_score[neighbor] = tentative_g

                f_score = (
                    tentative_g
                    + heuristic(
                        neighbor,
                        goal
                    )
                )

                heapq.heappush(
                    open_set,
                    (
                        f_score,
                        neighbor
                    )
                )

    return None


# ============================================================
# DISTANCE FUNCTION
# ============================================================

def distance_between(a, b):

    return math.sqrt(
        (b[0] - a[0]) ** 2
        +
        (b[1] - a[1]) ** 2
    )


# ============================================================
# SAFETY EVENT LOGGER
# ============================================================

def log_safety_event(
    event_type,
    description
):

    safety_events.append(
        {
            "step": mission_step,
            "position": current_position,
            "type": event_type,
            "description": description
        }
    )

    print("\n" + "!" * 70)

    print(
        f"SAFETY EVENT: {event_type}"
    )

    print(
        f"Position: {current_position}"
    )

    print(
        f"Description: {description}"
    )

    print("!" * 70)


# ============================================================
# INITIAL SAFETY CHECK
# ============================================================

print("\nINITIAL SAFETY CHECK")
print("-" * 70)

print(
    f"Battery level : "
    f"{battery_level:.1f}%"
)

print(
    f"GPS           : "
    f"{sensor_status['GPS']}"
)

print(
    f"Camera        : "
    f"{sensor_status['CAMERA']}"
)

print(
    f"Thermal       : "
    f"{sensor_status['THERMAL']}"
)

print(
    f"IMU           : "
    f"{sensor_status['IMU']}"
)

print(
    f"Obstacle      : "
    f"{sensor_status['OBSTACLE_SENSOR']}"
)

print(
    "\n✓ All critical systems operational"
)


# ============================================================
# INITIAL ROUTE
# ============================================================

route = calculate_safe_path(
    current_position,
    TARGET_POSITION,
    occupancy_grid
)

if route is None:

    print(
        "\n❌ No safe route to survivor."
    )

    sys.exit()


print("\nMISSION ROUTE")
print("-" * 70)

print(
    f"Start  : {current_position}"
)

print(
    f"Target : {TARGET_POSITION}"
)

print(
    f"Waypoints : {len(route)}"
)


# ============================================================
# AUTONOMOUS FLIGHT
# ============================================================

print("\n" + "=" * 70)
print("AUTONOMOUS FLIGHT STARTED")
print("=" * 70)


route_index = 0


while current_position != TARGET_POSITION:

    mission_step += 1

    # --------------------------------------------------------
    # SAFETY MONITOR
    # --------------------------------------------------------

    print(
        f"\n[SAFETY] Step {mission_step}"
    )

    print(
        f"[SAFETY] Position: "
        f"{current_position}"
    )

    print(
        f"[SAFETY] Battery: "
        f"{battery_level:.1f}%"
    )

    # --------------------------------------------------------
    # BATTERY CONSUMPTION
    # --------------------------------------------------------

    battery_level -= 1.0

    # --------------------------------------------------------
    # BATTERY WARNING
    # --------------------------------------------------------

    if (
        battery_level <= BATTERY_WARNING
        and safety_state == NORMAL
    ):

        safety_state = WARNING

        log_safety_event(
            "LOW BATTERY WARNING",
            "Battery below safety threshold."
        )

        print(
            "⚠ Continuing mission under "
            "battery monitoring."
        )

    # --------------------------------------------------------
    # SIMULATED CRITICAL FAILURE
    # --------------------------------------------------------

    if mission_step == 15:

        sensor_status["GPS"] = False

        emergency_triggered = True

        safety_state = EMERGENCY

        log_safety_event(
            "GPS FAILURE",
            "GPS signal lost during autonomous flight."
        )

        print(
            "⚠ GPS unavailable."
        )

        print(
            "🧠 Switching to fail-safe navigation."
        )

        # ----------------------------------------------------
        # FAIL-SAFE DECISION
        # ----------------------------------------------------

        safety_state = RETURN_TO_BASE

        print(
            "\nFAIL-SAFE DECISION"
        )

        print(
            "→ Mission objective suspended."
        )

        print(
            "→ Survivor approach cancelled."
        )

        print(
            "→ Return-to-base procedure activated."
        )

        # ----------------------------------------------------
        # RETURN ROUTE
        # ----------------------------------------------------

        return_route = calculate_safe_path(
            current_position,
            BASE_POSITION,
            occupancy_grid
        )

        if return_route is None:

            safety_state = MISSION_ABORT

            log_safety_event(
                "RETURN ROUTE FAILURE",
                "Unable to calculate safe route to base."
            )

            print(
                "❌ MISSION ABORTED"
            )

            break

        print(
            f"✓ Return route generated."
        )

        print(
            f"✓ Return waypoints: "
            f"{len(return_route)}"
        )

        route = return_route

        route_index = 0

    # --------------------------------------------------------
    # GET NEXT WAYPOINT
    # --------------------------------------------------------

    if current_position not in route:

        new_route = calculate_safe_path(
            current_position,
            BASE_POSITION
            if safety_state == RETURN_TO_BASE
            else TARGET_POSITION,
            occupancy_grid
        )

        if new_route is None:

            safety_state = MISSION_ABORT

            log_safety_event(
                "ROUTE FAILURE",
                "No safe route available."
            )

            break

        route = new_route

    current_index = route.index(
        current_position
    )

    if current_index + 1 >= len(route):

        break

    next_position = route[
        current_index + 1
    ]

    # --------------------------------------------------------
    # SAFETY CHECK NEXT CELL
    # --------------------------------------------------------

    if (
        occupancy_grid[
            next_position[1],
            next_position[0]
        ]
        in blocked_cells
    ):

        log_safety_event(
            "OBSTACLE DETECTED",
            f"Unsafe waypoint detected: "
            f"{next_position}"
        )

        destination = (
            BASE_POSITION
            if safety_state == RETURN_TO_BASE
            else TARGET_POSITION
        )

        new_route = calculate_safe_path(
            current_position,
            destination,
            occupancy_grid
        )

        if new_route is None:

            safety_state = MISSION_ABORT

            print(
                "❌ No safe alternative."
            )

            break

        route = new_route

        print(
            "✓ Safe route recalculated."
        )

        continue

    # --------------------------------------------------------
    # MOVE
    # --------------------------------------------------------

    movement = distance_between(
        current_position,
        next_position
    )

    total_distance += movement

    current_position = next_position

    flight_path.append(
        current_position
    )

    print(
        f"🚁 Drone → "
        f"{current_position}"
    )

    # --------------------------------------------------------
    # RETURN-TO-BASE COMPLETION
    # --------------------------------------------------------

    if (
        safety_state == RETURN_TO_BASE
        and current_position == BASE_POSITION
    ):

        print("\n" + "-" * 70)

        print(
            "✓ DRONE SUCCESSFULLY RETURNED TO BASE"
        )

        print(
            "✓ EMERGENCY PROCEDURE COMPLETED"
        )

        print(
            "✓ AIRCRAFT PRESERVED"
        )

        break


# ============================================================
# FINAL MISSION STATUS
# ============================================================

if (
    safety_state == RETURN_TO_BASE
    and current_position == BASE_POSITION
):

    mission_success = True

elif current_position == TARGET_POSITION:

    mission_success = True

else:

    mission_success = False


# ============================================================
# FINAL REPORT
# ============================================================

print("\n" + "=" * 70)
print("PHASE 9 - SAFETY & FAIL-SAFE REPORT")
print("=" * 70)

print(
    f"Initial position       : "
    f"{START_POSITION}"
)

print(
    f"Final position         : "
    f"{current_position}"
)

print(
    f"Final battery          : "
    f"{battery_level:.1f}%"
)

print(
    f"Safety state            : "
    f"{safety_state}"
)

print(
    f"Emergency triggered     : "
    f"{emergency_triggered}"
)

print(
    f"Safety events           : "
    f"{len(safety_events)}"
)

print(
    f"Flight distance         : "
    f"{total_distance:.2f} units"
)

print(
    f"Mission success         : "
    f"{mission_success}"
)


# ============================================================
# SAFETY EVENT REPORT
# ============================================================

print("\nSAFETY EVENT LOG")
print("-" * 70)

for index, event in enumerate(
    safety_events,
    start=1
):

    print(
        f"\nEvent #{index}"
    )

    print(
        f"Type        : "
        f"{event['type']}"
    )

    print(
        f"Step        : "
        f"{event['step']}"
    )

    print(
        f"Position    : "
        f"{event['position']}"
    )

    print(
        f"Description : "
        f"{event['description']}"
    )


# ============================================================
# PHASE 9 RESULT
# ============================================================

print("\n" + "=" * 70)
print("PHASE 9 RESULT")
print("=" * 70)

if (
    emergency_triggered
    and safety_state == RETURN_TO_BASE
    and current_position == BASE_POSITION
):

    print(
        "✓ SAFETY MONITORING SUCCESSFUL"
    )

    print(
        "✓ FAILURE CONDITION DETECTED"
    )

    print(
        "✓ FAIL-SAFE LOGIC ACTIVATED"
    )

    print(
        "✓ MISSION OBJECTIVE SAFELY SUSPENDED"
    )

    print(
        "✓ RETURN-TO-BASE EXECUTED"
    )

    print(
        "✓ DRONE SAFELY RECOVERED"
    )

else:

    print(
        "✗ FAIL-SAFE TEST NOT TRIGGERED"
    )

    print(
        "✗ Safety failure scenario was not executed."
    )
print("=" * 70)


# ============================================================
# VISUALIZATION
# ============================================================

print(
    "\nGenerating Phase 9 visualization..."
)


fig, ax = plt.subplots(
    figsize=(12, 10)
)


# ============================================================
# ENVIRONMENT
# ============================================================

free_mask = occupancy_grid == 0

ax.imshow(
    free_mask,
    cmap="Greys",
    origin="lower",
    extent=[
        0,
        MAP_WIDTH,
        0,
        MAP_HEIGHT
    ],
    alpha=0.10
)


debris_mask = occupancy_grid == DEBRIS

ax.imshow(
    debris_mask,
    cmap="Greys",
    origin="lower",
    extent=[
        0,
        MAP_WIDTH,
        0,
        MAP_HEIGHT
    ],
    alpha=0.70
)


fire_mask = occupancy_grid == FIRE

ax.imshow(
    fire_mask,
    cmap="Reds",
    origin="lower",
    extent=[
        0,
        MAP_WIDTH,
        0,
        MAP_HEIGHT
    ],
    alpha=0.60
)


flood_mask = occupancy_grid == FLOOD

ax.imshow(
    flood_mask,
    cmap="Blues",
    origin="lower",
    extent=[
        0,
        MAP_WIDTH,
        0,
        MAP_HEIGHT
    ],
    alpha=0.60
)


# ============================================================
# FLIGHT PATH
# ============================================================

if flight_path:

    x_values = [
        point[0]
        for point in flight_path
    ]

    y_values = [
        point[1]
        for point in flight_path
    ]

    x_values.insert(
        0,
        START_POSITION[0]
    )

    y_values.insert(
        0,
        START_POSITION[1]
    )

    ax.plot(
        x_values,
        y_values,
        linewidth=3,
        label="Drone Flight Path",
        zorder=5
    )


# ============================================================
# START / BASE
# ============================================================

ax.scatter(
    START_POSITION[0],
    START_POSITION[1],
    marker="^",
    s=300,
    edgecolors="black",
    linewidths=1.5,
    label="Drone Base",
    zorder=10
)


ax.annotate(
    "DRONE BASE",
    START_POSITION,
    xytext=(10, 10),
    textcoords="offset points",
    fontsize=10,
    fontweight="bold"
)


# ============================================================
# SURVIVOR
# ============================================================

ax.scatter(
    TARGET_POSITION[0],
    TARGET_POSITION[1],
    marker="*",
    s=450,
    edgecolors="black",
    linewidths=1.5,
    label="Survivor",
    zorder=10
)


ax.annotate(
    "SURVIVOR",
    TARGET_POSITION,
    xytext=(10, 10),
    textcoords="offset points",
    fontsize=10,
    fontweight="bold"
)


# ============================================================
# SAFETY EVENT LOCATION
# ============================================================

for event in safety_events:

    x, y = event["position"]

    ax.scatter(
        x,
        y,
        marker="X",
        s=250,
        edgecolors="black",
        linewidths=2,
        zorder=12
    )

    ax.annotate(
        event["type"],
        (x, y),
        xytext=(15, 15),
        textcoords="offset points",
        fontsize=9,
        fontweight="bold",
        bbox=dict(
            boxstyle="round",
            facecolor="white",
            alpha=0.90
        ),
        arrowprops=dict(
            arrowstyle="->",
            linewidth=1.5
        )
    )


# ============================================================
# AXES
# ============================================================

ax.set_xlim(
    0,
    MAP_WIDTH
)

ax.set_ylim(
    0,
    MAP_HEIGHT
)

ax.set_xlabel(
    "X Grid Position"
)

ax.set_ylabel(
    "Y Grid Position"
)

ax.set_title(
    "Phase 9 - Safety & Fail-Safe Management",
    fontsize=17,
    fontweight="bold"
)

ax.grid(
    True,
    alpha=0.25
)


# ============================================================
# INFORMATION PANEL
# ============================================================

status_text = (
    "AUTONOMOUS SAFETY MONITOR\n"
    "────────────────────────────\n"
    f"Safety State: {safety_state}\n\n"
    f"Battery: "
    f"{battery_level:.1f}%\n\n"
    f"Emergency: "
    f"{emergency_triggered}\n\n"
    f"Safety Events: "
    f"{len(safety_events)}\n\n"
    f"Final Position:\n"
    f"{current_position}\n\n"
    f"Mission Success:\n"
    f"{mission_success}"
)


ax.text(
    0.98,
    0.02,
    status_text,
    transform=ax.transAxes,
    fontsize=10,
    verticalalignment="bottom",
    horizontalalignment="right",
    bbox=dict(
        boxstyle="round",
        facecolor="white",
        alpha=0.90
    ),
    zorder=20
)


ax.legend(
    loc="upper left",
    fontsize=9
)


plt.tight_layout()


# ============================================================
# DISPLAY
# ============================================================

print(
    "\nLaunching Phase 9 visualization..."
)

plt.show()