# KYT Rule Schema Reference

## KytTxnRule — All Fields

### Identification & Metadata

| Field | Type | Description |
|---|---|---|
| `id` | String | Auto-assigned primary key. **Never send on create.** |
| `name` | String | Immutable slug auto-generated from `title` on creation. Max 64 chars. |
| `title` | String | Required. Human-readable name shown in UI. Max 128 chars. |
| `desc` | String | Optional detailed description. |
| `bundleName` | String | Bundle this rule belongs to. Max 128 chars. |
| `clientId` | String | Set from auth context. **Never send.** |

### Execution

| Field | Type | Default | Description |
|---|---|---|---|
| `types` | `List<String>` | — | Required. Transaction types (see below). Min 1 value. |
| `stage` | String | `eval` | `eval` only (do not set `pre` or `post` via this skill). |
| `priority` | Integer | — | Higher value = evaluated first. |
| `stopOnMatch` | Boolean | `false` | Stop processing remaining rules on match (only when not in dryRun). |
| `sourceKeys` | `List<String>` | — | Top-level source-key filter. If set and non-empty, rule only fires if the transaction's source key is in this list. |

### Conditions

| Field | Type | Description |
|---|---|---|
| `conditionEl` | String | SumScript boolean expression. Required for non-scheduled eval rules. |
| `varDefinitions` | Object | Variable definitions for parameterized rules. Omit unless needed. |
| `varValues` | Object | Variable runtime values. Omit unless needed. |

### Actions on Match

| Field | Type | Default | Description |
|---|---|---|---|
| `score` | Integer | `0` | Risk score added when rule matches. Use `0` when using `addScoreIf`. |
| `action` | String | `score` | `score` \| `onHold` \| `awaitUser` \| `reject`. Strongest action across all matched rules wins. |
| `tags` | `List<String>` | — | Tags assigned to the transaction on match. Auto-created in KYT settings if new. |
| `caseAction` | Object | — | Case creation config (see Case Action below). Omit if not needed. |
| `applicantChange` | Object | — | Applicant workflow change on match. Required for scheduled rules. |
| `applicantActions` | Object | — | Additional applicant actions. Required for scheduled rules if no `applicantChange`. |
| `txnActions` | `List<Object>` | — | Transaction property actions (e.g. `setProp`). |

### Scheduling (scheduled rules only)

| Field | Type | Description |
|---|---|---|
| `noEventTrigger` | Object | Trigger config for `scheduledEvent` rules (see Scheduled Rules section below). |

### Server-assigned (never send)

`actual`, `revision`, `scope`, `bgCheckTargets`,
`createdAt`, `modifiedAt`, `archivedAt`, `createdBy`, `modifiedBy`

---

## Transaction Types

| Type | Description | Required entitlement |
|---|---|---|
| `finance` | Financial transactions with counterparty | `KYT` |
| `travelRule` | Travel Rule transactions | `TRAVEL_RULE` |
| `kyc` | KYC / verification session events | `KYT` |
| `userPlatformEvent` | Login, logout, password change, 2FA events | `KYT_ANTI_FRAUD` + `KYT` |
| `scheduledEvent` | Periodic applicant-based events (no incoming txn) | `TM_SCHEDULED_EVENTS` + `KYT` |

Types may be combined except `scheduledEvent` which must be alone.

---

## Rule Statuses

| Status | `disabled` | `dryRun` | Behaviour |
|---|---|---|---|
| `testMode` (default) | `false` | `true` | Evaluates; result goes to `dryScore` only |
| `active` | `false` | `false` | Live — affects real score and action |
| `inactive` | `true` | — | Not evaluated |

**All new rules start in testMode.** Activate in the dashboard.

---

## SumScript Expression Root (`KytTxnExpressionRoot`)

The root context available inside `conditionEl`:

