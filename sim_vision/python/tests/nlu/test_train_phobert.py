from __future__ import annotations

import json
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch
from transformers import RobertaConfig, RobertaForSequenceClassification

from nlu import config, train_phobert as tp


class TinyTokenizer:
    """Thay PhoBERT tokenizer: mỗi từ ➔ id ổn định trong [3, 100)."""

    saved_to: Path | None = None

    def __call__(self, texts: list[str], max_length: int, truncation: bool, padding: str,
                 return_tensors: str) -> dict[str, torch.Tensor]:
        ids = torch.ones((len(texts), max_length), dtype=torch.long)        # 1 = <pad>
        mask = torch.zeros_like(ids)
        for r, t in enumerate(texts):
            toks = [0] + [3 + zlib.crc32(w.encode()) % 97 for w in t.split()][:max_length - 2] + [2]
            ids[r, :len(toks)] = torch.tensor(toks)
            mask[r, :len(toks)] = 1
        return {"input_ids": ids, "attention_mask": mask}

    def save_pretrained(self, path: Path) -> None:
        self.saved_to = Path(path)
        (Path(path) / "tokenizer_stub.txt").write_text("tiny", encoding="utf-8")


def tiny_model() -> RobertaForSequenceClassification:
    torch.manual_seed(0)
    cfg = RobertaConfig(vocab_size=100, hidden_size=16, num_hidden_layers=1, num_attention_heads=2,
                        intermediate_size=32, max_position_embeddings=80, num_labels=len(config.INTENTS),
                        pad_token_id=1)
    return RobertaForSequenceClassification(cfg)


def fake_data(n_per: int, intents: tuple[str, ...]) -> pd.DataFrame:
    rows = [{"text_seg": f"{it} câu số {i}", "intent": it} for it in intents for i in range(n_per)]
    return pd.DataFrame(rows)


def test_pipeline_on_40_fake_sentences(tmp_path: Path) -> None:
    intents = ("cam_on", "hoi_khoa", "nha_thuoc", "unknown")
    train_df, val_df = fake_data(10, intents), fake_data(3, intents)
    hp = tp.HParams(lr=5e-3, batch=8, epochs=3, patience=5, max_len=16)
    model, tok = tiny_model(), TinyTokenizer()
    logs: list[str] = []
    result = tp.train(model, tok, train_df, val_df, hp, torch.device("cpu"), log=logs.append)
    assert len(result["history"]) == 3 and logs[0].startswith("epoch 1 | train_loss ")
    assert result["val_probs"].shape == (12, len(config.INTENTS))
    np.testing.assert_allclose(result["val_probs"].sum(1), 1.0, atol=1e-5)
    thr = tp.write_outputs(tmp_path, model, tok, result, hp, {"device": "cpu", "n_train": 40})
    assert 0.3 <= thr["conf_threshold"] <= 0.9
    assert json.loads((tmp_path / "label_map.json").read_text())["unknown"] == config.INTENTS.index("unknown")
    assert json.loads((tmp_path / "threshold.json").read_text()) == thr
    assert (tmp_path / "config.json").is_file() and tok.saved_to == tmp_path
    report = (tmp_path / "train_report.md").read_text()
    assert "Ma trận nhầm lẫn" in report and "| lr | 0.005 |" in report


def test_early_stopping_keeps_best_epoch() -> None:
    intents = ("cam_on", "unknown")
    hp = tp.HParams(lr=0.0, batch=8, epochs=10, patience=2, max_len=8)       # lr 0 ➔ không cải thiện
    result = tp.train(tiny_model(), TinyTokenizer(), fake_data(8, intents), fake_data(2, intents), hp,
                      torch.device("cpu"), log=lambda s: None)
    assert len(result["history"]) == 3 and result["best_epoch"] == 1


def test_same_seed_same_result() -> None:
    intents = ("cam_on", "hoi_khoa", "unknown")
    hp = tp.HParams(lr=5e-3, batch=4, epochs=2, max_len=8)
    runs = [tp.train(tiny_model(), TinyTokenizer(), fake_data(6, intents), fake_data(2, intents), hp,
                     torch.device("cpu"), log=lambda s: None)["val_probs"] for _ in range(2)]
    np.testing.assert_allclose(runs[0], runs[1], atol=1e-6)


def test_improved_breaks_ties_with_val_loss() -> None:
    assert tp.improved(0.9, 5.0, 0.8, 0.1)
    assert tp.improved(1.0, 0.2, 1.0, 0.3) and not tp.improved(1.0, 0.3, 1.0, 0.2)
    assert not tp.improved(0.8, 0.0, 0.9, 1.0)


def test_threshold_maps_low_confidence_to_unknown() -> None:
    probs = np.array([[0.9, 0.05, 0.05], [0.4, 0.35, 0.25], [0.2, 0.7, 0.1]])
    assert tp.apply_threshold(probs, 0.5, unknown_idx=2).tolist() == [0, 2, 1]


def test_choose_threshold_prefers_value_near_start() -> None:
    probs = np.array([[0.95, 0.03, 0.02], [0.02, 0.96, 0.02], [0.4, 0.35, 0.25]])
    y = np.array([0, 1, 2])                            # câu thứ 3 thật ra là unknown
    thr, f1, curve = tp.choose_threshold(probs, y, unknown_idx=2)
    assert f1 == 1.0 and thr == 0.6                    # mọi ngưỡng 0.45–0.90 đều đúng hết ➔ gần 0.6 nhất
    assert [t for t, _ in curve][0] == 0.3 and [t for t, _ in curve][-1] == 0.9 and len(curve) == 13


def test_missing_files_reported(tmp_path: Path) -> None:
    (tmp_path / "config.json").write_text("{}")
    assert tp.missing_files(tmp_path) == ["vocab.txt", "bpe.codes", "pytorch_model.bin hoặc model.safetensors"]


def test_main_stops_when_model_files_missing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert tp.main(["--model-dir", str(tmp_path), "--data-dir", str(tmp_path)]) == 1
    assert "thiếu" in capsys.readouterr().err


def test_label_map_alphabetical_20_classes() -> None:
    lm = tp.label_map()
    assert list(lm) == sorted(lm) and len(lm) == 20 and "ho_tro_di_chuyen" in lm
