"""Câu trả lời tiếng Việt theo intent và slot (G14).

Chỉ chỉ đường, gọi nhân viên hoặc hỏi lại; KHÔNG đưa lời khuyên y khoa. Vị trí lấy từ hospital_map.json (giả lập).
"""

from __future__ import annotations

from voice.intent import load_map

CAP_CUU: str = "Tôi đang gọi nhân viên y tế ngay. Anh chị giữ bình tĩnh nhé."
KHONG_HO_TRO: str = ("Dạ, câu hỏi về chuyên môn y khoa tôi không trả lời được. "
                     "Anh chị vui lòng hỏi bác sĩ hoặc điều dưỡng nhé.")
UNKNOWN: str = "Dạ, anh chị cần tôi giúp gì ạ?"
ASK_DEPARTMENT: str = "Dạ, anh chị muốn đến khoa nào ạ? Nếu chưa rõ cần đến khoa nào, anh chị hỏi quầy tiếp đón nhé."
ASK_ROOM: str = "Dạ, anh chị muốn đến phòng nào ạ?"
ASK_DESTINATION: str = "Dạ, anh chị muốn tôi dẫn đến đâu ạ?"
ASK_FACILITY: str = "Dạ, anh chị cần tìm nhà vệ sinh, thang máy hay chỗ gửi xe ạ?"

FIXED: dict[str, str] = {
    "cap_cuu": CAP_CUU,
    "khong_ho_tro": KHONG_HO_TRO,
    "dieu_chinh_toc_do": "Dạ, tôi sẽ đi chậm lại ạ.",
    "dieu_chinh_am_luong": "Dạ, tôi sẽ nói to hơn ạ.",
    "dung_lai": "Dạ, tôi dừng lại đây chờ anh chị ạ.",
    "tiep_tuc": "Dạ, mình đi tiếp nhé.",
    "nhac_lai": "Dạ, tôi xin nói lại chậm hơn ạ.",
    "gap_nhan_vien": "Dạ, tôi đang gọi nhân viên đến hỗ trợ anh chị ạ.",
    "thoi_gian_cho": "Dạ, thời gian chờ tùy từng lúc. Anh chị xem bảng gọi số ở khu chờ, hoặc tôi gọi nhân viên giúp nhé.",
    "cam_on": "Dạ, không có gì ạ. Chúc anh chị mau khỏe.",
    "unknown": UNKNOWN,
}
# Intent chỉ tới một quầy cố định ➔ key trong "facilities".
DEFAULT_FACILITY: dict[str, str] = {
    "dang_ky_kham": "tiep_don",
    "bao_hiem": "bhyt",
    "thanh_toan": "thu_ngan",
    "nha_thuoc": "nha_thuoc",
    "ho_tro_di_chuyen": "xe_lan",
}


def _floor_text(floor: int | str) -> str:
    return "tầng hầm" if str(floor) == "0" else f"tầng {floor}"


def _facility(key: str) -> dict:
    return next(f for f in load_map()["facilities"] if f["key"] == key)


def _department(name: str) -> dict | None:
    return next((d for d in load_map()["departments"] if d["name"].lower() == name), None)


def _room(number: str) -> dict:
    """Phòng trong bản đồ; không có ➔ quy ước số đầu là tầng (vd 205 ➔ tầng 2)."""
    found = next((r for r in load_map()["rooms"] if r["number"] == number), None)
    return found or {"number": number, "name": f"Phòng {number}", "floor": int(number[0])}


def _facility_text(f: dict) -> str:
    """`where` đã gồm tầng (vd "ngay sảnh chính, tầng 1")."""
    return f"{f['name'][0].lower()}{f['name'][1:]} ở {f['where']} ạ."


def build(intent: str, slots: dict[str, str] | None) -> str:
    """Câu trả lời cho `intent`. Thiếu slot cần thiết ➔ câu hỏi lại."""
    slots = slots or {}
    if intent in FIXED:
        return FIXED[intent]
    if intent == "hoi_khoa":
        d = _department(slots.get("department", ""))
        if d is None:
            return ASK_DEPARTMENT
        return f"Dạ, khoa {d['name']} ở {_floor_text(d['floor'])}, phòng {d['room']}. Mời anh chị đi theo tôi."
    if intent == "hoi_phong":
        if "room" not in slots:
            return ASK_ROOM
        r = _room(slots["room"])
        return f"Dạ, phòng {r['number']} ở {_floor_text(r['floor'])}. Mời anh chị đi theo tôi."
    if intent == "dan_duong":
        d = _department(slots.get("department", ""))
        if d is not None:
            return f"Dạ, mời anh chị đi theo tôi đến khoa {d['name']}, {_floor_text(d['floor'])}."
        if "room" in slots:
            r = _room(slots["room"])
            return f"Dạ, mời anh chị đi theo tôi đến phòng {r['number']}, {_floor_text(r['floor'])}."
        return ASK_DESTINATION
    if intent == "tien_ich":
        key = slots.get("facility")
        return f"Dạ, {_facility_text(_facility(key))}" if key else ASK_FACILITY
    if intent in DEFAULT_FACILITY:
        key = slots.get("facility", DEFAULT_FACILITY[intent])
        if intent == "dang_ky_kham" and key not in ("tiep_don", "uu_tien"):
            key = "tiep_don"
        elif intent != "dang_ky_kham":
            key = DEFAULT_FACILITY[intent]
        return f"Dạ, {_facility_text(_facility(key))}"
    return UNKNOWN
