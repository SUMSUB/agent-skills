/**
 * Standalone Device Intelligence as a React hook.
 *
 * Pattern mirrors a production self-hosted integration: init on mount, expose a
 * capture() the form calls on submit, destroy on unmount. DI is best-effort —
 * every path fails open so a Fisherman error never blocks the real action.
 */
import { useCallback, useEffect, useRef } from 'react'
import { init, destroy, type Fisherman } from '@sumsub/fisherman'

async function getBehaviorToken(): Promise<string> {
  const r = await fetch('/api/di/token', { method: 'POST' })
  if (!r.ok) throw new Error('token mint failed')
  // Your /api/di/token forwards Sumsub's behavior-token response, whose JWT is the
  // `token` field (see behavior-token.sh) — not `accessToken`.
  return (await r.json()).token
}

export function useDeviceIntelligence() {
  const fishermanRef = useRef<Fisherman | undefined>(undefined)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const f = await init({
          token: await getBehaviorToken(),
          baseUrl: 'https://api.sumsub.com',
          accessTokenUpdateHandler: getBehaviorToken,
          // destroy() is module-global, not instance-scoped — without the
          // cancelled guard, a stale handler from an unmounted init (React
          // StrictMode double-mount) would kill the live session.
          onError: () => {
            if (!cancelled) destroy()
          },
        })
        if (!cancelled) {
          fishermanRef.current = f
        }
      } catch (e) {
        console.error('fisherman init failed (continuing without DI)', e)
      }
    })()

    return () => {
      cancelled = true
      destroy()
      fishermanRef.current = undefined
    }
  }, [])

  /** Call on the user action. Captures device signals; fails open. */
  const capture = useCallback(async (): Promise<void> => {
    const f = fishermanRef.current
    if (!f?.isDeviceIntelligenceEnabled) return
    try {
      await f.fingerprint({})
      // Migration path only: generate a deviceBindingId, pass it to
      // fingerprint({ deviceBindingId }), return it, and forward it to the
      // backend so the confirm call can echo it. Default flow: omit entirely —
      // the behavior token's sessionId handles correlation.
    } catch (e) {
      console.error('fingerprint failed (continuing)', e) // fail open
    }
  }, [])

  return { capture }
}

// Usage:
//   const { capture } = useDeviceIntelligence()
//   async function onSubmit() {
//     await capture()
//     await fetch('/api/login', { method: 'POST', body: JSON.stringify({ /* email, password */ }) })
//   }
