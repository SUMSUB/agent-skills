# Step 3 (Android) — Integration code

> **You're here if:** the project is Android — this is the core of the integration.
> **Prereqs:** framework installed (Step 2). No permissions step — the SDK declares and requests its own.

Create a new Kotlin file holding the reusable Sumsub glue, named `SumsubIntegration.kt`
(template: [`../examples/SumsubIntegration.kt`](../examples/SumsubIntegration.kt)). It defines two
small pieces and **owns no threading, lifecycle, or UI** — that stays in the host's
architecture (Step 4):

1. **`SumsubTokenProvider`** — a `fun interface` with `suspend fun fetchAccessToken(): String`.
   This is the seam into the app's own architecture: the host implements it in its
   **data/domain layer** (a repository, a use-case, a Retrofit/Ktor service) to return a
   fresh backend-signed access token. Because it's `suspend`, it composes with the app's
   coroutines and dispatchers — no callbacks, no manual threading.
2. **`SumsubLauncher(tokenProvider)`** — the only Sumsub-specific class. `present(activity, token)`
   builds the SDK via `SNSMobileSDK.Builder(activity)`, wires the handlers, and calls
   `launch()` (the SDK starts its own Activity). It deliberately does **not** fetch the
   initial token or hold a `CoroutineScope` — the host's `viewModelScope` /
   `lifecycleScope` does, so cancellation tracks the host lifecycle.

**Fit it to the host architecture (don't reinvent it).** From the Step 1 scan you know
whether the app is MVVM, MVI, etc. Place `SumsubIntegration.kt` in a sensible package, then in
Step 4 wire it the app's own way — the `SumsubTokenProvider` is implemented by the app's
repository (inject it with whatever DI the project uses: Hilt, Koin, or a manual
factory), and the launch is triggered from a ViewModel. Name the file in the change-set
approval before creating it:

> "I'll create `SumsubIntegration.kt` (`SumsubTokenProvider` + `SumsubLauncher`) in `<package>`,
> and wire `SumsubTokenProvider` to your `<repository>` — apply?"

**No separate "wire into target" step.** Unlike iOS (pbxproj), Gradle compiles any `.kt`
under a source set (`src/main/java|kotlin/...`) automatically.

Do **not** edit existing app code beyond the launch site the user named in intake (Q1)
and the token-provider wiring. Never touch unrelated files.

## The required token-expiration handler

The `TokenExpirationHandler` is **required** — without it the flow hangs when the token
expires mid-session. The launcher implements it for you by calling the same
`SumsubTokenProvider`.

> **Gotcha — the SDK callback is SYNCHRONOUS.** `onTokenExpired(): String?` must **return**
> the fresh token, on a **background thread**, and the SDK blocks on the return value. The
> template bridges the `suspend` provider with `runBlocking { tokenProvider.fetchAccessToken() }`
> — this is the **one** place `runBlocking` is correct (already off the main thread, and a
> value must be returned). Do not try to make it async or hop to the main thread. Returning
> `null` aborts the session.

## Optional handlers

Registered on the builder via `withHandlers(...)` (or the dedicated `with*Handler`). Forward
them to your state holder (ViewModel `StateFlow` / MVI state) if the UI needs progress:

| Handler          | Signature                                                    | Fires when                                         |
|------------------|--------------------------------------------------------------|----------------------------------------------------|
| `onStateChanged` | `(SNSSDKState, SNSSDKState) -> Unit` *(newState, prevState)* | SDK state changes — track progress                 |
| `onCompleted`    | `(SNSCompletionResult, SNSSDKState) -> Unit`                 | Flow closes — UX only, **not** the source of truth |
| `onError`        | `(SNSException) -> Unit`                                     | SDK throws                                         |

`SNSCompletionResult` is `SuccessTermination` or `AbnormalTermination(exception)`.
Key `SNSSDKState` values: `Ready`, `Initial`, `Incomplete`, `Pending`, `Approved`,
`TemporarilyDeclined`, `FinallyRejected`, and the sealed `Failed.*` family
(`Failed.Unauthorized`, `Failed.NetworkError`, …).

## Token source (no backend yet)

`SumsubTokenProvider` is where the real backend call goes. If the user has no backend
endpoint yet, implement it to return a hardcoded sandbox token for an initial end-to-end
test, and say so explicitly:

> "I've wired `SumsubTokenProvider` to your repository. Until that endpoint exists, have it
> return a hardcoded sandbox access token so you can see the flow; replace it with the real
> `suspend` backend call before shipping."

## Next

- Wire the launch point → [`4-launch.md`](4-launch.md)
