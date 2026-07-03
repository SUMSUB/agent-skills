---
name: sumsub-integrate-msdk
description: Integrate the Sumsub Mobile SDK (IdensicMobileSDK / SNSMobileSDK) into an iOS app — even when the user doesn't name the SDK (e.g. "add Sumsub/KYC to my iPhone app", "show the verification screen on iOS", "launch Sumsub from a view controller"). Covers install, permissions, init, token refresh, presenting the flow. SKIP for web (`sumsub-integrate-websdk`), backend / API-only token signing (`sumsub-api-generic`), theming (`sumsub-theme-msdk`), and non-iOS — Android / React Native / Flutter (not supported). iOS only.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Sumsub — Mobile SDK integration (iOS)

Embed Sumsub KYC into an existing iOS app via the **`IdensicMobileSDK`** framework
(main class **`SNSMobileSDK`**), from dependency install to presenting the
verification flow.

> **iOS only.** This skill targets the iOS Mobile SDK. Android is not covered yet.

This is the **trunk**: read the always-on sections below (intake, asking-vs-doing),
then use the [decision table](#how-to-navigate-this-skill) to open **only** the branch
files that match the project and the user's answers.

## Intake — ask these three questions first, in one message

Before touching any project file, ask all three together:

1. **Launch point.** "From which screen / ViewController (or SwiftUI view) should
   the Sumsub flow open? Please share the class name or describe the screen."

2. **Access token source.** "Does your app already have a way to fetch a Sumsub
   access token from your backend? (If yes, share the function name, endpoint URL,
   or service class. If not, I'll add a placeholder you can fill in when your
   backend is ready.)"

3. **Optional modules.** "The base SDK covers standard verification flows and is **always installed**. On top of it, do you need any of these
   add-ons?
   - **MRTDReader** — read the chip on biometric passports
   - **VideoIdent** — live video call with a moderator
   - **EID** — German eID card reading
   - **Fisherman** — device intelligence / fraud signals
   Skip them if you're not sure — they can be added later."

   Modules are **purely additive**. In a multi-select, list **only the four modules** —
   an empty selection already means "base only"; don't add "base only" as a
   co-selectable peer.

Do **not** ask about: the App Token or the secret key — those are server concerns
that never touch the app.

## Asking vs doing — keep approvals meaningful

- **Read-only is free** — scan / grep / read `Info.plist` & build settings without asking.
- **Batch mutations into one approval**, not one per line ("I'll add these 3 Info.plist
  keys [list] + this call site [diff] — apply?").
- **Ask explicitly only for:** editing existing app code, project-mutating commands
  (`pod install`), anything irreversible, and decisions you couldn't settle in intake.

## How to navigate this skill

After intake, open ONLY the rows that match the project (from Step 1) and the user's
intake answers. Each branch file is self-contained and ends with a **Next** pointer.
A letter (2A/2B, 6A/6B) marks a branch — pick one; plain numbers run in sequence.

| Step | Condition | Read |
|---|---|---|
| 1. Scan | always (first, after intake) | [`stages/1-scan.md`](stages/1-scan.md) |
| 2A. Install — CocoaPods | CocoaPods chosen (per Step 1) | [`stages/2a-install-cocoapods.md`](stages/2a-install-cocoapods.md) |
| 2B. Install — SPM | SPM chosen (per Step 1; the default) | [`stages/2b-install-spm.md`](stages/2b-install-spm.md) |
| 3. Permissions & capabilities | always | [`stages/3-permissions.md`](stages/3-permissions.md) |
| 4. Integration file | always | [`stages/4-integration-code.md`](stages/4-integration-code.md) |
| 5. Wire into target | always (right after creating the file) | [`stages/5-wire-target.md`](stages/5-wire-target.md) |
| 6A. Launch — UIKit | host is a UIKit ViewController | [`stages/6a-launch-uikit.md`](stages/6a-launch-uikit.md) |
| 6B. Launch — SwiftUI | host is a SwiftUI view | [`stages/6b-launch-swiftui.md`](stages/6b-launch-swiftui.md) |

> **Fallback (last resort only).** This skill and its branch files are the primary
> source — don't reach for external docs by default. Only if you hit a genuine blocker
> they don't resolve, consult the [Sumsub iOS docs](https://docs.sumsub.com/docs/get-started-ios).

When the tree is walked, return here for **Guardrails** and **Handoff**.

## Guardrails — what this skill must never do

- **Never edit existing app code** beyond the single targeted call site the user approved in intake.
- **Let the SDK present itself — in SwiftUI too.** Always launch via `SumsubVerification.start()` (`sdk.present()` / `sdk.present(from:)`). **Never** strong-hold the SDK or its `mainVC` across the flow, and **never** bridge `sdk.mainVC` into a SwiftUI `.fullScreenCover` / `.sheet`. `mainVC` strong-retains the SDK and the SDK fires `onDidDismiss` from that controller's `dealloc`; holding it yourself delays teardown and causes "opens every other time" + a crash on re-open. The SDK owns presentation **and** dismissal — one owner, clean re-open.
- **Never run `pod install`** (or any other shell command that modifies the project) without explicit user permission in the current message.
- **Never ask for or reference the App Token or secret key** — tokens are minted server-side.
- **Never store or reference the App Token or secret key** in any app file.
- **Never silently overwrite** an existing Info.plist key — always show the current value and ask first.
- **Never apply theme changes** in this skill — styling belongs in `sumsub-theme-msdk`.
- **Never gate access on in-app callbacks** — the authoritative verdict comes from the backend (webhook + applicant GET), not the SDK callbacks.

## Handoff

After all changes are complete, summarise clearly:

1. **Files created / modified** — list each with a one-line description.
2. **Stub that needs filling in** — if `fetchAccessToken` is a placeholder, say so explicitly and describe what the user must implement.
3. **Build step** — e.g. "Run `pod install`, then open the `.xcworkspace` and build" or "Build and run — SPM packages will resolve automatically."
4. **How to test** — explain: get a sandbox access token from your backend (or temporarily hardcode one), trigger the integration object's `start(…)` from the launch point, and verify the Sumsub flow appears. (NFC modules need a physical device — not the simulator.)
5. **Source of truth** — remind the user: the final verification result comes from the backend webhook + applicant read, not from the SDK callbacks.
6. **Next steps** — point to `sumsub-theme-msdk` for styling.
