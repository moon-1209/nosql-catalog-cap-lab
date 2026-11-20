from __future__ import annotations

import asyncio
import json
import logging
import math
import threading
import zlib
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from websockets.asyncio.client import connect

from voice import audio_sim, config
from voice.audio_sim import distance_gain, measured_snr_db, render
from voice.prepare_data import prepare
from voice.stt_server import (ClipStore, ProtocolError, SttServer, SttService, main, parse_utterance,
                              read_manifest, utterance_seed)
from voice.transcriber import FakeTranscriber, check_audio
from voice_testutil import data_dir, script_md  # noqa: F401  (fixture)

SR = config.SAMPLE_RATE


def _speech(seconds: float = 2.0, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * SR)) / SR
    return (0.2 * np.sin(2 * np.pi * 220 * t) * (1 + 0.5 * rng.standard_normal(t.size) * 0.1)).astype(np.float32)


# --- audio_sim ---

@pytest.mark.parametrize("d,g", [(1.0, 1.0), (2.0, 0.5), (4.0, 0.25), (0.5, 1.5), (0.0, 1.5), (0.8, 1.25)])
def test_audio_sim_gain(d: float, g: float) -> None:
    assert distance_gain(d) == pytest.approx(g)


@pytest.mark.parametrize("snr", [30.0, 20.0, 10.0, 5.0])
@pytest.mark.parametrize("dist", [0.5, 1.0, 2.0, 3.0])
def test_audio_sim_white_snr_within_half_db(snr: float, dist: float) -> None:
    x = _speech()
    out, eff = render(x, dist, snr, "white", np.random.default_rng(1))
    assert eff == pytest.approx(snr + 20 * math.log10(distance_gain(dist)))
    assert measured_snr_db(x * distance_gain(dist), out) == pytest.approx(eff, abs=0.5)


def test_audio_sim_example_2m() -> None:
    _, eff = render(_speech(), 2.0, 20, "white", np.random.default_rng(0))
    assert eff == pytest.approx(13.98, abs=0.01)


def test_audio_sim_none_is_clean_and_inf() -> None:
    x = _speech()
    out, eff = render(x, 0.5, 20, "none", np.random.default_rng(0))
    assert eff == math.inf
    np.testing.assert_allclose(out, x * 1.5, atol=1e-6)


def test_audio_sim_babble_and_file_snr() -> None:
    x = _speech()
    sources = [_speech(1.3, s) * 0.5 for s in range(5)]
    for name in ("babble", "lobby"):
        fn = lambda noise, n, rng: (audio_sim.make_babble(sources, n, rng) if noise == "babble"  # noqa: E731
                                    else audio_sim.fit_length(sources[0], n, rng))
        out, eff = render(x, 1.0, 10, name, np.random.default_rng(3), fn)
        assert measured_snr_db(x, out) == pytest.approx(10.0, abs=0.5)


def test_audio_sim_same_seed_same_output() -> None:
    x = _speech()
    a, _ = render(x, 1.4, 10, "white", np.random.default_rng(7))
    b, _ = render(x, 1.4, 10, "white", np.random.default_rng(7))
    c, _ = render(x, 1.4, 10, "white", np.random.default_rng(8))
    assert np.array_equal(a, b) and not np.array_equal(a, c)


def test_audio_sim_clipped_to_unit_range() -> None:
    x = np.full(SR, 0.9, dtype=np.float32)
    out, _ = render(x, 0.3, 0, "white", np.random.default_rng(0))
    assert out.min() >= -1.0 and out.max() <= 1.0


def test_audio_sim_fit_length_loops_short_noise() -> None:
    out = audio_sim.fit_length(np.arange(10, dtype=np.float32), 25, np.random.default_rng(0))
    assert out.size == 25 and set(np.unique(out)) <= set(range(10))


def test_audio_sim_unknown_noise_without_source() -> None:
    with pytest.raises(ValueError):
        render(_speech(), 1, 20, "babble", np.random.default_rng(0))


# --- transcriber ---

def test_transcriber_check_audio() -> None:
    with pytest.raises(ValueError, match="sample rate"):
        check_audio(np.zeros(100, np.float32), 44100)
    with pytest.raises(ValueError, match="mono"):
        check_audio(np.zeros((100, 2), np.float32), SR)
    with pytest.raises(ValueError, match="float32"):
        check_audio(np.zeros(100, np.float64), SR)


