from __future__ import annotations

import asyncio
import json
import threading

import pytest
from websockets.asyncio.client import connect

from conftest import FakeDetector, make_frame_msg
from yolo_server import main, start_server

DET = {"x1": 0.41, "y1": 0.2, "x2": 0.58, "y2": 0.86, "conf": 0.87}


async def _server(detector: FakeDetector):
    server = await start_server(detector, "127.0.0.1", 0)
    port = next(iter(server.sockets)).getsockname()[1]
    return server, f"ws://127.0.0.1:{port}"


async def test_valid_frame_returns_detections() -> None:
    server, url = await _server(FakeDetector([DET], infer_ms=21.4))
    async with server, connect(url) as ws:
        await ws.send(make_frame_msg(3))
        reply = json.loads(await asyncio.wait_for(ws.recv(), 5))
    assert reply == {"type": "detections", "frame_id": 3, "infer_ms": 21.4, "detections": [DET]}


async def test_server_survives_errors() -> None:
    det = FakeDetector()
    server, url = await _server(det)
    async with server, connect(url) as ws:
        await ws.send("abc")
        assert json.loads(await asyncio.wait_for(ws.recv(), 5)) == {
            "type": "error", "frame_id": None, "message": "invalid json"}
        await ws.send('{"type":"frame","frame_id":4}')
        assert json.loads(await asyncio.wait_for(ws.recv(), 5)) == {
            "type": "error", "frame_id": 4, "message": "missing field: jpeg_b64"}
        await ws.send(make_frame_msg(5))
        reply = json.loads(await asyncio.wait_for(ws.recv(), 5))
        assert reply["type"] == "detections" and reply["frame_id"] == 5
    assert det.calls == 1


async def test_backlog_processes_only_latest_frame() -> None:
    det = FakeDetector()
    det.gate = threading.Event()
    server, url = await _server(det)
    async with server, connect(url) as ws:
        await ws.send(make_frame_msg(0))
        assert await asyncio.to_thread(det.started.wait, 5)  # frame 0 đang suy luận
        for i in (1, 2, 3):
            await ws.send(make_frame_msg(i))
        await asyncio.sleep(0.2)  # để server đọc hết các frame dồn
        det.gate.set()
        ids = [json.loads(await asyncio.wait_for(ws.recv(), 5))["frame_id"] for _ in range(2)]
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(ws.recv(), 0.5)
    assert ids == [0, 3]
    assert det.calls == 2


def test_missing_model_exits_nonzero(tmp_path, capsys) -> None:
    code = main(["--model", str(tmp_path / "nope.pt")])
    assert code != 0
    assert "model file not found" in capsys.readouterr().err
    assert not (tmp_path / "nope.pt").exists()
