# Detecting an iOS app's design system

How to find the host app's design tokens so they can be mapped onto `SNSTheme`. Each section says **what to find → which SDK token it feeds**, then a focused command. Report what's present.

**Look in the design-system source first.** Many apps keep tokens in one place — a local SPM module (commonly named `DesignSystem`, `UIComponents`, `Design`, `Tokens`) or a central `Theme` / `Colors` / `Palette` type. These are naming *conventions*, not known packages; find the app's own. Scan it first, widen to the whole project only if there's no central source — broad name greps over a full app hit network/analytics code and a stray `brandColor` literal can hijack the accent.

```bash
find . -name 'Package.swift' -o -type d -iname '*designsystem*' -o -type d -iname '*uicomponents*'
grep -rlE 'struct (Theme|Colors|Palette|Tokens|DesignSystem)\b|enum (Theme|Colors|Palette)\b' --include='*.swift'
```

## 1. Colors → seeds (`background`, accent→`primary`, `neutral`, `success`/`warning`/`critical`)

**Asset catalogs** (most common, lowest-noise):
```bash
find . -type d -name '*.colorset'                       # all named colors
find . -type d -name '*.colorset' | grep -iE 'accent|tint|brand|primary|background|label|text|succ|warn|error|critical|positive|destruct'
cat <name>.colorset/Contents.json                       # components + appearances
```
`Contents.json` carries `components` and optional `appearances` (`luminosity: light|dark`). Check `color-space`: `display-p3` components are **not** sRGB — reconstruct with `UIColor(displayP3Red:…)` or convert before composing a hex / description; note the gamut.

**Code-defined colors:**
```bash
grep -rnE 'extension (UI)?Color' --include='*.swift'
grep -rniE '(accent|tint|primary|background|label|foreground)Color' --include='*.swift'
```
Look for a central `Theme`/`Colors` type, semantic names, and hex/RGB literals. An `@Observable` / `ObservableObject` `Theme` with a `tintColor` is the richest source — read its current values.

**Semantic state colors** — only count a hit that resolves to an **actual color** (a `.colorset`, a `UIColor`/`Color`, or a hex). Bare `error` / `success` in network or analytics code is not a design token. The colorset-name `find` above is the reliable signal; otherwise grep the colors/theme file you already located, not the whole project.

## 2. Fonts → `fonts.*`

```bash
grep -rnE 'extension (Font|UIFont)' --include='*.swift'
find . \( -name '*.ttf' -o -name '*.otf' \)             # bundled custom fonts
grep -rn 'UIAppFonts' --include='*.plist'               # "Fonts provided by application" key
```
A custom font is usable as long as `UIFont(name:)` resolves it at runtime; the `?? .systemFont(...)` fallback in the theme catches a miss. Note representative sizes/weights for headline / subtitle / body / button / caption.

## 3. Metrics → `*CornerRadius`, `*Height`, `screenHorizontalMargin`

```bash
grep -rnE '\.cornerRadius|cornerRadius:|RoundedRectangle\(cornerRadius:' --include='*.swift'
grep -rnE '\.padding\(\.horizontal|directionalLayoutMargins|layoutMargins' --include='*.swift'
```
- **Corner radius:** pick the *dominant* value — buttons, fields and cards usually share one → `buttonCornerRadius` / `fieldCornerRadius` / `cardCornerRadius`.
- **Heights:** read from the button / field components found in §4 → `buttonHeight` / `fieldHeight`; the SDK defaults (48) are fine if none stands out.
- **Screen side padding:** the dominant horizontal content inset → `screenHorizontalMargin` (it drives every horizontal margin in the SDK). Default 16.

No central constants file? Aggregate by frequency — the dominant radius and padding are obvious after a few screens.

## 4. Buttons & fields → `primaryButton*` / `secondaryButton*` / `field*`

```bash
grep -rnE 'ButtonStyle|PrimaryButton|SecondaryButton|\.bordered|\.borderedProminent|\.plain' --include='*.swift'
grep -rnE 'TextField|UITextField|textFieldStyle' --include='*.swift'
```
Determine: primary button background + label color; secondary button style (transparent/ outlined vs filled) + border width; text-field background, border (visibility/width), corner radius, placeholder/text/tint colors. If there are no named styles, infer from the app's prominent call-to-action (usually the bottom-of-screen action).

## 5. Navigation & icons → `navigationBarItem`, `images.iconBack` / `images.iconClose`

```bash
grep -rnE 'navigationBar|tintColor|toolbar(Item|TintColor)?' --include='*.swift'
find . -type d -name '*.imageset' | grep -iE 'back|arrow|chevron|close|dismiss|cross'
```
- Nav-bar / toolbar tint → `navigationBarItem` (close-button tint) / `toolbarTint`.
- Custom back / close **assets** → `images.iconBack` / `images.iconClose`. If the app uses the system back chevron, set `images.iconBack = nil` (the SDK then shows the iOS system button). Leave every other `images.*` alone.

## 6. Camera → `cameraBackground`

```bash
grep -rnE 'AVCaptureSession|CameraView|previewLayer|captureBackground' --include='*.swift' -l
```
The camera background is near-black in almost every app — note a value **only** if the app explicitly overrides the preview background to a substantially different dark tint.

## 7. Light / dark handling

```bash
grep -rnE 'preferredColorScheme|overrideUserInterfaceStyle|colorScheme' --include='*.swift'
```
Does the app follow the system, or force light/dark only?
- Both appearances → keep dynamic colors (`UIColor(named:)` or `UIColor { traits in … }`); derive the palette per variant.
- Single appearance → flat literals are acceptable; note which mode.

## 8. Framework (how to *read* tokens)

```bash
grep -rlE 'import SwiftUI|import UIKit' --include='*.swift' | head
```
SwiftUI vs UIKit only affects how you *read* tokens — the generated theme always emits `UIColor` / `UIFont`. Report which design-system shape the app uses (central module / asset catalog + extensions / inline tokens) and which tokens you extracted before Stage 2.
