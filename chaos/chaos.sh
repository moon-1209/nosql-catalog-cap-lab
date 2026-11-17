#!/usr/bin/env bash
# =====================================================================
# chaos.sh — công cụ tiêm lỗi của lab (Lâm – Chaos Lead)
#
# Nguyên lý: KHÔNG cài iptables/tc vào image ScyllaDB (image 2026.1 dựa trên
# UBI9-minimal, không có sẵn 2 công cụ này). Mỗi container mục tiêu được gắn
# một "sidecar" chạy CHUNG network namespace:
#     docker run --network container:<target> --cap-add NET_ADMIN netshoot
# Lệnh iptables/tc chạy trong sidecar nhưng tác động lên card mạng CỦA target.
# Mọi rule của một thao tác được áp trong MỘT lệnh docker exec nên có hiệu lực gần như
# đồng thời; cả lệnh chaos.sh (tính cả bước kiểm tra) mất ~0,2–0,5 s.
#
# Lệnh:
#   partition <target> [--mode peers|full] [--from a,b,...]
#       peers (mặc định): chặn 2 chiều giữa target và các node cùng nhóm.
#             Client/Prometheus vẫn nối được vào target → mô phỏng AZ bị tách
#             khỏi phần còn lại, client nằm trong AZ đó vẫn gọi được.
#       full: chặn MỌI lưu lượng trừ loopback (node "biến mất" khỏi mạng).
#   heal <target>                         gỡ toàn bộ rule iptables của lab
#   netem <target> [--delay MS] [--jitter MS] [--loss PCT] [--to a,b,...]
#       làm trễ/mất gói ở chiều ĐI RA của target; --to: chỉ áp cho gói tới các đích này
#   delay <target> <MS> [--to a,b]        viết tắt của netem --delay
#   loss  <target> <PCT> [--to a,b]       viết tắt của netem --loss
#   clear-netem <target>
#   pause <target> | unpause <target>     đóng băng tiến trình (giống GC pause dài)
#   prepare [target...]                   tạo sẵn sidecar để lúc tiêm lỗi nhanh hơn
#   status [target...]                    xem rule/qdisc kèm bộ đếm gói bị DROP/trễ
#   reset [--rm-sidecars]                 gỡ sạch mọi lỗi trên mọi container lab
#   mongo-primary                         in tên container đang là PRIMARY
#
# Biến môi trường:
#   CHAOS_LOG=<file.jsonl>  nơi ghi nhật ký thao tác (mặc định runs/chaos_manual.jsonl)
#   CHAOS_ANNOTATE=1        đẩy annotation lên Grafana (dùng khi demo thủ công)
# =====================================================================
set -euo pipefail
# shellcheck source=../lib/common.sh
source "$(cd "$(dirname "$0")" && pwd)/../lib/common.sh"

SIDECAR_PREFIX="chaos-sc-"
CHAOS_LOG="${CHAOS_LOG:-$RUNS_DIR/chaos_manual.jsonl}"
CHAOS_ANNOTATE="${CHAOS_ANNOTATE:-0}"

usage() {
  awk 'NR>1 && /^#/ {sub(/^# ?/, ""); print; next} NR>1 {exit}' "$0"
  exit "${1:-0}"
}

