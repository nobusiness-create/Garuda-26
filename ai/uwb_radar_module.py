# ============================================================
# UWB RADAR INTEGRATION MODULE
# SIH26177
# ============================================================

import time
import math
from dataclasses import dataclass, asdict


# ============================================================
# 1. STANDARD UWB OUTPUT
# ============================================================

@dataclass
class UWBDetection:

    timestamp: float

    # Target information
    detected: bool
    human_confidence: float

    # Radar position relative to drone
    range_m: float
    angle_deg: float

    # Human micro-motion / respiration evidence
    micro_motion_confidence: float
    breathing_confidence: float

    # Radar signal quality
    signal_quality: float

    # Useful classification
    concealed_target: bool


# ============================================================
# 2. UWB RADAR DRIVER INTERFACE
# ============================================================

class UWBRadar:

    def __init__(self):
        """
        Initialize the UWB radar.

        Later, replace this with the actual radar
        SDK / serial / USB initialization.
        """

        self.connected = False

    def connect(self):

        # ----------------------------------------------------
        # TEMPORARY SIMULATION
        # ----------------------------------------------------

        self.connected = True

        print("[UWB] Radar connected")

    def read_raw_data(self):
        """
        Read one radar measurement.

        TEMPORARY TEST DATA.
        Replace this function with the actual
        radar hardware interface later.
        """

        return {
            "range_m": 6.8,
            "angle_deg": 14.0,

            "human_confidence": 0.87,
            "micro_motion_confidence": 0.91,
            "breathing_confidence": 0.84,

            "signal_quality": 0.89
        }

    def process_measurement(self, raw):

        human_conf = max(
            0.0,
            min(1.0, raw["human_confidence"])
        )

        micro_motion = max(
            0.0,
            min(1.0, raw["micro_motion_confidence"])
        )

        breathing = max(
            0.0,
            min(1.0, raw["breathing_confidence"])
        )

        signal = max(
            0.0,
            min(1.0, raw["signal_quality"])
        )

        # ----------------------------------------------------
        # Combined UWB human confidence
        # ----------------------------------------------------

        uwb_confidence = (
            0.40 * human_conf +
            0.30 * micro_motion +
            0.20 * breathing +
            0.10 * signal
        )

        detected = (
            uwb_confidence >= 0.60
        )

        # ----------------------------------------------------
        # Concealed target
        # ----------------------------------------------------

        concealed = (
            uwb_confidence >= 0.70
            and
            breathing >= 0.60
        )

        return UWBDetection(

            timestamp=time.time(),

            detected=detected,

            human_confidence=round(
                human_conf,
                3
            ),

            range_m=round(
                raw["range_m"],
                2
            ),

            angle_deg=round(
                raw["angle_deg"],
                2
            ),

            micro_motion_confidence=round(
                micro_motion,
                3
            ),

            breathing_confidence=round(
                breathing,
                3
            ),

            signal_quality=round(
                signal,
                3
            ),

            concealed_target=concealed
        )

    def get_detection(self):

        if not self.connected:

            raise RuntimeError(
                "UWB radar is not connected."
            )

        raw = self.read_raw_data()

        return self.process_measurement(
            raw
        )


# ============================================================
# 3. UWB -> FUSION FORMAT
# ============================================================

def uwb_to_fusion_input(
    uwb: UWBDetection
):

    return {

        "sensor": "UWB_RADAR",

        "timestamp":
            uwb.timestamp,

        "detected":
            uwb.detected,

        "confidence":
            uwb.human_confidence,

        "range_m":
            uwb.range_m,

        "angle_deg":
            uwb.angle_deg,

        "micro_motion":
            uwb.micro_motion_confidence,

        "breathing":
            uwb.breathing_confidence,

        "signal_quality":
            uwb.signal_quality,

        "concealed_target":
            uwb.concealed_target
    }


# ============================================================
# 4. RADAR POLAR -> LOCAL X/Y
# ============================================================

def radar_to_local_xy(
    range_m,
    angle_deg
):

    angle_rad = math.radians(
        angle_deg
    )

    x = (
        range_m *
        math.cos(angle_rad)
    )

    y = (
        range_m *
        math.sin(angle_rad)
    )

    return {

        "x_m":
            round(x, 2),

        "y_m":
            round(y, 2)
    }


# ============================================================
# 5. UWB -> NAVIGATION TARGET
# ============================================================

def create_uwb_navigation_target(
    uwb: UWBDetection
):

    if not uwb.detected:

        return None

    local_position = (
        radar_to_local_xy(
            uwb.range_m,
            uwb.angle_deg
        )
    )

    return {

        "target_detected":
            True,

        "target_source":
            "UWB_RADAR",

        "target_type":
            (
                "CONCEALED_SURVIVOR"
                if uwb.concealed_target
                else "POSSIBLE_SURVIVOR"
            ),

        "confidence":
            uwb.human_confidence,

        "relative_position":
            local_position,

        "range_m":
            uwb.range_m,

        "angle_deg":
            uwb.angle_deg,

        "priority_hint":
            uwb.human_confidence
    }


# ============================================================
# 6. TEST
# ============================================================

def run_uwb_module():

    radar = UWBRadar()

    radar.connect()

    detection = radar.get_detection()

    print("\n================================")
    print("        UWB RADAR OUTPUT")
    print("================================")

    print(
        "Human confidence:",
        detection.human_confidence
    )

    print(
        "Range:",
        detection.range_m,
        "m"
    )

    print(
        "Angle:",
        detection.angle_deg,
        "deg"
    )

    print(
        "Micro-motion:",
        detection.micro_motion_confidence
    )

    print(
        "Breathing:",
        detection.breathing_confidence
    )

    print(
        "Signal quality:",
        detection.signal_quality
    )

    print(
        "Concealed target:",
        detection.concealed_target
    )

    # --------------------------------------------------------
    # UWB -> FUSION
    # --------------------------------------------------------

    fusion_input = (
        uwb_to_fusion_input(
            detection
        )
    )

    print("\nUWB -> EXISTING FUSION")

    print(
        fusion_input
    )

    # --------------------------------------------------------
    # UWB -> NAVIGATION
    # --------------------------------------------------------

    navigation_target = (
        create_uwb_navigation_target(
            detection
        )
    )

    print("\nUWB -> NAVIGATION")

    print(
        navigation_target
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    run_uwb_module()
