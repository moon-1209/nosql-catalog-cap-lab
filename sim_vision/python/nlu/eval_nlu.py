"""So sánh NLU luật (G14) và PhoBERT (G20) trên tập test (G23). Chỉ đọc tập test; không train, không chỉnh ngưỡng.

Chạy: python -m nlu.eval_nlu ➔ reports/nlu_compare.md, reports/nlu_compare.csv, reports/nlu_f1_vs_snr.png
- test_ref.csv (chữ chuẩn), test_stt.csv (kết quả STT G13) tách theo SNR, khoảng cách, loại ồn.
- accuracy, macro-F1 [KTC 95% bootstrap theo câu], F1 từng lớp, recall cap_cuu (+ câu bỏ sót), tỉ lệ clarify,
  độ trễ NLU trung bình và p95; McNemar giữa hai cách trên cùng tập câu.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from nlu import config
from nlu.nlu import IntentResult, Nlu

BOOTSTRAP_N: int = 1000
MODES: tuple[str, ...] = ("rule", "phobert")
COLORS: dict[str, str] = {"rule": "#2a78d6", "phobert": "#eb6834"}     # dataviz: slot 1, 2 (đã kiểm định)
LABELS: dict[str, str] = {"rule": "Luật (G14)", "phobert": "PhoBERT (G20)"}


def run(understand: Callable[[str], IntentResult], texts: list[str], threshold: float) -> pd.DataFrame:
    rows = []
    for t in texts:
        t0 = time.perf_counter()
        r = understand(t if isinstance(t, str) else "")
        ms = (time.perf_counter() - t0) * 1000.0
        rows.append({"pred": r.intent, "conf": r.intent_conf, "source": r.source, "nlu_ms": ms,
                     "clarify": r.intent != "cap_cuu" and r.intent_conf < threshold})
    return pd.DataFrame(rows)


def macro_f1(y: pd.Series, p: pd.Series) -> float:
    return float(f1_score(y, p, average="macro", labels=sorted(set(y)), zero_division=0))


def bootstrap_f1(y: np.ndarray, p: np.ndarray, n: int = BOOTSTRAP_N, seed: int = config.SEED) -> tuple[float, float]:
    if len(y) == 0:
        return float("nan"), float("nan")
    idx = np.random.default_rng(seed).integers(0, len(y), size=(n, len(y)))
    vals = [macro_f1(pd.Series(y[i]), pd.Series(p[i])) for i in idx]
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def mcnemar_test(ok_a: np.ndarray, ok_b: np.ndarray) -> dict[str, float]:
    """b = A đúng B sai, c = A sai B đúng. Exact (nhị thức) khi b + c < 25, không thì chi-square có hiệu chỉnh."""
    from statsmodels.stats.contingency_tables import mcnemar

    b = int((ok_a & ~ok_b).sum())
    c = int((~ok_a & ok_b).sum())
    if b + c == 0:
        return {"b": b, "c": c, "p": 1.0}
    res = mcnemar([[0, b], [c, 0]], exact=b + c < 25, correction=True)
    return {"b": b, "c": c, "p": float(res.pvalue)}


def metrics(df: pd.DataFrame, mode: str, with_ci: bool = True) -> dict[str, float]:
    y, p = df["intent"], df[f"{mode}_pred"]
    cc = df[df["intent"] == "cap_cuu"]
    out = {"n": len(df), "accuracy": float((y == p).mean()) if len(df) else float("nan"),
           "macro_f1": macro_f1(y, p) if len(df) else float("nan"),
           "recall_cap_cuu": float((cc[f"{mode}_pred"] == "cap_cuu").mean()) if len(cc) else float("nan"),
           "n_cap_cuu": len(cc), "clarify_rate": float(df[f"{mode}_clarify"].mean()) if len(df) else float("nan"),
           "nlu_ms_mean": float(df[f"{mode}_ms"].mean()), "nlu_ms_p95": float(df[f"{mode}_ms"].quantile(0.95))}
    if with_ci:
        out["f1_lo"], out["f1_hi"] = bootstrap_f1(y.to_numpy(), p.to_numpy())
    return out


def per_class(df: pd.DataFrame) -> pd.DataFrame:
    labels = sorted(set(df["intent"]))
    out = {"intent": labels, "n": [int((df["intent"] == lb).sum()) for lb in labels]}
    for m in MODES:
        out[m] = f1_score(df["intent"], df[f"{m}_pred"], average=None, labels=labels, zero_division=0)
    return pd.DataFrame(out)


def condition(df: pd.DataFrame) -> pd.Series:
    """Nhóm SNR: noise "none" ➔ "sạch" (SNR placeholder 30 không có nghĩa)."""
    return np.where(df["noise"] == "none", "sạch", df["snr_db"].map(lambda v: f"{v:g} dB"))


def plot(stt: pd.DataFrame, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    noisy = stt[stt["noise"] != "none"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for m in MODES:
        pts = noisy.groupby("snr_db").apply(lambda g: macro_f1(g["intent"], g[f"{m}_pred"]),
                                            include_groups=False).sort_index()
        ax.plot(pts.index, pts.values, marker="o", markersize=8, linewidth=2, color=COLORS[m], label=LABELS[m])
        ax.annotate(LABELS[m], (pts.index[0], pts.values[0]), xytext=(6, 0), textcoords="offset points",
                    va="center", fontsize=9, color="#333333")
        clean = stt[stt["noise"] == "none"]
        ax.axhline(macro_f1(clean["intent"], clean[f"{m}_pred"]), ls="--", lw=1, color=COLORS[m], alpha=0.6)
    ax.set(xlabel="SNR tại 1 m (dB) — nét đứt: không ồn", ylabel="Macro-F1",
           title="Macro-F1 intent trên kết quả STT theo SNR (babble + white, mọi khoảng cách)")
    ax.invert_xaxis()
    ax.grid(alpha=0.25, linewidth=0.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _pct(v: float) -> str:
    return "—" if v != v else f"{v:.1%}"


def summary_row(name: str, m: dict[str, float], mode: str) -> str:
    return (f"| {name} | {LABELS[mode]} | {m['n']} | {_pct(m['accuracy'])} | {m['macro_f1']:.3f} "
            f"[{m['f1_lo']:.3f}, {m['f1_hi']:.3f}] | {_pct(m['recall_cap_cuu'])} ({m['n_cap_cuu']}) | "
            f"{_pct(m['clarify_rate'])} | {m['nlu_ms_mean']:.1f} | {m['nlu_ms_p95']:.1f} |")


def group_table(stt: pd.DataFrame, key: pd.Series, title: str) -> list[str]:
    lines = [f"### Theo {title}", "", f"| {title} | n | Acc luật | Acc PhoBERT | F1 luật | F1 PhoBERT | "
             "Recall cap_cuu luật | Recall cap_cuu PhoBERT | McNemar b/c, p |", "| :-- |" + " --: |" * 8]
    for k, g in stt.groupby(key, sort=True):
        r, p = metrics(g, "rule", False), metrics(g, "phobert", False)
        mc = mcnemar_test(g["rule_ok"].to_numpy(), g["phobert_ok"].to_numpy())
        lines.append(f"| {k} | {len(g)} | {_pct(r['accuracy'])} | {_pct(p['accuracy'])} | {r['macro_f1']:.3f} | "
                     f"{p['macro_f1']:.3f} | {_pct(r['recall_cap_cuu'])} | {_pct(p['recall_cap_cuu'])} | "
                     f"{mc['b']}/{mc['c']}, {mc['p']:.3g} |")
    return lines + [""]


def evaluate(sets: dict[str, pd.DataFrame], engines: dict[str, tuple[Callable[[str], IntentResult], float]]
             ) -> dict[str, pd.DataFrame]:
    out = {}
    for name, df in sets.items():
        d = df.copy()
        for m, (fn, thr) in engines.items():
            r = run(fn, d["text"].tolist(), thr)
            d[f"{m}_pred"], d[f"{m}_conf"] = r["pred"].to_numpy(), r["conf"].to_numpy()
            d[f"{m}_source"], d[f"{m}_ms"], d[f"{m}_clarify"] = r["source"].to_numpy(), r["nlu_ms"].to_numpy(), \
                r["clarify"].to_numpy()
            d[f"{m}_ok"] = d[f"{m}_pred"] == d["intent"]
        out[name] = d
    return out


def render(res: dict[str, pd.DataFrame], thresholds: dict[str, float], plot_name: str | None) -> str:
    lines = ["# So sánh NLU: luật (G14) và PhoBERT (G20) (G23)", "",
             f"Ngưỡng tin cậy: luật {thresholds['rule']}, PhoBERT {thresholds['phobert']} (chọn trên val ở G19). "
             "Cả hai cách chạy luật khẩn cấp (cap_cuu của G14) trước. Bootstrap theo câu "
             f"{BOOTSTRAP_N} lần; McNemar exact khi b + c < 25.", "",
             "> **Hạn chế:** tập test chỉ có giọng A (1 người nói nam, 20 tuổi; giọng B chưa thu); câu train là câu "
             "sinh ra từ mẫu, không phải hội thoại bệnh viện thật; luật G14 được viết dựa trên chính câu kịch bản "
             "nên điểm của luật trên `test_ref` cao hơn thực tế. Ba intent `dieu_chinh_am_luong`, `nhac_lai`, "
             "`unknown` chưa có câu test.", "",
             "## Tổng hợp", "",
             "| Tập | Cách | n | Accuracy | Macro-F1 [KTC 95%] | Recall cap_cuu (n) | Tỉ lệ clarify | NLU ms TB | p95 NLU ms |",
             "| :-- | :-- | --: | --: | :-- | :-- | --: | --: | --: |"]
    for name, d in res.items():
        for m in MODES:
            lines.append(summary_row(name, metrics(d, m), m))
    lines += ["", "## McNemar (cùng tập câu)", "", "b = luật đúng, PhoBERT sai; c = luật sai, PhoBERT đúng.", "",
              "| Tập | n (luật = PhoBERT) | b | c | p |", "| :-- | --: | --: | --: | --: |"]
    for name, d in res.items():
        mc = mcnemar_test(d["rule_ok"].to_numpy(), d["phobert_ok"].to_numpy())
        lines.append(f"| {name} | {len(d)} | {mc['b']} | {mc['c']} | {mc['p']:.3g} |")
    stt = res.get("test_stt")
    if stt is not None:
        lines += ["", "## test_stt theo điều kiện", ""]
        lines += group_table(stt, pd.Series(condition(stt), index=stt.index), "SNR")
        lines += group_table(stt, stt["distance_m"].map(lambda v: f"{v:g} m"), "khoảng cách")
        lines += group_table(stt, stt["noise"], "loại ồn")
        if plot_name:
            lines += [f"![Macro-F1 theo SNR]({plot_name})", ""]
    for name, d in res.items():
        pc = per_class(d)
        lines += [f"## F1 từng lớp: {name}", "", "| intent | n | F1 luật | F1 PhoBERT |", "| :-- | --: | --: | --: |"]
        lines += [f"| {r.intent} | {r.n} | {r.rule:.3f} | {r.phobert:.3f} |" for r in pc.itertuples()] + [""]
    lines += ["## Câu cap_cuu bị bỏ sót", ""]
    for name, d in res.items():
        cc = d[d["intent"] == "cap_cuu"]
        for m in MODES:
            miss = cc[cc[f"{m}_pred"] != "cap_cuu"]
            lines.append(f"**{name}, {LABELS[m]}**: {len(miss)}/{len(cc)} bỏ sót.")
            extra = ["distance_m", "snr_db", "noise"] if "noise" in d else []
            for r in miss.itertuples():
                cond = f" ({r.noise}, {r.snr_db:g} dB, {r.distance_m:g} m)" if extra else ""
                lines.append(f"- `{r.clip_id}`{cond}: \"{r.text}\" ➔ {getattr(r, f'{m}_pred')} "
                             f"({getattr(r, f'{m}_conf'):.2f})")
            lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Compare rule and PhoBERT NLU on test sets (G23)")
    p.add_argument("--data-dir", type=Path, default=config.NLU_DATA_DIR)
    p.add_argument("--out-dir", type=Path, default=config.REPORTS_DIR)
    args = p.parse_args(sys.argv[1:] if argv is None else argv)
    sets = {n: pd.read_csv(args.data_dir / f"{n}.csv") for n in ("test_ref", "test_stt")}
    from nlu.phobert_intent import PhoBertIntent
    from nlu.segment import segment

    model = PhoBertIntent()
    engines = {"rule": (Nlu("rule").understand, config.CONF_THRESHOLD_DEFAULT),
               "phobert": (Nlu("phobert", model, segment).understand, model.threshold)}
    for t in ("xin chào", "khoa tim mạch ở đâu"):                    # khởi động JVM / MPS trước khi đo
        for fn, _ in engines.values():
            fn(t)
    res = evaluate(sets, engines)
    assert all(len(d) == len(sets[n]) for n, d in res.items())       # cùng số câu cho hai cách
    plot(res["test_stt"], args.out_dir / "nlu_f1_vs_snr.png")
    pd.concat([d.assign(set=n) for n, d in res.items()]).to_csv(args.out_dir / "nlu_compare.csv", index=False)
    (args.out_dir / "nlu_compare.md").write_text(
        render(res, {m: thr for m, (_, thr) in engines.items()}, "nlu_f1_vs_snr.png"), encoding="utf-8")
    print(f"wrote {args.out_dir / 'nlu_compare.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
