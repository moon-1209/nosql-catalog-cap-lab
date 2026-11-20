"""Dialogue policy (G20): IntentResult ➔ PolicyResult. Hàm thuần, trạng thái truyền vào (clarify_count, last_response).

Mọi câu trả lời lấy từ `voice.responses` (G14) hoặc bảng G20.1; không ghép chuỗi ngoài slot có trong bản đồ.
"""

from __future__ import annotations

from dataclasses import dataclass

from nlu import config, slots as slot_lib
from nlu.nlu import IntentResult
from voice import responses

CLARIFY: str = "Dạ, anh chị nói lại giúp tôi được không ạ?"
CALL_STAFF: str = "Tôi sẽ gọi nhân viên hỗ trợ anh chị ạ."
ASK_DEPARTMENT: str = "Dạ, anh chị muốn đến khoa nào ạ?"
ACTIONS: tuple[str, ...] = ("answer", "guide", "clarify", "call_staff", "emergency", "refuse", "repeat", "adjust")
ADJUST_INTENTS: frozenset[str] = frozenset({"dieu_chinh_toc_do", "dieu_chinh_am_luong", "dung_lai", "tiep_tuc"})
PLACE_INTENTS: frozenset[str] = frozenset({"hoi_khoa", "hoi_phong", "dan_duong"})


@dataclass(frozen=True)
class PolicyResult:
    action: str
    response: str
    target: str | None = None


def _clarify(response: str, clarify_count: int) -> PolicyResult:
    """Hỏi lại; đã hỏi lại MAX_CLARIFY lần ➔ gọi nhân viên."""
    if clarify_count >= config.MAX_CLARIFY:
        return PolicyResult("call_staff", CALL_STAFF)
    return PolicyResult("clarify", response)


def _guide(intent: str, s: dict[str, str]) -> PolicyResult | None:
    """Có khoa hoặc phòng trong bản đồ ➔ dẫn đường. hoi_phong ưu tiên phòng, còn lại ưu tiên khoa."""
    dept = s.get("department")
    room = s.get("room")
    order = (("room", room), ("department", dept)) if intent == "hoi_phong" else (("department", dept), ("room", room))
    for kind, value in order:
        if value is None:
            continue
        target = slot_lib.department_id(value) if kind == "department" else slot_lib.room_id(value)
        if target is None:
            continue
        if intent == "dan_duong":
            text = responses.build("dan_duong", {kind: value})
        else:
            text = responses.build("hoi_khoa" if kind == "department" else "hoi_phong", {kind: value})
        return PolicyResult("guide", text, target)
    return None


def decide(r: IntentResult, clarify_count: int, last_response: str | None,
           threshold: float = config.CONF_THRESHOLD_DEFAULT) -> PolicyResult:
    if r.intent == "cap_cuu":
        return PolicyResult("emergency", responses.CAP_CUU)
    if r.intent_conf < threshold:
        return _clarify(CLARIFY, clarify_count)
    if r.intent in PLACE_INTENTS:
        guided = _guide(r.intent, r.slots)
        if guided is not None:
            return guided
        return _clarify(responses.ASK_ROOM if r.intent == "hoi_phong" else ASK_DEPARTMENT, clarify_count)
    if r.intent == "khong_ho_tro":
        return PolicyResult("refuse", responses.KHONG_HO_TRO)
    if r.intent == "nhac_lai":
        return PolicyResult("repeat", last_response or responses.UNKNOWN)
    if r.intent in ADJUST_INTENTS:
        return PolicyResult("adjust", responses.FIXED[r.intent])
    return PolicyResult("answer", responses.build(r.intent, r.slots))


def all_responses() -> list[str]:
    """Mọi câu robot có thể nói: intent ✕ slot (mọi khoa, phòng, tiện ích trong bản đồ, hoặc không slot)
    ✕ clarify_count ✕ độ tin cậy cao/thấp. Dùng để duyệt câu (G20) và sinh sẵn giọng nói (G21)."""
    from voice.intent import load_map

    m = load_map()
    slot_options: list[dict[str, str]] = [{}]
    slot_options += [{"department": d["name"].lower()} for d in m["departments"]]
    slot_options += [{"room": r["number"]} for r in m["rooms"]]
    slot_options += [{"facility": f["key"]} for f in m["facilities"]]
    out: set[str] = set()
    for intent in config.INTENTS:
        for s in slot_options:
            for cc in (0, config.MAX_CLARIFY):
                for conf in (0.0, 1.0):
                    out.add(decide(IntentResult(intent, conf, s, "phobert", []), cc, None, 0.5).response)
    return sorted(out)
