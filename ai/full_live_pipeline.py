import cv2
import json
import subprocess
import sys
import time
from pathlib import Path

from ultralytics import YOLO

# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ============================================================
# EXISTING PROJECT MODULES
# ============================================================

from ai_fusion_connector import connect_ai_and_thermal
from simulation.thermal_sim import create_thermal_scene
from survivor_assessment import assess_survivor
from navigation_integration import assessment_to_navigation_record

from navigation.navigation_core import (
    drone_position,
    prioritize_survivors,
    a_star,
    calculate_path_distance,
    calculate_path_risk,
)

from navigation.flight_control import (
    adaptive_flight_controller,
)


# ============================================================
# SETTINGS
# ============================================================

VIDEO_PATH = "../test_video.mp4"
MODEL_PATH = "yolo11n.pt"

AUDIO_WAV_PATH = (
    "../audio_tests/"
    "freesound_community-help-echo-81995.wav"
)

AUDIO_WORKER = (
    Path(__file__).resolve().parent
    / "audio_worker.py"
)

CONFIDENCE = 0.30
IMAGE_SIZE = 960


# ============================================================
# SIMULATED UWB INPUT
#
# IMPORTANT:
# This is NOT physical UWB hardware.
# It demonstrates how the UWB output enters the pipeline.
# ============================================================

