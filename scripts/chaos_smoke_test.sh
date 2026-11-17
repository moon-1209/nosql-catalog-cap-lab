#!/usr/bin/env bash
# =====================================================================
# chaos_smoke_test.sh [--gossip]
# Chứng minh bằng SỐ ĐO rằng các lỗi mạng tiêm vào là thật:
#   T1  tc netem delay 100ms trên node3   → RTT node1→node3 tăng ≈ +100ms
#   T2  delay có lọc đích (--to node1)    → chỉ node1 thấy chậm, node2 không
#   T3  iptables partition (peers)        → node1→node3 mất 100% gói, nhưng
#                                          container "trung lập" vẫn ping được node3
#   T4  docker pause                      → CQL tới node3 không trả lời, unpause là hết
#   --gossip: ở T3 chờ thêm ~25s để chụp nodetool status hai phía (split-brain view)
# Toàn bộ output lưu ở evidence/tuan1/chaos_smoke_<thời_gian>.txt
# =====================================================================
set -uo pipefail
# shellcheck source=../lib/common.sh
source "$(cd "$(dirname "$0")" && pwd)/../lib/common.sh"

GOSSIP=0
[[ "${1:-}" == "--gossip" ]] && GOSSIP=1
OUT="$EVIDENCE_DIR/tuan1/chaos_smoke_$(stamp).txt"
mkdir -p "$(dirname "$OUT")"
exec > >(tee "$OUT") 2>&1
export CHAOS_LOG="$EVIDENCE_DIR/tuan1/chaos_smoke_events.jsonl"

N1=scylla-node1; N2=scylla-node2; N3=scylla-node3
IP3=$(container_ip "$N3")
[[ -n "$IP3" ]] || die "scylla-node3 chưa chạy"
RESULTS=()

# check <mô tả> <lệnh...> : chạy lệnh, 0 = PASS
check() {
  local name="$1"; shift
  if "$@"; then ok "PASS  $name"; RESULTS+=("PASS  $name")
  else err "FAIL  $name"; RESULTS+=("FAIL  $name"); fi
}
gt() { awk -v a="$1" -v b="$2" 'BEGIN { exit !(a + 0 > b + 0) }'; }
lt() { awk -v a="$1" -v b="$2" 'BEGIN { exit !(a + 0 < b + 0) }'; }
eq() { [[ "$1" == "$2" ]]; }

# ping từ netns của <src> tới node3; in "avg_ms loss_pct"
probe() {
  local src="$1" out avg loss
  out=$(docker exec "chaos-sc-$src" ping -c 10 -i 0.2 -W 1 -q "$IP3" 2>&1 || true)
  avg=$(grep -Eo '= [0-9.]+/[0-9.]+' <<<"$out" | head -1 | cut -d/ -f2)
  loss=$(grep -Eo '[0-9.]+% packet loss' <<<"$out" | grep -Eo '^[0-9]+' | head -1)
  echo "${avg:-NaN} ${loss:-100}"
}
# ping từ một container không thuộc nhóm scylla (đại diện client / Prometheus)
probe_neutral() {
  local out loss
  out=$(docker run --rm --network "$LAB_NETWORK" "$CHAOS_IMAGE" ping -c 5 -i 0.2 -W 1 -q "$IP3" 2>&1 || true)
  loss=$(grep -Eo '[0-9.]+% packet loss' <<<"$out" | grep -Eo '^[0-9]+' | head -1)
  echo "${loss:-100}"
}
cql_alive() {  # cql_alive <ip> <timeout_s> — node có trả lời CQL không (hỏi từ node1)
  docker exec "$N1" cqlsh "$1" --connect-timeout="$2" --request-timeout="$2" \
    -e "SELECT now() FROM system.local" >/dev/null 2>&1
}
n1_sees_n3_down() { nodetool_on "$N1" status | grep -Eq "^DN[[:space:]]+${IP3//./\\.}[[:space:]]"; }
n3_sees_two_down() { [[ $(nodetool_on "$N3" status | grep -Ec '^DN[[:space:]]') -eq 2 ]]; }

