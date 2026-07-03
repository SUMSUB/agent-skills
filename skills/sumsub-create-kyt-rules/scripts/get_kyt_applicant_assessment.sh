#!/usr/bin/env bash
# Get current applicant assessment scoring configuration.
# Usage: get_kyt_applicant_assessment.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${SUMSUB_APP_TOKEN:?}" "${SUMSUB_SECRET_KEY:?}"

exec bash "$SCRIPT_DIR/sumsub_curl.sh" GET "/resources/api/agent/tm/settings/applicantAssessment"
