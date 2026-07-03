#!/usr/bin/env bash
# Create a KYT rule.
# Usage: post_kyt_rule.sh [PAYLOAD_FILE|-]
#   Reads JSON payload from a file or stdin ("-" or omit for stdin).
#   The payload is the rule object; this script wraps it in the request
#   envelope: {"rule": <payload>, "metadata": {"source": "aiAgent"}}.
#
# Exit codes:
#   0 — HTTP 200; response body is KytTxnRuleView JSON (created rule).
#   1 — HTTP 4xx/5xx; response body contains the error message, HTTP status on stderr.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${SUMSUB_APP_TOKEN:?}" "${SUMSUB_SECRET_KEY:?}"

BODY_ARG="${1:--}"
RULE_TMP="$(mktemp)"
trap 'rm -f "${RULE_TMP}"' EXIT

if [[ "${BODY_ARG}" == "-" ]]; then
  cat >"${RULE_TMP}"
else
  cp "${BODY_ARG}" "${RULE_TMP}"
fi

WRAPPED_TMP="$(mktemp)"
trap 'rm -f "${RULE_TMP}" "${WRAPPED_TMP}"' EXIT
python3 -c "
import json, sys
rule = json.load(open(sys.argv[1]))
print(json.dumps({'rule': rule, 'metadata': {'source': 'aiAgent'}}))
" "${RULE_TMP}" >"${WRAPPED_TMP}"

exec bash "$SCRIPT_DIR/sumsub_curl.sh" POST "/resources/api/agent/tm/rules" "${WRAPPED_TMP}"
