"""Parse docs/kich_ban_thu_am.md into structured annotations for STT and Intent testing.

Outputs:
  - data/annotations.json
  - data/annotations.csv
"""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs" / "kich_ban_thu_am.md"
OUT_JSON = ROOT / "data" / "annotations.json"
OUT_CSV = ROOT / "data" / "annotations.csv"


def parse_script() -> tuple[list[dict], list[dict]]:
    with open(DOC_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    sections = re.split(r"##\s+", content)
    items = []

    for sec in sections:
        lines = sec.strip().splitlines()
        if not lines:
            continue
        sec_title = lines[0]

        for line in lines[1:]:
            m = re.match(r"\|\s*([A-Za-z0-9_]+)\s*\|\s*([^\|]+?)\s*\|\s*([a-zA-Z0-9_]+)\s*\|", line)
            if not m:
                continue
            code = m.group(1).strip()
            text = m.group(2).strip()
            intent = m.group(3).strip()
            if code in ("Mã", "ma", "Intent", "Code", "Người"):
                continue

            if "Kịch bản A" in sec_title:
                items.append({"code": code, "speaker": "A", "text": text, "intent": intent})
            elif "Kịch bản B" in sec_title:
                items.append({"code": code, "speaker": "B", "text": text, "intent": intent})
            elif "Câu chung" in sec_title:
                items.append({"code": f"A_{code}", "base_code": code, "speaker": "A", "text": text, "intent": intent, "common": True})
                items.append({"code": f"B_{code}", "base_code": code, "speaker": "B", "text": text, "intent": intent, "common": True})

    records = []
    for item in items:
        if item.get("common"):
            base_code = item.get("base_code")
            speaker_prefix = "Nam" if item["speaker"] == "A" else "Nu"
            file_id = f"{speaker_prefix}_{base_code}"
            records.append({
                "file_id": file_id,
                "code": base_code,
                "speaker": item["speaker"],
                "mode": "r",
                "mode_label": "reading",
                "intent": item["intent"],
                "text": item["text"],
                "expected_raw_file": f"data/raw/real_voice/{file_id}.m4a",
                "expected_wav_file": f"data/processed/real_voice/{file_id}.wav",
            })
            # Also keep A_C01_r format as alias
            for mode, mode_label in [("r", "reading"), ("n", "natural")]:
                alias_id = f"{item['code']}_{mode}"
                records.append({
                    "file_id": alias_id,
                    "code": item["code"],
                    "speaker": item["speaker"],
                    "mode": mode,
                    "mode_label": mode_label,
                    "intent": item["intent"],
                    "text": item["text"],
                    "expected_raw_file": f"data/raw/real_voice/{alias_id}.m4a",
                    "expected_wav_file": f"data/processed/real_voice/{alias_id}.wav",
                })
        else:
            for mode, mode_label in [("r", "reading"), ("n", "natural")]:
                file_id = f"{item['code']}_{mode}"
                records.append({
                    "file_id": file_id,
                    "code": item["code"],
                    "speaker": item["speaker"],
                    "mode": mode,
                    "mode_label": mode_label,
                    "intent": item["intent"],
                    "text": item["text"],
                    "expected_raw_file": f"data/raw/real_voice/{file_id}.m4a",
                    "expected_wav_file": f"data/processed/real_voice/{file_id}.wav",
                })

    return items, records


def main() -> None:
    items, records = parse_script()
    os.makedirs(ROOT / "data", exist_ok=True)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(
            {
                "total_prompts": len(items),
                "total_recordings_expected": len(records),
                "annotations": records,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["file_id", "speaker", "mode", "intent", "text", "expected_raw_file", "expected_wav_file"],
        )
        writer.writeheader()
        for r in records:
            writer.writerow({
                "file_id": r["file_id"],
                "speaker": r["speaker"],
                "mode": r["mode"],
                "intent": r["intent"],
                "text": r["text"],
                "expected_raw_file": r["expected_raw_file"],
                "expected_wav_file": r["expected_wav_file"],
            })

    print(f"Parsed {len(items)} prompt definitions -> {len(records)} recording files expected.")
    print(f"Saved: {OUT_JSON}")
    print(f"Saved: {OUT_CSV}")


if __name__ == "__main__":
    main()
