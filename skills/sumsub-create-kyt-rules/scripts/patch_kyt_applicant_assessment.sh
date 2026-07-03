#!/usr/bin/env bash
# Replace applicant assessment scoring configuration.
# Usage: patch_kyt_applicant_assessment.sh [PAYLOAD_FILE|-]
#   Reads JSON payload from a file or stdin ("-" or omit for stdin).
#
#   Payload shape:
#   {
#     "scores": [
#       {
#         "id": "unique-id",          -- required
#         "tag": "TagName",           -- required; must match an existing KYT tag
#         "includeInTotalScore": true,
#         "scoreWeight": 1.0,
#         "styleClass": "red",        -- colour name (same values as riskLevel styleClass)
#         "color": "#FF000080",       -- hex #RRGGBBAA
#         "items": [...],             -- nested sub-scores (same structure, recursive)
#         "rules": [{"id": "...", "name": "...", "title": "..."}]
#       }
#     ],
#     "companyBeneficiarySettings": [
#       {
#         "beneficiaryType": "ubo",   -- one of: shareholder, representative, director, ubo,
#                                     --   companyOfficer, secretary, founder, investor,
#                                     --   legalAdvisor, authorizedSignatory, trustee,
#                                     --   trustBeneficiary, trustSettlor, trustProtector, payer
#         "weight": 1.0
#       }
#     ]
#   }
#   Requires manageKytSettings permission.
#
# Exit codes:
#   0 — HTTP 200; response body is the updated ApplicantAssessmentSettingsDto.
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

exec bash "$SCRIPT_DIR/sumsub_curl.sh" PATCH "/resources/api/agent/tm/settings/applicantAssessment" "${BODY_TMP}"
