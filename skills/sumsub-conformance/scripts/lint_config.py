#!/usr/bin/env python3
"""Lint a resolved Sumsub config graph for misconfigurations and entitlement gaps.

Pure transformation — no network, no auth. Reads a config graph JSON on stdin
(as emitted by resolve_graph.sh; entitlements are read from graph.entitlements, or
pass an optional --entitlements file) and writes a findings report JSON to stdout.

Input graph shape:
  {
    "level": { ...ApplicantLevel... },
    "workflow": { ... } | null,
    "questionnaires": { "<id>": {...} | {"_error": "404"} },
    "poaPresets":     { "<id>": {...} | {"_error": "404"} },
    "crossCheckPresets": { "<id>": {...} | {"_error": "404"} }
  }

Entitlements file (optional, via --entitlements PATH): {"allowed": ["POA", ...]}.
When absent, entitlement-dependent rules emit severity "unknown" instead of "error".

Output:
  {
    "level": "<name>",
    "summary": {"error": N, "warn": N, "info": N, "unknown": N},
    "findings": [ {severity, rule, entity, message, fix}, ... ]
  }

Each rule mirrors a hard-won constraint documented in CLAUDE.md / the level &
PoA schema references. See references/lint-rules.md for the human catalog.
"""
import json
import os
import sys

# --- rule data + registry: single source of truth in references/rules.json ---
# Edit that file (not this one) to add lookup data or a rule's severity/fix.

_RULES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "references", "rules.json"
)
with open(_RULES_PATH) as _fh:
    _SPEC = json.load(_fh)

LOOKUPS = _SPEC["lookups"]
RULES = _SPEC["rules"]

VALID_AML_PROVIDERS = set(LOOKUPS["amlProviders"])
VALID_POA_PROVIDER_CATEGORIES = set(LOOKUPS["poaProviderCategories"])
DISCOURAGED_SELFIE_LIVENESS = set(LOOKUPS["discouragedSelfieLiveness"])
# docSet idDocSetType -> set of entitlements that satisfy it (any one suffices).
DOCSET_ENTITLEMENTS = {k: set(v) for k, v in LOOKUPS["docsetEntitlements"].items()}


def finding(rule, entity, message, severity=None, fix=None):
    """Build a finding. severity/fix default to the rule's registry entry; pass
    them explicitly only for dynamic cases (e.g. the entitlement gate's
    error/unknown split, or a fix that names the offending values).

    Raises if `rule` is not registered — a built-in guard against an unregistered
    rule id leaking out of the linter.
    """
    meta = RULES.get(rule)
    if meta is None:
        raise KeyError(f"unregistered rule id: {rule!r} (add it to references/rules.json)")
    return {
        "severity": severity if severity is not None else meta["severity"],
        "rule": rule,
        "entity": entity,
        "message": message,
        "fix": fix if fix is not None else meta["fix"],
    }


