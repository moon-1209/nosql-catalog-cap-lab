"""Read-only validation of the STT fine-tuning workspace manifests.

Checks (no data is ever modified):
  1. All datasets/*/metadata.csv readable with stable, unique sample IDs.
  2. audio_path / raw_path exist; wavs decode as 16 kHz mono.
  3. No duplicate sample_id across manifests.
  4. No identical audio (md5) in two different splits/pools.
  5. Supervised splits (train/validation/test) may only contain rows with
     human_verified=1, a verified_* status, and a non-empty transcript.
  6. Verification-state consistency: verified rows must carry a transcript
     and timestamp; pending rows must not carry one.
  7. No prompt_group leakage across supervised splits; a prompt_group may not
     have conflicting proposed_split values in pending_review.
  8. Excluded rows must carry an excluded_reason.

Prints a report and exits non-zero on errors. Never writes or edits data.

Usage:  python src/data/stt/finetuning/scripts/validate_dataset.py
"""

from __future__ import annotations

import csv
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

FT = Path(__file__).resolve().parents[1]          # src/data/stt/finetuning
REPO = FT.parents[3]                              # repository root

MANIFESTS = {
    "train": FT / "datasets/train/metadata.csv",
    "validation": FT / "datasets/validation/metadata.csv",
    "test": FT / "datasets/test/metadata.csv",
    "pending_review": FT / "datasets/pending_review/metadata.csv",
    "pending_transcripts": FT / "datasets/pending_transcripts/metadata.csv",
    "unannotated": FT / "datasets/unannotated/metadata.csv",
    "excluded": FT / "datasets/excluded/metadata.csv",
}
SUPERVISED = {"train", "validation", "test"}

