# PROJECT DEPLOYMENT GUIDE

## Prerequisites

- Docker Desktop ≥4.x, ≥4GB RAM cho container, Docker Compose v2.
- Python 3.11+; `pip install -r requirements.txt` (pymongo, scylla-driver, hdrhistogram).
- Cho analysis (nhánh Uyên): pandas, numpy, scipy, matplotlib, PyYAML.
- Repo đã checkout `feat/Duy` (+ `feat/Lam` nếu cần chaos_runner/compose đầy đủ, `feat/uyen-analysis-pipeline` nếu cần `src/`).

> Lưu ý merge state: hiện 3 nhánh chưa hợp nhất — lấy file infra từ `feat/Lam`, dataset+analysis từ `feat/uyen-analysis-pipeline`, scripts từ `feat/Duy`. Sau khi team merge về `develop` thì chỉ cần 1 nhánh.

## 1. Environment setup

```bash
cp .env.example .env && cp docker/.env.example docker/.env   # lab config, không secret
docker network create --subnet=10.88.88.0/24 lab-net
```

## 2. Cluster startup

```bash
# ScyllaDB 3 node (3 AZ)  — chon 1 trong 2 bo compose:
docker compose -f docker/scylla.yml up -d      # bo cua Duy (standalone)
# hoac: ./scripts/lab_up.sh scylla             # bo day du cua Lam (feat/Lam, co monitoring)

# MongoDB replica set
docker compose -f docker/mongo.yml up -d
docker exec -it mongo1 mongosh --eval \
 'rs.initiate({_id:"rs0",members:[{_id:0,host:"10.88.88.31:27017"},{_id:1,host:"10.88.88.32:27017"},{_id:2,host:"10.88.88.33:27017"}]})'
```

## 3. Health check (BAT BUOC truoc thi nghiem)

```bash
docker exec scylla-node1 nodetool status     # phai thay 3/3 UN
docker exec mongo1 mongosh --quiet --eval 'rs.status().members.map(m=>m.stateStr)'
```

## 4. Dataset & schema init

```bash
# Dataset chung da co san: data/sample/products.csv (5000 rows, origin=simulated)
# Script tu tao keyspace catalog (NTS datacenter1 RF=3) + table + seed.
# Hoac nap CQL thu cong qua scripts/apply_schema.sh <file.cql> (feat/Lam).
```

## 5. Experiment execution

Chay ben TRONG lab-net (khuyen nghi — dung IP that, khong can translator):

```bash
MSYS_NO_PATHCONV=1 docker run --rm --network lab-net -v "/$(pwd):/app" -w /app \
  python:3.11 bash -c "pip install -q scylla-driver pymongo && \
  SCYLLA_CONTACT_POINTS=10.88.88.11,10.88.88.12,10.88.88.13 \
  python scripts/cap_matrix_e2_e5.py"
```

Hoac chay tu host (fallback LocalAddressTranslator):

```bash
python scripts/e1a_zipf_workload.py --limit 2000     # Schema A replay
python scripts/e1b_bucketing_workload.py --limit 2000 # Schema B replay - CUNG ops
python scripts/cap_matrix_e2_e5.py                   # ONE/QUORUM/ALL + partition
python scripts/lwt_experiment.py && python scripts/counter_experiment.py
python scripts/mongodb_rollback_e6.py                # chay trong lab-net (E6 README)
```

Chaos co dieu phoi (feat/Lam):

```bash
./chaos_runner.py scenarios/e1_hot_partition.json \
  --harness-cmd "python3 scripts/e1a_zipf_workload.py --limit 5000"
# CAP duoi chaos_runner: them --external-chaos --partition-at T1 --heal-at T2
# (T1/T2 phai trung voi timeline scenario)
```

Output: `experiments/<EXP>/<run_id>/{access_log,consistency_log,chaos_events}.csv + manifest.json`.

## 6. Analysis (nhánh Uyên)

```bash
RUN=experiments/E1a_ScyllaDB/<run_id>
python -m src.catalog_analysis.top_partitions --data $RUN --out results/top_partitions
python -m src.catalog_analysis.stale_read    --data <cap_run> --out results/stale_read
python -m src.catalog_analysis.bootstrap_ci  --data $RUN --out results/bootstrap
# Evidence run cu (legacy contract):
python scripts/analyze_committed_runs.py
.venv/bin/python scripts/chart_committed_runs.py
```

## 7. Cleanup

```bash
./scripts/lab_down.sh            # feat/Lam
# hoac: docker compose -f docker/scylla.yml down; docker compose -f docker/mongo.yml down
docker network rm lab-net        # neu can reset hoan toan
```

## 7.5 Tài liệu vận hành liên quan

- Kiến trúc hệ thống: `docs/PROJECT_ARCHITECTURE.md`
- Monitoring/troubleshooting sâu: `docs/PROJECT_MONITORING.md`
- Backup & restore procedure: `docs/PROJECT_BACKUP_RECOVERY.md`
- Security audit: `docs/PROJECT_SECURITY_AUDIT.md`
- CI checks: `.github/workflows/ci.yml` (syntax + contract selftest)

## 8. Troubleshooting

| Trieu chung | Nguyen nhan | Fix |
|---|---|---|
| `NoHostAvailable` ngay khi healthy | node chua UN / translator sai | `nodetool status`; chay trong lab-net voi `SCYLLA_CONTACT_POINTS` |
| CAP_ALL fail 100% | node3 chua rejoin tu run truoc | code da co wait-for-UP; kiem tra `manifest.extra.post_heal_up_nodes` |
| `top_partitions` ra 0 reads/writes | log op khong phai READ/WRITE | run phai sinh tu `data_contract.py` v2 |
| `merge_asof` TypeError | ts la ISO string | contract v2 dung epoch ms |
| `stale_read` 0 events | consistency_log chua chaos markers | chaos events phai o `chaos_events.csv` |
| Port 9042 conflict | ca docker/ va compose/ cung up | chi up 1 bo |
