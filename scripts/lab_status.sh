#!/usr/bin/env bash
# =====================================================================
# lab_status.sh — nhìn nhanh toàn bộ lab: container, ring Scylla, replica set,
#                 target Prometheus, lỗi đang tiêm (nếu có).
# =====================================================================
set -uo pipefail
# shellcheck source=../lib/common.sh
source "$(cd "$(dirname "$0")" && pwd)/../lib/common.sh"
HERE="$(cd "$(dirname "$0")" && pwd)"

banner "Container của lab"
docker ps -a --filter label=lab.group --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker ps -a --filter label=lab.role=chaos-sidecar --format 'table {{.Names}}\t{{.Status}}'

first=$(first_scylla)
if [[ -n "$first" ]]; then
  banner "Ring ScyllaDB (nhìn từ $first)"
  nodetool_on "$first" status 2>&1 || true
  info "Phiên bản: $(docker exec "$first" scylla --version 2>/dev/null || echo '?')"
else
  warn "Không có node Scylla nào đang chạy"
fi

if container_running mongo1; then
  banner "MongoDB Replica Set"
  docker exec mongo1 mongosh --quiet --eval \
    'try { rs.status().members.forEach(m => print("  " + m.name + "  " + m.stateStr)) } catch (e) { print("  chưa khởi tạo: " + e.codeName) }'
fi

banner "Monitoring"
"$HERE/../monitoring/setup_monitoring.sh" status || true

banner "Lỗi đang tiêm"
if docker ps -q --filter label=lab.role=chaos-sidecar | grep -q .; then
  "$CHAOS_SH" status
else
  info "Không có sidecar chaos nào → lab sạch lỗi mạng"
fi
