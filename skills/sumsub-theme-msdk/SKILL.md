---
name: sumsub-theme-msdk
description: Analyze an iOS host app's design system (colors, fonts, corner radii, margins, light/dark) and generate Swift that themes the Sumsub Mobile SDK (SNSTheme) to match it. Use this whenever the user wants the Sumsub verification / KYC screens to match their app's look on iOS — "theme / brand / style the Sumsub SDK", "make the verification screen match my app", "match my KYC flow colors and fonts", "customize SNSMobileSDK appearance" — including when they don't say "theme" but ask to align the SDK's colors / fonts with their app. Scans for design tokens (asset-catalog `.colorset`, `Color` / `UIColor` & `Font` extensions, accent / tint, light/dark handling), derives a full palette, and writes a `SumsubTheme: SNSTheme` subclass. SKIP for theming the host app itself (this only styles the Sumsub SDK), web theming, and the SDK integration / setup (use `sumsub-integrate-msdk`). iOS only for now.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Sumsub — Mobile SDK theming (iOS)

Scan the host app's design system, derive a full palette, and write a `SumsubTheme: SNSTheme` subclass assigned as `sdk.theme = SumsubTheme()` — so the KYC screens match the app instead of looking bolted on. Every SDK theme property is either mapped from the app or explicitly derived; nothing is left at the SDK default by accident.

> **iOS only.** Android is not covered yet.

This is the **trunk** (always-on). Walk the four stages below in order: Scan → Map → Generate → Report.

## Asking vs doing — keep approvals meaningful

- **Read-only is free** — scan / grep / read the project's colors, fonts and build settings without asking.
- **Batch mutations into one approval**, not one per item ("I'll write `SumsubTheme.swift` here + insert this `sdk.theme = …` line [diff] — apply?").
- **Ask explicitly only for:** the target file path, genuinely ambiguous brand / legibility / font choices, and editing existing app code (the single `sdk.theme = …` line — the skill adds it itself, never punts it to the user).

## How to navigate this skill

A strictly linear flow — walk the four stages in order; each is self-contained and ends with a **Next** pointer:

1. [`stages/1-scan.md`](stages/1-scan.md) — scan the host app's design system (read-only).
2. [`stages/2-map.md`](stages/2-map.md) — map tokens onto the SDK theme (after resolving open decisions).
3. [`stages/3-generate.md`](stages/3-generate.md) — write the theme file (after the path is confirmed).
4. [`stages/4-report.md`](stages/4-report.md) — present the coverage report.

> **Fallback (last resort only).** This skill and its stage files are the primary source — don't reach for external docs by default. Only if you hit a genuine blocker they don't resolve, consult the [Sumsub iOS theme docs](https://docs.sumsub.com/docs/sdk-theme-api).

When the stages are walked, return here for **Guardrails** and **Handoff**.

## Guardrails — what this skill must never do

- **Never write the file without confirming the path** with the user.
- **Never leave a property at SDK default without noting it** in the report.
- **Never hard-code arbitrary values** — colors come from the app palette or the documented alpha-derivation.
- **Always show the hex** (or asset name) when reporting or asking; add a plain-word description in parentheses, never instead of the hex.
- **Never silently guess a genuinely ambiguous choice** — offer plain-word options + a recommendation; but don't over-ask where a safe default exists.
- **Never emit unsafe color/font code** — no flat `UIColor` literals for dual-appearance apps (use named assets or `UIColor { traits in … }`); no `UIFont(name:size:)` without a `?? .systemFont(…)` fallback; no decorative/app colors in the success/warning/critical slots.
- **Never theme the host app itself** — only the Sumsub SDK screens.
- **Never change SDK integration logic** (install / init / present). The skill's one edit to existing code is inserting `sdk.theme = …` at the launch site (after build, before show) — it makes that edit itself, with approval.
- **Never override `images.*` for verification-flow icons** — Sumsub-specific, not derivable from the host.

## Handoff

After the file is generated and wired, summarise:

1. **File created** — `SumsubTheme.swift` and where it lives; confirm it's a target member.
2. **Coverage** — the Stage 4 report (mapped / derived / nil), plus any contrast fix or choice the user made.
3. **Wiring done** — the exact launch site (file:line) where you inserted `sdk.theme = SumsubTheme()` (or `SumsubTheme.make()`). If no integration code was found (SDK not wired up yet), say so and point to [`sumsub-integrate-msdk`](../sumsub-integrate-msdk/SKILL.md) — the theme is ready to attach once it is.