UWB_TEST = {
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


# ============================================================
# SIMULATED DRONE STATE
#
# These will later come from MAVLink.
# ============================================================

DRONE_GRID = (2, 2)
DRONE_HEADING_DEG = 0.0
METERS_PER_CELL = 1.0

BATTERY_PERCENT = 75.0
CURRENT_SPEED = 3.0
CURRENT_ALTITUDE = 20.0


# ============================================================
# AUDIO ANALYSIS
# Run TensorFlow/YAMNet in a separate process so that the
# vision loop remains stable.
# ============================================================

def analyze_audio():
    print("\nAnalyzing audio...")

    try:

        result = subprocess.run(
            [
                sys.executable,
                str(AUDIO_WORKER),
                AUDIO_WAV_PATH,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        lines = [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        ]

        if not lines:
            raise RuntimeError(
                "Audio worker produced no result."
            )

        audio_result = json.loads(
            lines[-1]
        )

        if "error" in audio_result:
            raise RuntimeError(
                audio_result["error"]
            )

        return audio_result

    except Exception as exc:

        print(
            f"Audio analysis failed: {exc}"
        )

        return {
            "audio_status": "LOW",
            "audio_cue": "NONE",
            "audio_distress": False,
            "audio_score": 0.0,
            "audio_mean_score": 0.0,
            "distress_frames": 0,
            "persistent_frames": 0,
            "persistent_groups": 0,
        }


# ============================================================
# BUILD PERCEPTION RECORD
# ============================================================

def build_perception(
    track_id,
    confidence,
    bbox,
    fused,
    audio_result,
):
    if fused is not None:

        thermal_confidence = float(
            fused.get(
                "thermal_confidence",
                0.0,
            )
        )

        fused_confidence = float(
            fused.get(
                "confidence",
                confidence,
            )
        )

        fusion_status = fused.get(
            "fusion_status",
            "RGB_ONLY",
        )

    else:

        thermal_confidence = 0.0
        fused_confidence = confidence
        fusion_status = "RGB_ONLY"

    return {
        "id": track_id,

        # REAL RGB value from YOLO
        "visual_confidence": confidence,

        # RGB bounding box
        "bounding_box": bbox,

        # Thermal / fusion
        "thermal_confidence": thermal_confidence,
        "fused_confidence": fused_confidence,
        "fusion_status": fusion_status,

        # Audio
        "audio_distress": bool(
            audio_result.get(
                "audio_distress",
                False,
            )
        ),

        "audio_score": float(
            audio_result.get(
                "audio_score",
                0.0,
            )
        ),

        "audio_status": audio_result.get(
            "audio_status",
            "LOW",
        ),

        "audio_cue": audio_result.get(
            "audio_cue",
            "NONE",
        ),

        # UWB
        "uwb_detected": UWB_TEST[
            "uwb_detected"
        ],

        "uwb_confidence": UWB_TEST[
            "uwb_confidence"
        ],

        "uwb_range_m": UWB_TEST[
            "uwb_range_m"
        ],

        "uwb_angle_deg": UWB_TEST[
            "uwb_angle_deg"
        ],

        "uwb_micro_motion": UWB_TEST[
            "uwb_micro_motion"
        ],

        "uwb_breathing": UWB_TEST[
            "uwb_breathing"
        ],

        "uwb_signal_quality": UWB_TEST[
            "uwb_signal_quality"
        ],

        "uwb_concealed": UWB_TEST[
            "uwb_concealed"
        ],

        "uwb_relative_position": UWB_TEST[
            "uwb_relative_position"
        ],

        "uwb_target_type": UWB_TEST[
            "uwb_target_type"
        ],
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 78)
    print(
        "SIH26177 FULL LIVE RGB → AI → NAVIGATION PIPELINE"
    )
    print("=" * 78)

    print(
        "RGB input       : REAL VIDEO"
    )

    print(
        "Thermal         : SIMULATED"
    )

    print(
        "Audio           : TEST WAV"
    )

    print(
        "UWB             : SIMULATED TEST VALUES"
    )

    print(
        "Drone pose      : SIMULATED"
    )

    print(
        "Battery/state   : SIMULATED"
    )

    print("=" * 78)


    # ========================================================
    # AUDIO
    # ========================================================

    audio_result = analyze_audio()

    print(
        f"Audio status    : "
        f"{audio_result['audio_status']}"
    )

    print(
        f"Audio cue       : "
        f"{audio_result['audio_cue']}"
    )


    # ========================================================
    # YOLO
    # ========================================================

    print("\nLoading YOLO...")

    model = YOLO(
        MODEL_PATH
    )


    # ========================================================
    # VIDEO
    # ========================================================

    cap = cv2.VideoCapture(
        VIDEO_PATH
    )

    if not cap.isOpened():

        raise RuntimeError(
            f"Could not open video: {VIDEO_PATH}"
        )


    frame_count = 0
    selected_target = None
    latest_safe_path = None


    print("\nStarting live pipeline...")
    print("Press Q to quit.")


    while cap.isOpened():

        success, frame = cap.read()

        if not success:
            break

        frame_count += 1


        # ====================================================
        # REAL YOLO TRACKING
        # ====================================================

        results = model.track(

            frame,

            persist=True,

            tracker="botsort.yaml",

            classes=[0],

            conf=CONFIDENCE,

            imgsz=IMAGE_SIZE,

            verbose=False,
        )

        result = results[0]


        # ====================================================
        # SIMULATED THERMAL
        # ====================================================

        thermal_image = create_thermal_scene(
            scenario="day"
        )


        detections = []


        if result.boxes is not None:

            for box in result.boxes:

                confidence = float(
                    box.conf[0]
                )

                x1, y1, x2, y2 = (
                    box.xyxy[0].tolist()
                )

                bbox = [
                    int(x1),
                    int(y1),
                    int(x2),
                    int(y2),
                ]


                if box.id is not None:

                    track_id = int(
                        box.id[0]
                    )

                else:

                    track_id = -1


                # =================================================
                # RGB + THERMAL FUSION
                # =================================================

                ai_result = {
                    "type": "person",
                    "confidence": confidence,
                    "bounding_box": bbox,
                    "timestamp": time.time(),
                }


                try:

                    fused = (
                        connect_ai_and_thermal(
                            ai_result,
                            thermal_image,
                            condition="day",
                            brightness=0.90,
                            blur=0.05,
                            smoke=0.00,
                        )
                    )

                except Exception:

                    fused = None


                perception = build_perception(
                    track_id,
                    confidence,
                    bbox,
                    fused,
                    audio_result,
                )


                # =================================================
                # SURVIVOR ASSESSMENT
                # =================================================

                try:

                    assessment = (
                        assess_survivor(
                            perception
                        )
                    )

                except Exception as exc:

                    print(
                        f"Assessment error: {exc}"
                    )

                    assessment = None


                detections.append(
                    (
                        confidence,
                        track_id,
                        bbox,
                        perception,
                        assessment,
                    )
                )


        # ========================================================
        # SELECT STRONGEST REAL RGB DETECTION
        # ========================================================

        if detections:

            detections.sort(
                key=lambda item: item[0],
                reverse=True,
            )

            best = detections[0]

            (
                best_confidence,
                best_track_id,
                best_bbox,
                best_perception,
                best_assessment,
            ) = best


            # ====================================================
            # NAVIGATION
            #
            # The navigation target is still based on the
            # simulated UWB position.
            # The RGB confidence is REAL from the video.
            # ====================================================

            if best_assessment is not None:

                try:

                    nav_record = (
                        assessment_to_navigation_record(
                            best_assessment,
                            survivor_id=f"S-{best_track_id}",

                            drone_grid=DRONE_GRID,

                            drone_heading_deg=(
                                DRONE_HEADING_DEG
                            ),

                            meters_per_cell=(
                                METERS_PER_CELL
                            ),

                            perception=best_perception,
                        )
                    )

                    # Check whether the target has a
                    # valid navigation location.

                    if nav_record.get(
                        "location"
                    ) is not None:

                        prioritized = (
                            prioritize_survivors(
                                [nav_record]
                            )
                        )

                        selected_target = (
                            prioritized[0]
                        )

                        goal = tuple(
                            selected_target[
                                "location"
                            ]
                        )

                        latest_safe_path = (
                            a_star(
                                drone_position,
                                goal,
                                risk_aware=True,
                            )
                        )

                        if latest_safe_path:

                            path_distance = (
                                calculate_path_distance(
                                    latest_safe_path
                                )
                            )

                            path_risk, fire, flood = (
                                calculate_path_risk(
                                    latest_safe_path
                                )
                            )

                        else:

                            path_distance = None
                            path_risk = None
                            fire = None
                            flood = None


                        if path_risk is None:

                            obstacle_level = 1.0

                        elif path_risk <= 0:

                            obstacle_level = 0.0

                        elif path_risk <= 5:

                            obstacle_level = 0.3

                        elif path_risk <= 10:

                            obstacle_level = 0.6

                        else:

                            obstacle_level = 1.0


                        flight = (
                            adaptive_flight_controller(
                                survivor_probability=(
                                    float(
                                        best_assessment.get(
                                            "assessment_confidence",
                                            best_confidence,
                                        )
                                    )
                                ),
                                obstacle_level=(
                                    obstacle_level
                                ),
                                battery_percent=(
                                    BATTERY_PERCENT
                                ),
                                current_speed=(
                                    CURRENT_SPEED
                                ),
                                current_altitude=(
                                    CURRENT_ALTITUDE
                                ),
                            )
                        )


                    else:

                        selected_target = None

                except Exception as exc:

                    print(
                        f"Navigation error: {exc}"
                    )

                    selected_target = None

            else:

                selected_target = None


        else:

            best_confidence = 0.0
            best_track_id = -1
            best_bbox = None
            selected_target = None


        # ========================================================
        # VISUALIZATION
        # ========================================================

        person_count = len(
            detections
        )


        for (
            confidence,
            track_id,
            bbox,
            perception,
            assessment,
        ) in detections:

            x1, y1, x2, y2 = bbox

            is_best = (
                track_id
                == best_track_id
            )

            thickness = 3 if is_best else 2

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                thickness,
            )


            fused_conf = float(
                perception.get(
                    "fused_confidence",
                    confidence,
                )
            )

            thermal_conf = float(
                perception.get(
                    "thermal_confidence",
                    0.0,
                )
            )


            label = (
                f"ID:{track_id} "
                f"RGB:{confidence:.2f} "
                f"TH:{thermal_conf:.2f} "
                f"FUSED:{fused_conf:.2f}"
            )


            cv2.putText(
                frame,
                label,
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (0, 255, 0),
                2,
            )


        # --------------------------------------------------------
        # TOP STATUS
        # --------------------------------------------------------

        cv2.putText(
            frame,
            f"Persons: {person_count}",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.70,
            (255, 255, 255),
            2,
        )


        cv2.putText(
            frame,
            f"Audio: {audio_result['audio_status']}",
            (20, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.70,
            (255, 255, 255),
            2,
        )


        if selected_target is not None:

            cv2.putText(
                frame,
                (
                    f"TARGET: "
                    f"{selected_target['id']} "
                    f"{selected_target['priority']}"
                ),
                (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 255),
                2,
            )


            cv2.putText(
                frame,
                (
                    "ACTION: "
                    + flight["mission_action"]
                ),
                (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 255),
                2,
            )


        cv2.imshow(
            "SIH26177 FULL AI PIPELINE",
            frame,
        )


        key = (
            cv2.waitKey(1)
            & 0xFF
        )

        if key == ord("q"):
            break


    cap.release()
    cv2.destroyAllWindows()


    print("\n" + "=" * 78)
    print("FULL LIVE RGB PIPELINE COMPLETE")
    print("=" * 78)

    print(
        f"Frames processed : {frame_count}"
    )

    if selected_target is not None:

        print(
            f"Selected target  : "
            f"{selected_target['id']}"
        )

        print(
            f"Target type      : "
            f"{selected_target['target_type']}"
        )

        print(
            f"RGB confidence   : "
            f"{best_confidence:.3f}"
        )

        print(
            f"Priority         : "
            f"{selected_target['priority']}"
        )

        print(
            f"Priority score   : "
            f"{selected_target['priority_score']:.1f}"
        )

        if latest_safe_path:

            print(
                f"A* path cells    : "
                f"{len(latest_safe_path)}"
            )

            print(
                f"A* path distance : "
                f"{calculate_path_distance(latest_safe_path):.2f}"
            )

    print("=" * 78)


if __name__ == "__main__":
    main()
