#!/usr/bin/env python3
"""
Build the FULL countryMappings payload for the supported-documents PUT endpoint
(`PUT /resources/api/agent/globalSettings/idDocSettings/countryMappings`) from a
compact change spec.

PUT replaces the whole map server-side, so this builder does the merge locally
(read-modify-write): it starts from the client's CURRENT map (--current-file),
deep-merges the changed fields per (country, docType), and emits the complete
map. Entries and fields you don't mention are carried over unchanged — never
hand-craft a partial map for PUT. (To remove an override entirely — "Restore
default settings" — use remove_country_mapping.py; this builder refuses
`remove`.)

Usage:
    get_supported_docs.sh  > /tmp/catalogue.json
    get_global_settings.sh > /tmp/current.json     # fetch FRESH right before building
    echo '<spec>' | build_country_mappings.py \
        --current-file /tmp/current.json --catalog-file /tmp/catalogue.json

Input spec (stdin, YAML if PyYAML present, else JSON):
    changes:
      - country: BRA
        docType: ID_CARD
        expirationCheckMode: strict       # scalar fields: merged into the entry
        ocrSettings: {ocrRuleMode: MRZ_DOC}
        defaultFields: [firstName, dob]   # list fields: REPLACE the column wholesale
        extraFields:   [placeOfBirth]     # -> availableFields on the wire (PAID)

Output (stdout): full { "countryMappings": { ... } } ready to PUT.

NOTE on field lists: a column list is replaced wholesale. To ADD one field to a
column without dropping the others, read the current enabled set first
(recognition_status.py) and send the full intended list.

NOTE on new overrides: a BRAND-NEW (country, docType) entry is seeded with the
catalogue defaults for supported, doubleSided, doubleSidedCanBeChanged and
shouldBeSigned (spec values win), so it keeps behaving like the default entry it
shadows — else e.g. doubleSided=null would read as "any side" and silently drop
the catalogue's two-sides requirement. Existing overrides are never touched this
way — their null may be a deliberate "any side" choice.

NOTE on sides dual-write: when the spec sets sidesSelectionMode, the deprecated
supported/doubleSided pair is synced to the matching legacy values (dashboard
parity — see LEGACY_PAIR_BY_MODE), on new AND existing entries, so readers that
predate sidesSelectionMode see the same behavior.

See SKILL.md and references/fields-glossary.md.
"""
import argparse
import copy
import json
import sys

try:
    import yaml  # type: ignore
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

# Spec-control keys consumed by the builder, not written verbatim into the doc.
CONTROL_KEYS = {"country", "docType", "defaultFields", "extraFields"}

# Deprecated CountryDocument fields — refused outright. They still appear in
# GET responses (read them for context), but new writes must use the
# replacement; sending the legacy key would create stale overrides.
DEPRECATED_KEYS = {
    "supported": "use sidesSelectionMode: 'disabled' to stop accepting the doc type "
                 "(or a positive mode to accept it)",
    "doubleSided": "use sidesSelectionMode: oneSide/twoSides/smartMode",
    "doubleSidedCanBeChanged": "use sidesSelectionMode",
    "acceptedAsPoa": "deprecated on the backend; not editable via this skill",
    "acceptSameDocAsPoa": "deprecated on the backend; not editable via this skill",
}

# Fields deliberately NOT editable via this skill — the dashboard gates them
# (feature flag / Sumsub-only) and the agent must not bypass that.
RESTRICTED_KEYS = {
    "shouldBeSigned": "editable only in the dashboard behind the "
                      "'showRejectByMissingSignatureSetting' feature flag; enabling it makes "
                      "autochecks reject unsigned documents. Direct the user to the dashboard "
                      "or Sumsub support",
    "shouldBeMasked": "masking of legally protected national IDs (e.g. NGA NIN is "
                      "Sumsub-only even in the dashboard); changing it may violate local law. "
                      "Direct the user to the dashboard or Sumsub support",
}

EXPIRATION_CHECK_MODES = {"allowExpired", "strict",
                          "generallyAcceptedRegulations", "localRegulations"}
OCR_RULE_MODES = {"DEFAULT", "MRZ_DOC"}


def _die(msg, code=2):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def _load_spec(stream):
    data = stream.read()
    if not data.strip():
        _die("empty change spec on stdin")
    if _HAS_YAML:
        try:
            return yaml.safe_load(data)
        except yaml.YAMLError as e:
            _die(f"failed to parse spec as YAML/JSON: {e}")
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        _die(f"failed to parse spec as JSON: {e}; install PyYAML to accept YAML.")


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


