#!/usr/bin/env bash
# Get applicant risk level settings.
# Usage: get_kyt_risk_level_settings.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${SUMSUB_APP_TOKEN:?}" "${SUMSUB_SECRET_KEY:?}"

exec bash "$SCRIPT_DIR/sumsub_curl.sh" GET "/resources/api/agent/tm/settings/riskLevel"
