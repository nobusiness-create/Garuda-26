from pymavlink import mavutil
import math
import time
import json


# --------------------------------------------------
# MAVLink CONNECTION
# --------------------------------------------------

connection = mavutil.mavlink_connection(
    "udpin:0.0.0.0:14550"
)

print("Connecting to MAVLink...")
print("Waiting for heartbeat...")

connection.wait_heartbeat()

print("CONNECTED!")
print("System:", connection.target_system)
print("Component:", connection.target_component)


# --------------------------------------------------
# DRONE STATE
# --------------------------------------------------

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


# --------------------------------------------------
# RECEIVE MAVLINK DATA
# --------------------------------------------------

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


    # ----------------------------------------------
    # GPS + POSITION
    # ----------------------------------------------

    if msg_type == "GLOBAL_POSITION_INT":

        drone_state["latitude"] = msg.lat / 1e7

        drone_state["longitude"] = msg.lon / 1e7

        # Relative altitude in meters
        drone_state["altitude"] = msg.relative_alt / 1000.0

        # Horizontal velocity
        vx = msg.vx / 100.0
        vy = msg.vy / 100.0

        drone_state["velocity"] = (
            vx ** 2 + vy ** 2
        ) ** 0.5


    # ----------------------------------------------
    # ATTITUDE / IMU
    # ----------------------------------------------

    elif msg_type == "ATTITUDE":

        drone_state["attitude"]["roll"] = round(
            math.degrees(msg.roll), 2
        )

        drone_state["attitude"]["pitch"] = round(
            math.degrees(msg.pitch), 2
        )

        drone_state["attitude"]["yaw"] = round(
            math.degrees(msg.yaw), 2
        )


    # ----------------------------------------------
    # BATTERY
    # ----------------------------------------------

    elif msg_type == "SYS_STATUS":

        battery = msg.battery_remaining

        if battery >= 0:
            drone_state["battery"] = battery


    # ----------------------------------------------
    # FLIGHT MODE
    # ----------------------------------------------

    elif msg_type == "HEARTBEAT":

        drone_state["flight_mode"] = (
            mavutil.mode_string_v10(msg)
        )


    # ----------------------------------------------
    # GPS STATUS
    # ----------------------------------------------

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


    # ----------------------------------------------
    # TIMESTAMP
    # ----------------------------------------------

    drone_state["timestamp"] = time.time()


    # ----------------------------------------------
    # DISPLAY
    # ----------------------------------------------

    print("\n" + "=" * 50)

    print("DRONE STATE")

    print("=" * 50)

    print(
        f"Latitude:  {drone_state['latitude']}"
    )

    print(
        f"Longitude: {drone_state['longitude']}"
    )

    print(
        f"Altitude:  {drone_state['altitude']} m"
    )

    print(
        f"Roll:      {drone_state['attitude']['roll']}°"
    )

    print(
        f"Pitch:     {drone_state['attitude']['pitch']}°"
    )

    print(
        f"Yaw:       {drone_state['attitude']['yaw']}°"
    )

    print(
        f"Velocity:  {drone_state['velocity']} m/s"
    )

    print(
        f"Battery:   {drone_state['battery']}%"
    )

    print(
        f"GPS:       {drone_state['gps_status']}"
    )

    print(
        f"Mode:      {drone_state['flight_mode']}"
    )

    print(
        f"Connection: {drone_state['communication_status']}"
    )

    print(
        f"Timestamp: {drone_state['timestamp']}"
    )

    print("=" * 50)
