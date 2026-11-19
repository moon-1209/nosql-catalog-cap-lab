#!/usr/bin/env bash
die() { echo "ERROR: $*" >&2; exit 1; }
info() { echo "INFO: $*"; }
warn() { echo "WARN: $*"; }
ok() { echo "OK: $*"; }
