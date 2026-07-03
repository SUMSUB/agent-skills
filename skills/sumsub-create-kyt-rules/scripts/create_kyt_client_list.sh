#!/usr/bin/env bash
# Create a KYT client list (idempotent — succeeds if it already exists).
# Usage: create_kyt_client_list.sh <listName>
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${SUMSUB_APP_TOKEN:?}" "${SUMSUB_SECRET_KEY:?}"

LIST_NAME="${1:?listName argument required}"
exec bash "$SCRIPT_DIR/sumsub_curl.sh" POST "/resources/api/agent/tm/clientLists/${LIST_NAME}"
