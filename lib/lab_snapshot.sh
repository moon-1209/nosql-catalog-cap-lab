#!/usr/bin/env bash
# =====================================================================
# lab_snapshot.sh <thư_mục_run> <nhãn>
# Chụp "ảnh" trạng thái lab tại một thời điểm để làm bằng chứng cho báo cáo:
#   • nodetool status nhìn từ TỪNG node (thấy rõ split-brain: mỗi bên thấy bên kia DN)
#   • trạng thái lỗi đang tiêm (iptables/tc kèm bộ đếm gói)
#   • docker ps, rs.status() của MongoDB (nếu đang chạy)
# Các lệnh chạy song song, có timeout, để không làm lệch mốc thời gian của kịch bản.
# =====================================================================
set -uo pipefail
# shellcheck source=common.sh
source "$(cd "$(dirname "$0")" && pwd)/common.sh"

RUN_DIR="${1:?Dùng: lab_snapshot.sh <thư_mục_run> <nhãn>}"
TAG="${2:-snapshot}"
SAFE_TAG=$(printf '%s' "$TAG" | tr -c 'A-Za-z0-9_.-' '_' | cut -c1-60)
TS=$(now_ms)
OUT="$RUN_DIR/snapshots/${TS}_${SAFE_TAG}"
mkdir -p "$OUT"

{
  echo "{\"ts_ms\": $TS, \"iso\": \"$(iso_utc)\", \"tag\": \"${TAG//\"/\'}\"}"
} > "$OUT/snapshot.json"

docker ps -a --filter label=lab.group --format 'table {{.Names}}\t{{.Status}}' > "$OUT/docker_ps.txt" 2>&1 &

for n in $(scylla_nodes); do
  (
    if container_paused "$n"; then
      echo "(container đang PAUSE — không chạy được nodetool)" > "$OUT/nodetool_status_${n}.txt"
    else
      timeout 25 docker exec "$n" nodetool status > "$OUT/nodetool_status_${n}.txt" 2>&1 \
        || echo "(nodetool lỗi/timeout)" >> "$OUT/nodetool_status_${n}.txt"
    fi
  ) &
done

for m in $(mongo_nodes); do
  (
    if container_paused "$m"; then
      echo "(container đang PAUSE)" > "$OUT/mongo_rs_${m}.txt"
    else
      timeout 20 docker exec "$m" mongosh --quiet --eval \
        'try { rs.status().members.forEach(x => print(x.name + "  " + x.stateStr + "  optime=" + JSON.stringify(x.optimeDate))) } catch (e) { print("rs.status lỗi: " + e) }' \
        > "$OUT/mongo_rs_${m}.txt" 2>&1 || echo "(mongosh lỗi/timeout)" >> "$OUT/mongo_rs_${m}.txt"
    fi
  ) &
done

( timeout 30 "$CHAOS_SH" status > "$OUT/chaos_status.txt" 2>&1 || true ) &

wait
echo "$OUT"
