#!/usr/bin/env bash
# List all KYT tags with their assessment configuration and linked rules.
# Usage: get_kyt_tags.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${SUMSUB_APP_TOKEN:?}" "${SUMSUB_SECRET_KEY:?}"

exec bash "$SCRIPT_DIR/sumsub_curl.sh" GET "/resources/api/agent/tm/settings/tags"
