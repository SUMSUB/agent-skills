#!/usr/bin/env python3
"""
Build a full countryMappings payload that REMOVES one or more (country, docType)
overrides — i.e. "Restore default settings" for those entries. The removed entries
fall back to the catalogue default on read.

The edit builder (build_country_mappings.py) only merges and never deletes, so
removal has its own builder: this produces the client's full current map MINUS
the named entries, to be sent with the PUT (replace-all) endpoint via
put_country_mappings.sh.

Usage:
    get_global_settings.sh > /tmp/current.json
    remove_country_mapping.py --current-file /tmp/current.json BRA:ID_CARD FRA:PASSPORT > /tmp/payload.json
    put_country_mappings.sh /tmp/payload.json     # PUT (replace-all)

Each positional arg is COUNTRY:DOCTYPE. Output (stdout): { "countryMappings": ... }.
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


def _country_mappings(doc):
    if isinstance(doc.get("countryMappings"), dict):
        return doc["countryMappings"]
    id_doc = doc.get("idDocSettings")
    if isinstance(id_doc, dict) and isinstance(id_doc.get("countryMappings"), dict):
        return id_doc["countryMappings"]
    _die("--current-file has no countryMappings")


def main():
    ap = argparse.ArgumentParser(description="Build a PUT payload that removes (restores) overrides.")
    ap.add_argument("--current-file", required=True, help="client's current global settings JSON")
    ap.add_argument("targets", nargs="+", metavar="COUNTRY:DOCTYPE",
                    help="entries to remove, e.g. BRA:ID_CARD")
    args = ap.parse_args()

    mappings = json.loads(json.dumps(_country_mappings(_read_json(args.current_file))))  # deep copy

    removed, missing = [], []
    for target in args.targets:
        if ":" not in target:
            _die(f"target '{target}' must be COUNTRY:DOCTYPE")
        country, doc_type = target.split(":", 1)
        docs = mappings.get(country)
        if docs and doc_type in docs:
            docs.pop(doc_type)
            removed.append(target)
            if not docs:
                mappings.pop(country)
        else:
            missing.append(target)

    for t in removed:
        print(f"will remove (restore default): {t}", file=sys.stderr)
    for t in missing:
        print(f"warning: {t} is not in the client's overrides — nothing to remove", file=sys.stderr)
    if not removed:
        _die("none of the requested entries exist in the current overrides")

    json.dump({"countryMappings": mappings}, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
