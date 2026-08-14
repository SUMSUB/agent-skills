---
name: sumsub-supported-id-documents
description: Query AND edit Sumsub's supported identity documents. READ the built-in catalogue (documentsByCountries) — which document types are supported per country, whether they're double-sided, which OCR fields are default vs. available. EDIT a client's own supported-document overrides (idDocSettings.countryMappings) via the global-settings API. TRIGGER when the user asks "which countries / document types support field X", "what fields can I collect for a passport in DEU", "is the ID card double-sided in France", OR wants to change supported documents / toggle a document type / edit collected fields for a country. SKIP for creating levels or questionnaires (use the dedicated skills).
allowed-tools: Read, Bash
---

# Sumsub — Supported Documents Reference

Answers questions about Sumsub's built-in supported-documents catalogue
(`documentsByCountries`): per country and document type, whether the type is
supported, whether it's double-sided, and which OCR fields are extracted by
default vs. optionally available.

The catalogue is large (~250 countries, ~1350 country/doc-type pairs). This
skill never dumps it into the conversation — a local Python script keeps the
full catalogue in-process and returns only the relevant slice, collapsing to an
aggregate summary when a flat list would be too large to be useful.

## Endpoints

| Method | Path | When |
|---|---|---|
| `GET` | `/resources/api/agent/supportedDocs/documentsByCountries` | Read the built-in supported-documents catalogue (defaults for every country). |
| `GET` | `/resources/api/agent/globalSettings` | Read the client's CURRENT settings, incl. their `idDocSettings.countryMappings` overrides. |
| `GET` | `/resources/api/agent/globalSettings/extensionRules` | Read Sumsub's built-in expiry-extension rules (read-only reference; backs the "officially extended documents" expiry modes). |
| `PUT` | `/resources/api/agent/globalSettings/idDocSettings/countryMappings` | **Replace-all — the only write path.** Always send the FULL map built by the scripts (read-modify-write for edits, minus-one-entry for removals). |

All use App Token auth with `manageClientSettings`.

The catalogue GET returns `{ "countryMappings": { "<ISO3>": { "<DOC_TYPE>": { supported, doubleSided, doubleSidedCanBeChanged, shouldBeSigned, acceptDigitalDoc, acceptScreenshots, expirationCheckMode, sidesSelectionMode, defaultFields[], availableFields[] } } } }`.

> ⚠️ **Two different shapes — mind the path.** The catalogue GET puts
> `countryMappings` at the **top level**. GET globalSettings nests it one level
> deeper, under **`idDocSettings.countryMappings`** (the root also has `minAge`,
> `poaCheckSettings`, `poiCheckSettings` — the key-wide expiry mode — etc.). When reading `/tmp/current.json` (globalSettings) in an
> inline `python3 -c`, use `['idDocSettings']['countryMappings']` — the top-level
> path raises `KeyError: 'countryMappings'`.

> Fields are serialised `NON_NULL`: a flag that is **absent** from the JSON is at
> its default (not set). For acceptance flags, absent ⇒ `false` (e.g. no
> `acceptScreenshots` key ⇒ screenshots are **not** accepted). Never report a flag
> as enabled just because it's missing; report the default and say it's the default.

> **PUT is replace-all:** the backend swaps the whole `countryMappings` map for
> whatever you send — anything omitted is wiped (reverts to catalogue defaults).
> That's why every write goes through the scripts: `build_country_mappings.py`
> merges your changes into a FRESH copy of the current map, and
> `remove_country_mapping.py` builds the map minus one entry. Never hand-craft a
> partial payload, and never reuse a stale `/tmp/current.json` — re-fetch it right
> before building or a concurrent dashboard edit gets silently reverted.

### Key-wide root blocks in GET globalSettings (read them, don't miss them)

Besides `idDocSettings.countryMappings`, the globalSettings root carries
**key-wide** blocks that change document answers. They are read-only context for
this skill (edits here go through PUT countryMappings only), but skipping them
gives wrong answers — a per-country entry that looks "not configured" may be
governed by a root block:

