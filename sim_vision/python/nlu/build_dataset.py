"""Dựng dữ liệu intent cho PhoBERT (G18): data/nlu/{train,val,test_ref,test_stt,leak_removed}.csv + stats.md.

Chạy: python -m nlu.build_dataset [--stt-csv reports/stt_eval_*.csv] [--per-intent 120]

- test_ref: text_ref của clip ref_verified (G11); test_stt: hyp của G13 cho cùng clip. KHÔNG dùng để train.
- train/val: seed.csv (tự viết) ➔ ghép slot từ hospital_map.json ➔ biến đổi có quy tắc ➔ reviewed.csv (keep = 1).
- Câu giống câu test hoặc câu trong kịch bản thu âm (Levenshtein chuẩn hóa ≥ 0.9) ➔ loại, ghi leak_removed.csv.
- Chia 85/15 phân tầng theo intent, rồi thêm lỗi kiểu STT cho 30% câu train.
"""

from __future__ import annotations

import argparse
import csv
import random
import re
import sys
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from pathlib import Path

import pandas as pd
from rapidfuzz.distance import Levenshtein
from rapidfuzz.process import cdist
from sklearn.model_selection import train_test_split

from nlu import asr_noise, config
from nlu.vi_numbers import read_number, spell_digits
from voice import config as voice_config
from voice.intent import load_map
from voice.text_norm import normalize
from voice.transcripts import load_script_table

LEAK_THRESHOLD: float = 0.9
VAL_FRAC: float = 0.15
NOISE_FRAC: float = 0.3
PER_INTENT_MAX: int = 120
MIN_TRAIN: int = 60
COLUMNS: list[str] = ["id", "text", "text_seg", "intent", "source", "split"]
STT_EXTRA: list[str] = ["clip_id", "snr_db", "distance_m", "noise"]

PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")
PRONOUNS: tuple[str, ...] = ("tôi", "em", "mình", "bác", "cháu")
# Tiền tố / hậu tố theo kiểu câu: q = câu hỏi, c = câu đề nghị / mệnh lệnh / cảm thán.
PREFIXES: dict[str, tuple[str, ...]] = {
    "q": ("", "dạ ", "ờ ", "à ", "bạn ơi ", "robot ơi ", "cho {p} hỏi ", "xin lỗi cho {p} hỏi "),
    "c": ("", "dạ ", "ờ ", "à ", "bạn ơi ", "robot ơi ", "này "),
}
SUFFIXES: dict[str, tuple[str, ...]] = {
    "q": ("", " ạ", " vậy", " vậy ạ", " nhỉ", " thế", " bạn ơi"),
    "c": ("", " nhé", " nha", " ạ", " với", " bạn ơi"),
}
# Danh từ chỉ tiện ích dùng cho tien_ich (key trong "facilities" của hospital_map.json).
FACILITY_NOUNS: dict[str, tuple[str, ...]] = {
    "thang_may": ("thang máy", "cầu thang máy"),
    "nha_ve_sinh": ("nhà vệ sinh", "toilet", "nhà vệ sinh nam", "phòng vệ sinh"),
    "gui_xe": ("chỗ gửi xe", "bãi để xe", "nhà xe"),
    "ghe_cho": ("ghế chờ", "khu ngồi chờ", "chỗ ngồi đợi"),
    "can_tin": ("căng tin", "nhà ăn", "chỗ mua đồ ăn", "chỗ bán nước"),
}
# Khoa cấp cứu thuộc intent cap_cuu (A_26), không ghép vào mẫu hoi_khoa / dan_duong.
EXCLUDED_DEPARTMENTS: frozenset[str] = frozenset({"Cấp cứu"})
# Bí danh phòng quá chung (dễ lẫn với thoi_gian_cho, khong_ho_tro) không dùng làm {room_name}.
EXCLUDED_ROOM_ALIASES: frozenset[str] = frozenset({"kết quả", "xét nghiệm"})
# Câu đã kết thúc bằng tiểu từ ➔ không thêm hậu tố; kết thúc bằng "không" ➔ chỉ thêm hậu tố hợp với câu hỏi có/không.
FINAL_PARTICLES: frozenset[str] = frozenset({"nhé", "nha", "với", "ạ", "đi", "đã", "thôi", "nhỉ", "thế", "vậy"})
AFTER_KHONG: frozenset[str] = frozenset({"", " ạ", " vậy", " bạn ơi"})
NONSENSE_SYLLABLES: tuple[str, ...] = ("la", "bô", "tí", "xu", "ma", "kê", "rô", "ni", "pha", "đô", "quy", "lê",
                                       "mo", "tu", "xà", "bin", "gô", "nhe", "ráp", "tơ")
NONSENSE_COUNT: int = 30


