"""Interactive review helper for STT transcript verification (read/append-only).

Plays each pending sample's WAV via macOS `afplay` (built-in, no deps),
shows script reference + model prediction, and lets the reviewer type the
verbatim transcript and a status. Writes results back into the same manifest
CSV (UTF-8 preserved, stable sample IDs untouched).

It NEVER auto-fills a transcript and NEVER auto-marks verified; every
verified status requires a human keystroke.

Usage (run from repo root):
  python src/data/stt/finetuning/scripts/review_tool.py --set r   # 90 script-read takes
  python src/data/stt/finetuning/scripts/review_tool.py --set n   # 80 natural takes
  python src/data/stt/finetuning/scripts/review_tool.py --set r --no-audio   # text-only triage
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

FT = Path(__file__).resolve().parents[1]
REPO = FT.parents[3]

SETS = {
    # set -> (manifest, transcript field, status field, allowed statuses)
    "r": (
        FT / "datasets/pending_review/metadata.csv",
        "transcript_verified",
        "verification_status",
        ["pending_review", "verified_match", "verified_corrected",
         "unusable_audio", "needs_manual_review"],
    ),
    "n": (
        FT / "datasets/pending_transcripts/metadata.csv",
        "verbatim_transcript",
        "transcript_status",
        ["pending_transcription", "transcribed", "verified",
         "unusable_audio", "needs_manual_review"],
    ),
    "u": (  # unannotated groups: kids, Female 30, Male 30, "(1)" second takes
        FT / "datasets/unannotated/metadata.csv",
        "verbatim_transcript",
        "transcript_status",
        ["pending_transcription", "transcribed", "verified",
         "unusable_audio", "needs_manual_review"],
    ),
}


def play(wav_rel: str) -> None:
    p = REPO / wav_rel
    if p.is_file():
        subprocess.run(["afplay", str(p)], check=False)
    else:
        print(f"  !! missing audio: {wav_rel}")


_MODEL = None  # lazily loaded (processor, model, device) or None if unavailable


def get_asr():
    """Load the local PhoASR model once. Returns None when unavailable."""
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    try:
        import torch
        from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
        model_dir = REPO / "models" / "PhoASR-whisper-small"
        if not model_dir.is_dir():
            return None
        device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
        processor = AutoProcessor.from_pretrained(str(model_dir), local_files_only=True)
        model = AutoModelForSpeechSeq2Seq.from_pretrained(str(model_dir), local_files_only=True).to(device)
        model.eval()
        _MODEL = (processor, model, device)
    except Exception:
        _MODEL = None
    return _MODEL


def transcribe(wav_rel: str) -> str:
    """Best-effort ASR prediction. Never raises; returns '' on failure."""
    try:
        import soundfile as sf
        import torch
        asr = get_asr()
        if not asr:
            return ""
        processor, model, device = asr
        audio, _ = sf.read(str(REPO / wav_rel), dtype="float32")
        if getattr(audio, "ndim", 1) > 1:
            audio = audio.mean(axis=1)
        inputs = processor(audio, sampling_rate=16000, return_tensors="pt", return_attention_mask=True)
        with torch.no_grad():
            out = model.generate(input_features=inputs.input_features.to(device),
                                 attention_mask=inputs.attention_mask.to(device),
                                 language="vi", task="transcribe")
        return processor.batch_decode(out["sequences"] if isinstance(out, dict) else out,
                                      skip_special_tokens=True)[0].strip()
    except Exception:
        return ""


def save_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    tmp.replace(path)  # atomic-ish: never a half-written manifest


def auto_loop(rows, path, fields, s_field, args) -> bool:
    """Auto-advance review: play audio, run ASR, show both, move on.
    Returns True if the manifest changed (predictions stored)."""
    asr_ok = get_asr() is not None
    print(f"ASR model: {'loaded (PhoASR-whisper-small)' if asr_ok else 'UNAVAILABLE — audio-only mode'}")
    print("Ctrl+C pauses and saves. Predictions go to model_prediction only — never GT.\n")
    dirty = False
    count = 0
    try:
        for i, row in enumerate(rows):
            if not row[s_field].startswith("pending"):
                continue
            if args.limit and count >= args.limit:
                break
            count += 1
            print("=" * 70)
            print(f"[{i + 1}/{len(rows)}] {row['sample_id']}  speaker={row.get('speaker_id') or row.get('voice_group')}")
            print(f"  {row['audio_path']}")
            print(f"  script: {row['script_reference'] or '(none)'}")
            if not args.no_audio:
                play(row["audio_path"])
            pred = row.get("model_prediction") or transcribe(row["audio_path"])
            if pred:
                row["model_prediction"] = pred  # prediction field only, never transcript
                dirty = True
            print(f"  ASR   : {pred or '(unavailable)'}")
    except KeyboardInterrupt:
        print("\n\nPaused by user — saving progress…")
    return dirty


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--set", choices=["r", "n", "u"], required=True)
    ap.add_argument("--no-audio", action="store_true", help="skip afplay playback")
    ap.add_argument("--auto", action="store_true", help="auto-advance: play + ASR, no Enter needed")
    ap.add_argument("--limit", type=int, default=0, help="max records to process (0 = all pending)")
    ap.add_argument("--dry-run", action="store_true", help="run the flow without writing the manifest")
    args = ap.parse_args()

    path, t_field, s_field, allowed = SETS[args.set]
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    fields = list(rows[0].keys())

    if args.auto:
        dirty = auto_loop(rows, path, fields, s_field, args)
        if dirty and not args.dry_run:
            save_csv(path, fields, rows)
            print(f"Saved {path}")
        elif dirty:
            print("(dry-run) changes not written")
        return 0
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    fields = list(rows[0].keys())
    pending = [r for r in rows if r[s_field].startswith("pending")]
    print(f"{len(pending)} pending rows in {path.relative_to(REPO)}")
    print("Commands: [Enter]=skip  r=replay  q=save&quit  else type verbatim transcript.\n")

    dirty = False
    for i, row in enumerate(rows):
        if not row[s_field].startswith("pending"):
            continue
        print("=" * 70)
        print(f"[{i + 1}/{len(rows)}] {row['sample_id']}  speaker={row.get('speaker_id')}  {row['audio_path']}")
        print(f"  script: {row['script_reference']}")
        print(f"  model : {row['model_prediction']}")
        if not args.no_audio:
            play(row["audio_path"])
        while True:
            ans = input("verbatim> ").strip()
            if ans == "r":
                play(row["audio_path"])
                continue
            if ans == "q":
                break
            if ans == "":
                break
            row[t_field] = ans
            if t_field == "transcript_verified":
                match = " (script text differs)" if ans != row["script_reference"] else ""
                default = "verified_match" if not match else "verified_corrected"
            else:
                default = "transcribed"
                match = ""
            st = input(f"status [{default}{match}] (Enter=accept, or one of {allowed}): ").strip() or default
            if st not in allowed:
                print(f"  invalid status {st!r}; row left pending")
                break
            row[s_field] = st
            row["verification_timestamp"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            note = input("notes (optional)> ").strip()
            if note:
                row["reviewer_notes"] = note
            dirty = True
            break
        if ans == "q":
            break

    if dirty:
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
        done = sum(1 for r in rows if not r[s_field].startswith("pending"))
        print(f"\nSaved {path} — {done}/{len(rows)} reviewed.")
    else:
        print("\nNo changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
