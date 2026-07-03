# Step 6B — Launch point (SwiftUI)

> **You're here if:** the host app launch screen is a SwiftUI view.
> **Prereqs:** the integration file (`SumsubVerification.swift`) is created (Step 4) and in the target (Step 5). The thin `SumsubSwiftUI.swift` helper is optional — see below.

**Let the SDK present itself — the same path as UIKit.** From a SwiftUI view, just trigger `SumsubVerification.start()`. The SDK presents over the key window's root view controller (a `UIHostingController` in a SwiftUI app — this works fine) and dismisses itself on finish/close. Hold the launcher in a `@StateObject` (or `@State`) so it survives the async token fetch.

```swift
// Held so it isn't deallocated during the async token fetch.
@StateObject private var sumsub = SumsubPresenter()

Button("Verify") { sumsub.launch() }
```

`SumsubPresenter` (in `SumsubSwiftUI.swift`) is a one-line forwarder to `SumsubVerification.start()`. You can skip it entirely and hold `SumsubVerification` directly:

```swift
@State private var sumsub = SumsubVerification()

Button("Verify") { sumsub.start() }
```

> **Do NOT bridge `sdk.mainVC` into a `.fullScreenCover` / `.sheet`.** It looks idiomatic, but it breaks the SDK's lifecycle. The SDK's `mainVC` (a `UINavigationController`) **strong-retains the SDK**, and the SDK fires `onDidDismiss` from that controller's `dealloc`. If SwiftUI (or your own `sdkVC` property) strong-holds `mainVC`, the controller doesn't dealloc on time, so the dismiss callback fires late — on the *next* launch — stomping the new presentation's binding ("opens every other time") and crashing on the re-entrant release (`sdkVC = nil`). Separately, the SDK dismisses its own `mainVC`, so SwiftUI and the SDK fight over who owns the presentation. Letting the SDK present itself sidesteps all of this: one owner, clean teardown, reliable re-open. (Sumsub's own SwiftUI sample apps use the `.fullScreenCover` bridge but are one-shot demos that never re-open or reset the binding — don't copy them.)

> **Swift 6 / strict concurrency.** If the project builds in Swift 6 mode, mark the launch class `@MainActor` and hop to the main actor inside SDK callbacks. See [`../references/swift6-concurrency.md`](../references/swift6-concurrency.md).

## Next

- Core flow is done — return to **Handoff** in [`../SKILL.md`](../SKILL.md).
