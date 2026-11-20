from __future__ import annotations

import sys

import numpy as np

from detector import normalize_boxes


def test_normalized_coordinates() -> None:
    dets = normalize_boxes(np.array([[262.4, 96.0, 371.2, 412.8]]), np.array([0.8712]), 640, 480)
    assert dets == [{"x1": 0.41, "y1": 0.2, "x2": 0.58, "y2": 0.86, "conf": 0.8712}]


def test_sorted_by_conf_desc() -> None:
    xyxy = np.array([[0, 0, 10, 10], [10, 10, 20, 20], [20, 20, 30, 30]], dtype=float)
    dets = normalize_boxes(xyxy, np.array([0.5, 0.9, 0.7]), 100, 100)
    assert [d["conf"] for d in dets] == [0.9, 0.7, 0.5]


def test_clamped_to_unit_range_and_ordered() -> None:
    dets = normalize_boxes(np.array([[-5.0, -1.0, 700.0, 500.0]]), np.array([0.6]), 640, 480)
    d = dets[0]
    assert (d["x1"], d["y1"], d["x2"], d["y2"]) == (0.0, 0.0, 1.0, 1.0)
    assert 0 <= d["x1"] < d["x2"] <= 1 and 0 <= d["y1"] < d["y2"] <= 1


def test_degenerate_box_dropped() -> None:
    assert normalize_boxes(np.array([[700.0, 10.0, 800.0, 20.0]]), np.array([0.9]), 640, 480) == []


def test_empty() -> None:
    assert normalize_boxes(np.zeros((0, 4)), np.zeros((0,)), 640, 480) == []


def test_ultralytics_not_imported_by_modules() -> None:
    import protocol  # noqa: F401
    import detector  # noqa: F401
    assert "ultralytics" not in sys.modules
