#!/usr/bin/env bash
# =====================================================================
# lab_up.sh [scylla] [mongo] [monitoring] | all
#   Không tham số  = scylla + monitoring (bộ dùng hằng ngày)
#   all            = scylla + mongo + monitoring
# Ví dụ: ./lab_up.sh mongo     # chỉ bật MongoDB Replica Set
# =====================================================================
set -euo pipefail
# shellcheck source=../../lib/common.sh
source "$(cd "$(dirname "$0")" && pwd)/../../lib/common.sh"
HERE="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_DIR="$HERE/../compose"

components=("$@")
[[ ${#components[@]} -gt 0 ]] || components=(scylla monitoring)
[[ "${components[0]}" == "all" ]] && components=(scylla mongo monitoring)

require_cmd docker curl python3

up_scylla() {
  banner "ScyllaDB 3 node ($SCYLLA_IMAGE, smp=$SCYLLA_SMP, memory=$SCYLLA_MEMORY)"
  local aio; aio=$(cat /proc/sys/fs/aio-max-nr 2>/dev/null || echo 0)
  (( aio >= 1048576 )) || warn "fs.aio-max-nr=$aio thấp — nếu node chết, chạy 00_kiem_tra_moi_truong.sh --fix"
  info "Khởi động tuần tự node1 → node2 → node3 (mỗi node chờ node trước healthy, ~1–2 phút/node)..."
  lab_compose -f "$COMPOSE_DIR/scylla.yml" up -d
  wait_until "Cả 3 node ở trạng thái UN" 420 all_scylla_un scylla-node1
  nodetool_on scylla-node1 status
}

up_mongo() {
  banner "MongoDB Replica Set $MONGO_RS ($MONGO_IMAGE)"
  lab_compose -f "$COMPOSE_DIR/mongo.yml" up -d --wait
  docker exec -e "MONGO_RS=$MONGO_RS" -e "MONGO1_IP=$MONGO1_IP" -e "MONGO2_IP=$MONGO2_IP" -e "MONGO3_IP=$MONGO3_IP" \
    mongo1 mongosh --quiet /lab-scripts/rs-init.js
  ok "Chuỗi kết nối: mongodb://$MONGO1_IP:27017,$MONGO2_IP:27017,$MONGO3_IP:27017/?replicaSet=$MONGO_RS"
}

up_monitoring() {
  banner "Monitoring (scylla-monitoring $SCYLLA_MONITORING_VERSION + cAdvisor)"
  "$HERE/../monitoring/setup_monitoring.sh" start
}

ensure_network
for c in "${components[@]}"; do
  case "$c" in
    scylla) up_scylla ;;
    mongo) up_mongo ;;
    monitoring) up_monitoring ;;
    *) die "Thành phần không hợp lệ: $c (scylla|mongo|monitoring|all)" ;;
  esac
done

banner "Lab đã sẵn sàng"
cat >&2 <<EOF
  CQL (từ WSL):        $SCYLLA1_IP,$SCYLLA2_IP,$SCYLLA3_IP : 9042   (từ Windows: localhost:9042)
  Grafana:             $GRAFANA_URL/d/nosql-cap-lab
  Prometheus:          $PROM_URL/targets
  Trạng thái:          $HERE/lab_status.sh
  Kiểm thử nhanh:      $HERE/smoke_test_cql.sh  và  $HERE/chaos_smoke_test.sh
EOF
