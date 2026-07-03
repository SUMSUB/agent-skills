# Registering a source file in a classic `project.pbxproj`

When the target does **not** use synchronized groups (no
`PBXFileSystemSynchronizedRootGroup` in `project.pbxproj`), a new `.swift` file must
be registered explicitly. Prefer the Ruby `xcodeproj` gem if available — it generates valid UUIDs; hand-edit only as fallback. To hand-edit, add the four entries by mirroring an existing sibling file:

1. a `PBXBuildFile`,
2. a `PBXFileReference`,
3. a child in the group, and
4. an entry in the target's `Sources` build phase.

Then validate with `plutil -lint project.pbxproj`. Do this yourself — do not ask the
user to drag the file in via Xcode.

> This is the canonical place for source-file registration. The theming skill
> (`sumsub-theme-msdk`) creates `SumsubTheme.swift` and wires it in the same way.
