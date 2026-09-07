from pymavlink import mavutil
import math
import time

connection = mavutil.mavlink_connection(
    "udpin:0.0.0.0:14550"
)

print("Waiting for heartbeat...")
connection.wait_heartbeat()

print("CONNECTED!")
print("System:", connection.target_system)
print("Component:", connection.target_component)

print("\nReceiving telemetry...\n")

while True:

    msg = connection.recv_match(
        type=[
            "GLOBAL_POSITION_INT",
            "ATTITUDE",
            "SYS_STATUS",
            "HEARTBEAT"
        ],
        blocking=True
    )

    if msg is None:
        continue

    msg_type = msg.get_type()

    if msg_type == "GLOBAL_POSITION_INT":

        latitude = msg.lat / 1e7
        longitude = msg.lon / 1e7
        altitude = msg.relative_alt / 1000.0

        print(
            f"GPS: {latitude:.7f}, "
            f"{longitude:.7f} | "
            f"Alt: {altitude:.2f} m"
        )

    elif msg_type == "ATTITUDE":

        roll = math.degrees(msg.roll)
        pitch = math.degrees(msg.pitch)
        yaw = math.degrees(msg.yaw)

        print(
            f"ATTITUDE: "
            f"R={roll:.1f}° "
            f"P={pitch:.1f}° "
            f"Y={yaw:.1f}°"
        )

    elif msg_type == "SYS_STATUS":

        print(
            f"BATTERY: "
            f"{msg.battery_remaining}%"
        )

    elif msg_type == "HEARTBEAT":

        mode = mavutil.mode_string_v10(msg)

        print(
            f"MODE: {mode}"
        )
