#!/usr/bin/env bash
# =====================================================================
# lab_down.sh [--purge]
#   Dừng toàn bộ lab (Scylla, Mongo, monitoring, sidecar chaos).
#   --purge : xóa luôn volume dữ liệu (Scylla/Mongo) — dùng khi muốn làm lại từ đầu.
#             Dữ liệu Prometheus KHÔNG bị xóa (giữ lại làm bằng chứng cho báo cáo).
# =====================================================================
set -euo pipefail
# shellcheck source=../lib/common.sh
source "$(cd "$(dirname "$0")" && pwd)/../lib/common.sh"
HERE="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_DIR="$HERE/../compose"

PURGE=()
if [[ "${1:-}" == "--purge" ]]; then
  read -r -p "Xóa TOÀN BỘ dữ liệu Scylla/Mongo? Gõ 'yes' để xác nhận: " ans
  [[ "$ans" == "yes" ]] || die "Đã hủy"
  PURGE=(-v)
fi

"$CHAOS_SH" reset --rm-sidecars || true
"$HERE/../monitoring/setup_monitoring.sh" stop || true
lab_compose -f "$COMPOSE_DIR/mongo.yml" down "${PURGE[@]}" || true
# node4 (tuần 2) dùng chung project với 3 node đầu
node4_file="$LAB_ROOT/tuan2_scaleout-hot-partition/compose/node4.yml"
if [[ -f "$node4_file" ]]; then
  lab_compose -f "$COMPOSE_DIR/scylla.yml" -f "$node4_file" down "${PURGE[@]}" || true
else
  lab_compose -f "$COMPOSE_DIR/scylla.yml" down "${PURGE[@]}" || true
fi
ok "Lab đã dừng${PURGE:+ và xóa dữ liệu}"
