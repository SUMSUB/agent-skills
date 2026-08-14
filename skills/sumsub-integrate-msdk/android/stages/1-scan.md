# Step 1 (Android) — Scan the project (read-only)

> **You're here if:** the project was detected as **Android** (Gradle / Kotlin), and intake is done.
> **Prereqs:** none — this is read-only; no approval needed.

After intake, inspect without editing anything:

- **Bail early if not native Android.** `package.json` with `react-native`, or a `pubspec.yaml` → cross-platform
  wrapper, not supported — stop and tell the user. No `build.gradle[.kts]` / `AndroidManifest.xml`, or no module
  applying `com.android.application` → stop; this skill needs a real Android app project.
- **Find the app module** — the module whose `build.gradle[.kts]` applies the `com.android.application` plugin (usually
  `app/`).
    - **One** application module → use it; confirm to the user ("I'll use module **app**").
    - **Multiple** application modules → ask which one.
- **Build language:** note Groovy (`build.gradle`) vs Kotlin DSL (`build.gradle.kts`), and whether the project uses a
  **version catalog** (`gradle/libs.versions.toml`) — you'll match both when editing.
- **Where repositories are declared:** `dependencyResolutionManagement { repositories { … } }` in
  `settings.gradle[.kts]` (modern, Gradle 7+) **or** `allprojects { repositories { … } }` in the root `build.gradle` (
  older). You'll add the Sumsub Maven repo in whichever the project uses — not both.
- **`minSdk`** (in the app module's `defaultConfig`) — must be **≥ 23**. If lower, surface the value and tell the user
  it must be raised to 23 to proceed; fold the bump into the install approval. If the user refuses, stop — the SDK won't
  build below 23.
- **Kotlin version** — must be **≥ 2.1.0**. If lower, flag it; older Kotlin fails to compile against the SDK.
- **UI toolkit:** note whether the launch screen uses Jetpack Compose or Views — it only affects the launch site (Step
  4), not the rest.

Summarise findings for the user before proceeding.

## Next

- Install the framework → [`2-install-dependencies.md`](2-install-dependencies.md)
