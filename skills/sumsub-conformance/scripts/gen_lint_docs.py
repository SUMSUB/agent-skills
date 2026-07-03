#!/usr/bin/env python3
"""Generate the rule catalog + lookup tables in references/lint-rules.md from
references/rules.json — the single source of truth.

The generated blocks live between `<!-- GEN:rules -->`/`<!-- /GEN:rules -->` and
`<!-- GEN:lookups -->`/`<!-- /GEN:lookups -->` markers; the surrounding prose is
hand-written and left untouched.

    python3 scripts/gen_lint_docs.py          # rewrite lint-rules.md in place
    python3 scripts/gen_lint_docs.py --check   # exit 1 if the file is out of sync

`test_lint.py` runs the --check path so docs can never silently drift from rules.json.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RULES_JSON = os.path.join(HERE, "..", "references", "rules.json")
DOC_MD = os.path.join(HERE, "..", "references", "lint-rules.md")


def load_spec():
    with open(RULES_JSON) as fh:
        return json.load(fh)


def build_rules_table(spec):
    rows = ["| Rule | Severity | Detection | Fix |", "|---|---|---|---|"]
    for rid, meta in spec["rules"].items():
        sev = meta.get("severityDoc", meta["severity"])
        rows.append(f"| `{rid}` | {sev} | {meta['detection']} | {meta['fix']} |")
    return "\n".join(rows)


def build_lookups(spec):
    lk = spec["lookups"]
    lines = []
    lines.append("- **Valid AML providers** (`amlCaseType`): "
                 + ", ".join(f"`{x}`" for x in lk["amlProviders"]) + ".")
    lines.append("- **Valid PoA `allowedTypesSettings` keys**: "
                 + ", ".join(f"`{x}`" for x in lk["poaProviderCategories"]) + ".")
    lines.append("- **Discouraged SELFIE `videoRequired`**: "
                 + ", ".join(f"`{x}`" for x in lk["discouragedSelfieLiveness"])
                 + " (default is `passiveLiveness`).")
    lines.append("- **docSet → entitlement** (any one satisfies the step):")
    for t, ents in lk["docsetEntitlements"].items():
        lines.append(f"    - `{t}` → " + " | ".join(f"`{e}`" for e in ents))
    return "\n".join(lines)


def splice(text, name, content):
    start, end = f"<!-- GEN:{name} -->", f"<!-- /GEN:{name} -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        raise SystemExit(f"marker block GEN:{name} not found in {DOC_MD}")
    return pattern.sub(lambda _: f"{start}\n{content}\n{end}", text)


def render(text, spec):
    text = splice(text, "rules", build_rules_table(spec))
    text = splice(text, "lookups", build_lookups(spec))
    return text


def main():
    spec = load_spec()
    with open(DOC_MD) as fh:
        current = fh.read()
    updated = render(current, spec)

    if "--check" in sys.argv[1:]:
        if current != updated:
            sys.stderr.write("lint-rules.md is out of sync with rules.json — "
                             "run: python3 scripts/gen_lint_docs.py\n")
            return 1
        print("lint-rules.md is in sync with rules.json")
        return 0

    with open(DOC_MD, "w") as fh:
        fh.write(updated)
    print(f"wrote {DOC_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
