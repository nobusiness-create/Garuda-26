from pymavlink import mavutil
import math
import time
import json


# ==================================================
# MAVLINK CONNECTION
# ==================================================

connection = mavutil.mavlink_connection(
    "udpin:0.0.0.0:14550"
)

print("Waiting for heartbeat...")

connection.wait_heartbeat()

print("CONNECTED!")
print("System:", connection.target_system)
print("Component:", connection.target_component)


# ==================================================
# INITIAL DRONE STATE
# ==================================================

drone_state = {
    "latitude": None,
    "longitude": None,
    "altitude": None,

    "attitude": {
        "roll": None,
        "pitch": None,
        "yaw": None
    },

    "velocity": None,

    "battery": None,

    "gps_status": None,

    "flight_mode": None,

    "communication_status": "CONNECTED",

    "timestamp": None
}


# ==================================================
# MAIN TELEMETRY LOOP
# ==================================================

while True:

    msg = connection.recv_match(
        type=[
            "GLOBAL_POSITION_INT",
            "ATTITUDE",
            "SYS_STATUS",
            "HEARTBEAT",
            "GPS_RAW_INT"
        ],
        blocking=True
    )

    if msg is None:
        continue

    msg_type = msg.get_type()


    # ==================================================
    # GPS / POSITION
    # ==================================================

    if msg_type == "GLOBAL_POSITION_INT":

        drone_state["latitude"] = round(
            msg.lat / 1e7,
            7
        )

        drone_state["longitude"] = round(
            msg.lon / 1e7,
            7
        )

        drone_state["altitude"] = round(
            msg.relative_alt / 1000.0,
            2
        )

        vx = msg.vx / 100.0
        vy = msg.vy / 100.0

        drone_state["velocity"] = round(
            math.sqrt(vx**2 + vy**2),
            2
        )


    # ==================================================
    # ATTITUDE / IMU
    # ==================================================

    elif msg_type == "ATTITUDE":

        drone_state["attitude"]["roll"] = round(
            math.degrees(msg.roll),
            2
        )

        drone_state["attitude"]["pitch"] = round(
            math.degrees(msg.pitch),
            2
        )

        drone_state["attitude"]["yaw"] = round(
            math.degrees(msg.yaw),
            2
        )


    # ==================================================
    # BATTERY
    # ==================================================

    elif msg_type == "SYS_STATUS":

        if msg.battery_remaining >= 0:

            drone_state["battery"] = (
                msg.battery_remaining
            )


    # ==================================================
    # FLIGHT MODE
    # ==================================================

    elif msg_type == "HEARTBEAT":

        drone_state["flight_mode"] = (
            mavutil.mode_string_v10(msg)
        )


    # ==================================================
    # GPS STATUS
    # ==================================================

    elif msg_type == "GPS_RAW_INT":

        fix_type = msg.fix_type

        if fix_type == 0:

            drone_state["gps_status"] = "NO_GPS"

        elif fix_type == 1:

            drone_state["gps_status"] = "NO_FIX"

        elif fix_type == 2:

            drone_state["gps_status"] = "2D_FIX"

        elif fix_type >= 3:

            drone_state["gps_status"] = "3D_FIX"


    # ==================================================
    # TIMESTAMP
    # ==================================================

    drone_state["timestamp"] = time.time()


    # ==================================================
    # PRINT JSON
    # ==================================================

    print(
        json.dumps(
            drone_state,
            indent=2
        )
    )
