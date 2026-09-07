import sys
import os
import math
import heapq
import time
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
# IMPORT DISASTER ENVIRONMENT FROM PHASE 2
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
# PHASE 8
# DYNAMIC MISSION MONITORING & REPLANNING
# ============================================================

print("=" * 70)
print("PHASE 8 - DYNAMIC MISSION MONITORING & REPLANNING")
print("=" * 70)


# ============================================================
# SURVIVOR DATA FROM PHASE 6
# ============================================================

survivors = [
    {
        "id": "S3",
        "position": (7, 22),
        "priority": "CRITICAL",
        "priority_score": 82.2
    },

    {
        "id": "S1",
        "position": (26, 26),
        "priority": "HIGH",
        "priority_score": 67.2
    },

    {
        "id": "S2",
        "position": (18, 7),
        "priority": "HIGH",
        "priority_score": 56.6
    }
]


# ============================================================
# MISSION PARAMETERS
# ============================================================

current_position = drone_position

blocked_cells = {
    DEBRIS,
    FIRE,
    FLOOD
}

mission_success = False

visited_survivors = []

complete_flight_path = []

planned_segments = []

replanning_events = []

hazards_detected = []

total_distance = 0.0

mission_step = 0

dynamic_hazard_triggered = False


# ============================================================
# A* SAFE PATH PLANNER
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

        cell_type = grid[y, x]

        if cell_type in blocked_cells:
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

    f_score = {
        start: heuristic(start, goal)
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
                g_score[current] +
                cost
            )

            if (
                neighbor not in g_score
                or tentative_g < g_score[neighbor]
            ):

                came_from[neighbor] = current

                g_score[neighbor] = tentative_g

                f_score[neighbor] = (
                    tentative_g +
                    heuristic(
                        neighbor,
                        goal
                    )
                )

                heapq.heappush(
                    open_set,
                    (
                        f_score[neighbor],
                        neighbor
                    )
                )

    return None


# ============================================================
# DISTANCE CALCULATION
# ============================================================

def calculate_distance(path):

    if path is None or len(path) < 2:
        return 0.0

    distance = 0.0

    for i in range(1, len(path)):

        x1, y1 = path[i - 1]
        x2, y2 = path[i]

        distance += math.sqrt(
            (x2 - x1) ** 2 +
            (y2 - y1) ** 2
        )

    return distance


# ============================================================
# ROUTE SAFETY CHECK
# ============================================================

def is_route_affected(path, hazard):

    if path is None:
        return False

    return hazard in path


# ============================================================
# MISSION INITIALIZATION
# ============================================================

print("\nMISSION INITIALIZATION")
print("-" * 70)

print(
    f"Drone starting position : "
    f"{current_position}"
)

print(
    f"Map size                : "
    f"{MAP_WIDTH} x {MAP_HEIGHT}"
)

print(
    f"Survivors               : "
    f"{len(survivors)}"
)

print("\nRescue priority sequence:")

for index, survivor in enumerate(
    survivors,
    start=1
):

    print(
        f"{index}. "
        f"{survivor['id']} → "
        f"{survivor['priority']} "
        f"({survivor['priority_score']}) "
        f"at {survivor['position']}"
    )


# ============================================================
# AUTONOMOUS MONITORING START
# ============================================================

print("\n" + "=" * 70)
print("AUTONOMOUS MISSION MONITORING STARTED")
print("=" * 70)

print("\n✓ Environment monitoring active")
print("✓ Hazard monitoring active")
print("✓ Route monitoring active")
print("✓ Autonomous replanning active")
print("✓ Multi-survivor mission active")


# ============================================================
# MAIN MULTI-SURVIVOR MISSION
# ============================================================

