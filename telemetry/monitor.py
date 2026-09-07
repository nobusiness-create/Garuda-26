import requests
import time
import os

while True:

    try:
        data = requests.get(
            "http://127.0.0.1:8000/drone-state",
            timeout=2
        ).json()

        os.system("clear")

        print("=" * 50)
        print("       SIH26001 DRONE TELEMETRY")
        print("=" * 50)

        print(f"Latitude   : {data['latitude']}")
        print(f"Longitude  : {data['longitude']}")
        print(f"Altitude   : {data['altitude']} m")
        print(f"Velocity   : {data['velocity']} m/s")

        print()

        print(f"Roll       : {data['attitude']['roll']}°")
        print(f"Pitch      : {data['attitude']['pitch']}°")
        print(f"Yaw        : {data['attitude']['yaw']}°")

        print()

        print(f"Battery    : {data['battery']}%")
        print(f"GPS        : {data['gps_status']}")
        print(f"Mode       : {data['flight_mode']}")
        print(f"Connection : {data['communication_status']}")

        print()

        print(f"Timestamp  : {data['timestamp']}")

        print("=" * 50)

    except Exception as e:

        print("Unable to get drone state")
        print(e)

    time.sleep(1)
