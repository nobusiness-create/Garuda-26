import csv
import os
import wave
import numpy as np

import tensorflow as tf
import tensorflow_hub as hub


YAMNET_URL = "https://tfhub.dev/google/yamnet/1"
SAMPLE_RATE = 16000

FRAME_THRESHOLD = 0.15
MIN_DISTRESS_FRAMES = 2
MAX_FRAME_GAP = 2

DISTRESS_CLASSES = [
    "Screaming",
    "Shout",
    "Yell",
    "Whimper",
]


print("Loading YAMNet audio module...")
model = hub.load(YAMNET_URL)

class_map = tf.keras.utils.get_file(
    "yamnet_class_map.csv",
    "https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv"
)

class_names = []

with open(class_map, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)

    for row in reader:
        class_names.append(row[2])


class_to_index = {
    name.lower(): i
    for i, name in enumerate(class_names)
}


def load_wav(path):

    with wave.open(path, "rb") as wav:

        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        frame_count = wav.getnframes()

        raw = wav.readframes(frame_count)

    if sample_width == 2:

        audio = np.frombuffer(
            raw,
            dtype=np.int16
        ).astype(np.float32)

        audio /= 32768.0

    elif sample_width == 4:

        audio = np.frombuffer(
            raw,
            dtype=np.int32
        ).astype(np.float32)

        audio /= 2147483648.0

    else:

        raise ValueError(
            f"Unsupported WAV sample width: {sample_width}"
        )

    if channels > 1:

        audio = audio.reshape(-1, channels)
        audio = np.mean(audio, axis=1)

    if sample_rate != SAMPLE_RATE:

        raise ValueError(
            f"Expected {SAMPLE_RATE} Hz audio, "
            f"got {sample_rate} Hz"
        )

    return audio


def analyze_audio_file(path):

    if not os.path.exists(path):

        raise FileNotFoundError(path)

    audio = load_wav(path)

    scores, _, _ = model(audio)
    scores = scores.numpy()

    distress_frame_scores = []

    for frame in scores:

        values = []

        for class_name in DISTRESS_CLASSES:

            index = class_to_index.get(
                class_name.lower()
            )

            if index is not None:

                values.append(
                    float(frame[index])
                )

        if values:

            distress_frame_scores.append(
                max(values)
            )

        else:

            distress_frame_scores.append(0.0)

    distress_frame_scores = np.array(
        distress_frame_scores
    )

    distress_frames = np.where(
        distress_frame_scores >= FRAME_THRESHOLD
    )[0]

    # --------------------------------------------------------
    # Group nearby distress frames
    # --------------------------------------------------------

    groups = []
    current_group = []

    for frame_idx in distress_frames:

        if not current_group:

            current_group = [int(frame_idx)]

        elif frame_idx - current_group[-1] <= MAX_FRAME_GAP:

            current_group.append(int(frame_idx))

        else:

            groups.append(current_group)
            current_group = [int(frame_idx)]

    if current_group:
        groups.append(current_group)

    persistent_groups = [
        group
        for group in groups
        if len(group) >= MIN_DISTRESS_FRAMES
    ]

    persistent_frames = [
        frame
        for group in persistent_groups
        for frame in group
    ]

    peak_distress = (
        float(np.max(distress_frame_scores))
        if len(distress_frame_scores)
        else 0.0
    )

    mean_distress = (
        float(np.mean(distress_frame_scores))
        if len(distress_frame_scores)
        else 0.0
    )

    if len(persistent_frames) >= MIN_DISTRESS_FRAMES:

        if peak_distress >= 0.30:
            status = "HIGH"
        else:
            status = "MEDIUM"

        cue = "AUDIO_DISTRESS_CUE"

    else:

        status = "LOW"
        cue = "NONE"

    return {
        "audio_status": status,
        "audio_cue": cue,
        "audio_distress": cue == "AUDIO_DISTRESS_CUE",
        "audio_score": round(peak_distress, 3),
        "audio_mean_score": round(mean_distress, 3),
        "distress_frames": len(distress_frames),
        "persistent_frames": len(persistent_frames),
        "persistent_groups": len(persistent_groups),
    }


if __name__ == "__main__":

    test_file = (
        "/home/legion/sih_drone/audio_tests/"
        "freesound_community-help-echo-81995.wav"
    )

    result = analyze_audio_file(test_file)

    print("\nAudio module test:")
    print("=" * 50)

    for key, value in result.items():
        print(f"{key}: {value}")
