# Stage 1 — Scan the host app's design system

> **You're here if:** the user wants to theme the Sumsub SDK to match their iOS app.
> **Prereqs:** none — this stage is read-only (scan / grep / read); no approval needed.

Full detection greps and globs: [`../references/detection-guide.md`](../references/detection-guide.md).

Collect the tokens below into an internal picture (you'll present it in the Stage 4 report). For each, note: found / not found, source (asset / code / inferred), and the light + dark values if both exist.

## Seed colors (build the Palette from these six)

| Token | Where to look | Notes |
|---|---|---|
| **Background** | `backgroundCommon`, `backgroundColor`, `.background`, `BackgroundPrimary`, asset `PrimaryBackground` / `Background` | Main screen background — pick the **primary** screen bg, not a card/surface color (it also paints the SDK nav bar; see Stage 2 pitfalls). Fall back to `.systemBackground` if only a secondary surface exists |
| **Accent / tint** | `AccentColor.colorset`, `tintColor`, `accentColor`, `.accentColor`, `primary`, `brand` | The principal branded color; also drives info |
| **Neutral (text)** | `label`, `primaryText`, `foreground`, `contentPrimary`, asset `Label` / `Foreground` / `PrimaryText` | Dominant text color |
| **Success** | `success`, `green`, `.success`, `positive` | Approved state — capture the **strong** color |
| **Warning** | `warning`, `orange`, `.warning`, `caution` | Pending state — capture the **strong** color |
| **Critical** | `error`, `destructive`, `critical`, `red`, `.critical` | Rejected state — capture the **strong** color |

For success / warning / critical, capture the **strong** color (the one used for text and icons). The SDK feeds it into `content*` at full strength and derives the pale `background*` state surfaces from it automatically — you don't need a separate pale variant.

**Info needs no seed.** The SDK uses the accent for it (`contentInfo` = accent, `backgroundInfo` = accent faded). Don't hunt for or invent an info / blue color.

**Missing seeds — fallback derivation:** if success / warning / critical are absent, derive them from the nearest found color by rotating its hue: success ≈ 140° (green), warning ≈ 30° (orange), critical ≈ 0° (red). Keep moderate-to-strong saturation and roughly the same lightness as the other seeds.

## Additional tokens (direct overrides — capture carefully)

These take **priority** over the palette-derived baselines — they're what make the theme actually match the app instead of looking like a tinted SDK default. Don't treat them as optional:

- **Primary button**: background color, label color, corner radius, height
- **Secondary button**: style (outlined / filled / text-only), bg color, label color, border width. If the app exposes no named button styles, infer from its prominent call-to-action buttons (usually the bottom-of-screen action). Whatever you find, the Stage 2 mapping fills the **full** primary + secondary color set from the accent — never leave button states unset.
- **Field / input**: background, border color, border width, corner radius, height
- **Navigation bar**: back-button icon (custom asset vs system chevron), tint color
- **Camera screen**: background color (almost always near-black; note only if substantially different)
- **Typography**: font family, weight-to-role mapping (headline / body / button / caption), sizes
- **Screen layout**: the dominant horizontal side padding the app uses for content → `screenHorizontalMargin` (it drives every horizontal inset in the SDK, so matching it makes the flow feel laid out like the host)

## Light/dark handling

Detect how the app stores color variants:
- `.colorset` with `light`/`dark` appearances → `UIColor(named:)` carries both
- `UIColor { traits in ... }` in code → reconstruct the same pattern
- Single appearance only → flat literal; note which mode it is

## Decisions to put to the user (don't guess)

Theming is taste plus legibility. Decide everything you safely can from documented defaults and proceed — **only pause to ask when one of these is genuinely open**, as a short multiple-choice with each option in plain words, a one-line "why", and one marked **recommended**. Use [`../references/color-language.md`](../references/color-language.md) for the wording and the contrast/harmony reasoning.

- **Several accent / brand candidates.** More than one plausible brand color (e.g. an `AccentColor` *and* a differing `tintColor`). → "Which is your brand color?" — show each as hex + parenthetical description; it drives the whole palette.
- **A primary-button legibility problem.** Accent fill + white label is below 4.5:1 (light/pastel accents). → offer "dark text on your color (recommended)", "darken the color for white text", "keep as-is (fails legibility)". Always cite the approximate ratio and *why*.
- **Missing semantic colors.** No success / warning / critical in the app. → "I can derive a standard green / amber / red (recommended), reuse your accent, or you can give me specific colors." Overriding the convention (e.g. a red brand into *success*) reads as wrong.
- **Secondary button style.** App's secondary style is unclear (outlined vs filled vs text-only). → show the options in words; it changes `secondaryButton*` + border.
- **Font role mapping.** The app exposes several fonts or a font *picker* (no single family). → ask which font maps to headings vs body. (Don't invent a mapping across 6 fonts silently.)
- **Light-only / dark-only app.** → confirm the SDK should match that single appearance rather than offering both.

For everything else (documented palette derivations, sensible metric defaults), proceed without asking — over-questioning is as bad as guessing. When you apply a non-obvious default, note it so it shows in the Stage 4 report and the user can veto it.

## Next

- Resolve any open decisions above, then → [`2-map.md`](2-map.md). (No mid-flow summary is needed — the full findings land in the Stage 4 report.)
