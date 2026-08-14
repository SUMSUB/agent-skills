# Stage 3 — Generate `SumsubTheme.swift`

> **You're here if:** the palette and all token mappings are decided (Stage 2).
> **Prereqs:** **target file path confirmed with the user** (suggest placing it alongside the integration file, or in the project root; default filename `SumsubTheme.swift`); project concurrency mode known (for the Swift 6 note below).

Structure (mirrors [`../examples/SumsubTheme.swift`](../examples/SumsubTheme.swift)):

```swift
final class SumsubTheme: SNSTheme {
    override init() {
        super.init()
        // MARK: - Colors  (all properties; organized by section)
        // MARK: - Fonts
        // MARK: - Metrics
    }
}
```

Every SDK theme property is either mapped from the host app or explicitly derived from the seed palette — nothing is left at the SDK default by accident.

**Read host tokens, not hard-coded hex.** Reference the app's own colors — `UIColor(named:)` for asset-catalog colors, or the app's `Theme`/`Color` object — so the generated theme tracks the source. This also handles light/dark for free: `UIColor(named:)` carries both appearances, or use `UIColor { traits in … }` for programmatic colors. Flat literals are only acceptable for single-appearance apps.

A plain `override init()` is the default and is enough for almost every app. Two Swift-6 caveats (see [`../references/swift6-theme-factory.md`](../references/swift6-theme-factory.md)): (1) if the project sets default actor isolation to MainActor (`SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`), the override **must** be `nonisolated override init() { … }` or it won't compile — this is needed even for an asset-only theme; (2) *additionally*, if the theme reads a `@MainActor` source (e.g. an `@Observable` app `Theme`), or you want a runtime-switchable theme rebuilt per launch, move those reads into a `@MainActor static func make()` factory.

## Wire the file into the target

A new `SumsubTheme.swift` is not compiled until it's a target member — handle this yourself, don't ask the user to drag it in.

- **Synchronized groups (Xcode 16+):** if `project.pbxproj` contains `PBXFileSystemSynchronizedRootGroup`, just place the file in the target's folder — it's included automatically.
- **Classic project:** register it explicitly — the canonical recipe lives in [`../../../sumsub-integrate-msdk/ios/references/pbxproj-editing.md`](../../../sumsub-integrate-msdk/ios/references/pbxproj-editing.md) (prefer the Ruby `xcodeproj` gem; to hand-edit, add the four pbxproj entries mirroring a sibling `.swift` file, then validate with `plutil -lint`). `SumsubTheme.swift` registers exactly the same way as any source file.

## Set the theme at the launch site

This is the skill's **one** edit to existing app code, and it's the point of the job: find where the app creates the SDK instance and set `sdk.theme = SumsubTheme()` right after it's created, **before it's shown**. The theme is a plain property — *how* the SDK is presented (the SDK presents itself via `present()` in both UIKit and SwiftUI) doesn't matter.

- **Where to look:** grep for `SNSMobileSDK(`, `init(accessToken:`, `setupWithAccessToken`, `.theme`, `isReady`, `present(`, `mainVC`. The instance is often a local `let sdk = …`. (The iOS SDK uses a plain initializer — there is no `.builder()/.build()`; that's Android.)
- If the app was integrated via `sumsub-integrate-msdk`, it's in `SumsubVerification.swift` (function `configuredSDK`), which already carries a commented placeholder `// sdk.theme = SumsubTheme()` — uncomment/replace it.
- Show the one-line diff and get approval (it edits existing code). Don't touch any other integration logic (init / handlers / present).
- **If you can't find the launch site** (manual integration behind a wrapper / coordinator / ObjC, or the SDK isn't wired up yet): don't guess a location and don't loop on widening greps. Stop and hand the user the exact one-liner to paste — `sdk.theme = SumsubTheme()` (or `SumsubTheme.make()`), set right after the instance is created and before it's shown. If there's no `SNSMobileSDK(...)` anywhere, the SDK isn't integrated — point to [`sumsub-integrate-msdk`](../../../sumsub-integrate-msdk/SKILL.md). Either way the theme file is complete and ready to attach.

> **Verify it compiles.** A wrong color/font/property name surfaces only at build time. Offer to build (or tell the user to build and run) — the theme renders in the simulator.

## Next

- [`4-report.md`](4-report.md) — present the coverage report.
