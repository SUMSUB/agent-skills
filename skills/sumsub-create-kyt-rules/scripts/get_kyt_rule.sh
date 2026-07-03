#!/usr/bin/env bash
# Get a single KYT rule by id.
# Usage: get_kyt_rule.sh RULE_ID
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${SUMSUB_APP_TOKEN:?}" "${SUMSUB_SECRET_KEY:?}"

RULE_ID="${1:?Usage: get_kyt_rule.sh RULE_ID}"
exec bash "$SCRIPT_DIR/sumsub_curl.sh" GET "/resources/api/agent/tm/rules/${RULE_ID}"
