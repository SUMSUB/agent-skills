#!/usr/bin/env python3
"""Conformance trace engine — pure, no network.

Inputs:
  - requirements (mapped) JSON  : the regulation's requirements, with the agent's
                                  question-mapping already filled in (see references/requirements-schema.md)
  - config graph JSON           : resolve_graph.sh output (level + questionnaires+scores + workflow + entitlements)

For each requirement it deterministically classifies into one bucket:
  MISSING                  — required block absent
  SCORING-MISMATCH         — question present but its option scores differ from the regulation
  COLLECTED-NOT-ENFORCED   — data collected/scored, but no workflow/scoring rule acts on it  ← the flagship
  NOT-CONFIG-REPRESENTABLE — outcome lives in SDK/platform/CRM (not checkable from Sumsub config)
  CONFORMANT               — collected + scored + enforced as specified

Every finding cites EVIDENCE and a BASIS (deterministic vs judgment). The question
matching is the agent's judgment (upstream); the score compare and the workflow
enforcement search done here are deterministic.

Usage:
  python3 trace.py --requirements req.json --graph config-graph.json
"""
import argparse
import json
import sys

BUCKETS = ["MISSING", "SCORING-MISMATCH", "COLLECTED-NOT-ENFORCED",
           "NOT-CONFIG-REPRESENTABLE", "CONFORMANT"]


def _walk_strings(node, out):
    """Collect every `exp` path and `lit` value from a workflow condition AST."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("exp", "lit") and isinstance(v, (str, int, float)):
                out.append(str(v))
            else:
                _walk_strings(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk_strings(v, out)


def enforcement_blob(graph):
    """Lowercased blob of everything the engine ACTS on: workflow edge conditions
    + any scoring config. This is where enforcement signals must appear."""
    toks = []
    wf = graph.get("workflow") or {}
    for e in (wf.get("edges") or []):
        _walk_strings(e.get("condition"), toks)
    # node-level conditions/actions + node id/type/name (so a signal can match a
    # routing TARGET like a finalRejection / manualReview node, not just edge conditions)
    for n in (wf.get("nodes") or []):
        for k in ("id", "type", "name"):
            v = n.get(k)
            if isinstance(v, str):
                toks.append(v)
        _walk_strings(n.get("condition"), toks)
        _walk_strings(n.get("actions"), toks)
    # a separate scoring config, if the graph carries one
    _walk_strings(graph.get("scoring"), toks)
    return " ".join(toks).lower()


def _item_at(graph, match):
    """Resolve a questionnaire item from a match {questionnaire, section, item}.
    Handles sections/items as either lists or dicts."""
    q = (graph.get("questionnaires") or {}).get(match.get("questionnaire"))
    if not isinstance(q, dict) or q.get("_error"):
        return None
    secs = q.get("sections")
    sec = _index(secs, match.get("section"))
    if sec is None:
        return None
    return _index(sec.get("items"), match.get("item")) if isinstance(sec, dict) else None


def _index(coll, key):
    if isinstance(coll, list):
        try:
            return coll[int(key)]
        except (ValueError, TypeError, IndexError):
            return None
    if isinstance(coll, dict):
        if key in coll:
            return coll[key]
        vals = list(coll.values())
        try:
            return vals[int(key)]
        except (ValueError, TypeError, IndexError):
            return None
    return None


def _deployed_scores(item):
    opts = item.get("options") if isinstance(item, dict) else None
    if isinstance(opts, list):
        return [o.get("score") for o in opts if isinstance(o, dict)]
    if isinstance(opts, dict):
        return [o.get("score") for o in opts.values() if isinstance(o, dict)]
    return None


LIVENESS_MODES = {"passiveliveness", "staticliveness", "liveness", "enabled"}


def _docsets(graph):
    return (((graph.get("level") or {}).get("requiredIdDocs") or {}).get("docSets")) or []


def _applicant_fields(graph):
    names = set()
    for d in _docsets(graph):
        if d.get("idDocSetType") == "APPLICANT_DATA":
            for f in (d.get("fields") or []):
                if f.get("name"):
                    names.add(str(f["name"]).lower())
    return names


def _country_admitted(level, iso):
    """Would an applicant resident in `iso` be admitted by the level's geo rules?"""
    iso = iso.upper()
    ri = level.get("requiredIdDocs") or {}
    inc = [c.upper() for c in (ri.get("includedCountries") or [])]
    exc = [c.upper() for c in (ri.get("excludedCountries") or [])]
    if iso in exc:
        return False
    if iso in ("USA", "US") and level.get("rejectUsaResidents") is True:
        return False
    if inc:  # allowlist present → admitted only if listed
        return iso in inc
    return True  # no allowlist, not excluded → admitted


