# Detecting an Android app's design system

How to find the host app's design tokens so they can be mapped onto `SNSTheme`. Each section says **what to find → which
SDK token it feeds**, then a focused command. Report what's present.

**Look in the design-system source first.** Many apps keep tokens in one place — a dedicated Gradle module (commonly
named `designsystem`, `ui`, `core-ui`, `theme`) or, for Compose apps, a `ui/theme/` package (`Color.kt`, `Theme.kt`,
`Type.kt`, `Shape.kt` — the Android Studio template layout). These are naming *conventions*, not known modules; find the
app's own. Scan it first, widen to the whole project only if there's no central source — broad name greps over a full
app hit network/analytics code and a stray `brandColor` literal can hijack the accent.

```bash
find . -type d \( -iname '*designsystem*' -o -iname 'theme' -o -iname 'core-ui' \) -not -path '*/build/*'
find . -path '*ui/theme/*' -name '*.kt' -not -path '*/build/*'
```

Exclude `build/` everywhere — generated R classes and merged resources are noise.

## 0. SDK version → Theme API availability

```bash
grep -rn 'idensic-mobile-sdk' --include='build.gradle*' --include='*.toml' .
```

## 1. Colors → seeds (`background`, accent→`primary`, `neutral`, `success`/`warning`/`critical`)

**XML resources** (View-based and hybrid apps):

```bash
find . -name 'colors.xml' -not -path '*/build/*'                      # values/ and values-night/
grep -rn 'color name=' --include='colors.xml' . | grep -iE 'accent|brand|primary|background|surface|text|succ|warn|error|critical|positive|destruct'
grep -rnE 'colorPrimary|colorSecondary|colorSurface|colorOnSurface|colorError|android:windowBackground|textColorPrimary' --include='themes.xml' --include='styles.xml' .
```

Theme attrs (`colorPrimary`, `colorSurface`, …) usually point at `@color/...` — chase the reference to the actual value.
A `values-night/` twin means dual appearance.

**Compose colors:**

```bash
grep -rnE 'lightColorScheme|darkColorScheme|Color\(0x' --include='*.kt' -l . | grep -v '/build/'
```

The `ColorScheme` builders are the richest source — `primary`, `background`, `onBackground`, `error` map straight onto
the seeds; a `darkColorScheme` sibling gives the night variants.

**Semantic state colors** — only count a hit that resolves to an **actual color** (a `<color>` resource, a `Color(0x…)`
literal). Bare `error` / `success` in network or analytics code is not a design token. Grep the colors/theme file you
already located, not the whole project.

## 2. Fonts → `fonts.*`

```bash
find . -path '*res/font*' -not -path '*/build/*'                      # bundled font resources
grep -rnE 'fontFamily|FontFamily\(|Font\(R\.font' --include='*.kt' --include='*.xml' . | grep -v '/build/'
```

Compose `Typography` (in `Type.kt`) gives the role → family/weight/size mapping directly; View apps carry it in
`TextAppearance` styles. Note representative **sp** sizes for headline / subtitle / body / caption. A font loaded with
`ResourcesCompat.getFont` resolves or returns null — the `?: Typeface.…` fallback in the theme catches a miss.

## 3. Metrics → `*CornerRadius`, `*Height`, `screenHorizontalMargin`

```bash
grep -rnE 'cornerRadius|RoundedCornerShape\(|ShapeAppearance' --include='*.kt' --include='*.xml' . | grep -v '/build/'
grep -rnE 'padding\(horizontal|layout_margin(Start|End|Horizontal)|marginHorizontal' --include='*.kt' --include='*.xml' . | grep -v '/build/'
find . -name 'dimens.xml' -not -path '*/build/*'
```

- **Corner radius:** pick the *dominant* value — Compose `Shapes` (`Shape.kt`) or a `ShapeAppearance` style usually
  settles it → `buttonCornerRadius` / `fieldCornerRadius` / `cardCornerRadius`.
- **Heights:** read from the button / field components found in §4 → `buttonHeight` / `fieldHeight`; the SDK defaults
  (48dp) are fine if none stands out.
- **Screen side padding:** the dominant horizontal content inset → `screenHorizontalMargin` (it drives every horizontal
  margin in the SDK). Default 16dp.

## 4. Buttons & fields → `primaryButton*` / `secondaryButton*` / `field*`

```bash
grep -rnE '(Primary|Secondary)Button|OutlinedButton|TextButton|Widget\.Material.*Button' --include='*.kt' --include='*.xml' . | grep -v '/build/'
grep -rnE 'OutlinedTextField|TextInputLayout|TextField\(' --include='*.kt' --include='*.xml' . | grep -v '/build/'
```

Determine: primary button background + label color; secondary button style (transparent / outlined vs filled) + border
width; text-field background, border (visibility / width / focus ring), corner radius, placeholder/text/tint colors.
`OutlinedTextField` / `TextInputLayout` box stroke = a visible `fieldBorder` and usually an accent `fieldBorderFocused`.
If there are no named styles, infer from the app's prominent call-to-action (usually the bottom-of-screen action).

## 5. Camera → `cameraBackground`

The camera background is near-black in almost every app — note a value **only** if the app has its own camera UI with an
explicitly different dark tint.

## 6. Light / dark handling

```bash
find . -type d -name 'values-night' -not -path '*/build/*'
grep -rnE 'isSystemInDarkTheme|setDefaultNightMode|darkColorScheme' --include='*.kt' . | grep -v '/build/'
```

Does the app follow the system, or force one mode (`AppCompatDelegate.setDefaultNightMode(MODE_NIGHT_NO/YES)`)?

- Both appearances → resolve every color **twice** (light + dark configuration contexts, or both Compose schemes) →
  two-argument `SNSThemeColor(light, dark)`.
- Single appearance → one-argument `SNSThemeColor`; note which mode.

## 7. UI toolkit (how to *read* tokens)

```bash
grep -rlE 'androidx\.compose' --include='*.kt' . | grep -v '/build/' | head
```

Compose vs Views only affects how you *read* tokens — the generated theme always emits ARGB ints and `Typeface`s. Report
which design-system shape the app uses (Compose theme package / XML resources + theme attrs / a token module) and which
tokens you extracted before Stage 2.
