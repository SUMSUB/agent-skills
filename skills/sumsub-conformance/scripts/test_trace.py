#!/usr/bin/env python3
"""Offline unit test for trace.py — no network, no creds.

Asserts the trace engine puts each synthetic requirement in the right bucket, so
every bucket (incl. MISSING and SCORING-MISMATCH) is exercised. Exit 0 = pass.

    python3 scripts/test_trace.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLES = os.path.join(HERE, "..", "examples")
sys.path.insert(0, HERE)
import trace as trace_engine  # noqa: E402


def load(name):
    with open(os.path.join(EXAMPLES, name)) as fh:
        return json.load(fh)


def main():
    failures = []

    reqs = load("sample-requirements.json")
    graph = load("sample-graph.json")
    out = trace_engine.trace(reqs, graph)
    by_id = {f["id"]: f["bucket"] for f in out["findings"]}

    expected = {
        "scored-ok": "CONFORMANT",
        "scored-mismatch": "SCORING-MISMATCH",
        "absent-question": "MISSING",
        "aml-enforced": "CONFORMANT",
        "score-band-not-enforced": "COLLECTED-NOT-ENFORCED",
        "popup-disclosure": "NOT-CONFIG-REPRESENTABLE",
        "identity-docset-ok": "CONFORMANT",
        "company-docset-missing": "MISSING",
        "ent-present": "CONFORMANT",
        "ent-missing": "MISSING",
        "field-missing": "MISSING",
        "liveness-missing": "MISSING",
        "geo-missing": "MISSING",
    }
    for rid, want in expected.items():
        got = by_id.get(rid)
        if got != want:
            failures.append(f"{rid}: expected {want}, got {got}")

    # Guardrail property: trace only walks requirements -> deployment, never the
    # reverse, so a deployed question that is NOT in the regulation can never be
    # mis-flagged as a finding. Assert no finding references an unknown id.
    if set(by_id) != set(expected):
        failures.append(f"unexpected finding ids: {set(by_id) ^ set(expected)}")

    # Discriminating-signal guardrail: a generic token that happens to appear in a
    # catch-all edge must NOT make an unenforced outcome look enforced.
    blob = trace_engine.enforcement_blob(graph)
    if "country" not in blob:
        failures.append("test fixture changed: expected 'country' token in catch-all edge")
    probe = trace_engine.classify(
        {"id": "x", "type": "routing-outcome", "enforceable": "config",
         "enforcementSignal": ["albania"]}, graph, blob)
    if probe["bucket"] != "COLLECTED-NOT-ENFORCED":
        failures.append("discriminating-signal guardrail failed: high-risk-country override "
                        "should be COLLECTED-NOT-ENFORCED despite a generic 'country' token")

    # Canonical report renderer: produces Markdown with every bucket section + caveats.
    import report as report_mod
    md = report_mod.render(out)
    for needed in ("# Conformance report", "| Bucket | Count |", "## Findings", "## Caveats"):
        if needed not in md:
            failures.append(f"report.py missing section: {needed!r}")

    if failures:
        print("FAIL")
        for f in failures:
            print("  -", f)
        return 1
    print("PASS — all buckets exercised; guardrails hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