@dataclass(frozen=True)
class Sample:
    text: str
    intent: str
    source: str     # seed | template | variant | reviewed | nonsense | asr_noise
    base: str       # nhóm gốc (id câu seed) để lấy mẫu đều giữa các câu seed


def slot_values(hmap: dict) -> dict[str, list[str]]:
    """Giá trị cho từng placeholder, chỉ lấy từ hospital_map.json."""
    depts: list[str] = []
    for d in hmap["departments"]:
        if d["name"] in EXCLUDED_DEPARTMENTS:
            continue
        for a in [d["name"].lower(), *d["aliases"]]:
            if "khoa" not in a.split() and a not in depts:
                depts.append(a)
    rooms: list[str] = []
    for r in hmap["rooms"]:
        n = r["number"]
        rooms += [n, read_number(int(n)), spell_digits(n)]
    room_names = [a for r in hmap["rooms"] for a in r["aliases"] if a not in EXCLUDED_ROOM_ALIASES]
    keys = {f["key"] for f in hmap["facilities"]}
    unknown_keys = set(FACILITY_NOUNS) - keys
    if unknown_keys:
        raise ValueError(f"facility keys not in hospital_map.json: {sorted(unknown_keys)}")
    facilities = [n for k in FACILITY_NOUNS for n in FACILITY_NOUNS[k]]
    return {"department": depts, "room": rooms, "room_name": room_names, "facility": facilities}


def _clean(text: str) -> str:
    """Gộp khoảng trắng và từ lặp do ghép ("phòng phòng tiêm", "khoa khoa nhi")."""
    words = text.split()
    out = [w for i, w in enumerate(words) if i == 0 or not (w == words[i - 1] and w in ("phòng", "khoa", "chỗ"))]
    return " ".join(out)


def expand_templates(seed: list[dict[str, str]], values: dict[str, list[str]]) -> list[Sample]:
    """Câu seed có placeholder ➔ mọi giá trị slot; không có ➔ giữ nguyên (source = seed)."""
    out: list[Sample] = []
    for row in seed:
        names = PLACEHOLDER_RE.findall(row["text"])
        if not names:
            out.append(Sample(_clean(row["text"]), row["intent"], "seed", row["id"]))
            continue
        if len(set(names)) != 1:
            raise ValueError(f"{row['id']}: one placeholder kind per template, got {names}")
        name = names[0]
        if name not in values:
            raise ValueError(f"{row['id']}: unknown placeholder {{{name}}}")
        for v in values[name]:
            out.append(Sample(_clean(row["text"].replace("{" + name + "}", v)), row["intent"], "template", row["id"]))
    return out


def rule_variants(text: str, kind: str) -> list[str]:
    """Đổi xưng hô, bỏ chủ ngữ "tôi", thêm từ đệm đầu/cuối câu (kể cả chuyển "bạn ơi" ra cuối câu)."""
    words = text.split()
    bases = {text}
    if "tôi" in words:
        bases |= {" ".join(p if w == "tôi" else w for w in words) for p in PRONOUNS}
        if words[0] == "tôi" and len(words) >= 3:
            bases.add(" ".join(words[1:]))
    out: set[str] = set()
    for b in bases:
        pronoun = next((w for w in b.split() if w in PRONOUNS), "tôi")
        for pre in PREFIXES[kind]:
            if "hỏi" in pre and b.startswith("cho "):
                continue
            last = b.split()[-1]
            for suf in SUFFIXES[kind]:
                if suf and (last in FINAL_PARTICLES or (last == "không" and suf not in AFTER_KHONG)):
                    continue
                if pre.startswith("bạn ơi") and suf == " bạn ơi":
                    continue
                out.add(_clean(pre.format(p=pronoun) + b + suf))
    out.discard(text)
    return sorted(out)


def nonsense(n: int, rng: random.Random) -> list[str]:
    return [" ".join(rng.choice(NONSENSE_SYLLABLES) for _ in range(rng.randint(3, 6))) for _ in range(n)]


def build_pool(seed: list[dict[str, str]], hmap: dict, reviewed: list[dict[str, str]], rng: random.Random) -> list[Sample]:
    kinds = {r["id"]: r["kind"] for r in seed}
    pool: list[Sample] = []
    for s in expand_templates(seed, slot_values(hmap)):
        pool.append(s)
        pool += [Sample(v, s.intent, "variant", s.base) for v in rule_variants(s.text, kinds[s.base])]
    pool += [Sample(normalize(r["text"]), r["intent"], "reviewed", "reviewed") for r in reviewed]
    pool += [Sample(t, "unknown", "nonsense", "nonsense") for t in nonsense(NONSENSE_COUNT, rng)]
    return dedupe(pool)


