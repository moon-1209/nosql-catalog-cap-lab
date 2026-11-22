# =====================================================================
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/common.sh
source "$HERE/lib/common.sh"

KS=""; CF=""; DO_CLEANUP=1; BAL_TIMEOUT=600
while [[ $# -gt 0 ]]; do
  case "$1" in
    --ks) KS="$2"; shift 2 ;;
    --cf) CF="$2"; shift 2 ;;
    --no-cleanup) DO_CLEANUP=0; shift ;;
    --balance-timeout) BAL_TIMEOUT="$2"; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) die "Tham số lạ: $1" ;;
  esac
done

T1_COMPOSE="$LAB_ROOT/compose/scylla.yml"
N4_COMPOSE="$HERE/compose/node4.yml"
PROMQ=(python3 "$LAB_ROOT/lib/promlib.py" instant)
TABLET_EXPR='sum by (instance) (scylla_column_family_tablet_count)'
[[ -n "$KS" ]] && TABLET_EXPR="sum by (instance) (scylla_column_family_tablet_count{ks=\"$KS\"${CF:+,cf=\"$CF\"}})"

OUT="$EVIDENCE_DIR/tuan2/scaleout_$(stamp)"
mkdir -p "$OUT"
EV="$OUT/events.jsonl"
exec > >(tee "$OUT/console.log") 2>&1

event() {  # event <tên> [chi tiết] — ghi mốc thời gian + annotation Grafana, in ra ts_ms
  local ts; ts=$(now_ms)
  printf '{"ts_ms":%s,"iso":"%s","event":"%s","detail":"%s"}\n' "$ts" "$(iso_utc)" "$1" "${2:-}" >> "$EV"
  curl -s -m 3 -X POST -H 'Content-Type: application/json' "$GRAFANA_URL/api/annotations" \
    -d "{\"time\":$ts,\"tags\":[\"chaos\",\"scaleout\"],\"text\":\"scale-out: $1 ${2:-}\"}" >/dev/null 2>&1 || true
  echo "$ts"
}

status_snapshot() {  # status_snapshot <hậu tố>
  nodetool_on scylla-node1 status > "$OUT/status_$1.txt" 2>&1 || true
  if [[ -n "$KS" ]]; then
    nodetool_on scylla-node1 status "$KS" ${CF:+"$CF"} > "$OUT/ownership_${1}.txt" 2>&1 || true
  fi
  "${PROMQ[@]}" "$TABLET_EXPR" > "$OUT/tablets_$1.txt" 2>&1 || true
}

node4_code() {  # trạng thái của node4 trong góc nhìn node1: UN/UJ/DN/...
  nodetool_on scylla-node1 status 2>/dev/null | awk -v ip="$SCYLLA4_IP" '$2 == ip {print $1; exit}'
}

# ---------------------------------------------------------------------
container_running scylla-node4 && die "scylla-node4 đã chạy rồi — muốn làm lại: docker rm -f scylla-node4 && docker volume rm nosql-lab-scylla_scylla4-data"
all_scylla_un scylla-node1 || die "Cụm 3 node chưa UN đầy đủ"

banner "Trước scale-out"
status_snapshot before
cat "$OUT/status_before.txt"
[[ -s "$OUT/tablets_before.txt" ]] && { echo "Tablet/node:"; cat "$OUT/tablets_before.txt"; }

banner "Khởi động scylla-node4 (rack $NODE4_RACK, IP $SCYLLA4_IP)"
T_START=$(event bootstrap_start "rack=$NODE4_RACK")
lab_compose -f "$T1_COMPOSE" -f "$N4_COMPOSE" up -d --no-deps scylla-node4

T_UJ=""; T_UN=""
deadline=$(( $(date +%s) + 900 ))
while (( $(date +%s) < deadline )); do
  code=$(node4_code || true)
  if [[ "$code" == "UJ" && -z "$T_UJ" ]]; then T_UJ=$(event node4_joining); info "node4: UJ (đang stream dữ liệu)"; fi
  if [[ "$code" == "UN" ]]; then T_UN=$(event node4_UN); break; fi
  sleep 2
done
[[ -n "$T_UN" ]] || die "Sau 15 phút node4 vẫn chưa UN — xem docker logs scylla-node4"
BOOT_S=$(awk -v a="$T_START" -v b="$T_UN" 'BEGIN { printf "%.1f", (b - a) / 1000 }')
ok "node4 UN sau ${BOOT_S}s"
"$LAB_ROOT/monitoring/setup_monitoring.sh" targets

banner "Theo dõi tablets tự cân bằng (tối đa ${BAL_TIMEOUT}s)"
echo "ts_ms,instance,tablets" > "$OUT/tablets_timeline.csv"
BAL_S="n/a"; prev=""; same=0
deadline=$(( $(date +%s) + BAL_TIMEOUT ))
while (( $(date +%s) < deadline )); do
  snap=$("${PROMQ[@]}" "$TABLET_EXPR" 2>/dev/null | sort || true)
  if [[ -z "$snap" ]]; then
    info "Không có metric tablet (keyspace dùng vnodes hoặc chưa có bảng) → bỏ qua bước này"
    break
  fi
  ts=$(now_ms)
  while IFS=$'\t' read -r lab val; do
    echo "$ts,${lab#instance=},$val" >> "$OUT/tablets_timeline.csv"
  done <<< "$snap"
  echo "$(date +%T)  $(tr '\n' ' ' <<< "$snap")"
  # coi là ổn định khi node4 đã có tablet và phân bố không đổi qua 4 lần đo (≈60s)
  if grep -q "scylla-node4" <<< "$snap" && [[ "$snap" == "$prev" ]]; then
    same=$((same + 1))
  else
    same=0
  fi
  prev="$snap"
  if (( same >= 4 )); then
    T_BAL=$(event tablets_balanced)
    BAL_S=$(awk -v a="$T_UN" -v b="$T_BAL" 'BEGIN { printf "%.1f", (b - a) / 1000 - 60 }')
    ok "Tablets ổn định ~${BAL_S}s sau khi node4 UN"
    break
  fi
  sleep 15
done

if (( DO_CLEANUP )); then
  banner "nodetool cleanup trên node cũ (lần lượt từng node — theo khuyến nghị của ScyllaDB)"
  echo "node,duration_ms" > "$OUT/cleanup.csv"
  for n in scylla-node1 scylla-node2 scylla-node3; do
    t0=$(now_ms)
    nodetool_on "$n" cleanup || warn "cleanup trên $n báo lỗi"
    t1=$(now_ms)
    echo "$n,$((t1 - t0))" >> "$OUT/cleanup.csv"
    ok "$n cleanup xong sau $(( (t1 - t0) / 1000 ))s"
  done
  event cleanup_done >/dev/null
fi

banner "Sau scale-out"
status_snapshot after
cat "$OUT/status_after.txt"
[[ -s "$OUT/tablets_after.txt" ]] && { echo "Tablet/node:"; cat "$OUT/tablets_after.txt"; }

cat > "$OUT/summary.json" <<EOF
{
  "bootstrap_start_ms": $T_START,
  "joining_seen_ms": ${T_UJ:-null},
  "node4_un_ms": $T_UN,
  "bootstrap_seconds": $BOOT_S,
  "tablets_balanced_after_un_seconds": "$BAL_S",
  "node4_rack": "$NODE4_RACK",
  "scylla_image": "$SCYLLA_IMAGE"
}
EOF
banner "XONG — bootstrap ${BOOT_S}s, tablets ổn định sau ${BAL_S}s. Bằng chứng: $OUT"