for survivor_index, survivor in enumerate(
    survivors,
    start=1
):

    survivor_id = survivor["id"]

    target_position = survivor["position"]

    print("\n" + "=" * 70)

    print(
        f"MISSION TARGET #{survivor_index}: "
        f"{survivor_id}"
    )

    print("=" * 70)

    print(
        f"Current position : "
        f"{current_position}"
    )

    print(
        f"Target position  : "
        f"{target_position}"
    )

    print(
        f"Priority         : "
        f"{survivor['priority']}"
    )

    # --------------------------------------------------------
    # INITIAL ROUTE
    # --------------------------------------------------------

    path = calculate_safe_path(
        current_position,
        target_position,
        occupancy_grid
    )

    if path is None:

        print(
            f"❌ No safe route to "
            f"{survivor_id}"
        )

        mission_success = False
        break

    initial_segment = path.copy()

    print(
        f"✓ Initial safe route calculated"
    )

    print(
        f"✓ Route waypoints: "
        f"{len(path)}"
    )

    # --------------------------------------------------------
    # SAVE INITIAL SEGMENT
    # --------------------------------------------------------

    planned_segments.append(
        {
            "survivor": survivor_id,
            "type": "initial",
            "path": path.copy()
        }
    )

    # --------------------------------------------------------
    # DYNAMIC HAZARD TRIGGER
    # --------------------------------------------------------

    hazard_for_this_target = None

    if (
        not dynamic_hazard_triggered
        and len(path) > 10
    ):

        # Choose a point several cells ahead
        # so the drone detects a hazard before
        # reaching it.

        hazard_index = min(
            8,
            len(path) - 2
        )

        hazard_for_this_target = path[
            hazard_index
        ]

        dynamic_hazard_triggered = True

        print(
            "\nDynamic hazard simulation armed."
        )

        print(
            f"⚠ Future route cell selected: "
            f"{hazard_for_this_target}"
        )

    # --------------------------------------------------------
    # FLIGHT EXECUTION
    # --------------------------------------------------------

    segment_path = []

    segment_distance = 0.0

    local_index = 0

    while current_position != target_position:

        # ----------------------------------------------------
        # DYNAMIC ENVIRONMENT MONITORING
        # ----------------------------------------------------

        print(
            f"\n[MONITOR] "
            f"Step {mission_step}"
        )

        print(
            f"[MONITOR] Drone position: "
            f"{current_position}"
        )

        # ----------------------------------------------------
        # SIMULATE NEW HAZARD
        # ----------------------------------------------------

        if (
            hazard_for_this_target is not None
            and local_index == 5
            and hazard_for_this_target
            not in hazards_detected
        ):

            new_hazard = hazard_for_this_target

            print("\n" + "!" * 70)
            print("⚠ NEW DYNAMIC HAZARD DETECTED")
            print("!" * 70)

            print(
                f"⚠ Hazard location: "
                f"{new_hazard}"
            )

            # Add hazard to environment

            occupancy_grid[
                new_hazard[1],
                new_hazard[0]
            ] = FIRE

            hazards_detected.append(
                new_hazard
            )

            print(
                "⚠ Environment map updated"
            )

            # ------------------------------------------------
            # CHECK CURRENT ROUTE
            # ------------------------------------------------

            remaining_path = path[
                path.index(current_position):
            ]

            print(
                "🧠 Checking current route..."
            )

            route_affected = is_route_affected(
                remaining_path,
                new_hazard
            )

            if route_affected:

                print(
                    "⚠ CURRENT ROUTE COMPROMISED"
                )

                print(
                    "🧠 Autonomous replanning initiated..."
                )

                replanning_events.append(
                    {
                        "step": mission_step,
                        "position": current_position,
                        "hazard": new_hazard,
                        "target": target_position
                    }
                )

                # --------------------------------------------
                # REPLAN
                # --------------------------------------------

                new_path = calculate_safe_path(
                    current_position,
                    target_position,
                    occupancy_grid
                )

                if new_path is None:

                    print(
                        "❌ No safe alternative route."
                    )

                    mission_success = False
                    break

                path = new_path

                planned_segments.append(
                    {
                        "survivor": survivor_id,
                        "type": "replanned",
                        "path": path.copy()
                    }
                )

                print(
                    "✓ NEW SAFE ROUTE GENERATED"
                )

                print(
                    f"✓ New waypoints: "
                    f"{len(path)}"
                )

                print(
                    "✓ Drone continuing "
                    "on replanned route."
                )

            else:

                print(
                    "✓ Current route unaffected."
                )

        # ----------------------------------------------------
        # GET CURRENT POSITION INDEX
        # ----------------------------------------------------

        if current_position not in path:

            print(
                "⚠ Current position not found "
                "in active route."
            )

            new_path = calculate_safe_path(
                current_position,
                target_position,
                occupancy_grid
            )

            if new_path is None:

                print(
                    "❌ Emergency route "
                    "calculation failed."
                )

                mission_success = False
                break

            path = new_path

        current_index = path.index(
            current_position
        )

        # ----------------------------------------------------
        # CHECK IF TARGET REACHED
        # ----------------------------------------------------

        if current_position == target_position:
            break

        if current_index + 1 >= len(path):

            print(
                "⚠ Route exhausted. "
                "Replanning..."
            )

            new_path = calculate_safe_path(
                current_position,
                target_position,
                occupancy_grid
            )

            if new_path is None:

                mission_success = False
                break

            path = new_path

            continue

        # ----------------------------------------------------
        # NEXT POSITION
        # ----------------------------------------------------

        next_position = path[
            current_index + 1
        ]

        # ----------------------------------------------------
        # LAST-SECOND SAFETY CHECK
        # ----------------------------------------------------

        next_cell_type = occupancy_grid[
            next_position[1],
            next_position[0]
        ]

        if next_cell_type in blocked_cells:

            print("\n⚠ HAZARD DETECTED AHEAD")

            print(
                f"⚠ Unsafe waypoint: "
                f"{next_position}"
            )

            print(
                "🧠 Emergency replanning..."
            )

            replanning_events.append(
                {
                    "step": mission_step,
                    "position": current_position,
                    "hazard": next_position,
                    "target": target_position
                }
            )

            new_path = calculate_safe_path(
                current_position,
                target_position,
                occupancy_grid
            )

            if new_path is None:

                print(
                    "❌ No safe route available."
                )

                mission_success = False
                break

            path = new_path

            print(
                "✓ Emergency safe route generated."
            )

            continue

        # ----------------------------------------------------
        # MOVE DRONE
        # ----------------------------------------------------

        movement = math.sqrt(
            (
                next_position[0]
                - current_position[0]
            ) ** 2
            +
            (
                next_position[1]
                - current_position[1]
            ) ** 2
        )

        segment_distance += movement

        total_distance += movement

        current_position = next_position

        segment_path.append(
            current_position
        )

        complete_flight_path.append(
            current_position
        )

        print(
            f"🚁 Drone → "
            f"{current_position}"
        )

        mission_step += 1

        local_index += 1

        time.sleep(0.05)

    # --------------------------------------------------------
    # TARGET REACHED
    # --------------------------------------------------------

    if current_position == target_position:

        print("\n" + "-" * 70)

        print(
            f"✓ SURVIVOR {survivor_id} REACHED"
        )

        print(
            f"✓ Location: "
            f"{target_position}"
        )

        print(
            f"✓ Priority: "
            f"{survivor['priority']}"
        )

        print(
            f"✓ Segment distance: "
            f"{segment_distance:.2f} units"
        )

        print(
            "✓ Survivor secured."
        )

        visited_survivors.append(
            survivor_id
        )


    else:

        print(
            f"❌ Failed to reach "
            f"{survivor_id}"
        )

        break


