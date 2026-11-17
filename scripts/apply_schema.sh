#!/usr/bin/env bash
# =====================================================================
# apply_schema.sh <file.cql> [file2.cql ...]
# Nạp schema CQL (của Uyên: phương án A / B) vào cụm qua cqlsh trên node1.
# Sau khi nạp, in DESCRIBE KEYSPACE để kiểm tra replication + tablets.
# Gợi ý: keyspace nên khai báo
#   WITH replication = {'class': 'NetworkTopologyStrategy', 'replication_factor': 3}
# để mỗi rack (= AZ) giữ đúng 1 bản sao.
# =====================================================================
set -euo pipefail
# shellcheck source=../lib/common.sh
source "$(cd "$(dirname "$0")" && pwd)/../lib/common.sh"

[[ $# -ge 1 ]] || die "Dùng: $0 <file.cql> [...]"
node=$(first_scylla); [[ -n "$node" ]] || die "Chưa có node Scylla nào chạy"
all_scylla_un "$node" || die "Cụm chưa UN đầy đủ — không nạp schema lúc topology đang đổi"

for f in "$@"; do
  [[ -f "$f" ]] || die "Không thấy file $f"
  # Cảnh báo sớm các lựa chọn dễ làm hỏng thí nghiệm CAP
  if grep -qi "SimpleStrategy" "$f"; then
    warn "$f dùng SimpleStrategy → replica KHÔNG phân theo rack/AZ; nên đổi sang NetworkTopologyStrategy"
  fi
  dest="/tmp/$(basename "$f")"
  docker cp "$f" "$node:$dest"
  info "Nạp $f ..."
  docker exec "$node" cqlsh -f "$dest"
  ok "Đã nạp $f"
done

info "Keyspace hiện có (bỏ qua keyspace hệ thống):"
cqlsh_on "$node" "SELECT keyspace_name, replication FROM system_schema.keyspaces;" | grep -vE ' system|audit' || true
