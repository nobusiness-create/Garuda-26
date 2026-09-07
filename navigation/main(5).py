import numpy as np
import matplotlib.pyplot as plt
import heapq
import sys
import os

# Add project root to Python path
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(0, PROJECT_ROOT)

from phase2.main import (
    occupancy_grid,
    risk_map,
    drone_position,
    survivor_position,
    MAP_WIDTH,
    MAP_HEIGHT,
    DEBRIS,
    FIRE,
    FLOOD
)


# ============================================================
# PHASE 3
# RISK-AWARE A* PATH PLANNING
#
# Compare:
#
# 1. Naive shortest path
#    -> shortest distance
#    -> ignores environmental risk
#
# 2. Risk-aware A*
#    -> considers distance + disaster risk
#    -> prefers safer routes
#
# Goal:
# Find the safest practical route from drone to survivor.
# ============================================================


# ============================================================
# 1. SETTINGS
# ============================================================

RISK_WEIGHT = 3.0

# Movement cost
STRAIGHT_COST = 1.0
DIAGONAL_COST = np.sqrt(2)

# Large penalty for dangerous areas.
# This makes the planner strongly prefer safe cells.
FIRE_PENALTY = 50.0
FLOOD_PENALTY = 20.0


# ============================================================
# 2. MOVEMENT DIRECTIONS
# ============================================================

MOVEMENTS = [
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
    (-1, -1),
    (-1, 1),
    (1, -1),
    (1, 1)
]


# ============================================================
# 3. CHECK VALID CELL
# ============================================================

def is_valid_cell(x, y):

    if x < 0 or x >= MAP_WIDTH:
        return False

    if y < 0 or y >= MAP_HEIGHT:
        return False

    # Debris/buildings are completely blocked.
    if occupancy_grid[y][x] == DEBRIS:
        return False

    return True


# ============================================================
# 4. HEURISTIC
# ============================================================

def heuristic(a, b):

    """
    Euclidean distance heuristic.
    """

    dx = a[0] - b[0]
    dy = a[1] - b[1]

    return np.sqrt(dx ** 2 + dy ** 2)


# ============================================================
# 5. CELL RISK
# ============================================================

def get_cell_risk(x, y):

    """
    Returns environmental risk of a cell.

    0       -> safe
    FIRE    -> high risk
    FLOOD   -> moderate risk
    """

    cell_risk = risk_map[y][x]

    return float(cell_risk)


# ============================================================
# 6. RISK-AWARE MOVEMENT COST
# ============================================================

def movement_cost(current, neighbour, risk_aware=True):

    x, y = neighbour

    # --------------------------------------------------------
    # Distance cost
    # --------------------------------------------------------

    dx = abs(neighbour[0] - current[0])
    dy = abs(neighbour[1] - current[1])

    if dx == 1 and dy == 1:

        distance_cost = DIAGONAL_COST

    else:

        distance_cost = STRAIGHT_COST


    # --------------------------------------------------------
    # Naive A*
    #
    # Only distance matters.
    # --------------------------------------------------------

    if not risk_aware:

        return distance_cost


    # --------------------------------------------------------
    # Risk-aware A*
    #
    # Total movement cost =
    #
    # distance + risk weight × environmental risk
    # --------------------------------------------------------

    risk = get_cell_risk(x, y)

    return (
        distance_cost +
        RISK_WEIGHT * risk
    )


# ============================================================
# 7. A* PATH PLANNER
# ============================================================

def a_star(start, goal, risk_aware=True):

    """
    A* path planning.

    If risk_aware = False:
        Finds shortest traversable path.

    If risk_aware = True:
        Finds path minimizing:

            distance + environmental risk
    """

    # Priority queue
    open_set = []

    heapq.heappush(
        open_set,
        (0, start)
    )

    came_from = {}

    g_score = {
        start: 0
    }

    f_score = {
        start: heuristic(start, goal)
    }


    while open_set:

        _, current = heapq.heappop(open_set)


        # ----------------------------------------------------
        # Goal reached
        # ----------------------------------------------------

        if current == goal:

            path = []

            while current in came_from:

                path.append(current)

                current = came_from[current]

            path.append(start)

            path.reverse()

            return path


        # ----------------------------------------------------
        # Explore neighbours
        # ----------------------------------------------------

        for dx, dy in MOVEMENTS:

            nx = current[0] + dx
            ny = current[1] + dy

            neighbour = (nx, ny)


            if not is_valid_cell(nx, ny):

                continue


            # ------------------------------------------------
            # Prevent diagonal movement through corners.
            # ------------------------------------------------

            if dx != 0 and dy != 0:

                if not is_valid_cell(
                    current[0] + dx,
                    current[1]
                ):

                    continue

                if not is_valid_cell(
                    current[0],
                    current[1] + dy
                ):

                    continue


            # ------------------------------------------------
            # Calculate new cost
            # ------------------------------------------------

            step_cost = movement_cost(
                current,
                neighbour,
                risk_aware
            )

            tentative_g = (
                g_score[current] +
                step_cost
            )


            if (
                neighbour not in g_score
                or tentative_g < g_score[neighbour]
            ):

                came_from[neighbour] = current

                g_score[neighbour] = tentative_g

                f_score[neighbour] = (
                    tentative_g +
                    heuristic(neighbour, goal)
                )

                heapq.heappush(
                    open_set,
                    (
                        f_score[neighbour],
                        neighbour
                    )
                )


    return None


# ============================================================
# 8. CALCULATE PATH DISTANCE
# ============================================================

def calculate_path_distance(path):

    if path is None:
        return float("inf")

    distance = 0.0

    for i in range(1, len(path)):

        x1, y1 = path[i - 1]
        x2, y2 = path[i]

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        if dx == 1 and dy == 1:

            distance += DIAGONAL_COST

        else:

            distance += STRAIGHT_COST

    return distance


# ============================================================
# 9. CALCULATE ENVIRONMENTAL RISK
# ============================================================

def calculate_path_risk(path):

    if path is None:

        return float("inf"), 0, 0


    total_risk = 0.0

    fire_cells = 0
    flood_cells = 0


    for x, y in path:

        cell_risk = get_cell_risk(x, y)

        total_risk += cell_risk


        # ----------------------------------------------------
        # Detect fire
        # ----------------------------------------------------

        if occupancy_grid[y][x] == FIRE:

            fire_cells += 1


        # ----------------------------------------------------
        # Detect flood
        # ----------------------------------------------------

        elif occupancy_grid[y][x] == FLOOD:

            flood_cells += 1


    return (
        total_risk,
        fire_cells,
        flood_cells
    )


# ============================================================
# 10. PRINT PATH SUMMARY
# ============================================================

def print_path_summary(
    name,
    path
):

    print("\n------------------------------------------")
    print(name)
    print("------------------------------------------")


    if path is None:

        print("NO PATH FOUND.")

        return


    distance = calculate_path_distance(path)

    risk, fire, flood = calculate_path_risk(path)


    print(
        f"Number of path cells: {len(path)}"
    )

    print(
        f"Path distance: {distance:.2f} cells"
    )

    print(
        f"Environmental risk: {risk:.2f}"
    )

    print(
        f"Fire cells crossed: {fire}"
    )

    print(
        f"Flood cells crossed: {flood}"
    )


# ============================================================
# 11. GET BOTH PATHS
# ============================================================

print("\n==========================================")
print("PHASE 3 - RISK-AWARE A* PATH PLANNING")
print("==========================================")

print(
    f"Drone position: {drone_position}"
)

print(
    f"Survivor position: {survivor_position}"
)

print(
    f"Risk weight: {RISK_WEIGHT}"
)


# ------------------------------------------------------------
# Naive shortest path
# ------------------------------------------------------------

shortest_path = a_star(
    drone_position,
    survivor_position,
    risk_aware=False
)


# ------------------------------------------------------------
# Risk-aware path
# ------------------------------------------------------------

safe_path = a_star(
    drone_position,
    survivor_position,
    risk_aware=True
)


# ============================================================
# 12. PRINT RESULTS
# ============================================================

print_path_summary(
    "NAIVE SHORTEST PATH",
    shortest_path
)

print_path_summary(
    "RISK-AWARE A* PATH",
    safe_path
)


# ============================================================
# 13. COMPARE BOTH PATHS
# ============================================================

if shortest_path is not None:

    shortest_distance = calculate_path_distance(
        shortest_path
    )

    shortest_risk, shortest_fire, shortest_flood = (
        calculate_path_risk(shortest_path)
    )

else:

    shortest_distance = float("inf")
    shortest_risk = float("inf")
    shortest_fire = 0
    shortest_flood = 0


if safe_path is not None:

    safe_distance = calculate_path_distance(
        safe_path
    )

    safe_risk, safe_fire, safe_flood = (
        calculate_path_risk(safe_path)
    )

else:

    safe_distance = float("inf")
    safe_risk = float("inf")
    safe_fire = 0
    safe_flood = 0


# ============================================================
# 14. SAFETY IMPROVEMENT
# ============================================================

if (
    shortest_path is not None
    and safe_path is not None
):

    distance_difference = (
        safe_distance -
        shortest_distance
    )


    risk_reduction = (
        shortest_risk -
        safe_risk
    )


