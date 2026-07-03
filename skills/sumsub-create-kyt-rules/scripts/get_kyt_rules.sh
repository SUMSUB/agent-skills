#!/usr/bin/env bash
# List KYT rules.
# Usage: get_kyt_rules.sh [--limit N] [--offset N]
#   Defaults: limit=50, offset=0
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${SUMSUB_APP_TOKEN:?}" "${SUMSUB_SECRET_KEY:?}"

LIMIT=50
OFFSET=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --limit)  LIMIT="$2";  shift 2 ;;
    --offset) OFFSET="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

exec bash "$SCRIPT_DIR/sumsub_curl.sh" GET "/resources/api/agent/tm/rules/-/installed?limit=${LIMIT}&offset=${OFFSET}"