# ============================================================
# FINAL MISSION STATUS
# ============================================================

if len(visited_survivors) == len(survivors):

    mission_success = True

else:

    mission_success = False


# ============================================================
# FINAL MISSION REPORT
# ============================================================

print("\n" + "=" * 70)
print("PHASE 8 - AUTONOMOUS MISSION REPORT")
print("=" * 70)

print(
    f"Survivors detected        : "
    f"{len(survivors)}"
)

print(
    f"Survivors reached         : "
    f"{len(visited_survivors)}"
)

print(
    f"Rescue sequence           : "
    f"{' → '.join(visited_survivors)}"
)

print(
    f"Dynamic hazards detected  : "
    f"{len(hazards_detected)}"
)

print(
    f"Replanning events         : "
    f"{len(replanning_events)}"
)

print(
    f"Total flight distance     : "
    f"{total_distance:.2f} grid units"
)

print(
    f"Final drone position      : "
    f"{current_position}"
)

print(
    f"Mission success           : "
    f"{mission_success}"
)


# ============================================================
# REPLANNING REPORT
# ============================================================

print("\nREPLANNING EVENTS")
print("-" * 70)

if len(replanning_events) == 0:

    print(
        "No replanning events occurred."
    )

else:

    for index, event in enumerate(
        replanning_events,
        start=1
    ):

        print(
            f"\nEvent #{index}"
        )

        print(
            f"Step              : "
            f"{event['step']}"
        )

        print(
            f"Drone position    : "
            f"{event['position']}"
        )

        print(
            f"New hazard        : "
            f"{event['hazard']}"
        )

        print(
            f"Current target    : "
            f"{event['target']}"
        )

        print(
            "Action            : "
            "ROUTE REPLANNED"
        )


