#!/usr/bin/env bash
# Create or update a KYT tag.
# Usage: post_kyt_tag.sh [PAYLOAD_FILE|-]
#   Reads JSON payload from a file or stdin ("-" or omit for stdin).
#   Payload: {"tag": {"name": "...", "styleClass": "...", "color": "#RRGGBBAA",
#                     "scorable": true, "includeInReporting": true, "scoreWeight": 1.0}}
#   color must be an 8-digit hex value (#RRGGBBAA). All tag fields are optional except name.
#   Requires manageKytSettings permission.
#
# Exit codes:
#   0 — HTTP 200; response is empty (void).
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

exec bash "$SCRIPT_DIR/sumsub_curl.sh" POST "/resources/api/agent/tm/settings/tag" "${BODY_TMP}"
