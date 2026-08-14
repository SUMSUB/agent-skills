# Swift 6 / actor isolation — `nonisolated init` (+ optional `@MainActor` factory)

> Applies when the project builds in **Swift 6 mode** or sets "default actor isolation =
> MainActor" (`SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`). Detect from `SWIFT_VERSION` /
> `SWIFT_STRICT_CONCURRENCY` / `SWIFT_DEFAULT_ACTOR_ISOLATION` in build settings before assuming.

There are **two separate** concerns here. Get the first one wrong and the theme won't compile;
the second only applies to some apps.

## 1. `nonisolated override init()` — needed whenever default isolation is MainActor

`SNSTheme` is an Objective-C class; its `init` is imported into Swift as **nonisolated**. Under
`SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`, your subclass's `init` (implicit or explicit) becomes
**main-actor-isolated** and the compiler rejects the override:

> *"Main actor-isolated initializer 'init()' has different actor isolation from nonisolated
> overridden declaration."*

Fix: mark the override `nonisolated` explicitly. This is required **even if the theme reads only
asset-catalog names / literals** (no `@MainActor` source at all):

```swift
final class SumsubTheme: SNSTheme {
    nonisolated override init() {
        super.init()
        // asset-catalog reads, literals, and alpha-derivations are all fine here —
        // UIColor(named:) / UIColor(...) are nonisolated.
        colors.backgroundCommon = UIColor(named: "Background") ?? .systemBackground
        // …
    }
}
```

That single `nonisolated override init()` is the whole fix for the common case. Keep the class
**nonisolated** — do not annotate it `@MainActor`.

## 2. `@MainActor` factory — only if the theme reads a `@MainActor` source

If (and only if) the theme needs to read main-actor-isolated app state — e.g. a `@MainActor` /
`@Observable` design-system object like `Theme.shared` exposing SwiftUI `Color` tokens — those reads
can't happen inside the nonisolated `init`. Move them into a `@MainActor` factory and keep `init`
nonisolated:

```swift
final class SumsubTheme: SNSTheme {
    nonisolated override init() { super.init() }   // satisfies the nonisolated Obj-C override

    @MainActor
    static func make(appTheme: AppTheme = .shared) -> SumsubTheme {
        let t = SumsubTheme()          // inherited nonisolated init
        t.configure(with: appTheme)
        return t
    }
    @MainActor private func configure(with appTheme: AppTheme) {
        colors.backgroundCommon = UIColor(appTheme.background)   // main-actor reads live here
        // …
    }
}
```

Then wire it as `sdk.theme = SumsubTheme.make()` at the launch site (instead of `SumsubTheme()`).

**You need BOTH pieces when default isolation is MainActor *and* the theme reads a `@MainActor`
source** (e.g. IceCubesApp's `DesignSystem` `Theme`): the `nonisolated init` satisfies the override,
and the `make()` factory does the main-actor reads. If default isolation is MainActor but the theme
derives only from asset names / literals, you need just the `nonisolated init` (section 1). If the
project isn't in Swift 6 / MainActor-default mode at all, a plain `override init()` is fine.

The `make()` factory is also the clean answer for a **runtime-switchable host theme** (white-label,
a theme picker) even outside Swift 6: building `SumsubTheme.make()` fresh at each launch snapshots
whatever brand / accent / font is current. See the launch-site wiring in
[`../stages/3-generate.md`](../stages/3-generate.md).
