# Step 5 — Wire the new file into the target

> **You're here if:** you just created a `.swift` file (the integration file).
> **Prereqs:** the file exists on disk.

A freshly-written `.swift` file on disk is **not** compiled until it is a member of the app target. Don't leave this to the user — handle it, then verify:

- **Synchronized groups (Xcode 16+):** if the target uses `PBXFileSystemSynchronizedRootGroup` (grep `project.pbxproj` for it), any file placed inside the target's folder is included automatically — nothing to edit. Just write the file in the right directory and say so.
- **Classic pbxproj:** the file must be registered explicitly — see [`../references/pbxproj-editing.md`](../references/pbxproj-editing.md).

This applies to **every** file you create — `SumsubVerification.swift`, the optional SwiftUI helper `SumsubSwiftUI.swift` (if you created one in Step 4), and later `SumsubTheme.swift` from the theming skill.

## Next

- Wire the launch point for your UI framework:
  - UIKit → [`6a-launch-uikit.md`](6a-launch-uikit.md)
  - SwiftUI → [`6b-launch-swiftui.md`](6b-launch-swiftui.md)
