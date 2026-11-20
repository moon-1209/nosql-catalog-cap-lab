"""PhoBERT đã fine-tune (G19) ➔ xác suất intent (G20). Nạp một lần, suy luận trong torch.inference_mode()."""

from __future__ import annotations

import json
import os
from pathlib import Path

import torch

from nlu import config


def load_threshold(model_dir: Path = config.PHOBERT_FT_DIR) -> float:
    path = model_dir / "threshold.json"
    if not path.is_file():
        return config.CONF_THRESHOLD_DEFAULT
    return float(json.loads(path.read_text(encoding="utf-8"))["conf_threshold"])


class PhoBertIntent:
    def __init__(self, model_dir: Path = config.PHOBERT_FT_DIR, device: str = "auto") -> None:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        label_map = json.loads((model_dir / "label_map.json").read_text(encoding="utf-8"))
        self.labels: list[str] = [name for name, _ in sorted(label_map.items(), key=lambda kv: kv[1])]
        if tuple(self.labels) != config.INTENTS:
            raise ValueError(f"{model_dir}/label_map.json khác tập intent Mục 2.2")
        if device == "auto":
            device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.device = torch.device(device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir, local_files_only=True)
        self.model.to(self.device).eval()
        self.threshold: float = load_threshold(model_dir)
        self.predict("xin chào")                                # khởi động (lần đầu trên MPS chậm)

    @torch.inference_mode()
    def predict(self, text_seg: str) -> list[tuple[str, float]]:
        enc = self.tokenizer([text_seg], max_length=config.MAX_SEQ_LEN, truncation=True, return_tensors="pt")
        logits = self.model(input_ids=enc["input_ids"].to(self.device),
                            attention_mask=enc["attention_mask"].to(self.device)).logits
        probs = torch.softmax(logits.float(), dim=-1)[0].cpu().tolist()
        return sorted(zip(self.labels, probs), key=lambda kv: -kv[1])
