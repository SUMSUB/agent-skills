# Sumsub ID Connect — scopes, library options & response shapes

## OIDC discovery (well-known)

Authoritative metadata: <https://id.sumsub.com/.well-known/openid-configuration>.

| Field | Value |
|---|---|
| `issuer` | `https://id.sumsub.com/` |
| `authorization_endpoint` | `https://id.sumsub.com/api/snsId/oauth/authorize` |
| `token_endpoint` (standard OIDC) | `https://id.sumsub.com/api/snsId/oauth/token` — accepts `client_secret_basic` / `client_secret_post` |
| `userinfo_endpoint` | `https://id.sumsub.com/api/snsId/oauth/userInfo` — returns OIDC claims with the access_token |
| `jwks_uri` | `https://id.sumsub.com/.well-known/jwks.json` — RSA public keys for `id_token` validation |
| `id_token_signing_alg_values_supported` | `RS256` only |
| `code_challenge_methods_supported` | `S256` only (must SHA-256 + base64url; no `plain`) |
| `response_types_supported` | `code` only |
| `grant_types_supported` | `authorization_code`, `refresh_token` |
| `scopes_supported` | `openid`, `email`, `name`, `profile`, `share`, `offline_access` |

The Sumsub-specific App-Token-authenticated alternative to the standard token
endpoint is `POST https://api.sumsub.com/resources/snsId/api/connect/token`
(HMAC-signed). Either route accepts the same `authorization_code` from any of
the four integration methods in Stage 1.

## Scopes (`permissions` array in the library, `scope` string in raw OIDC)

| Scope | Purpose | Effect |
|---|---|---|
| `openid` | Mandatory for OIDC. | Server returns an `id_token` JWT alongside `access_token`. |
| `email` | Verified email. | `email` claim available on `/userInfo` and in `id_token`. |
| `name` | Verified name. | `given_name`, `family_name`, `name` claims. |
| `profile` | Verified profile claims. | `created_at` and additional profile data per OIDC standard. |
| `share` | **Required to use the share-token / reuse flow.** | Lets the integrator call `POST /resources/accessTokens/sumsubIdShareToken`. |
| `offline_access` | Long-lived session. | Server returns a `refresh_token`. Without this, the access_token cannot be refreshed — the user has to re-authorise. |

`scopes_supported` from well-known is authoritative; this table is a
shorthand. Request only what you actually consume — extra scopes trigger
extra checks in the user-facing flow.

## `@sumsub/id-connect` — `createButton(options)` parameters

The library handles the OAuth-2.0 + PKCE dance for you. If you omit
`codeChallenge`, the library generates a verifier internally and persists it
in `sessionStorage`; supply your own only if you want full control over PKCE
lifecycle.

| Name | Type | Required | Description |
|---|---|---|---|
| `clientId` | string | yes | OIDC client id from Dashboard → Dev Space → OIDC Settings. |
| `permissions` | string[] | yes | List of OIDC scopes — `['openid', 'share', 'name']` is the common starter set. |
| `container` | HTMLElement | yes | DOM element that the branded button is mounted into. |
| `onSuccess` | `(resp) => void` | yes | Receives `{ code, state }`. The `code` is short-lived — exchange immediately. |
| `onError` | `(err) => void` | no | Receives error details if the flow fails. |
| `onLoading` | `(isLoading: boolean) => void` | no | Toggles while the popup is loading. |
| `className` | string | no | CSS class applied to the rendered button — use for style overrides. |
| `text` | string | no | Button label (default: `connect`). |
| `loginHint` | string | no | Email prefilled in the sign-in step. |
| `state` | string | no | OAuth `state` value — CSRF nonce, echoed back in `onSuccess`. |
| `codeChallenge` | string | no | PKCE challenge if you generate the verifier yourself; otherwise the library handles PKCE. |
| `baseUrl` | string | no | Override the Sumsub base URL. Usually omit. |

## `@sumsub/id-connect` — `openModal(options)` parameters

Same library, same PKCE behaviour — no `container`/`className`/`text`
because there is no rendered button.

| Name | Type | Required | Description |
|---|---|---|---|
| `clientId` | string | yes | OIDC client id. |
| `permissions` | string[] | yes | List of OIDC scopes. |
| `onSuccess` | `(resp) => void` | yes | Receives `{ code, state }`. |
| `onError` | `(err) => void` | no | Error details. |
| `onLoading` | `(isLoading: boolean) => void` | no | Use to toggle a spinner on your own trigger. |
| `loginHint` | string | no | Prefill email. |
| `state` | string | no | CSRF nonce. |
| `codeChallenge` | string | no | PKCE challenge — see `createButton` notes. |
| `baseUrl` | string | no | Override Sumsub base URL. |

## `AuthorizeResponse` shape