# ============================================================
# FINAL RESULT
# ============================================================

print("\n" + "=" * 70)
print("PHASE 8 RESULT")
print("=" * 70)

if mission_success:

    print(
        "✓ DYNAMIC MISSION MONITORING SUCCESSFUL"
    )

    print(
        "✓ ENVIRONMENT CHANGES DETECTED"
    )

    print(
        "✓ ROUTE SAFETY VERIFIED"
    )

    print(
        "✓ AUTONOMOUS REPLANNING EXECUTED"
    )

    print(
        "✓ ALL SURVIVORS REACHED"
    )

    print(
        "✓ MISSION COMPLETED SUCCESSFULLY"
    )

else:

    print(
        "✗ AUTONOMOUS MISSION FAILED"
    )

print("=" * 70)


# ============================================================
# PHASE 8 VISUALIZATION
# ============================================================

print(
    "\nGenerating Phase 8 visualization..."
)


fig, ax = plt.subplots(
    figsize=(12, 10)
)


# ============================================================
# DISASTER ENVIRONMENT
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
    alpha=0.70
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
# DRAW PLANNED ROUTES
# ============================================================

for segment in planned_segments:

    segment_path = segment["path"]

    if len(segment_path) < 2:
        continue

    x_values = [
        point[0]
        for point in segment_path
    ]

    y_values = [
        point[1]
        for point in segment_path
    ]

    if segment["type"] == "initial":

        ax.plot(
            x_values,
            y_values,
            linestyle="--",
            linewidth=2,
            alpha=0.35,
            label="Initial Planned Route",
            zorder=3
        )

    else:

        ax.plot(
            x_values,
            y_values,
            linewidth=3,
            alpha=0.85,
            label="Replanned Route",
            zorder=5
        )


# ============================================================
# ACTUAL DRONE FLIGHT PATH
# ============================================================

if complete_flight_path:

    flight_x = [
        point[0]
        for point in complete_flight_path
    ]

    flight_y = [
        point[1]
        for point in complete_flight_path
    ]

    # Include starting position

    flight_x.insert(
        0,
        drone_position[0]
    )

    flight_y.insert(
        0,
        drone_position[1]
    )

    ax.plot(
        flight_x,
        flight_y,
        linewidth=3,
        alpha=0.9,
        label="Actual Drone Flight",
        zorder=6
    )


