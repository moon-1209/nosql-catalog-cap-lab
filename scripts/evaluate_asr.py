"""Comprehensive ASR evaluation benchmark on the real hospital voice dataset.

Evaluates every processed WAV under src/data/stt/processed/real_voice/wav/
whose stem maps to a file_id in data/annotations.json. When the same stem
exists in several speaker folders, canonical benchmark folders win
(scripts/stt_paths.BENCHMARK_SOURCE_DIRS).

Metrics quantified:
  - WER (Word Error Rate - raw & normalized)
  - CER (Character Error Rate - normalized)
  - Sentence Accuracy / Exact Match %
  - Normalized Match %
  - Latency & RTF (Real-Time Factor = inference_duration / audio_duration)
  - Stratified breakdown: reading (_r), natural (_n), common (Nam_C/Nu_C)

Outputs (under src/data/stt/evaluation/):
  - predictions/asr_predictions_<N>_samples.csv
  - metrics/asr_summary.json
  - error_analysis/error_analysis_<N>_samples.csv
"""

from __future__ import annotations

import csv
import json
import re
import time
from pathlib import Path

import jiwer
import numpy as np
import soundfile as sf
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

from stt_paths import (
    ANNOTATIONS_FILE,
    BENCHMARK_SOURCE_DIRS,
    ERROR_ANALYSIS_DIR,
    METRICS_DIR,
    PREDICTIONS_DIR,
    PROCESSED_WAV_DIR,
    ROOT,
)

MODEL_DIR = ROOT / "models" / "PhoASR-whisper-small"
WAV_DIR = PROCESSED_WAV_DIR
PREDICTIONS_DIR_ = PREDICTIONS_DIR
METRICS_DIR_ = METRICS_DIR
ERROR_ANALYSIS_DIR_ = ERROR_ANALYSIS_DIR
OUT_JSON = METRICS_DIR / "asr_summary.json"


