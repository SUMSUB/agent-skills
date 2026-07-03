# Step 1 — Scan the project (read-only)

> **You're here if:** intake is done (the three questions answered).
> **Prereqs:** none — this is read-only; no approval needed.

After intake, inspect without editing anything:

- **Bail early if not native iOS.** `package.json` with `react-native`, or a `pubspec.yaml` → cross-platform wrapper, not supported — stop and tell the user. No `.xcodeproj` / `.xcworkspace`, or no iOS **app** target (e.g. a library-only `Package.swift`) → stop; this skill needs a real iOS app project with an app target.
- Find `.xcodeproj` / `.xcworkspace` and list iOS app targets.
  - **One** iOS app target → use it; confirm to the user ("I'll use target **AppName**").
  - **Multiple** iOS app targets → ask which one.
- Determine the dependency manager:
  - `Podfile` present → CocoaPods.
  - `Package.swift` or SPM references in `.xcodeproj` → SPM.
  - Neither → default to SPM and tell the user.
- Check deployment target (`IPHONEOS_DEPLOYMENT_TARGET`) — must be ≥ iOS 13.0. If it's lower, surface the current value and tell the user it must be raised to 13.0 to proceed; ask permission to raise it (a project mutation — fold this into the install approval). Raise it where the client declares it, and make sure the value actually reaches the app target. If the user refuses, stop — the SDK won't build below 13.0.

Summarise findings for the user before proceeding.

## Next — install the framework — pick CocoaPods or SPM

- Both `Podfile` **and** SPM present → don't guess; ask the user which to use, then follow one of the next installation links.
- `Podfile` only → [`2a-install-cocoapods.md`](2a-install-cocoapods.md)
- SPM, or no dependency manager yet (default to SPM) → [`2b-install-spm.md`](2b-install-spm.md)
