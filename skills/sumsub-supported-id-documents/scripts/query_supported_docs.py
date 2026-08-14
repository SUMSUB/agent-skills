#!/usr/bin/env python3
"""
Query the Sumsub supported-documents reference (the `documentsByCountries`
catalogue) with a compact filter spec.

The catalogue is large (~250 countries × several doc types). Dumping it raw
into an LLM context is wasteful, and a naive value filter does not help when
the value is near-universal (e.g. `dob` is a default field for 100% of pairs).
This script keeps the full catalogue in-process and returns only the relevant
slice — or, when a slice would be uselessly large, an aggregate summary instead.

Usage:
    get_supported_docs.sh > /tmp/docs.json
    echo '{"countries": ["DEU"]}' | query_supported_docs.py --data-file /tmp/docs.json

Input: a compact spec on stdin (YAML if PyYAML is installed, else JSON).
Data:  the full catalogue JSON via --data-file (as returned by the API).
Output: filtered JSON slice or an aggregate summary on stdout.

See SKILL.md for the spec format and the list-vs-summary decision rules.
"""
import argparse
import json
import sys

try:
    import yaml  # type: ignore
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

# A field present in more than this share of matched pairs makes a per-pair
# list useless ("it's everywhere"); the script collapses to a summary instead.
UNIVERSAL_THRESHOLD = 0.80
# Even below the coverage threshold, a field-presence result this large is not
# worth listing pair-by-pair — collapse to a distribution summary instead.
MAX_LIST_BEFORE_SUMMARY = 200
# When a near-universal field is ABSENT from only a short list, that complement
# is more useful than the long presence list — include it up to this size.
COMPLEMENT_MAX = 20
# How many top countries / docTypes to show in a distribution summary.
TOP_N = 10
# Default cap on returned list items before truncation kicks in.
DEFAULT_LIMIT = 100

FIELD_KINDS = {"default", "available", "any"}
OUTPUT_MODES = {"auto", "list", "summary"}


def _load_spec(stream):
    data = stream.read()
    if not data.strip():
        return {}
    if _HAS_YAML:
        try:
            return yaml.safe_load(data) or {}
        except yaml.YAMLError as e:
            _die(f"failed to parse spec as YAML/JSON: {e}")
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        _die(f"failed to parse spec as JSON: {e}; install PyYAML to accept YAML.")


def _die(msg, code=2):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def _flatten(catalogue):
    """Expand {countryMappings: {COUNTRY: {DOC_TYPE: {...}}}} into a flat list of
    pair records, each carrying its country, docType and the per-doc config."""
    mappings = catalogue.get("countryMappings")
    if not isinstance(mappings, dict):
        _die("data-file has no 'countryMappings' object — is this the documentsByCountries catalogue?")
    pairs = []
    for country, docs in mappings.items():
        if not isinstance(docs, dict):
            continue
        for doc_type, cfg in docs.items():
            if not isinstance(cfg, dict):
                continue
            pairs.append({"country": country, "docType": doc_type, "cfg": cfg})
    return pairs


def _spec_get_list(spec, key):
    val = spec.get(key)
    if val is None:
        return None
    if isinstance(val, str):
        return [val]
    if isinstance(val, list):
        return [str(v) for v in val]
    _die(f"'{key}' must be a string or list of strings; got {val!r}")


def _matches_flags(cfg, flags):
    for flag_name, want in flags.items():
        if bool(cfg.get(flag_name, False)) != bool(want):
            return False
    return True


def _field_in(cfg, field, kind):
    if kind == "default":
        return field in cfg.get("defaultFields", [])
    if kind == "available":
        return field in cfg.get("availableFields", [])
    return field in cfg.get("defaultFields", []) or field in cfg.get("availableFields", [])


def _apply_filters(pairs, countries, doc_types, flags):
    """Apply the structural filters (country / docType / flags). The `field`
    filter is applied separately so we can measure its coverage for auto-mode."""
    out = []
    for p in pairs:
        if countries and p["country"] not in countries:
            continue
        if doc_types and p["docType"] not in doc_types:
            continue
        if flags and not _matches_flags(p["cfg"], flags):
            continue
        out.append(p)
    return out


