# Stage 2 — Map tokens onto the SDK theme

> **You're here if:** the scan is done (and any open decisions are resolved with the user).
> **Prereqs:** seed colors + additional tokens identified.

## Build the Palette

Construct a palette from the **six** seeds using alpha-derivation — the same approach as the SDK's internal `SNSTheme.Palette`. All derived colors fade the seed by an alpha; no HSL manipulation is needed.

> **Critical — the neutral seed must not resolve to pure black.** `backgroundNeutral` (and the slots it backs — the not-submitted status card, the country / phone field) is correctly derived as `neutral × 0.05`, a faint tint of the strong text color — **keep that derivation; don't swap in a flat surface color.** The catch: the SDK pipes every `*Background` token (and their internal `sns_*BackgroundColor` aliases) through a "safe" guard that replaces any color whose **white component is 0** — pure black, *alpha ignored* — with an **opaque** `#010101`. So if `neutral` resolves to pure `#000` (`.label` in light mode, `UIColor.black`), `neutral × 0.05` is force-opaqued into a solid black block — which is why those surfaces went **black in light mode** but were fine in dark (there `.label` resolves to white, white ≠ 0). **Fix the seed, not the slot:** if `neutral` resolves to pure `#000` (`.label` in light mode, `UIColor.black`), nudge it to `#010101` (`UIColor(white: 1.0/255.0, alpha: 1)`) — the minimal off-black that clears the guard (white component ≠ 0; it's literally the value the guard itself substitutes). Visually identical for text, and its 5% tint then survives.
> 
> The guard checks the *resolved* value, whatever the source — an app token can itself be `.label` or a system color (e.g. an asset defined as `secondarySystemBackgroundColor`), so check what your neutral actually resolves to.

```
background100 = background          neutral100 = text
primary100 = accent                 neutral80  = text × 0.80
primary80  = accent × 0.80          neutral60  = text × 0.60
primary50  = accent × 0.50          neutral40  = text × 0.40
primary20  = accent × 0.20          neutral20  = text × 0.20
primary10  = accent × 0.10          neutral10  = text × 0.10
primary5   = accent × 0.05          neutral5   = text × 0.05

success100  warning100  critical100   (seeds, full strength)
successN    warningN    criticalN     (same alpha scale: 20/10/…)
```

**Info has no seed** — the SDK derives it from the accent: `contentInfo = primary100`, `backgroundInfo = primary10`. So info **is** the accent; never invent a separate info color.

**Semantic ramps go two ways:** the seed feeds `content*` at full strength (×100), and the matching `background*` is the same color faded (×10–20). So capture the app's *strong* semantic color (the one used for text/icons); the pale background variant is derived.

For dynamic (light/dark) seeds, `.withAlphaComponent` preserves the dynamic behavior, so the faded tokens adapt per appearance automatically — just heed the pure-black guard above for the `*Background` slots. If two adjacent tokens resolve to the same value, keep one and reuse it.

**SwiftUI source tokens:** if the app exposes its palette as SwiftUI `Color` (e.g. a central `Theme: ObservableObject` with `Color` properties), bridge each to UIKit at the read site — `let accent = UIColor(appTheme.accent)`. `Color` → `UIColor` is lossless on iOS 14+ and preserves light/dark. The generated theme always stores `UIColor`; never assign a `Color` to a `colors.*` slot.

## Map every color

Assign every SDK color property. **Palette baseline** is the default; apply the **direct app token** instead when one was found (the "override when" condition). **Context** is where the token actually shows up in the flow — use it to judge whether an app token genuinely belongs.