def _validate_enums(doc, country, doc_type):
    ecm = doc.get("expirationCheckMode")
    if ecm is not None and ecm not in EXPIRATION_CHECK_MODES:
        _die(f"{country}/{doc_type}: invalid expirationCheckMode '{ecm}'; "
             f"allowed: {sorted(EXPIRATION_CHECK_MODES)}")
    ocr = doc.get("ocrSettings")
    if isinstance(ocr, dict):
        mode = ocr.get("ocrRuleMode")
        if mode is not None and mode not in OCR_RULE_MODES:
            _die(f"{country}/{doc_type}: invalid ocrSettings.ocrRuleMode '{mode}'; "
                 f"allowed: {sorted(OCR_RULE_MODES)}")


def _field_category(catalogue, country, doc_type, field):
    cat = (catalogue.get(country, {}) or {}).get(doc_type)
    if not cat:
        return None
    if field in cat.get("defaultFields", []):
        return "default"
    if field in cat.get("availableFields", []):
        return "available"
    return None


def _apply_field_columns(doc, country, doc_type, requested_default, requested_extra,
                         catalogue, summary):
    """Set the Default/Extra field columns the caller specified. Each column is a
    WHOLESALE replace: we set exactly what the caller passed (after validating each
    field belongs to that column). We do NOT auto-move a field to the other column:
    that would silently replace the other column's list and could wipe fields the
    caller never meant to touch. A misplaced field is a hard error telling the
    caller the correct column."""
    for field in (requested_default or []):
        if _field_category(catalogue, country, doc_type, field) == "available":
            _die(f"{country}/{doc_type}: '{field}' is an Extra Field — put it under "
                 "'extraFields', not 'defaultFields'.")
    for field in (requested_extra or []):
        if _field_category(catalogue, country, doc_type, field) == "default":
            _die(f"{country}/{doc_type}: '{field}' is a Default Field — put it under "
                 "'defaultFields', not 'extraFields'.")

    if requested_default is not None and not requested_default:
        _die(f"{country}/{doc_type}: 'defaultFields: []' cannot disable the whole Default "
             "column — the backend keeps the catalogue defaults when the list is empty "
             "(at least one default field stays on). Omit 'defaultFields' to leave it "
             "unchanged, or list the fields that should remain.")

    parts = []
    if requested_default is not None:
        doc["defaultFields"] = list(requested_default)
        parts.append(f"Default Fields → {', '.join(requested_default) or '(none)'}")
    if requested_extra is not None:
        doc["availableFields"] = list(requested_extra)
        tag = "PAID, requires ADVANCED_OCR" if requested_extra else "PAID"
        parts.append(f"Extra Fields ({tag}) → {', '.join(requested_extra) or '(none)'}")
    if parts:
        summary.append(f"{country}/{doc_type}: " + "; ".join(parts)
                       + "  [replaces the whole column — include all fields that should stay on]")


# Catalogue defaults copied onto a BRAND-NEW override so it keeps behaving like
# the default entry it shadows. Without this a sparse override would persist
# these as null — e.g. doubleSided=null reads as "any side", silently dropping
# the catalogue's two-sides requirement.
SEED_KEYS = ("supported", "doubleSided", "doubleSidedCanBeChanged", "shouldBeSigned")

# Dashboard dual-write parity (supportedDocumentMapping): when the spec sets
# sidesSelectionMode, the deprecated supported/doubleSided pair is synced to the
# matching legacy values so pre-sidesSelectionMode readers see the same behavior.
LEGACY_PAIR_BY_MODE = {
    "disabled":  {"supported": False, "doubleSided": False},
    "oneSide":   {"supported": True,  "doubleSided": False},
    "smartMode": {"supported": True,  "doubleSided": False},
    "twoSides":  {"supported": True,  "doubleSided": True},
}


def _seed_new_override_from_catalogue(country, doc_type, catalogue, summary):
    """Return the catalogue defaults a new (country, docType) override starts from.
    Only keys present (non-null) in the catalogue are copied; a null there (e.g.
    doubleSided for genuine "any side" docs) stays absent. Spec values are applied
    on top and win."""
    cat = (catalogue.get(country, {}) or {}).get(doc_type) or {}
    seed = {key: cat[key] for key in SEED_KEYS if cat.get(key) is not None}
    if seed:
        seeded = ", ".join(f"{k}={json.dumps(v)}" for k, v in seed.items())
        summary.append(f"{country}/{doc_type}: new override seeded with catalogue "
                       f"defaults ({seeded})")
    return seed


