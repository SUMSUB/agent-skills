#!/usr/bin/env python3
"""
Show a human-readable diff between the client's CURRENT supported-documents
settings and a built full-map PUT payload — for the confirmation step before PUT.
Removals show as REMOVED; entries the builder carried over unchanged are silent.

Use this instead of hand-writing an inline `python3 -c "..."` diff: it's a fixed,
pre-approved script (no per-call permission prompt) and prints a clean per-field
diff grouped by country / doc type.

Usage:
    diff_country_mappings.py --current-file /tmp/current.json --payload-file /tmp/payload.json

Both files may be either the raw global-settings response (countryMappings nested
under idDocSettings) or a {countryMappings: ...} payload — the script finds the
map either way. Output is human-readable on stdout; exit 0 always (it's a report).
"""
import argparse
import json
import sys


def _die(msg, code=2):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except OSError as e:
        _die(f"cannot read {path}: {e}", code=3)
    except json.JSONDecodeError as e:
        _die(f"{path} is not valid JSON: {e}", code=3)


def _country_mappings(doc, source):
    if isinstance(doc.get("countryMappings"), dict):
        return doc["countryMappings"]
    id_doc = doc.get("idDocSettings")
    if isinstance(id_doc, dict) and isinstance(id_doc.get("countryMappings"), dict):
        return id_doc["countryMappings"]
    _die(f"{source} has no countryMappings")


def _fmt(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def diff(current, payload):
    """PUT replace-all semantics: a doc present in current but absent from the
    payload is REMOVED, and fields absent from the payload doc become null.
    Entries carried over unchanged by the builder produce no lines."""
    lines = []
    for country in sorted(set(current) | set(payload)):
        cur_docs = current.get(country, {})
        new_docs = payload.get(country, {})
        for doc_type in sorted(set(cur_docs) | set(new_docs)):
            cur = cur_docs.get(doc_type)
            new = new_docs.get(doc_type)
            if cur is None and new is not None:
                lines.append(f"+ {country}/{doc_type}: ADDED")
                continue
            if cur is not None and new is None:
                lines.append(f"- {country}/{doc_type}: REMOVED (restored to catalogue default)")
                continue
            field_lines = []
            for key in sorted(set(cur) | set(new)):
                cv, nv = cur.get(key), new.get(key)
                if cv != nv:
                    field_lines.append(f"      {key}: {_fmt(cv)} → {_fmt(nv)}")
            if field_lines:
                lines.append(f"~ {country}/{doc_type}: CHANGED")
                lines.extend(field_lines)
    return lines


def main():
    ap = argparse.ArgumentParser(description="Diff current settings vs a built payload.")
    ap.add_argument("--current-file", required=True)
    ap.add_argument("--payload-file", required=True)
    args = ap.parse_args()

    current = _country_mappings(_read_json(args.current_file), "--current-file")
    payload = _country_mappings(_read_json(args.payload_file), "--payload-file")

    lines = diff(current, payload)
    if not lines:
        print("No changes — payload matches current settings.")
    else:
        print("Changes to apply (current → new):")
        for line in lines:
            print(f"  {line}")


if __name__ == "__main__":
    main()