| SDK property | Context (where it shows) | Palette baseline | Override when |
|---|---|---|---|
| `navigationBarItem` | Nav-bar item tint (back + close buttons) | `neutral60` | App has a specific nav-bar icon tint |
| `alertTint` | System alert action color | `primary100` | App has a distinct alert tint |
| `backgroundCommon` | Background of almost every screen | `background100` | — (always a seed) |
| `backgroundNeutral` | Step-state bg (incl. **not-submitted status card**) + `.filled` card bg | `neutral5` | App has an explicit card/surface color |
| `backgroundInfo` | Notification-panel / info surfaces | `primary10` | App has an explicit info-state surface |
| `backgroundSuccess` | Success state bg + success picture | `success20` | App has an explicit success surface |
| `backgroundWarning` | Warning state bg + warning picture | `warning10` | App has an explicit warning surface |
| `backgroundCritical` | Critical state bg + failure picture | `critical20` | App has an explicit error surface |
| `contentLink` | Text links | `primary100` | App has a distinct link color |
| `contentStrong` | Headlines + `subtitle1` | `neutral100` | — (always a seed) |
| `contentNeutral` | Body / `subtitle2` / `caption` / accessories | `neutral80` | App has explicit secondary-text color |
| `contentWeak` | Minor captions / light accessories | `neutral80` | App has explicit tertiary color |
| `contentInfo` | Info surfaces: notification panel / toasts / cards + video viewport border | `primary100` | — (derives from accent) |
| `contentSuccess` | Success-state text / icon | `success100` | — |
| `contentWarning` | Warning-state text / icon | `warning100` | — |
| `contentCritical` | Critical-state text / icon | `critical100` | — |
| `primaryButtonBackground` | Primary button fill | `primary100` | App primary button has its own bg |
| `primaryButtonBackgroundHighlighted` | Primary button pressed | primaryBg × 0.8 | — |
| `primaryButtonBackgroundDisabled` | Primary button disabled | primaryBg × 0.4 | — |
| `primaryButtonContent` | Primary button label | white (verify ≥ 4.5:1) | App has explicit button-label color |
| `primaryButtonContentHighlighted` | Primary label pressed | primaryContent × 0.8 | — |
| `primaryButtonContentDisabled` | Primary label disabled | primaryContent × 0.6 | — |
| `secondaryButtonBackground` | Secondary button fill | `.clear` | App uses filled secondary buttons |
| `secondaryButtonBackgroundHighlighted` | Secondary button pressed | `primary5` (clear bg) or bg × 0.8 | — |
| `secondaryButtonBackgroundDisabled` | Secondary button disabled | `.clear` (when bg clear) | — |
| `secondaryButtonContent` | Secondary button label | `primary100` | App secondary button has own content color |
| `secondaryButtonContentHighlighted` | Secondary label pressed | secondaryContent × 0.8 | — |
| `secondaryButtonContentDisabled` | Secondary label disabled | secondaryContent × 0.5 | — |
| `fieldButtonBackgroundHighlighted` | Phone-field country button (pressed) | `neutral5` | — |
| `linkButtonBackgroundHighlighted` | Link button (pressed) | `primary5` | — |
| `linkButtonContent` | Link-button label (also the `button` font color) | `primary100` | — |
| `linkButtonContentDisabled` | Link-button label disabled | `primary50` | — |
| `cardPlainBackground` | `.plain` card bg (nullable) | `nil` | App uses plain-card surfaces |
| `cardBorderedBackground` | `.bordered` card bg (nullable) | `nil` | App uses bordered-card surfaces |
| `cameraBackground` | Camera screen background | near-black `UIColor(white: 0.1, alpha: 1)` | App camera uses a custom dark tint |
| `cameraBackgroundOverlay` | Camera dimming overlay | cameraBackground × 0.8 | — |
| `cameraContent` | Camera control tints (gallery / shutter) | `white × 0.8` | — |
| `fieldBackground` | Text-field background | `neutral5` | App fields have an explicit background |
| `fieldBackgroundInvalid` | Invalid text-field background | `critical10` | — |
| `fieldBorder` | Text-field border | `.clear` | App fields have a visible border |
| `fieldPlaceholder` | Field placeholder text | `neutral40` | App has an explicit placeholder color |
| `fieldContent` | Field input text | `neutral80` | — |
| `fieldTint` | Field cursor / checkboxes / radios | `primary100` | — |
| `listSeparator` | List item separators | `neutral20` | — |
| `listSelectedItemBackground` | Selected list / picker item bg | `neutral5` | — |
| `bottomSheetHandle` | Bottom-sheet grab handle | `neutral20` | — |
| `bottomSheetBackground` | Bottom-sheet panel bg | background | — |
| `toolbarTint` | Toolbar button tint | `primary100` | App has a distinct toolbar tint |
| `toolbarBackground` | Toolbar bar background | `nil` | — |
| `progressBarShimmer` | Progress-bar shimmer sweep | `white50` light / `white20` dark | — |
| `progressBarBackground` | Progress-bar unfilled track | `primary20` | — |
| `progressBarTint` | Progress-bar fill | `primary100` | — |

## Background & card pitfalls (read before mapping `backgroundCommon` / cards)

- **`backgroundCommon` also paints the navigation bar.** It's not just the content area — the SDK sets the nav-bar background to `backgroundCommon`. So if you seed it from a *secondary / surface* asset (e.g. a grey `…_background` card color), the nav bar and safe area read grey while the rest of the screen reads white (or vice-versa) — a visible mismatch. **Seed `backgroundCommon` from the app's true primary screen background**, not a card/surface color. If the only `background`-named asset is a secondary surface, or the app is single-appearance / the primary is ambiguous, prefer `.systemBackground` (adaptive) over a fixed grey surface.

