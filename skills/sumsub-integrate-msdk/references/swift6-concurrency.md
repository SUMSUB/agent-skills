# Swift 6 / strict concurrency

> Applies when the project builds in **Swift 6 mode** (or has "default actor isolation = MainActor"). Detect from `SWIFT_VERSION` / `SWIFT_STRICT_CONCURRENCY` in build settings before assuming.

The SDK's callbacks are **nonisolated**, so the compiler will reject capturing main-actor state in them — e.g. *"Task-isolated 'onDismiss' is captured by a main actor-isolated closure"*.

- Mark the launch class `@MainActor`.
- Inside SDK callbacks, hop explicitly before touching app/UI state: `sdk.onDidDismiss { _ in Task { @MainActor in onDismiss?() } }` (or `DispatchQueue.main.async { … }`, as in the SwiftUI presenter [`../examples/SumsubSwiftUI.swift`](../examples/SumsubSwiftUI.swift)).

Applies when writing the integration code — the launch class and its SDK callbacks ([`4-integration-code.md`](../stages/4-integration-code.md)) — and to the SwiftUI presenter's binding hop ([`6b-launch-swiftui.md`](../stages/6b-launch-swiftui.md)).
