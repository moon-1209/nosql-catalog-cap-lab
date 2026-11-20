"""Slot từ hospital_map.json (G20). Chỉ gán giá trị có trong bản đồ.

Khác G14 (`voice.intent.extract_slots`): số phòng 3 chữ số không có trong bản đồ ➔ không gán `room`
(G14 vẫn gán và đoán tầng theo chữ số đầu).
"""

from __future__ import annotations

import unicodedata

from voice.intent import _find_alias, load_map, numbers_in, tokenize

MAX_FLOOR: int = 20


def extract(text: str) -> dict[str, str]:
    """department (tên khoa viết thường), room (số phòng), floor, facility (key) ➔ chỉ khi có trong bản đồ."""
    m = load_map()
    tokens = tokenize(text)
    slots: dict[str, str] = {}
    dept = _find_alias(tokens, m["departments"])
    if dept is not None:
        slots["department"] = dept["name"].lower()
    known_rooms = {r["number"] for r in m["rooms"]}
    room = next((str(n) for n in numbers_in(tokens) if 100 <= n <= 999 and str(n) in known_rooms), None)
    if room is None:
        named = _find_alias(tokens, m["rooms"])
        room = named["number"] if named is not None else None
    if room is not None:
        slots["room"] = room
    for i, t in enumerate(tokens[:-1]):
        if t == "tầng":
            n = numbers_in(tokens[i + 1:i + 2])
            if n and 0 <= n[0] <= MAX_FLOOR:
                slots["floor"] = str(n[0])
                break
    fac = _find_alias(tokens, m["facilities"])
    if fac is not None:
        slots["facility"] = fac["key"]
    return slots


def slug(name: str) -> str:
    """"Tim mạch" ➔ "tim_mach" (bỏ dấu, đ ➔ d, khoảng trắng ➔ _)."""
    nfd = unicodedata.normalize("NFD", name.lower().replace("đ", "d"))
    return "_".join("".join(c for c in nfd if not unicodedata.combining(c)).split())


def department_id(name: str) -> str | None:
    d = next((d for d in load_map()["departments"] if d["name"].lower() == name), None)
    return f"dept_{slug(d['name'])}" if d is not None else None


def room_id(number: str) -> str | None:
    return f"room_{number}" if any(r["number"] == number for r in load_map()["rooms"]) else None