# ============================================================
# DRONE START
# ============================================================

ax.scatter(
    drone_position[0],
    drone_position[1],
    marker="^",
    s=280,
    edgecolors="black",
    linewidths=1.5,
    label="Drone Start",
    zorder=9
)


ax.annotate(
    "DRONE START",
    drone_position,
    xytext=(8, 8),
    textcoords="offset points",
    fontsize=10,
    fontweight="bold"
)


# ============================================================
# SURVIVORS
# ============================================================

for index, survivor in enumerate(
    survivors,
    start=1
):

    x, y = survivor["position"]

    survivor_id = survivor["id"]

    ax.scatter(
        x,
        y,
        marker="*",
        s=420,
        edgecolors="black",
        linewidths=1.5,
        label=(
            f"{survivor_id} - "
            f"{survivor['priority']}"
        ),
        zorder=10
    )

    ax.annotate(
        (
            f"#{index} {survivor_id}\n"
            f"{survivor['priority']}\n"
            f"Score: "
            f"{survivor['priority_score']}"
        ),
        (x, y),
        xytext=(10, 10),
        textcoords="offset points",
        fontsize=9,
        fontweight="bold",
        bbox=dict(
            boxstyle="round",
            facecolor="white",
            alpha=0.85
        ),
        zorder=11
    )


# ============================================================
# DYNAMIC HAZARDS
# ============================================================

for index, hazard in enumerate(
    hazards_detected,
    start=1
):

    hx, hy = hazard

    ax.scatter(
        hx,
        hy,
        marker="X",
        s=260,
        edgecolors="black",
        linewidths=1.5,
        label=(
            "Dynamic Hazard"
            if index == 1
            else None
        ),
        zorder=12
    )

    ax.annotate(
        "DYNAMIC HAZARD\nREPLANNING",
        hazard,
        xytext=(20, 25),
        textcoords="offset points",
        fontsize=9,
        fontweight="bold",
        ha="center",
        bbox=dict(
            boxstyle="round",
            facecolor="white",
            alpha=0.90
        ),
        arrowprops=dict(
            arrowstyle="->",
            linewidth=1.5
        ),
        zorder=13
    )


# ============================================================
# REPLANNING EVENT MARKERS
# ============================================================

for event in replanning_events:

    px, py = event["position"]

    ax.scatter(
        px,
        py,
        marker="o",
        s=180,
        facecolors="none",
        edgecolors="black",
        linewidths=2,
        zorder=14
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
    "Phase 8 - Dynamic Mission Monitoring & Replanning",
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

info_text = (
    "AUTONOMOUS MISSION MONITOR\n"
    "────────────────────────────\n"
    f"Mission Success: {mission_success}\n"
    f"Survivors: {len(survivors)}\n"
    f"Reached: {len(visited_survivors)}\n\n"
    f"Rescue Order:\n"
    f"{' → '.join(visited_survivors)}\n\n"
    f"Dynamic Hazards:\n"
    f"{len(hazards_detected)}\n\n"
    f"Replanning Events:\n"
    f"{len(replanning_events)}\n\n"
    f"Flight Distance:\n"
    f"{total_distance:.2f} units\n\n"
    "STATUS:\n"
    "AUTONOMOUS REPLANNING ACTIVE"
)


ax.text(
    0.98,
    0.02,
    info_text,
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


# ============================================================
# LEGEND
# ============================================================

handles, labels = ax.get_legend_handles_labels()

# Remove duplicate labels

unique = {}

for handle, label in zip(
    handles,
    labels
):

    if label not in unique:

        unique[label] = handle


ax.legend(
    unique.values(),
    unique.keys(),
    loc="upper left",
    fontsize=9
)


plt.tight_layout()


# ============================================================
# DISPLAY
# ============================================================

print(
    "\nLaunching Phase 8 visualization..."
)

plt.show()