def test_transcriber_truncates_over_30s(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        out = check_audio(np.zeros(31 * SR, np.float32), SR)
    assert out.size == 30 * SR and "truncated" in caplog.text


def test_transcriber_fake() -> None:
    fake = FakeTranscriber({"A_07_r": "phòng 205"})
    assert fake.transcribe(np.zeros(SR, np.float32), SR, "A_07_r") == "phòng 205"
    assert fake.transcribe(np.zeros(SR, np.float32), SR, "khác") == ""
    assert fake.calls == 2


# --- parse_utterance ---

GOOD = {"type": "utterance", "utt_id": 7, "clip_id": "A_07_r", "distance_m": 1.4, "snr_db": 20, "noise": "babble"}


def test_parse_utterance_ok() -> None:
    u = parse_utterance(json.dumps(GOOD))
    assert (u.utt_id, u.clip_id, u.distance_m, u.snr_db, u.noise) == (7, "A_07_r", 1.4, 20.0, "babble")


@pytest.mark.parametrize("text,msg,uid", [
    ("abc", "invalid json", None),
    ("[1]", "invalid json", None),
    (json.dumps({**GOOD, "type": "frame"}), "invalid field: type", 7),
    (json.dumps({k: v for k, v in GOOD.items() if k != "clip_id"}), "missing field: clip_id", 7),
    (json.dumps({**GOOD, "utt_id": "7"}), "invalid field: utt_id", None),
    (json.dumps({**GOOD, "utt_id": True}), "invalid field: utt_id", None),
    (json.dumps({**GOOD, "distance_m": -1}), "invalid field: distance_m", 7),
    (json.dumps({**GOOD, "snr_db": "20"}), "invalid field: snr_db", 7),
    (json.dumps({**GOOD, "noise": ""}), "invalid field: noise", 7),
])
def test_parse_utterance_errors(text: str, msg: str, uid: int | None) -> None:
    with pytest.raises(ProtocolError) as ei:
        parse_utterance(text)
    assert (ei.value.message, ei.value.utt_id) == (msg, uid)


def test_utterance_seed_stable() -> None:
    assert utterance_seed(7, "A_07_n") == utterance_seed(7, "A_07_n") == zlib.crc32(b"7:A_07_n") == 3730372786
    assert utterance_seed(8, "A_07_n") != utterance_seed(7, "A_07_n")


# --- server (FakeTranscriber) ---

@pytest.fixture
def store(data_dir: Path, script_md: Path) -> ClipStore:  # noqa: F811
    prepare(data_dir, script_md)
    return ClipStore(read_manifest(config.manifest_path(data_dir)), config.wav_dir(data_dir), data_dir / "noise")


def _fake(store: ClipStore) -> FakeTranscriber:
    return FakeTranscriber({c: r["text_ref"] for c, r in store.manifest.items()})


async def _start(service: SttService, queue_max: int = 4):
    server = await SttServer(service, queue_max).start("127.0.0.1", 0)
    return server, f"ws://127.0.0.1:{next(iter(server.sockets)).getsockname()[1]}"


async def _ask(ws, msg: dict | str) -> dict:
    await ws.send(msg if isinstance(msg, str) else json.dumps(msg))
    return json.loads(await asyncio.wait_for(ws.recv(), 5))


def _utt(uid: int, clip: str = "A_07_r", **kw) -> dict:
    return {"type": "utterance", "utt_id": uid, "clip_id": clip, "distance_m": 1.0, "snr_db": 20, "noise": "none",
            **kw}


async def test_server_transcript_without_nlu(store: ClipStore) -> None:
    server, url = await _start(SttService(store, _fake(store)))
    async with server, connect(url) as ws:
        r = await _ask(ws, _utt(1))
    assert r["type"] == "transcript" and r["utt_id"] == 1 and r["clip_id"] == "A_07_r"
    assert r["text"] == "Phòng khám số 205 đi đường nào?"
    assert r["intent"] is None and r["response"] is None and r["effective_snr_db"] is None
    assert r["audio_s"] == pytest.approx(1.4, abs=0.06) and r["stt_ms"] >= 0


async def test_server_transcript_with_nlu_and_noise(store: ClipStore) -> None:
    nlu = (lambda t: ("hoi_phong", 1.0, {"room": "205"}), lambda i, s: f"Dạ, phòng {s['room']}.")
    server, url = await _start(SttService(store, _fake(store), nlu))
    async with server, connect(url) as ws:
        r = await _ask(ws, _utt(2, distance_m=2.0, noise="babble"))
        w = await _ask(ws, _utt(3, distance_m=2.0, noise="white"))
    assert (r["intent"], r["intent_conf"], r["slots"], r["response"]) == ("hoi_phong", 1.0, {"room": "205"},
                                                                          "Dạ, phòng 205.")
    assert r["effective_snr_db"] == pytest.approx(13.98, abs=0.01)
    assert w["type"] == "transcript"


async def test_server_errors_do_not_stop_server(store: ClipStore) -> None:
    fake = _fake(store)
    server, url = await _start(SttService(store, fake))
    async with server, connect(url) as ws:
        assert await _ask(ws, "{bad") == {"type": "error", "utt_id": None, "message": "invalid json"}
        assert await _ask(ws, _utt(1, "Z_01_r")) == {"type": "error", "utt_id": 1, "message": "clip not found: Z_01_r"}
        assert await _ask(ws, _utt(2, noise="lobby")) == {"type": "error", "utt_id": 2,
                                                         "message": "noise not found: lobby"}
        assert (await _ask(ws, _utt(3)))["type"] == "transcript"
    assert fake.calls == 1


async def test_server_noise_file(store: ClipStore, data_dir: Path) -> None:  # noqa: F811
    noise_dir = data_dir / "noise"
    noise_dir.mkdir()
    sf.write(str(noise_dir / "lobby.wav"), np.random.default_rng(0).standard_normal(SR // 2) * 0.1, SR)
    server, url = await _start(SttService(store, _fake(store)))
    async with server, connect(url) as ws:
        r = await _ask(ws, _utt(1, noise="lobby", snr_db=10))
    assert r["type"] == "transcript" and r["effective_snr_db"] == 10.0


class _Blocking(FakeTranscriber):
    def __init__(self, texts: dict[str, str]) -> None:
        super().__init__(texts)
        self.started = threading.Event()
        self.gate = threading.Event()

    def transcribe(self, audio: np.ndarray, sr: int, clip_id: str | None = None) -> str:
        self.started.set()
        self.gate.wait(5)
        return super().transcribe(audio, sr, clip_id)


async def test_server_busy_when_queue_full(store: ClipStore) -> None:
    tr = _Blocking({})
    server, url = await _start(SttService(store, tr), queue_max=4)
    async with server, connect(url) as ws:
        await ws.send(json.dumps(_utt(0)))
        assert await asyncio.to_thread(tr.started.wait, 5)       # utt 0 đang chạy
        for i in range(1, 6):                                     # 1..4 vào hàng chờ, 5 bị từ chối
            await ws.send(json.dumps(_utt(i)))
        busy = json.loads(await asyncio.wait_for(ws.recv(), 5))
        tr.gate.set()
        done = [json.loads(await asyncio.wait_for(ws.recv(), 5))["utt_id"] for _ in range(5)]
    assert busy == {"type": "error", "utt_id": 5, "message": "stt busy"}
    assert done == [0, 1, 2, 3, 4]


async def test_server_stt_exception_returns_error(store: ClipStore) -> None:
    class Boom(FakeTranscriber):
        def transcribe(self, audio, sr, clip_id=None):  # type: ignore[override]
            raise RuntimeError("mps exploded")
    server, url = await _start(SttService(store, Boom({})))
    async with server, connect(url) as ws:
        r = await _ask(ws, _utt(4))
    assert r == {"type": "error", "utt_id": 4, "message": "stt failed: RuntimeError"}


async def test_server_log_has_no_text(store: ClipStore, caplog: pytest.LogCaptureFixture) -> None:
    secret = "Phòng khám số 205"
    server, url = await _start(SttService(store, _fake(store)))
    with caplog.at_level(logging.DEBUG):
        async with server, connect(url) as ws:
            await _ask(ws, _utt(9))
    assert "utt_id=9 clip_id=A_07_r audio_s=" in caplog.text
    assert secret not in caplog.text and "205" not in caplog.text


def test_server_main_without_manifest(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--data-dir", str(tmp_path)]) == 1
    assert "prepare_data" in capsys.readouterr().err


def test_server_babble_pool_falls_back_to_other_sentences(store: ClipStore) -> None:
    assert store.babble_pool("A_07_r") == ["A_25_r", "A_C03_r"]
    store.manifest["B_01_r"] = {**store.manifest["A_07_r"], "clip_id": "B_01_r", "speaker": "B"}
    assert store.babble_pool("A_07_r") == ["B_01_r"]