| Field | Type | Description |
|---|---|---|
| `data` | `TxnDataExpressionData` | Transaction data provided by the client |
| `txn` | `TxnExpressionData` | Sumsub-side transaction metadata |
| `applicant` | `KytTxnApplicantExpressionData` | Applicant as known to Sumsub |
| `counterparty` | `TxnParticipantExpressionData` | The other party in the transaction |
| `remitter` | `TxnParticipantExpressionData` | Sender (applicant on outgoing, counterparty on incoming) |
| `beneficiary` | `TxnParticipantExpressionData` | Receiver (applicant on incoming, counterparty on outgoing) |
| `txns` | `KytTxnExpressionTypes` | Transaction aggregates (lazy-loaded). See Aggregation section. |
| `clientLists` | `ClientLists` | Named client lists — `clientLists.listName.contains(value)` or `value IN clientLists.listName` |
| `poi` | `PoiExpressionData` | Applicant proof of identity |
| `poa` | `PoaExpressionData` | Applicant proof of address |
| `questionnaires` | Object | Questionnaire values — `questionnaires[qId][sectionId][itemId]` |
| `preScoringContext` | `PreScoringContextExpressionData` | Data from pre-scoring runners (AML, crypto, etc.) |
| `currentScore` | INT | Accumulated score from preceding rules |
| `currentMatchedRuleNames` | `STRING[]` | Names of already-matched rules this session |
| `txnFraudInfo` | `KytTxnFraudExpressionData` | Fraud analysis data (behavioral, device, IP, email, phone) |

---

## `data` — Transaction Data (`TxnDataExpressionData`)

| Field | Type | Description |
|---|---|---|
| `data.info` | `TxnInfoExpressionData` | Financial info (see below) |
| `data.type` | STRING | Transaction type: `finance`, `kyc`, `travelRule`, `userPlatformEvent`, `scheduledEvent` |
| `data.txnId` | STRING | Client-supplied transaction ID |
| `data.txnDate` | DATE | Transaction date (client-side UTC) |
| `data.sourceKey` | STRING | Source key assigned to the transaction |
| `data.applicant` | `TxnParticipantExpressionData` | Applicant as reported in the transaction payload |
| `data.userPlatformEventInfo` | Object | For `userPlatformEvent` type: `.type` (`login`\|`failedLogin`\|`signup`\|…), `.twoFaUsed`, `.passwordHash` |

### `data.info` — Financial Info (`TxnInfoExpressionData`)

| Field | Type | Description |
|---|---|---|
| `data.info.amount` | FLOAT | Amount in source currency |
| `data.info.amountInDefaultCurrency` | FLOAT | Amount normalized to tenant default currency **Use this for threshold checks** |
| `data.info.currencyCode` | STRING | Source currency code (e.g. `USD`, `EUR`) |
| `data.info.defaultCurrencyCode` | STRING | Tenant default currency code |
| `data.info.currencyType` | STRING | `fiat` \| `crypto` |
| `data.info.direction` | STRING | `in` (received) \| `out` (sent) |
| `data.info.type` | STRING | Transfer subtype: `transfer`, `deposit`, `withdrawal` |
| `data.info.paymentDetails` | STRING | Free-text payment comment |
| `data.info.mcc` | INT | Merchant category code |

---

## `applicant` — Applicant (`KytTxnApplicantExpressionData`)

| Field | Type | Description |
|---|---|---|
| `applicant.externalUserId` | STRING | Client-side user ID |
| `applicant.country` | STRING | ISO 3166-1 alpha-3 country |
| `applicant.fullName` | STRING | Full name |
| `applicant.email` | STRING | Email address |
| `applicant.phone` | `PhoneExpressionData` | `.number`, `.country` |
| `applicant.type` | STRING | `individual` \| `company` |
| `applicant.tags` | `STRING[]` | Applicant-level tags |
| `applicant.riskLabels.aml` | `STRING[]` | AML risk labels: `pep`, `sanctions`, `terrorism`, `crime`, `adverseMedia`, `fitnessProbity` |
| `applicant.riskLabels.crossCheck` | `STRING[]` | Cross-check signals: `addressCountryVsIpCountryMismatch`, `manyAccountDuplicates`, … |
| `applicant.riskLabels.device` | `STRING[]` | Device risk: `vpnUsage`, `torUsage`, `highRiskIp`, … |
| `applicant.review.decision` | STRING | `approved` \| `rejected` \| `resubmission` |
| `applicant.assessment.totalScore` | FLOAT | Aggregated applicant risk score |
| `applicant.fixedInfo` | `ApplicantInfoExpressionData` | `.country`, `.firstName`, `.lastName`, `.dob`, `.residenceCountry`, … |
| `applicant.checks.watchlist.matchStatuses` | `STRING[]` | Watchlist results: `unknown`, `no_match`, `potential_match`, `false_positive`, `true_positive` |

