import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm


# ============================================================
# PHASE 2
# DISASTER ENVIRONMENT / RISK MAP
#
# 0 = FREE SPACE
# 1 = BUILDING / DEBRIS
# 2 = FIRE HAZARD
# 3 = FLOOD
# 4 = SURVIVOR
# 5 = DRONE
# ============================================================


# ============================================================
# 1. MAP SETTINGS
# ============================================================

MAP_WIDTH = 30
MAP_HEIGHT = 30

FREE = 0
DEBRIS = 1
FIRE = 2
FLOOD = 3
SURVIVOR = 4
DRONE = 5


# ============================================================
# 2. CREATE OCCUPANCY GRID
# ============================================================

occupancy_grid = np.zeros(
    (MAP_HEIGHT, MAP_WIDTH),
    dtype=int
)


# ============================================================
# 3. BUILDING / DEBRIS
# ============================================================

# Building 1

occupancy_grid[
    8:14,
    5:11
] = DEBRIS


# Building 2

occupancy_grid[
    18:24,
    18:25
] = DEBRIS


# Building 3

occupancy_grid[
    3:7,
    20:25
] = DEBRIS


# ============================================================
# 4. FIRE HAZARDS
# ============================================================

# Fire region 1

occupancy_grid[
    12:16,
    13:17
] = FIRE


# Fire region 2

occupancy_grid[
    21:25,
    8:12
] = FIRE


# ============================================================
# 5. FLOODED REGION
# ============================================================

occupancy_grid[
    24:28,
    14:22
] = FLOOD


# ============================================================
# 6. SURVIVORS
# ============================================================

survivor_position = (26, 26)

survivor_y, survivor_x = survivor_position

occupancy_grid[
    survivor_y,
    survivor_x
] = SURVIVOR


# ============================================================
# 7. DRONE START POSITION
# ============================================================

drone_position = (2, 2)

drone_y, drone_x = drone_position

occupancy_grid[
    drone_y,
    drone_x
] = DRONE


# ============================================================
# 8. RISK MAP
# ============================================================

risk_map = np.zeros_like(
    occupancy_grid,
    dtype=float
)


# Free space

risk_map[
    occupancy_grid == FREE
] = 0


# Flood

risk_map[
    occupancy_grid == FLOOD
] = 5


# Fire

risk_map[
    occupancy_grid == FIRE
] = 10


# Debris/buildings

risk_map[
    occupancy_grid == DEBRIS
] = 100


# Survivor and drone are not hazards

risk_map[
    occupancy_grid == SURVIVOR
] = 0

risk_map[
    occupancy_grid == DRONE
] = 0


# ============================================================
# 9. DISPLAY DISASTER MAP
# ============================================================

plt.figure(figsize=(10, 10))


# Custom colors:
#
# 0 = free
# 1 = debris
# 2 = fire
# 3 = flood
# 4 = survivor
# 5 = drone

cmap = ListedColormap([
    "white",
    "dimgray",
    "red",
    "deepskyblue",
    "limegreen",
    "orange"
])


# ------------------------------------------------------------
# BUG FIX: previously imshow had no explicit norm, so colors
# were auto-scaled continuously between the grid's min and max
# value. That only rendered correctly here because all six
# categories (0-5) happen to be present in this specific map.
# If a future map is missing a category (e.g. no fire cells),
# the colors would silently shift onto the wrong cells with no
# error. A BoundaryNorm locks each integer value to its exact
# intended color regardless of which values appear in the data.
# ------------------------------------------------------------

category_boundaries = [
    -0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5
]

discrete_norm = BoundaryNorm(
    category_boundaries,
    cmap.N
)


plt.imshow(
    occupancy_grid,
    cmap=cmap,
    norm=discrete_norm,
    origin="lower",
    interpolation="nearest"
)


# ============================================================
# 10. LABEL MAP OBJECTS
# ============================================================

plt.scatter(
    drone_x,
    drone_y,
    s=180,
    marker="^",
    edgecolors="black",
    label="Drone"
)


plt.scatter(
    survivor_x,
    survivor_y,
    s=180,
    marker="*",
    edgecolors="black",
    label="Survivor"
)


# ============================================================
# 11. GRID
# ============================================================

plt.xticks(
    np.arange(0, MAP_WIDTH, 2)
)

plt.yticks(
    np.arange(0, MAP_HEIGHT, 2)
)

plt.grid(
    True,
    linewidth=0.5,
    alpha=0.4
)


plt.xlabel(
    "X Grid Position"
)

plt.ylabel(
    "Y Grid Position"
)

plt.title(
    "Phase 2 - Virtual Disaster Environment"
)

plt.legend()

plt.tight_layout()

plt.show()


# ============================================================
# 12. DISPLAY RISK MAP
# ============================================================

plt.figure(figsize=(10, 10))


plt.imshow(
    risk_map,
    cmap="hot",
    origin="lower",
    interpolation="nearest"
)


plt.colorbar(
    label="Risk Level"
)


plt.scatter(
    drone_x,
    drone_y,
    s=180,
    marker="^",
    edgecolors="white",
    label="Drone"
)


plt.scatter(
    survivor_x,
    survivor_y,
    s=180,
    marker="*",
    edgecolors="white",
    label="Survivor"
)


plt.xticks(
    np.arange(0, MAP_WIDTH, 2)
)

plt.yticks(
    np.arange(0, MAP_HEIGHT, 2)
)

plt.grid(
    True,
    linewidth=0.5,
    alpha=0.4
)


plt.xlabel(
    "X Grid Position"
)

plt.ylabel(
    "Y Grid Position"
)

plt.title(
    "Phase 2 - Disaster Risk Map"
)

plt.legend()

plt.tight_layout()

plt.show()


# ============================================================
# 13. MAP STATISTICS
# ============================================================

free_cells = np.sum(
    occupancy_grid == FREE
)

debris_cells = np.sum(
    occupancy_grid == DEBRIS
)

fire_cells = np.sum(
    occupancy_grid == FIRE
)

flood_cells = np.sum(
    occupancy_grid == FLOOD
)

if __name__ == "__main__":
    print("\n==========================================")
    print("PHASE 2 - DISASTER MAP")
    print("==========================================")

    print(
        f"Map size: "
        f"{MAP_WIDTH} x {MAP_HEIGHT}"
    )

    print(
        f"Total cells: "
        f"{MAP_WIDTH * MAP_HEIGHT}"
    )

    print(
        f"Free cells: "
        f"{free_cells}"
    )

    print(
        f"Debris cells: "
        f"{debris_cells}"
    )

    print(
        f"Fire hazard cells: "
        f"{fire_cells}"
    )

    print(
        f"Flood cells: "
        f"{flood_cells}"
    )

    print(
        f"Drone position: "
        f"({drone_x}, {drone_y})"
    )

    print(
        f"Survivor position: "
        f"({survivor_x}, {survivor_y})"
    )

    print("==========================================")