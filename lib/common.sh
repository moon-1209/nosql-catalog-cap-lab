#!/usr/bin/env bash
# =====================================================================
# lib/common.sh — hàm dùng chung cho mọi script bash của lab.
# Cách dùng trong script khác:
#   source "$(dirname "$0")/../lib/common.sh"     (đường dẫn tương đối tùy vị trí)
# File này KHÔNG tự chạy; nó chỉ định nghĩa biến + hàm.
# =====================================================================

# Thư mục gốc của repo (thư mục chứa lab.env)
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export LAB_ROOT

# Nạp cấu hình chung; set -a để mọi biến được export cho tiến trình con (python, compose)
if [[ -f "$LAB_ROOT/lab.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  . "$LAB_ROOT/lab.env"
  set +a
else
  echo "Không tìm thấy $LAB_ROOT/lab.env" >&2
  exit 1
fi

# Đường dẫn tới các công cụ dùng lại giữa các tuần
CHAOS_SH="$LAB_ROOT/chaos/chaos.sh"
SNAPSHOT_SH="$LAB_ROOT/lib/lab_snapshot.sh"
RUNS_DIR="${RUNS_DIR:-$LAB_ROOT/runs}"
EVIDENCE_DIR="${EVIDENCE_DIR:-$LAB_ROOT/evidence}"
export CHAOS_SH SNAPSHOT_SH RUNS_DIR EVIDENCE_DIR

# ---------------------------------------------------------------------
# Log có màu (tắt màu khi không phải terminal, ví dụ khi ghi ra file)
# ---------------------------------------------------------------------
if [[ -t 2 ]]; then
  C_RESET=$'\e[0m'; C_RED=$'\e[31m'; C_GREEN=$'\e[32m'; C_YELLOW=$'\e[33m'; C_CYAN=$'\e[36m'; C_BOLD=$'\e[1m'
else
  C_RESET=""; C_RED=""; C_GREEN=""; C_YELLOW=""; C_CYAN=""; C_BOLD=""
fi

info() { printf '%s %s[INFO]%s %s\n' "$(date +%H:%M:%S)" "$C_CYAN" "$C_RESET" "$*" >&2; }
ok()   { printf '%s %s[ OK ]%s %s\n' "$(date +%H:%M:%S)" "$C_GREEN" "$C_RESET" "$*" >&2; }
warn() { printf '%s %s[WARN]%s %s\n' "$(date +%H:%M:%S)" "$C_YELLOW" "$C_RESET" "$*" >&2; }
err()  { printf '%s %s[FAIL]%s %s\n' "$(date +%H:%M:%S)" "$C_RED" "$C_RESET" "$*" >&2; }
die()  { err "$*"; exit 1; }

banner() {
  local line="=================================================================="
  printf '\n%s%s\n  %s\n%s%s\n' "$C_BOLD" "$line" "$*" "$line" "$C_RESET" >&2
}

# ---------------------------------------------------------------------
# Thời gian: luôn ghi epoch milli-giây (UTC) để khớp log của Duy và Prometheus
# ---------------------------------------------------------------------
now_ms()  { date +%s%3N; }
iso_utc() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
stamp()   { date +%Y%m%d_%H%M%S; }

require_cmd() {
  local c
  for c in "$@"; do
    command -v "$c" >/dev/null 2>&1 || die "Thiếu lệnh '$c'. Cài đặt rồi chạy lại."
  done
}

# ---------------------------------------------------------------------
# Docker helpers
# ---------------------------------------------------------------------
container_exists()  { docker inspect "$1" >/dev/null 2>&1; }
container_running() { [[ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null)" == "true" ]]; }
container_paused()  { [[ "$(docker inspect -f '{{.State.Paused}}' "$1" 2>/dev/null)" == "true" ]]; }

# IP của container trên mạng lab
container_ip() {
  docker inspect -f "{{with index .NetworkSettings.Networks \"$LAB_NETWORK\"}}{{.IPAddress}}{{end}}" "$1" 2>/dev/null
}

# Liệt kê container đang chạy theo nhóm (label lab.group=scylla|mongo)
lab_group_members() {
  docker ps --filter "label=lab.group=$1" --format '{{.Names}}' | sort
}
scylla_nodes() { lab_group_members scylla; }
mongo_nodes()  { lab_group_members mongo; }

# Container scylla đầu tiên đang chạy (dùng làm điểm hỏi nodetool/cqlsh)
first_scylla() { scylla_nodes | head -n1; }

lab_compose() {
  # $@: các tham số cho docker compose (vd: -f file.yml up -d)
  docker compose --env-file "$LAB_ROOT/lab.env" "$@"
}

ensure_network() {
  if docker network inspect "$LAB_NETWORK" >/dev/null 2>&1; then
    return 0
  fi
  info "Tạo mạng $LAB_NETWORK ($LAB_SUBNET, IP động trong $LAB_IP_RANGE)"
  docker network create --driver bridge \
    --subnet "$LAB_SUBNET" --ip-range "$LAB_IP_RANGE" --gateway "$LAB_GATEWAY" \
    --label lab.managed=true "$LAB_NETWORK" >/dev/null
}

# wait_until <mô tả> <timeout giây> <lệnh...> : lặp tới khi lệnh trả về 0
wait_until() {
  local desc="$1" timeout="$2"; shift 2
  local start; start=$(date +%s)
  until "$@" >/dev/null 2>&1; do
    if (( $(date +%s) - start >= timeout )); then
      err "Hết ${timeout}s mà vẫn chưa: $desc"
      return 1
    fi
    sleep 2
  done
  ok "$desc (sau $(( $(date +%s) - start ))s)"
}

# ---------------------------------------------------------------------
# ScyllaDB helpers
# ---------------------------------------------------------------------
nodetool_on() {
  # nodetool_on <container> <args...>  — chạy nodetool bên trong container
  local node="$1"; shift
  docker exec "$node" nodetool "$@"
}

cqlsh_on() {
  # cqlsh_on <container> "<câu lệnh CQL>"  — cqlsh chạy bên trong container, nối vào chính node đó
  local node="$1"; shift
  docker exec "$node" cqlsh -e "$*"
}

# Trả về 0 nếu MỌI node scylla đang chạy đều là UN trong góc nhìn của <observer>
all_scylla_un() {
  local observer="${1:-$(first_scylla)}"
  [[ -n "$observer" ]] || return 1
  local status ip n
  status=$(nodetool_on "$observer" status 2>/dev/null) || return 1
  for n in $(scylla_nodes); do
    ip=$(container_ip "$n")
    [[ -n "$ip" ]] || return 1
    grep -Eq "^UN[[:space:]]+${ip//./\\.}[[:space:]]" <<<"$status" || return 1
  done
}

# Đếm số node UN mà <observer> nhìn thấy
count_un() {
  local observer="$1"
  nodetool_on "$observer" status 2>/dev/null | grep -Ec '^UN[[:space:]]' || true
}
