#!/usr/bin/env bash
# =====================================================================
# smoke_test_cql.sh — kiểm tra cụm Scylla hoạt động đúng ở mức CQL:
#   1) tạo keyspace RF=3 (NetworkTopologyStrategy), bảng kv
#   2) ghi qua node1 với CONSISTENCY ALL
#   3) đọc lại từ TỪNG node với CONSISTENCY ONE → phải ra cùng giá trị
#   4) in getendpoints (3 replica) và DESCRIBE KEYSPACE (thấy tablets bật/tắt)
# Bằng chứng cho cổng 08/11 "Lab chạy thử". Kết quả lưu vào evidence/tuan1/.
# =====================================================================
set -euo pipefail
# shellcheck source=../../lib/common.sh
source "$(cd "$(dirname "$0")" && pwd)/../../lib/common.sh"

OUT="$EVIDENCE_DIR/tuan1/smoke_cql_$(stamp).txt"
mkdir -p "$(dirname "$OUT")"
exec > >(tee "$OUT") 2>&1

all_scylla_un scylla-node1 || die "Cụm chưa ở trạng thái UN đầy đủ — chạy lab_up.sh trước"

banner "1. Tạo keyspace lab_smoke (RF=3)"
cqlsh_on scylla-node1 "CREATE KEYSPACE IF NOT EXISTS lab_smoke WITH replication = {'class': 'NetworkTopologyStrategy', 'replication_factor': 3};
CREATE TABLE IF NOT EXISTS lab_smoke.kv (k text PRIMARY KEY, v int, writer text, ts timestamp);"
cqlsh_on scylla-node1 "DESCRIBE KEYSPACE lab_smoke" | head -n 12

value=$(( (RANDOM % 9000) + 1000 ))
banner "2. Ghi v=$value qua scylla-node1 với CONSISTENCY ALL"
cqlsh_on scylla-node1 "CONSISTENCY ALL; INSERT INTO lab_smoke.kv (k, v, writer, ts) VALUES ('smoke', $value, 'scylla-node1', toTimestamp(now()));"

banner "3. Đọc lại từ từng node với CONSISTENCY ONE"
fails=0
for n in $(scylla_nodes); do
  got=$(cqlsh_on "$n" "CONSISTENCY ONE; SELECT v FROM lab_smoke.kv WHERE k = 'smoke';" \
        | grep -E '^[[:space:]]*-?[0-9]+[[:space:]]*$' | tr -d '[:space:]' || true)
  if [[ "$got" == "$value" ]]; then
    ok "$n trả về v=$got"
  else
    err "$n trả về '$got' (mong đợi $value)"; fails=$((fails+1))
  fi
done

banner "4. Replica của khóa 'smoke' (phải đủ 3 IP, mỗi IP thuộc 1 rack)"
nodetool_on scylla-node1 getendpoints lab_smoke kv smoke
nodetool_on scylla-node1 status lab_smoke kv 2>/dev/null || nodetool_on scylla-node1 status

if (( fails == 0 )); then
  banner "SMOKE CQL: PASS  (log: $OUT)"
else
  banner "SMOKE CQL: FAIL ($fails node đọc sai)  (log: $OUT)"
  exit 1
fi
