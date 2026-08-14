# Step 4 (Android) — Launch point

> **You're here if:** the project is Android and `SumsubIntegration.kt` is created.
> **Prereqs:** `SumsubTokenProvider` + `SumsubLauncher` exist and are under a source set (Step 3).

Wire the launch into the screen the user named in intake (Q1), **the app's own way**.
The shape is always the same and matches any architecture (MVVM / MVI / plain):

1. The user triggers verification (button tap / intent).
2. A **ViewModel** fetches the token in `viewModelScope` (calling your `SumsubTokenProvider`
   repository) and emits a **one-shot effect** carrying the token.
3. The **screen** collects that effect lifecycle-safely and calls
   `launcher.present(activity, token)` — `present` needs an `Activity`, which a ViewModel
   must not hold, so the launch itself stays in the view layer.

Inject the **same** `SumsubTokenProvider` instance (your repository) into both the
ViewModel and the `SumsubLauncher` — via the project's DI (Hilt/Koin) or a factory.
Show the call sites before writing.

## ViewModel (MVVM) — owns the async work

```kotlin
class VerificationViewModel(
    private val tokenProvider: SumsubTokenProvider,   // your repository, injected
) : ViewModel() {

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _effects = Channel<VerificationEffect>(Channel.BUFFERED)
    val effects = _effects.receiveAsFlow()

    fun onVerifyClicked() {
        viewModelScope.launch {
            _isLoading.value = true
            val token = runCatching { tokenProvider.fetchAccessToken() }.getOrNull()
            _isLoading.value = false
            _effects.send(
                if (token != null) VerificationEffect.Launch(token) else VerificationEffect.Error
            )
        }
    }
}

sealed interface VerificationEffect {
    data class Launch(val accessToken: String) : VerificationEffect
    data object Error : VerificationEffect
}
```

## Collect the effect and launch — Views (Activity / Fragment)

```kotlin
private val viewModel: VerificationViewModel by viewModels { /* your factory / DI */ }
private val launcher = SumsubLauncher(/* same SumsubTokenProvider via DI */)

override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    verifyButton.setOnClickListener { viewModel.onVerifyClicked() }

    lifecycleScope.launch {
        repeatOnLifecycle(Lifecycle.State.STARTED) {       // collect only while visible
            viewModel.effects.collect { effect ->
                when (effect) {
                    is VerificationEffect.Launch -> launcher.present(this@HomeActivity, effect.accessToken)
                    VerificationEffect.Error -> showError()
                }
            }
        }
    }
}
```

In a **Fragment**, use `viewLifecycleOwner.lifecycleScope` and pass `requireActivity()` to
`present(...)`.

## Collect the effect and launch — Jetpack Compose

```kotlin
@Composable
fun VerifyScreen(viewModel: VerificationViewModel = viewModel()) {
    val activity = LocalContext.current.findActivity()
    val launcher = remember { SumsubLauncher(/* token provider via DI */) }
    val isLoading by viewModel.isLoading.collectAsStateWithLifecycle()
    val lifecycleOwner = LocalLifecycleOwner.current

    LaunchedEffect(lifecycleOwner) {
        lifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {   // collect only while visible
            viewModel.effects.collect { effect ->
                when (effect) {
                    is VerificationEffect.Launch -> launcher.present(activity, effect.accessToken)
                    VerificationEffect.Error -> { /* show a snackbar / error state */ }
                }
            }
        }
    }

    Button(onClick = viewModel::onVerifyClicked, enabled = !isLoading) {
        Text(if (isLoading) "Starting…" else "Verify")
    }
}

// LocalContext.current is often a ContextWrapper (themed context), not the Activity —
// a bare `as Activity` cast can crash. Unwrap instead:
private tailrec fun Context.findActivity(): Activity = when (this) {
    is Activity -> this
    is ContextWrapper -> baseContext.findActivity()
    else -> error("No Activity in the context chain")
}
```

## MVI variant

Same pieces, folded into the app's MVI contract: `onVerifyClicked()` becomes an
`Intent.StartVerification` reduced in the store; `isLoading` is part of the single state;
`VerificationEffect.Launch` is a one-shot **side-effect** (not state — never keep a token
in replayable state). The view collects effects and calls `launcher.present(...)`. If the
app surfaces SDK progress, forward the launcher's `onStateChanged` / `onCompleted` into new
intents so the reducer owns it.

## Next

- Core flow is done — return to **Handoff** in [`../../SKILL.md`](../../SKILL.md).
