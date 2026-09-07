import requests


DRONE_STATE_URL = "http://127.0.0.1:8000/drone-state"


def get_drone_state():

    try:

        response = requests.get(
            DRONE_STATE_URL,
            timeout=0.5
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:

        print("Drone state unavailable:", e)

        return None


if __name__ == "__main__":

    state = get_drone_state()

    print("\n===== DRONE STATE =====")

    if state is None:

        print("No drone telemetry.")

    else:

        print("Latitude :", state["latitude"])
        print("Longitude:", state["longitude"])
        print("Altitude :", state["altitude"])
        print("Battery  :", state["battery"])
        print("GPS      :", state["gps_status"])
        print("Mode     :", state["flight_mode"])
        
