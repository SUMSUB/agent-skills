# sumsub-integrate-dint-standalone

Agent skill that integrates **Sumsub Device Intelligence (the [`@sumsub/fisherman`](https://www.npmjs.com/package/@sumsub/fisherman) JS module)** into your own web pages that have **no Sumsub WebSDK widget** — login, signup, password reset, 2FA, checkout, or any high-value action you want fraud-screened (bots, emulators, VPN/proxy, reused devices, multi-accounting).

> **Already embed the Sumsub WebSDK on the page?** Don't use this — Device Intelligence rides along inside the SDK. Use the sibling skill [`sumsub-integrate-dint-websdk`](../sumsub-integrate-dint-websdk/) instead.

## How an agent uses it

This is an [Agent Skill](https://agentskills.io): install it, then ask your coding agent (Claude Code, Codex, Cursor, …) in plain language, e.g.

- *"Add device intelligence to my login page"*
- *"Fingerprint the device at signup and screen for multi-accounting"*
- *"Use Fisherman standalone to send a platform event"*

The agent reads [`SKILL.md`](SKILL.md) — the full, authoritative recipe — and drives the integration for you. This README is the human-facing orientation; `SKILL.md` is what the agent follows.

## What it sets up — the loop

```
preflight ─▶ 1. backend mints a behavior access token  (POST /resources/accessTokens/behavior)
            2. browser: @sumsub/fisherman init + fingerprint() on the user action
            3. backend confirms the event with the captured device
            4. you read the verdict + device risk labels (dashboard / webhook)
```

Capturing the device is inert until you **confirm the event server-side** (step 3) — that's what makes Sumsub run the analysis.

## Prerequisites

- A **sandbox** App Token + secret (`sbx:` prefix) from the Sumsub dashboard — never use production credentials during integration. See [`sumsub-api-auth`](../sumsub-api-auth/).
- **Device Intelligence enabled** for the workspace (not self-serve — ask your CSM / `support@sumsub.com`). The preflight verifies it.
- Node + npm for the frontend (`npm i @sumsub/fisherman`).

## Run it yourself

```bash
# 0. Validate the workspace (HMAC works + Device Intelligence enabled)
SUMSUB_APP_TOKEN=sbx:... SUMSUB_SECRET_KEY=... bash scripts/preflight.sh

# 1. Mint a behavior access token (backend). Response: { "token": "..." }
SUMSUB_APP_TOKEN=sbx:... SUMSUB_SECRET_KEY=... bash examples/behavior-token.sh <sessionId> [ttlInSecs]

# 3. Confirm a platform event with the captured device (backend, App-Token + HMAC signed)
SUMSUB_APP_TOKEN=sbx:... SUMSUB_SECRET_KEY=... \
  bash examples/submit-platform-event.sh <behaviorAccessToken> <externalUserId> [eventType]
```

Then check the Sumsub dashboard → **Transactions** → filter **User platform event** for the device details + risk labels.

## Files

| File | Purpose |
|---|---|
| [`SKILL.md`](SKILL.md) | The full recipe the agent follows (stages, field reference, gotchas, go-live). |
| [`scripts/preflight.sh`](scripts/preflight.sh) | Workspace validator — confirms HMAC signing works **and** Device Intelligence is enabled. Run before anything else. |
| [`examples/behavior-token.sh`](examples/behavior-token.sh) | Backend: mint the behavior access token (signs the JSON body). Returns the JWT in the `token` field. |
| [`examples/fisherman-vanilla.html`](examples/fisherman-vanilla.html) | Browser capture, vanilla JS — `init` → `fingerprint()` on submit, fail-open. |
| [`examples/fisherman-react.tsx`](examples/fisherman-react.tsx) | Browser capture as a React hook (StrictMode-safe teardown). |
| [`examples/submit-platform-event.sh`](examples/submit-platform-event.sh) | Backend: confirm the event (App-Token + HMAC signed, behavior token carried as `?accessToken=`). |
| [`references/standalone-flow.md`](references/standalone-flow.md) | Event variants (platform event / financial txn / pre-KYC), result reading, failure-mode rules. |

## Key facts (easy to get wrong)

- The mint response field is **`token`** — **not** `accessToken`. (Behavior tokens carry no `userId`, unlike the WebSDK access-token endpoint.)
- The confirm call is **App-Token + HMAC signed**; the behavior token rides along as the `?accessToken=` query param — it does **not** replace signing.
- DI must **never block your real flow** — Fisherman is wrapped fail-open; a capture error must not stop login/signup.
- Read the verdict **server-side** (dashboard / webhook), never trust the browser.

## See also

- [`sumsub-integrate-dint-websdk`](../sumsub-integrate-dint-websdk/) — Device Intelligence when the page already embeds the WebSDK widget.
- [`sumsub-integrate-websdk`](../sumsub-integrate-websdk/) — the base KYC WebSDK embed (token signing, webhook patterns reused here).
- [`sumsub-api-auth`](../sumsub-api-auth/) — HMAC signing shared by every Sumsub skill.
- [Get started with Device Intelligence](https://docs.sumsub.com/reference/get-started-with-device-intelligence) — authoritative Sumsub docs.
