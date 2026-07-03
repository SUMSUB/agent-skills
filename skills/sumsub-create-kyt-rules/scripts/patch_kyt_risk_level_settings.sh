#!/usr/bin/env bash
# Update applicant risk level settings.
# Usage: patch_kyt_risk_level_settings.sh [PAYLOAD_FILE|-]
#   Reads JSON payload from a file or stdin ("-" or omit for stdin).
#   Payload: {"riskLevelThresholds": [{"label": "Low", "rangeFrom": 0, "styleClass": "green"}, ...]}
#   styleClass must be one of: grey, black, blue, green, cyan, teal, lime, yellow,
#                               orange, volcano, red, pink, fuchsia, purple, purpleLight
#   Requires at least 2 thresholds. Requires manageKytSettings permission.
#
# Exit codes:
#   0 — HTTP 200; response body is the updated ApplicantRiskLevelSettingsDto.
#   1 — HTTP 4xx/5xx; response body contains the error message, HTTP status on stderr.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${SUMSUB_APP_TOKEN:?}" "${SUMSUB_SECRET_KEY:?}"

BODY_ARG="${1:--}"
BODY_TMP="$(mktemp)"
trap 'rm -f "${BODY_TMP}"' EXIT

if [[ "${BODY_ARG}" == "-" ]]; then
  cat >"${BODY_TMP}"
else
  cp "${BODY_ARG}" "${BODY_TMP}"
fi

exec bash "$SCRIPT_DIR/sumsub_curl.sh" PATCH "/resources/api/agent/tm/settings/riskLevel" "${BODY_TMP}"