VERIFIED_R = {"verified_match", "verified_corrected"}
VERIFIED_N = {"transcribed", "verified"}
PENDING_R = {"pending_review", "needs_manual_review", "unusable_audio"}
PENDING_N = {"pending_transcription", "needs_manual_review", "unusable_audio"}


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    all_rows: dict[str, list[dict]] = {}

    # 1: manifests readable, stable ids, required columns per type
    for name, path in MANIFESTS.items():
        if not path.is_file():
            errors.append(f"{name}: manifest missing: {path}")
            continue
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
        if rows and not rows[0].get("sample_id"):
            errors.append(f"{name}: missing sample_id column")
        if any(not r.get("sample_id", "").strip() for r in rows):
            errors.append(f"{name}: empty sample_id present")
        all_rows[name] = rows

    # 3: duplicate sample IDs
    id_where = defaultdict(list)
    for name, rows in all_rows.items():
        for r in rows:
            id_where[r["sample_id"]].append(name)
    for sid, places in id_where.items():
        if len(places) > 1:
            errors.append(f"duplicate sample_id {sid} in {places}")

    # 2: audio paths exist and decode
    n_ok = n_bad = 0
    try:
        import soundfile as sf
    except ImportError:
        sf = None
        warnings.append("soundfile unavailable; decode check skipped")
    for name, rows in all_rows.items():
        for r in rows:
            for key in ("audio_path", "wav_path", "raw_path"):
                p = r.get(key)
                if p and not (REPO / p).is_file():
                    errors.append(f"{name}/{r['sample_id']}: missing {key}: {p}")
                    n_bad += 1
                    break
            else:
                wav_rel = r.get("audio_path") or r.get("wav_path")
                if sf and wav_rel:
                    try:
                        info = sf.info(str(REPO / wav_rel))
                        if info.samplerate != 16000 or info.channels != 1:
                            errors.append(f"{name}/{r['sample_id']}: wav not 16kHz mono")
                            n_bad += 1
                            continue
                    except Exception as e:
                        errors.append(f"{name}/{r['sample_id']}: wav unreadable: {e}")
                        n_bad += 1
                        continue
                n_ok += 1

    # 4: identical audio (md5) must not span splits/pools
    md5_where = defaultdict(set)
    for name, rows in all_rows.items():
        if name == "excluded":
            continue  # excluded rows intentionally alias supervised audio
        for r in rows:
            p = REPO / (r.get("audio_path") or "")
            if p.is_file():
                md5_where[hashlib.md5(p.read_bytes()).hexdigest()].add(name)
    for h, places in md5_where.items():
        if len(places) > 1:
            errors.append(f"identical audio md5 {h[:12]}… in pools {sorted(places)}")

    # 5 + 6: supervised contents and verification-state consistency
    n_eligible = 0
    for name in SUPERVISED:
        for r in all_rows.get(name, []):
            n_eligible += 1
            if r.get("human_verified") != "1":
                errors.append(f"{name}/{r['sample_id']}: human_verified != 1")
            if r.get("verification_status") not in VERIFIED_R | VERIFIED_N:
                errors.append(f"{name}/{r['sample_id']}: status {r.get('verification_status')!r} not verified")
            if not (r.get("transcript") or "").strip():
                errors.append(f"{name}/{r['sample_id']}: empty transcript in supervised split")
    if n_eligible == 0:
        warnings.append("supervised splits are EMPTY — 0 samples meet verified-GT eligibility")

    for r in all_rows.get("pending_review", []):
        st = r.get("verification_status", "")
        if st in VERIFIED_R:
            if not (r.get("transcript_verified") or "").strip():
                errors.append(f"pending_review/{r['sample_id']}: {st} but empty transcript_verified")
            if not (r.get("verification_timestamp") or "").strip():
                errors.append(f"pending_review/{r['sample_id']}: {st} but no timestamp")
        elif st not in PENDING_R:
            errors.append(f"pending_review/{r['sample_id']}: unknown status {st!r}")
        elif (r.get("transcript_verified") or "").strip():
            errors.append(f"pending_review/{r['sample_id']}: transcript present while status {st}")

    for r in all_rows.get("pending_transcripts", []) + all_rows.get("unannotated", []):
        st = r.get("transcript_status", "")
        if st in VERIFIED_N:
            if not (r.get("verbatim_transcript") or "").strip():
                errors.append(f"pending_transcripts/{r['sample_id']}: {st} but empty verbatim_transcript")
        elif st not in PENDING_N:
            errors.append(f"pending_transcripts/{r['sample_id']}: unknown status {st!r}")
        elif (r.get("verbatim_transcript") or "").strip():
            errors.append(f"pending_transcripts/{r['sample_id']}: transcript present while status {st}")

    # 7: prompt-group leakage in supervised splits + consistent proposal
    pg_sup = defaultdict(set)
    for name in SUPERVISED:
        for r in all_rows.get(name, []):
            pg_sup[r["prompt_group"]].add(name)
    for pg, places in pg_sup.items():
        if len(places) > 1:
            errors.append(f"prompt leakage: {pg} in {sorted(places)}")
    pg_prop = defaultdict(set)
    for r in all_rows.get("pending_review", []):
        pg_prop[r["prompt_group"]].add(r.get("proposed_split", ""))
    for pg, splits in pg_prop.items():
        if len(splits) > 1:
            errors.append(f"pending_review prompt_group {pg} has conflicting proposed_split {sorted(splits)}")

    # 8: excluded rows need a reason
    for r in all_rows.get("excluded", []):
        if not (r.get("excluded_reason") or "").strip():
            errors.append(f"excluded/{r['sample_id']}: missing excluded_reason")

    speakers = sorted({r.get("speaker_id") for rows in all_rows.values() for r in rows if r.get("speaker_id")})
    if len(speakers) < 3:
        warnings.append(f"only {len(speakers)} speaker(s) {speakers} — no speaker-disjoint evaluation possible")

    print("=" * 60)
    print("STT FINETUNING DATASET VALIDATION (GT-verification aware)")
    print("=" * 60)
    for name, path in MANIFESTS.items():
        print(f"  {name:<22} {len(all_rows.get(name, [])):>4} rows")
    print("-" * 60)
    print(f"  audio paths verified OK : {n_ok}")
    print(f"  audio paths broken      : {n_bad}")
    print(f"  supervised-eligible     : {n_eligible}")
    print(f"  distinct speakers       : {speakers}")
    print("-" * 60)
    for w in warnings:
        print(f"  WARNING: {w}")
    if errors:
        for e in errors[:50]:
            print(f"  ERROR: {e}")
        if len(errors) > 50:
            print(f"  … and {len(errors) - 50} more errors")
        print(f"\nRESULT: FAIL ({len(errors)} error(s), {len(warnings)} warning(s))")
        return 1
    print(f"\nRESULT: PASS ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