def lint(graph, allowed):
    """allowed: set[str] of entitlements, or None when unknown."""
    findings = []
    level = graph.get("level") or {}
    name = level.get("name", "<unknown level>")
    docsets = (((level.get("requiredIdDocs") or {}).get("docSets")) or [])

    # --- entitlement gates per docSet ---
    for ds in docsets:
        t = ds.get("idDocSetType")
        needed = DOCSET_ENTITLEMENTS.get(t)
        if not needed:
            continue
        if allowed is None:
            findings.append(finding(
                "docset-entitlement-mismatch", name,
                f"Step «{t}» needs one of {sorted(needed)}; entitlements could not be fetched.",
                severity="unknown",
                fix="Run sumsub-check-permissions and re-audit, or confirm the entitlement with your CSM.",
            ))
        elif not (needed & allowed):
            findings.append(finding(
                "docset-entitlement-mismatch", name,
                f"Step «{t}» requires one of {sorted(needed)}, none present in tenant entitlements.",
                fix=f"Contact your CSM to enable one of {sorted(needed)}, or drop the «{t}» step.",
            ))

    # --- device intelligence silently downgraded ---
    # Only fires on an explicit enabled:true (the silent-downgrade gotcha). A bare
    # DEVICE_CHECK docSet without the entitlement is already covered by
    # docset-entitlement-mismatch above, so we don't double-report it here.
    dev = level.get("deviceIntelligenceSettings") or {}
    if dev.get("enabled") is True:
        if allowed is None:
            findings.append(finding(
                "device-intelligence-no-entitlement", name,
                "deviceIntelligenceSettings.enabled is on but entitlements are unknown.",
                severity="unknown",
            ))
        elif "DEVICE_INTELLIGENCE" not in allowed:
            findings.append(finding(
                "device-intelligence-no-entitlement", name,
                "deviceIntelligenceSettings.enabled:true but DEVICE_INTELLIGENCE entitlement is missing — "
                "the API accepts it and returns 200 but stores enabled:false.",
            ))

    # --- AML provider gate ---
    wl = level.get("watchListCheckSettings") or {}
    aml = wl.get("amlCaseType")
    if aml is not None and aml not in VALID_AML_PROVIDERS:
        findings.append(finding(
            "aml-provider-invalid", name,
            f"watchListCheckSettings.amlCaseType «{aml}» is not a known provider.",
            fix=f"Use one of {sorted(VALID_AML_PROVIDERS)}, or omit it to inherit the tenant default.",
        ))
    if wl.get("useCustomWatchListCheckSettings") is True or aml is not None:
        findings.append(finding(
            "aml-custom-watchlist-gated", name,
            "Custom AML/watchlist settings are set. The AML provider is tenant-gated — "
            "an unprovisioned provider makes the level POST fail with 400, or settings are dropped.",
        ))

    # --- per-docSet structural rules ---
    seen_types = {}
    for ds in docsets:
        t = ds.get("idDocSetType")
        # PoA preset wiring
        if t and t.startswith("PROOF_OF_RESIDENCE"):
            pid = ds.get("poaStepSettingsId")
            if not pid:
                findings.append(finding(
                    "poa-preset-missing", name,
                    f"Step «{t}» has no poaStepSettingsId — the server rejects the level (\"PoA preset can't be null\").",
                ))
            elif _unresolved(graph.get("poaPresets", {}), pid):
                findings.append(finding(
                    "poa-preset-unresolved", name,
                    f"Step «{t}» references PoA preset id {pid}, which did not resolve (deleted or wrong env).",
                ))
        # Questionnaire wiring
        if t and t.startswith("QUESTIONNAIRE"):
            qid = ds.get("questionnaireDefId") or ds.get("questionnaireId")
            if not qid:
                findings.append(finding(
                    "questionnaire-missing", name,
                    f"Step «{t}» has no questionnaireDefId — it will silently do nothing in the SDK.",
                ))
            elif _unresolved(graph.get("questionnaires", {}), qid):
                findings.append(finding(
                    "questionnaire-unresolved", name,
                    f"Step «{t}» references questionnaire id {qid}, which did not resolve (GET 404).",
                ))
        # Selfie liveness
        if t and t.startswith("SELFIE"):
            vr = ds.get("videoRequired")
            if vr is None:
                findings.append(finding(
                    "selfie-no-liveness", name,
                    f"Step «{t}» has no videoRequired set — liveness behaviour is undefined.",
                ))
            elif vr in DISCOURAGED_SELFIE_LIVENESS:
                findings.append(finding(
                    "selfie-deprecated-liveness", name,
                    f"Step «{t}» uses deprecated/discouraged videoRequired:{vr}.",
                ))
        # NB: captureParams is intentionally NOT linted. It is @Transient and the
        # server DERIVES it on every read, so an audit (which reads config back)
        # always sees it — flagging it would fire on every healthy level.

        # count exact-type occurrences for the duplicate check
        if t:
            seen_types[t] = seen_types.get(t, 0) + 1

    # Any exact-type repeat is rejected by Sumsub — additional captures must use a
    # distinct numbered type (IDENTITY2, QUESTIONNAIRE2…), which is a different
    # string and so never collides here. No type is exempt from this.
    for t, cnt in seen_types.items():
        if cnt > 1:
            findings.append(finding(
                "duplicate-docset-type", name,
                f"idDocSetType «{t}» appears {cnt} times — Sumsub rejects duplicate steps of the same type.",
            ))

    # --- PoA preset internal: provider category keys ---
    for pid, preset in (graph.get("poaPresets") or {}).items():
        if not isinstance(preset, dict) or preset.get("_error"):
            continue
        ats = preset.get("allowedTypesSettings")
        if isinstance(ats, dict):
            bad = [k for k in ats.keys() if k not in VALID_POA_PROVIDER_CATEGORIES]
            if bad:
                findings.append(finding(
                    "poa-allowed-types-bad-keys", preset.get("name", pid),
                    f"PoA preset allowedTypesSettings has non-provider keys {bad}.",
                    fix=f"Keys must be provider categories: {sorted(VALID_POA_PROVIDER_CATEGORIES)} (not document sub-types).",
                ))

    # --- legacy SDK ---
    if level.get("websdkNext") is not True:
        findings.append(finding(
            "legacy-websdk", name,
            "websdkNext is not true — the level stays on the deprecated WebSDK 1.0.",
        ))

    # --- workflow heuristic: high-risk routing without PEP/AML branch ---
    wf = graph.get("workflow")
    if isinstance(wf, dict) and wf:
        blob = json.dumps(wf).lower()
        mentions_high_risk = "country" in blob and ("excluded" in blob or "high" in blob or "risk" in blob)
        mentions_aml = "aml" in blob or "pep" in blob or "watchlist" in blob or "sanction" in blob
        if mentions_high_risk and not mentions_aml:
            findings.append(finding(
                "workflow-high-risk-no-pep-aml",
                wf.get("name", "<workflow>"),
                "Workflow routes on country/risk but shows no PEP/AML/watchlist branch.",
            ))

    return findings


