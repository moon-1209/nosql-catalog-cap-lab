from __future__ import annotations

import asyncio
import base64
import json
import threading
from pathlib import Path

import numpy as np
import pytest
from websockets.asyncio.client import connect

from tts import config
from tts.text_for_tts import text_for_tts
from tts.tts_engine import FakeTTS, Synthesizer, TtsCache, cache_key, postprocess, prepare_codec_cache, rms_dbfs
from tts.tts_server import ProtocolError, TtsServer, TtsService, build_audio, parse_speak

VOICE = config.ROBOT_VOICE


@pytest.mark.parametrize("raw,spoken", [
    ("Phòng 205", "Phòng hai không năm"),
    ("Dạ, phòng 205 ở tầng 2. Mời anh chị đi theo tôi.", "Dạ, phòng hai không năm ở tầng hai. Mời anh chị đi theo tôi."),
    ("phòng số 112", "phòng số một một hai"),
    ("Quầy BHYT ở tầng 1", "Quầy bảo hiểm y tế ở tầng một"),
    ("khoa Nhi, phòng 401", "khoa Nhi, phòng bốn không một"),
    ("chờ 15 phút", "chờ mười lăm phút"),
    ("mã 0123", "mã không một hai ba"),
])
def test_text_for_tts(raw: str, spoken: str) -> None:
    assert text_for_tts(raw) == spoken


def _synth(tmp_path: Path, engine: FakeTTS | None = None) -> tuple[Synthesizer, FakeTTS]:
    e = engine or FakeTTS()
    return Synthesizer(e, TtsCache(tmp_path / "cache"), "test-v1"), e


def test_cache_miss_then_hit(tmp_path: Path) -> None:
    synth, engine = _synth(tmp_path)
    a = synth.speak("Dạ, phòng 205 ở tầng 2.", VOICE)
    b = synth.speak("Dạ, phòng 205 ở tầng 2.", VOICE)
    assert (a.cache_hit, b.cache_hit, engine.calls) == (False, True, 1)
    assert a.pcm16 == b.pcm16 and b.tts_ms < 100
    synth.speak("Dạ, phòng 205 ở tầng 2.", "Giọng khác")
    assert engine.calls == 2                                             # khóa gồm cả giọng
    assert len(list((tmp_path / "cache").glob("*.wav"))) == 2


def test_cache_key_depends_on_text_voice_version() -> None:
    k = cache_key("Dạ", "A", "v1")
    assert k != cache_key("Dạ", "B", "v1") and k != cache_key("Dạ", "A", "v2")
    assert cache_key("Dạ", "A", "v1") == cache_key("Dạ", "A", "v1")        # cùng NFC


def test_postprocess_resample_rms_pad_pcm() -> None:
    sr = 48000
    t = np.arange(int(1.5 * sr)) / sr
    audio = (0.05 * np.sin(2 * np.pi * 300 * t)).astype(np.float32)
    pcm = postprocess(audio, sr)
    x = np.frombuffer(pcm, dtype="<i2")
    pad = int(config.PAD_S * config.OUT_SAMPLE_RATE)
    assert len(pcm) == 2 * x.size
    assert x.size == pytest.approx(1.5 * 24000 + 2 * pad, abs=2)                 # đã resample về 24 kHz
    assert not x[:pad].any() and not x[-pad:].any()                            # 100 ms im lặng hai đầu
    assert rms_dbfs(x[pad:-pad] / 32767.0) == pytest.approx(-20.0, abs=1.0)


def test_postprocess_clips_and_rejects_empty() -> None:
    loud = np.concatenate([np.full(100, 0.001, np.float32), np.ones(4, np.float32)])    # đỉnh vượt 1 sau chuẩn hóa
    x = np.frombuffer(postprocess(loud, 24000), dtype="<i2")
    assert x.max() <= 32767 and x.min() >= -32767
    with pytest.raises(ValueError):
        postprocess(np.zeros(0, np.float32), 24000)


def test_speech_duration_matches_pcm(tmp_path: Path) -> None:
    synth, _ = _synth(tmp_path)
    s = synth.speak("Dạ, mình đi tiếp nhé.", VOICE)
    assert s.sample_rate == 24000
    assert s.duration_s == pytest.approx(len(s.pcm16) / 2 / 24000)


def test_parse_speak_validation() -> None:
    ok = parse_speak(json.dumps({"type": "speak", "utt_id": 7, "text": " Dạ. ", "voice": VOICE}), {VOICE})
    assert (ok.utt_id, ok.text, ok.voice) == (7, "Dạ.", VOICE)
    cases = [
        ("{bad", "invalid json", None),
        (json.dumps({"type": "utterance", "utt_id": 1}), "invalid field: type", 1),
        (json.dumps({"type": "speak", "utt_id": True, "text": "a", "voice": VOICE}), "invalid field: utt_id", None),
        (json.dumps({"type": "speak", "utt_id": 2, "voice": VOICE}), "missing field: text", 2),
        (json.dumps({"type": "speak", "utt_id": 3, "text": "  ", "voice": VOICE}), "text empty", 3),
        (json.dumps({"type": "speak", "utt_id": 4, "text": "a" * 301, "voice": VOICE}), "text too long", 4),
        (json.dumps({"type": "speak", "utt_id": 5, "text": "a", "voice": "X"}), "voice not found: X", 5),
    ]
    for raw, message, uid in cases:
        with pytest.raises(ProtocolError) as e:
            parse_speak(raw, {VOICE})
        assert (e.value.message, e.value.utt_id) == (message, uid)
    assert parse_speak(json.dumps({"type": "speak", "utt_id": 6, "text": "a" * 300, "voice": VOICE})).text == "a" * 300


