# ============================================================
# ADAPTIVE FLIGHT CONTROL
# SIH26177 DISASTER-RESPONSE DRONE
#
# Integrates:
#   - Adaptive speed
#   - Adaptive altitude
#
# These are decision-level controllers.
# They do NOT directly send MAVLink commands yet.
# ============================================================


def adaptive_speed_controller(
    survivor_probability,
    obstacle_level,
    battery_percent,
    current_speed,
):
    """
    Decide desired horizontal speed.

    survivor_probability : 0.0 -> 1.0
    obstacle_level       : 0.0 -> 1.0
    battery_percent      : 0 -> 100
    current_speed        : m/s
    """

    survivor_probability = float(
        survivor_probability
    )

    obstacle_level = float(
        obstacle_level
    )

    battery_percent = float(
        battery_percent
    )

    current_speed = float(
        current_speed
    )

    # --------------------------------------------------------
    # Survivor-confidence-based speed
    # --------------------------------------------------------

    if survivor_probability < 0.30:

        target_speed = 7.0
        action = "FAST SEARCH"

    elif survivor_probability < 0.60:

        target_speed = 3.0
        action = "SLOW SEARCH"

    elif survivor_probability < 0.80:

        target_speed = 1.0
        action = "VERY SLOW SEARCH"

    else:

        target_speed = 0.0
        action = "HOVER AND INVESTIGATE"

    # --------------------------------------------------------
    # Obstacle safety override
    # --------------------------------------------------------

    if obstacle_level > 0.80:

        target_speed = 0.0
        action = "STOP / AVOID OBSTACLE"

    elif obstacle_level > 0.50:

        target_speed = min(
            target_speed,
            1.0,
        )

        action = "SLOW DUE TO OBSTACLE"

    # --------------------------------------------------------
    # Battery override
    # --------------------------------------------------------

    if battery_percent < 20:

        target_speed = min(
            target_speed,
            2.0,
        )

        action = "LOW BATTERY - RETURN"

    return {
        "target_speed_mps": target_speed,
        "action": action,
        "survivor_probability": survivor_probability,
        "obstacle_level": obstacle_level,
        "battery_percent": battery_percent,
        "current_speed_mps": current_speed,
    }


def adaptive_altitude_controller(
    survivor_probability,
    obstacle_level,
    battery_percent,
    current_altitude,
):
    """
    Decide desired altitude above ground.

    This is currently a prototype decision policy.
    """

    survivor_probability = float(
        survivor_probability
    )

    obstacle_level = float(
        obstacle_level
    )

    battery_percent = float(
        battery_percent
    )

    current_altitude = float(
        current_altitude
    )

    # --------------------------------------------------------
    # Survivor-confidence-based altitude
    # --------------------------------------------------------

    if survivor_probability < 0.30:

        target_altitude = 40.0
        action = "WIDE AREA SEARCH"

    elif survivor_probability < 0.60:

        target_altitude = 20.0
        action = "DETAILED SEARCH"

    elif survivor_probability < 0.80:

        target_altitude = 15.0
        action = "LOW ALTITUDE INVESTIGATION"

    else:

        target_altitude = 10.0
        action = "HOVER / INVESTIGATE"

    # --------------------------------------------------------
    # Obstacle safety override
    # --------------------------------------------------------

    if obstacle_level > 0.80:

        target_altitude = max(
            current_altitude,
            20.0,
        )

        action = "CLIMB / AVOID OBSTACLE"

    elif obstacle_level > 0.50:

        target_altitude = max(
            target_altitude,
            20.0,
        )

        action = "MAINTAIN SAFE ALTITUDE"

    # --------------------------------------------------------
    # Battery override
    # --------------------------------------------------------

    if battery_percent < 20:

        action = "RETURN TO HOME"

    return {
        "target_altitude_m": target_altitude,
        "action": action,
        "survivor_probability": survivor_probability,
        "obstacle_level": obstacle_level,
        "battery_percent": battery_percent,
        "current_altitude_m": current_altitude,
    }


# ============================================================
# COMBINED FLIGHT DECISION
# ============================================================

def adaptive_flight_controller(
    survivor_probability,
    obstacle_level,
    battery_percent,
    current_speed,
    current_altitude,
):
    """
    Run speed and altitude controllers together.
    """

    speed = adaptive_speed_controller(
        survivor_probability,
        obstacle_level,
        battery_percent,
        current_speed,
    )

    altitude = adaptive_altitude_controller(
        survivor_probability,
        obstacle_level,
        battery_percent,
        current_altitude,
    )

    # --------------------------------------------------------
    # Overall mission action
    # --------------------------------------------------------

    if battery_percent < 20:

        mission_action = "RETURN TO HOME"

    elif obstacle_level > 0.80:

        mission_action = "AVOID OBSTACLE"

    elif survivor_probability >= 0.80:

        mission_action = "HOVER / INVESTIGATE"

    else:

        mission_action = "CONTINUE SEARCH"

    return {
        "speed": speed,
        "altitude": altitude,
        "mission_action": mission_action,
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    result = adaptive_flight_controller(
        survivor_probability=0.894,
        obstacle_level=0.10,
        battery_percent=75,
        current_speed=3.0,
        current_altitude=20.0,
    )

    print("\n" + "=" * 65)
    print("ADAPTIVE FLIGHT CONTROL TEST")
    print("=" * 65)

    print("\nSPEED")
    print("-" * 65)

    for key, value in result["speed"].items():
        print(
            f"{key:25}: {value}"
        )

    print("\nALTITUDE")
    print("-" * 65)

    for key, value in result["altitude"].items():
        print(
            f"{key:25}: {value}"
        )

    print("\nMISSION")
    print("-" * 65)

    print(
        "Overall action:",
        result["mission_action"],
    )

    print("=" * 65)
