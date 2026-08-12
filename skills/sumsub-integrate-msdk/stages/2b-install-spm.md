# Step 2B — Install via Swift Package Manager

> **You're here if:** SPM is the chosen dependency manager (per Step 1; the default).
> **Prereqs:** Step 1 done — you know the app target.

The base package is `https://github.com/sumsub/IdensicMobileSDK-iOS.git`, product `IdensicMobileSDK`. On top of it, add each optional module the user confirmed in intake (Q3) — if they confirmed none, just the base. Each module is its **own** SPM package (repo + product), pinned to the same version as the base; all four are listed in [`../examples/Package.swift.snippet`](../examples/Package.swift.snippet) (commented out).

Tell the user exactly what you'll add and why, ask once, and edit only after explicit approval.

Pick the path by whether the project has a `Package.swift`:

1. **No `Package.swift`** — an `.xcodeproj` / `.xcworkspace` app (the usual case). Add the package programmatically by editing `project.pbxproj` — see [`../references/spm-pbxproj.md`](../references/spm-pbxproj.md).
2. **Has a `Package.swift`** — an SPM package / SPM-defined target. Edit it: add the `.package` + `.product` entries (see [`../examples/Package.swift.snippet`](../examples/Package.swift.snippet)).

Both file-editing paths need the latest tag for the version (`from:`, or the pbxproj version rule) — resolve it with:

```bash
git ls-remote --tags --refs https://github.com/sumsub/IdensicMobileSDK-iOS.git \
  | awk -F/ '{print $NF}' | sort -V | tail -1
```

## Next

- Add permissions & capabilities → [`3-permissions.md`](3-permissions.md) (it also covers the Info.plist / entitlement keys any modules you added need)
