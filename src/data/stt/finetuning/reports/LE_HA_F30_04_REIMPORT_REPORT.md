# F30_4.zip RE-AUDIT & REIMPORT DECISION REPORT

**Date:** 2026-11-01
**Repository:** `/Users/pickapu/Documents/PyCharmMiscProject/Data-Science-Major-Project`
**Branch:** `quang-manh`
**Source ZIP:** `/Users/pickapu/Downloads/Study/Nữ/F30_4.zip`
**Task:** re-audit the "F30_4 = 70/70 duplicate of F30_01" verdict; import only if content differs.

---

## 1. Re-Audit Verdict

**Kết luận trước đây ĐÚNG.** `F30_4.zip` là bản export trùng hoàn toàn của batch
`F30_01` (speaker `LH_F30_3`). Phát hiện này được xác nhận bằng **ba tầng kiểm chứng
độc lập, tất cả đều ở mức nội dung — không dùng filename làm tiêu chí:**

| Tầng kiểm chứng | Phương pháp | Kết quả |
|---|---|---|
| 1. Raw MD5 | md5 toàn bộ bytes của từng member, so với index md5 của **1.143 raw audio files** trong dataset (filename-agnostic) | **70/70 EXACT DUPLICATE** → tất cả trỏ về `Lê Hà/Nữ 30/F30_01/` |
| 2. Byte equality | so sánh trực tiếp `zip_member_bytes == raw_file_bytes` | `byte_eq=True` — file giống hệt từng byte |
| 3. Decoded PCM | decode member (WebM/Opus 48k) + resample 16kHz mono, so element-wise với raw decode **và** processed WAV | `decoded_eq=True`, `vs_processed_eq=True` |

**Kiểm tra ánh xạ (theo yêu cầu task):**
- 0/70 trường hợp "md5 trùng nhưng tên file khác" — mọi hit đều name-aligned với
  `F30_01/`. Không có so sánh nhầm file cùng tên.
- Cross-batch: **0/70** member của F30_4 khớp `F30_02`, `F30_04` hay `F30_07` —
  duplicate chỉ xảy ra với `F30_01`.
- "Same filename, different content": **0** — mọi file cùng tên đều byte-identical.

## 2. Per-File Audit (mẫu 8/70 — toàn bộ 70 file cùng kết quả)

| member | size | raw MD5 | decoded PCM-MD5 | dur | canonical |
|---|---|---|---|---|---|
| F30_C01_n.wav | 83,386 | `cd5b882a…` | `1ccbbdf4…` | 5.22s | `F30_01/F30_C01_n.wav` |
| F30_C01_r.wav | 81,454 | `d72b3dcf…` | `47bfc9a6…` | 5.10s | `F30_01/F30_C01_r.wav` |
| F30_C02_n.wav | 73,726 | `e1b15fa4…` | `86889750…` | 4.62s | `F30_01/F30_C02_n.wav` |
| F30_C02_r.wav | 65,032 | `2d6dbb27…` | `eba987d9…` | 4.08s | `F30_01/F30_C02_r.wav` |
| F30_C03_n.wav | 80,808 | `fb20777a…` | `5b2165de…` | 5.04s | `F30_01/F30_C03_n.wav` |
| F30_C03_r.wav | 74,046 | `0f3ed898…` | `287c7f7b…` | 4.62s | `F30_01/F30_C03_r.wav` |
| F30_C04_n.wav | 83,386 | `a6845dea…` | `a77b2dcf…` | 5.22s | `F30_01/F30_C04_n.wav` |
| F30_C04_r.wav | 83,386 | `729712f6…` | `22215734…` | 5.22s | `F30_01/F30_C04_r.wav` |

Waveform spot-check (5 file ngẫu nhiên): `F30_T01_r`, `F30_T10_n`, `F30_C05_r`,
`F30_T25_n`, `F30_C10_r` — decoded PCM **element-wise identical** với cả raw
`F30_01` lẫn processed WAV `F30_01`.

## 3. Phân loại

| Loại | Số lượng |
|---|---|
| Tổng audio trong ZIP | 70 (WebM/Opus 48k mislabeled `.wav` + `metadata.json`) |
| Exact duplicate (raw MD5) | **70** |
| Same filename, different content | 0 |
| New recording | **0** |

**Metadata đối chiếu:** F30_4 subject = `id F30, Nữ, 30, Nam, province ""` —
trùng profile `LH_F30_3` (`F30_01`: Nữ 30, Nam, blank). `exportDate` khác nhau
(F30_01: 2026-10-30T07:21Z → F30_4: 2026-11-01T07:15Z) = **cùng session ghi âm,
export lại sau ~24h**. Đây là tái-export của app ghi âm, không phải speaker mới
và không phải recording mới.

