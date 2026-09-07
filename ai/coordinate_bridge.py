import math
import json


# ============================================================
# SIH26177
# WORLD / DRONE FRAME -> NAVIGATION GRID
#
# IMPORTANT:
# This module does NOT assume the navigation grid convention.
# meters_per_cell and drone_heading_deg are explicit inputs.
# ============================================================


def transform_relative_position_to_world(
    relative_x_m,
    relative_y_m,
    drone_x,
    drone_y,
    drone_heading_deg
):
    """
    Convert a target position expressed in the drone's local
    frame into a world-frame metric position.

    Local convention used here:
        +X = forward
        +Y = left/right according to the radar frame

    The radar module currently provides:
        x = range * cos(angle)
        y = range * sin(angle)

    drone_heading_deg:
        heading of the drone in the same world frame.
    """

    theta = math.radians(
        float(drone_heading_deg)
    )

    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)

    world_dx = (
        relative_x_m * cos_theta
        - relative_y_m * sin_theta
    )

    world_dy = (
        relative_x_m * sin_theta
        + relative_y_m * cos_theta
    )

    return {
        "x_m": round(
            drone_x + world_dx,
            3
        ),
        "y_m": round(
            drone_y + world_dy,
            3
        )
    }


def world_to_grid(
    world_x_m,
    world_y_m,
    meters_per_cell
):
    """
    Convert world metric coordinates to grid coordinates.

    meters_per_cell MUST come from the navigation setup.
    """

    if meters_per_cell <= 0:
        raise ValueError(
            "meters_per_cell must be > 0"
        )

    grid_x = int(
        round(
            world_x_m /
            meters_per_cell
        )
    )

    grid_y = int(
        round(
            world_y_m /
            meters_per_cell
        )
    )

    return (
        grid_x,
        grid_y
    )


def relative_uwb_to_grid(
    relative_position,
    drone_grid_position,
    drone_heading_deg,
    meters_per_cell
):
    """
    Complete UWB relative-position -> grid transform.

    drone_grid_position:
        (x, y) grid coordinate.

    meters_per_cell:
        physical scale of each navigation cell.
    """

    if relative_position is None:
        raise ValueError(
            "UWB relative position is missing"
        )

    relative_x = float(
        relative_position["x_m"]
    )

    relative_y = float(
        relative_position["y_m"]
    )

    drone_grid_x = float(
        drone_grid_position[0]
    )

    drone_grid_y = float(
        drone_grid_position[1]
    )

    # --------------------------------------------------------
    # Convert grid position of drone into world metres.
    # --------------------------------------------------------

    drone_world_x = (
        drone_grid_x *
        meters_per_cell
    )

    drone_world_y = (
        drone_grid_y *
        meters_per_cell
    )

    # --------------------------------------------------------
    # Rotate UWB target into world frame.
    # --------------------------------------------------------

    target_world = (
        transform_relative_position_to_world(
            relative_x,
            relative_y,
            drone_world_x,
            drone_world_y,
            drone_heading_deg
        )
    )

    # --------------------------------------------------------
    # Convert back into navigation grid.
    # --------------------------------------------------------

    target_grid = world_to_grid(
        target_world["x_m"],
        target_world["y_m"],
        meters_per_cell
    )

    return {
        "target_world_m": target_world,
        "target_grid": target_grid,
        "drone_grid": (
            int(drone_grid_position[0]),
            int(drone_grid_position[1])
        ),
        "drone_heading_deg":
            float(drone_heading_deg),
        "meters_per_cell":
            float(meters_per_cell)
    }


def print_transform(result):

    print("\n" + "=" * 65)
    print("SIH26177 UWB -> NAVIGATION COORDINATE TRANSFORM")
    print("=" * 65)

    print(
        json.dumps(
            result,
            indent=4
        )
    )

    print("=" * 65)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    # These are TEST VALUES ONLY.
    #
    # They are NOT claiming that the teammate's real
    # navigation grid uses this scale or heading.

    uwb_relative = {
        "x_m": 6.60,
        "y_m": 1.65
    }

    drone_grid = (
        2,
        2
    )

    drone_heading = 0.0

    meters_per_cell = 1.0

    result = relative_uwb_to_grid(
        relative_position=uwb_relative,
        drone_grid_position=drone_grid,
        drone_heading_deg=drone_heading,
        meters_per_cell=meters_per_cell
    )

    print_transform(
        result
    )