| Root path | What it holds | When it changes the answer |
|---|---|---|
| `poiCheckSettings.expirationCheckMode` | key-wide expiry mode | fallback in the expiry cascade (**C**) |
| `poiCheckSettings.minimumResidualValidityInMonths` | doc must stay valid ≥ N more months; **`0` = no requirement** (see **C**) | part of any validity answer (**C**) |
| `ongoingMonitoringSettings` (`enabled`, `idDocExpireInDays`) | expiry monitoring AFTER approval (licence-gated) | "what happens when the doc expires" |
| `minAge` / `maxAge` | key-wide age limits (checked against DOB); dashboard auto-fills on save (min 16 — 18 for RUS-licensed keys — max 110), so usually present | "why was the doc/applicant rejected by age" |
| `idDocSettings.ekycSourceMappings` | eKYC sources per country — sibling of `countryMappings`, edited on the SAME dashboard "Supported ID documents" screen but saved as a separate payload; PUT countryMappings preserves it server-side (the endpoint only replaces `countryMappings`) | eKYC questions; don't confuse with countryMappings |
| `enableAutoCompleteShortDates` | OCR auto-completes 2-digit years in dates (dashboard: "Birth date" checkbox) | recognised date values |
| `imageConstraints` (`minFileSize`, `maxFileSize`) | upload size limits (dashboard: General → Applicant settings) | "why was the file not accepted" |
| `poaCheckSettings` (deprecated) | POA acceptance (`validMonths`, `acceptIdAsPoa`, `acceptSameDocAsPoa`) | POA questions — report as read-only context |
| `crossValidatorSettings` | doc-vs-profile comparison (`nameComparisonMode`, `fuzzyThreshold`, …); API-only, no dashboard UI | mismatch/cross-check rejections |

Everything else on the root (`watchListCheckSettings`, `cryptoCheckSettings`,
`bankCardCheckSettings`, `kybIntegrationSettings`, `uiSettings`,
`duplicateSettings`, `sourceKeysSettings`, `applicantTags`, `supportEmail`,
`disableSumsubId`, `idDocServiceSettings`) is outside this skill's domain — don't
answer document questions from those blocks or offer to edit them here.

## Auth — App Token + secret (sandbox only)

Same model as the other write skills. See [`sumsub-api-auth`](../sumsub-api-auth/SKILL.md).

| Var | Example |
|---|---|
| `SUMSUB_APP_TOKEN` | `sbx:...` — sandbox App Token from the dashboard. |
| `SUMSUB_SECRET_KEY` | The paired secret shown once at token creation. |
| `SUMSUB_BASE` | Optional. Defaults to `https://api.sumsub.com`. |

**DEFAULT to effective recognition status (A).** Any question about what a country
/ doc type recognises, collects, or has available **right now** — including
phrasings like "what fields are currently available / recognised / collected",
"what fields are available for BRA", "what does the passport collect" — is about
the CLIENT'S effective state, so use **recognition status (A)**. The bare
catalogue is defaults only and will give a misleading answer ("available" in the
catalogue ≠ enabled for this client).

Only use the **catalogue query (B)** when the user explicitly asks what is
*possible* in the abstract or across countries — "which countries support field
X", "is gender ever extractable for passports", "what doc types exist for BRA".

A question about **expiry / validity checks** ("what validity checks apply",
"is an expired doc accepted") → use **(C)** below: report the `expirationCheckMode`
AND the concrete extension rule that applies (the 60+ / extension text), not just
the mode.