## 4. Import Decision

**KHÔNG IMPORT** — điều kiện "audio có nội dung khác dữ liệu hiện tại" không thỏa.
Theo đúng quy tắc dedup của dataset, tạo `F30_08` với 70 audio byte-identical sẽ
vi phạm Data Integrity (duplicate records + duplicate PCM checksums).

Trạng thái hiện có (không thay đổi gì trong task này):

| Artifact | Path | Trạng thái |
|---|---|---|
| Archive ZIP | `data/raw/archives/Lê Hà/Nữ 30/F30_05.zip` | đã có — **byte-identical** với `F30_4.zip` (md5 `5ca4156e…`, sha256 `8c925169…`) |
| Raw dir | `data/raw/real_voice/Lê Hà/Nữ 30/F30_05/` | không tạo (duplicate — canonical là `F30_01/`) |
| Processed dir | `processed/…/F30_05/` | không tạo |
| Provenance | `download_manifest.csv` — 1 zip row + 70 `duplicate_skipped` member rows + 1 metadata row | đã log từ import trước |
| Bản copy thứ 2 | `Nữ (2).zip::Nữ/F30_5.zip` → `archives/…/F30_06.zip` | đã archive (71/72 members = F30_4, chỉ `metadata.json` khác exportDate) |

## 5. Manifests — không thay đổi

| Manifest | Trước | Sau | Δ |
|---|---|---|---|
| `unannotated/metadata.csv` | 956 | 956 | 0 |
| `review_queue.csv` | 1136 | 1136 | 0 |
| `stt_dataset_manifest.csv` | 1143 | 1143 | 0 |
| `download_manifest.csv` | 1628 | 1628 | 0 |

Canonical records của nội dung này đã tồn tại: `LH_F30_3` / `F30_01`
(70 unannotated + 70 review_queue + 70 stt_dataset_manifest).

## 6. Validation

`.venv/bin/python src/data/stt/finetuning/scripts/validate_dataset.py` → **PASS**
(1 pre-existing warning: supervised splits empty — unrelated).

| Check | Kết quả |
|---|---|
| ZIP integrity `F30_4.zip` | OK (`unzip -t`) |
| Source SHA-256 | `8c925169cb08727a…` — khớp archive `F30_05.zip`, không đổi |
| Audio mới import | 0 (đúng — toàn duplicate) |
| Duplicate sample_id | 0 |
| Broken paths | 0 (1,136 rows) |
| Ghi đè dữ liệu cũ | 0 — không file nào được ghi/sửa/xóa |
| Annotation / GT / review status | không đổi |
| Subjects khác | không đổi |

## 7. Directory Tree (không đổi so với trước audit)

```
data/raw/real_voice/Lê Hà/Nữ 30/
├── F30_01/   70 wav + metadata.json   (LH_F30_3 — canonical của nội dung F30_4)
├── F30_02/   70 wav + metadata.json   (LH_F30_2)
├── F30_04/   70 wav + metadata.json   (LH_F30_4)
└── F30_07/   70 wav + metadata.json   (LH_F30_5)

data/raw/archives/Lê Hà/Nữ 30/
├── F30_01.zip  F30_02.zip  F30_04.zip
├── F30_05.zip  ← F30_4.zip (duplicate export, archive-only)
├── F30_06.zip  ← Nữ (2).zip::Nữ/F30_5.zip (duplicate export, archive-only)
└── F30_07.zip

src/data/stt/processed/real_voice/wav/Lê Hà/Nữ 30/
├── F30_01/  F30_02/  F30_04/  F30_07/   (70 wav each)
```

## 8. Kết luận

- Verdict "F30_4 duplicate of F30_01" **được tái xác nhận ở mức byte + PCM**, không
  chỉ filename hay metadata: 70/70 file giống hệt từng byte với `LH_F30_3`/`F30_01`.
- **0 audio mới → 0 records tạo thêm.** Batch `F30_08` không được tạo vì không có
  nội dung mới — tạo nó sẽ vi phạm nguyên tắc no-duplicate của dataset.
- Nếu thực tế có một bản ghi U30 khác cần import (ví dụ export mới hơn của app với
  audio thật sự khác), cần file ZIP khác — `F30_4.zip` hiện tại chắc chắn là
  re-export của `F30_01`.
