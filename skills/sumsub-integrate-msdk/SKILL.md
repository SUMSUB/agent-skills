---
name: sumsub-integrate-msdk
description: Integrate the Sumsub Mobile SDK (IdensicMobileSDK / SNSMobileSDK) into a native iOS or Android app — even when the user doesn't name the SDK (e.g. "add Sumsub/KYC to my iPhone app", "add KYC to my Android app", "show the verification screen", "launch Sumsub from a view controller / activity"). Detects the platform from the project (iOS Xcode/Swift vs Android Gradle/Kotlin) and follows the matching track. Covers install, permissions, init, token refresh, and presenting / launching the flow. SKIP for web (`sumsub-integrate-websdk`), backend / API-only token signing (`sumsub-api-generic`), theming (`sumsub-theme-msdk`), and React Native / Flutter (not supported — native iOS & Android only).
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Sumsub — Mobile SDK integration (iOS & Android)

Embed Sumsub KYC into an existing native app via the **`IdensicMobileSDK`** framework
(main class **`SNSMobileSDK`**), from dependency install to presenting / launching the
verification flow — on **iOS** (Swift) or **Android** (Kotlin).

This is the **trunk**: read the always-on sections below (intake, asking-vs-doing),
detect the platform, then use the [decision table](#how-to-navigate-this-skill) to open
**only** the branch files that match the platform, the project, and the user's answers.

## Intake — ask these three questions first, in one message

Before touching any project file, ask all three together:

1. **Launch point.** "From which screen should the Sumsub flow open? Please share the
   class name or describe the screen." — *iOS:* a ViewController or SwiftUI view;
   *Android:* an Activity, Fragment, or Composable.

2. **Access token source.** "Does your app already have a way to fetch a Sumsub
   access token from your backend? (If yes, share the function name, endpoint URL,
   or service class. If not, I'll add a placeholder you can fill in when your
   backend is ready.)"

3. **Optional modules.** "The base SDK covers standard verification flows and is **always installed**. On top of it, do
   you need any of these
   add-ons?
    - **NFC** (passport / eMRTD chip reading) — *iOS:* `MRTDReader`; *Android:* the `nfc` module – read the chip on
      biometric passports
    - **VideoIdent** — live video call with a moderator
    - **EID** — German eID card reading
    - **Fisherman / Device Intelligence** — fraud signals *(iOS: optional
      module; **Android: bundled in the base SDK since 1.43.0** — nothing to add)*
      Skip them if you're not sure — they can be added later."

   Modules are **purely additive**. In a multi-select, list **only the modules** —
   an empty selection already means "base only"; don't add "base only" as a
   co-selectable peer.

Do **not** ask about: the App Token or the secret key — those are server concerns
that never touch the app.

## Asking vs doing — keep approvals meaningful

- **Read-only is free** — scan / grep / read `Info.plist`, `AndroidManifest.xml` & build files without asking.
- **Batch mutations into one approval**, not one per line ("I'll add these 3 Info.plist
  keys [list] + this call site [diff] — apply?").
- **Ask explicitly only for:** editing existing app code, project-mutating commands
  (`pod install`, a Gradle sync), anything irreversible, and decisions you couldn't settle in intake.

## Detect the platform (do this before opening any branch file)

Decide whether this is an **iOS** or **Android** project — the install steps, the
permission model, and the generated language all differ. Read-only.

```bash
# iOS markers
find . -maxdepth 3 \( -name '*.xcodeproj' -o -name '*.xcworkspace' -o -name 'Podfile' -o -name 'Package.swift' \) 2>/dev/null
# Android markers
find . -maxdepth 3 \( -name 'build.gradle' -o -name 'build.gradle.kts' -o -name 'settings.gradle*' -o -name 'AndroidManifest.xml' \) 2>/dev/null
```

- **iOS only** (`.xcodeproj` / `Package.swift` / `Podfile`, no Gradle) → **iOS track**.
- **Android only** (`build.gradle[.kts]` / `AndroidManifest.xml`, no Xcode) → **Android track**.
- **Both present** (a monorepo, or a React-Native / Flutter shell with native folders) →
  report both and **ask which platform to integrate.** One platform per run. (React
  Native / Flutter wrappers themselves are out of scope — this skill targets the native
  SDKs; the Step-1 scan bails on a detected wrapper.)
- **Neither** → ask the user to point at the app's source root.

Confirm the detected platform if there was any ambiguity, then follow the matching track.

## How to navigate this skill

After intake, open ONLY the rows that match the **detected platform**, the project (from
Step 1), and the user's intake answers. Each branch file is self-contained and ends with
a **Next** pointer. A letter (2A/2B, 6A/6B) marks a branch — pick one; plain numbers run
in sequence.

### iOS track

| Step                          | Condition                              | Read                                                                       |
|-------------------------------|----------------------------------------|----------------------------------------------------------------------------|
| 1. Scan                       | always (first, after intake)           | [`ios/stages/1-scan.md`](ios/stages/1-scan.md)                             |
| 2A. Install — CocoaPods       | CocoaPods chosen (per Step 1)          | [`ios/stages/2a-install-cocoapods.md`](ios/stages/2a-install-cocoapods.md) |
| 2B. Install — SPM             | SPM chosen (per Step 1; the default)   | [`ios/stages/2b-install-spm.md`](ios/stages/2b-install-spm.md)             |
| 3. Permissions & capabilities | always                                 | [`ios/stages/3-permissions.md`](ios/stages/3-permissions.md)               |
| 4. Integration file           | always                                 | [`ios/stages/4-integration-code.md`](ios/stages/4-integration-code.md)     |
| 5. Wire into target           | always (right after creating the file) | [`ios/stages/5-wire-target.md`](ios/stages/5-wire-target.md)               |
| 6A. Launch — UIKit            | host is a UIKit ViewController         | [`ios/stages/6a-launch-uikit.md`](ios/stages/6a-launch-uikit.md)           |
| 6B. Launch — SwiftUI          | host is a SwiftUI view                 | [`ios/stages/6b-launch-swiftui.md`](ios/stages/6b-launch-swiftui.md)       |

### Android track

| Step                      | Condition                                                | Read                                                                                   |
|---------------------------|----------------------------------------------------------|----------------------------------------------------------------------------------------|
| 1. Scan                   | always (first, after intake)                             | [`android/stages/1-scan.md`](android/stages/1-scan.md)                                 |
| 2. Install — Dependencies | always                                                   | [`android/stages/2-install-dependencies.md`](android/stages/2-install-dependencies.md) |
| 3. Integration file       | always (Gradle auto-compiles — no wire-into-target step) | [`android/stages/3-integration-code.md`](android/stages/3-integration-code.md)         |
| 4. Launch                 | always                                                   | [`android/stages/4-launch.md`](android/stages/4-launch.md)                             |

> **Fallback (last resort only).** This skill and its branch files are the primary
> source — don't reach for external docs by default. Only if you hit a genuine blocker
> they don't resolve, consult the Sumsub docs:
> [iOS](https://docs.sumsub.com/docs/get-started-ios) ·
> [Android](https://docs.sumsub.com/docs/get-started-android).

When the tree is walked, return here for **Guardrails** and **Handoff**.

## Guardrails — what this skill must never do

- **Detect the platform first** — never emit Swift into an Android project or Kotlin into an iOS one; if both are
  present, ask which to integrate.
- **Never edit existing app code** beyond the single targeted call site the user approved in intake.
- **(iOS) Let the SDK present itself — in SwiftUI too.** Always launch via `SumsubVerification.start()` (
  `sdk.present()` / `sdk.present(from:)`). **Never** strong-hold the SDK or its `mainVC` across the flow, and **never**
  bridge `sdk.mainVC` into a SwiftUI `.fullScreenCover` / `.sheet`. `mainVC` strong-retains the SDK and the SDK fires
  `onDidDismiss` from that controller's `dealloc`; holding it yourself delays teardown and causes "opens every other
  time" + a crash on re-open. The SDK owns presentation **and** dismissal — one owner, clean re-open.
- **(Android) Never add camera/mic permissions or runtime prompts** — the SDK declares and requests them itself; adding
  your own can double-prompt or conflict.
- **(Android) The token-refresh handler is synchronous** — `onTokenExpired()` must return the token on a background
  thread; bridge the suspend token call with `runBlocking`, not the iOS async/callback pattern.
- **Never run a project-mutating command** (`pod install`, a Gradle sync/build) without explicit user permission in the
  current message.
- **Never ask for or reference the App Token or secret key** — tokens are minted server-side.
- **Never store or reference the App Token or secret key** in any app file.
- **Never silently overwrite** an existing Info.plist / AndroidManifest value — always show the current value and ask
  first.
- **Never apply theme changes** in this skill — styling belongs in `sumsub-theme-msdk`.
- **Never gate access on in-app callbacks** — the authoritative verdict comes from the backend (webhook + applicant
  GET), not the SDK callbacks.

## Handoff

After all changes are complete, summarise clearly:

1. **Files created / modified** — list each with a one-line description.
2. **Stub that needs filling in** — if the token fetch is a placeholder, say so explicitly and describe what the user
   must implement. (On Android it's the single `SumsubTokenProvider.fetchAccessToken` suspend function — the launcher
   reuses it for mid-session refresh.)
3. **Build step** — iOS: "Run `pod install`, then open the `.xcworkspace` and build" or "Build and run — SPM packages
   resolve automatically"; Android: "Sync Gradle, then build & run".
4. **How to test** — explain: get a sandbox access token from your backend (or temporarily hardcode one), trigger
   verification from the launch point (iOS: `SumsubVerification.start(…)`; Android: the ViewModel action whose effect
   makes the screen call `SumsubLauncher.present(…)`), and verify the Sumsub flow appears. (NFC modules need a
   physical device — not the iOS simulator / Android emulator.)
5. **Source of truth** — remind the user: the final verification result comes from the backend webhook + applicant read,
   not from the SDK callbacks.
6. **Next steps** — point to `sumsub-theme-msdk` for styling (iOS & Android).