def _unresolved(bucket, key):
    """True if key is missing from bucket or its entry is an error marker."""
    entry = bucket.get(str(key)) if bucket else None
    if entry is None:
        return True
    if isinstance(entry, dict) and entry.get("_error"):
        return True
    return False


def _load_entitlements(path):
    """Read a check-permissions output file -> set of allowed entitlements.

    Tolerant of the trailing 'HTTP <code>' line that sumsub_curl.sh / the
    check-permissions script append, so the agent can feed that output directly.
    """
    with open(path) as fh:
        lines = fh.read().splitlines()
    if lines and lines[-1].startswith("HTTP "):
        lines = lines[:-1]
    data = json.loads("\n".join(lines))
    # check-permissions returns {"allowedChecks": {KEY: label, ...}} — the KEYS are
    # the granted entitlements. (Fall back to a flat "allowed" list if present.)
    checks = data.get("allowedChecks")
    if isinstance(checks, dict):
        return set(checks.keys())
    return set(data.get("allowed") or [])


def main():
    allowed = None
    argv = sys.argv[1:]
    if "--entitlements" in argv:
        allowed = _load_entitlements(argv[argv.index("--entitlements") + 1])

    graph = json.load(sys.stdin)
    # resolve_graph.sh embeds entitlements (allowedChecks keys) in the graph, so the
    # hygiene pass runs as `resolve_graph.sh X | lint_config.py` with no separate file.
    if allowed is None and isinstance(graph.get("entitlements"), list):
        allowed = set(graph["entitlements"])
    findings = lint(graph, allowed)

    summary = {"error": 0, "warn": 0, "info": 0, "unknown": 0}
    for f in findings:
        summary[f["severity"]] = summary.get(f["severity"], 0) + 1

    order = {"error": 0, "unknown": 1, "warn": 2, "info": 3}
    findings.sort(key=lambda f: order.get(f["severity"], 9))

    out = {
        "level": (graph.get("level") or {}).get("name", "<unknown level>"),
        "summary": summary,
        "findings": findings,
    }
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
