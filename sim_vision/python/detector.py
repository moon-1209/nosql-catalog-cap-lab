"""Bộ nhận diện người. `Detector` là interface để test dùng model giả."""

from __future__ import annotations

import time
from typing import Any, Protocol

import numpy as np

from protocol import YOLO_CONF

PERSON_CLASS_ID: int = 0  # COCO


class Detector(Protocol):
    def detect(self, img: np.ndarray) -> tuple[list[dict[str, float]], float]:
        """Trả `(detections, infer_ms)`; detections theo Mục 2.2, sắp conf giảm dần."""
        ...


def normalize_boxes(
    xyxy: np.ndarray, confs: np.ndarray, width: int, height: int
) -> list[dict[str, float]]:
    """Box pixel ➔ tọa độ chuẩn hóa [0, 1], làm tròn 4 chữ số, sắp conf giảm dần.

    Box suy biến sau khi kẹp/làm tròn (x1 >= x2 hoặc y1 >= y2) bị bỏ.
    """
    dets: list[dict[str, float]] = []
    for (x1, y1, x2, y2), conf in zip(np.asarray(xyxy, dtype=float), np.asarray(confs, dtype=float)):
        d = {
            "x1": round(min(max(x1 / width, 0.0), 1.0), 4),
            "y1": round(min(max(y1 / height, 0.0), 1.0), 4),
            "x2": round(min(max(x2 / width, 0.0), 1.0), 4),
            "y2": round(min(max(y2 / height, 0.0), 1.0), 4),
            "conf": round(float(conf), 4),
        }
        if d["x1"] < d["x2"] and d["y1"] < d["y2"]:
            dets.append(d)
    dets.sort(key=lambda d: d["conf"], reverse=True)
    return dets


class YoloDetector:
    """YOLOv8n qua ultralytics. Load model một lần lúc khởi tạo."""

    def __init__(self, model_path: str, conf: float = YOLO_CONF) -> None:
        from ultralytics import YOLO  # import trễ: test không cần ultralytics

        self._model: Any = YOLO(model_path)
        self._conf: float = conf
        # Chạy nháp một lần để frame đầu tiên không bị tính thời gian khởi động.
        self._model(np.zeros((480, 640, 3), dtype=np.uint8), classes=[PERSON_CLASS_ID],
                    conf=self._conf, verbose=False)

    def detect(self, img: np.ndarray) -> tuple[list[dict[str, float]], float]:
        t0 = time.perf_counter()
        result = self._model(img, classes=[PERSON_CLASS_ID], conf=self._conf, verbose=False)[0]
        boxes = result.boxes
        h, w = img.shape[:2]
        dets = normalize_boxes(boxes.xyxy.cpu().numpy(), boxes.conf.cpu().numpy(), w, h)
        return dets, (time.perf_counter() - t0) * 1000.0