def dedupe(samples: Iterable[Sample]) -> list[Sample]:
    """Theo văn bản đã chuẩn hóa; câu trùng mà khác nhãn ➔ lỗi (seed mâu thuẫn)."""
    seen: dict[str, Sample] = {}
    for s in samples:
        key = normalize(s.text)
        if key in seen:
            if seen[key].intent != s.intent:
                raise ValueError(f"same text, different intents: {key!r} ({seen[key].intent}, {s.intent})")
            continue
        seen[key] = replace(s, text=key)
    return list(seen.values())


def remove_similar(pool: list[Sample], tests: list[str], threshold: float = LEAK_THRESHOLD,
                   ) -> tuple[list[Sample], list[dict[str, object]]]:
    """Loại câu có normalized Levenshtein similarity ≥ threshold với bất kỳ câu test nào."""
    if not pool or not tests:
        return list(pool), []
    test_norm = [normalize(t) for t in tests]
    sims = cdist([s.text for s in pool], test_norm, scorer=Levenshtein.normalized_similarity, workers=-1)
    kept: list[Sample] = []
    leaked: list[dict[str, object]] = []
    for s, row in zip(pool, sims):
        j = int(row.argmax())
        if row[j] >= threshold:
            leaked.append({"text": s.text, "intent": s.intent, "source": s.source, "base": s.base,
                           "similar_to": test_norm[j], "similarity": round(float(row[j]), 4)})
        else:
            kept.append(s)
    return kept, leaked


def balanced_sample(samples: list[Sample], k: int, rng: random.Random) -> list[Sample]:
    """Lấy tối đa k câu, xoay vòng giữa các nhóm `base` để câu seed nào cũng có mặt."""
    groups: dict[str, list[Sample]] = {}
    for s in samples:
        groups.setdefault(s.base, []).append(s)
    for g in groups.values():
        rng.shuffle(g)
    order = sorted(groups)
    out: list[Sample] = []
    while len(out) < k and any(groups[b] for b in order):
        for b in order:
            if groups[b] and len(out) < k:
                out.append(groups[b].pop())
    return out


def stratified_split(samples: list[Sample], val_frac: float, seed: int) -> tuple[list[Sample], list[Sample]]:
    train, val = train_test_split(samples, test_size=val_frac, random_state=seed,
                                  stratify=[s.intent for s in samples])
    return list(train), list(val)


def load_test_ref(manifest: pd.DataFrame) -> pd.DataFrame:
    m = manifest[manifest["ref_verified"].astype(str) == "True"]
    rows, seen = [], set()
    for _, r in m.sort_values("clip_id").iterrows():
        key = normalize(r["text_ref"])
        if key not in seen:
            seen.add(key)
            rows.append({"text": r["text_ref"], "intent": r["intent"], "source": "test_ref", "split": "test_ref",
                         "clip_id": r["clip_id"]})
    df = pd.DataFrame(rows)
    df.insert(0, "id", [f"ref{i:04d}" for i in range(len(df))])
    return df


def load_test_stt(stt: pd.DataFrame, verified: set[str]) -> pd.DataFrame:
    s = stt[stt["clip_id"].isin(verified) & stt["hyp"].notna() & stt["error"].isna()]
    df = pd.DataFrame({"text": s["hyp"], "intent": s["intent_true"], "source": "test_stt", "split": "test_stt",
                       "clip_id": s["clip_id"], "snr_db": s["snr_db"], "distance_m": s["distance_m"],
                       "noise": s["noise"]}).reset_index(drop=True)
    df.insert(0, "id", [f"stt{i:05d}" for i in range(len(df))])
    return df


def latest_stt_csv(reports_dir: Path) -> Path | None:
    found = sorted(reports_dir.glob("stt_eval_*.csv"))
    return found[-1] if found else None


def to_frame(samples: list[Sample], split: str, prefix: str) -> pd.DataFrame:
    df = pd.DataFrame([{"text": s.text, "intent": s.intent, "source": s.source, "split": split} for s in samples])
    df.insert(0, "id", [f"{prefix}{i:05d}" for i in range(len(df))])
    return df


def stats_table(frames: dict[str, pd.DataFrame]) -> str:
    counts = {name: Counter(df["intent"]) for name, df in frames.items()}
    lines = ["| intent | " + " | ".join(frames) + " |", "| :-- |" + " --: |" * len(frames)]
    for it in config.INTENTS:
        lines.append(f"| {it} | " + " | ".join(str(counts[n].get(it, 0)) for n in frames) + " |")
    lines.append("| **tổng** | " + " | ".join(str(len(df)) for df in frames.values()) + " |")
    return "\n".join(lines)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def check_labels(rows: Iterable[dict[str, str]], where: str) -> None:
    bad = sorted({r["intent"] for r in rows} - set(config.INTENTS))
    if bad:
        raise ValueError(f"{where}: intents outside Mục 2.2: {bad}")


