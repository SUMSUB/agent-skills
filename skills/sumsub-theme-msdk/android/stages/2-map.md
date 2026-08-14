# Stage 2 (Android) — Map tokens onto the SDK theme

> **You're here if:** the scan is done (and any open decisions are resolved with the user).
> **Prereqs:** seed colors + additional tokens identified.

## Build the Palette

Construct a palette from the **six** seeds using alpha-derivation. All derived colors fade the seed by an alpha; no HSL
manipulation is needed. In code that's `ColorUtils.setAlphaComponent(seed, (fraction * 255).roundToInt())`
(androidx.core) applied to the resolved ARGB int.

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

**Info has no seed** — derive it from the accent: `contentInfo = primary100`, `backgroundInfo = primary10`. So info
**is** the accent; never invent a separate info color.

**Semantic ramps go two ways:** the seed feeds `content*` at full strength (×100), and the matching `background*` is the
same color faded (×10–20). So capture the app's *strong* semantic color (the one used for text/icons); the pale
background variant is derived.

## Light/dark — resolve both variants explicitly

`SNSThemeColor` takes **two** colors: `SNSThemeColor(light, dark)` — those are the actual parameter names; one argument
means "same in both modes". Unlike iOS dynamic colors, an Android color **resolved from resources is a flat int for the
current UI mode** — reading `R.color.x` once does *not* carry the night variant. So for a dual-appearance app:

- **Resource-qualified colors** (`values` + `values-night`): resolve each color **twice**, through a light- and a
  dark-configuration context (the generated file includes the helper — see Stage 3), and pass both to
  `SNSThemeColor(light, dark)`.
- **Compose schemes**: read the same token from the light and dark `ColorScheme` objects
  (`LightColors.primary.toArgb()`, `DarkColors.primary.toArgb()`).
- **Single-appearance app** (confirmed in Stage 1): the one-argument constructor is correct; note the mode in the
  report.

Alpha-derivation composes with this: derive from the light seed **and** the dark seed separately, then pair the results.

## Map every color

Assign every SDK color property. **Palette baseline** is the default; apply the **direct app token** instead when one
was found (the "override when" condition). **Context** is where the token actually shows up in the flow — use it to
judge whether an app token genuinely belongs.