# ---------------------------------------------------------------------
# Script chạy BÊN TRONG sidecar (sh của Alpine). Tham số truyền qua biến môi
# trường của docker exec -e ... nên không phải lo quoting.
# ---------------------------------------------------------------------
NS_PRELUDE=$(cat <<'EOS'
set -e
IPT=""
for b in iptables iptables-nft iptables-legacy; do
  if $b -w -L -n >/dev/null 2>&1; then IPT="$b -w"; break; fi
done
[ -n "$IPT" ] || { echo "Không chạy được iptables (kernel thiếu ip_tables/nf_tables?)" >&2; exit 90; }
IFACE=$(ip -o -4 addr show | awk -v ip="$TIP/" 'index($4, ip)==1 {split($2, a, "@"); print a[1]; exit}')
[ -n "$IFACE" ] || { echo "Không tìm thấy card mạng mang IP $TIP" >&2; exit 91; }
ensure_chains() {
  $IPT -N LAB_CHAOS_IN  2>/dev/null || true
  $IPT -N LAB_CHAOS_OUT 2>/dev/null || true
  $IPT -C INPUT  -j LAB_CHAOS_IN  2>/dev/null || $IPT -I INPUT  1 -j LAB_CHAOS_IN
  $IPT -C OUTPUT -j LAB_CHAOS_OUT 2>/dev/null || $IPT -I OUTPUT 1 -j LAB_CHAOS_OUT
}
add_once() { $IPT -C "$@" 2>/dev/null || $IPT -A "$@"; }
EOS
)

NS_PARTITION_PEERS=$(cat <<'EOS'
ensure_chains
for ip in $PEER_IPS; do
  add_once LAB_CHAOS_IN  -s "$ip" -j DROP
  add_once LAB_CHAOS_OUT -d "$ip" -j DROP
done
EOS
)

NS_PARTITION_FULL=$(cat <<'EOS'
ensure_chains
add_once LAB_CHAOS_IN  -i lo -j RETURN
add_once LAB_CHAOS_IN  -j DROP
add_once LAB_CHAOS_OUT -o lo -j RETURN
add_once LAB_CHAOS_OUT -j DROP
EOS
)

NS_HEAL=$(cat <<'EOS'
while $IPT -D INPUT  -j LAB_CHAOS_IN  2>/dev/null; do :; done
while $IPT -D OUTPUT -j LAB_CHAOS_OUT 2>/dev/null; do :; done
$IPT -F LAB_CHAOS_IN  2>/dev/null || true
$IPT -F LAB_CHAOS_OUT 2>/dev/null || true
$IPT -X LAB_CHAOS_IN  2>/dev/null || true
$IPT -X LAB_CHAOS_OUT 2>/dev/null || true
EOS
)

NS_NETEM=$(cat <<'EOS'
tc qdisc del dev "$IFACE" root >/dev/null 2>&1 || true
if [ -z "$TO_IPS" ]; then
  tc qdisc add dev "$IFACE" root netem $NETEM_ARGS
else
  # prio 3 band: lưu lượng thường vào band 2 (1:2); chỉ gói tới IP trong TO_IPS
  # bị filter u32 đẩy vào band 3 (1:3) có gắn netem.
  tc qdisc add dev "$IFACE" root handle 1: prio bands 3 priomap 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
  tc qdisc add dev "$IFACE" parent 1:3 handle 30: netem $NETEM_ARGS
  for ip in $TO_IPS; do
    tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip dst "$ip/32" flowid 1:3
  done
fi
echo "$IFACE"
EOS
)

NS_CLEAR_NETEM=$(cat <<'EOS'
tc qdisc del dev "$IFACE" root >/dev/null 2>&1 || true
EOS
)

NS_STATUS=$(cat <<'EOS'
echo "  -- iptables ($IPT) | cột pkts = số gói đã bị DROP --"
$IPT -L LAB_CHAOS_IN  -v -n 2>/dev/null | sed 's/^/  /' || echo "  (không có chain LAB_CHAOS_IN)"
$IPT -L LAB_CHAOS_OUT -v -n 2>/dev/null | sed 's/^/  /' || echo "  (không có chain LAB_CHAOS_OUT)"
echo "  -- tc qdisc ($IFACE) --"
tc -s qdisc show dev "$IFACE" | sed 's/^/  /'
EOS
)

