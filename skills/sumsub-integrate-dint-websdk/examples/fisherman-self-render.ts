/**
 * Advanced: self-rendered / headless Device Intelligence wiring.
 *
 * ONLY needed if you drive the Sumsub verification API yourself instead of
 * embedding the prebuilt `snsWebSdk` widget. With the prebuilt widget the SDK
 * does all of this for you when "Capture device data" is enabled on the level —
 * you write nothing.
 *
 * Mirrors the lifecycle the WebSDK runs internally:
 *   - init once with the SDK access token
 *   - fingerprint on each step transition, bound to (applicantId, attemptId)
 *   - re-init on a level transition (attemptId changes)
 *   - forward the returned visitorId as X-External-Device-Fingerprint
 *
 * Usage: one FishermanSession per user / verification flow, and only one
 * active at a time — the underlying SDK is a module-level singleton, so the
 * constructor throws if a previous session was not dispose()d. Do not share
 * instances across users (e.g. in SSR or shared-worker contexts).
 */
import { init, destroy, type Fisherman } from '@sumsub/fisherman'

export class FishermanSession {
  // The underlying @sumsub/fisherman init()/destroy() are module-level
  // singletons, so two live sessions would corrupt each other's state.
  private static active = false

  private fisherman: Fisherman | undefined
  private visitorId = ''
  private lastAttemptId: string | undefined
  private disposed = false

  constructor() {
    if (FishermanSession.active) {
      throw new Error(
        'Only one FishermanSession may be active at a time — call dispose() on the previous one first',
      )
    }
    FishermanSession.active = true
  }

  private async initFisherman(accessToken: string, baseUrl: string) {
    try {
      this.fisherman = await init({
        token: accessToken,
        baseUrl, // region-specific API host, e.g. https://api.sumsub.com
        onError: () => {
          // The SDK destroys on error and re-inits after the next token refresh.
          destroy()
          this.fisherman = undefined
        },
      })
    } catch (e) {
      // log to your error tracker; DI failures must never block verification
      console.error('fisherman init failed', e)
    }
  }

  /**
   * Call on every step / page transition. Pass the CURRENT applicantId +
   * attemptId. A changed attemptId means a level transition → re-init so the
   * device binds to the new level.
   */
  async captureDevice(
    accessToken: string,
    baseUrl: string,
    applicantId: string,
    attemptId: string,
  ) {
    try {
      if (attemptId !== this.lastAttemptId) {
        this.lastAttemptId = attemptId
        this.visitorId = ''
        if (this.fisherman) {
          destroy()
          this.fisherman = undefined
        }
        await this.initFisherman(accessToken, baseUrl)
      }

      if (this.fisherman?.isDeviceIntelligenceEnabled) {
        const res = await this.fisherman.fingerprint({
          linkedId: applicantId,
          deviceBindingId: `${applicantId}-${attemptId}`,
        })
        // Guard against a stale resolve: a fingerprint() from an earlier attempt can
        // settle AFTER a newer captureDevice() advanced lastAttemptId (and destroyed
        // its session). Writing its visitorId now would bind a stale device to the
        // current attempt, so only keep it if we're still on the same attempt.
        if (attemptId === this.lastAttemptId) {
          this.visitorId = res.visitorId ?? '' // visitorId is optional in the response type
        }
      }
    } catch (e) {
      console.error('fisherman fingerprint failed', e)
    }
  }

  /** Add to the headers of the verification API calls you make after capture. */
  deviceHeaders(): Record<string, string> {
    return this.visitorId ? { 'X-External-Device-Fingerprint': this.visitorId } : {}
  }

  /** Call when the verification flow ends; frees the slot for the next session. */
  dispose() {
    // Idempotent on purpose: a stale double-dispose() must NOT clear the static
    // `active` flag a second time — by then a newer session may own it, and
    // releasing the slot under it would let two sessions run concurrently.
    // Guarding on `active` itself is not enough (the new session already set it
    // back to true); each instance must release the slot at most once.
    if (this.disposed) return
    this.disposed = true
    if (this.fisherman) {
      destroy()
      this.fisherman = undefined
    }
    this.visitorId = ''
    this.lastAttemptId = undefined
    FishermanSession.active = false
  }
}
