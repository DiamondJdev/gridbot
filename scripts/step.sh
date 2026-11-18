#!/usr/bin/env bash
set -euo pipefail

if (( $# < 2 )); then
  printf 'Usage: %s <label> <command> [args...]\n' "$0" >&2
  exit 2
fi

label=$1
shift
slug=$(printf '%s' "$label" | LC_ALL=C tr '[:upper:]' '[:lower:]' | LC_ALL=C sed -E 's/[^a-z0-9]+/-/g; s/^-|-$//g')
mkdir -p artifacts/logs
log="artifacts/logs/${slug:-step}.log"

if "$@" > "$log" 2>&1; then
  printf '%s: passed\n' "$label"
else
  code=$?
  tail -n 40 "$log"
  printf '%s: FAILED (exit %d)\n' "$label" "$code"
  exit "$code"
fi
