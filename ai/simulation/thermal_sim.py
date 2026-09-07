import cv2
import numpy as np


def create_thermal_scene(scenario="day"):

    width = 640
    height = 480

    # --------------------------------------------------
    # BACKGROUND
    # --------------------------------------------------

    if scenario == "day":
        background = 70

    elif scenario == "night":
        background = 35

    elif scenario == "fire_smoke":
        background = 60

    elif scenario == "smoke":
        background = 55

    elif scenario == "debris":
        background = 45

    else:
        background = 50

    thermal = np.full(
        (height, width),
        background,
        dtype=np.uint8
    )

    # --------------------------------------------------
    # BACKGROUND DEBRIS
    # --------------------------------------------------

    cv2.rectangle(
        thermal,
        (80, 100),
        (180, 180),
        max(0, background - 10),
        -1
    )

    cv2.rectangle(
        thermal,
        (450, 80),
        (570, 160),
        max(0, background - 5),
        -1
    )

    # --------------------------------------------------
    # SIMULATED SURVIVOR
    # --------------------------------------------------

    if scenario == "day":

        head_temp = 210
        body_temp = 175

    elif scenario == "night":

        head_temp = 240
        body_temp = 210

    elif scenario == "fire_smoke":

        head_temp = 225
        body_temp = 195

    elif scenario == "smoke":

        head_temp = 235
        body_temp = 205

    elif scenario == "debris":

        head_temp = 230
        body_temp = 200

    else:

        head_temp = 200
        body_temp = 170

    # Head
    cv2.circle(
        thermal,
        (320, 240),
        18,
        head_temp,
        -1
    )

    # Body
    cv2.rectangle(
        thermal,
        (295, 258),
        (345, 340),
        body_temp,
        -1
    )

    # Legs
    cv2.line(
        thermal,
        (310, 340),
        (295, 390),
        body_temp,
        12
    )

    cv2.line(
        thermal,
        (330, 340),
        (345, 390),
        body_temp,
        12
    )

    # Arms
    cv2.line(
        thermal,
        (295, 275),
        (260, 320),
        body_temp,
        10
    )

    cv2.line(
        thermal,
        (345, 275),
        (380, 320),
        body_temp,
        10
    )

    # --------------------------------------------------
    # DEBRIS OCCLUSION
    # --------------------------------------------------

    if scenario == "debris":

        cv2.rectangle(
            thermal,
            (240, 320),
            (410, 430),
            65,
            -1
        )

    # --------------------------------------------------
    # FIRE / HOT OBJECT
    # --------------------------------------------------

    if scenario == "fire_smoke":

        # Large extremely hot region.
        # It is deliberately positioned away
        # from the survivor.

        cv2.circle(
            thermal,
            (500, 300),
            55,
            240,
            -1
        )

        cv2.circle(
            thermal,
            (500, 300),
            35,
            255,
            -1
        )

        cv2.circle(
            thermal,
            (500, 300),
            18,
            255,
            -1
        )

    return thermal


# ======================================================
# VISUALIZATION TEST
# ======================================================

if __name__ == "__main__":

    scenario = "fire_smoke"

    thermal_image = create_thermal_scene(
        scenario
    )

    thermal_colored = cv2.applyColorMap(
        thermal_image,
        cv2.COLORMAP_INFERNO
    )

    cv2.imwrite(
        "simulation_thermal_raw.png",
        thermal_image
    )

    cv2.imwrite(
        "simulation_thermal.png",
        thermal_colored
    )

    cv2.imshow(
        "Simulated Thermal Camera",
        thermal_colored
    )

    print(
        f"Thermal simulation created: "
        f"{scenario}"
    )

    print(
        "Raw thermal data saved as "
        "simulation_thermal_raw.png"
    )

    print(
        "Colorized image saved as "
        "simulation_thermal.png"
    )

    cv2.waitKey(0)

    cv2.destroyAllWindows()