# ---------------------------------------------------------------------
# Nhật ký + annotation
# ---------------------------------------------------------------------
record() {
  # record <action> <target> <chi tiết>
  local action="$1" target="$2" detail="${3:-}"
  local ts; ts=$(now_ms)
  detail=${detail//\"/\'}
  mkdir -p "$(dirname "$CHAOS_LOG")"
  printf '{"ts_ms":%s,"iso":"%s","action":"%s","target":"%s","detail":"%s"}\n' \
    "$ts" "$(iso_utc)" "$action" "$target" "$detail" >> "$CHAOS_LOG"
  if [[ "$CHAOS_ANNOTATE" == "1" ]]; then
    curl -s -m 3 -X POST -H 'Content-Type: application/json' "$GRAFANA_URL/api/annotations" \
      -d "{\"time\":$ts,\"tags\":[\"chaos\",\"$action\",\"$target\"],\"text\":\"$action $target $detail\"}" \
      >/dev/null 2>&1 || true
  fi
}

# ---------------------------------------------------------------------
# Sidecar
# ---------------------------------------------------------------------
sidecar_name() { echo "${SIDECAR_PREFIX}$1"; }

ensure_sidecar() {
  # Sidecar chỉ hợp lệ khi đang chạy trong ĐÚNG network namespace hiện tại của target.
  # Khi target restart, Docker cấp netns mới (SandboxKey đổi) dù container ID giữ nguyên,
  # nên so sánh cả ID lẫn SandboxKey rồi mới dùng lại sidecar cũ.
  local target="$1" sc ident cur
  sc=$(sidecar_name "$target")
  container_running "$target" || die "Container '$target' không chạy (hoặc không tồn tại)"
  ident=$(docker inspect -f '{{.Id}}|{{.NetworkSettings.SandboxKey}}' "$target")
  if container_running "$sc"; then
    cur=$(docker inspect -f '{{index .Config.Labels "lab.target_ident"}}' "$sc" 2>/dev/null || true)
    [[ "$cur" == "$ident" ]] && return 0
    warn "Sidecar $sc đang gắn vào netns cũ (target đã restart/tạo lại) → tạo lại"
  fi
  docker rm -f "$sc" >/dev/null 2>&1 || true
  docker run -d --name "$sc" \
    --network "container:$target" \
    --cap-add NET_ADMIN --cap-add NET_RAW \
    --label lab.role=chaos-sidecar --label "lab.target=$target" --label "lab.target_ident=$ident" \
    "$CHAOS_IMAGE" sleep infinity >/dev/null
}

has_sidecar() { container_running "$(sidecar_name "$1")"; }

# ns_run <target> <script> [VAR=giá_trị ...] — chạy script trong netns của target bằng 1 docker exec
ns_run() {
  local target="$1" script="$2"; shift 2
  local tip; tip=$(container_ip "$target")
  [[ -n "$tip" ]] || die "$target không có IP trên mạng $LAB_NETWORK"
  local -a envs=(-e "TIP=$tip")
  local kv
  for kv in "$@"; do envs+=(-e "$kv"); done
  docker exec "${envs[@]}" "$(sidecar_name "$target")" sh -c "$NS_PRELUDE
$script"
}

# ---------------------------------------------------------------------
# Giải tên → IP; peer mặc định = các container cùng lab.group
# ---------------------------------------------------------------------
resolve_ips() {
  local item ip out=()
  for item in ${1//,/ }; do
    if [[ "$item" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      out+=("$item")
    else
      ip=$(container_ip "$item")
      [[ -n "$ip" ]] || die "Không tìm thấy IP của '$item' trên mạng $LAB_NETWORK"
      out+=("$ip")
    fi
  done
  echo "${out[*]}"
}

default_peers() {
  local target="$1" group
  group=$(docker inspect -f '{{index .Config.Labels "lab.group"}}' "$target")
  [[ -n "$group" ]] || die "$target không có label lab.group — hãy chỉ rõ --from"
  lab_group_members "$group" | grep -vx "$target" | paste -sd, - || true
}

# ---------------------------------------------------------------------
# Các lệnh
# ---------------------------------------------------------------------
cmd_partition() {
  local target="" mode="peers" from=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --mode) mode="$2"; shift 2 ;;
      --from) from="$2"; shift 2 ;;
      -*) die "Tham số lạ: $1" ;;
      *) target="$1"; shift ;;
    esac
  done
  [[ -n "$target" ]] || die "Thiếu <target>"
  ensure_sidecar "$target"
  case "$mode" in
    full)
      ns_run "$target" "$NS_PARTITION_FULL" || die "Partition thất bại trên $target"
      ok "PARTITION(full): $target bị cắt khỏi toàn bộ mạng"
      record partition "$target" "mode=full"
      ;;
    peers)
      [[ -n "$from" ]] || from=$(default_peers "$target")
      [[ -n "$from" ]] || die "Không có peer nào để chặn"
      local ips; ips=$(resolve_ips "$from")
      ns_run "$target" "$NS_PARTITION_PEERS" "PEER_IPS=$ips" || die "Partition thất bại trên $target"
      ok "PARTITION(peers): $target ⟂ {$from}"
      record partition "$target" "mode=peers from=$from"
      ;;
    *) die "--mode phải là peers hoặc full" ;;
  esac
}