A broad question about how a document is handled ("acceptance rules", "what
settings apply", "what's configured for X") → use **(D)** below: read the
whole effective `(country, docType)` entry from GET globalSettings and report
**every** setting on it, on or off — don't curate or guess a subset, and don't omit
flags left at their default.

If unsure which the user means, pick **A** (effective) — it's the honest answer
and it also tells you what the catalogue allows.

> ⚠️ **Always go through these scripts — never read the Paler source.** If you
> happen to have the `paler` repo open, do NOT answer from its files
> (`documents-by-countries.json`, Java sources, etc.). Those contain only the
> built-in catalogue defaults — the **client's effective state**
> (`countryMappings` overrides + `ADVANCED_OCR`) is not in the code at all, only
> behind the API. Reading source can only give defaults and will silently answer
> the wrong question. The data must come from `get_global_settings.sh` /
> `get_supported_docs.sh` / `get_entitlements.sh`.

### A. Effective recognition status (what's really recognised)

```bash
S=${CLAUDE_SKILL_DIR}/scripts
$S/get_supported_docs.sh  > /tmp/catalogue.json
$S/get_global_settings.sh > /tmp/current.json
ADV=$($S/get_entitlements.sh ADVANCED_OCR >/dev/null 2>&1 && echo true || echo false)

$S/recognition_status.py BRA PASSPORT \
    --current-file /tmp/current.json \
    --catalog-file /tmp/catalogue.json \
    --advanced-ocr "$ADV"
# Omit the doc type to report ALL doc types for the country in one go
# (e.g. "fields for documents from Brazil"):
$S/recognition_status.py BRA \
    --current-file /tmp/current.json --catalog-file /tmp/catalogue.json --advanced-ocr "$ADV"
```
Reports each field as ✅ recognised (free / PAID) or ⬜ not recognised (with the
reason: default turned off / extra not enabled / ADVANCED_OCR off). Present this
to the user — it's the honest "what's actually recognised" answer.

### B. Catalogue query (what's possible)

1. **Fetch the catalogue once**: `get_supported_docs.sh > /tmp/catalogue.json`
   (reuse it for follow-ups — large and static within a session).
2. **Translate the question into a compact filter spec** (see below).
3. **Run the query** — spec on stdin, catalogue via `--data-file`:
   ```bash
   echo '{"countries": ["DEU"]}' \
     | ${CLAUDE_SKILL_DIR}/scripts/query_supported_docs.py --data-file /tmp/catalogue.json
   ```
4. **Report** the slice. If it's a `summary` (see decision rules), explain the
   coverage/distribution rather than inventing a list.

### C. Expiry / validity checks (mode + actual extension rule)

For any question about a document's **expiry / validity checks** ("what validity
checks apply", "is an expired X accepted", "validity rules for BRA ID") give
BOTH parts — don't stop at the mode:

1. **The mode** — resolve it through the full cascade, not just the per-country
   entry (see the four modes in
   [references/fields-glossary.md](references/fields-glossary.md)):
   `idDocSettings.countryMappings.<country>.<docType>.expirationCheckMode`
   → if absent, the **key-wide** `poiCheckSettings.expirationCheckMode` at the
   globalSettings **root** → if absent, the catalogue default for the pair.
   Both client values come from the same `get_global_settings.sh` response —
   don't stop at the `(country, docType)` entry: a missing per-country mode with
   `poiCheckSettings.expirationCheckMode` set means that key-wide mode IS active
   for the pair.
2. **The actual extension rule** — if the mode accepts extended documents
   (`generallyAcceptedRegulations` / `localRegulations`), pull the concrete rule
   that applies and show it. **Don't just offer to** — include it:
   ```bash
   $S/get_extension_rules.sh > /tmp/ext.json
   # then filter to the country/doc type, e.g.:
   python3 -c "import json;[print(r['docType']['idDocType'],'—',r.get('defaultDescription'))
     for r in json.load(open('/tmp/ext.json'))['rules']
     if r['docType']['country']=='BRA' and r['docType']['idDocType']=='ID_CARD']"
   ```
   e.g. for BRA/ID_CARD this surfaces "owner 60+ ⇒ valid indefinitely". That rule
   is the real answer to "what expiry checks apply" — the mode alone is incomplete.
3. **The other validity knobs** — a complete validity answer also reports, when
   set on the globalSettings root:
   - `poiCheckSettings.minimumResidualValidityInMonths` — ⚠️ **`0` means "accept
     any validity period" (no requirement)**, it is what the dashboard writes for
     the default radio — never report it as "must be valid ≥ 0 months". A
     non-zero N = the doc must remain valid at least N more months at check time
     (stricter than "not expired"; the dashboard's custom option defaults to 3).
   - `ongoingMonitoringSettings.idDocExpireInDays` (with `enabled`) — expiry
     monitoring after approval: the doc is flagged N days before it expires
     (dashboard default 7). Absent/0 = no expiry alerting. The whole section is
     licence-gated (`ONGOING_MONITORING_EXPIRED_DOCS` background-check target).
   Both are key-wide (no per-country variant) — read them from the same
   `get_global_settings.sh` response.

   **Where the key-wide mode is edited:** dashboard → Global Settings → User
   Verification → ID verification → "ID doc expiry settings". That screen only
   offers `strict` ("respect validity period"), `generallyAcceptedRegulations`
   and, via its extra checkbox, `localRegulations` — key-wide `allowExpired` is
   not settable from the dashboard (per-country entries can still have it via
   the Supported Documents drawer or the API).

### D. Full settings dump (everything that's on/off)

For a broad "how is this document handled / what's configured" question, don't
hand-pick a subset — read the **whole** effective `(country, docType)` entry and
report every setting on it.

```bash
$S/get_global_settings.sh > /tmp/current.json   # client's effective settings
$S/get_supported_docs.sh  > /tmp/catalogue.json  # catalogue, for the default baseline
# Pull the entry the client actually has (override), e.g. BRA/ID_CARD:
# NOTE: in GET globalSettings the map is nested under idDocSettings.countryMappings
# (NOT top-level — that's only the catalogue GET). Using the wrong path → KeyError.
python3 -c "import json;print(json.dumps(
  json.load(open('/tmp/current.json'))['idDocSettings']['countryMappings'].get('BRA',{}).get('ID_CARD',{}),
  indent=2, ensure_ascii=False))"
```

Then present every key on that entry as a setting — `supported`,
`sidesSelectionMode` / `doubleSided`, `shouldBeSigned`, `acceptDigitalDoc`,
`acceptScreenshots`, `expirationCheckMode`, `ocrSettings`, sub-type flags,
`defaultFields` / `availableFields`, and anything else present — translating each to
its UI meaning via [references/fields-glossary.md](references/fields-glossary.md).

Rules for an honest dump:
- **Don't curate.** Walk the keys that are actually on the entry; don't decide some
  are "not relevant". A setting you skip reads as "not configured".
- **Defaults are absent (`NON_NULL`).** A missing key is at its default, not off-
  screen. If the client has no override for the pair at all, the whole entry is
  absent — fall back to the catalogue entry (`/tmp/catalogue.json`) for the baseline
  and say these are Sumsub defaults, not client settings.
- **Report independent flags independently.** In particular `acceptDigitalDoc`
  (uploaded files/scans/PDFs) and `acceptScreenshots` (screenshots) are separate
  checks — state each on its own; never merge them or say "only live camera photos".
- **Expiry:** `expirationCheckMode` missing on the entry does NOT mean catalogue
  default — check the key-wide `poiCheckSettings.expirationCheckMode` at the
  globalSettings root first (cascade in **C**). When the effective mode accepts
  extended docs, also surface the concrete extension rule (see **C**) — the mode
  alone is incomplete.

## Procedure (edit a client's supported documents) — read-modify-write + PUT

The endpoint is replace-all, so edits are read-modify-write: fetch the current
map, let the builder merge your changes into it locally, PUT the full result.
Both input files are required by the builder.

1. **Read the catalogue and the CURRENT settings** (fetch `current.json` fresh —
   a stale snapshot would revert edits made in between):
   ```bash
   ${CLAUDE_SKILL_DIR}/scripts/get_supported_docs.sh  > /tmp/catalogue.json
   ${CLAUDE_SKILL_DIR}/scripts/get_global_settings.sh > /tmp/current.json
   ```

2. **Translate the request into a compact change spec** (see below) — only the
   fields you want to change, per `(country, docType)`.

3. **Build the full payload** (current map + merged changes):
   ```bash
   echo '<change spec>' | ${CLAUDE_SKILL_DIR}/scripts/build_country_mappings.py \
       --current-file /tmp/current.json --catalog-file /tmp/catalogue.json > /tmp/payload.json
   ```
   The script validates enums and that each field is in the right column, and
   prints a `Field changes:` summary. It refuses to auto-move a field to the other
   column (that would silently replace the other column's list) — fix the spec if
   it errors. A brand-new `(country, docType)` override is seeded with the
   catalogue defaults for `supported`, `doubleSided`, `doubleSidedCanBeChanged`
   and `shouldBeSigned` (spec values win; a null catalogue value stays absent), so
   the new entry keeps behaving like the default it shadows — e.g. `doubleSided`
   null would otherwise read as "any side", dropping the catalogue's two-sides
   requirement. And whenever the spec sets `sidesSelectionMode`, the deprecated
   `supported`/`doubleSided` pair is synced to the matching legacy values (same
   dual-write the dashboard does), so pre-`sidesSelectionMode` readers see the
   same behavior. Both are reported in the summary.

4. **If the change sets any `extraFields`, verify the ADVANCED_OCR entitlement**
   (billed add-on; without it the backend silently drops them):
   ```bash
   ${CLAUDE_SKILL_DIR}/scripts/get_entitlements.sh ADVANCED_OCR
   ```
   If not enabled, warn the user and don't proceed with extra fields. Default
   Fields are not gated.

4b. **Critical fraud settings need an explicit warning.** If the change sets
   `acceptScreenshots: true` (disables screenshot protection) or
   `acceptDigitalDoc: true` (accepts easily-modified uploaded files), the build
   script prints a `warning:` — relay it to the user verbatim and get a clear
   "yes" before applying. Enabling screenshots especially may approve fake
   applications and expose the client to penalties/chargebacks. (Turning these
   OFF is safe and needs no special warning.)

5. **Show the diff and WAIT for explicit confirmation.** Diff the payload against
   the same `current.json` it was built from (don't hand-write an inline
   `python3 -c` diff):
   ```bash
   ${CLAUDE_SKILL_DIR}/scripts/diff_country_mappings.py \
       --current-file /tmp/current.json --payload-file /tmp/payload.json
   ```
   Entries the builder carried over unchanged are silent, so the diff shows only
   your changes. Anything showing as REMOVED that you didn't intend means the
   payload was built from the wrong/stale snapshot — rebuild, don't PUT. This is a
   workspace-wide change — never apply without an explicit "yes".

6. **PUT** the confirmed payload:
   ```bash
   ${CLAUDE_SKILL_DIR}/scripts/put_country_mappings.sh /tmp/payload.json
   ```

7. **Report** the HTTP status and what changed. On a 4xx, surface the body
   verbatim. If you set `extraFields` without ADVANCED_OCR, re-read the settings
   and note the extra fields were dropped server-side.

> **Changing one field in a column without losing the others:** a column list in
> the spec replaces that column wholesale. To turn ON one more extra field while
> keeping the existing ones, first read the current enabled set
> (`recognition_status.py`) and pass the FULL intended `extraFields` list.

## Procedure (remove / restore default) — PUT

To restore a `(country, docType)` to the catalogue default, remove its override
from the full map and PUT the result:

```bash
${CLAUDE_SKILL_DIR}/scripts/get_global_settings.sh > /tmp/current.json
${CLAUDE_SKILL_DIR}/scripts/remove_country_mapping.py \
    --current-file /tmp/current.json BRA:ID_CARD > /tmp/payload.json   # full map MINUS the entry
# show the diff (the removal shows as REMOVED), confirm, then PUT:
${CLAUDE_SKILL_DIR}/scripts/diff_country_mappings.py \
    --current-file /tmp/current.json --payload-file /tmp/payload.json
${CLAUDE_SKILL_DIR}/scripts/put_country_mappings.sh /tmp/payload.json   # PUT (replace-all)
```

### Change spec

A **sparse** spec — list only the fields you want to change per `(country,
docType)`. Field keys mirror the dashboard "Fields management" screen (two
checkbox columns: **Default Fields** / **Extra Fields**).

```yaml
changes:
  - country: DEU                   # ISO-3
    docType: ID_CARD               # IdDocType
    expirationCheckMode: strict    # scalar settings — merged locally, others preserved
    ocrSettings: {ocrRuleMode: MRZ_DOC}
  - country: BRA
    docType: PASSPORT
    extraFields: [placeOfBirth, gender]   # REPLACES the Extra Fields column (PAID)
```

This covers the main "Supported ID Documents" screen buttons:
- **Manage documents** — set fields / modes / subtypes (keys below)
- **Change documents sides** — set `sidesSelectionMode`
  (`oneSide`/`twoSides`/`smartMode`; `disabled` = the "Don't accept" option)
- **Restore default settings** — NOT done here; it's a removal → use the
  separate removal procedure (`remove_country_mapping.py`) above; the builder
  refuses `remove`.

How it maps to recognition and cost (the script reports this):

- **Default Fields** — free; checked fields are recognised. Omit a field to
  uncheck it (stop recognising). Default fields are checked by default.
- **Extra Fields** — recognised only when checked, and that requires the
  `ADVANCED_OCR` entitlement (step 4). These are the paid fields.
- A field's column is **fixed by the catalogue** — you can't list a field under
  the wrong column. If you do, the script **errors out** (it will not auto-move the
  field, because that would silently replace the other column's list) and tells you
  the correct column — fix the spec. Read the catalogue (`{country, docType}` query)
  to see which fields live in which column.
- The script prints a `Field recognition result:` summary per doc listing what's
  recognised free vs. PAID. **Show it to the user on the confirmation step** — it
  speaks the same language as the UI ("Default Fields" / "Extra Fields").

On the wire `extraFields` becomes the API's `availableFields` — the script maps
it for you; you only deal in UI terms.

**Every other control on the "Fields management" screen is settable too** — set
the matching key in the change spec. The full UI-control → spec-key table (with
enum values and mappings) is in
[references/fields-glossary.md](references/fields-glossary.md). Highlights:

| User asks | Spec key | Value |
|---|---|---|
| accept docs sent as images/files (scans, PDFs) — not just live camera photos | `acceptDigitalDoc` | `true` |
| accept screenshots specifically | `acceptScreenshots` | `true` |
| MRZ mode | `ocrSettings: {ocrRuleMode: MRZ_DOC}` | |
| prefer non-latin recognition | `ocrSettings: {preferNonLatinFromOcr: true}` | |
| expiry policy | `expirationCheckMode` | `allowExpired`/`strict`/`generallyAcceptedRegulations`/`localRegulations` |
| accept only/reject some subtypes | `allowedOcrDocumentTypes` / `forbiddenOcrDocumentTypes` | subtype id list |
| hide subtypes in WebSDK | `disableDocumentReferences` | `true` |
| accept this doc type at all | `sidesSelectionMode` | a positive mode to accept; `disabled` to stop accepting |
| how many sides required | `sidesSelectionMode` | `smartMode`/`oneSide`/`twoSides`/`disabled` |

The script validates enum values (`expirationCheckMode`, `ocrRuleMode`) and fails
on typos. Truly internal keys not in the glossary (`shouldBeMaskedSettings`,
`documentReferences`, …) are passed through from the baseline untouched — don't
invent values for them.

**Deprecated keys are NOT settable** — `supported`, `doubleSided`,
`doubleSidedCanBeChanged`, `acceptedAsPoa`, `acceptSameDocAsPoa` are deprecated
on the backend; `build_country_mappings.py` rejects them with the replacement to
use (sides/acceptance → `sidesSelectionMode`; the POA flags have none — decline
the edit). You'll still see them in GET responses — read them for context, never
put them in a change spec. The ONE place they're still written is the builder's
own seeding of a brand-new override, which copies their defaults from
`GET /supportedDocs/documentsByCountries` so the new entry keeps behaving like
the catalogue default for legacy readers — that happens automatically, not via
the spec.

**Gated keys are NOT settable either** — `shouldBeSigned` (dashboard-editable
only behind the `showRejectByMissingSignatureSetting` feature flag; turns on
auto-rejection of unsigned documents) and `shouldBeMasked` (masking of legally
protected national IDs — JPN/KOR/NLD/NGA/SGP; for NGA ID_CARD even the dashboard
allows only Sumsub staff). `build_country_mappings.py` rejects both. If asked to
change them, explain the gate and direct the user to the dashboard (with the
flag enabled) or Sumsub support. Reading/reporting them is fine.

The valid entries for `defaultFields` / `availableFields` are **per country and
doc type** — not a fixed global list. Read the catalogue first (a `field`-level
or `{country, docType}` query) to learn the valid field names before building a
change spec.

## Filter spec

All keys optional. Different keys combine with AND; lists within a key are OR.

```yaml
countries: [DEU, FRA]            # ISO-3 codes
docTypes:  [ID_CARD, DRIVERS]    # document types
field:     placeOfBirth          # find where this OCR field exists (inverse query)
fieldKind: available | default | any   # which list to search field in (default: any)
flags:                           # match per-doc boolean flags
  supported: true                # IMPLICIT DEFAULT — unsupported docs are excluded
  doubleSided: false             #   unless you set supported:false explicitly
output:    auto | list | summary # default: auto
limit:     100                   # max items in a list before truncation
```

### Examples

| Question | Spec |
|---|---|
| What can I collect for a German ID card? | `{"countries":["DEU"],"docTypes":["ID_CARD"]}` |
| Which countries/types expose the `category` field? | `{"field":"category","fieldKind":"available"}` |
| Where is `parentName1` collectable at all? | `{"field":"parentName1"}` |
| Which docs are double-sided in France? | `{"countries":["FRA"],"flags":{"doubleSided":true}}` |
| Include unsupported docs too | `{"countries":["DEU"],"flags":{"supported":false}}` |

## List vs. summary (auto mode)

The script returns `mode: "list"` for compact results and `mode: "summary"`
when a flat list would be useless:

- **Near-universal field** (present in ≥ 80% of matched pairs, e.g. `dob`,
  `firstName`): returns coverage + `byDocType`; if the field is absent from only
  a short list, that complement is returned as `absentIn`.
- **Too many matches** (a field-presence result over 200 pairs): returns
  coverage + `byDocType` + `topCountries` distribution instead of a truncated
  list.

To force a flat list anyway, set `output: list` and raise `limit`.

## Gotchas

- **Unsupported documents are hidden by default.** A doc with `supported: false`
  can't be configured, so it's excluded unless you pass `flags.supported: false`.
  This keeps coverage math honest (otherwise empty-field unsupported pairs
  dilute every percentage).
- **This is the built-in catalogue, not the client's overrides.** What a specific
  client actually has enabled lives in their global settings
  (`idDocSettings.countryMappings`) — a different endpoint. Use this skill to
  learn what's *possible*, not what a given account has *configured*.
- **`PROFILE_SCREENSHOT` and a long tail of non-POI types** (`OTHER`, `VISA`,
  `UTILITY_BILL`, …) live in this catalogue too. Filter by `docTypes` if the
  user only cares about passports / ID cards / driver's licences.
- **Verification Level settings override Global Settings.** This skill edits the
  client's *global* supported-documents config. A specific Verification Level can
  carry its own supported-documents overrides that take **higher priority** for
  applicants on that level. The level opts into this with `useCustomIdDocSettings:
  true` — when set, the level's own `idDocSettings.countryMappings` fully replaces
  global for that level (a flag absent there is at its default, ignoring global).
  So a global change may not take effect for a level that overrides it — if a user
  reports "my change didn't apply", read the level and check `useCustomIdDocSettings`
  and its `idDocSettings`. To actually edit a level's document settings, use the
  [`sumsub-create-level`](../sumsub-create-level/SKILL.md) skill (GET the level,
  change the flag in its `idDocSettings`, PATCH the **full** level back).
