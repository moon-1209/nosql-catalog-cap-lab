#!/usr/bin/env bash
# =====================================================================
# 00_kiem_tra_moi_truong.sh [--fix]
# Kiểm tra máy (WSL2 + Docker) có đủ điều kiện dựng lab chưa.
#   --fix : tự sửa những gì sửa được (sysctl aio-max-nr, nạp module netem) — cần sudo
# Chạy TRƯỚC lab_up.sh. Kết quả PASS/WARN/FAIL cuối cùng dùng làm bằng chứng cổng 04/11.
# =====================================================================
set -uo pipefail
# shellcheck source=../../lib/common.sh
source "$(cd "$(dirname "$0")" && pwd)/../../lib/common.sh"

FIX=0
[[ "${1:-}" == "--fix" ]] && FIX=1
PASS=0; WARNS=0; FAILS=0
pass() { ok "$*"; PASS=$((PASS+1)); }
wrn()  { warn "$*"; WARNS=$((WARNS+1)); }
fail() { err "$*"; FAILS=$((FAILS+1)); }

banner "Kiểm tra môi trường lab ($(date '+%F %T'))"

# 1. WSL2
if grep -qi microsoft /proc/version 2>/dev/null; then
  pass "Đang chạy trong WSL2: $(uname -r)"
else
  wrn "Không phải WSL2 (vẫn dùng được nếu là Linux thật): $(uname -r)"
fi

# 2. Docker
if ! command -v docker >/dev/null; then
  fail "Chưa cài Docker CLI"
elif ! docker info >/dev/null 2>&1; then
  fail "Không nói chuyện được với Docker daemon (chưa start? user chưa thuộc nhóm docker?)"
else
  os=$(docker info --format '{{.OperatingSystem}}' 2>/dev/null)
  if [[ "$os" == *"Docker Desktop"* ]]; then
    wrn "Đang dùng Docker Desktop. IP container (10.88.88.x) thường KHÔNG truy cập được từ shell WSL → harness của Duy nên chạy trong container trên mạng $LAB_NETWORK, hoặc chuyển sang docker-ce cài thẳng trong WSL (khuyến nghị, xem README)."
  else
    pass "Docker Engine chạy trong WSL: $os, server $(docker version --format '{{.Server.Version}}' 2>/dev/null)"
  fi
  if docker compose version >/dev/null 2>&1; then
    pass "Docker Compose v2: $(docker compose version --short 2>/dev/null)"
  else
    fail "Thiếu docker compose v2 (plugin)"
  fi
fi

# 3. cgroup v2 (cAdvisor + docker pause cần)
if [[ "$(stat -fc %T /sys/fs/cgroup 2>/dev/null)" == "cgroup2fs" ]]; then
  pass "cgroup v2"
else
  wrn "Không phải cgroup v2 — cAdvisor có thể thiếu metric"
fi

# 4. fs.aio-max-nr (ScyllaDB cần ~11k slot AIO mỗi shard)
need_aio=1048576
cur_aio=$(cat /proc/sys/fs/aio-max-nr 2>/dev/null || echo 0)
if (( cur_aio >= need_aio )); then
  pass "fs.aio-max-nr = $cur_aio"
elif (( FIX )); then
  sudo sysctl -w fs.aio-max-nr=$need_aio >/dev/null && \
  echo "fs.aio-max-nr = $need_aio" | sudo tee /etc/sysctl.d/99-nosql-lab.conf >/dev/null && \
  pass "Đã nâng fs.aio-max-nr lên $need_aio (lưu /etc/sysctl.d/99-nosql-lab.conf)"
else
  fail "fs.aio-max-nr = $cur_aio (< $need_aio) → node Scylla sẽ chết với 'Could not setup Async I/O'. Chạy lại với --fix"
fi

# 5. Module kernel cho tc netem (kernel WSL 6.x build sẵn dạng module =m)
mods_missing=()
for m in sch_netem sch_prio cls_u32; do
  [[ -d /sys/module/$m ]] || mods_missing+=("$m")
