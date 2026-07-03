# Step 2A — Install via CocoaPods

> **You're here if:** CocoaPods is the chosen dependency manager (per Step 1).
> **Prereqs:** Step 1 done — you know the app target.

The project already has a `Podfile` (we don't create one — no Podfile means SPM). Merge the Sumsub pieces into it; the full example is in [`../examples/Podfile.snippet`](../examples/Podfile.snippet):

- **Sources** (top of the Podfile, outside any target): `IdensicMobileSDK` lives in Sumsub's spec repo, so add `source 'https://github.com/SumSubstance/Specs.git'`. If the Podfile declares no `source` yet, also add the default `source 'https://cdn.cocoapods.org/'` — once any custom source is present, the default must be explicit.
- **Pods** (inside the existing app target's `target '…' do … end` block): `pod 'IdensicMobileSDK'`, plus a line per module confirmed in intake (Q3) — e.g. `pod 'IdensicMobileSDK/MRTDReader'`. None confirmed → just the base.
- **`use_frameworks!`**: IdensicMobileSDK is a dynamic Swift framework, so the app target needs dynamic linking. Check whether `use_frameworks!` is already declared (at the Podfile root or inside the app target's block). If it's missing, add it — prefer inside the app target's `do … end` block to scope it to that target. If the project deliberately uses static linking, flag the conflict and ask rather than forcing it.
- **Deployment target**: the SDK needs iOS ≥ 13. The effective minimum comes from both the Podfile's `platform :ios` line and the project's `IPHONEOS_DEPLOYMENT_TARGET` — reconcile them: both must be `13.0`+ and the value must actually reach the app target, otherwise `pod install` won't resolve. Raise it where the client declared it (the `platform` line, the project, or the target's build settings).

In the snippet `YourApp` is a placeholder — use the project's real app target. Apply in **one edit**; tell the user exactly what you'll add and why, ask once, and edit only after explicit approval.

After editing, ask: "Should I run `pod install` now, or would you prefer to run it yourself?" Run it **only with explicit permission**.

## Next

- Add permissions & capabilities → [`3-permissions.md`](3-permissions.md) (it also covers the Info.plist / entitlement keys any modules you added need)