def build(out_dir: Path, manifest_csv: Path, stt_csv: Path, script_md: Path,
          segment: Callable[[str], str], per_intent: int = PER_INTENT_MAX, seed: int = config.SEED,
          hmap: dict | None = None) -> int:
    """Trả 0 nếu xong, 2 nếu có intent < MIN_TRAIN câu train (không ghi train/val)."""
    rng = random.Random(seed)
    hmap = hmap or load_map()
    seed_rows = read_csv_rows(out_dir / "seed.csv")
    check_labels(seed_rows, "seed.csv")
    reviewed_path = out_dir / "reviewed.csv"
    reviewed = [r for r in read_csv_rows(reviewed_path) if r.get("keep", "").strip() == "1"] \
        if reviewed_path.is_file() else []
    check_labels(reviewed, "reviewed.csv")

    manifest = pd.read_csv(manifest_csv, dtype=str)
    test_ref = load_test_ref(manifest)
    test_stt = load_test_stt(pd.read_csv(stt_csv), set(test_ref["clip_id"]) |
                             set(manifest.loc[manifest["ref_verified"] == "True", "clip_id"]))
    script_texts = [r.text for r in load_script_table(script_md).values()]
    tests = sorted(set(test_ref["text"]) | set(test_stt["text"]) | set(script_texts))

    pool = build_pool(seed_rows, hmap, reviewed, rng)
    pool, leaked = remove_similar(pool, tests)
    by_intent: dict[str, list[Sample]] = {}
    for s in pool:
        by_intent.setdefault(s.intent, []).append(s)
    chosen = [s for it in config.INTENTS for s in balanced_sample(by_intent.get(it, []), per_intent, rng)]
    train, val = stratified_split(chosen, VAL_FRAC, seed)
    noisy = asr_noise.augment([s.text for s in train], NOISE_FRAC, seed)
    train_texts = {s.text for s in train} | {s.text for s in val}
    train += [Sample(t, train[i].intent, "asr_noise", train[i].base) for i, t in noisy if t not in train_texts]

    frames = {"train": to_frame(train, "train", "tr"), "val": to_frame(val, "val", "va"),
              "test_ref": test_ref, "test_stt": test_stt}
    pd.DataFrame(leaked, columns=["text", "intent", "source", "base", "similar_to", "similarity"]) \
        .to_csv(out_dir / "leak_removed.csv", index=False)
    table = stats_table(frames)
    print(table)
    print(f"\nleak_removed: {len(leaked)} câu; pool sau lọc: {len(pool)}")
    short = [it for it in config.INTENTS if (frames["train"]["intent"] == it).sum() < MIN_TRAIN]
    if short:
        print(f"\nCẢNH BÁO: intent có < {MIN_TRAIN} câu train: {short}. Bổ sung seed.csv rồi chạy lại.",
              file=sys.stderr)
        return 2
    for name, df in frames.items():
        df["text_seg"] = [segment(normalize(t)) for t in df["text"]]
        cols = COLUMNS + (STT_EXTRA if name == "test_stt" else ["clip_id"] if name == "test_ref" else [])
        df[cols].to_csv(out_dir / f"{name}.csv", index=False)
    (out_dir / "stats.md").write_text(
        f"# Thống kê dữ liệu intent (G18)\n\nseed={seed}, per_intent={per_intent}, leak_removed={len(leaked)}, "
        f"stt_csv={stt_csv.name}\n\n{table}\n", encoding="utf-8")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build intent dataset for PhoBERT (G18)")
    p.add_argument("--out-dir", type=Path, default=config.NLU_DATA_DIR)
    p.add_argument("--data-dir", type=Path, default=voice_config.DATA_DIR)
    p.add_argument("--stt-csv", type=Path, default=None, help="kết quả G13 (mặc định: file mới nhất trong reports/)")
    p.add_argument("--per-intent", type=int, default=PER_INTENT_MAX)
    p.add_argument("--seed", type=int, default=config.SEED)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    stt_csv = args.stt_csv or latest_stt_csv(config.REPORTS_DIR)
    if stt_csv is None or not stt_csv.is_file():
        print("ERROR: không tìm thấy reports/stt_eval_*.csv: chạy `python -m voice.eval_stt` (G13) trước",
              file=sys.stderr)
        return 1
    if not (args.out_dir / "seed.csv").is_file():
        print(f"ERROR: thiếu {args.out_dir / 'seed.csv'}", file=sys.stderr)
        return 1
    from nlu.segment import segment

    return build(args.out_dir, voice_config.manifest_path(args.data_dir), stt_csv, voice_config.SCRIPT_MD,
                 segment, args.per_intent, args.seed)


if __name__ == "__main__":
    sys.exit(main())
