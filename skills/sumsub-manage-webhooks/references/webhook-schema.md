# ClientWebhook — schema reference

Sources: Sumsub OpenAPI (`components.schemas.ClientWebhook`, `ClientWebhookHeader`, `ClientWebhookSendingStats`, `ClientWebhookSignatureAlgorithm`, `ClientCallbackDefinitionTargetType`).

## `ClientWebhook`

| Field | Type | Notes |
|---|---|---|
| `id` | string | Server-assigned on first POST. Include in the body to update; omit to create. |
| `name` | string | Required for the dashboard UI; the API treats it as freeform. |
| `description` | string | Optional. |
| `target` | string | Required. URL for `http`, channel id for `slack`, address for `email` / `telegram`. |
| `targetType` | enum | `http`, `email`, `slack`, `telegram`. Default in practice is `http`. |
| `types` | string[] | Required, non-empty. Event-type names — see below. |
| `applicantType` | enum | `individual` or `company`. Omit to receive both. |
| `sourceKeys` | string[] | Optional restriction to specific source-key streams. Leave empty for "all". |
| `secretKey` | string | HMAC secret used to sign payload bodies. **Note: the endpoint returns this value in plaintext on GET** for any caller with `manageClientSettings` permission — it is not masked or write-only. The skill's `get` subcommand redacts it client-side as a defensive measure, but the raw API response carries the full secret. Treat any token that can read this endpoint as having direct access to all webhook secrets. |
| `signatureAlgorithm` | enum | `HMAC_SHA1_HEX`, `HMAC_SHA256_HEX`, `HMAC_SHA512_HEX`. SHA1 is the legacy default; newer integrations should use SHA256. SHA512 is supported but rarely used. The builder defaults to `HMAC_SHA256_HEX`. |
| `headers` | `ClientWebhookHeader[]` | Optional extra HTTP headers sent on every delivery. Each entry is `{key, value}`. |
| `notResendFailedWebhooks` | boolean | If `true`, no retries on delivery failure (fire-and-forget). Default `false` (Sumsub retries with backoff). |
| `clientId` | string | Server-populated (the tenant id). Do not send. |
| `createdAt` / `createdBy` | string | Server-populated audit trail. |

## `ClientCallbackDefinitionTargetType` (enum — `targetType` values)

`telegram`, `slack`, `email`, `http`.

## `ClientWebhookSignatureAlgorithm` (enum — `signatureAlgorithm` values)

`HMAC_SHA1_HEX`, `HMAC_SHA256_HEX`, `HMAC_SHA512_HEX`. The signature is sent as `x-payload-digest` (alg-dependent). Verify on the receiver by computing the HMAC of the raw body with your `secretKey`.

## `ClientWebhookHeader`

`{key: string, value: string}`. Sumsub adds these verbatim to each outbound POST. The receiver sees them mixed with Sumsub's own headers; pick unambiguous names.

## Endpoints

The public API resource (`ClientWebhookApiResource`, App Token auth, `manageClientSettings`) exposes:

| Verb | Path | Notes |
|---|---|---|
| `GET` | `/resources/api/clientWebhooks` | Returns `EntityResult<ClientWebhook>` — `{list: {items: [ClientWebhook]}}`. **Capped at the oldest 50** server-side (`getOldest50`). |
| `GET` | `/resources/api/clientWebhooks/{id}` | Returns one `ClientWebhook` by id. Use for confirmation after a write or to resolve `name` from a known id. |
| `POST` | `/resources/api/agent/clientWebhooks` | Create. Body MUST NOT include `id` (DTO: `ClientWebhookCreateRequest`). Server assigns it. |
| `PATCH` | `/resources/api/agent/clientWebhooks` | Update an existing webhook (by `id` in body, DTO: `ClientWebhookUpdateRequest`).|

No public-API `DELETE` and no `/stats` endpoint — use the Sumsub dashboard UI for those operations.

## Common event-type strings

The OpenAPI keeps `types[]` as a freeform `string[]`. The names below cover the events Sumsub commonly emits — but the server doesn't validate them, so a typo silently fails open (the webhook simply never fires).

```
# Applicant lifecycle
applicantCreated, applicantPrechecked, applicantPending, applicantReviewed,
applicantOnHold, applicantActivated, applicantDeactivated, applicantReset,
applicantLevelChanged, applicantTagsChanged, applicantPersonalInfoChanged,
applicantDeleted, applicantPersonalDataDeleted

# Action workflow
applicantActionPending, applicantActionReviewed, applicantActionOnHold

# Workflow
applicantWorkflowCompleted

# Video ident
videoIdentStatusChanged, videoIdentCompositionCompleted

# KYT — applicant-scoped
applicantKytTxnApproved, applicantKytTxnRejected, applicantKytTxnReviewed,
applicantKytTxnDeleted, applicantKytTxnDataChanged, applicantKytTxnAwaitingUser,
applicantKytOnHold

# KYT — case-scoped
kytCaseCreated, kytCaseStatusChanged, kytCaseReviewed

# AML case
amlCaseApproved, amlCaseRejected, amlCaseOnHold

# Travel Rule / KYB
travelRuleAction, kybCompanyActivity
```

Two names from older docs that the live dashboard does **not** emit (don't use these):
- ~~`applicantWorkflowRunCompleted`~~ → use `applicantWorkflowCompleted`
- ~~`kytCaseUpdated`~~ → use `kytCaseStatusChanged`

Unknown event types are silently dropped by Sumsub — they fail open (the webhook just never fires). The skill doesn't validate them either (we don't want to lag the platform's actual support).

## Gotchas

- **`POST` is upsert.** Same endpoint creates and updates — dispatch is by presence of `id` in the body. Forgetting to include `id` on update creates a *new* duplicate webhook.
- **`secretKey` is NOT write-only.** The endpoint returns secrets in plaintext on GET to anyone with `manageClientSettings` permission. Plan accordingly: rotate secrets on operator off-boarding, and don't paste GET output into screenshots or logs. To keep the existing secret on update, you can either omit the field (the server preserves the prior value if you don't set it) or echo the value back from a previous GET.
- **Headers `{key, value}` not `{name, value}`.** The header collection uses `key`, not `name`. Easy to swap by reflex.
- **`notResendFailedWebhooks: true` is rarely the right setting.** Disabling retries usually causes silent data loss when your endpoint has a 30-second hiccup. Only use if your receiver does its own retry.
- **Webhook idempotency is the receiver's responsibility.** Sumsub may deliver the same event more than once (retries on ambiguous failures); de-dupe by event id on your side.
- **No bulk endpoints.** To replace N webhooks, POST each individually. The skill's `manage_webhooks.sh` doesn't do batch operations.
