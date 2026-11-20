from __future__ import annotations

import asyncio
import itertools
import json
import re
import sys
from pathlib import Path

import pytest
from websockets.asyncio.client import connect

from nlu import config, policy, slots
from nlu.dialogue import DialogueEngine
from nlu.nlu import IntentResult, Nlu, emergency_rule
from nlu.policy import PolicyResult, decide
from voice import responses
from voice.intent import load_map
from voice.stt_server import ClipStore, SttServer, SttService, read_manifest
from voice.transcriber import FakeTranscriber
from voice import config as voice_config
from voice.prepare_data import prepare
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "voice"))
from voice_testutil import data_dir, script_md  # noqa: E402, F401

BANNED = ("nên uống", "uống thuốc", "liều", "nhịn ăn", "bệnh của", "chẩn đoán", "không sao đâu", "nên khám khoa")


class FakeIntentModel:
    """Trả phân phối cố định; ghi lại câu đã nhận (đã tách từ)."""

    def __init__(self, intent: str = "hoi_khoa", conf: float = 0.97) -> None:
        self.intent, self.conf = intent, conf
        self.seen: list[str] = []

    def predict(self, text_seg: str) -> list[tuple[str, float]]:
        self.seen.append(text_seg)
        rest = (1.0 - self.conf) / (len(config.INTENTS) - 1)
        probs = [(i, self.conf if i == self.intent else rest) for i in config.INTENTS]
        return sorted(probs, key=lambda kv: -kv[1])


def _nlu(intent: str = "hoi_khoa", conf: float = 0.97) -> tuple[Nlu, FakeIntentModel]:
    m = FakeIntentModel(intent, conf)
    return Nlu("phobert", m, segment=lambda t: t.replace("tim mạch", "tim_mạch")), m


# --- NLU ---

def test_emergency_rule_runs_before_phobert() -> None:
    nlu, model = _nlu("cam_on", 0.99)
    r = nlu.understand("Bố mình đang khó thở quá, gọi bác sĩ giúp mình với!")
    assert (r.intent, r.intent_conf, r.source, r.top3) == ("cap_cuu", 1.0, "rule_emergency", [])
    assert model.seen == []


def test_phobert_gets_segmented_normalized_text() -> None:
    nlu, model = _nlu("hoi_khoa", 0.97)
    r = nlu.understand("Cho hỏi khoa Tim mạch?")
    assert model.seen == ["cho hỏi khoa tim_mạch"]
    assert (r.intent, r.source, r.slots) == ("hoi_khoa", "phobert", {"department": "tim mạch"})
    assert r.intent_conf == pytest.approx(0.97) and len(r.top3) == 3 and r.top3[0][0] == "hoi_khoa"


def test_empty_text_is_unknown() -> None:
    nlu, model = _nlu()
    assert nlu.understand(" ?! ") == IntentResult("unknown", 0.0, {}, "rule", [])
    assert model.seen == []


def test_rule_mode_same_interface() -> None:
    r = Nlu("rule").understand("Khoa tiêu hóa ở tầng mấy?")
    assert (r.intent, r.intent_conf, r.source) == ("hoi_khoa", 1.0, "rule")
    assert r.slots == {"department": "tiêu hóa"} and r.top3 == [("hoi_khoa", 1.0)]
    assert Nlu("rule").understand("Khoa cấp cứu ở đâu?").source == "rule_emergency"
    with pytest.raises(ValueError):
        Nlu("phobert")


def test_emergency_rule_words() -> None:
    assert emergency_rule("bà em bị chóng mặt sắp ngã rồi")
    assert emergency_rule("có người ngất")
    assert not emergency_rule("nhà vệ sinh ở đâu")


# --- slots ---

def test_room_not_in_map_is_not_a_slot() -> None:
    assert "room" not in slots.extract("phòng 999 ở đâu")
    assert "room" not in slots.extract("phòng chín trăm chín mươi chín ở đâu")
    assert slots.extract("phòng hai trăm linh năm ở đâu")["room"] == "205"
    assert slots.extract("phòng siêu âm tim ở đâu")["room"] == "302"
    assert slots.extract("khoa abc xyz ở đâu") == {}