def build(spec, current, catalogue):
    if not isinstance(spec, dict) or "changes" not in spec:
        _die("spec must be an object with a 'changes' list")
    changes = spec["changes"]
    if not isinstance(changes, list) or not changes:
        _die("'changes' must be a non-empty list")

    result = copy.deepcopy(current)
    warnings, summary = [], []

    for i, change in enumerate(changes):
        if not isinstance(change, dict):
            _die(f"changes[{i}] must be an object; got {change!r}")
        if change.get("remove"):
            _die(f"changes[{i}] uses remove — this builder only edits. "
                 "Use remove_country_mapping.py to restore defaults.")
        country = change.get("country")
        doc_type = change.get("docType")
        if not country or not doc_type:
            _die(f"changes[{i}] requires both 'country' and 'docType'")

        delta = {}
        for key, value in change.items():
            if key in CONTROL_KEYS:
                continue
            if key in DEPRECATED_KEYS:
                _die(f"{country}/{doc_type}: '{key}' is deprecated and not settable "
                     f"via this skill — {DEPRECATED_KEYS[key]}.")
            if key in RESTRICTED_KEYS:
                _die(f"{country}/{doc_type}: '{key}' is not editable via this skill — "
                     f"{RESTRICTED_KEYS[key]}.")
            delta[key] = value

        _validate_enums(delta, country, doc_type)

        if delta.get("acceptScreenshots") is True:
            warnings.append(
                f"{country}/{doc_type}: acceptScreenshots=true is a CRITICAL fraud setting — "
                "it DISABLES screenshot protection. Fake applications may be approved and "
                "approval rates may look higher only because fraud is not blocked. May expose "
                "you to penalties and chargebacks. Confirm with the user before applying.")
        if delta.get("acceptDigitalDoc") is True:
            warnings.append(
                f"{country}/{doc_type}: acceptDigitalDoc=true accepts uploaded files/scans/PDFs — "
                "digital documents are easy to modify to pass verification; consider extra checks. "
                "Confirm with the user.")

        if "defaultFields" in change or "extraFields" in change:
            _apply_field_columns(delta, country, doc_type,
                                 change.get("defaultFields"), change.get("extraFields"),
                                 catalogue, summary)

        mode = delta.get("sidesSelectionMode")
        if mode is not None:
            legacy_pair = LEGACY_PAIR_BY_MODE.get(mode)
            if legacy_pair is None:
                _die(f"{country}/{doc_type}: invalid sidesSelectionMode '{mode}'; "
                     f"allowed: {sorted(LEGACY_PAIR_BY_MODE)}")
            delta.update(legacy_pair)
            summary.append(f"{country}/{doc_type}: sidesSelectionMode={mode} also syncs the "
                           f"legacy pair (supported={json.dumps(legacy_pair['supported'])}, "
                           f"doubleSided={json.dumps(legacy_pair['doubleSided'])}) — dashboard parity")

        if not delta:
            _die(f"changes[{i}] for {country}/{doc_type} has nothing to change")

        existing = result.get(country, {}).get(doc_type)
        if existing is None:
            entry = _seed_new_override_from_catalogue(country, doc_type, catalogue, summary)
            entry.update(delta)
            result.setdefault(country, {})[doc_type] = entry
        else:
            existing.update(delta)

    if summary:
        print("Field changes:", file=sys.stderr)
        for s in summary:
            print(f"  {s}", file=sys.stderr)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)

    return {"countryMappings": result}


def main():
    ap = argparse.ArgumentParser(
        description="Build the full countryMappings PUT payload (current settings + changes).")
    ap.add_argument("--current-file", required=True,
                    help="client's current settings JSON (from get_global_settings.sh); "
                         "fetch FRESH right before building — PUT replaces the whole map, "
                         "so a stale snapshot would revert edits made in between")
    ap.add_argument("--catalog-file", required=True,
                    help="default catalogue JSON (from get_supported_docs.sh); used to route "
                         "Default/Extra field lists and to backfill sides for new overrides")
    args = ap.parse_args()

    spec = _load_spec(sys.stdin)
    current = _country_mappings(_read_json(args.current_file), "--current-file")
    catalogue = _country_mappings(_read_json(args.catalog_file), "--catalog-file")

    payload = build(spec, current, catalogue)
    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
