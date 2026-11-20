from __future__ import annotations

import base64
import json

import pytest

from conftest import make_frame_msg
from protocol import ProtocolError, build_detections, build_error, parse_frame


def test_valid_frame() -> None:
    frame_id, img = parse_frame(make_frame_msg(3, 64, 48))
    assert frame_id == 3
    assert img.shape == (48, 64, 3)


@pytest.mark.parametrize("text", ["abc", "", "{", "[1, 2]", "42"])
def test_invalid_json(text: str) -> None:
    with pytest.raises(ProtocolError) as ei:
        parse_frame(text)
    assert ei.value.message == "invalid json"
    assert ei.value.frame_id is None


def test_missing_jpeg_example_from_spec() -> None:
    with pytest.raises(ProtocolError) as ei:
        parse_frame('{"type":"frame","frame_id":4}')
    assert ei.value.message == "missing field: jpeg_b64"
    assert ei.value.frame_id == 4


@pytest.mark.parametrize("field", ["type", "frame_id", "jpeg_b64", "width", "height"])
def test_missing_each_field(field: str) -> None:
    msg = json.loads(make_frame_msg(7))
    del msg[field]
    with pytest.raises(ProtocolError) as ei:
        parse_frame(json.dumps(msg))
    assert ei.value.message == f"missing field: {field}"
    assert ei.value.frame_id == (None if field == "frame_id" else 7)


@pytest.mark.parametrize("field,value", [
    ("type", "detections"), ("frame_id", -1), ("frame_id", "1"), ("frame_id", True),
    ("frame_id", 1.5), ("width", 0), ("height", "48"), ("jpeg_b64", 123),
])
def test_invalid_field_values(field: str, value: object) -> None:
    msg = json.loads(make_frame_msg(7))
    msg[field] = value
    with pytest.raises(ProtocolError) as ei:
        parse_frame(json.dumps(msg))
    assert ei.value.message == f"invalid field: {field}"


@pytest.mark.parametrize("payload", [
    "not base64 !!", base64.b64encode(b"definitely not a jpeg").decode(), "",
])
def test_invalid_jpeg(payload: str) -> None:
    msg = json.loads(make_frame_msg(9))
    msg["jpeg_b64"] = payload
    with pytest.raises(ProtocolError) as ei:
        parse_frame(json.dumps(msg))
    assert ei.value.message == "invalid jpeg"
    assert ei.value.frame_id == 9


def test_size_mismatch() -> None:
    msg = json.loads(make_frame_msg(2, 64, 48))
    msg["width"] = 640
    with pytest.raises(ProtocolError) as ei:
        parse_frame(json.dumps(msg))
    assert ei.value.message == "size mismatch"


def test_build_detections_shape() -> None:
    dets = [{"x1": 0.41, "y1": 0.2, "x2": 0.58, "y2": 0.86, "conf": 0.87}]
    out = json.loads(build_detections(3, dets, 21.44))
    assert out == {"type": "detections", "frame_id": 3, "infer_ms": 21.4, "detections": dets}


def test_build_error_shape() -> None:
    assert json.loads(build_error(None, "invalid json")) == {
        "type": "error", "frame_id": None, "message": "invalid json"}
