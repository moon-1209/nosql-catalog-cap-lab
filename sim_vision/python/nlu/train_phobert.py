"""Fine-tune PhoBERT-base-v2 phân loại intent (G19). Chạy offline từ model local.

Chạy: python -m nlu.train_phobert [--epochs 10 --batch 16 --lr 2e-5 ...]
Ra: PHOBERT_FT_DIR/ (model, tokenizer, label_map.json, threshold.json, train_report.md).
KHÔNG đọc test_ref.csv / test_stt.csv (để G23).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from nlu import config

REQUIRED_FILES: tuple[str, ...] = ("config.json", "vocab.txt", "bpe.codes")
WEIGHT_FILES: tuple[str, ...] = ("pytorch_model.bin", "model.safetensors")
THRESHOLDS: tuple[float, ...] = tuple(round(0.30 + 0.05 * i, 2) for i in range(13))     # 0.30 … 0.90


@dataclass(frozen=True)
class HParams:
    lr: float = 2e-5
    batch: int = 16
    epochs: int = 10
    warmup: float = 0.1
    weight_decay: float = 0.01
    patience: int = 3
    seed: int = config.SEED
    max_len: int = config.MAX_SEQ_LEN
    grad_clip: float = 1.0


def missing_files(model_dir: Path) -> list[str]:
    missing = [f for f in REQUIRED_FILES if not (model_dir / f).is_file()]
    if not any((model_dir / f).is_file() for f in WEIGHT_FILES):
        missing.append(" hoặc ".join(WEIGHT_FILES))
    return missing


def pick_device() -> torch.device:
    return torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def label_map(labels: tuple[str, ...] = config.INTENTS) -> dict[str, int]:
    return {name: i for i, name in enumerate(labels)}


def encode(tokenizer: Any, texts: list[str], max_len: int) -> dict[str, torch.Tensor]:
    enc = tokenizer(texts, max_length=max_len, truncation=True, padding="max_length", return_tensors="pt")
    return {"input_ids": enc["input_ids"], "attention_mask": enc["attention_mask"]}


@torch.inference_mode()
def predict_proba(model: torch.nn.Module, enc: dict[str, torch.Tensor], device: torch.device,
                  batch: int = 64) -> np.ndarray:
    model.eval()
    out = []
    n = enc["input_ids"].shape[0]
    for i in range(0, n, batch):
        logits = model(**{k: v[i:i + batch].to(device) for k, v in enc.items()}).logits
        out.append(torch.softmax(logits.float(), dim=-1).cpu().numpy())
    return np.concatenate(out) if out else np.zeros((0, 0))


def macro_f1(y: np.ndarray, pred: np.ndarray) -> float:
    return float(f1_score(y, pred, average="macro", labels=np.unique(y), zero_division=0))


def cross_entropy(probs: np.ndarray, y: np.ndarray) -> float:
    return float(-np.log(np.clip(probs[np.arange(len(y)), y], 1e-12, 1.0)).mean())


def improved(f1: float, loss: float, best_f1: float, best_loss: float) -> bool:
    """Macro-F1 cao hơn; bằng nhau ➔ val loss thấp hơn (val bão hòa F1 = 1.0 từ sớm, xem ASSUMPTIONS G19)."""
    return f1 > best_f1 + 1e-9 or (abs(f1 - best_f1) <= 1e-9 and loss < best_loss)


def apply_threshold(probs: np.ndarray, threshold: float, unknown_idx: int) -> np.ndarray:
    pred = probs.argmax(axis=1)
    return np.where(probs.max(axis=1) < threshold, unknown_idx, pred)


def choose_threshold(probs: np.ndarray, y: np.ndarray, unknown_idx: int,
                     start: float = config.CONF_THRESHOLD_DEFAULT) -> tuple[float, float, list[tuple[float, float]]]:
    """Ngưỡng trong THRESHOLDS cho macro-F1 cao nhất (dự đoán dưới ngưỡng ➔ unknown).
    Bằng điểm ➔ chọn ngưỡng gần điểm khởi đầu 0.6 nhất."""
    curve = [(t, macro_f1(y, apply_threshold(probs, t, unknown_idx))) for t in THRESHOLDS]
    best_f1 = max(f for _, f in curve)
    best_t = min((t for t, f in curve if f >= best_f1 - 1e-12), key=lambda t: (abs(t - start), t))
    return best_t, best_f1, curve


def train(model: torch.nn.Module, tokenizer: Any, train_df: pd.DataFrame, val_df: pd.DataFrame,
          hp: HParams, device: torch.device, log: Callable[[str], None] = print) -> dict[str, Any]:
    """Huấn luyện, giữ trọng số tốt nhất theo macro-F1 val (đã nạp lại vào `model`). Trả lịch sử và xác suất val."""
    from transformers import get_linear_schedule_with_warmup

    set_seed(hp.seed)
    lm = label_map()
    y_train = torch.tensor([lm[i] for i in train_df["intent"]])
    y_val = np.array([lm[i] for i in val_df["intent"]])
    enc_train = encode(tokenizer, train_df["text_seg"].tolist(), hp.max_len)
    enc_val = encode(tokenizer, val_df["text_seg"].tolist(), hp.max_len)
    model.to(device)
    no_decay = ("bias", "LayerNorm.weight", "layer_norm.weight")
    groups = [
        {"params": [p for n, p in model.named_parameters() if not any(k in n for k in no_decay)],
         "weight_decay": hp.weight_decay},
        {"params": [p for n, p in model.named_parameters() if any(k in n for k in no_decay)], "weight_decay": 0.0},
    ]
    optim = torch.optim.AdamW(groups, lr=hp.lr)
    steps_per_epoch = (len(train_df) + hp.batch - 1) // hp.batch
    total = steps_per_epoch * hp.epochs
    sched = get_linear_schedule_with_warmup(optim, int(hp.warmup * total), total)
    gen = torch.Generator().manual_seed(hp.seed)
    history: list[dict[str, float]] = []
    best_f1, best_loss, best_state, best_epoch, bad = -1.0, float("inf"), None, 0, 0
    for epoch in range(1, hp.epochs + 1):
        model.train()
        t0 = time.perf_counter()
        perm = torch.randperm(len(train_df), generator=gen)
        loss_sum = 0.0
        for i in range(0, len(perm), hp.batch):
            idx = perm[i:i + hp.batch]
            out = model(**{k: v[idx].to(device) for k, v in enc_train.items()}, labels=y_train[idx].to(device))
            optim.zero_grad()
            out.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), hp.grad_clip)
            optim.step()
            sched.step()
            loss_sum += out.loss.item() * len(idx)
        probs = predict_proba(model, enc_val, device)
        f1 = macro_f1(y_val, probs.argmax(axis=1))
        val_loss = cross_entropy(probs, y_val)
        history.append({"epoch": epoch, "train_loss": loss_sum / len(perm), "val_loss": val_loss, "val_macro_f1": f1,
                        "seconds": time.perf_counter() - t0})
        log(f"epoch {epoch} | train_loss {loss_sum / len(perm):.4f} | val_loss {val_loss:.4f} | "
            f"val_macro_f1 {f1:.4f} | {time.perf_counter() - t0:.0f}s")
        if improved(f1, val_loss, best_f1, best_loss):
            best_f1, best_loss, best_epoch, bad = f1, val_loss, epoch, 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= hp.patience:
                log(f"early stopping: {hp.patience} epoch không cải thiện")
                break
    assert best_state is not None
    model.load_state_dict(best_state)
    probs = predict_proba(model, enc_val, device)
    return {"history": history, "best_epoch": best_epoch, "best_val_macro_f1": best_f1, "val_probs": probs,
            "y_val": y_val}


def confusion_md(y: np.ndarray, pred: np.ndarray, labels: tuple[str, ...]) -> str:
    present = sorted(set(y) | set(pred))
    cm = confusion_matrix(y, pred, labels=present)
    short = [labels[i][:8] for i in present]
    lines = ["| thật \\ dự đoán | " + " | ".join(short) + " |", "| :-- |" + " --: |" * len(present)]
    for i, row in zip(present, cm):
        lines.append(f"| {labels[i]} | " + " | ".join(str(v) if v else "·" for v in row) + " |")
    return "\n".join(lines)


def confused_pairs(y: np.ndarray, pred: np.ndarray, labels: tuple[str, ...]) -> list[tuple[str, str, int]]:
    pairs: dict[tuple[str, str], int] = {}
    for a, b in zip(y, pred):
        if a != b:
            pairs[(labels[a], labels[b])] = pairs.get((labels[a], labels[b]), 0) + 1
    return sorted(((a, b, n) for (a, b), n in pairs.items()), key=lambda x: -x[2])


def write_outputs(out_dir: Path, model: Any, tokenizer: Any, result: dict[str, Any], hp: HParams,
                  extra: dict[str, Any]) -> dict[str, Any]:
    labels = config.INTENTS
    unknown_idx = labels.index("unknown")
    y, probs = result["y_val"], result["val_probs"]
    pred = probs.argmax(axis=1)
    thr, thr_f1, curve = choose_threshold(probs, y, unknown_idx)
    out_dir.mkdir(parents=True, exist_ok=True)
    model.config.id2label = dict(enumerate(labels))
    model.config.label2id = label_map()
    model.save_pretrained(out_dir)
    tokenizer.save_pretrained(out_dir)
    (out_dir / "label_map.json").write_text(json.dumps(label_map(), ensure_ascii=False, indent=1), encoding="utf-8")
    threshold = {"conf_threshold": thr, "val_macro_f1_with_threshold": round(thr_f1, 4),
                 "val_macro_f1_no_threshold": round(macro_f1(y, pred), 4)}
    (out_dir / "threshold.json").write_text(json.dumps(threshold, indent=1), encoding="utf-8")
    per_class = f1_score(y, pred, average=None, labels=list(range(len(labels))), zero_division=0)
    lines = [
        "# Báo cáo fine-tune PhoBERT-base-v2 (G19)", "",
        f"Ngày: {time.strftime('%Y-%m-%d %H:%M')}. Thiết bị: {extra.get('device')}. "
        f"Dữ liệu: train {extra.get('n_train')} câu, val {len(y)} câu (`data/nlu`). Không dùng tập test.", "",
        "## Siêu tham số", "", "| Tham số | Giá trị |", "| :-- | :-- |",
        *[f"| {k} | {v} |" for k, v in asdict(hp).items()],
        "| optimizer | AdamW, lịch tuyến tính có warmup, không fp16 |", "",
        "## Theo epoch", "", "| epoch | train_loss | val_loss | val_macro_f1 | giây |", "| --: | --: | --: | --: | --: |",
        *[f"| {h['epoch']} | {h['train_loss']:.4f} | {h['val_loss']:.4f} | {h['val_macro_f1']:.4f} | {h['seconds']:.0f} |"
          for h in result["history"]],
        "", f"Checkpoint tốt nhất: epoch {result['best_epoch']} (macro-F1 val {result['best_val_macro_f1']:.4f}). "
        "Early stopping theo macro-F1 val; bằng điểm ➔ chọn epoch có val loss thấp hơn.", "",
        "## Kết quả trên val (checkpoint tốt nhất)", "",
        f"- Accuracy: {accuracy_score(y, pred):.4f}",
        f"- Macro-F1: {macro_f1(y, pred):.4f}",
        f"- Ngưỡng tin cậy chọn trên val: **{thr}** (macro-F1 khi coi `max_prob < ngưỡng` là `unknown`: "
        f"{thr_f1:.4f}). Bằng điểm ➔ chọn ngưỡng gần 0.6 nhất.", "",
        "| ngưỡng | " + " | ".join(f"{t:.2f}" for t, _ in curve) + " |", "| :-- |" + " --: |" * len(curve),
        "| macro-F1 | " + " | ".join(f"{f:.4f}" for _, f in curve) + " |", "",
        "### F1 từng lớp", "", "| intent | F1 | số câu val |", "| :-- | --: | --: |",
        *[f"| {labels[i]} | {per_class[i]:.4f} | {(y == i).sum()} |" for i in range(len(labels))], "",
        "### Ma trận nhầm lẫn", "", confusion_md(y, pred, labels), "",
        "### Cặp hay nhầm", "",
        *([f"- {a} ➔ {b}: {n}" for a, b, n in confused_pairs(y, pred, labels)] or ["- Không có câu val nào sai."]),
        "",
    ]
    for title, body in extra.get("sections", []):
        lines += [f"## {title}", "", body, ""]
    (out_dir / "train_report.md").write_text("\n".join(lines), encoding="utf-8")
    return threshold


def parse_args(argv: list[str]) -> argparse.Namespace:
    d = HParams()
    p = argparse.ArgumentParser(description="Fine-tune PhoBERT-base-v2 for intent classification (G19)")
    p.add_argument("--data-dir", type=Path, default=config.NLU_DATA_DIR)
    p.add_argument("--model-dir", type=Path, default=config.PHOBERT_DIR)
    p.add_argument("--out-dir", type=Path, default=config.PHOBERT_FT_DIR)
    p.add_argument("--lr", type=float, default=d.lr)
    p.add_argument("--batch", type=int, default=d.batch)
    p.add_argument("--epochs", type=int, default=d.epochs)
    p.add_argument("--warmup", type=float, default=d.warmup)
    p.add_argument("--weight-decay", type=float, default=d.weight_decay)
    p.add_argument("--patience", type=int, default=d.patience)
    p.add_argument("--seed", type=int, default=d.seed)
    p.add_argument("--repeat", action="store_true", help="train lần 2 cùng seed để đo sai lệch (không lưu)")
    return p.parse_args(argv)


def _load(model_dir: Path) -> tuple[Any, Any]:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir, num_labels=len(config.INTENTS),
                                                               local_files_only=True)
    return model, tok


def main(argv: list[str] | None = None) -> int:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    args = parse_args(sys.argv[1:] if argv is None else argv)
    missing = missing_files(args.model_dir)
    if missing:
        print(f"ERROR: {args.model_dir} thiếu: {', '.join(missing)}", file=sys.stderr)
        return 1
    paths = [args.data_dir / "train.csv", args.data_dir / "val.csv"]
    if not all(p.is_file() for p in paths):
        print("ERROR: thiếu train.csv / val.csv: chạy `python -m nlu.build_dataset` (G18) trước", file=sys.stderr)
        return 1
    train_df, val_df = (pd.read_csv(p) for p in paths)
    hp = HParams(args.lr, args.batch, args.epochs, args.warmup, args.weight_decay, args.patience, args.seed)
    device = pick_device()
    print(f"device={device} train={len(train_df)} val={len(val_df)} {hp}")
    model, tok = _load(args.model_dir)
    try:
        result = train(model, tok, train_df, val_df, hp, device)
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            print(f"ERROR: hết bộ nhớ trên {device}. Thử giảm --batch (vd 8).", file=sys.stderr)
            return 1
        raise
    # Lưu ngay sau lượt 1 (dừng giữa lượt --repeat không làm mất model).
    thr = write_outputs(args.out_dir, model, tok, result, hp, {"device": str(device), "n_train": len(train_df)})
    sections: list[tuple[str, str]] = []
    if args.repeat:
        model2, _ = _load(args.model_dir)
        r2 = train(model2, tok, train_df, val_df, hp, device, log=lambda s: print("[lần 2] " + s))
        diff = float(np.abs(r2["val_probs"] - result["val_probs"]).max())
        same = float((r2["val_probs"].argmax(1) == result["val_probs"].argmax(1)).mean())
        sections.append(("Chạy lại cùng seed", (
            f"Lần 1: macro-F1 val {result['best_val_macro_f1']:.4f} (epoch {result['best_epoch']}); "
            f"lần 2: {r2['best_val_macro_f1']:.4f} (epoch {r2['best_epoch']}). Cùng dự đoán trên {same:.1%} câu val; "
            f"chênh lệch xác suất lớn nhất {diff:.4f}. MPS không bảo đảm tất định tuyệt đối.")))
        del model2
    with (args.out_dir / "train_report.md").open("a", encoding="utf-8") as f:
        for title, body in sections:
            f.write(f"## {title}\n\n{body}\n\n")
    # Kiểm chứng: nạp lại từ out_dir cho cùng kết quả trên val.
    model_re, tok_re = _load(args.out_dir)
    model_re.to(device)
    probs_re = predict_proba(model_re, encode(tok_re, val_df["text_seg"].tolist(), hp.max_len), device)
    same = float((probs_re.argmax(1) == result["val_probs"].argmax(1)).mean())
    diff = float(np.abs(probs_re - result["val_probs"]).max())
    with (args.out_dir / "train_report.md").open("a", encoding="utf-8") as f:
        f.write(f"## Nạp lại từ thư mục đã lưu\n\nCùng dự đoán trên {same:.1%} câu val; chênh lệch xác suất lớn nhất "
                f"{diff:.2e}.\n")
    print(f"saved {args.out_dir} | {json.dumps(thr)} | reload same={same:.1%} maxdiff={diff:.2e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
