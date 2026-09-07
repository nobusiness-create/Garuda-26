import numpy as np

# ============================================================
# PHASE 2 - DISASTER ENVIRONMENT / RISK MAP
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
# OCCUPANCY GRID
# ============================================================

occupancy_grid = np.zeros(
    (MAP_HEIGHT, MAP_WIDTH),
    dtype=int
)

# ============================================================
# BUILDINGS / DEBRIS
# ============================================================

occupancy_grid[8:14, 5:11] = DEBRIS
occupancy_grid[18:24, 18:25] = DEBRIS
occupancy_grid[3:7, 20:25] = DEBRIS

# ============================================================
# FIRE
# ============================================================

occupancy_grid[12:16, 13:17] = FIRE
occupancy_grid[21:25, 8:12] = FIRE

# ============================================================
# FLOOD
# ============================================================

occupancy_grid[24:28, 14:22] = FLOOD

# ============================================================
# DEFAULT TEST SURVIVOR / DRONE
# ============================================================

survivor_position = (26, 26)
drone_position = (2, 2)

sy, sx = survivor_position
dy, dx = drone_position

occupancy_grid[sy, sx] = SURVIVOR
occupancy_grid[dy, dx] = DRONE

# ============================================================
# RISK MAP
# ============================================================

risk_map = np.zeros_like(
    occupancy_grid,
    dtype=float
)

risk_map[occupancy_grid == FREE] = 0
risk_map[occupancy_grid == FLOOD] = 5
risk_map[occupancy_grid == FIRE] = 10
risk_map[occupancy_grid == DEBRIS] = 100
risk_map[occupancy_grid == SURVIVOR] = 0
risk_map[occupancy_grid == DRONE] = 0

print("[PHASE2] Environment loaded")
print(f"[PHASE2] Map: {MAP_WIDTH} x {MAP_HEIGHT}")
print(f"[PHASE2] Drone: {drone_position}")
print(f"[PHASE2] Test survivor: {survivor_position}")
