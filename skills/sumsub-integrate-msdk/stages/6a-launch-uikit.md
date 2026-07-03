# Step 6A — Launch point (UIKit)

> **You're here if:** the host app launch screen is a UIKit `UIViewController`.
> **Prereqs:** the integration file is created and in the target.

Add the call to the ViewController the user named in intake. Before writing, show the user the exact lines you intend to add:

```swift
// In the ViewController the user specified — keep a strong property, not a
// throwaway local: the token fetch is async, and a local would deallocate first.
private let sumsub = SumsubVerification()
// …then, on the trigger (e.g. button tap):
sumsub.start(from: self)
```

## Next

- Core flow is done — return to **Handoff** in [`../SKILL.md`](../SKILL.md).