| SDK property                           | Context (where it shows)                          | Palette baseline                                        | Override when                                                     |
|----------------------------------------|---------------------------------------------------|---------------------------------------------------------|-------------------------------------------------------------------|
| `navigationBarItem`                    | Close-button tint                                 | `neutral60`                                             | App has a specific app-bar icon tint                              |
| `alertTint`                            | System alert actions + toolbar buttons            | `primary100`                                            | App has a distinct alert/toolbar tint                             |
| `statusBarColor`                       | Status bar behind the SDK screens                 | `background100`                                         | App uses a distinct status-bar color                              |
| `backgroundCommon`                     | Background of almost every screen + alerts        | `background100`                                         | — (always a seed)                                                 |
| `backgroundNeutral`                    | Step-state bg + `DEFAULT`-style card bg           | `neutral5`                                              | App has an explicit card/surface color                            |
| `backgroundInfo`                       | Processing-state bg (applicant-data multi-select) | `primary10`                                             | App has an explicit info-state surface                            |
| `backgroundSuccess`                    | Success step-state bg                             | `success20`                                             | App has an explicit success surface                               |
| `backgroundWarning`                    | Warning step-state bg                             | `warning10`                                             | App has an explicit warning surface                               |
| `backgroundCritical`                   | Critical step-state bg                            | `critical20`                                            | App has an explicit error surface                                 |
| `contentLink`                          | Text links                                        | `primary100`                                            | App has a distinct link color                                     |
| `contentStrong`                        | Headlines / some subtitles / alert text           | `neutral100`                                            | — (always a seed)                                                 |
| `contentNeutral`                       | Body / `subtitle2` / accessories                  | `neutral80`                                             | App has explicit secondary-text color                             |
| `contentWeak`                          | Minor captions + inactive radio/checkbox          | `neutral80`                                             | App has explicit tertiary color                                   |
| `contentInfo`                          | Video-screen viewport border                      | `primary100`                                            | — (derives from accent)                                           |
| `contentSuccess`                       | Success-state text / icon                         | `success100`                                            | —                                                                 |
| `contentWarning`                       | Warning-state text / icon                         | `warning100`                                            | —                                                                 |
| `contentCritical`                      | Critical-state text / icon                        | `critical100`                                           | —                                                                 |
| `primaryButtonBackground`              | Primary button fill                               | `primary100`                                            | App primary button has its own bg                                 |
| `primaryButtonBackgroundHighlighted`   | Primary button pressed                            | primaryBg × 0.8                                         | —                                                                 |
| `primaryButtonBackgroundDisabled`      | Primary button disabled                           | primaryBg × 0.4                                         | —                                                                 |
| `primaryButtonContent`                 | Primary button label                              | white (verify ≥ 4.5:1)                                  | App has explicit button-label color                               |
| `primaryButtonContentHighlighted`      | Primary label pressed                             | primaryContent × 0.8                                    | —                                                                 |
| `primaryButtonContentDisabled`         | Primary label disabled                            | primaryContent × 0.6                                    | —                                                                 |
| `secondaryButtonBackground`            | Secondary button fill                             | transparent                                             | App uses filled secondary buttons                                 |
| `secondaryButtonBackgroundHighlighted` | Secondary button pressed                          | `primary5` (transparent bg) or bg × 0.8                 | —                                                                 |
| `secondaryButtonBackgroundDisabled`    | Secondary button disabled                         | transparent (when bg transparent)                       | —                                                                 |
| `secondaryButtonContent`               | Secondary button label                            | `primary100`                                            | App secondary button has own content color                        |
| `secondaryButtonContentHighlighted`    | Secondary label pressed                           | secondaryContent × 0.8                                  | —                                                                 |
| `secondaryButtonContentDisabled`       | Secondary label disabled                          | secondaryContent × 0.5                                  | —                                                                 |
| `linkButtonContent`                    | Link-button label                                 | `primary100`                                            | —                                                                 |
| `linkButtonContentDisabled`            | Link-button label disabled                        | `primary50`                                             | —                                                                 |
| `linkButtonBackgroundHighlighted`      | Link button (pressed)                             | `primary5`                                              | —                                                                 |
| `cardPlainBackground`                  | `PLAIN` card bg                                   | SDK default (transparent)                               | App uses plain-card surfaces                                      |
| `cardBorderedBackground`               | `BORDERED` card bg                                | SDK default (transparent)                               | App uses bordered-card surfaces                                   |
| `cameraBackground`                     | Camera screen background                          | near-black `0xFF1A1A1A` (the SDK default)               | App camera uses a custom dark tint                                |
| `cameraBackgroundOverlay`              | Camera dimming overlay                            | cameraBackground × 0.75                                 | —                                                                 |
| `cameraContent`                        | Camera control tints (gallery / capture)          | white                                                   | —                                                                 |
| `fieldBackground`                      | Text-field background                             | `neutral5`                                              | App fields have an explicit background                            |
| `fieldBackgroundInvalid`               | Invalid text-field background                     | `critical10`                                            | —                                                                 |
| `fieldBorder`                          | Text-field border                                 | transparent                                             | App fields have a visible border                                  |
| `fieldBorderDisabled`                  | Disabled text-field border                        | transparent (or border × 0.5 when border set)           | —                                                                 |
| `fieldBorderFocused`                   | Focused text-field border                         | transparent; `primary100` if the app shows a focus ring | App uses Material outlined fields (focus ring is their signature) |
| `fieldPlaceholder`                     | Field placeholder text                            | `neutral40`                                             | App has an explicit placeholder color                             |
| `fieldContent`                         | Field input text                                  | `neutral80`                                             | —                                                                 |
| `fieldTint`                            | Field cursor / checkboxes / radios (active)       | `primary100`                                            | —                                                                 |
| `listSeparator`                        | List item separators                              | `neutral20`                                             | —                                                                 |
| `listSelectedItemBackground`           | Selected list / picker item bg                    | `neutral5`                                              | —                                                                 |
| `bottomSheetHandle`                    | Bottom-sheet grab handle                          | `neutral20`                                             | —                                                                 |
| `bottomSheetBackground`                | Bottom-sheet panel bg                             | `background100`                                         | —                                                                 |
| `progressBarTint`                      | Progress indicator fill                           | `primary100`                                            | —                                                                 |
| `progressBarBackground`                | Progress indicator track                          | `primary20`                                             | —                                                                 |