def test_build_audio_message(tmp_path: Path) -> None:
    synth, _ = _synth(tmp_path)
    s = synth.speak("Dạ.", VOICE)
    m = json.loads(build_audio(7, s))
    assert set(m) == {"type", "utt_id", "sample_rate", "channels", "pcm16_b64", "duration_s", "tts_ms", "cache_hit"}
    assert (m["type"], m["utt_id"], m["sample_rate"], m["channels"]) == ("audio", 7, 24000, 1)
    assert base64.b64decode(m["pcm16_b64"]) == s.pcm16


def test_prepare_codec_cache_layout(tmp_path: Path) -> None:
    codec = tmp_path / "codec"
    codec.mkdir()
    for f in ("moss_audio_tokenizer_decode_full.onnx", "moss_audio_tokenizer_encode.onnx", "x.data"):
        (codec / f).write_text(f)
    root = prepare_codec_cache(codec, tmp_path / "hf", "Org/Repo-ONNX")
    snap = root / "models--Org--Repo-ONNX" / "snapshots" / "local"
    assert (root / "models--Org--Repo-ONNX" / "refs" / "main").read_text() == "local"
    assert (snap / "x.data").is_symlink() and (snap / "x.data").read_text() == "x.data"
    prepare_codec_cache(codec, tmp_path / "hf", "Org/Repo-ONNX")                    # chạy lại không lỗi
    with pytest.raises(FileNotFoundError):
        prepare_codec_cache(tmp_path / "hf", tmp_path / "hf2")


# --- server ---

async def _start(service: TtsService, queue_max: int = 4):
    server = await TtsServer(service, queue_max).start("127.0.0.1", 0)
    return server, f"ws://127.0.0.1:{next(iter(server.sockets)).getsockname()[1]}"


async def _ask(ws, msg: dict | str) -> dict:
    await ws.send(msg if isinstance(msg, str) else json.dumps(msg))
    return json.loads(await asyncio.wait_for(ws.recv(), 5))


def _speak(uid: int, text: str = "Dạ, phòng 205 ở tầng 2.") -> dict:
    return {"type": "speak", "utt_id": uid, "text": text, "voice": VOICE}


async def test_server_roundtrip_and_errors(tmp_path: Path) -> None:
    synth, engine = _synth(tmp_path)
    server, url = await _start(TtsService(synth))
    async with server, connect(url) as ws:
        first = await _ask(ws, _speak(1))
        second = await _ask(ws, _speak(2))
        too_long = await _ask(ws, _speak(3, "a" * 400))
        bad = await _ask(ws, "{bad")
    assert (first["type"], first["cache_hit"], second["cache_hit"]) == ("audio", False, True)
    assert second["tts_ms"] < 100 and engine.calls == 1
    assert too_long == {"type": "error", "utt_id": 3, "message": "text too long"}
    assert bad == {"type": "error", "utt_id": None, "message": "invalid json"}


async def test_server_queue_full_is_busy(tmp_path: Path) -> None:
    engine = FakeTTS()
    engine.gate = threading.Event()
    synth, _ = _synth(tmp_path, engine)
    server, url = await _start(TtsService(synth), queue_max=4)
    async with server, connect(url) as ws:
        await ws.send(json.dumps(_speak(0, "câu số 0")))
        for _ in range(100):                                  # chờ worker nhận câu đầu (đang tổng hợp)
            if engine.calls:
                break
            await asyncio.sleep(0.01)
        for i in range(1, 6):                                 # 4 vào hàng chờ + 1 bị từ chối
            await ws.send(json.dumps(_speak(i, f"câu số {i}")))
        busy = json.loads(await asyncio.wait_for(ws.recv(), 5))
        engine.gate.set()
        rest = [json.loads(await asyncio.wait_for(ws.recv(), 5)) for _ in range(5)]
    assert busy == {"type": "error", "utt_id": 5, "message": "tts busy"}
    assert sorted(r["utt_id"] for r in rest) == [0, 1, 2, 3, 4] and all(r["type"] == "audio" for r in rest)


async def test_server_engine_failure_returns_error(tmp_path: Path) -> None:
    class Boom(FakeTTS):
        def synth(self, text: str, voice: str):
            raise RuntimeError("x")

    server, url = await _start(TtsService(Synthesizer(Boom(), TtsCache(tmp_path), "v")))
    async with server, connect(url) as ws:
        r = await _ask(ws, _speak(4))
        ok_after = await _ask(ws, {"type": "speak", "utt_id": 5, "text": "x" * 301, "voice": VOICE})
    assert r == {"type": "error", "utt_id": 4, "message": "tts failed: RuntimeError"}
    assert ok_after["message"] == "text too long"


def test_pregen_reports_counts(tmp_path: Path) -> None:
    from tts.pregen import pregen

    synth, engine = _synth(tmp_path)
    texts = ["Dạ, mình đi tiếp nhé.", "Dạ, phòng 205 ở tầng 2. Mời anh chị đi theo tôi."]
    r1 = pregen(synth, texts, VOICE, log=lambda s: None)
    r2 = pregen(synth, texts, VOICE, log=lambda s: None)
    assert (r1["misses"], r2["hits"], engine.calls) == (2, 2, 2)
