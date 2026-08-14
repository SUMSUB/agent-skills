#!/usr/bin/env bash
# Manage tags on a Sumsub applicant profile.
#
# Usage:
#   manage_applicant_tags.sh list      <applicantId>
#   manage_applicant_tags.sh add       <applicantId> <tag> [<tag>...]   # additive (POST /tags/add)
#   manage_applicant_tags.sh overwrite <applicantId> <tag> [<tag>...]   # REPLACES the full set (POST /tags)
#   manage_applicant_tags.sh remove    <applicantId> <tag> [<tag>...]   # DELETE /tags
#
# `overwrite` is destructive — the caller must have shown the current tags to
# the user and gotten explicit confirmation BEFORE running it (see SKILL.md).
# Every write is followed by a read-back (GET /one) so the caller can compare.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${SUMSUB_APP_TOKEN:?set SUMSUB_APP_TOKEN}" "${SUMSUB_SECRET_KEY:?set SUMSUB_SECRET_KEY}"

if [[ $# -lt 2 ]]; then
  sed -n '2,12p' "$0" >&2
  exit 2
fi

CMD="$1"
APPLICANT_ID="$2"
shift 2

tags_json() {
  python3 -c 'import json, sys; print(json.dumps(sys.argv[1:]))' "$@"
}

read_back() {
  bash "$SCRIPT_DIR/sumsub_curl.sh" GET "/resources/applicants/${APPLICANT_ID}/one" \
    | python3 -c '
import json, sys
a = json.load(sys.stdin)
if "id" not in a:
    print(json.dumps(a, indent=2))
    sys.exit(1)
fixed = a.get("fixedInfo") or a.get("info") or {}
name = " ".join(p for p in (fixed.get("firstName"), fixed.get("lastName")) if p)
print("name=" + (name or a.get("externalUserId") or "(no name)"))
print("externalUserId=" + str(a.get("externalUserId", "")))
tags = a.get("tags", [])
if tags:
    print("tags=" + json.dumps(tags))
else:
    print("tags=[]  # tags field is absent when the set is empty")
print("clientId=" + str(a.get("clientId", "")))
print("id=" + str(a.get("id", "")))
'
}

write_tags() { # method path — tag names in "$@"
  local method="$1" path="$2"
  shift 2
  if [[ $# -lt 1 ]]; then
    echo "error: at least one tag name required" >&2
    exit 2
  fi
  tags_json "$@" | bash "$SCRIPT_DIR/sumsub_curl.sh" "$method" "$path" -
  echo
  echo "--- read-back ---"
  read_back
}

case "$CMD" in
  list)
    read_back
    ;;
  add)
    write_tags POST "/resources/applicants/${APPLICANT_ID}/tags/add" "$@"
    ;;
  overwrite)
    write_tags POST "/resources/applicants/${APPLICANT_ID}/tags" "$@"
    ;;
  remove)
    write_tags DELETE "/resources/applicants/${APPLICANT_ID}/tags" "$@"
    ;;
  *)
    echo "error: unknown subcommand '$CMD' (list | add | overwrite | remove)" >&2
    exit 2
    ;;
esac
