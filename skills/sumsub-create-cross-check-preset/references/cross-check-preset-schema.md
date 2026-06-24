# CrossCheckPreset — schema reference

Source: Sumsub OpenAPI (`components.schemas.CrossCheckPresetCreateRequest`, `CrossCheckPresetUpdateRequest`, `CrossCheckPresetSettings`).

## Top-level fields (`CrossCheckPresetRequest`)

| Field | Type | Notes |
|---|---|---|
| `id` | hex string | Server-assigned on POST; **required on PATCH**. Never set on POST. |
| `title` | string, 1–256 chars | **Required.** Shown in the dashboard preset list. |
| `description` | string, ≤512 chars | Optional. |
| `mode` | string enum | **Required.** `basic` (only mode supported via API) or `advanced` (dashboard-only — POST/PATCH returns 403). |
| `basicSettings` | `CrossCheckPresetSettings` | Used when `mode=basic`. Holds the name/address comparison modes. |
| `rules` | `CrossCheckRule[]`, ≤200 | Used in `advanced` mode only; ignore for this skill. |

## `CrossCheckPresetSettings`

| Field | Type | Default behavior | Notes |
|---|---|---|---|
| `nameComparisonMode` | string enum | Sumsub picks the workspace default | One of `strict`, `weakContainment`, `def`, `ai`. Deprecated values (`fuzzy`, `containment`, `fuzzyContainment`) still parse but should NOT be set on new presets. |
| `addressComparisonMode` | string enum | Sumsub picks the workspace default | One of `strict`, `fuzzy`. |
| `ignoreMiddleNameMismatch` | boolean | `false` | If true, a different middle name doesn't trigger a name mismatch. |
| `ignoreProvidedInfoMismatch` | boolean | `false` | If true, user-typed info that disagrees with the document is not flagged. |

## `NameComparisonMode` semantics

| Value | Meaning |
|---|---|
| `strict` | Exact-match after light normalisation (case, diacritics). |
| `weakContainment` | Token-level containment; "Jon Smith" matches "Jonathan Andrew Smith". |
| `def` | Sumsub's recommended default; balances strictness with approval rate. |
| `ai` | ML-based comparison; tolerant of nicknames, transliterations, and word order. |
| `fuzzy` *(deprecated)* | Edit-distance fuzzy match. Replaced by `ai`. |
| `containment` *(deprecated)* | Replaced by `weakContainment`. |
| `fuzzyContainment` *(deprecated)* | Combination of the two deprecated modes. |

## `AddressComparisonMode` semantics

| Value | Meaning |
|---|---|
| `strict` | Character-level match after normalisation. |
| `fuzzy` | Word-order- and abbreviation-tolerant. |

## Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/resources/api/agent/crossCheckPresets` | API (App Token) | Create. Returns `CrossCheckPresetDto` with assigned `id`. |
| `PATCH` | `/resources/api/agent/crossCheckPresets` | API (App Token) | Update by `id` in body. |
| `GET` | `/resources/api/agent/crossCheckPresets/{id}` | API (App Token) | Read one. |

There is no public-API list or DELETE endpoint — to find a preset by
title you need to remember its `id` from creation. Browsing all presets
or deleting one is done by an operator in the Sumsub dashboard UI.

## Gotchas

- **`mode: advanced` is rejected on the API** with `403 Advanced cross-check
  presets cannot be managed via API`. If the user needs advanced rules, the
  dashboard is the only path.
- **Rule evaluation runs on PATCH/POST**. The server runs `testAndThrow` on
  the supplied `rules` (advanced mode) and rejects the entire body if any
  rule fails. For basic mode this is a no-op.
- **The default preset always exists** and applies to any level that
  doesn't specify `crossCheckPresetId`. Creating a new preset doesn't
  change anything until you attach it.
- **Attaching to a level** is a separate step — set `crossCheckPresetId`
  on the level via `sumsub-create-level` or direct PATCH.

## Defaults guidance — keep them unless you have a reason

Sumsub's default cross-check preset has been tuned across many real-world
flows. Common reasons people *think* they need a custom preset but
shouldn't:

| User says | Better answer |
|---|---|
| "Our region has lots of name variants" | The `def` and `ai` modes already handle this. |
| "Addresses don't match because of abbreviations" | The default `addressComparisonMode` already tolerates common abbreviations. |
| "We want stricter checks" | Stricter = lower approval rate. Cite the trade-off explicitly before agreeing. |
| "Users have middle names that differ" | The default already ignores middle-name mismatches in most cases. |

Legitimate reasons to override:
- A specific regulator demands exact-match on a specific field.
- A specific market has a known transliteration mismatch the defaults handle poorly (and the user has data to prove it).
- A/B test for conversion (with metrics and rollback plan).