- **`nil` cards are transparent, not "white".** `cardPlainBackground` / `cardBorderedBackground = nil` makes the SDK use `clearColor`, so cards show **whatever is behind them**. The default `verificationStepCardStyle` is `.filled`, so the standard status cards take `backgroundNeutral` (handle it per the bullet above) — these `nil` slots only bite if you switch to `.plain` / `.bordered`, in which case give them an explicit opaque surface.

## Font mapping

Map host app font roles to SDK slots. A custom font is usable as long as `UIFont(name:)` resolves it at runtime; the `?? .systemFont(...)` fallback below catches a miss, so prefer the app font and flag any uncertainty in the report. (Custom fonts are normally registered through `UIAppFonts` — the *Fonts provided by application* array in Info.plist.)

**Verify registration.** If a custom font file (`.ttf`/`.otf`) is bundled but **not** listed in `UIAppFonts`, `UIFont(name:)` returns nil and the SDK silently renders the system font instead. When you map a custom font, check the Info.plist `UIAppFonts` array; if the family is missing, call it out in the Stage 4 report (the theme still compiles thanks to the fallback — it just won't show the brand font until registered).

| SDK slot | Default | Paired content color | Host app role |
|---|---|---|---|
| `headline1` | System Bold 24pt | `contentStrong` | Largest title / h1 |
| `headline2` | System Bold 20pt | `contentStrong` | Section title / h2 |
| `subtitle1` | System Semibold 18pt | `contentStrong` | Emphasized subtitle |
| `subtitle2` | System Regular 16pt | `contentNeutral` | Secondary subtitle |
| `body` | System Regular 14pt | `contentNeutral` | Body / form labels |
| `button` | System Semibold 18pt | `linkButtonContent` | Button label |
| `caption` | System Regular 12pt | `contentWeak` | Captions / footnotes |

Always provide a system fallback:
```swift
fonts.headline1 = UIFont(name: "Inter-Bold", size: 24) ?? .systemFont(ofSize: 24, weight: .bold)
```

## Metrics mapping

| SDK property | Source | Default if not found |
|---|---|---|
| `buttonHeight` | App primary button height (pt) | 48 |
| `buttonCornerRadius` | App button corner radius | 8 |
| `buttonBorderWidth` | Secondary button border width | 1 |
| `fieldHeight` | Text field height | 48 |
| `fieldCornerRadius` | Text field corner radius | 8 |
| `fieldBorderWidth` | Text field border width | 0; set to 1 if `fieldBorder` is non-clear |
| `cardCornerRadius` | Card / surface corner radius | same as `fieldCornerRadius` |
| `cardBorderWidth` | Card border width | 1 |
| `screenHorizontalMargin` | Dominant screen side padding (see Stage 1) | 16 |
| `commonStatusBarStyle` | Auto from bg luminance (see below) | — |
| `cameraStatusBarStyle` | `.default` (SDK default) | `.default` |

`screenHorizontalMargin` drives **every** horizontal content inset in the SDK, so matching the app's dominant side padding is what makes the flow feel laid out like the host.

**Status bar auto-detection:** use the light-mode variant of `backgroundCommon`. Perceived luminance `L = 0.299R + 0.587G + 0.114B`. If `L < 0.5` → `.lightContent`; else → `.default` (adaptive on iOS 13+). It's a single static value — pick by the light appearance, the default OS mode.

## Icons

`iconClose` and `iconBack` default to the SDK's **own** built-in glyphs (a cross and an arrow). Override them only when the host app uses custom assets for those controls. To match an app that uses the system back chevron, set `images.iconBack = nil` — that switches the SDK to the iOS system back button (this is a deliberate choice, not the default).

Do not override any other `images.*` entries unless the user explicitly asks.

## Left at SDK defaults (set only on explicit request)

Beyond the tables above, `SNSThemeMetrics` also has document-frame / autocapture-frame / viewport widths and radii, the `*CardStyle` enums (`verificationStepCardStyle`, etc.), bottom-sheet sizing, header alignments, and close-bar style — and `images.*` holds ~35 template icons plus picture/step/document dictionaries. The skill leaves all of these at the SDK default (they recolor themselves from `colors`); touch them only if the user names one.

## Next

- [`3-generate.md`](3-generate.md) — write the theme file.
