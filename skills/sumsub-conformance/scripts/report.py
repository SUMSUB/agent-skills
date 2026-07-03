#!/usr/bin/env python3
"""Render a conformance trace into the CANONICAL Markdown report — pure, no network.

The report format is fixed here so every run looks identical (don't hand-format in
prose). Reads trace.py output (JSON) on stdin or via --in, writes Markdown to stdout.

    python3 trace.py --requirements r.json --graph g.json | python3 report.py
    python3 report.py --in trace.json [--date 2026-06-12]
"""
import argparse
import json
import sys

# Fixed display order + marker. Gaps first, CONFORMANT last.
BUCKET_ORDER = [
    ("MISSING", "🔴"),
    ("SCORING-MISMATCH", "🟠"),
    ("COLLECTED-NOT-ENFORCED", "🟠"),
    ("NOT-CONFIG-REPRESENTABLE", "⚪"),
    ("CONFORMANT", "✅"),
]
MARK = dict(BUCKET_ORDER)


def render(trace):
    s = trace.get("summary", {})

    def n(b):
        return s.get(b, 0)

    # headline: any real config gap?
    gaps = n("MISSING") + n("SCORING-MISMATCH") + n("COLLECTED-NOT-ENFORCED")
    headline = "❌ Config gaps found" if gaps else "✅ No config gaps in the verifiable scope"

    out = []
    out.append(f"# Conformance report — {trace.get('regulation', '<regulation>')}")
    line = f"**Level:** `{trace.get('level', '<level>')}`"
    if trace.get("date"):
        line += f" · **Date:** {trace['date']}"
    out.append(line)
    out.append("")
    out.append(f"**{headline}.** "
               f"{n('CONFORMANT')} conformant · {n('COLLECTED-NOT-ENFORCED')} collected-but-not-enforced · "
               f"{n('MISSING')} missing · {n('SCORING-MISMATCH')} scoring-mismatch · "
               f"{n('NOT-CONFIG-REPRESENTABLE')} need human review.")
    out.append("")

    # summary table (fixed order)
    out.append("| Bucket | Count |")
    out.append("|---|---|")
    for b, m in BUCKET_ORDER:
        out.append(f"| {m} {b} | {n(b)} |")
    out.append("")

    # findings grouped, fixed order
    by_bucket = {}
    for f in trace.get("findings", []):
        by_bucket.setdefault(f.get("bucket"), []).append(f)
    out.append("## Findings")
    for b, m in BUCKET_ORDER:
        rows = by_bucket.get(b) or []
        if not rows:
            continue
        out.append("")
        out.append(f"### {m} {b} ({len(rows)})")
        for f in rows:
            # lead with the citation into the source document; the internal id is demoted
            cite = f.get("source") or f.get("id")
            out.append(f"- **{cite}** — {f.get('text', '')}")
            out.append(f"  - evidence: {f.get('evidence', '')}")
            tail = f"  - basis: `{f.get('basis', '')}`"
            if f.get("source"):  # keep the internal id available but quiet
                tail += f" · id: `{f.get('id')}`"
            out.append(tail)

    # fixed caveats footer
    out.append("")
    out.append("## Caveats")
    out.append("- **Advisory, not a compliance guarantee** — a human signs off.")
    out.append("- Findings marked `basis: judgment` rest on regulation reading / question mapping, not verified fact.")
    out.append("- `NOT-CONFIG-REPRESENTABLE` items (SDK/platform/process) were **bucketed, not verified** — review them separately.")
    out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile")
    ap.add_argument("--date")
    args = ap.parse_args()
    raw = open(args.infile).read() if args.infile else sys.stdin.read()
    trace = json.loads(raw)
    if args.date:
        trace["date"] = args.date
    sys.stdout.write(render(trace))


if __name__ == "__main__":
    main()
