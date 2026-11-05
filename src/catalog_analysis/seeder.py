"""Deterministic catalog data seeder for the CAP lab experiments.

Generates, from a YAML config + random seed:

  products.csv        - catalog rows matching Schema A/B payload columns
                        (category_id + bucket + clustering columns)
  access_log.csv      - SIMULATED request stream (READ/WRITE per category)
                        for hot-partition analysis
  consistency_log.csv - SIMULATED read/write version events on hot keys
                        for stale-read analysis
  manifest.json       - seed, config snapshot, row counts, origin label

Reproducible: identical config + seed => byte-identical CSVs.

CLI:
  python -m src.catalog_analysis.seeder \
      --config config/seeder.yaml --records 5000 --requests 20000 \
      --seed 42 --out data/sample
"""

from __future__ import annotations

import argparse
import binascii
import json
import time
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
BASE_TS = np.datetime64("2026-01-01T00:00:00").astype("datetime64[ms]").astype(np.int64)
SPAN_MS = np.int64(30 * 24 * 3600 * 1000)  # 30 days in milliseconds

ADJ = ["Aero", "Novo", "Prime", "Ultra", "Eco", "Pro", "Flex", "Omni", "Neo", "Max"]
NOUN = ["Hub", "Kit", "Set", "Pro", "Lite", "Plus", "Go", "Box", "One", "X"]
THING = ["Speaker", "Jacket", "Blender", "Racket", "Drone", "Novel", "Serum",
         "Filter", "Snack", "Toy", "Cable", "Desk", "Ring", "Vitamin", "Bottle",
         "Drill", "Console", "Tent", "Purifier", "Watch"]
COLORS = ["black", "white", "red", "blue", "green", "silver", "gold"]
SIZES = ["XS", "S", "M", "L", "XL", "one-size"]


def zipf_weights(n: int, alpha: float, rng: np.random.Generator) -> np.ndarray:
    """Normalised Zipf probabilities over n items, rank order shuffled."""
    w = 1.0 / np.power(np.arange(1, n + 1, dtype=np.float64), alpha)
    w /= w.sum()
    return w[rng.permutation(n)]


def product_id_for(seed: int, idx: int) -> str:
    return str(uuid.uuid5(NAMESPACE, f"catalog-seed{seed}-product{idx}"))


def gen_products(cfg: dict, rng: np.random.Generator) -> pd.DataFrame:
    n = cfg["records"]
    cats = np.array(cfg["categories"])
    weights = zipf_weights(len(cats), cfg["category_zipf_alpha"], rng)
    cat_idx = rng.choice(len(cats), size=n, p=weights)
    category_id = cats[cat_idx]

    product_ids = np.array([product_id_for(cfg["seed"], i) for i in range(n)])
    bucket = np.array(
        [binascii.crc32(p.encode()) % cfg["num_buckets"] for p in product_ids],
        dtype=np.int32,
    )
    added_at = BASE_TS + rng.integers(0, SPAN_MS, size=n, dtype=np.int64)
    brand = np.array([f"brand-{i:03d}" for i in range(cfg["brands"])])[
        rng.integers(0, cfg["brands"], size=n)
    ]
    name = np.array([
        f"{ADJ[i % len(ADJ)]} {THING[(i * 7) % len(THING)]} {NOUN[(i * 13) % len(NOUN)]}"
        for i in rng.integers(0, 10_000, size=n)
    ])
    price = np.round(rng.uniform(cfg["price"]["min"], cfg["price"]["max"], n), 2)
    stock = rng.integers(0, cfg["stock"]["max"] + 1, size=n, dtype=np.int32)
    rating = np.round(rng.uniform(1.0, 5.0, n), 1)
    attributes = np.array([
        json.dumps({"color": COLORS[i % len(COLORS)], "size": SIZES[i % len(SIZES)]})
        for i in rng.integers(0, 100, size=n)
    ])

    return pd.DataFrame({
        "category_id": category_id,
        "bucket": bucket,
        "added_at": added_at,
        "product_id": product_ids,
        "name": name,
        "brand": brand,
        "price": price,
        "currency": "USD",
        "stock": stock,
        "rating": rating,
        "attributes": attributes,
    })


def gen_access_log(cfg: dict, products: pd.DataFrame,
                   rng: np.random.Generator) -> pd.DataFrame:
    """Simulated request stream routed by Zipf over categories."""
    n = cfg["requests"]
    cats = np.array(cfg["categories"])
    weights = zipf_weights(len(cats), cfg["access_zipf_alpha"], rng)
    cat_idx = rng.choice(len(cats), size=n, p=weights)

    ids_by_cat = products.groupby("category_id")["product_id"].apply(np.array)
    product_ids = np.empty(n, dtype=object)
    for c, arr in ids_by_cat.items():
        mask = cats[cat_idx] == c
        product_ids[mask] = arr[rng.integers(0, len(arr), size=int(mask.sum()))]

    ops = np.where(rng.random(n) < cfg["read_ratio"], "READ", "WRITE")
    ts = BASE_TS + np.sort(rng.integers(0, SPAN_MS, size=n, dtype=np.int64))
    latency = np.round(rng.lognormal(mean=np.log(8.0), sigma=0.5, size=n), 3)

    return pd.DataFrame({
        "ts": ts,
        "request_id": [f"req-{i:07d}" for i in range(n)],
        "op": ops,
        "category_id": cats[cat_idx],
        "product_id": product_ids,
        "latency_ms": latency,
    })


