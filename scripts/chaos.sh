#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/../lib/common.sh"

case "$1" in
  partition)
    target="$2"
    docker network disconnect lab-net "$target" 2>/dev/null || true
    echo "PARTITION: $target disconnected"
    ;;
  heal)
    target="$2"
    docker network connect lab-net "$target" 2>/dev/null || true
    echo "HEAL: $target reconnected"
    ;;
  reset)
    echo "RESET: Nothing to reset in stub"
    ;;
  *)
    echo "Usage: $0 {partition|heal|reset} <target>"
    exit 1
    ;;
esac
