#!/usr/bin/env python3
"""Offline unit test for lint_config.py — no network, no creds.

Runs the linter against the clean and dirty example graphs and asserts the
expected rule set. Exit 0 = pass, 1 = fail.

    python3 scripts/test_lint.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLES = os.path.join(HERE, "..", "examples")
sys.path.insert(0, HERE)
import lint_config  # noqa: E402


def load(name):
    with open(os.path.join(EXAMPLES, name)) as fh:
        return json.load(fh)


def rule_ids(findings):
    return {f["rule"] for f in findings}


def main():
    failures = []

    # 1) clean graph + the entitlements it needs -> no error/warn
    clean = lint_config.lint(load("audit-input.json"), allowed={"POA", "QUESTIONNAIRE"})
    bad = [f for f in clean if f["severity"] in ("error", "warn")]
    if bad:
        failures.append(f"clean graph produced {len(bad)} error/warn findings: {rule_ids(bad)}")

    # 2) dirty graph + empty entitlements -> every expected rule fires
    dirty = lint_config.lint(load("audit-input-dirty.json"), allowed=set())
    got = rule_ids(dirty)
    expected = {
        "docset-entitlement-mismatch",
        "device-intelligence-no-entitlement",
        "aml-provider-invalid",
        "aml-custom-watchlist-gated",
        "poa-preset-missing",
        "questionnaire-unresolved",
        "selfie-no-liveness",
        "duplicate-docset-type",
        "poa-allowed-types-bad-keys",
        "legacy-websdk",
    }
    missing = expected - got
    if missing:
        failures.append(f"dirty graph missing expected rules: {sorted(missing)}")

    # 3) unknown entitlements -> gate rules degrade to 'unknown', not 'error'
    unknown = lint_config.lint(load("audit-input-dirty.json"), allowed=None)
    gate = [f for f in unknown if f["rule"] == "docset-entitlement-mismatch"]
    if gate and any(f["severity"] != "unknown" for f in gate):
        failures.append("entitlement gate did not degrade to 'unknown' when entitlements absent")

    # 4) exact-type duplicate of a "repeatable-family" type still fires (regression
    #    guard for the dropped REPEATABLE_PREFIXES exemption — two IDENTITY is invalid).
    dup_graph = {"level": {"name": "dup", "websdkNext": True, "requiredIdDocs": {"docSets": [
        {"idDocSetType": "IDENTITY", "types": ["PASSPORT"], "videoRequired": "docapture"},
        {"idDocSetType": "IDENTITY", "types": ["ID_CARD"], "videoRequired": "docapture"},
    ]}}}
    if "duplicate-docset-type" not in rule_ids(lint_config.lint(dup_graph, allowed=set())):
        failures.append("duplicate IDENTITY docSets not flagged (REPEATABLE exemption regression)")

    # 5) discouraged selfie videoRequired value is flagged (not silently passed).
    selfie_graph = {"level": {"name": "s", "websdkNext": True, "requiredIdDocs": {"docSets": [
        {"idDocSetType": "SELFIE", "videoRequired": "disabled"},
    ]}}}
    if "selfie-deprecated-liveness" not in rule_ids(lint_config.lint(selfie_graph, allowed=set())):
        failures.append("selfie videoRequired:disabled not flagged")

    # 6) CHAINLINK_ATTESTATION is entitlement-gated like its SOLANA/LINEA siblings.
    chain_graph = {"level": {"name": "c", "websdkNext": True, "requiredIdDocs": {"docSets": [
        {"idDocSetType": "CHAINLINK_ATTESTATION"},
    ]}}}
    if "docset-entitlement-mismatch" not in rule_ids(lint_config.lint(chain_graph, allowed=set())):
        failures.append("CHAINLINK_ATTESTATION not entitlement-gated")

    # 7) entitlements loader reads allowedChecks keys and tolerates a trailing HTTP line
    #    (regression guard for the live false-positive: wrong field -> empty -> all-ERROR).
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        tf.write('{"allowedChecks": {"POA": "Proof of address", "QUESTIONNAIRE": "Q"}}\nHTTP 200\n')
        ent_path = tf.name
    loaded = lint_config._load_entitlements(ent_path)
    os.unlink(ent_path)
    if loaded != {"POA", "QUESTIONNAIRE"}:
        failures.append(f"_load_entitlements should read allowedChecks keys, got {loaded}")

    # 8) registry drift: every rule id emitted by lint_config.py must be registered
    #    in rules.json, and vice versa (no orphan rules in either direction).
    import re
    with open(os.path.join(HERE, "lint_config.py")) as fh:
        src = fh.read()
    code_ids = set(re.findall(r'finding\(\s*"([^"]+)"', src))
    registry_ids = set(lint_config.RULES.keys())
    if code_ids != registry_ids:
        failures.append(
            f"rule-id drift: only-in-code={sorted(code_ids - registry_ids)} "
            f"only-in-rules.json={sorted(registry_ids - code_ids)}"
        )

    # 9) doc drift: lint-rules.md must equal what gen_lint_docs renders from rules.json.
    import gen_lint_docs
    with open(gen_lint_docs.DOC_MD) as fh:
        doc = fh.read()
    if gen_lint_docs.render(doc, gen_lint_docs.load_spec()) != doc:
        failures.append("lint-rules.md is out of sync — run python3 scripts/gen_lint_docs.py")

    if failures:
        print("FAIL")
        for f in failures:
            print("  -", f)
        return 1
    print("PASS — clean=0 err/warn, dirty fires all expected rules, gate degrades to unknown")
    return 0


if __name__ == "__main__":
    sys.exit(main())
