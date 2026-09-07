import time
from ultralytics import YOLO


class DisasterDetector:

    def __init__(
        self,
        person_model="yolo11n.pt",
        hazard_model="/home/legion/.cache/huggingface/hub/models--rabahdev--fire-smoke-yolov8n/snapshots/13017fe8af477c25f5298d168e2dfede4b000753/best.pt",
        confidence_threshold=0.25,
        imgsz=960
    ):

        # Person detector
        self.person_model = YOLO(person_model)

        # Fire / smoke detector
        self.hazard_model = YOLO(hazard_model)

        self.confidence_threshold = confidence_threshold
        self.imgsz=imgsz


    def _process_results(self, results, model):
        

        detections = []

        for result in results:

            if result.boxes is None:
                continue

            for box in result.boxes:

                confidence = float(box.conf[0])

                if confidence < self.confidence_threshold:
                    continue

                class_id = int(box.cls[0])

                class_name = model.names[class_id]
                # Only keep disaster-relevant classes
                if model == self.person_model and class_name != "person":
                    continue

                x1, y1, x2, y2 = box.xyxy[0].tolist()

                detection = {
                    "type": class_name,
                    "confidence": round(confidence, 3),
                    "bounding_box": [
                        round(x1),
                        round(y1),
                        round(x2),
                        round(y2)
                    ],
                    "timestamp": time.time()
                }

                detections.append(detection)

        return detections


    def detect(self, frame):

        detections = []

        # -------------------------
        # PERSON DETECTION
        # -------------------------

        person_results = self.person_model(
            frame,
            conf=self.confidence_threshold,
            imgsz=self.imgsz,
            verbose=False
        )

        detections.extend(
            self._process_results(
                person_results,
                self.person_model
            )
        )


        # -------------------------
        # FIRE / SMOKE DETECTION
        # -------------------------

        hazard_results = self.hazard_model(
            frame,
            conf=self.confidence_threshold,
            imgsz=self.imgsz,
            verbose=False
        )

        detections.extend(
            self._process_results(
                hazard_results,
                self.hazard_model
            )
        )


        return detections
