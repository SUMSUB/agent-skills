#!/usr/bin/env bash
# List KYT rules in a bundle by name and installation status.
# Usage: get_kyt_bundle.sh <bundleName> <category>
#   category: installed | available | archived
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${SUMSUB_APP_TOKEN:?}" "${SUMSUB_SECRET_KEY:?}"

BUNDLE_NAME="${1:?Usage: get_kyt_bundle.sh BUNDLE_NAME CATEGORY}"
CATEGORY="${2:?Usage: get_kyt_bundle.sh BUNDLE_NAME CATEGORY}"

exec bash "$SCRIPT_DIR/sumsub_curl.sh" GET "/resources/api/agent/tm/rules/-/bundle/${BUNDLE_NAME}/${CATEGORY}"