cmd_heal() {
  local target="${1:-}"
  [[ -n "$target" ]] || die "Thiếu <target>"
  if ! has_sidecar "$target"; then
    info "$target chưa từng bị partition (không có sidecar) — bỏ qua"
    return 0
  fi
  ns_run "$target" "$NS_HEAL" || die "Heal thất bại trên $target"
  ok "HEAL: đã gỡ rule iptables trên $target"
  record heal "$target" ""
}

cmd_netem() {
  local target="" delay="" jitter="" loss="" to=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --delay)  delay="$2"; shift 2 ;;
      --jitter) jitter="$2"; shift 2 ;;
      --loss)   loss="$2"; shift 2 ;;
      --to)     to="$2"; shift 2 ;;
      -*) die "Tham số lạ: $1" ;;
      *) target="$1"; shift ;;
    esac
  done
  [[ -n "$target" ]] || die "Thiếu <target>"
  [[ -n "$delay$loss" ]] || die "Cần ít nhất --delay hoặc --loss"
  local args=""
  if [[ -n "$delay" ]]; then
    args="delay ${delay}ms"
    [[ -n "$jitter" && "$jitter" != "0" ]] && args+=" ${jitter}ms"
  fi
  [[ -n "$loss" && "$loss" != "0" ]] && args+=" loss ${loss}%"
  args="${args# }"
  local to_ips=""
  [[ -n "$to" ]] && to_ips=$(resolve_ips "$to")

  ensure_sidecar "$target"
  local iface
  iface=$(ns_run "$target" "$NS_NETEM" "NETEM_ARGS=$args" "TO_IPS=$to_ips") \
    || die "tc netem thất bại trên $target — trong WSL hãy chạy: sudo modprobe sch_netem sch_prio cls_u32"
  ok "NETEM: $target ($iface) $args${to:+ → chỉ tới {$to}}"
  record netem "$target" "$args${to:+ to=$to}"
}

cmd_clear_netem() {
  local target="${1:-}"
  [[ -n "$target" ]] || die "Thiếu <target>"
  if ! has_sidecar "$target"; then
    info "$target không có sidecar — không có netem để gỡ"
    return 0
  fi
  ns_run "$target" "$NS_CLEAR_NETEM" || die "Gỡ netem thất bại trên $target"
  ok "CLEAR-NETEM: $target"
  record clear_netem "$target" ""
}

cmd_pause() {
  local target="${1:-}"; [[ -n "$target" ]] || die "Thiếu <target>"
  if container_paused "$target"; then info "$target đang pause sẵn"; return 0; fi
  docker pause "$target" >/dev/null
  ok "PAUSE: $target bị đóng băng (process còn đó nhưng không phản hồi)"
  record pause "$target" ""
}

cmd_unpause() {
  local target="${1:-}"; [[ -n "$target" ]] || die "Thiếu <target>"
  if ! container_paused "$target"; then info "$target không bị pause"; return 0; fi
  docker unpause "$target" >/dev/null
  ok "UNPAUSE: $target"
  record unpause "$target" ""
}

