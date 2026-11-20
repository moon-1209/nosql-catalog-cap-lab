"""Download CC0 1K glTF hospital, laboratory, clinic & interior 3D models from Poly Haven.

Downloads each model's 1k .gltf, .bin, and textures/ into
sim_vision/godot/assets/models/<asset_id>/ matching existing CREDITS.md conventions.
"""

from __future__ import annotations

import json
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "sim_vision" / "godot" / "assets" / "models"
HEADERS = {"User-Agent": "RoboHelperHospital/1.0"}

DEPRECATED_ASSETS = [
    "metal_trash_can",
]

ASSET_IDS = [
    "plastic_monobloc_chair_01",
    "metal_stool_01",
    "medical_box",
    "medical_tape",
    "WetFloorSign_01",
    "Shelf_01",
    "steel_frame_shelves_01",
    "steel_frame_shelves_02",
    "drawer_cabinet",
    "wall_clock",
    "chemistry_set",
    "industrial_microscope",
    "clipboard",
    "office_notepads",
    "stationery_supplies",
    "fire_alarm",
    "security_camera_01",
    "ceiling_fan",
]


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 0:
        return
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as resp:
        dest.write_bytes(resp.read())


def download_asset(asset_id: str) -> dict:
    info = fetch_json(f"https://api.polyhaven.com/info/{asset_id}")
    files = fetch_json(f"https://api.polyhaven.com/files/{asset_id}")
    gltf_entry = files["gltf"]["1k"]["gltf"]

    target_dir = MODELS_DIR / asset_id
    target_dir.mkdir(parents=True, exist_ok=True)

    gltf_filename = f"{asset_id}_1k.gltf"
    download_file(gltf_entry["url"], target_dir / gltf_filename)

    for rel_path, meta in gltf_entry.get("include", {}).items():
        download_file(meta["url"], target_dir / rel_path)

    authors = ", ".join(info.get("authors", {}).keys())
    print(f"[OK] {asset_id} ({info.get('name', asset_id)}) — Authors: {authors}")
    return {
        "id": asset_id,
        "name": info.get("name", asset_id),
        "authors": authors,
        "url": f"https://polyhaven.com/a/{asset_id}",
    }


def main() -> None:
    for dep in DEPRECATED_ASSETS:
        dep_dir = MODELS_DIR / dep
        if dep_dir.exists():
            shutil.rmtree(dep_dir)
            print(f"[REMOVED] Deprecated model directory: {dep_dir}")

    print(f"Downloading {len(ASSET_IDS)} CC0 1K glTF models to {MODELS_DIR}...")
    results = []
    for aid in ASSET_IDS:
        results.append(download_asset(aid))
    print("\nAll models downloaded successfully!")
    for r in results:
        print(
            f"| {r['name']} | {r['url']} | {r['authors']} | CC0 1.0 | `models/{r['id']}/` |"
        )


if __name__ == "__main__":
    main()