def test_target_ids() -> None:
    assert slots.department_id("tim mạch") == "dept_tim_mach"
    assert slots.department_id("tiêu hóa") == "dept_tieu_hoa"
    assert slots.department_id("không có") is None
    assert slots.room_id("205") == "room_205" and slots.room_id("999") is None


# --- policy (bảng G20.1) ---

def _r(intent: str, conf: float = 0.95, **s: str) -> IntentResult:
    return IntentResult(intent, conf, dict(s), "phobert", [])


def test_policy_emergency() -> None:
    assert decide(_r("cap_cuu", 0.1), 5, None) == PolicyResult("emergency", responses.CAP_CUU)


def test_policy_low_confidence() -> None:
    assert decide(_r("hoi_khoa", 0.4, department="tim mạch"), 0, None, 0.6) == PolicyResult("clarify", policy.CLARIFY)
    assert decide(_r("hoi_khoa", 0.4), 1, None, 0.6).action == "clarify"
    assert decide(_r("hoi_khoa", 0.4), 2, None, 0.6) == PolicyResult("call_staff", policy.CALL_STAFF)
    assert decide(_r("hoi_khoa", 0.6), 0, None, 0.6).action != "call_staff"            # bằng ngưỡng ➔ không thấp


def test_policy_guide_with_slot() -> None:
    p = decide(_r("hoi_khoa", department="tim mạch"), 0, None)
    assert p.action == "guide" and p.target == "dept_tim_mach"
    assert p.response == "Dạ, khoa Tim mạch ở tầng 3, phòng 301. Mời anh chị đi theo tôi."
    p = decide(_r("hoi_phong", room="205"), 0, None)
    assert (p.action, p.target) == ("guide", "room_205") and "phòng 205 ở tầng 2" in p.response
    p = decide(_r("dan_duong", room="302"), 0, None)
    assert (p.action, p.target) == ("guide", "room_302") and p.response.startswith("Dạ, mời anh chị đi theo tôi")
    assert decide(_r("hoi_phong", department="nhi"), 0, None).target == "dept_nhi"


def test_policy_place_without_slot_clarifies() -> None:
    assert decide(_r("hoi_khoa"), 0, None) == PolicyResult("clarify", policy.ASK_DEPARTMENT)
    assert decide(_r("dan_duong"), 0, None) == PolicyResult("clarify", policy.ASK_DEPARTMENT)
    assert decide(_r("hoi_phong"), 0, None) == PolicyResult("clarify", responses.ASK_ROOM)
    assert decide(_r("hoi_khoa"), 2, None).action == "call_staff"


def test_policy_refuse_repeat_adjust_answer() -> None:
    assert decide(_r("khong_ho_tro"), 0, None) == PolicyResult("refuse", responses.KHONG_HO_TRO)
    assert decide(_r("nhac_lai"), 0, "Dạ, nhà thuốc ở cuối sảnh.") == PolicyResult("repeat", "Dạ, nhà thuốc ở cuối sảnh.")
    assert decide(_r("nhac_lai"), 0, None) == PolicyResult("repeat", responses.UNKNOWN)
    for it in ("dieu_chinh_toc_do", "dieu_chinh_am_luong", "dung_lai", "tiep_tuc"):
        assert decide(_r(it), 0, None) == PolicyResult("adjust", responses.FIXED[it])
    assert decide(_r("nha_thuoc"), 0, None) == PolicyResult("answer", responses.build("nha_thuoc", {}))
    assert decide(_r("cam_on"), 0, None).action == "answer"
    assert decide(_r("unknown", 0.9), 0, None) == PolicyResult("answer", responses.UNKNOWN)


def test_examples_g20() -> None:
    eng = DialogueEngine(_nlu("hoi_khoa", 0.97)[0], 0.6)
    d = eng("bố mình đang khó thở quá gọi bác sĩ giúp mình với", {})
    assert (d["intent"], d["source"], d["action"]) == ("cap_cuu", "rule_emergency", "emergency")
    d = eng("cho hỏi khoa tim mạch", {})
    assert (d["slots"], d["action"], d["target"]) == ({"department": "tim mạch"}, "guide", "dept_tim_mach")
    assert eng("khoa abc xyz ở đâu", {})["action"] == "clarify"
    low = DialogueEngine(_nlu("hoi_khoa", 0.4)[0], 0.6)
    assert low("ờ à", {"clarify_count": 2})["action"] == "call_staff"
    d = DialogueEngine(_nlu("khong_ho_tro", 0.9)[0], 0.6)("em có cần nhịn ăn không", {})
    assert d["action"] == "refuse" and not any(b in d["response"].lower() for b in BANNED)


