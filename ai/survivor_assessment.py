import json


# ============================================================
# SIH26177
# MULTI-SENSOR SURVIVOR ASSESSMENT
#
# Inputs:
#   RGB
#   Thermal
#   Audio
#   UWB Radar
#
# This module interprets sensor evidence.
# It does NOT treat audio alone as survivor detection.
# ============================================================


def assess_survivor(perception):
    """
    Convert unified RGB + thermal + audio + UWB
    perception data into a survivor assessment.
    """

    # --------------------------------------------------------
    # RGB / THERMAL
    # --------------------------------------------------------

    visual_conf = float(
        perception.get(
            "visual_confidence",
            0.0
        )
    )

    thermal_conf = float(
        perception.get(
            "thermal_confidence",
            0.0
        ) or 0.0
    )

    fused_conf = float(
        perception.get(
            "fused_confidence",
            0.0
        ) or 0.0
    )

    rgb_thermal_confirmed = (
        perception.get("fusion_status") == "FUSED"
        and fused_conf >= 0.60
    )

    # --------------------------------------------------------
    # AUDIO
    # --------------------------------------------------------

    audio_distress = bool(
        perception.get(
            "audio_distress",
            False
        )
    )

    audio_score = float(
        perception.get(
            "audio_score",
            0.0
        )
    )

    # --------------------------------------------------------
    # UWB
    # --------------------------------------------------------

    uwb_detected = bool(
        perception.get(
            "uwb_detected",
            False
        )
    )

    uwb_conf = float(
        perception.get(
            "uwb_confidence",
            0.0
        )
    )

    uwb_breathing = float(
        perception.get(
            "uwb_breathing",
            0.0
        )
    )

    uwb_micro_motion = float(
        perception.get(
            "uwb_micro_motion",
            0.0
        )
    )

    uwb_concealed = bool(
        perception.get(
            "uwb_concealed",
            False
        )
    )

    uwb_position = perception.get(
        "uwb_relative_position"
    )

    # ========================================================
    # TARGET TYPE
    # ========================================================

    if (
        uwb_detected
        and uwb_concealed
        and uwb_breathing >= 0.60
    ):

        target_type = "CONCEALED_SURVIVOR"

    elif rgb_thermal_confirmed:

        target_type = "VISIBLE_SURVIVOR"

    elif uwb_detected:

        target_type = "POSSIBLE_SURVIVOR"

    elif audio_distress:

        target_type = "AUDIO_CUE_ONLY"

    else:

        target_type = "UNCONFIRMED"

    # ========================================================
    # EVIDENCE
    # ========================================================

    evidence = []

    if visual_conf >= 0.60:
        evidence.append("RGB_PERSON")

    if thermal_conf >= 0.60:
        evidence.append("THERMAL_SIGNATURE")

    if rgb_thermal_confirmed:
        evidence.append("RGB_THERMAL_CONFIRMATION")

    if audio_distress:
        evidence.append("AUDIO_DISTRESS_CUE")

    if uwb_detected:
        evidence.append("UWB_HUMAN_ACTIVITY")

    if uwb_breathing >= 0.60:
        evidence.append("UWB_BREATHING")

    if uwb_micro_motion >= 0.60:
        evidence.append("UWB_MICRO_MOTION")

    # ========================================================
    # ASSESSMENT CONFIDENCE
    #
    # Rule-based prototype only.
    # This is not a calibrated probability.
    # ========================================================

    if target_type == "CONCEALED_SURVIVOR":

        assessment_confidence = max(
            uwb_conf,
            (
                0.80 * uwb_breathing
                + 0.20 * uwb_micro_motion
            )
        )

    elif target_type == "VISIBLE_SURVIVOR":

        assessment_confidence = max(
            fused_conf,
            (
                0.50 * visual_conf
                + 0.50 * thermal_conf
            )
        )

    elif target_type == "POSSIBLE_SURVIVOR":

        assessment_confidence = uwb_conf

    else:

        assessment_confidence = 0.0

    # --------------------------------------------------------
    # AUDIO SUPPORT
    #
    # Audio can support an already detected survivor,
    # but cannot create a survivor by itself.
    # --------------------------------------------------------

    if (
        target_type in (
            "VISIBLE_SURVIVOR",
            "CONCEALED_SURVIVOR"
        )
        and audio_distress
    ):

        assessment_confidence += min(
            0.05,
            audio_score * 0.10
        )

    assessment_confidence = min(
        1.0,
        assessment_confidence
    )

    # ========================================================
    # EVIDENCE LEVEL
    # ========================================================

    evidence_count = len(evidence)

    if target_type == "CONCEALED_SURVIVOR":

        evidence_level = "HIGH"

    elif (
        target_type == "VISIBLE_SURVIVOR"
        and evidence_count >= 2
    ):

        evidence_level = "HIGH"

    elif target_type == "POSSIBLE_SURVIVOR":

        evidence_level = "MEDIUM"

    elif audio_distress:

        evidence_level = "LOW"

    else:

        evidence_level = "NONE"

    # ========================================================
    # NAVIGATION TARGET
    # ========================================================

    navigation_target = None

    if (
        target_type == "CONCEALED_SURVIVOR"
        and uwb_position is not None
    ):

        navigation_target = {
            "target_type": "CONCEALED_SURVIVOR",
            "source": "UWB_RADAR",
            "confidence": round(
                assessment_confidence,
                3
            ),
            "relative_position": uwb_position,
            "range_m": perception.get(
                "uwb_range_m"
            ),
            "angle_deg": perception.get(
                "uwb_angle_deg"
            )
        }

    elif target_type == "VISIBLE_SURVIVOR":

        navigation_target = {
            "target_type": "VISIBLE_SURVIVOR",
            "source": "RGB_THERMAL",
            "confidence": round(
                assessment_confidence,
                3
            ),
            "bounding_box": perception.get(
                "bounding_box"
            )
        }

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {

        "survivor_detected": (
            target_type in (
                "VISIBLE_SURVIVOR",
                "CONCEALED_SURVIVOR"
            )
        ),

        "target_type": target_type,

        "assessment_confidence": round(
            assessment_confidence,
            3
        ),

        "evidence_level": evidence_level,

        "evidence": evidence,

        "audio_support": audio_distress,

        "uwb_support": uwb_detected,

        "navigation_target": navigation_target,

        "timestamp": perception.get(
            "timestamp"
        )
    }


def print_assessment(result):

    print("\n" + "=" * 60)
    print("SIH26177 SURVIVOR ASSESSMENT")
    print("=" * 60)

    print(
        json.dumps(
            result,
            indent=4
        )
    )

    print("=" * 60)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    perception = {

        "id": 7,

        "type": "person",

        "visual_confidence": 0.88,

        "thermal_confidence": 0.79,

        "fused_confidence": 0.82,

        "fusion_status":
            "FUSED_UWB_CONCEALED",

        "audio_distress": True,

        "audio_score": 0.236,

        "audio_status": "MEDIUM",

        "audio_cue":
            "AUDIO_DISTRESS_CUE",

        "uwb_detected": True,

        "uwb_confidence": 0.87,

        "uwb_range_m": 6.8,

        "uwb_angle_deg": 14.0,

        "uwb_micro_motion": 0.91,

        "uwb_breathing": 0.84,

        "uwb_signal_quality": 0.89,

        "uwb_concealed": True,

        "uwb_relative_position": {
            "x_m": 6.60,
            "y_m": 1.65
        },

        "bounding_box": [
            222,
            408,
            348,
            861
        ],

        "timestamp": 1788028034.77
    }

    result = assess_survivor(
        perception
    )

    print_assessment(
        result
    )