def finding(req, bucket, evidence, basis):
    return {
        "id": req.get("id"),
        "source": req.get("source"),   # citation in the original document (§/page/heading)
        "text": req.get("text"),
        "type": req.get("type"),
        "enforceable": req.get("enforceable"),
        "bucket": bucket,
        "evidence": evidence,
        "basis": basis,
    }


def classify(req, graph, blob):
    enforceable = req.get("enforceable", "config")
    rtype = req.get("type")

    # 1) outcomes that simply cannot live in Sumsub config
    if enforceable in ("sdk", "platform"):
        examples = ("disclosure pop-up / demo / read-only / CRM" if enforceable == "sdk"
                    else "record-keeping / reporting / org process / runtime monitoring")
        return finding(req, "NOT-CONFIG-REPRESENTABLE",
                       f"Outcome is enforced in {enforceable} ({examples}), not Sumsub config — needs human review.",
                       "deterministic")

    # 2) data-collection requirements (a question must exist, optionally scored)
    if rtype in ("question", "scoring"):
        match = req.get("match")
        if not match:
            return finding(req, "MISSING",
                           "No deployed question/docSet was matched to this requirement.",
                           "judgment (agent mapping found no match)")
        # 2a) identity / document-collection requirement → check the level's docSets
        if "docSet" in match:
            want = match["docSet"]
            docsets = (((graph.get("level") or {}).get("requiredIdDocs") or {}).get("docSets")) or []
            ds = next((d for d in docsets if d.get("idDocSetType") == want), None)
            if ds is None:
                return finding(req, "MISSING",
                               f"Level has no «{want}» docSet — this data is not collected.",
                               "deterministic")
            need = match.get("types") or []
            have = set(ds.get("types") or [])
            missing_t = [t for t in need if t not in have]
            if missing_t:
                return finding(req, "MISSING",
                               f"«{want}» docSet present but missing required doc types {missing_t} (has {sorted(have)}).",
                               "deterministic")
            return finding(req, "CONFORMANT",
                           f"«{want}» docSet present" + (f" with required types {need}." if need else "."),
                           "deterministic")
        # 2b) questionnaire-item requirement
        item = _item_at(graph, match)
        if item is None:
            return finding(req, "MISSING",
                           f"Mapped question {match} did not resolve in the deployed questionnaire.",
                           "deterministic")
        expect = req.get("expectScores")
        if expect is not None:
            got = _deployed_scores(item)
            if got != expect:
                return finding(req, "SCORING-MISMATCH",
                               f"Deployed option scores {got} != regulation {expect} at {match}.",
                               "deterministic (given the agent's question mapping)")
        return finding(req, "CONFORMANT",
                       f"Question present and scoring matches regulation at {match}.",
                       "deterministic (given the agent's question mapping)")

    # 2c) entitlement presence — tenant must hold a capability
    if rtype == "entitlement":
        ents = set(graph.get("entitlements") or [])
        want = req.get("match", {}).get("entitlements") or req.get("match", {}).get("entitlement")
        want = [want] if isinstance(want, str) else (want or [])
        if not ents:
            return finding(req, "MISSING", "Tenant entitlements unknown/empty — cannot confirm the capability.", "deterministic")
        if any(w in ents for w in want):
            return finding(req, "CONFORMANT", f"Tenant holds entitlement(s) {[w for w in want if w in ents]}.", "deterministic")
        return finding(req, "MISSING", f"Tenant lacks required entitlement(s) {want} (has {sorted(ents)}).", "deterministic")

    # 2d) data-field collection — APPLICANT_DATA must collect named field(s)
    if rtype == "data-field":
        have = _applicant_fields(graph)
        want = req.get("match", {}).get("fields") or req.get("match", {}).get("field") or []
        want = [want] if isinstance(want, str) else want
        if not want:
            return finding(req, "COLLECTED-NOT-ENFORCED",
                           "Underspecified requirement: no field name(s) to check.", "judgment")
        missing = [f for f in want if f.lower() not in have]
        if missing:
            return finding(req, "MISSING", f"APPLICANT_DATA does not collect {missing} (collects {sorted(have)}).", "deterministic")
        return finding(req, "CONFORMANT", f"APPLICANT_DATA collects required field(s) {want}.", "deterministic")

    # 2e) liveness / biometric — SELFIE step must enforce a liveness mode
    if rtype == "liveness":
        selfie = next((d for d in _docsets(graph) if str(d.get("idDocSetType", "")).startswith("SELFIE")), None)
        if selfie is None:
            return finding(req, "MISSING", "No SELFIE step — biometric liveness is not collected.", "deterministic")
        vr = str(selfie.get("videoRequired") or "").lower()
        if vr in LIVENESS_MODES:
            return finding(req, "CONFORMANT", f"SELFIE enforces liveness (videoRequired={vr}).", "deterministic")
        return finding(req, "COLLECTED-NOT-ENFORCED",
                       f"SELFIE collected but videoRequired={vr or 'unset'} is not a liveness mode "
                       f"({sorted(LIVENESS_MODES)}).", "deterministic")

    # 2f) country eligibility — geographic allowlist / prohibited jurisdictions
    if rtype == "country-eligibility":
        level = graph.get("level") or {}
        m = req.get("match") or {}
        if m.get("mustHaveAllowlist"):
            ri = level.get("requiredIdDocs") or {}
            if (ri.get("includedCountries") or ri.get("excludedCountries") or level.get("rejectUsaResidents")):
                return finding(req, "CONFORMANT", "A geographic restriction is configured.", "deterministic")
            return finding(req, "MISSING", "No geographic restriction — the level admits all countries.", "deterministic")
        prohibit = [c.upper() for c in (m.get("mustExclude") or [])]
        if not prohibit:
            return finding(req, "COLLECTED-NOT-ENFORCED",
                           "Underspecified requirement: no mustHaveAllowlist/mustExclude criterion.", "judgment")
        admitted = [c for c in prohibit if _country_admitted(level, c)]
        if admitted:
            return finding(req, "MISSING", f"Prohibited jurisdiction(s) still admitted: {admitted}.", "deterministic")
        return finding(req, "CONFORMANT", f"Prohibited jurisdiction(s) {prohibit} are not admitted.", "deterministic")

    # 3) config-enforceable outcomes (screening / routing) — search the enforcement blob
    if rtype in ("screening", "routing-outcome"):
        signal = [s.lower() for s in (req.get("enforcementSignal") or [])]
        if not signal:
            return finding(req, "COLLECTED-NOT-ENFORCED",
                           "No enforcementSignal provided to locate this outcome in routing.",
                           "judgment (no signal)")
        present = [s for s in signal if s in blob]
        missing = [s for s in signal if s not in blob]
        if not missing:
            return finding(req, "CONFORMANT",
                           f"Workflow/scoring conditions reference all signal tokens {signal}.",
                           "deterministic")
        return finding(req, "COLLECTED-NOT-ENFORCED",
                       f"Data is collected, but routing references {present or 'none'} and is MISSING {missing} — "
                       "the outcome is not enforced.",
                       "deterministic")

    return finding(req, "COLLECTED-NOT-ENFORCED",
                   f"Unhandled requirement type {rtype!r}; cannot confirm enforcement.",
                   "judgment")


def trace(requirements_doc, graph):
    reqs = requirements_doc.get("requirements", [])
    blob = enforcement_blob(graph)
    findings = [classify(r, graph, blob) for r in reqs]
    summary = {b: 0 for b in BUCKETS}
    for f in findings:
        summary[f["bucket"]] = summary.get(f["bucket"], 0) + 1
    order = {b: i for i, b in enumerate(["MISSING", "SCORING-MISMATCH",
             "COLLECTED-NOT-ENFORCED", "NOT-CONFIG-REPRESENTABLE", "CONFORMANT"])}
    findings.sort(key=lambda f: order.get(f["bucket"], 9))
    return {
        "regulation": requirements_doc.get("regulation", "<regulation>"),
        "level": (graph.get("level") or {}).get("name", "<level>"),
        "summary": summary,
        "findings": findings,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--requirements", required=True)
    ap.add_argument("--graph", required=True)
    args = ap.parse_args()
    with open(args.requirements) as fh:
        reqs = json.load(fh)
    with open(args.graph) as fh:
        graph = json.load(fh)
    out = trace(reqs, graph)
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
