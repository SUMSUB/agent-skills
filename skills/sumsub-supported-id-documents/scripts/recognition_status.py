#!/usr/bin/env python3
"""
Show the EFFECTIVE recognition status of every OCR field for a given country and
document type — i.e. what is actually recognised for THIS client right now, not
just what the catalogue allows.

It combines three inputs:
  1. the client's current settings  (--current-file, from get_global_settings.sh)
  2. the default catalogue          (--catalog-file, from get_supported_docs.sh)
  3. whether ADVANCED_OCR is enabled (--advanced-ocr, from get_entitlements.sh)

Why all three: a field is only really recognised if (a) it's checked in the
client's effective settings AND (b) — for Extra Fields — the client has the
ADVANCED_OCR entitlement (otherwise the backend drops it silently).

Usage:
    recognition_status.py BRA PASSPORT \
        --current-file /tmp/current.json \
        --catalog-file /tmp/catalogue.json \
        --advanced-ocr true|false

Output (stdout, JSON): per-field status grouped into recognised / not recognised.
A human-readable summary is printed to stderr.
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


def status(country, doc_type, current, catalogue, advanced_ocr):
    cat = catalogue.get(country, {}).get(doc_type)
    if not cat:
        _die(f"{country}/{doc_type} is not in the catalogue")
    cat_default = cat.get("defaultFields", [])
    cat_available = cat.get("availableFields", [])

    # Effective config, resolved per column to match the backend:
    #   Default column — the catalogue defaults stay recognised unless the client's
    #     override supplies a NON-EMPTY defaultFields list. An empty/absent list does
    #     NOT disable the column (see OcrFieldsInfoModel#enrichWithClientCountryDocument),
    #     so a sparse scalar-only override must fall back to the catalogue here.
    #   Extra column — base is empty; the client's availableFields only ADD extras.
    override = current.get(country, {}).get(doc_type)
    configured = override is not None
    override_default = (override or {}).get("defaultFields")
    on_default = set(override_default) if override_default else set(cat_default)
    on_available = set((override or {}).get("availableFields") or [])

    recognised, not_recognised = [], []

    for field in cat_default:
        if field in on_default:
            recognised.append({"field": field, "column": "default", "paid": False})
        else:
            not_recognised.append({"field": field, "column": "default",
                                   "reason": "turned off (default field unchecked)"})

    for field in cat_available:
        if field in on_available and advanced_ocr:
            recognised.append({"field": field, "column": "extra", "paid": True})
        elif field in on_available and not advanced_ocr:
            not_recognised.append({"field": field, "column": "extra",
                                   "reason": "enabled but ADVANCED_OCR is OFF — backend drops it"})
        else:
            not_recognised.append({"field": field, "column": "extra",
                                   "reason": "extra field, not enabled"})

    return {
        "country": country,
        "docType": doc_type,
        "advancedOcr": advanced_ocr,
        "source": "client override" if configured else "catalogue default (client has no override)",
        "recognised": recognised,
        "notRecognised": not_recognised,
    }


def _print_summary(result):
    print(f"Recognised fields for {result['country']} / {result['docType']} "
          f"(source: {result['source']}):", file=sys.stderr)
    if result["recognised"]:
        for f in result["recognised"]:
            tag = "PAID — ADVANCED_OCR" if f["paid"] else "free"
            print(f"  ✅ {f['field']} ({tag})", file=sys.stderr)
    else:
        print("  (none)", file=sys.stderr)
    print("Not recognised:", file=sys.stderr)
    if result["notRecognised"]:
        for f in result["notRecognised"]:
            print(f"  ⬜ {f['field']} — {f['reason']}", file=sys.stderr)
    else:
        print("  (none)", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="Effective OCR recognition status for a country/doc type.")
    ap.add_argument("country", help="ISO-3 country code, e.g. BRA")
    ap.add_argument("docType", nargs="?",
                    help="document type, e.g. PASSPORT. Omit to report ALL doc types for the country.")
    ap.add_argument("--current-file", required=True, help="client's global settings JSON")
    ap.add_argument("--catalog-file", required=True, help="default catalogue JSON")
    ap.add_argument("--advanced-ocr", required=True, choices=["true", "false"],
                    help="whether the client has the ADVANCED_OCR entitlement")
    args = ap.parse_args()

    current = _country_mappings(_read_json(args.current_file), "--current-file")
    catalogue = _country_mappings(_read_json(args.catalog_file), "--catalog-file")
    advanced_ocr = args.advanced_ocr == "true"

    if args.docType:
        doc_types = [args.docType]
    else:
        doc_types = sorted(catalogue.get(args.country, {}).keys())
        if not doc_types:
            _die(f"{args.country} is not in the catalogue")

    results = []
    for dt in doc_types:
        result = status(args.country, dt, current, catalogue, advanced_ocr)
        _print_summary(result)
        results.append(result)

    out = results[0] if args.docType else {"country": args.country, "docTypes": results}
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
