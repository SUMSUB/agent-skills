#!/usr/bin/env bash
# Resolve a level's FULL deployed config graph for a conformance trace, as one JSON.
#
# Emits (stdout):
#   {
#     "level": {...ApplicantLevel...},
#     "questionnaires": { "<id>": {...full definition incl. per-option scores...} | {"_error": <http>} },
#     "poaPresets":     { "<id>": {...} | {"_error": <http>} },
#     "crossCheckPresets": { "<id>": {...} | {"_error": <http>} },
#     "workflow": {...full workflow incl. nodes/edges/conditions...} | null,
#     "entitlements": ["POA", "QUESTIONNAIRE", ...]    # allowedChecks keys, [] if unfetchable
#   }
#
# The workflow is AUTO-FOUND: the one whose nodes reference this level (no need to
# pass an id). Questionnaires are pulled in full (content + scores) — the trace needs them.
#
# Usage: resolve_graph.sh <levelNameOrId>
# Requires SUMSUB_APP_TOKEN (sbx:) + SUMSUB_SECRET_KEY. All HTTP via sumsub_curl.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURL="${SUMSUB_CURL:-$SCRIPT_DIR/sumsub_curl.sh}"
LEVEL_SEL="${1:?usage: resolve_graph.sh <levelNameOrId>}"

: "${SUMSUB_APP_TOKEN:?set SUMSUB_APP_TOKEN}" "${SUMSUB_SECRET_KEY:?set SUMSUB_SECRET_KEY}"
if [[ "${SUMSUB_ENV:-}" == "dev" && -z "${SUMSUB_BASE:-}" ]]; then
  export SUMSUB_BASE="https://dev-api.sumsub.com"
fi

# Pre-fetch the collections that have list endpoints; python resolves the rest by id.
LEVELS_JSON="$(bash "$CURL" GET "/resources/applicants/-/levels" 2>/dev/null)"
WORKFLOWS_JSON="$(bash "$CURL" GET "/resources/api/applicantWorkflows" 2>/dev/null)"
ENTITLEMENTS_RAW="$(bash "$CURL" GET "/resources/api/agent/settings/bgCheckTargets" 2>/dev/null || true)"

LEVEL_SEL="$LEVEL_SEL" LEVELS_JSON="$LEVELS_JSON" WORKFLOWS_JSON="$WORKFLOWS_JSON" \
ENTITLEMENTS_RAW="$ENTITLEMENTS_RAW" \
python3 - "$CURL" <<'PY'
import json, os, subprocess, sys

curl = sys.argv[1]
sel = os.environ["LEVEL_SEL"]


def strip_http(text):
    lines = text.splitlines()
    if lines and lines[-1].startswith("HTTP "):
        code = lines[-1].split()[1] if len(lines[-1].split()) > 1 else "?"
        return "\n".join(lines[:-1]), code
    return text, "?"


def get(path):
    out = subprocess.run(["bash", curl, "GET", path], capture_output=True, text=True)
    body, code = strip_http(out.stdout)
    try:
        return json.loads(body), code
    except Exception:
        return None, code


def parse_env(name):
    try:
        body, _ = strip_http(os.environ.get(name, ""))
        return json.loads(body)
    except Exception:
        return None


def items_of(doc):
    if isinstance(doc, dict):
        lst = doc.get("list")
        if isinstance(lst, dict) and isinstance(lst.get("items"), list):
            return lst["items"]
        if isinstance(doc.get("items"), list):
            return doc["items"]
    return doc if isinstance(doc, list) else []


# --- level ---
levels = items_of(parse_env("LEVELS_JSON"))
level = next((lv for lv in levels
             if lv.get("name") == sel or str(lv.get("id")) == sel or str(lv.get("_id")) == sel), None)
if level is None:
    sys.stderr.write(f"error: level '{sel}' not found among {len(levels)} levels\n")
    sys.exit(4)
level_name = level.get("name")
docsets = ((level.get("requiredIdDocs") or {}).get("docSets")) or []

# --- referenced entities by id (full content) ---
questionnaires, poa, crosscheck = {}, {}, {}


def resolve(bucket, path, key):
    key = str(key)
    if key in bucket:
        return
    doc, code = get(path)
    bucket[key] = doc if (doc is not None and code.startswith("2")) else {"_error": code}


for ds in docsets:
    qid = ds.get("questionnaireDefId") or ds.get("questionnaireId")
    if qid:
        resolve(questionnaires, f"/resources/api/questionnaires/{qid}", qid)
    pid = ds.get("poaStepSettingsId")
    if pid:
        resolve(poa, f"/resources/api/poaStepSettings/{pid}", pid)
cc = level.get("crossCheckPresetId")
if cc:
    resolve(crosscheck, f"/resources/api/crossCheckPresets/{cc}", cc)

# --- auto-find the workflow that references this level ---
workflow = None
for wf in items_of(parse_env("WORKFLOWS_JSON")):
    for n in (wf.get("nodes") or []):
        lvl = (n.get("applicantLevel") or {}).get("levelName")
        if lvl == level_name:
            full, code = get(f"/resources/api/applicantWorkflows/{wf.get('id')}")
            workflow = full if (full and code.startswith("2")) else wf
            break
    if workflow:
        break

# --- entitlements (allowedChecks keys) ---
ent = []
ed = parse_env("ENTITLEMENTS_RAW")
if isinstance(ed, dict) and isinstance(ed.get("allowedChecks"), dict):
    ent = sorted(ed["allowedChecks"].keys())

json.dump({
    "level": level,
    "questionnaires": questionnaires,
    "poaPresets": poa,
    "crossCheckPresets": crosscheck,
    "workflow": workflow,
    "entitlements": ent,
}, sys.stdout, indent=2, ensure_ascii=False)
sys.stdout.write("\n")
PY
