import json
import time
import math


def radar_to_local_xy(range_m, angle_deg):
    """
    Convert UWB radar range + angle into local X/Y
    coordinates relative to the drone.
    """

    angle_rad = math.radians(
        float(angle_deg)
    )

    x = float(range_m) * math.cos(angle_rad)
    y = float(range_m) * math.sin(angle_rad)

    return {
        "x_m": round(x, 2),
        "y_m": round(y, 2)
    }


def create_perception_output(
    track_id,
    ai_result,
    fused_result=None,
    audio_result=None,
    uwb_result=None
):
    """
    Common SIH26177 perception output.

    Sources:
        RGB
        Thermal
        Audio
        UWB radar
    """

    output = {
        "id": track_id,

        "type": "person",

        "confidence": round(
            float(ai_result["confidence"]),
            3
        ),

        "visual_confidence": round(
            float(ai_result["confidence"]),
            3
        ),

        "thermal_confidence": None,

        "fused_confidence": None,

        "fusion_status": "RGB_ONLY",

        "dominant_sensor": "RGB",

        "bounding_box": ai_result.get(
            "bounding_box"
        ),

        "timestamp": ai_result.get(
            "timestamp",
            time.time()
        ),

        # ----------------------------------------------------
        # AUDIO
        # ----------------------------------------------------

        "audio_distress": False,

        "audio_score": 0.0,

        "audio_status": "LOW",

        "audio_cue": "NONE",

        # ----------------------------------------------------
        # UWB RADAR
        # ----------------------------------------------------

        "uwb_detected": False,

        "uwb_confidence": 0.0,

        "uwb_range_m": None,

        "uwb_angle_deg": None,

        "uwb_micro_motion": 0.0,

        "uwb_breathing": 0.0,

        "uwb_signal_quality": 0.0,

        "uwb_concealed": False,

        "uwb_relative_position": None,

        "uwb_target_type": None
    }


    # ========================================================
    # RGB + THERMAL
    # ========================================================

    if (
        fused_result is not None
        and
        fused_result.get(
            "fusion_status"
        ) == "FUSED"
    ):

        output["fused_confidence"] = round(
            float(
                fused_result.get(
                    "confidence",
                    ai_result["confidence"]
                )
            ),
            3
        )

        output["thermal_confidence"] = round(
            float(
                fused_result.get(
                    "thermal_confidence",
                    0.0
                )
            ),
            3
        )

        output["fusion_status"] = "FUSED"

        output["dominant_sensor"] = fused_result.get(
            "dominant_sensor",
            "UNKNOWN"
        )


    # ========================================================
    # AUDIO
    # ========================================================

    if audio_result is not None:

        output["audio_distress"] = bool(
            audio_result.get(
                "audio_distress",
                False
            )
        )

        output["audio_score"] = round(
            float(
                audio_result.get(
                    "audio_score",
                    0.0
                )
            ),
            3
        )

        output["audio_status"] = audio_result.get(
            "audio_status",
            "LOW"
        )

        output["audio_cue"] = audio_result.get(
            "audio_cue",
            "NONE"
        )


    # ========================================================
    # UWB RADAR
    # ========================================================

    if uwb_result is not None:

        output["uwb_detected"] = bool(
            uwb_result.get(
                "detected",
                False
            )
        )

        output["uwb_confidence"] = round(
            float(
                uwb_result.get(
                    "human_confidence",
                    uwb_result.get(
                        "confidence",
                        0.0
                    )
                )
            ),
            3
        )

        if uwb_result.get("range_m") is not None:

            output["uwb_range_m"] = round(
                float(
                    uwb_result["range_m"]
                ),
                2
            )

        if uwb_result.get("angle_deg") is not None:

            output["uwb_angle_deg"] = round(
                float(
                    uwb_result["angle_deg"]
                ),
                2
            )

        output["uwb_micro_motion"] = round(
            float(
                uwb_result.get(
                    "micro_motion",
                    uwb_result.get(
                        "micro_motion_confidence",
                        0.0
                    )
                )
            ),
            3
        )

        output["uwb_breathing"] = round(
            float(
                uwb_result.get(
                    "breathing",
                    uwb_result.get(
                        "breathing_confidence",
                        0.0
                    )
                )
            ),
            3
        )

        output["uwb_signal_quality"] = round(
            float(
                uwb_result.get(
                    "signal_quality",
                    0.0
                )
            ),
            3
        )

        output["uwb_concealed"] = bool(
            uwb_result.get(
                "concealed_target",
                False
            )
        )

        # -----------------------------------------------
        # Radar range + angle -> local position
        # -----------------------------------------------

        if (
            output["uwb_range_m"] is not None
            and
            output["uwb_angle_deg"] is not None
        ):

            output["uwb_relative_position"] = (
                radar_to_local_xy(
                    output["uwb_range_m"],
                    output["uwb_angle_deg"]
                )
            )

        # -----------------------------------------------
        # UWB target classification
        # -----------------------------------------------

        if output["uwb_detected"]:

            if output["uwb_concealed"]:

                output["uwb_target_type"] = (
                    "CONCEALED_SURVIVOR"
                )

            else:

                output["uwb_target_type"] = (
                    "POSSIBLE_SURVIVOR"
                )


    # ========================================================
    # COMBINED FUSION STATUS
    # ========================================================

    if output["uwb_detected"]:

        if output["uwb_concealed"]:

            output["fusion_status"] = (
                "FUSED_UWB_CONCEALED"
            )

        elif output["fusion_status"] == "FUSED":

            output["fusion_status"] = (
                "FUSED_RGB_THERMAL_UWB"
            )

        else:

            output["fusion_status"] = (
                "UWB_SUPPORTED"
            )


    return output


def print_perception_output(data):
    """
    Human-readable display for debugging.
    """

    print("\n" + "=" * 60)
    print("SIH26177 PERCEPTION OUTPUT")
    print("=" * 60)

    print(
        json.dumps(
            data,
            indent=4
        )
    )

    print("=" * 60)