else:

    distance_difference = 0
    risk_reduction = 0


# ============================================================
# 15. FINAL NAVIGATION DECISION
# ============================================================

print("\n==========================================")
print("PATH COMPARISON")
print("==========================================")


print(
    f"Shortest-path distance : "
    f"{shortest_distance:.2f}"
)

print(
    f"Shortest-path risk     : "
    f"{shortest_risk:.2f}"
)

print(
    f"Risk-aware distance    : "
    f"{safe_distance:.2f}"
)

print(
    f"Risk-aware risk        : "
    f"{safe_risk:.2f}"
)

print(
    f"Distance difference    : "
    f"{distance_difference:+.2f}"
)

print(
    f"Risk reduction         : "
    f"{risk_reduction:.2f}"
)


print("\n==========================================")
print("PHASE 3 RESULT")
print("==========================================")


if safe_path is None:

    print(
        "Navigation decision:"
    )

    print(
        "NO SAFE ROUTE TO SURVIVOR"
    )


elif safe_risk < shortest_risk:

    print(
        "Navigation decision:"
    )

    print(
        "SAFE ROUTE PREFERRED"
    )

    print(
        "Reason:"
    )

    print(
        "Risk-aware A* accepted a longer route"
    )

    print(
        "to significantly reduce environmental risk."
    )


else:

    print(
        "Navigation decision:"
    )

    print(
        "SHORTEST ROUTE IS ALSO SAFE"
    )


print(
    f"\nFinal path length: "
    f"{safe_distance:.2f} cells"
)

print(
    f"Final environmental risk: "
    f"{safe_risk:.2f}"
)

print(
    f"Fire exposure: "
    f"{safe_fire} cells"
)

print(
    f"Flood exposure: "
    f"{safe_flood} cells"
)


# ============================================================
# 16. VISUALIZE BOTH PATHS
# ============================================================

plt.figure(
    figsize=(13, 9)
)


# ------------------------------------------------------------
# Display risk map
# ------------------------------------------------------------

plt.imshow(
    risk_map,
    origin="lower",
    extent=[
        0,
        MAP_WIDTH,
        0,
        MAP_HEIGHT
    ],
    cmap="magma",
    alpha=0.45
)


# ------------------------------------------------------------
# Draw debris
# ------------------------------------------------------------

for y in range(MAP_HEIGHT):

    for x in range(MAP_WIDTH):

        if occupancy_grid[y][x] == DEBRIS:

            plt.scatter(
                x,
                y,
                marker="s",
                s=180,
                alpha=0.65
            )


# ------------------------------------------------------------
# Draw shortest path
# ------------------------------------------------------------

if shortest_path is not None:

    shortest_x = [
        p[0]
        for p in shortest_path
    ]

    shortest_y = [
        p[1]
        for p in shortest_path
    ]

    plt.plot(
        shortest_x,
        shortest_y,
        linestyle="--",
        linewidth=2.5,
        label="Naive Shortest Path"
    )


# ------------------------------------------------------------
# Draw risk-aware path
# ------------------------------------------------------------

if safe_path is not None:

    safe_x = [
        p[0]
        for p in safe_path
    ]

    safe_y = [
        p[1]
        for p in safe_path
    ]

    plt.plot(
        safe_x,
        safe_y,
        linewidth=4,
        label="Risk-Aware A* Safe Path"
    )


# ------------------------------------------------------------
# Drone
# ------------------------------------------------------------

plt.scatter(
    drone_position[0],
    drone_position[1],
    s=220,
    marker="^",
    label="Drone"
)


# ------------------------------------------------------------
# Survivor
# ------------------------------------------------------------

plt.scatter(
    survivor_position[0],
    survivor_position[1],
    s=250,
    marker="*",
    label="Survivor"
)


# ------------------------------------------------------------
# Labels
# ------------------------------------------------------------

plt.xlabel(
    "X Grid Position"
)

plt.ylabel(
    "Y Grid Position"
)

plt.title(
    "Phase 3 - Naive vs Risk-Aware A* Path Planning"
)

plt.xlim(
    -1,
    MAP_WIDTH
)

plt.ylim(
    -1,
    MAP_HEIGHT
)

plt.grid(
    True,
    alpha=0.3
)

plt.legend()

plt.tight_layout()

plt.show()


# ============================================================
# 17. FINAL REPORT
# ============================================================

print("\n==========================================")
print("PHASE 3 COMPLETE")
print("==========================================")

print(
    "The drone evaluated both:"
)

print(
    "1. Shortest geometric route"
)

print(
    "2. Risk-aware route"
)

print(
    "The selected route prioritizes survivor"
)

print(
    "accessibility while minimizing disaster exposure."
)

print("==========================================")