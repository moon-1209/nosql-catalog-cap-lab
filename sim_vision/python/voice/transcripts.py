"""Đọc bảng kịch bản thu âm (G11): mỗi bảng markdown có cột Mã, Câu, Intent."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

_CODE_RE = re.compile(r"^(?:(A|B)_(\d{2})|(C\d{2}))$")


@dataclass(frozen=True)
class ScriptRow:
    text: str
    intent: str


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_script_table(md_text: str) -> dict[str, ScriptRow]:
    """Trả dict sentence key ➔ ScriptRow. Mã A_xx, B_xx giữ nguyên; Cxx tách thành A_Cxx và B_Cxx."""
    rows: dict[str, ScriptRow] = {}
    cols: dict[str, int] | None = None
    for line in unicodedata.normalize("NFC", md_text).splitlines():
        if not line.lstrip().startswith("|"):
            cols = None
            continue
        cells = _cells(line)
        if {"Mã", "Câu", "Intent"} <= set(cells):
            cols = {name: cells.index(name) for name in ("Mã", "Câu", "Intent")}
            continue
        if cols is None or all(set(c) <= set(":- ") for c in cells):
            continue
        code = cells[cols["Mã"]]
        m = _CODE_RE.match(code)
        if m is None:
            continue
        row = ScriptRow(text=cells[cols["Câu"]], intent=cells[cols["Intent"]])
        keys = [code] if m.group(3) is None else [f"A_{code}", f"B_{code}"]
        for key in keys:
            if key in rows:
                raise ValueError(f"duplicate script code: {key}")
            rows[key] = row
    return rows


def load_script_table(md_path: Path) -> dict[str, ScriptRow]:
    return parse_script_table(Path(md_path).read_text(encoding="utf-8"))
