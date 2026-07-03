# sumsub-integrate-dint-websdk

Agent skill that adds **Sumsub Device Intelligence (the [`@sumsub/fisherman`](https://www.npmjs.com/package/@sumsub/fisherman) module)** to a project that **already verifies users with the Sumsub WebSDK**. Device Intelligence captures low-level device/browser signals (fingerprint, bot/automation, VPN/proxy, emulator, incognito, reused-device) and attaches them to the applicant as **device risk labels** that feed risk scoring.

> **No WebSDK widget on the page** (login / signup / checkout)? Use [`sumsub-integrate-dint-standalone`](../sumsub-integrate-dint-standalone/).
> **Setting up the base WebSDK embed itself?** Use [`sumsub-integrate-websdk`](../sumsub-integrate-websdk/).

## How an agent uses it

This is an [Agent Skill](https://agentskills.io): install it, then ask your coding agent (Claude Code, Codex, Cursor, …) in plain language, e.g.

- *"Add device intelligence to my WebSDK flow"*
- *"Enable device capture / fingerprinting in the WebSDK"*
- *"How do device risk labels get onto a verified applicant?"*

The agent reads [`SKILL.md`](SKILL.md) — the full, authoritative recipe — and drives the integration. This README is the human-facing orientation; `SKILL.md` is what the agent follows.

## The headline

**For a standard WebSDK integration, Device Intelligence is a dashboard toggle, not new code.**

```
1. Enable "Capture device data" on the verification level   ← one-time, in the dashboard
2. Re-launch your existing WebSDK flow                  ← NOTHING new on the frontend
   └─ the SDK auto-inits Fisherman with the same token, fingerprints the device,
      attaches it to the applicant
3. Sumsub computes device signals + risk labels
4. You read the verdict + device signals server-side    ← same applicantReviewed webhook + GET
```

The **advanced self-rendered path** (you drive the verification API yourself instead of the prebuilt `snsWebSdk` widget) is the only case where you own the Fisherman lifecycle — see Stage 3 in `SKILL.md` and [`examples/fisherman-self-render.ts`](examples/fisherman-self-render.ts).

## Prerequisites

- A working base WebSDK integration ([`sumsub-integrate-websdk`](../sumsub-integrate-websdk/)).
- **"Capture device data" enabled** on the verification level (dashboard → level → **Device intelligence** section). If the setting is missing, Device Intelligence isn't provisioned for the workspace — contact Sumsub.
- A **sandbox** App Token + secret (`sbx:` prefix) to read results back. See [`sumsub-api-auth`](../sumsub-api-auth/).

## Run it yourself

```bash
# Read the applicant (incl. device risk labels) server-side
SUMSUB_APP_TOKEN=sbx:... SUMSUB_SECRET_KEY=... bash examples/read-device-results.sh <externalUserId>
```

In the dashboard: applicant profile → **Devices** tab, the completed verification's **Device Check** block, or **Transactions** → a device row → **View device details**.

## Files

| File | Purpose |
|---|---|
| [`SKILL.md`](SKILL.md) | The full recipe the agent follows (enable capture, in-SDK lifecycle, self-render wiring, reading signals, go-live). |
| [`examples/fisherman-self-render.ts`](examples/fisherman-self-render.ts) | Advanced headless wiring — mirrors the SDK's own Fisherman lifecycle (`init` → gated `fingerprint()` → `destroy()`+re-init per `attemptId` → `X-External-Device-Fingerprint` forwarding). |
| [`examples/read-device-results.sh`](examples/read-device-results.sh) | Read the applicant + device risk labels server-side (App-Token + HMAC). |
| [`references/device-signals.md`](references/device-signals.md) | The device risk-label catalog and where each label surfaces. |

## Key facts (easy to get wrong)

- The prebuilt WebSDK drives Fisherman for you — **you write no frontend code**; "Capture device data" on the level is the whole required setup.
- **Self-render path only:** gate every `fingerprint()` on `isDeviceIntelligenceEnabled`, `destroy()`+re-init on each `attemptId` change (so devices bind to the right level), and forward `visitorId` as the `X-External-Device-Fingerprint` header. That header is **enrichment** — the actual applicant binding is the per-attempt `deviceBindingId` (`applicantId-attemptId`).
- Read device risk labels **server-side** (applicant GET / webhook), never from the browser.
- "Capture device data" is **per-level, per-workspace** — enabling it in sandbox does not carry to production.

## See also

- [`sumsub-integrate-dint-standalone`](../sumsub-integrate-dint-standalone/) — Device Intelligence on pages with no WebSDK widget (login / signup / checkout).
- [`sumsub-integrate-websdk`](../sumsub-integrate-websdk/) — the base WebSDK embed this skill sits on top of.
- [`sumsub-api-auth`](../sumsub-api-auth/) — HMAC signing shared by every Sumsub skill.
- [Device Intelligence docs](https://docs.sumsub.com/docs/device-intelligence) — authoritative Sumsub docs.
