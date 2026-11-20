"""Copy wav đã xử lý sang Godot (G11): godot/assets/voices/<clip_id>.wav + clips.json (không chứa text_ref).

Chạy: python -m voice.sync_voices [--data-dir DIR] [--dest godot/assets/voices]
"""

from __future__ import annotations

import argparse
import csv
import filecmp
import json
import shutil
import sys
from pathlib import Path

from voice import config

DEFAULT_DEST: Path = Path(__file__).resolve().parents[2] / "godot" / "assets" / "voices"
CLIP_FIELDS: tuple[str, ...] = ("speaker", "gender", "sentence_id", "take", "intent", "duration_s")


def build_clips(rows: list[dict[str, str]]) -> dict[str, dict]:
    """Dòng manifest ➔ {clip_id: {speaker, gender, sentence_id, take, intent, duration_s}}."""
    return {r["clip_id"]: {k: float(r[k]) if k == "duration_s" else r[k] for k in CLIP_FIELDS}
            for r in sorted(rows, key=lambda r: r["clip_id"])}


def sync(data_dir: Path, dest: Path) -> dict[str, int]:
    """Copy wav mới hoặc đã đổi, xóa wav thừa, ghi clips.json. Trả {copied, kept, removed}."""
    with config.manifest_path(data_dir).open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    clips = build_clips(rows)
    dest.mkdir(parents=True, exist_ok=True)
    counts = {"copied": 0, "kept": 0, "removed": 0}
    for cid in clips:
        src = config.wav_dir(data_dir) / f"{cid}.wav"
        dst = dest / f"{cid}.wav"
        if dst.exists() and filecmp.cmp(src, dst, shallow=False):
            counts["kept"] += 1
        else:
            shutil.copyfile(src, dst)
            counts["copied"] += 1
    for old in dest.glob("*.wav"):
        if old.stem not in clips:
            old.unlink()
            old.with_name(old.name + ".import").unlink(missing_ok=True)
            counts["removed"] += 1
    (dest / "clips.json").write_text(json.dumps(clips, ensure_ascii=False, indent=1), encoding="utf-8")
    return counts


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, default=config.DATA_DIR)
    p.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    args = p.parse_args(sys.argv[1:] if argv is None else argv)
    if not config.manifest_path(args.data_dir).exists():
        print("không có manifest.csv: chạy `python -m voice.prepare_data` trước", file=sys.stderr)
        return 1
    c = sync(args.data_dir, args.dest)
    print(f"copy {c['copied']}, giữ {c['kept']}, xóa {c['removed']} ➔ {args.dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