def test_engine_updates_state() -> None:
    eng = DialogueEngine(_nlu("hoi_khoa", 0.4)[0], 0.6)
    state: dict = {}
    assert [eng("ờ", state)["action"] for _ in range(3)] == ["clarify", "clarify", "call_staff"]
    assert state["clarify_count"] == 0 and state["last_response"] == policy.CALL_STAFF
    rep = DialogueEngine(_nlu("nhac_lai", 0.9)[0], 0.6)("nói lại đi", state)
    assert rep["response"] == policy.CALL_STAFF and state["last_response"] == policy.CALL_STAFF


def test_every_possible_response_is_safe_and_in_map() -> None:
    """In hết tổ hợp intent ✕ slot ✕ trạng thái: không có lời khuyên y khoa, địa điểm đều có trong bản đồ."""
    m = load_map()
    slot_options = [{}] + [{"department": d["name"].lower()} for d in m["departments"]] + \
        [{"room": r["number"]} for r in m["rooms"]] + [{"facility": f["key"]} for f in m["facilities"]]
    texts = set()
    for intent, s, cc, conf in itertools.product(config.INTENTS, slot_options, (0, 2), (0.3, 0.95)):
        p = decide(IntentResult(intent, conf, s, "phobert", []), cc, None)
        assert p.action in policy.ACTIONS
        texts.add(p.response)
        if p.action == "guide":
            assert p.target is not None
    assert not [t for t in texts if any(b in t.lower() for b in BANNED)]
    numbers = {r["number"] for r in m["rooms"]} | {d["room"] for d in m["departments"]}
    for t in texts:
        for n in re.findall(r"phòng (\d{3})", t):
            assert n in numbers, t
    assert len(texts) > 40 and texts == set(policy.all_responses())


# --- stt_server với DialogueEngine ---

@pytest.fixture
def store(data_dir: Path, script_md: Path) -> ClipStore:  # noqa: F811
    prepare(data_dir, script_md)
    return ClipStore(read_manifest(voice_config.manifest_path(data_dir)), voice_config.wav_dir(data_dir),
                     data_dir / "noise")


async def test_stt_server_adds_action_target_and_keeps_state(store: ClipStore) -> None:
    fake = FakeTranscriber({c: r["text_ref"] for c, r in store.manifest.items()})
    eng = DialogueEngine(_nlu("hoi_phong", 0.97)[0], 0.6)
    server = await SttServer(SttService(store, fake, eng)).start("127.0.0.1", 0)
    url = f"ws://127.0.0.1:{next(iter(server.sockets)).getsockname()[1]}"

    async def ask(ws, uid: int, clip: str) -> dict:
        await ws.send(json.dumps({"type": "utterance", "utt_id": uid, "clip_id": clip, "distance_m": 1.0,
                                  "snr_db": 20, "noise": "none"}))
        return json.loads(await asyncio.wait_for(ws.recv(), 5))

    async with server, connect(url) as ws:
        r = await ask(ws, 1, "A_07_r")
    old = {"type", "utt_id", "clip_id", "text", "intent", "intent_conf", "slots", "response", "stt_ms", "audio_s",
           "effective_snr_db"}
    assert set(r) == old | {"action", "target"}
    assert (r["intent"], r["slots"], r["action"], r["target"]) == ("hoi_phong", {"room": "205"}, "guide", "room_205")
    low = DialogueEngine(_nlu("hoi_phong", 0.3)[0], 0.6)
    server = await SttServer(SttService(store, fake, low)).start("127.0.0.1", 0)
    url = f"ws://127.0.0.1:{next(iter(server.sockets)).getsockname()[1]}"
    async with server:
        async with connect(url) as ws:
            acts = [(await ask(ws, i, "A_07_r"))["action"] for i in range(3)]
        async with connect(url) as ws2:                       # kết nối mới ➔ trạng thái mới
            first = (await ask(ws2, 9, "A_07_r"))["action"]
    assert acts == ["clarify", "clarify", "call_staff"] and first == "clarify"
