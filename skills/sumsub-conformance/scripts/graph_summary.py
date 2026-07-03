#!/usr/bin/env python3
"""Print a clean, mapping-oriented summary of a config-graph.json — pure, no network.

USE THIS in the Map step instead of hand-iterating the graph JSON. The graph MIXES
shapes and ad-hoc probes keep crashing on that:
  - `level`, `workflow`        → objects (dicts)
  - `questionnaires`, `poaPresets`, `crossCheckPresets` → **dicts keyed by id** (iterating
    yields the id STRINGS, not objects — `for q in graph['questionnaires']` then `q.get(...)` crashes)
  - `entitlements`             → **list of strings** (no `.get`)

It prints questionnaire section/item INDICES + option scores — exactly what you need to fill
`match: {questionnaire, section, item}` + `expectScores`, plus docSets/fields/geo/workflow/entitlements.

  bash resolve_graph.sh <level> > cfg.json
  python3 graph_summary.py cfg.json        # or: ... | python3 graph_summary.py
"""
import json
import sys


def _txt(o):
    if isinstance(o, dict):
        for k in ("value", "text", "title", "label", "question", "name"):
            v = o.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return None


def _seq(coll):
    """(index, value) for a list; (key, value) for a dict — the form `match` uses."""
    if isinstance(coll, list):
        return list(enumerate(coll))
    if isinstance(coll, dict):
        return list(coll.items())
    return []


def main():
    raw = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    g = json.loads(raw)
    out = []

    lvl = g.get("level") or {}
    ri = lvl.get("requiredIdDocs") or {}
    out.append(f"LEVEL: {lvl.get('name')}  (id {lvl.get('id')})  websdkNext={lvl.get('websdkNext')}")
    inc = ri.get("includedCountries") or []
    out.append(f"  geo: includedCountries={len(inc)}{' '+str(inc[:6])+'…' if inc else ''}  "
               f"excludedCountries={ri.get('excludedCountries')}  rejectUsaResidents={lvl.get('rejectUsaResidents')}")
    out.append("  docSets:")
    for ds in ri.get("docSets") or []:
        t = ds.get("idDocSetType")
        extra = ""
        if t == "APPLICANT_DATA":
            extra = "  fields=" + str([f.get("name") for f in (ds.get("fields") or [])])
        elif str(t).startswith("SELFIE"):
            extra = f"  videoRequired={ds.get('videoRequired')}"
        elif ds.get("types"):
            extra = f"  types={ds.get('types')}"
        out.append(f"    - {t}{extra}")
    ents = g.get("entitlements")
    out.append(f"  entitlements (list): {ents}")

    out.append("QUESTIONNAIRES (dict keyed by id — use the [section]/[item] indices below for `match`):")
    for qid, q in _seq(g.get("questionnaires")):
        if not isinstance(q, dict) or q.get("_error"):
            err = q.get("_error") if isinstance(q, dict) else "?"
            out.append(f"  {qid}: UNRESOLVED ({err})")
            continue
        out.append(f"  «{qid}» — {_txt(q) or ''}")
        for skey, sec in _seq(q.get("sections")):
            out.append(f"    section[{skey}]: {_txt(sec) or ''}")
            items = sec.get("items") if isinstance(sec, dict) else None
            for ikey, item in _seq(items):
                labs = [f"{_txt(ov) or okey}={ov.get('score') if isinstance(ov, dict) else ''}"
                        for okey, ov in _seq(item.get("options") if isinstance(item, dict) else None)]
                out.append(f"      item[{ikey}] ({item.get('type') if isinstance(item, dict) else '?'}): {_txt(item) or ''}")
                if labs:
                    out.append(f"          options: {labs}")

    for label in ("poaPresets", "crossCheckPresets"):
        d = g.get(label) or {}
        ids = [f"{k}{'(UNRESOLVED)' if isinstance(v, dict) and v.get('_error') else ''}" for k, v in d.items()]
        out.append(f"  {label}: {ids}")

    wf = g.get("workflow") or {}
    if wf:
        out.append(f"WORKFLOW: «{wf.get('title') or wf.get('name')}»  "
                   f"nodes={len(wf.get('nodes') or [])} edges={len(wf.get('edges') or [])}")
        for n in wf.get("nodes") or []:
            lname = (n.get("applicantLevel") or {}).get("levelName")
            out.append(f"    node {n.get('id')} ({n.get('type')}){' → level '+lname if lname else ''}")
        for e in wf.get("edges") or []:
            cond = json.dumps(e.get("condition")) if e.get("condition") else "—"
            out.append(f"    edge {e.get('from')} → {e.get('to')}  when={cond[:200]}")
    else:
        out.append("WORKFLOW: none")

    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
