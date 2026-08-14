# Stage 4 (Android) — Report

> **You're here if:** `SumsubTheme.kt` is written and `.withTheme(sumsubTheme(activity))` is attached at the launch site
> (Stage 3).
> **Prereqs:** the file exists on disk under a source set.

This is the summary the user actually reads — make it the human-readable wrap-up of the whole job. **Always lead with
the value** (hex or resource name) and add a plain-word description **in parentheses** so they can picture it — e.g.
"primaryButtonBackground → `#0A84FF` (your brand color, a vivid medium blue)" — using [
`../../references/color-language.md`](../../references/color-language.md). Never drop the hex; the words are a reference
aid, not a replacement. For dual-appearance apps show both values ("`#FFFFFF` light / `#1E232E` dark").

Present a coverage table grouped by section (Colors / Fonts / Metrics):

```
Mapped directly   — token found in app, used as-is (with value)
Derived           — derived from [seed] via alpha × N (with value)
Left at default   — property intentionally left at the SDK default
Not found         — not detected; palette fallback used (with derived value)
```

Also call out: the launch site where `.withTheme(...)` was inserted (file:line), any contrast fix you made, any
non-obvious default you applied, and any choice the user picked.

## Next

- The walk is complete — return to **Guardrails** and **Handoff** in [`../../SKILL.md`](../../SKILL.md).
