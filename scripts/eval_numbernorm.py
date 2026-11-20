"""Number-normalized STT metric variant (read-only recomputation).

Recomputes WER/CER from the existing prediction CSV
(src/data/stt/evaluation/predictions/asr_predictions_*_samples.csv) with an
extra Vietnamese number-word -> digit normalization applied on top of the
baseline normalization, WITHOUT re-running the model and WITHOUT touching
the baseline outputs.

Baseline rules are preserved exactly:
  baseline  : lowercase -> strip punctuation -> collapse whitespace
  numbernorm: baseline -> scripts/vi_number_norm.normalize_numbers()

Outputs:
  src/data/stt/evaluation/predictions/asr_predictions_<N>_numbernorm.csv
  src/data/stt/evaluation/metrics/asr_summary_numbernorm.json
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import jiwer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stt_paths import METRICS_DIR, PREDICTIONS_DIR, ROOT
from vi_number_norm import normalize_numbers


def main() -> None:
    pred_csv = sorted(PREDICTIONS_DIR.glob("asr_predictions_*_samples.csv"))[-1]
    rows = list(csv.DictReader(open(pred_csv, encoding="utf-8")))
    print(f"Recomputing metrics from {pred_csv.name} ({len(rows)} samples)")

    def subset_metrics(subset: list[dict], gt_key: str, pr_key: str) -> dict:
        if not subset:
            return {}
        gt = [r[gt_key] for r in subset]
        pr = [r[pr_key] for r in subset]
        return {
            "count": len(subset),
            "wer": round(jiwer.wer(gt, pr), 4),
            "cer": round(jiwer.cer(gt, pr), 4),
        }

    # number-normalized variants of the already baseline-normalized strings
    for r in rows:
        r["numnorm_ground_truth"] = normalize_numbers(r["norm_ground_truth"])
        r["numnorm_prediction"] = normalize_numbers(r["norm_prediction"])
        r["numnorm_wer"] = round(
            jiwer.wer(r["numnorm_ground_truth"], r["numnorm_prediction"])
            if r["numnorm_ground_truth"] else 0.0, 4)
        r["numnorm_cer"] = round(
            jiwer.cer(r["numnorm_ground_truth"], r["numnorm_prediction"])
            if r["numnorm_ground_truth"] else 0.0, 4)

    cats = {"overall": rows}
    for c in ("reading", "natural", "common"):
        cats[c] = [r for r in rows if r["category"] == c]

    summary = {
        "note": "numbernorm = baseline normalization + vi_number_norm (words->digits). "
                "Baseline columns are byte-identical to the canonical run.",
        "source_predictions": pred_csv.name,
        "categories": {},
    }
    for name, subset in cats.items():
        summary["categories"][name] = {
            "baseline": subset_metrics(subset, "norm_ground_truth", "norm_prediction"),
            "numbernorm": subset_metrics(subset, "numnorm_ground_truth", "numnorm_prediction"),
        }

    out_csv = PREDICTIONS_DIR / pred_csv.name.replace("_samples", "_numbernorm")
    fields = list(rows[0].keys())
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    out_json = METRICS_DIR / "asr_summary_numbernorm.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'Category':<10} | {'n':>3} | {'base WER':>8} | {'numnorm WER':>11} | {'base CER':>8} | {'numnorm CER':>11}")
    print("-" * 75)
    for name, m in summary["categories"].items():
        b, nn = m["baseline"], m["numbernorm"]
        print(f"{name:<10} | {b['count']:>3} | {b['wer']:>8.2%} | {nn['wer']:>11.2%} | {b['cer']:>8.2%} | {nn['cer']:>11.2%}")
    print(f"\nWrote {out_csv}\nWrote {out_json}")

    changed = [r["file_id"] for r in rows
               if r["numnorm_ground_truth"] != r["norm_ground_truth"]
               or r["numnorm_prediction"] != r["norm_prediction"]]
    print(f"Samples affected by number normalization ({len(changed)}): {changed}")


if __name__ == "__main__":
    main()
