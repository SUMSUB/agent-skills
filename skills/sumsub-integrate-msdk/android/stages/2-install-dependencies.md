# Step 2 (Android) — Install via Gradle

> **You're here if:** the project is Android (per Step 1).
> **Prereqs:** Step 1 done — you know the app module, build language, and where repos are declared.

Two edits — the repository, then the dependency. Tell the user exactly what you'll add and why, ask once, and edit only
after explicit approval.

1. **Maven repository.** The SDK is on Sumsub's own Maven repo, not Maven Central, so resolution fails without it. Add
   `maven { url "https://maven.sumsub.com/repository/maven-public/" }` in the **one** place the project declares
   repositories (from Step 1): `dependencyResolutionManagement` in `settings.gradle[.kts]` (modern) or
   `allprojects { repositories }` in the root `build.gradle` (older). Full shape — both styles, Groovy + Kotlin DSL —
   in [`../examples/settings.gradle.kts.snippet`](../examples/settings.gradle.kts.snippet).

   **If eID was selected in intake (Q3), also add the private repo** in the same repositories block:
   `https://maven.sumsub.com/repository/maven-private/` with `credentials { username / password }` read from Gradle
   properties (shape in the same snippet). The credentials come from Sumsub support — tell the user to request them
   and put the values in `~/.gradle/gradle.properties` (`sumsubRepoUsername` / `sumsubRepoPassword`); **never**
   hardcode or commit them.

2. **Dependency.** In the **app module** build file (match Groovy vs `.kts`), add the base implementation plus a line
   per module confirmed in intake (Q3). If the project uses a **version catalog** (`gradle/libs.versions.toml`, per
   Step 1), declare the version and libraries there and reference them the house way instead of inlining coordinates.
   Pin one version and reuse it for every Sumsub artifact — base and modules **must** share the same version. Full
   shape in [`../examples/build.gradle.kts.snippet`](../examples/build.gradle.kts.snippet):
    - Base: `implementation "com.sumsub.sns:idensic-mobile-sdk:$version"`
    - VideoIdent: `…:idensic-mobile-sdk-videoident:$version`
    - EID: `…:idensic-mobile-sdk-eid:$version` — resolves from the **private repo added in edit 1**; without that repo
      and its credentials the dependency won't resolve.
    - NFC (MRTDReader): `…:idensic-mobile-sdk-nfc:$version` — on MSDK ≥ 1.40.0 the build may also need a packaging
      exclusion in the app module: `packaging { resources.excludes += "META-INF/versions/9/OSGI-INF/MANIFEST.MF" }`.
      Add it only if the build fails on that duplicate resource.
    - **Device Intelligence (Fisherman)** is **bundled in the base since 1.43.0** — no separate dependency on Android.

   Resolve the latest version from the [SDK changelog](https://docs.sumsub.com/docs/changelog-android) (or ask the
   user); don't hardcode a stale one.

3. **`minSdk ≥ 23`** — if Step 1 found it lower, raise it in the app module's `defaultConfig` as part of this same
   change-set.

After editing, ask: "Should I trigger a Gradle sync / build now, or would you prefer to in Android Studio?" Run any
Gradle command **only with explicit permission**.

## Next

- Create the integration code → [`3-integration-code.md`](3-integration-code.md)