def normalize_text(text: str) -> str:
    """Normalize Vietnamese text for fair ASR acoustic comparison:
    lowercase, remove punctuation, strip duplicate whitespaces.
    """
    text = text.lower()
    # Remove punctuation
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_audio(path: Path, target_sr: int = 16000) -> tuple[np.ndarray, float]:
    audio, sr = sf.read(str(path), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    duration = len(audio) / sr
    return audio, duration


def main() -> None:
    for d in (PREDICTIONS_DIR_, METRICS_DIR_, ERROR_ANALYSIS_DIR_):
        d.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print("================================================================")
    print("PhoASR-whisper-small: 70 Real Voice Benchmark Evaluation")
    print("================================================================")
    print(f"Device: {device} ({torch.cuda.get_device_name(0) if device == 'cuda' else 'CPU'})")
    print(f"Model path: {MODEL_DIR}")
    print(f"Dataset:    {WAV_DIR}")

    # Load annotations
    with open(ANNOTATIONS_FILE, "r", encoding="utf-8") as f:
        annot_data = json.load(f)
    annotations = {r["file_id"]: r for r in annot_data["annotations"]}

    # Collect wav files recursively. Keep only stems that map to an annotation
    # file_id; when the same stem exists in several speaker folders (e.g. child
    # re-recordings in "Trẻ con"), prefer canonical benchmark folders, then
    # root-level files (Nu_C*.wav).
    def dir_rank(p: Path) -> int:
        rel = p.parent.relative_to(WAV_DIR).as_posix()
        if rel == ".":
            return 0
        try:
            return 1 + BENCHMARK_SOURCE_DIRS.index(rel)
        except ValueError:
            return 1 + len(BENCHMARK_SOURCE_DIRS)

    candidates: dict[str, list[Path]] = {}
    for p in sorted(WAV_DIR.rglob("*.wav")):
        candidates.setdefault(p.stem, []).append(p)

    wav_files = []
    duplicates = []
    for stem, paths in candidates.items():
        if stem not in annotations:
            continue
        paths.sort(key=dir_rank)
        wav_files.append(paths[0])
        duplicates.extend(paths[1:])
    wav_files.sort(key=lambda p: p.stem)
    print(f"Found {len(wav_files)} annotated WAV files for evaluation.")

    missing_audio = sorted(set(annotations) - {p.stem for p in wav_files})
    unannotated = sorted({p.stem for p in WAV_DIR.rglob("*.wav")} - set(annotations))
    if missing_audio:
        print(f"WARNING: {len(missing_audio)} annotations have no audio file: {missing_audio}")
    if unannotated:
        print(f"WARNING: {len(unannotated)} audio files have no annotation and were skipped: {unannotated}")
    if duplicates:
        print(f"INFO: {len(duplicates)} wavs share an annotated file_id and were skipped (non-canonical folder).")

    # Load Model & Processor
    print("\nLoading PhoASR model directly from disk (local_files_only=True)...")
    t0 = time.time()
    processor = AutoProcessor.from_pretrained(str(MODEL_DIR), local_files_only=True)
    model = AutoModelForSpeechSeq2Seq.from_pretrained(str(MODEL_DIR), local_files_only=True).to(device)
    model.eval()
    print(f"Model loaded in {time.time() - t0:.2f}s.\n")

    results = []
    failed = []
    total_audio_time = 0.0
    total_infer_time = 0.0

    print(f"{'#':<3} | {'File ID':<10} | {'Mode':<7} | {'Audio(s)':<8} | {'Infer(s)':<8} | {'RTF':<6} | {'Norm WER':<8} | {'Prediction Preview'}")
    print("-" * 90)

    for idx, wav_path in enumerate(wav_files, 1):
        file_id = wav_path.stem
        meta = annotations.get(file_id, {})
        ground_truth = meta.get("text", "")
        intent = meta.get("intent", "")
        mode_label = meta.get("mode_label", "reading" if "_r" in file_id or "Nam_C" in file_id else "natural")
        speaker = meta.get("speaker", "A")

        try:
            # Load audio
            audio, duration = load_audio(wav_path, target_sr=16000)
            total_audio_time += duration

            # Prepare inputs
            inputs = processor(audio, sampling_rate=16000, return_tensors="pt", return_attention_mask=True)
            input_features = inputs.input_features.to(device)
            attention_mask = inputs.attention_mask.to(device)

            # Inference
            t_start = time.perf_counter()
            with torch.no_grad():
                outputs = model.generate(
                    input_features=input_features,
                    attention_mask=attention_mask,
                    language="vi",
                    task="transcribe",
                    return_dict_in_generate=True,
                )
            infer_time = time.perf_counter() - t_start
            total_infer_time += infer_time

            pred_text = processor.batch_decode(outputs["sequences"], skip_special_tokens=True)[0].strip()
        except Exception as e:
            print(f"{idx:<3} | {file_id:<10} | FAILED: {e}")
            failed.append({"file_id": file_id, "error": str(e)})
            continue

        # Metrics calculation
        norm_gt = normalize_text(ground_truth)
        norm_pred = normalize_text(pred_text)

        raw_match = (pred_text == ground_truth)
        norm_match = (norm_pred == norm_gt)

        # WER & CER
        sample_raw_wer = jiwer.wer(ground_truth, pred_text) if ground_truth else 0.0
        sample_norm_wer = jiwer.wer(norm_gt, norm_pred) if norm_gt else 0.0
        sample_norm_cer = jiwer.cer(norm_gt, norm_pred) if norm_gt else 0.0
        rtf = infer_time / duration if duration > 0 else 0.0

        # Category
        if file_id.startswith(("Nam_C", "Nu_C")):
            category = "common"
        elif file_id.endswith("_r"):
            category = "reading"
        else:
            category = "natural"

        results.append({
            "file_id": file_id,
            "wav_path": wav_path.relative_to(WAV_DIR).as_posix(),
            "category": category,
            "speaker": speaker,
            "mode": mode_label,
            "intent": intent,
            "duration_s": round(duration, 3),
            "infer_time_s": round(infer_time, 3),
            "rtf": round(rtf, 3),
            "ground_truth": ground_truth,
            "prediction": pred_text,
            "norm_ground_truth": norm_gt,
            "norm_prediction": norm_pred,
            "raw_match": raw_match,
            "norm_match": norm_match,
            "raw_wer": round(sample_raw_wer, 4),
            "norm_wer": round(sample_norm_wer, 4),
            "norm_cer": round(sample_norm_cer, 4),
        })

        preview = pred_text[:35] + ("..." if len(pred_text) > 35 else "")
        print(f"{idx:<3} | {file_id:<10} | {category:<7} | {duration:6.2f}s  | {infer_time:6.2f}s  | {rtf:5.2f}  | {sample_norm_wer:6.2%}   | {preview}")

    # Aggregations
    def compute_subset_metrics(subset: list[dict]) -> dict:
        n = len(subset)
        if n == 0:
            return {}
        all_gt_raw = [r["ground_truth"] for r in subset]
        all_pred_raw = [r["prediction"] for r in subset]
        all_gt_norm = [r["norm_ground_truth"] for r in subset]
        all_pred_norm = [r["norm_prediction"] for r in subset]

        corpus_raw_wer = jiwer.wer(all_gt_raw, all_pred_raw)
        corpus_norm_wer = jiwer.wer(all_gt_norm, all_pred_norm)
        corpus_norm_cer = jiwer.cer(all_gt_norm, all_pred_norm)

        raw_acc = sum(1 for r in subset if r["raw_match"]) / n
        norm_acc = sum(1 for r in subset if r["norm_match"]) / n
        avg_infer = sum(r["infer_time_s"] for r in subset) / n
        avg_rtf = sum(r["rtf"] for r in subset) / n

        return {
            "count": n,
            "raw_wer": round(corpus_raw_wer, 4),
            "norm_wer": round(corpus_norm_wer, 4),
            "norm_cer": round(corpus_norm_cer, 4),
            "exact_sentence_accuracy": round(raw_acc, 4),
            "normalized_sentence_accuracy": round(norm_acc, 4),
            "mean_inference_s": round(avg_infer, 3),
            "mean_rtf": round(avg_rtf, 3),
        }

    overall_metrics = compute_subset_metrics(results)
    reading_metrics = compute_subset_metrics([r for r in results if r["category"] == "reading"])
    natural_metrics = compute_subset_metrics([r for r in results if r["category"] == "natural"])
    common_metrics = compute_subset_metrics([r for r in results if r["category"] == "common"])

    summary = {
        "model": "Qualcomm-AI-Research/PhoASR-whisper-small",
        "dataset": "real_hospital_inquiry_voice_vietnamese",
        "total_samples": len(results),
        "total_audio_duration_s": round(total_audio_time, 2),
        "total_inference_time_s": round(total_infer_time, 2),
        "overall_rtf": round(total_infer_time / total_audio_time, 3),
        "overall": overall_metrics,
        "failed_samples": failed,
        "by_category": {
            "reading_r": reading_metrics,
            "natural_n": natural_metrics,
            "common_c": common_metrics,
        },
    }

    if not results:
        print("No samples evaluated; nothing to write.")
        return

    # Save per-sample predictions CSV
    out_csv = PREDICTIONS_DIR_ / f"asr_predictions_{len(results)}_samples.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    # Save metrics summary JSON
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # Save error analysis: failed samples + worst normalized-WER predictions
    err_csv = ERROR_ANALYSIS_DIR_ / f"error_analysis_{len(results)}_samples.csv"
    err_rows = sorted(results, key=lambda r: r["norm_wer"], reverse=True)[:50]
    err_fields = ["file_id", "wav_path", "category", "ground_truth", "prediction",
                  "norm_wer", "norm_cer", "rtf"]
    with open(err_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=err_fields)
        writer.writeheader()
        writer.writerows([{k: r[k] for k in err_fields} for r in err_rows])
        writer.writerows([{k: "" for k in err_fields}])
        writer.writerows([{"file_id": "__failed__", "wav_path": r["file_id"], "prediction": r["error"]} for r in failed])

    print("\n" + "=" * 65)
    print("BENCHMARK SUMMARY REPORT")
    print("=" * 65)
    print(f"Total Samples Evaluated: {len(results)} ({total_audio_time/60:.1f} minutes of speech)")
    print(f"Total Inference Time:    {total_infer_time:.2f}s (Real-Time Factor: {total_infer_time/total_audio_time:.3f}x)")
    print("-" * 65)
    print(f"{'Category':<15} | {'Samples':<7} | {'Norm WER':<10} | {'Norm CER':<10} | {'Sentence Acc':<12}")
    print("-" * 65)
    print(f"{'Reading (_r)':<15} | {reading_metrics['count']:<7} | {reading_metrics['norm_wer']:<10.2%} | {reading_metrics['norm_cer']:<10.2%} | {reading_metrics['normalized_sentence_accuracy']:<12.2%}")
    print(f"{'Common (C)':<15} | {common_metrics['count']:<7} | {common_metrics['norm_wer']:<10.2%} | {common_metrics['norm_cer']:<10.2%} | {common_metrics['normalized_sentence_accuracy']:<12.2%}")
    print(f"{'Natural (_n)':<15} | {natural_metrics['count']:<7} | {natural_metrics['norm_wer']:<10.2%} | {natural_metrics['norm_cer']:<10.2%} | {natural_metrics['normalized_sentence_accuracy']:<12.2%}")
    print("-" * 65)
    print(f"{'OVERALL':<15} | {overall_metrics['count']:<7} | {overall_metrics['norm_wer']:<10.2%} | {overall_metrics['norm_cer']:<10.2%} | {overall_metrics['normalized_sentence_accuracy']:<12.2%}")
    print("=" * 65)
    print(f"\nDetailed per-sample CSV saved to: {out_csv}")
    print(f"Summary JSON saved to:           {OUT_JSON}")
    print(f"Error analysis saved to:         {err_csv}")


if __name__ == "__main__":
    main()