def _top_counts(pairs, key, top_n=None):
    counts = {}
    for p in pairs:
        counts[p[key]] = counts.get(p[key], 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    if top_n is not None:
        ordered = ordered[:top_n]
    return {k: v for k, v in ordered}


def _item_view(p):
    cfg = p["cfg"]
    view = {"country": p["country"], "docType": p["docType"]}
    for k in ("supported", "doubleSided", "doubleSidedCanBeChanged", "shouldBeSigned"):
        if k in cfg:
            view[k] = cfg[k]
    if "defaultFields" in cfg:
        view["defaultFields"] = cfg["defaultFields"]
    if "availableFields" in cfg:
        view["availableFields"] = cfg["availableFields"]
    return view


def query(spec, catalogue):
    countries = _spec_get_list(spec, "countries")
    doc_types = _spec_get_list(spec, "docTypes")
    field = spec.get("field")
    field_kind = spec.get("fieldKind", "any")
    if field_kind not in FIELD_KINDS:
        _die(f"fieldKind must be one of {sorted(FIELD_KINDS)}; got {field_kind!r}")
    flags = spec.get("flags") or {}
    if not isinstance(flags, dict):
        _die(f"flags must be an object; got {flags!r}")
    # Unsupported documents can't be configured, so they're excluded by default.
    # The caller must opt in explicitly (flags.supported: false) to see them.
    if "supported" not in flags:
        flags = {**flags, "supported": True}
    output = spec.get("output", "auto")
    if output not in OUTPUT_MODES:
        _die(f"output must be one of {sorted(OUTPUT_MODES)}; got {output!r}")
    limit = spec.get("limit", DEFAULT_LIMIT)

    pairs = _flatten(catalogue)
    base = _apply_filters(pairs, countries, doc_types, flags)

    if field:
        present = [p for p in base if _field_in(p["cfg"], field, field_kind)]
        coverage = len(present) / len(base) if base else 0.0
        near_universal = coverage >= UNIVERSAL_THRESHOLD
        too_many = len(present) > MAX_LIST_BEFORE_SUMMARY
        force_summary = output == "summary" or (
            output == "auto" and (near_universal or too_many)
        )
        if force_summary:
            absent = [p for p in base if not _field_in(p["cfg"], field, field_kind)]
            result = {
                "mode": "summary",
                "field": field,
                "fieldKind": field_kind,
                "presentIn": len(present),
                "totalPairs": len(base),
                "coverage": f"{round(100 * coverage)}%",
                "distinctCountries": len({p["country"] for p in present}),
                "byDocType": _top_counts(present, "docType"),
            }
            if near_universal:
                result["note"] = (
                    "near-universal field — filtering by it barely narrows the set"
                )
                if 0 < len(absent) <= COMPLEMENT_MAX:
                    result["absentIn"] = [
                        {"country": p["country"], "docType": p["docType"]} for p in absent
                    ]
            else:
                result["note"] = (
                    f"{len(present)} matches — too many to list; add countries/docTypes "
                    "filters to narrow, or set output:list with a higher limit to force a list."
                )
                result["topCountries"] = _top_counts(present, "country", TOP_N)
            return result
        matched = present
    else:
        matched = base

    truncated = output != "summary" and len(matched) > limit
    items = matched[:limit] if truncated else matched
    result = {
        "mode": "list",
        "totalMatches": len(matched),
        "returned": len(items),
        "truncated": truncated,
        "items": [_item_view(p) for p in items],
    }
    if truncated:
        result["hint"] = (
            f"{len(matched)} matches exceed limit {limit}; add countries/docTypes "
            "filters to narrow, or set a higher 'limit'."
        )
    return result


def main():
    ap = argparse.ArgumentParser(description="Filter the supported-documents catalogue.")
    ap.add_argument("--data-file", required=True,
                    help="path to the documentsByCountries catalogue JSON (from get_supported_docs.sh)")
    args = ap.parse_args()

    spec = _load_spec(sys.stdin)
    if not isinstance(spec, dict):
        _die(f"spec must be an object; got {type(spec).__name__}")

    try:
        with open(args.data_file, encoding="utf-8") as f:
            catalogue = json.load(f)
    except OSError as e:
        _die(f"cannot read --data-file: {e}", code=3)
    except json.JSONDecodeError as e:
        _die(f"--data-file is not valid JSON: {e}", code=3)

    result = query(spec, catalogue)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