def gen_consistency_log(cfg: dict, products: pd.DataFrame,
                        rng: np.random.Generator) -> pd.DataFrame:
    """Simulated write/read version events on hot keys.

    Each WRITE commits a new version; each READ returns some committed
    version.  Staleness is *derived* downstream by comparing the returned
    version to the latest write committed before the read timestamp.
    """
    c = cfg["consistency"]
    n = cfg["consistency_events"]
    keys = products["product_id"].sample(
        n=min(c["hot_keys"], len(products)), random_state=cfg["seed"]
    ).to_numpy()
    nodes = np.array(c["nodes"])
    p_node = c["partition_node"]

    ts = BASE_TS + np.sort(rng.integers(0, SPAN_MS, size=n, dtype=np.int64))
    p_start = BASE_TS + int(SPAN_MS * c["partition_start_frac"])
    p_end = p_start + int(SPAN_MS * c["partition_duration_frac"])

    key_weights = zipf_weights(len(keys), 1.1, rng)
    versions: dict[str, int] = {}
    rows = []
    for i in range(n):
        key = keys[rng.choice(len(keys), p=key_weights)]
        node = nodes[rng.integers(0, len(nodes))]
        level = c["levels"][rng.integers(0, len(c["levels"]))]
        t = int(ts[i])
        partitioned = p_start <= t < p_end
        state = "PARTITIONED" if partitioned else "NORMAL"

        if rng.random() < 0.35 or versions.get(key, 0) == 0:
            versions[key] = versions.get(key, 0) + 1
            rows.append((t, "WRITE", key, versions[key], level, node, state))
            continue

        latest = versions[key]
        probs = c["stale_probability"][level]
        p = probs["on_partition_node"] if (partitioned and node == p_node) else (
            probs["partitioned"] if partitioned else probs["normal"])
        returned = rng.integers(1, latest) if (latest > 1 and rng.random() < p) else latest
        rows.append((t, "READ", key, returned, level, node, state))

    return pd.DataFrame(
        rows, columns=["ts", "event", "key", "version",
                       "consistency_level", "node", "network_state"]
    )


def validate(products: pd.DataFrame, cfg: dict) -> list[str]:
    problems = []
    if products["product_id"].duplicated().any():
        problems.append("duplicate product_id values")
    pk = products[["category_id", "added_at", "product_id"]]
    if pk.duplicated().any():
        problems.append("duplicate Schema-A primary keys")
    pkb = products[["category_id", "bucket", "added_at", "product_id"]]
    if pkb.duplicated().any():
        problems.append("duplicate Schema-B primary keys")
    expected = products["product_id"].map(
        lambda p: binascii.crc32(p.encode()) % cfg["num_buckets"])
    if not bool((expected.to_numpy() == products["bucket"].to_numpy()).all()):
        problems.append("bucket column inconsistent with hash(product_id)")
    if not products["category_id"].isin(cfg["categories"]).all():
        problems.append("category_id outside configured category list")
    return problems


def seed(cfg: dict, out_dir: Path) -> dict:
    rng = np.random.default_rng(cfg["seed"])
    t0 = time.time()
    products = gen_products(cfg, rng)
    access = gen_access_log(cfg, products, rng)
    consistency = gen_consistency_log(cfg, products, rng)

    problems = validate(products, cfg)
    if problems:
        raise ValueError("seeder validation failed: " + "; ".join(problems))

    out_dir.mkdir(parents=True, exist_ok=True)
    products.to_csv(out_dir / "products.csv", index=False)
    access.to_csv(out_dir / "access_log.csv", index=False)
    consistency.to_csv(out_dir / "consistency_log.csv", index=False)

    shares = products["category_id"].value_counts(normalize=True)
    manifest = {
        "origin": "simulated",
        "seed": cfg["seed"],
        "config": cfg,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rows": {
            "products": len(products),
            "access_log": len(access),
            "consistency_log": len(consistency),
        },
        "top_category_share": float(shares.iloc[0]),
        "top_category": str(shares.index[0]),
        "validation": "passed",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    manifest["elapsed_s"] = round(time.time() - t0, 2)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/seeder.yaml")
    ap.add_argument("--out", default="data/full")
    ap.add_argument("--records", type=int, help="override products count")
    ap.add_argument("--requests", type=int, help="override access_log events")
    ap.add_argument("--seed", type=int, help="override random seed")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())
    for key in ("records", "requests", "seed"):
        if getattr(args, key) is not None:
            cfg[key] = getattr(args, key)

    manifest = seed(cfg, Path(args.out))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
