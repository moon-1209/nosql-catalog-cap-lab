from __future__ import annotations

import base64
import json
import threading
import time

import cv2
import numpy as np
import pytest


def make_frame_msg(frame_id: int, width: int = 64, height: int = 48) -> str:
    img = np.full((height, width, 3), 127, dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return json.dumps({
        "type": "frame", "frame_id": frame_id, "width": width, "height": height,
        "jpeg_b64": base64.b64encode(buf.tobytes()).decode("ascii"),
    })


class FakeDetector:
    """Trả kết quả cố định; có thể chặn để giả lập suy luận chậm."""

    def __init__(self, dets: list[dict[str, float]] | None = None, infer_ms: float = 12.34) -> None:
        self.dets = dets or []
        self.infer_ms = infer_ms
        self.calls = 0
        self.gate: threading.Event | None = None
        self.started = threading.Event()

    def detect(self, img: np.ndarray) -> tuple[list[dict[str, float]], float]:
        self.calls += 1
        self.started.set()
        if self.gate is not None:
            assert self.gate.wait(timeout=5)
        return list(self.dets), self.infer_ms


@pytest.fixture
def fake_detector() -> FakeDetector:
    return FakeDetector()


def wait_until(cond, timeout: float = 5.0) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.01)
    return False