all_lab_targets() { { scylla_nodes; mongo_nodes; } | sort -u; }

cmd_prepare() {
  local t targets=("$@")
  [[ ${#targets[@]} -gt 0 ]] || mapfile -t targets < <(all_lab_targets)
  for t in "${targets[@]}"; do
    ensure_sidecar "$t"
    ns_run "$t" ":" || die "Sidecar của $t không dùng được iptables/ip"
  done
  ok "Sidecar sẵn sàng cho: ${targets[*]}"
}

cmd_status() {
  local t targets=("$@")
  [[ ${#targets[@]} -gt 0 ]] || mapfile -t targets < <(all_lab_targets)
  for t in "${targets[@]}"; do
    printf '\n%s== %s ==%s  state=%s\n' "$C_BOLD" "$t" "$C_RESET" \
      "$(docker inspect -f '{{.State.Status}}' "$t" 2>/dev/null || echo missing)"
    if ! has_sidecar "$t"; then
      echo "  (chưa có sidecar → chưa từng bị tiêm lỗi mạng)"
      continue
    fi
    ns_run "$t" "$NS_STATUS" || warn "Không đọc được trạng thái của $t"
  done
}

cmd_reset() {
  local rm_sc=0 t
  [[ "${1:-}" == "--rm-sidecars" ]] && rm_sc=1
  for t in $(all_lab_targets); do
    if container_paused "$t"; then cmd_unpause "$t"; fi
    if has_sidecar "$t"; then
      ns_run "$t" "$NS_HEAL
$NS_CLEAR_NETEM" >/dev/null 2>&1 || warn "Không dọn được $t"
    fi
  done
  if [[ $rm_sc -eq 1 ]]; then
    docker ps -aq --filter label=lab.role=chaos-sidecar | xargs -r docker rm -f >/dev/null
  fi
  ok "RESET: lab sạch lỗi (pause / iptables / netem)"
  record reset "*" "rm_sidecars=$rm_sc"
}

cmd_mongo_primary() {
  local m out found=()
  for m in $(mongo_nodes); do
    out=$(docker exec "$m" mongosh --quiet --eval 'db.hello().isWritablePrimary' 2>/dev/null || true)
    [[ "$out" == "true" ]] && found+=("$m")
  done
  [[ ${#found[@]} -gt 0 ]] || die "Không member nào nhận là PRIMARY"
  if [[ ${#found[@]} -gt 1 ]]; then
    warn "Có ${#found[@]} member cùng nhận là PRIMARY (split-brain tạm thời): ${found[*]}"
  fi
  echo "${found[0]}"
}

main() {
  [[ $# -gt 0 ]] || usage 1
  require_cmd docker
  local cmd="$1"; shift
  case "$cmd" in
    partition)     cmd_partition "$@" ;;
    heal)          cmd_heal "$@" ;;
    netem)         cmd_netem "$@" ;;
    delay)         [[ $# -ge 2 ]] || die "Dùng: delay <target> <ms>"; local t="$1" d="$2"; shift 2; cmd_netem "$t" --delay "$d" "$@" ;;
    loss)          [[ $# -ge 2 ]] || die "Dùng: loss <target> <pct>";  local t="$1" p="$2"; shift 2; cmd_netem "$t" --loss "$p" "$@" ;;
    clear-netem)   cmd_clear_netem "$@" ;;
    pause)         cmd_pause "$@" ;;
    unpause)       cmd_unpause "$@" ;;
    prepare)       cmd_prepare "$@" ;;
    status)        cmd_status "$@" ;;
    reset)         cmd_reset "$@" ;;
    mongo-primary) cmd_mongo_primary ;;
    -h|--help|help) usage 0 ;;
    *) err "Lệnh không hợp lệ: $cmd"; usage 1 ;;
  esac
}
main "$@"
