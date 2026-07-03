# Describing colors in plain language & judging combinations

**Always show the hex (or asset name)** — it's the authoritative value the user or their designer acts on, and it must never be dropped. But a bare hex is hard to picture, so add a plain-word description **in parentheses**, and explain *why* a pairing reads well or badly. This file is the rulebook for the words and the reasoning — the hex always stays.

## Hex → plain words

Convert the sRGB hex to HSL, then compose a short phrase **`[saturation] [lightness] [hue]`**, plus a familiar anchor when one is obvious.

**Hue family** (HSL hue°, ignore when saturation is very low):

| ° | Family | ° | Family |
|---|---|---|---|
| 345–15 | red | 150–195 | teal |
| 15–30 | coral / orange-red | 195–210 | cyan |
| 30–45 | orange | 210–250 | blue |
| 45–60 | amber / gold | 250–270 | indigo |
| 60–75 | yellow | 270–290 | violet |
| 75–100 | lime | 290–330 | magenta / purple |
| 100–150 | green | 330–345 | pink |

**Lightness:** <12 % near-black / charcoal · 12–30 % dark · 30–55 % medium · 55–80 % light · >80 % near-white.

**Saturation:** <15 % muted / greyish (call it **grey** — warm or cool — if lightness is mid and saturation is near zero) · 15–50 % soft / moderate · 50–80 % rich · >80 % vivid.

Examples: `#0A84FF` → "a vivid medium blue (iOS system blue)"; `#1C1C1E` → "near-black charcoal"; `#E5C07B` → "a soft light amber"; `#F2F2F7` → "an almost-white cool grey"; `#34C759` → "a vivid green (the standard 'success' green)".

**Dynamic (light/dark) colors:** describe both variants — "light mode: near-white; dark mode: near-black charcoal".

## Judging a pairing — why it works or clashes

State the reason in one line whenever you flag or recommend something.

- **Contrast = legibility (the hard rule).** Text vs its background should hit WCAG **≥ 4.5:1** (normal text) / **≥ 3:1** (large text & UI elements). A button label on its fill is text → **≥ 4.5:1**. Below that it "clashes" because it's hard to read — always cite the approximate ratio. Classic trap: a **light or pastel accent + white text** lands around 1.5–2.5:1 (unreadable) → propose dark text or a darker fill.
- **Saturation balance.** Muted/neutral UI with one vivid call-to-action is the safe, professional look (the eye goes to the CTA). Two competing vivids of equal area fight each other. An all-muted palette reads calm but flat.
- **Temperature & harmony.** Analogous hues (near each other on the wheel) feel calm and cohesive; complementary hues (opposite) pop but can "vibrate" if both are vivid and large. The reliable pattern: neutrals + one brand accent as the single pop.
- **Semantic convention (don't fight meaning).** Green = success, red = error/critical, orange = warning, blue = info. Never wire a brand color into a slot whose meaning it contradicts (e.g. a red brand color into the *success* slot) — users read the color, not the label. The exception is **info**: its color convention is soft, so when no blue fits the app's palette, the **accent** is the better choice there — cohesion beats a clashing blue.

## How to present a choice

Offer 2–4 concrete options, each leading with the value and a plain-word description in parentheses, name the trade-off in one line each, and mark one **recommended** (usually: keep the user's color, fix the legibility). Example:

> Your accent is `#5AC8FA` (a light sky blue). White button text on it is only ~1.9:1 — too faint to read. How should the primary button look?
> - **Dark text on your blue** — recommended; ~8:1, keeps your brand color.
> - **A darker blue with white text** — keeps white labels, shifts the hue a bit.
> - **Keep white on light blue** — not recommended; fails legibility.

Recommend, don't dictate — the user's brand may override the safe default, and that's their call. Just make the consequence visible.