banner "Chuẩn bị: reset lỗi cũ + tạo sidecar cho node1/2/3"
"$CHAOS_SH" reset
"$CHAOS_SH" prepare "$N1" "$N2" "$N3"
read -r base _ < <(probe "$N1")
info "RTT nền node1→node3: ${base} ms"

banner "T1 — netem delay 100ms trên toàn bộ egress của node3"
"$CHAOS_SH" delay "$N3" 100
read -r d1 _ < <(probe "$N1")
info "RTT node1→node3 khi delay: ${d1} ms"
check "T1 delay làm RTT tăng thêm ≥ 90ms (nền ${base} → ${d1} ms)" gt "$d1" "$(awk -v b="$base" 'BEGIN { print b + 90 }')"
"$CHAOS_SH" clear-netem "$N3"
read -r back _ < <(probe "$N1")
check "T1 gỡ netem → RTT về < 20ms (đo được ${back} ms)" lt "$back" 20

banner "T2 — delay 100ms CHỈ với gói từ node3 đi tới node1"
"$CHAOS_SH" delay "$N3" 100 --to "$N1"
read -r d_n1 _ < <(probe "$N1")
read -r d_n2 _ < <(probe "$N2")
info "RTT node1→node3 = ${d_n1} ms ; node2→node3 = ${d_n2} ms"
check "T2 node1 thấy chậm (${d_n1} ms ≥ 90)" gt "$d_n1" 90
check "T2 node2 KHÔNG bị ảnh hưởng (${d_n2} ms < 20)" lt "$d_n2" 20
"$CHAOS_SH" clear-netem "$N3"

banner "T3 — iptables partition (peers): node3 ⟂ {node1, node2}"
"$CHAOS_SH" partition "$N3" --mode peers
read -r _ loss1 < <(probe "$N1")
neutral_loss=$(probe_neutral)
info "Mất gói node1→node3 = ${loss1}% ; container trung lập→node3 = ${neutral_loss}%"
check "T3 node1→node3 mất 100% gói" eq "$loss1" 100
check "T3 container trung lập vẫn tới được node3 (mất 0%)" eq "$neutral_loss" 0
"$CHAOS_SH" status "$N3"
if (( GOSSIP )); then
  info "Chờ 25s cho failure detector (failure_detector_timeout_in_ms mặc định 20000) ..."
  sleep 25
  echo "----- nodetool status nhìn từ node1 -----"; nodetool_on "$N1" status
  echo "----- nodetool status nhìn từ node3 -----"; nodetool_on "$N3" status
  check "T3 node1 thấy node3 là DN" n1_sees_n3_down
  check "T3 node3 thấy 2 node còn lại là DN (split-brain view)" n3_sees_two_down
fi
"$CHAOS_SH" heal "$N3"
read -r _ loss_h < <(probe "$N1")
check "T3 heal → node1→node3 hết mất gói (${loss_h}%)" eq "$loss_h" 0

banner "T4 — docker pause node3"
"$CHAOS_SH" pause "$N3"
if cql_alive "$IP3" 3; then paused_alive=1; else paused_alive=0; fi
check "T4 khi pause, CQL tới node3 KHÔNG trả lời" eq "$paused_alive" 0
"$CHAOS_SH" unpause "$N3"
sleep 3
check "T4 unpause → CQL tới node3 trả lời lại" cql_alive "$IP3" 10

banner "Dọn dẹp + chờ cụm về UN"
"$CHAOS_SH" reset
wait_until "Cả cụm trở lại UN" 120 all_scylla_un "$N1" || true

banner "TỔNG KẾT"
printf '  %s\n' "${RESULTS[@]}"
if printf '%s\n' "${RESULTS[@]}" | grep -q '^FAIL'; then
  err "Có test FAIL — xem log: $OUT"
  exit 1
fi
ok "Mọi test PASS — log: $OUT"
