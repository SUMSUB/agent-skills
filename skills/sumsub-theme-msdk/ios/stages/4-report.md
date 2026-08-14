# Stage 4 — Report

> **You're here if:** `SumsubTheme.swift` is written, wired into the target, and `sdk.theme = …` is set at the launch site (Stage 3).
> **Prereqs:** the file exists on disk and is a target member.

This is the summary the user actually reads — make it the human-readable wrap-up of the whole job. **Always lead with the value** (hex or asset name) and add a plain-word description **in parentheses** so they can picture it — e.g. "primaryButtonBackground → `#0A84FF` (your brand color, a vivid medium blue)" — using [`../../references/color-language.md`](../../references/color-language.md). Never drop the hex; the words are a reference aid, not a replacement.

Present a coverage table grouped by section (Colors / Fonts / Metrics / Icons):

```
Mapped directly   — token found in app, used as-is (with value)
Derived           — derived from [seed] via alpha × N (with value)
Left at nil       — property is nullable and nil is intentional
Not found         — not detected; palette fallback used (with derived value)
```

Also call out: the launch site where `sdk.theme = …` was inserted (file:line), any contrast fix you made, any non-obvious default you applied, and any choice the user picked.

## Next

- The walk is complete — return to **Guardrails** and **Handoff** in [`../../SKILL.md`](../../SKILL.md).
