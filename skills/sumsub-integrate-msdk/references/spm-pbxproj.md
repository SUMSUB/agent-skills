# Adding an SPM package to an Xcode project's `project.pbxproj`

When the project is an Xcode project **without** a `Package.swift`, the SPM package
reference lives inside `project.pbxproj`. There is no first-party Apple CLI to add it,
but the file is editable.

- **Preferred (automatable):** edit `*.xcodeproj/project.pbxproj` directly to add an
  `XCRemoteSwiftPackageReference` (the repo URL + version rule), an
  `XCSwiftPackageProductDependency` for `IdensicMobileSDK`, and reference that product
  in the app target's `Frameworks` build phase + `packageProductDependencies`. Mirror
  an existing package entry if the project already has one. After editing, Xcode
  resolves and writes `Package.resolved` on next open. If the Ruby `xcodeproj` gem is
  available, prefer it over hand-editing — it generates valid UUIDs for you. **Always
  show the diff and ask before editing the pbxproj**, then have the user open Xcode to
  let it resolve.
- **Fallback (manual):** if pbxproj editing is risky for this project (unusual layout,
  no template entry to mirror), instruct the user to add it via *File → Add Package
  Dependencies* in Xcode, paste the URL, and pick the `IdensicMobileSDK` product.
