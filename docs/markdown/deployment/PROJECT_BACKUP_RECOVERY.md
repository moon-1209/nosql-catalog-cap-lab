# BACKUP & RECOVERY

> Trạng thái: **PROCEDURE DOCUMENTED — RUNTIME VERIFICATION BLOCKED** (máy audit không có Docker).
> Failover (E6) KHÔNG được tính là backup/recovery — đây là hai yêu cầu khác nhau.

## 1. Cần backup những gì

| Data | Vì sao | Volume |
|---|---|---|
| `catalog.*` ScyllaDB | dataset + experiment state | `scylla-node{1,2,3}-data` |
| `benchmark_db.*` MongoDB | E6 state | `mongo{1,2,3}-data` |
| `experiments/` run artifacts | evidence — đã trong git | n/a |
| `data/sample/` | dataset chung — đã trong git | n/a |

## 2. Procedure đề xuất (chưa verify runtime)

### ScyllaDB — nodetool snapshot

```bash
# 1. Snapshot đồng nhất trên cả 3 node (keyspace catalog)
for n in scylla-node1 scylla-node2 scylla-node3; do
  docker exec $n nodetool snapshot catalog --tag backup_$(date +%Y%m%d)
done

# 2. Copy snapshot ra host
mkdir -p backups/scylla/$(date +%Y%m%d)
for n in scylla-node1 scylla-node2 scylla-node3; do
  docker cp $n:/var/lib/scylla/data/catalog \
    backups/scylla/$(date +%Y%m%d)/$n
done

# 3. Restore (isolated test): dựng cụm mới, tạo schema, sstableloader hoặc
#    copy snapshot vào data dir + nodetool refresh
# 4. Verify: SELECT COUNT(*) FROM catalog.products_by_category
#    so với count ghi lại trong manifest trước backup
```

### MongoDB — mongodump / mongorestore

```bash
docker exec mongo1 mongodump --db benchmark_db --out /tmp/backup
docker cp mongo1:/tmp/backup backups/mongo/$(date +%Y%m%d)
# Restore test: docker exec mongo1 mongorestore --db benchmark_db_restore /tmp/backup/benchmark_db
# Verify: db.failover_test.countDocuments() giữa 2 db
```

## 3. Recovery objectives (tham chiếu lab)

| Metric | Mục tiêu | Ghi chú |
|---|---|---|
| RPO | 1 experiment run | snapshot sau mỗi run lớn |
| RTO | ~5 phút | docker volume restore + refresh |
| Kiểm chứng | COUNT(*) khớp + spot-check 10 rows | bắt buộc trước khi coi backup hợp lệ |

## 4. Limitations

- Procedure **chưa chạy thật** — lệnh dựa trên docs chuẩn nodetool/mongodump; cần verify trên máy lab rồi cập nhật trạng thái VERIFIED.
- Volume names phải kiểm lại qua `docker volume ls` sau khi `lab_up` (compose project prefix có thể khác nhau giữa `docker/` và `compose/`).
- Không có scheduled/incremental backup, không encryption, không off-site — phù hợp lab, không phù hợp production.

## 5. Next action

Trên máy có Docker: chạy procedure §2 → ghi kết quả COUNT trước/sau → cập nhật status thành VERIFIED kèm run_id/backup_id.
