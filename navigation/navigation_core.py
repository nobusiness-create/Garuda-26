import heapq
import math
import numpy as np

from navigation.phase2.main import (
    occupancy_grid,
    risk_map,
    MAP_WIDTH,
    MAP_HEIGHT,
    DEBRIS,
    FIRE,
    FLOOD,
    drone_position,
)

# ============================================================
# PHASE 6 - SURVIVOR PRIORITIZATION
# Same scoring logic as teammate's main(12).py
# ============================================================

CONDITION_SCORE = {
    "CRITICAL": 40,
    "SERIOUS": 30,
    "MODERATE": 20,
    "STABLE": 10,
}

ACCESSIBILITY_SCORE = {
    "ACCESSIBLE": 10,
    "DIFFICULT": 5,
    "INACCESSIBLE": 0,
}

HAZARD_SCORE = {
    "HIGH": 20,
    "MEDIUM": 10,
    "LOW": 5,
}


def calculate_distance(point_a, point_b):
    return math.sqrt(
        (point_a[0] - point_b[0]) ** 2
        + (point_a[1] - point_b[1]) ** 2
    )


def calculate_priority(survivor):
    """
    Same Phase 6 priority formula used by teammate's code.
    """

    condition_score = CONDITION_SCORE.get(
        survivor["condition"],
        0,
    )

    confidence_score = (
        survivor["detection_confidence"] / 10
    )

    accessibility_score = ACCESSIBILITY_SCORE.get(
        survivor["accessibility"],
        0,
    )

    hazard_score = HAZARD_SCORE.get(
        survivor["hazard"],
        0,
    )

    distance = calculate_distance(
        drone_position,
        survivor["location"],
    )

    distance_score = max(
        0,
        15 - distance / 3,
    )

    total_score = (
        condition_score
        + confidence_score
        + accessibility_score
        + hazard_score
        + distance_score
    )

    survivor["condition_score"] = condition_score
    survivor["confidence_score"] = confidence_score
    survivor["accessibility_score"] = accessibility_score
    survivor["hazard_score"] = hazard_score
    survivor["distance"] = distance
    survivor["distance_score"] = distance_score
    survivor["priority_score"] = total_score

    if total_score >= 70:
        survivor["priority"] = "CRITICAL"

    elif total_score >= 55:
        survivor["priority"] = "HIGH"

    elif total_score >= 40:
        survivor["priority"] = "MEDIUM"

    else:
        survivor["priority"] = "LOW"

    return survivor


def prioritize_survivors(survivors):
    """
    Calculate priority for every survivor and return
    highest-priority survivor first.
    """

    evaluated = []

    for survivor in survivors:
        evaluated.append(
            calculate_priority(
                dict(survivor)
            )
        )

    evaluated.sort(
        key=lambda x: x["priority_score"],
        reverse=True,
    )

    return evaluated


# ============================================================
# PHASE 3 - RISK-AWARE A*
# Same core path-planning logic as teammate's main(5).py
# ============================================================

RISK_WEIGHT = 3.0

STRAIGHT_COST = 1.0
DIAGONAL_COST = np.sqrt(2)

MOVEMENTS = [
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
    (-1, -1),
    (-1, 1),
    (1, -1),
    (1, 1),
]


def is_valid_cell(x, y):
    if x < 0 or x >= MAP_WIDTH:
        return False

    if y < 0 or y >= MAP_HEIGHT:
        return False

    # Debris/buildings are completely blocked.
    if occupancy_grid[y][x] == DEBRIS:
        return False

    return True


def heuristic(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]

    return np.sqrt(
        dx ** 2 + dy ** 2
    )


def get_cell_risk(x, y):
    return float(
        risk_map[y][x]
    )


def movement_cost(
    current,
    neighbour,
    risk_aware=True,
):
    dx = abs(
        neighbour[0] - current[0]
    )
    dy = abs(
        neighbour[1] - current[1]
    )

    if dx == 1 and dy == 1:
        distance_cost = DIAGONAL_COST
    else:
        distance_cost = STRAIGHT_COST

    if not risk_aware:
        return distance_cost

    risk = get_cell_risk(
        neighbour[0],
        neighbour[1],
    )

    return (
        distance_cost
        + RISK_WEIGHT * risk
    )


def a_star(
    start,
    goal,
    risk_aware=True,
):
    """
    Same A* implementation used in teammate's Phase 3.
    """

    if not is_valid_cell(
        start[0],
        start[1],
    ):
        return None

    if not is_valid_cell(
        goal[0],
        goal[1],
    ):
        return None

    open_set = []

    heapq.heappush(
        open_set,
        (0, start),
    )

    came_from = {}

    g_score = {
        start: 0
    }

    f_score = {
        start: heuristic(
            start,
            goal,
        )
    }

    while open_set:

        _, current = heapq.heappop(
            open_set
        )

        if current == goal:

            path = []

            while current in came_from:
                path.append(current)
                current = came_from[current]

            path.append(start)
            path.reverse()

            return path

        for dx, dy in MOVEMENTS:

            nx = current[0] + dx
            ny = current[1] + dy

            neighbour = (
                nx,
                ny,
            )

            if not is_valid_cell(
                nx,
                ny,
            ):
                continue

            # Prevent diagonal corner cutting.
            if dx != 0 and dy != 0:

                if not is_valid_cell(
                    current[0] + dx,
                    current[1],
                ):
                    continue

                if not is_valid_cell(
                    current[0],
                    current[1] + dy,
                ):
                    continue

            step_cost = movement_cost(
                current,
                neighbour,
                risk_aware,
            )

            tentative_g = (
                g_score[current]
                + step_cost
            )

            if (
                neighbour not in g_score
                or tentative_g
                < g_score[neighbour]
            ):

                came_from[neighbour] = current

                g_score[neighbour] = tentative_g

                f_score[neighbour] = (
                    tentative_g
                    + heuristic(
                        neighbour,
                        goal,
                    )
                )

                heapq.heappush(
                    open_set,
                    (
                        f_score[neighbour],
                        neighbour,
                    )
                )

    return None


def calculate_path_distance(path):
    if path is None:
        return float("inf")

    distance = 0.0

    for i in range(
        1,
        len(path),
    ):

        x1, y1 = path[i - 1]
        x2, y2 = path[i]

        dx = abs(
            x2 - x1
        )
        dy = abs(
            y2 - y1
        )

        if dx == 1 and dy == 1:
            distance += DIAGONAL_COST
        else:
            distance += STRAIGHT_COST

    return distance


def calculate_path_risk(path):
    if path is None:
        return float("inf"), 0, 0

    total_risk = 0.0
    fire_cells = 0
    flood_cells = 0

    for x, y in path:

        total_risk += get_cell_risk(
            x,
            y,
        )

        if occupancy_grid[y][x] == FIRE:
            fire_cells += 1

        elif occupancy_grid[y][x] == FLOOD:
            flood_cells += 1

    return (
        total_risk,
        fire_cells,
        flood_cells,
    )
