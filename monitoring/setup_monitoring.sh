#!/usr/bin/env bash
# =====================================================================
# setup_monitoring.sh — ScyllaDB Monitoring Stack 4.16.3 (Prometheus + Grafana)
#                       + cAdvisor, tất cả nằm chung mạng lab-net.
#
#   ./setup_monitoring.sh start     # clone (nếu cần) + chạy stack
#   ./setup_monitoring.sh targets   # sinh lại danh sách node (sau khi thêm node 4)
#   ./setup_monitoring.sh stop
#   ./setup_monitoring.sh status
#
# Vì sao dùng start-all.sh chính chủ thay vì tự viết compose Prometheus/Grafana?
#   Dashboard của Scylla phụ thuộc rất nhiều recording rule (wlatencyp99, cql:*...)
#   do chính repo scylla-monitoring sinh ra; dùng bản gốc thì dashboard chắc chắn
#   khớp với ScyllaDB 2026.1 (bản 4.16 khai báo hỗ trợ 2026.1).
# =====================================================================
set -euo pipefail
# shellcheck source=../lib/common.sh
source "$(cd "$(dirname "$0")" && pwd)/../lib/common.sh"

HERE="$(cd "$(dirname "$0")" && pwd)"
MON_DIR="$HERE/scylla-monitoring"
BUILD="$HERE/build"
PROM_DATA="$HERE/prometheus_data"
DASHBOARD="$HERE/dashboards/nosql-cap-lab.json"
TARGETS_FILE="$BUILD/scylla_servers.yml"
EXTRA_TARGETS="$BUILD/prometheus_extra_targets.yml"

clone_if_needed() {
  if [[ -f "$MON_DIR/CURRENT_VERSION.sh" ]]; then
    local cur; cur=$(cat "$MON_DIR/CURRENT_VERSION.sh")
    [[ "$cur" == "$SCYLLA_MONITORING_VERSION" ]] || \
      warn "Đang có scylla-monitoring $cur, lab.env yêu cầu $SCYLLA_MONITORING_VERSION (xóa thư mục $MON_DIR để clone lại)"
    return 0
  fi
  require_cmd git
  info "Clone scylla-monitoring $SCYLLA_MONITORING_VERSION ..."
  git clone -q --depth 1 --branch "$SCYLLA_MONITORING_VERSION" \
    https://github.com/scylladb/scylla-monitoring.git "$MON_DIR"
  ok "Đã clone vào $MON_DIR"
}

# Ghi danh sách target TẠI CHỖ (giữ nguyên inode). Lý do: start-all.sh bind-mount
# đúng file này vào container Prometheus; nếu tạo file mới rồi rename thì container
# vẫn nhìn inode cũ và không thấy node mới.
write_targets() {
  mkdir -p "$BUILD"
  local nodes; nodes=$(scylla_nodes)
  [[ -n "$nodes" ]] || die "Chưa có node scylla nào đang chạy — chạy ../scripts/lab_up.sh scylla trước"
  {
    echo "# Sinh tự động bởi setup_monitoring.sh lúc $(iso_utc) — đừng sửa tay"
    echo "- targets:"
    local n
    for n in $nodes; do echo "    - $n"; done
    echo "  labels:"
    echo "    cluster: $SCYLLA_CLUSTER_NAME"
    echo "    dc: $SCYLLA_DC"
  } > "$TARGETS_FILE"
  ok "Target Prometheus: $(echo "$nodes" | tr '\n' ' ')"
}

write_extra_targets() {
  mkdir -p "$BUILD"
  sed "s/__CLUSTER__/$SCYLLA_CLUSTER_NAME/g" "$HERE/prometheus_extra_targets.yml" > "$EXTRA_TARGETS"
}

start_cadvisor() {
  lab_compose -f "$HERE/../compose/cadvisor.yml" up -d
  ok "cAdvisor: http://localhost:8080"
}

start_stack() {
  ensure_network
  clone_if_needed
  write_targets
  write_extra_targets
  start_cadvisor
  mkdir -p "$PROM_DATA"

  info "Khởi động Prometheus + Grafana (scylla-monitoring $SCYLLA_MONITORING_VERSION) ..."
  (
    cd "$MON_DIR"
    ./start-all.sh \
      -v 2026.1 \
      -d "$PROM_DATA" \
      -s "$TARGETS_FILE" \
      -T "$EXTRA_TARGETS" \
      -j "$DASHBOARD" \
      -D "--net=$LAB_NETWORK" \
      --scrap "$SCRAPE_INTERVAL_S" \
      --evaluation-interval 10s \
      -b "--storage.tsdb.retention.time=$PROM_RETENTION" \
      --no-loki --no-renderer --no-alertmanager
  )
  wait_until "Prometheus sẵn sàng" 90 curl -sf "$PROM_URL/-/ready"
  wait_until "Grafana sẵn sàng" 120 curl -sf "$GRAFANA_URL/api/health"
  ok "Grafana:    $GRAFANA_URL  (dashboard lab: $GRAFANA_URL/d/nosql-cap-lab)"
  ok "Prometheus: $PROM_URL/targets"
}

stop_stack() {
  if [[ -x "$MON_DIR/kill-all.sh" ]]; then
    (cd "$MON_DIR" && ./kill-all.sh) || true
  else
    docker rm -f aprom agraf aalert >/dev/null 2>&1 || true
  fi
  lab_compose -f "$HERE/../compose/cadvisor.yml" down || true
  ok "Đã dừng monitoring (dữ liệu Prometheus vẫn giữ trong $PROM_DATA)"
}

show_status() {
  docker ps --filter name=aprom --filter name=agraf --filter name=cadvisor \
    --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
  if curl -sf "$PROM_URL/-/ready" >/dev/null 2>&1; then
    info "Trạng thái target (job / instance / health):"
    curl -s "$PROM_URL/api/v1/targets?state=active" | python3 -c '
import json, sys
d = json.load(sys.stdin)["data"]["activeTargets"]
for t in sorted(d, key=lambda x: (x["labels"].get("job",""), x["labels"].get("instance",""))):
    print(f"  {t[\"labels\"].get(\"job\",\"?\"):14s} {t[\"labels\"].get(\"instance\",\"?\"):22s} {t[\"health\"]}")
'
  else
    warn "Prometheus chưa chạy"
  fi
}

case "${1:-start}" in
  start)   start_stack ;;
  targets) write_targets ;;   # Prometheus dùng file_sd nên tự nạp lại, không cần restart
  stop)    stop_stack ;;
  restart) stop_stack; start_stack ;;
  status)  show_status ;;
  *) die "Dùng: $0 start|targets|stop|restart|status" ;;
esac
