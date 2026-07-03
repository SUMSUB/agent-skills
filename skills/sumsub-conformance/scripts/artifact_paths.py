#!/usr/bin/env python3
"""Derive the CANONICAL artifact paths for a regulation file — pure, no network.

Artifacts MUST live in the SAME directory as the source regulation file and be
named from its stem (filename without extension):
  <stem>_regulations.json  — the extracted + mapped requirements
  <stem>_config.json       — the resolved config graph (resolve_graph.sh output)
  <stem>_report.md         — the rendered conformance report

Prints eval-able shell so the agent never improvises names/locations:
  eval "$(python3 scripts/artifact_paths.py /path/Level4regulations.pdf)"
  # → $REQUIREMENTS, $CONFIG, $REPORT
e.g. Level4regulations.pdf → Level4regulations_regulations.json / _config.json / _report.md
"""
import os
import sys


def derive(src):
    d = os.path.dirname(os.path.abspath(src))
    stem = os.path.splitext(os.path.basename(src))[0]
    return {
        "REQUIREMENTS": os.path.join(d, f"{stem}_regulations.json"),
        "CONFIG": os.path.join(d, f"{stem}_config.json"),
        "REPORT": os.path.join(d, f"{stem}_report.md"),
    }


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: artifact_paths.py <regulation-file>\n")
        return 2
    for k, v in derive(sys.argv[1]).items():
        # shell-quote the value (paths may contain spaces, e.g. 'Phase 4 …pdf')
        print(f"{k}='" + v.replace("'", "'\\''") + "'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
