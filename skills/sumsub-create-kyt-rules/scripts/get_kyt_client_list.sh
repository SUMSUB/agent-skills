#!/usr/bin/env bash
# Get a KYT client list by name.
# Usage: get_kyt_client_list.sh <listName>
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${SUMSUB_APP_TOKEN:?}" "${SUMSUB_SECRET_KEY:?}"

LIST_NAME="${1:?listName argument required}"
exec bash "$SCRIPT_DIR/sumsub_curl.sh" GET "/resources/api/agent/tm/clientLists/${LIST_NAME}"
