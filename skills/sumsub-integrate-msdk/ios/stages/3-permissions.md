# Step 3 — Permissions & capabilities

> **You're here if:** always
> **Prereqs:** the framework (and any confirmed modules) installed (Step 2).

This step declares everything the OS needs: the base permission keys, **plus** the extra Info.plist / entitlement keys for any optional modules added in Step 2.

> **Gotcha — "Info.plist" may be build settings.** Modern Xcode targets often have **no `Info.plist` file**; its keys live in the target's build settings as `INFOPLIST_KEY_…` (e.g. `INFOPLIST_KEY_NSCameraUsageDescription`). Check `GENERATE_INFOPLIST_FILE` / `INFOPLIST_FILE` first. The **string** usage-description keys map directly (`INFOPLIST_KEY_NSCameraUsageDescription`, etc.). The **array** keys — `select-identifiers` and `UIBackgroundModes` — have no clean `INFOPLIST_KEY_` form: if the target has no Info.plist file, create one and point `INFOPLIST_FILE` at it, then add the arrays there. Leave `GENERATE_INFOPLIST_FILE = YES` — Xcode merges the `INFOPLIST_KEY_` strings into that file. (The `.entitlements` key is always its own file.)

## Permissions

The base SDK needs these four keys:

- `NSCameraUsageDescription`
- `NSMicrophoneUsageDescription`
- `NSPhotoLibraryUsageDescription`
- `NSLocationWhenInUseUsageDescription`

Only if **MRTDReader** or **EID** are confirmed in intake:

- `NFCReaderUsageDescription`

All the string descriptions for these keys are in [`../examples/Info.plist.snippet`](../examples/Info.plist.snippet).

Check the project (Info.plist, build settings, or `.entitlements`) first, then ask **once** before writing:

- **Missing keys** — add them in one batch (use the snippet's strings, or the app's own wording).
- **Keys already set** — never silently overwrite; show the current value and ask whether to keep or update.

> **Gotcha — localized usage strings.** iOS localizes usage-description strings via
> `<lang>.lproj/InfoPlist.strings` (entries keyed by the same key, e.g.
> `"NSCameraUsageDescription" = "We use the camera to capture your documents.";`). When an app does
> this, the value in the base `Info.plist` is just the development-language fallback and is often
> left as the **key name itself** or a placeholder — that is **not** a rejectable stub. So before
> flagging an existing usage-description value as a stub or overwriting it, grep for that key in
> `**/*.lproj/InfoPlist.strings`. If a localized string exists, the permission is properly described
> — leave it alone (don't raise an App Store warning, don't overwrite the plist value). When the app
> localizes Info.plist (any `InfoPlist.strings` present) and you're **adding** new keys, put the
> human-readable description in the localized `InfoPlist.strings` (at least `Base.lproj`) to match
> the app's pattern, not only a literal string in `Info.plist`.

## NFC configuration

Only if **MRTDReader** or **EID** are confirmed in intake:

- Add in **Info.plist** the `com.apple.developer.nfc.readersession.iso7816.select-identifiers` key. Value is an array with per-module AIDs (see [`../examples/Info.plist.snippet`](../examples/Info.plist.snippet)). Add the AIDs for each confirmed module; if both, union them and keep the shared AID **only once**.

- Add to **.entitlements**: `com.apple.developer.nfc.readersession.formats` = `["TAG"]` (the "Near Field Communication Tag Reading" capability). If the target has no `.entitlements` file, create one and set `CODE_SIGN_ENTITLEMENTS` to its path. Under automatic signing Xcode registers it on the App ID for you; manual step only under manual signing or a provisioning failure.

## UIBackgroundModes

Only if **VideoIdent** is confirmed in intake:

- Add in **Info.plist** the `audio` string to the `UIBackgroundModes` array.

## Next

- Create the integration code → [`4-integration-code.md`](4-integration-code.md)