---

## `counterparty` / `remitter` / `beneficiary` (`TxnParticipantExpressionData`)

| Field | Type | Description |
|---|---|---|
| `.fullName` | STRING | Full name |
| `.externalUserId` | STRING | Client-side ID |
| `.email` | STRING | Email |
| `.phone` | STRING | Phone number |
| `.type` | STRING | `individual` \| `company` |
| `.residenceCountry` | STRING | ISO 3166-1 alpha-3 |
| `.address.country` | STRING | ISO 3166-1 alpha-3 |
| `.paymentMethod.accountId` | STRING | Bank account / card / crypto address |
| `.paymentMethod.type` | STRING | `card`, `account`, `crypto` |
| `.institutionInfo.code` | STRING | Bank BIC/SWIFT code |
| `.institutionInfo.name` | STRING | Bank name |
| `.device.ipInfo.country` | STRING | IP country (alpha-3) |

---

## `txn` — Sumsub Transaction Metadata (`TxnExpressionData`)

| Field | Type | Description |
|---|---|---|
| `txn.createdAt` | DATE | When the transaction was received by Sumsub |
| `txn.externalUserId` | STRING | Applicant external ID |
| `txn.tags` | `STRING[]` | Transaction-level tags already assigned |
| `txn.review.decision` | STRING | `approved` \| `rejected` \| `resubmission` |
| `txn.scoringResult.score` | INT | Final score after all rules |
| `txn.travelRuleInfo.status` | STRING | Travel rule state: `completed`, `counterpartyVaspNotFound`, `awaitingCounterparty`, … |

---

## `txns` — Aggregates (`KytTxnExpressionTypes`)

Access transaction aggregates via `txns.<type>.<groupBy>.<timeWindow>.<op>(...)`.

### Types

| Root field | Covers |
|---|---|
| `txns.finance` | Finance transactions |
| `txns.travelRule` | Travel Rule transactions |
| `txns.kyc` | KYC events |
| `txns.userPlatformEvent` | Platform events |

### Group By (chain after type)

| Modifier | Groups by |
|---|---|
| `.all` | All transactions |
| `.byApplicant` | Same applicant |
| `.byIp` | Same IP address |
| `.byDevice` | Same device fingerprint |
| `.byRemitter` | Same remitter |
| `.byCounterparty` | Same counterparty |
| `.byBeneficiary` | Same beneficiary |

### Direction / Status Filters (chain after group by)

| Modifier | Effect |
|---|---|
| `.in` | Incoming only |
| `.out` | Outgoing only |
| `.sameDirection` | Same direction as current |
| `.sameCounterparty` | Same counterparty external ID |
| `.excludeCurrent` | Exclude the current transaction |
| `.rejected` | Only rejected transactions |
| `.approved` | Only approved transactions |

### Time Windows (chain after filters)

| Modifier | Description |
|---|---|
| `.allTime` | All time |
| `.lastHours(n)` | Last N hours |
| `.lastDays(n)` | Last N days |
| `.lastWeeks(n)` | Last N weeks |
| `.lastMonths(n)` | Last N months |
| `.currentCalendarMonth` | This calendar month |
| `.lastCalendarMonth` | Previous calendar month |

### Aggregate Operations (terminal)

| Operation | Description |
|---|---|
| `.count()` | Number of matching transactions |
| `.sum(it.data.info.amountInDefaultCurrency)` | Sum of amounts |
| `.distinctCount(it.data.applicant.externalUserId)` | Distinct count |

**Examples:**
```
# More than 5 outgoing transfers by same applicant in last 24h
txns.finance.byApplicant.out.lastHours(24).count() > 5

# Total outgoing amount in last 30 days
txns.finance.byApplicant.out.lastDays(30).sum(it.data.info.amountInDefaultCurrency) > 100000

# Number of distinct counterparties in last week
txns.finance.byApplicant.lastWeeks(1).distinctCount(it.data.counterparty.externalUserId) > 10
```

