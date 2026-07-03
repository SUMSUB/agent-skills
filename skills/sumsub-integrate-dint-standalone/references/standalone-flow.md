# Standalone Device Intelligence — event variants and failure-mode rules

Extends [SKILL.md](../SKILL.md). Covers: when to use the standalone path,
complete JSON bodies for each confirm variant, reading results, and failure-mode rules.
The four-stage loop and device-linking mechanics are in SKILL.md.

## When standalone (vs WebSDK)

| Use standalone (this skill) | Use the WebSDK path |
|---|---|
| Login, signup, password reset, 2FA | The page shows the Sumsub KYC widget |
| Checkout / payment / withdrawal screening | Document + selfie verification flow |
| Pre-KYC gating (screen before account creation) | Identity verification itself |
| Any custom page with no Sumsub widget | — |

If a Sumsub WebSDK widget is on the page, DI is already bundled — see
[`sumsub-integrate-dint-websdk`](../../sumsub-integrate-dint-websdk/SKILL.md). Don't run
both on the same page.

## Event / confirm variants (extends SKILL.md Stage 3)

All three hit the no-applicant transaction endpoint (the applicant is resolved by
`applicant.externalUserId`), App-Token + HMAC signed with the behavior token
carried alongside as the `?accessToken=` query param (it rides with signing, it
does not replace it).

**Applicant platform event** — login / signup / password reset / 2FA:

```json
POST /resources/applicants/-/kyt/txns/-/data?accessToken=<behaviorToken>
{
  "txnId": "<unique-id-you-generate>",   // required — rejected with 422 if missing
  "type": "userPlatformEvent",
  "applicant": { "externalUserId": "<your-user-id>", "type": "individual" },
  "userPlatformEventInfo": {
    "type": "login"
    // type ∈ login | failedLogin | signup | passwordReset | twoFaReset | general
    // optional: "passwordHash": "...", "twoFaUsed": true
  }
}
```

**Financial transaction** — payment / withdrawal / transfer screening:

```json
POST /resources/applicants/-/kyt/txns/-/data?accessToken=<behaviorToken>
{
  "txnId": "<unique-id-you-generate>",   // required
  "type": "finance",
  "applicant": { "externalUserId": "<your-user-id>", "type": "individual" },
  "info": {
    "amount": 100.0,
    "currencyCode": "EUR",
    "currencyType": "fiat",   // fiat | crypto
    "direction": "out"        // out = applicant sends, in = applicant receives
  }
}
```

**Create applicant (pre-KYC)** — screen a user before/at signup: create the
applicant with `levelName`, `accessToken`, `externalUserId` (optionally
`creationTrackingData.ip` for Advanced IP), then **request the applicant
check** to trigger the DI analysis.

Authoritative, exhaustive schemas (the bodies above are the load-bearing subset):
- <https://docs.sumsub.com/reference/send-applicant-platform-event-with-captured-device>
- <https://docs.sumsub.com/reference/send-financial-transaction-with-captured-device>
- <https://docs.sumsub.com/reference/use-device-intelligence-for-pre-kyc-check>

## Reading results

- **Dashboard:** Transactions and Travel Rule → Transactions → filter type
  **User platform event** → open a row for device details + risk labels.
- **Webhooks:** transaction/event reviewed webhooks; verify the signature on
  **raw bytes** (same rules as the WebSDK skill's webhook stage).
- **Risk labels & scoring:** the device label catalog is shared with the WebSDK
  path — full signal definitions are in the `sumsub-integrate-dint-websdk`
  skill's `references/device-signals.md` (install that skill for the file).

## Failure-mode rules

- **Fail open.** DI is a fraud signal, not an auth gate on your own page. A
  Fisherman init/fingerprint error must never block login/signup. Wrap in
  try/catch and proceed.
- **One `sessionId` per logical session**, generated server-side and opaque —
  it is what correlates the captured device to the confirm call. No device
  fields are needed in the confirm body. (`deviceBindingId` in `fingerprint()`
  is a migration-path option only, not required for the default flow.)
- **Don't trust the browser** for the verdict — read it from the dashboard or a
  webhook, server-side.