```ts
type AuthorizeResponse = {
  code?: string;   // short-lived authorization code — exchange on backend immediately
  state?: string;  // mirrors what you passed in (or library-generated)
};
```

## Raw OIDC authorize URL (Method 4 — no library)

```
https://id.sumsub.com/api/snsId/oauth/authorize
  ?client_id=<your-client-id>
  &response_type=code
  &redirect_uri=<exact match of an allowlisted URI in OIDC Settings>
  &scope=openid+share+name
  &state=<random CSRF nonce>
  &code_challenge=<base64url(SHA256(code_verifier))>
  &code_challenge_method=S256
  &login_hint=<optional email>
```

Snake-case OIDC-standard parameter names — even though the docs page (and the
JS library) use camelCase variants (`clientId`, `responseType`, `loginHint`),
the actual authorize endpoint accepts the OIDC-standard snake-case form.
**Method 4 requires you to generate the `code_verifier` yourself**, derive the
challenge, store the verifier (sessionStorage is the conventional choice),
and forward it to your backend after the callback so the token exchange can
pass it as `codeVerifier`. Without that, `/connect/token` returns
`401 Invalid code` regardless of how good your `code` is.

## Token-endpoint response shape

```json
{
  "access_token":  "snd-id-con-a-...",
  "refresh_token": "snd-id-con-r-...",   // only if `offline_access` was granted
  "id_token":      "eyJhbGciOi...",       // only if `openid` was granted (RS256-signed)
  "token_type":    "Bearer",
  "expires_in":    86400                  // 24h
}
```

- `access_token` lifespan: 24 hours.
- `refresh_token` (when present): server-side only, encrypted at rest, never
  expose to the browser.
- `id_token`: standard OIDC JWT signed with **RS256**. Validate against the
  RSA public keys at `https://id.sumsub.com/.well-known/jwks.json`. Use a
  mature library (`jose`, `pyjwt`, `jjwt`) — don't hand-roll signature
  verification.

## Share-token response shape

```json
{
  "token":          "_act-snsId-...",       // pass to /reuse
  "forClientId":    "<echoed>",
  "sharingAllowed": true                    // false → mint a share link first
}
```

If `sharingAllowed: false`, redirect via `POST /resources/snsId/oauth/shareLink`:

```
Authorization: Bearer <sumsubIdConnectToken>
{
  "redirectUri":  "<allowlisted callback>",
  "forClientId":  "<same recipient clientId>",
  "displayMode":  "page",
  "state":        "<csrf nonce>"
}
```

Response: `{ "link": "https://id.sumsub.com/share/<id>" }` — expires in 5
minutes. On consent, Sumsub redirects to `redirectUri` with a signed JWT in
`?token=…` exposing `sharingAllowed: true`.

## Reuse endpoint result

`POST /resources/api/reusableIdentity/reuse` returns an `ApplicantPublicDto`
with `id`, `createdAt`, `key`, `clientId`, and (when available)
`review.reviewStatus`. The applicant is created in *your* workspace using
documents copied from Sumsub ID; the recipient level still runs its
configured checks against them.

Always call `/reuse/preview` (GET, same query parameters) first — it returns
the same DTO shape without creating anything, so you catch
`reusable-kyc-not-compatible-doc-type` (errorCode `10513`) before committing.

## Common error responses

| HTTP | description / errorCode | Cause |
|---|---|---|
| 404 | `Invalid clientId: client_id` | Sumsub ID Connect is not enabled for this `clientId`. Run `scripts/preflight.sh` to confirm, then email Sumsub support. |
| 401 | `Invalid code` | Three common causes: PKCE mismatch (verifier doesn't hash to the challenge sent at authorize), code already used (single-use — refreshing the callback page double-fires), or code expired (short TTL — exchange immediately). |
| 401 | `invalid_client` / `Client authentication failed` | Standard OIDC token endpoint rejected the `client_secret_basic` credentials. Re-check `client_id` and `client_secret`. The secret is shown once at OIDC client creation — if lost, regenerate (which breaks existing integrations). |
| 400 | `invalid_redirect_uri` / `Invalid redirect uri` | The `redirect_uri` sent on `/authorize` (or `/shareLink`) isn't in the OIDC client's allowlist. Sumsub matches byte-for-byte; add the exact string to Dev Space → OIDC Settings. |
| 400 | `'forClientId' and 'sumsubIdConnectToken' must be provided…` | Missing field on `/resources/accessTokens/sumsubIdShareToken`. |

Full `reusable-kyc-*` error catalog (errorCodes `10501`–`10521`, ~20 entries
covering partner setup, share-token validity, donor state, doc compatibility,
freshness, capture settings, and contact-match) — see Stage 4 → **Reuse error
codes** in [`../SKILL.md`](../SKILL.md). Kept there as the single source of
truth to avoid drift.
