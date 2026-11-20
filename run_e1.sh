#!/usr/bin/env bash
# =====================================================================
# run_e1.sh — chạy E1-A (Schema A) rồi E1-B (Schema B) với CÙNG kịch bản, rồi so sánh.
#   ./run_e1.sh --a shop.products_by_category --b shop.products_by_category_bucketed \
#               --harness-a "python3 ~/harness.py --schema A --duration {duration_s} --out {run_dir}/harness" \
#               --harness-b "python3 ~/harness.py --schema B --duration {duration_s} --out {run_dir}/harness"
#   ./run_e1.sh --self-test       #  dùng mini_load (zipf vs uniform)
#                                 # để kiểm tra pipeline đo → KHÔNG phải số liệu chính thức
# Mỗi lượt: chaos_runner (kịch bản e1_hot_partition, 300s, chụp toppartitions giây 120)
#           → hot_partition_audit (bỏ 60s warm-up) → cuối cùng so sánh A vs B.
# Kết quả: runs/E1-A_*/, runs/E1-B_*/ và evidence/tuan2/E1_compare_<thời_gian>.md
# =====================================================================
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/common.sh
source "$HERE/lib/common.sh"

A=""; B=""; HA="${E1_HARNESS_A:-}"; HB="${E1_HARNESS_B:-}"; SELF=0; COOLDOWN=60
while [[ $# -gt 0 ]]; do
  case "$1" in
    --a) A="$2"; shift 2 ;;
    --b) B="$2"; shift 2 ;;
    --harness-a) HA="$2"; shift 2 ;;
    --harness-b) HB="$2"; shift 2 ;;
    --self-test) SELF=1; shift ;;
    --cooldown) COOLDOWN="$2"; shift 2 ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    *) die "Tham số lạ: $1" ;;
  esac
done

if (( SELF )); then
  A="lab_load.kv"; B="lab_load.kv"
  LOAD="python3 $LAB_ROOT/lib/mini_load.py --create --rate 400 --duration {duration_s} --keys 5000"
  HA="$LOAD --dist zipf --zipf-s 1.3 --out {run_dir}/mini_load.csv"
  HB="$LOAD --dist uniform --out {run_dir}/mini_load.csv"
  warn "CHẾ ĐỘ TỰ KIỂM TRA: A = khóa Zipf, B = khóa đều trên cùng 1 bảng — chỉ để chứng minh pipeline đo hoạt động"
fi
[[ "$A" == *.* && "$B" == *.* ]] || die "Cần --a KS.BẢNG và --b KS.BẢNG (hoặc --self-test)"
[[ -n "$HA" && -n "$HB" ]] || warn "Không có lệnh harness → runner chỉ chạy kịch bản; phải bơm tải song song bằng tay"

SC="$HERE/scenarios/e1_hot_partition.json"
STAMP=$(stamp)
summaries=()
for v in A B; do
  if [[ $v == A ]]; then tbl="$A"; h="$HA"; else tbl="$B"; h="$HB"; fi
  ks="${tbl%%.*}"; cf="${tbl#*.}"
  run_id="E1-${v}_${STAMP}"
  banner "E1-$v  ($tbl)  run_id=$run_id"
  args=("$SC" --run-id "$run_id" --param "ks=$ks" --param "cf=$cf")
  [[ -n "$h" ]] && args+=(--harness-cmd "$h")
  python3 "$HERE/chaos_runner.py" "${args[@]}"
  python3 "$HERE/hot_partition_audit.py" --run "$RUNS_DIR/$run_id" --ks "$ks" --cf "$cf" --label "E1-$v"
  summaries+=("$RUNS_DIR/$run_id/hot_partition/hot_partition_summary.json")
  if [[ $v == A ]]; then info "Nghỉ ${COOLDOWN}s cho cụm về trạng thái nền..."; sleep "$COOLDOWN"; fi
done

mkdir -p "$EVIDENCE_DIR/tuan2"
python3 "$HERE/hot_partition_audit.py" compare "${summaries[@]}" --out "$EVIDENCE_DIR/tuan2/E1_compare_${STAMP}.md"
ok "Xong E1: runs/E1-*_${STAMP}/hot_partition/*.csv và toppartitions/*.csv"
