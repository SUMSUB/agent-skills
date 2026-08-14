# Step 4 — Integration code

> **You're here if:** always — this is the core of the integration.
> **Prereqs:** framework installed (Step 2), Info.plist permissions added (Step 3).

Create a new Swift file encapsulating the SDK lifecycle, named `SumsubVerification.swift` (template: [`../examples/SumsubVerification.swift`](../examples/SumsubVerification.swift)). The template wires the SDK handlers, including the **required** `tokenExpirationHandler` — without it the flow hangs when the token expires mid-session.

`SumsubVerification.start()` is the single launch path for **both** UIKit and SwiftUI — the SDK presents itself over the key window's root VC and dismisses itself. (Do **not** build a `mainVC` + `.fullScreenCover` bridge — see [`6b-launch-swiftui.md`](6b-launch-swiftui.md) for why it breaks the SDK lifecycle.)

**SwiftUI launch point → optional thin helper.** If the launch point from intake (Q1) is a SwiftUI view, you *may* also create `SumsubSwiftUI.swift` — a one-line `SumsubPresenter` `ObservableObject` that forwards to `SumsubVerification.start()` (template: [`../examples/SumsubSwiftUI.swift`](../examples/SumsubSwiftUI.swift)). It's only a small seam for exposing verification state to the UI later; the view can just hold `SumsubVerification` directly. If you do create it, add it to the same change-set so Step 5 wires **both** files into the target. (UIKit needs only `SumsubVerification.swift`.)

**Placement isn't a separate question.** Choose a spot that fits the project's structure (from the Step 1 scan — near similar service/manager files, or a sensible group), then **name it in the change-set approval before creating it**:

> "I'll create `SumsubVerification.swift` in `<group / folder>` — apply?"

The user redirects there if they want it elsewhere. Note that in Xcode the **group** and the filesystem **folder** can differ (classic projects) or match (synchronized groups, Xcode 16+) — place it sensibly in both. (Getting the file into the target — synchronized groups vs `project.pbxproj` — is [`5-wire-target.md`](5-wire-target.md).)

Do **not** edit any existing app code except the one call site the user named in intake (Q1). Never touch unrelated files.

> **Swift 6 / strict concurrency.** If the project builds in Swift 6 mode (check `SWIFT_VERSION` / `SWIFT_STRICT_CONCURRENCY` in build settings), the launch class needs `@MainActor` plus explicit main-actor hops inside SDK callbacks — see [`../references/swift6-concurrency.md`](../references/swift6-concurrency.md).

## Token stub (no backend yet)

If the user has no backend token source yet, create the stub and explain clearly:

> "I'll add a `fetchAccessToken` placeholder that currently returns `nil`. The SDK will not launch until you replace this with a real network call to your backend. Even a hardcoded sandbox token string works for initial testing — the SDK will launch and you can see the flow."

## Next

- Register the new file(s) in the target → [`5-wire-target.md`](5-wire-target.md)