**Not on Android** (don't port from iOS): `toolbarTint` / `toolbarBackground` (covered by `alertTint`),
`progressBarShimmer`, `fieldButtonBackgroundHighlighted`, and the whole `images.*` section — Android SDK icons recolor
themselves from `colors`; there is nothing to override in the Theme API.

**Transparent cards show what's behind them.** `cardPlainBackground` / `cardBorderedBackground` default to transparent,
and the default `verificationStepCardStyle` is `DEFAULT`, whose cards take `backgroundNeutral`. The transparent slots
only bite if you switch a `*CardStyle` metric to `PLAIN` / `BORDERED` — give them an explicit opaque surface in that
case.

## Font mapping

Map host app font roles to SDK slots. `SNSThemeFont(typeface: Typeface, sizeSp: Int)` — the size is in **sp**. Load
custom fonts with `ResourcesCompat.getFont(context, R.font.…)` and always keep a system fallback
(`?: Typeface.DEFAULT` / `DEFAULT_BOLD`) — a missing or renamed font resource must degrade, not crash.

| SDK slot    | Paired content color | Host app role        | Typical size |
|-------------|----------------------|----------------------|--------------|
| `headline1` | `contentStrong`      | Largest title / h1   | 24sp         |
| `headline2` | `contentStrong`      | Section title / h2   | 20sp         |
| `subtitle1` | `contentStrong`      | Emphasized subtitle  | 18sp         |
| `subtitle2` | `contentNeutral`     | Secondary subtitle   | 16sp         |
| `body`      | `contentNeutral`     | Body / form labels   | 14sp         |
| `caption`   | `contentWeak`        | Captions / footnotes | 12sp         |

There is **no `button` font slot** on Android — button typography is SDK-managed. Take sizes from the app's own
typography (Compose `Typography` or text-appearance styles) when it defines these roles; the sp values above are the
fallback scale.

```kotlin
fonts.headline1 = SNSThemeFont(
    ResourcesCompat.getFont(context, R.font.inter_bold) ?: Typeface.DEFAULT_BOLD, 24
)
```

## Metrics mapping

Metric `Float` values are **pixels** — convert the app's dp values at build time (the generated file includes a `dp()`
helper; `resources.getDimension(...)` also returns px).

| SDK property             | Source                                     | Default if not found                                |
|--------------------------|--------------------------------------------|-----------------------------------------------------|
| `buttonHeight`           | App primary button height (dp)             | 48dp                                                |
| `buttonCornerRadius`     | App button corner radius                   | 8dp                                                 |
| `buttonBorderWidth`      | Secondary button border width              | 1dp                                                 |
| `fieldHeight`            | Text field height                          | 48dp                                                |
| `fieldCornerRadius`      | Text field corner radius                   | 8dp                                                 |
| `fieldBorderWidth`       | Text field border width                    | 0dp; set to 1dp if `fieldBorder` is non-transparent |
| `cardCornerRadius`       | Card / surface corner radius               | same as `fieldCornerRadius`                         |
| `cardBorderWidth`        | Card border width                          | 1dp                                                 |
| `screenHorizontalMargin` | Dominant screen side padding (see Stage 1) | 16dp                                                |

`screenHorizontalMargin` drives **every** horizontal content inset in the SDK, so matching the app's dominant side
padding is what makes the flow feel laid out like the host.

## Left at SDK defaults (set only on explicit request)

Beyond the tables above, `metrics` also has `activityIndicatorStyle` (spinner size), `viewportBorderWidth` (selfie
viewport), `bottomSheetCornerRadius` / `bottomSheetHandleSize`, `listSeparatorHeight` / `listSeparatorMarginLeft` /
`listSeparatorMarginRight`, `segmentedControlCornerRadius`, the document-frame metrics (`documentFrameBorderWidth` /
`documentFrameCornerRadius` / `documentFrameCornerSize`), the eight `*CardStyle` enums (`verificationStepCardStyle`,
`supportItemCardStyle`, `documentTypeCardStyle`, `selectedCountryCardStyle`, `agreementCardStyle`,
`videoIdentLanguageCardStyle`, `videoIdentStepCardStyle`, `sumsubIdCardStyle` — values `DEFAULT` / `PLAIN` /
`BORDERED`), and `screenHeaderAlignment` / `sectionHeaderAlignment`. The skill leaves all of these at the SDK default;
touch them only if the user names one.

## Next

- [`3-generate.md`](3-generate.md) — write the theme file.
