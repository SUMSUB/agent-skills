# Stage 3 (Android) — Generate `SumsubTheme.kt`

> **You're here if:** the palette and all token mappings are decided (Stage 2).
> **Prereqs:** **target file path confirmed with the user** (suggest placing it next to `SumsubIntegration.kt` if the
> app was integrated via `sumsub-integrate-msdk`, otherwise a sensible package; default filename `SumsubTheme.kt`).

Structure (mirrors [`../examples/SumsubTheme.kt`](../examples/SumsubTheme.kt)):

```kotlin
fun sumsubTheme(context: Context): SNSTheme = SNSTheme {
    // Colors  (all properties; organized by section)
    // Fonts
    // Metrics
}
```

A **factory function taking a `Context`**, not a stored singleton — resources must be resolved against a real context,
and rebuilding per launch keeps the theme in sync with runtime day/night switches. Every SDK theme property is either
mapped from the host app or explicitly derived from the seed palette — nothing is left at the SDK default by accident
(the deliberate exceptions are listed in Stage 2's "Left at SDK defaults").

**Read host tokens, not hard-coded hex.** Reference the app's own resources —
`ContextCompat.getColor(context, R.color.…)` for XML colors, the app's Compose color objects via `.toArgb()` — so the
generated theme tracks the source. Flat literals are only acceptable for values that exist nowhere in the app (e.g. a
derived camera background).

**Dual-appearance apps: resolve light + dark explicitly.** A resource read returns the current mode's value only. The
template carries a small helper that builds light/dark configuration contexts, so every resource-backed color becomes
`SNSThemeColor(light.color(R.color.x), dark.color(R.color.x))` — `light` / `dark` are also the constructor's actual
parameter names. For Compose-scheme apps, read the light and dark `ColorScheme` objects instead — same two-argument
constructor. Single-appearance apps use the one-argument form.

**Helpers the template ships** (keep them; they make the mapping readable):

- `Context.color(resId)` / day- and night-context builders — dual-mode resource reads
- `Int.alpha(fraction)` — the Stage 2 alpha-derivation (`ColorUtils.setAlphaComponent`)
- `Context.dp(value)` — dp → px for metric `Float`s
- `font(resId, fallback)` — `ResourcesCompat.getFont` with a `Typeface` fallback

## Attach the theme at the launch site

This is the skill's **one** edit to existing app code, and it's the point of the job: find where the app builds the SDK
and add `.withTheme(sumsubTheme(activity))` to the builder chain, **before `.build()`**.

- **Where to look:** grep for `SNSMobileSDK.Builder`, `withAccessToken`, `withTheme`, `.launch()`. (The Android SDK uses
  a builder — a plain `SNSMobileSDK(...)` initializer is iOS.)
- If the app was integrated via `sumsub-integrate-msdk`, it's in `SumsubIntegration.kt` (function `present`), which
  already carries a commented placeholder `// .withTheme(sumsubTheme(activity))` — uncomment it.
- Show the one-line diff and get approval (it edits existing code). Don't touch any other integration logic (builder
  handlers / token provider / launch).
- **If you can't find the launch site** (manual integration behind a wrapper, or the SDK isn't wired up yet): don't
  guess a location and don't loop on widening greps. Stop and hand the user the exact one-liner to paste —
  `.withTheme(sumsubTheme(activity))` on the builder, before `.build()`. If there's no `SNSMobileSDK.Builder` anywhere,
  the SDK isn't integrated — point to [`sumsub-integrate-msdk`](../../../sumsub-integrate-msdk/SKILL.md). Either way the
  theme file is complete and ready to attach.

No wire-into-target step — Gradle compiles any `.kt` under a source set automatically.

> **Verify it compiles.** A wrong color/font/property name surfaces only at build time. Offer to build (with explicit
> permission — it's a Gradle command) or tell the user to build and run — the theme renders in the emulator.

## Next

- [`4-report.md`](4-report.md) — present the coverage report.