---

## SumScript Operators

| Operator | Use |
|---|---|
| `AND` | Logical and (short-circuit) |
| `OR` | Logical or (short-circuit, stops at first true) |
| `EOR` | Eager OR — evaluates ALL branches (use for addScoreIf chains) |
| `NOT` | Logical not |
| `IN` | List membership: `"value" IN someList` |
| `==`, `!=` | Equality |
| `>`, `<`, `>=`, `<=` | Numeric comparison |
| `+`, `-`, `*`, `/` | Arithmetic |
| `addScoreIf(expr, score)` | Add score if expr is true; returns BOOL (side-effect function) |

String literals use single quotes: `'out'`, `'rejected'`.

---

## `addScoreIf` Pattern

Use when different sub-conditions should contribute different scores. Set payload `score: 0` and
`action: "score"` to avoid double-counting.

**EOR (independent flags — all evaluated):**
```
addScoreIf(data.info.amountInDefaultCurrency > 100000, 50) EOR
addScoreIf(applicant.country IN clientLists.sanctioned_countries, 100) EOR
addScoreIf("pep" IN applicant.riskLabels.aml, 75)
```

**OR (mutually exclusive tiers — stops at first match, highest tier first):**
```
addScoreIf(data.info.amountInDefaultCurrency > 1000000, 100) OR
addScoreIf(data.info.amountInDefaultCurrency > 100000, 50) OR
addScoreIf(data.info.amountInDefaultCurrency > 10000, 20)
```

---

## Scheduled Rules (`noEventTrigger`)

Used when `types: ["scheduledEvent"]`. Defines which applicants the rule fires for.

### Structure

```json
{
  "noEventTrigger": {
    "type": "byLevelName",
    "levelParams": {
      "levelName": "basic-kyc-level",
      "days": 365
    },
    "activateAt": "2025-01-01T00:00:00.000Z"
  }
}
```

| Field | Type | Description |
|---|---|---|
| `type` | String | `byLevelName` or `byCustomExpression` |
| `levelParams.levelName` | String | Required for `byLevelName`. Applicant level to target. |
| `levelParams.days` | Integer | Required for `byLevelName`. Days after review date. |
| `customExpressionParams.applicantFilter` | String | Required for `byCustomExpression`. SumScript expression. |
| `activateAt` | Date | Only process applicants created after this date. |

### Required Applicant Action (at least one)

```json
{
  "applicantChange": {
    "type": "applicantLevel",
    "applicantLevel": {
      "levelName": "target-level-name",
      "resetDocSets": [{"idDocSetType": "SELFIE"}]
    }
  }
}
```

`applicantChange.type` options: `applicantLevel`, `finalRejection`, `manualReview`.

---

## Case Action (`caseAction`)

| Field | Type | Default | Description |
|---|---|---|---|
| `createCase` | Boolean | `false` | Enable case creation on rule match |
| `groupByType` | String | `byRule` | `byRule` (one case per rule) or `byApplicant` (one case per applicant) |
| `blueprintId` | String | — | Case blueprint id (optional; uses default template if omitted) |
| `priority` | String | — | `low`, `medium`, or `high` |
| `deadlineHours` | Integer | — | Investigation deadline in hours |

---

## Transaction Action (`txnActions`)

Set a custom property on the transaction when the rule matches:

```json
{
  "txnActions": [
    {
      "type": "setProp",
      "setPropertyActionParams": {
        "propName": "riskCategory",
        "elExpression": "'high'"
      }
    }
  ]
}
```

---

## Payload Constraints Summary

| Must include | Must NOT include |
|---|---|
| `title` (non-empty, ≤128 chars) | `id`, `name`, `clientId` |
| `types` (min 1 value) | `scope`, `bgCheckTargets`, `dryRun`, `disabled` |
| `conditionEl` for non-scheduled eval rules | `actual`, `revision`, timestamps, author fields |
| `noEventTrigger` + applicant action for scheduled rules | Empty containers (`sourceKeys: []`, etc.) |
