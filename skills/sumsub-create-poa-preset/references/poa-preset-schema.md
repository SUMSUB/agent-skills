# PoaStepSettings — schema reference

Source: Sumsub OpenAPI (`components.schemas.PoaStepSettings`, plus `PoaDocumentSettings`, `PoaTypeSettings`, `PoiAsPoaSettings`, `CrossValidatorSettings`).

## Top-level fields (`PoaStepSettings`)

| Field | Type | Notes |
|---|---|---|
| `name` | string, ≥1 char | **Required**. Shown in the dashboard preset list. Must be a non-empty string; need not be unique. |
| `desc` | string | Optional description. |
| `includedCountries` | string[] ISO-3 | Country **allow-list**. If set, the preset only applies when the applicant is in one of these countries. |
| `excludedCountries` | string[] ISO-3 | Country **block-list**. If set, the preset *does not* apply for these countries (falls back to the level's default behavior). Mutually exclusive with `includedCountries`. |
| `settings` | `PoaDocumentSettings` | **Defaults applied everywhere** (subject to the country scope above). |
| `changedSettingsByCountry` | `Map<ISO-3, PoaDocumentSettings>` | Per-country overrides. Whole settings block per key — Sumsub does NOT merge with `settings` at the field level; whatever you put here replaces the defaults for that country. The skill builder accepts a partial spec and only emits the keys you set, but downstream Sumsub treats present fields as the full per-country answer. |
| `sharedTo` | array | Optional cross-tenant sharing references. Pass-through. |
| `id`, `clientId`, `createdAt`, `createdBy`, `modifiedAt`, `copiedFrom`, `copyOf` | various | Server-populated. Do not send. |

## `PoaDocumentSettings`

| Field | Type | Notes |
|---|---|---|
| `acceptDocScreenshot` | boolean | Allow phone screenshots of e-statements / bills. |
| `acceptMultiplePages` | boolean | Allow a multi-page POA upload. |
| `acceptableLanguages` | string[] | ISO-639-1 language codes — limits which OCR languages the validator accepts. |
| `allowedAddressTypes` | string[] | Which address types pass. Observed values: `dwelling` (residential), `poBox` (P.O. boxes globally), `poBoxSpecialCountries` (P.O. boxes only in countries where they are legally accepted as residence). |
| `allowedTypesSettings` | `Map<PoaCompanyContactType, PoaTypeSettings>` | Per provider-type rules (see below). |
| `crossValidatorSettings` | `CrossValidatorSettings` | Name/address comparison between POI and POA. |
| `poiAsPoaSettings` | `PoiAsPoaSettings` | Whether the identity doc can also count as proof of address. |
| `requirePoiPoaCountryMatch` | boolean | Reject if POI country ≠ POA country. |
| `useOnlyIssueDateForExpiredCheck` | boolean | Use only the document's `issuedDate` (not `expiry`) when checking "still fresh enough" against `validMonths`. |

## `PoaCompanyContactType` (provider-type enum — keys of `allowedTypesSettings`)

`bank`, `utilityProvider`, `governmentOrganization`, `mobileOperator`, `other`.

## `PoaTypeSettings` (one per provider type)

| Field | Type | Notes |
|---|---|---|
| `validMonths` | number | How many months a doc of this type is accepted past its issue date. |
| `acceptUnconventionalProviders` | boolean | Allow non-mainstream providers (e.g. a small local co-op bank). Pairs with `poaUnconventionalProviderSettings`. |
| `allowedSubTypes` | `PoaSubType[]` | Which sub-types this provider may produce. Enum below. |
| `forbiddenDocumentNames` | string[] (≤300) | OCR'd doc names that auto-reject (e.g. `"Welcome packet"`). |
| `forbiddenOrgNames` | string[] (≤300) | Organization names to reject. |
| `forbiddenOrgWebsites` | string[] (≤300) | Org websites to reject. |
| `poaUnconventionalProviderSettings` | object | `{allowedOrgNames[], allowedOrgWebsites[]}`. Only consulted when `acceptUnconventionalProviders=true`. |

## `PoaSubType` (enum — `allowedSubTypes` values)

`statement`, `voterRegistration`, `taxBill`, `telecom`, `utilityBill`, `bankStatement`, `bankLetter`, `lease`, `universityLetter`, `employmentLetter`, `other`.

Typical pairings (observed in real-world configs):
- `bank` → `[bankStatement, bankLetter, other]`
- `utilityProvider` → `[telecom, utilityBill, other]`
- `governmentOrganization` → `[statement, voterRegistration, taxBill, other]`
- `other` → `[lease, other, universityLetter]`
- `mobileOperator` → no sub-types (handled separately)

## `PoiAsPoaSettings`

| Field | Type | Notes |
|---|---|---|
| `acceptPoiAsPoa` | boolean | Master switch — allow an identity document to also serve as proof of address. |
| `acceptSamePoiAsPoa` | boolean | Allow the **same physical document** that was used for POI to be re-used for POA. |
| `validMonths` | number | How recent the POI must be to count as POA. |
| `allowedTypes` | string[] | `IdDocType` values eligible. Production data uses `[PASSPORT, ID_CARD, RESIDENCE_PERMIT, DRIVERS]`. |

## `CrossValidatorSettings`

| Field | Type | Notes |
|---|---|---|
| `nameComparisonMode` | enum | `strict`, `weakContainment`, `def`, `ai`, `fuzzy`, `containment`, `fuzzyContainment`. |
| `addressComparisonMode` | enum | `strict` or `fuzzy`. |
| `fuzzyThreshold` | number 0-1 | Similarity threshold when `*ComparisonMode = fuzzy`. Production data uses ~0.75. |
| `ignoreMiddleNameMismatch` | boolean | Pass when only middle names differ. |
| `ignoreFixedInfo` | boolean | Skip applicant-`fixedInfo` comparison entirely (only check against POI doc data). |

## Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/resources/api/agent/poaStepSettings` | API (App Token) | Create a new preset. Body must NOT carry `id`. |
| `PATCH` | `/resources/api/agent/poaStepSettings` | API (App Token) | Update an existing preset. Body MUST carry `id`. |
| `GET` | `/resources/api/agent/poaStepSettings/{id}` | API (App Token) | Read one preset (verify what landed; resolve `name` from a known `id`). |

There is no list or DELETE endpoint on the public API — to find a preset
by name you need to remember its `id` from creation. Browsing all presets
or deleting one is done by an operator in the Sumsub dashboard UI.

## Patterns observed in 16 real-world presets

| Pattern | Frequency |
|---|---|
| Global preset (no country scope) | 12 / 16 |
| `excludedCountries` only | 3 / 16 |
| `includedCountries` only | 1 / 16 (Brazil-specific) |
| Has per-country overrides | 4 / 16 (BRA, ALA, AFG, etc.) |
| `poiAsPoaSettings` enabled | 16 / 16 (always present, often with same-doc + 3-month validity) |
| `crossValidatorSettings` enabled | 16 / 16 (typically `weakContainment` + `fuzzy` + `0.75`) |
| Provider keys covered | `bank` + `utilityProvider` + `governmentOrganization` + `mobileOperator` + `other` is the standard "full" set |

## Common gotchas

- **`includedCountries` and `excludedCountries` are mutually exclusive.** Sumsub silently uses whichever is non-empty if both are set; the builder rejects upfront.
- **ISO-3 country codes** (not alpha-2). `USA`, `DEU`, `BRA` — not `US`, `DE`, `BR`.
- **`changedSettingsByCountry[<country>]` replaces, not merges.** When you override a country, include every field you care about — Sumsub uses the per-country block as the answer for that country, not as a delta on `settings`. The skill's `byCountry` shorthand emits what you ask for; if you want to keep `settings`-level fields, restate them in the override.
- **`acceptSamePoiAsPoa: true` requires `acceptPoiAsPoa: true`.** The dashboard greys out same-doc when POI-as-POA is off; Sumsub validates this server-side.
- **Validity-month logic** — by default Sumsub checks "doc issue date is within `validMonths` ago AND not expired." Setting `useOnlyIssueDateForExpiredCheck=true` removes the expiry check (useful for docs without explicit expiry dates).
- **Unconventional providers** are off by default; turning them on without populating `allowedOrgs.names` / `allowedOrgs.websites` will accept many noisy results.
- **Attaching to a level** is a separate step. After creation, edit any `PROOF_OF_RESIDENCE` doc-set on the relevant level: `poaStepSettingsId = "<new preset id>"`. See the `sumsub-create-level` skill.
- **`allowedTypesSettings` map keys are provider categories, not document sub-types.** Keys must be one of `bank | utilityProvider | governmentOrganization | mobileOperator | other`. Sending a sub-type name (e.g. `"utilityBill"` or `"bankStatement"`) as a map key returns 400. Sub-types go inside `allowedSubTypes` of the matching provider entry.
