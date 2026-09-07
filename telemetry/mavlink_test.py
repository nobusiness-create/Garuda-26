from pymavlink import mavutil

connection = mavutil.mavlink_connection(
    'udpin:0.0.0.0:14550'
)

print("Waiting for MAVLink heartbeat...")

connection.wait_heartbeat()

print("Heartbeat received!")
print("System:", connection.target_system)
print("Component:", connection.target_component)
