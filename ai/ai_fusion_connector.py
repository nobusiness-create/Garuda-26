from typing import Dict, Any, Optional
import time

from role2_complete_sensor_fusion import (
    Detection,
    SensorFusionEngine
)

from preprocessing.thermal import (
    calculate_thermal_evidence
)

from simulation.thermal_sim import (
    create_thermal_scene
)


# ============================================================
# AI OUTPUT -> FUSION INPUT
# ============================================================

def ai_output_to_detection(
    ai_result: Dict[str, Any]
) -> Optional[Detection]:

    required_fields = [
        "type",
        "confidence",
        "timestamp"
    ]

    for field in required_fields:

        if field not in ai_result:

            print(
                f"ERROR: AI output is missing '{field}'"
            )

            return None

    object_type = str(
        ai_result["type"]
    ).lower()

    if object_type == "person":

        object_type = "survivor"

    return Detection(

        sensor="RGB",

        object_type=object_type,

        confidence=float(
            ai_result["confidence"]
        ),

        timestamp=float(
            ai_result["timestamp"]
        ),

        bounding_box=ai_result.get(
            "bounding_box"
        )
    )


# ============================================================
# YOUR THERMAL ANALYSIS -> FUSION INPUT
# ============================================================

def run_thermal_analysis(
    thermal_image,
    survivor_box,
    timestamp
):

    thermal_result = calculate_thermal_evidence(

        thermal_image,

        survivor_box
    )

    return {

        "type": "survivor",

        "confidence":
            thermal_result[
                "thermal_confidence"
            ],

        "timestamp":
            timestamp,

        "bounding_box":
            list(survivor_box),

        "thermal_analysis":
            thermal_result
    }


# ============================================================
# THERMAL RESULT -> DETECTION
# ============================================================

def thermal_output_to_detection(
    thermal_result: Optional[Dict[str, Any]]
) -> Optional[Detection]:

    if thermal_result is None:

        return None

    return Detection(

        sensor="THERMAL",

        object_type=str(
            thermal_result["type"]
        ),

        confidence=float(
            thermal_result["confidence"]
        ),

        timestamp=float(
            thermal_result["timestamp"]
        ),

        bounding_box=thermal_result.get(
            "bounding_box"
        )
    )


# ============================================================
# MAIN CONNECTION
# ============================================================

def connect_ai_and_thermal(

    ai_result: Dict[str, Any],

    thermal_image,

    condition="day",

    brightness=0.90,

    blur=0.05,

    smoke=0.00
):

    # --------------------------------------------------------
    # CREATE FUSION ENGINE
    # --------------------------------------------------------

    fusion = SensorFusionEngine(

        max_time_difference=0.15
    )

    # --------------------------------------------------------
    # RGB / AI DETECTION
    # --------------------------------------------------------

    rgb_detection = (
        ai_output_to_detection(
            ai_result
        )
    )

    if rgb_detection is None:

        return {

            "status": "ERROR",

            "message":
                "Invalid AI output"
        }

    # --------------------------------------------------------
    # GET AI BOUNDING BOX
    # --------------------------------------------------------

    survivor_box = (
        ai_result.get(
            "bounding_box"
        )
    )

    if survivor_box is None:

        return {

            "status": "ERROR",

            "message":
                "AI output has no bounding_box"
        }

    # --------------------------------------------------------
    # RUN YOUR THERMAL ANALYSIS
    # --------------------------------------------------------

    thermal_result = (
        run_thermal_analysis(

            thermal_image,

            survivor_box,

            rgb_detection.timestamp
        )
    )

    # --------------------------------------------------------
    # THERMAL DETECTION
    # --------------------------------------------------------

    thermal_detection = (
        thermal_output_to_detection(
            thermal_result
        )
    )

    # --------------------------------------------------------
    # RGB RELIABILITY
    # --------------------------------------------------------

    rgb_reliability = (
        fusion.calculate_rgb_reliability(

            brightness=brightness,

            blur=blur,

            smoke=smoke,

            condition=condition
        )
    )

    # --------------------------------------------------------
    # THERMAL RELIABILITY
    # --------------------------------------------------------

    thermal_quality = (
        thermal_result[
            "confidence"
        ]
    )

    thermal_reliability = (
        fusion.calculate_thermal_reliability(

            thermal_quality=
                thermal_quality,

            saturation=0.05,

            condition=condition
        )
    )

    # --------------------------------------------------------
    # UPDATE RGB HEALTH
    # --------------------------------------------------------

    fusion.update_sensor(

        sensor_name="RGB",

        timestamp=
            rgb_detection.timestamp,

        available=True,

        quality=
            rgb_reliability,

        reason=
            "AI RGB detection received"
    )

    # --------------------------------------------------------
    # UPDATE THERMAL HEALTH
    # --------------------------------------------------------

    fusion.update_sensor(

        sensor_name="THERMAL",

        timestamp=
            thermal_detection.timestamp,

        available=True,

        quality=
            thermal_reliability,

        reason=
            "Thermal analysis completed"
    )

    # --------------------------------------------------------
    # FUSE
    # --------------------------------------------------------

    result = fusion.fuse(

        rgb_detection=
            rgb_detection,

        thermal_detection=
            thermal_detection
    )

    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    return {

        "type":
            result.object_type,

        "confidence":
            result.fused_confidence,

        "visual_confidence":
            result.rgb_confidence,

        "thermal_confidence":
            result.thermal_confidence,

        "rgb_reliability":
            result.rgb_reliability,

        "thermal_reliability":
            result.thermal_reliability,

        "timestamp":
            result.timestamp,

        "fusion_status":
            result.fusion_status,

        "dominant_sensor":
            result.dominant_sensor,

        "rgb_status":
            result.rgb_status,

        "thermal_status":
            result.thermal_status,

        "explanation":
            result.explanation,

        "bounding_box":
            ai_result.get(
                "bounding_box"
            ),

        "thermal_analysis":
            thermal_result[
                "thermal_analysis"
            ]
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\n")
    print("=" * 60)
    print("AI + YOUR THERMAL ANALYSIS + FUSION TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # SIMULATED AI RESULT
    # --------------------------------------------------------

    ai_result = {

        "type": "person",

        "confidence": 0.888,

        "bounding_box":
            [255, 215, 390, 400],

        "timestamp":
            time.time()
    }

    # --------------------------------------------------------
    # TEMPORARY THERMAL IMAGE
    # --------------------------------------------------------

    thermal_image = (
        create_thermal_scene(
            "fire_smoke"
        )
    )

    # --------------------------------------------------------
    # RUN COMPLETE CONNECTION
    # --------------------------------------------------------

    result = connect_ai_and_thermal(

        ai_result=
            ai_result,

        thermal_image=
            thermal_image,

        condition="night",

        brightness=0.15,

        blur=0.05,

        smoke=0.00
    )

    # --------------------------------------------------------
    # PRINT RESULT
    # --------------------------------------------------------

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )