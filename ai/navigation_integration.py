import sys
from pathlib import Path

# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from survivor_assessment import assess_survivor
from coordinate_bridge import relative_uwb_to_grid


# ============================================================
# HELPERS
# ============================================================

def _get_uwb_relative_position(assessment):
    """
    Get UWB relative position safely.

    The assessment may contain the target position either:
      1. inside assessment["navigation_target"]
      2. directly inside assessment["relative_position"]

    Returns:
        {"x_m": ..., "y_m": ...}
        or None
    """

    navigation_target = (
        assessment.get("navigation_target")
        or {}
    )

    relative_position = (
        navigation_target.get("relative_position")
    )

    if relative_position is not None:
        return relative_position

    relative_position = (
        assessment.get("relative_position")
    )

    if relative_position is not None:
        return relative_position

    return None


def _get_navigation_source(assessment):
    navigation_target = (
        assessment.get("navigation_target")
        or {}
    )

    return navigation_target.get(
        "source"
    )


# ============================================================
# MAIN ADAPTER
# ============================================================

def assessment_to_navigation_record(
    assessment,
    survivor_id="S1",
    drone_grid=(2, 2),
    drone_heading_deg=0.0,
    meters_per_cell=1.0,
    perception=None,
):
    """
    Convert AI survivor assessment into a navigation record.

    Important:
      drone_grid, heading and meters_per_cell are currently
      simulation values until the real drone pose is connected.
    """

    target_type = assessment.get(
        "target_type"
    )

    confidence = float(
        assessment.get(
            "assessment_confidence",
            0.0
        )
    )

    # ========================================================
    # UWB-LOCALIZED SURVIVOR
    #
    # Both CONCEALED_SURVIVOR and POSSIBLE_SURVIVOR may have
    # a valid UWB position.
    # ========================================================

    if target_type in (
        "CONCEALED_SURVIVOR",
        "POSSIBLE_SURVIVOR",
    ):

        relative_position = (
            _get_uwb_relative_position(
                assessment
            )
        )

        # The assessment module may intentionally omit the
        # navigation target for POSSIBLE_SURVIVOR. In that case,
        # recover the spatial measurement from the raw UWB
        # perception input.
        if relative_position is None and perception is not None:
            relative_position = perception.get(
                "uwb_relative_position"
            )

        if relative_position is None:

            raise ValueError(
                f"{target_type} has no UWB "
                "relative position."
            )

        bridge = relative_uwb_to_grid(
            relative_position=relative_position,
            drone_grid_position=drone_grid,
            drone_heading_deg=drone_heading_deg,
            meters_per_cell=meters_per_cell,
        )

        source = (
            _get_navigation_source(
                assessment
            )
            or "UWB_RADAR"
        )

        return {
            "id": survivor_id,

            "location": tuple(
                bridge["target_grid"]
            ),

            "detection_confidence": (
                confidence * 100.0
            ),

            # These are initially filled by the navigation
            # integration layer and may be refined later.
            "condition": "UNKNOWN",
            "accessibility": "UNKNOWN",
            "hazard": "UNKNOWN",

            # Rich AI information
            "target_type": target_type,
            "source": source,
            "assessment_confidence": confidence,

            "range_m": assessment.get(
                "range_m"
            ),

            "angle_deg": assessment.get(
                "angle_deg"
            ),

            "relative_position": (
                relative_position
            ),

            "evidence_level": (
                assessment.get(
                    "evidence_level"
                )
            ),

            "evidence": (
                assessment.get(
                    "evidence",
                    []
                )
            ),

            "position_mode": (
                "SIMULATION_TRANSFORM"
            ),
        }

    # ========================================================
    # VISIBLE SURVIVOR
    # ========================================================

    if target_type == "VISIBLE_SURVIVOR":

        return {
            "id": survivor_id,
            "location": None,

            "detection_confidence": (
                confidence * 100.0
            ),

            "condition": "UNKNOWN",
            "accessibility": "UNKNOWN",
            "hazard": "UNKNOWN",

            "target_type": target_type,
            "source": "RGB_THERMAL",
            "assessment_confidence": confidence,

            "evidence_level": (
                assessment.get(
                    "evidence_level"
                )
            ),

            "evidence": (
                assessment.get(
                    "evidence",
                    []
                )
            ),

            "position_mode": (
                "IMAGE_SPACE_ONLY"
            ),
        }

    # ========================================================
    # UNLOCALIZED DETECTION
    # ========================================================

    return {
        "id": survivor_id,
        "location": None,

        "detection_confidence": (
            confidence * 100.0
        ),

        "condition": "UNKNOWN",
        "accessibility": "UNKNOWN",
        "hazard": "UNKNOWN",

        "target_type": target_type,

        "source": (
            _get_navigation_source(
                assessment
            )
        ),

        "assessment_confidence": confidence,

        "evidence_level": (
            assessment.get(
                "evidence_level"
            )
        ),

        "evidence": (
            assessment.get(
                "evidence",
                []
            )
        ),

        "position_mode": (
            "UNLOCALIZED"
        ),
    }


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    perception = {
        "id": 7,

        "visual_confidence": 0.88,
        "thermal_confidence": 0.79,
        "fused_confidence": 0.82,
        "fusion_status": "FUSED_UWB_CONCEALED",

        "audio_distress": True,
        "audio_score": 0.236,
        "audio_status": "MEDIUM",
        "audio_cue": "AUDIO_DISTRESS_CUE",

        "uwb_detected": True,
        "uwb_confidence": 0.87,
        "uwb_range_m": 6.8,
        "uwb_angle_deg": 14.0,
        "uwb_micro_motion": 0.91,
        "uwb_breathing": 0.84,
        "uwb_signal_quality": 0.89,
        "uwb_concealed": True,

        "uwb_relative_position": {
            "x_m": 6.6,
            "y_m": 1.65,
        },

        "uwb_target_type": "CONCEALED_SURVIVOR",
    }

    assessment = assess_survivor(
        perception
    )

    record = assessment_to_navigation_record(
        assessment,
        survivor_id="S1",
        drone_grid=(2, 2),
        drone_heading_deg=0.0,
        meters_per_cell=1.0,
        perception=perception,
    )

    print("\n" + "=" * 70)
    print("NAVIGATION ADAPTER TEST")
    print("=" * 70)

    for key, value in record.items():
        print(
            f"{key}: {value}"
        )

    print("=" * 70)