done
if (( ${#mods_missing[@]} == 0 )); then
  pass "Module tc đã nạp: sch_netem sch_prio cls_u32"
elif (( FIX )); then
  if sudo modprobe -a "${mods_missing[@]}" 2>/dev/null; then
    printf '%s\n' sch_netem sch_prio cls_u32 | sudo tee /etc/modules-load.d/nosql-lab.conf >/dev/null
    pass "Đã nạp module: ${mods_missing[*]} (lưu /etc/modules-load.d/nosql-lab.conf)"
  else
    fail "modprobe ${mods_missing[*]} thất bại → kernel WSL quá cũ? Chạy 'wsl --update' trong PowerShell rồi thử lại"
  fi
else
  wrn "Chưa nạp module: ${mods_missing[*]} (tc thường tự nạp khi cần; chắc ăn thì chạy lại với --fix)"
fi

# 6. Tài nguyên
mem_gb=$(awk '/MemTotal/ {printf "%d", $2/1024/1024}' /proc/meminfo)
if (( mem_gb >= 9 )); then pass "RAM cho WSL: ${mem_gb} GB"
elif (( mem_gb >= 7 )); then wrn "RAM cho WSL: ${mem_gb} GB — đủ cho 3 node Scylla + monitoring; khi thêm node 4 nên tắt Mongo (xem .wslconfig.example)"
else fail "RAM cho WSL chỉ ${mem_gb} GB — tăng memory trong %UserProfile%\\.wslconfig"
fi
cpus=$(nproc)
if (( cpus >= 6 )); then pass "CPU: $cpus luồng"; else wrn "CPU: $cpus luồng — nên đặt SCYLLA_SMP=1 trong lab.env"; fi
free_gb=$(df -BG --output=avail "$LAB_ROOT" | tail -1 | tr -dc '0-9')
if (( free_gb >= 15 )); then pass "Ổ đĩa trống: ${free_gb} GB"; else wrn "Ổ đĩa trống chỉ ${free_gb} GB (nên ≥ 15 GB)"; fi

# 7. Vị trí repo (bind mount từ /mnt/c rất chậm và lỗi quyền)
if [[ "$LAB_ROOT" == /mnt/* ]]; then
  wrn "Repo đang nằm trên ổ Windows ($LAB_ROOT). Nên clone vào ~/ trong WSL"
else
  pass "Repo nằm trong filesystem WSL: $LAB_ROOT"
fi

# 8. Cổng cần trống (bỏ qua nếu chính lab đang chiếm)
for p in 3000 9090 9042 27017 8080; do
  if ss -ltnH "sport = :$p" 2>/dev/null | grep -q .; then
    owner=$(docker ps --filter "publish=$p" --format '{{.Names}}' | head -1)
    if [[ -n "$owner" ]]; then pass "Cổng $p đang do container lab '$owner' dùng"
    else wrn "Cổng $p đang bị tiến trình khác chiếm"; fi
  else
    pass "Cổng $p trống"
  fi
done

# 9. Công cụ phụ
for c in git curl python3; do
  if command -v "$c" >/dev/null; then pass "Có $c"; else fail "Thiếu $c (sudo apt install $c)"; fi
done
if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
  pass "Python $(python3 -c 'import platform; print(platform.python_version())')"
else
  fail "Cần Python ≥ 3.8"
fi
# scylla-monitoring sinh dashboard bằng make_dashboards.py (cần PyYAML)
if python3 -c 'import yaml' 2>/dev/null; then
  pass "Có PyYAML (scylla-monitoring cần để sinh dashboard)"
elif (( FIX )) && sudo apt-get install -y -q python3-yaml >/dev/null 2>&1; then
  pass "Đã cài python3-yaml"
else
  fail "Thiếu PyYAML → sudo apt install python3-yaml (hoặc chạy lại với --fix)"
fi

# 10. WSL có route được tới IP container không (chỉ kiểm khi node1 đang chạy)
if container_running scylla-node1 2>/dev/null; then
  if timeout 3 bash -c "exec 3<>/dev/tcp/$SCYLLA1_IP/9042" 2>/dev/null; then
    pass "Từ WSL kết nối thẳng được $SCYLLA1_IP:9042 → harness chạy trực tiếp trong WSL được"
  else
    wrn "Không kết nối được $SCYLLA1_IP:9042 từ WSL → chạy harness trong container trên mạng $LAB_NETWORK"
  fi
fi

# 11. Đồng hồ (mọi log so khớp theo epoch ms)
info "Giờ UTC của WSL: $(date -u '+%F %T'). So với đồng hồ Windows; lệch > 1s thì chạy: sudo hwclock -s"

banner "Kết quả: PASS=$PASS  WARN=$WARNS  FAIL=$FAILS"
(( FAILS == 0 ))
