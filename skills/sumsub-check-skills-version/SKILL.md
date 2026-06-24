---
name: sumsub-check-skills-version
description: Verify that the locally installed Sumsub agent-skills package is compatible with the published version before doing any Sumsub work. TRIGGER at the start of any task that touches Sumsub — Sumsub Dev MCP tools (mcp__Sumsub_Dev__*), KYC/AML workflows, applicants, checks, transactions, verification levels, verification links, questionnaires, fraud network, VASP lists, or anything Sumsub-related — so the user is warned before a stale skills package produces wrong results. Also use this skill when the user explicitly asks "are my Sumsub skills up to date / current", "is there a newer version of the Sumsub skills", or similar. Skip the actual update (the user runs `npx skills add SumSubstance/agent-skills --all` themselves) and skip any other Sumsub API or entity task — those have their own skills.
allowed-tools: Bash
---

# Sumsub: Check Skills Version

Detects version drift between the locally installed `@sumsub/agent-skills` package and the canonical version published at `https://api.sumsub.com/llms.txt`, so that out-of-date skills don't silently produce stale or incorrect Sumsub behavior.

**This skill's one user-visible deliverable is the `headsup` line.** Running `check_version.sh` only *computes* it; the skill has not done its job until that line appears in your reply to the user. Treat emitting it exactly like emitting the result of any other tool call — not as an optional courtesy.

## Two-phase protocol (this is how the heads-up actually lands)

Only your FINAL reply reaches the user, and you surface what is freshest in your context when you compose it. If you compute the heads-up first and then do a task, the task result becomes the freshest thing and the heads-up gets dropped. To prevent that, split the work into two phases:

**Phase 1 — compute the verdict (before the task).** Run `check_version.sh`. It computes the verdict and caches the rendered heads-up. Note whether a `headsup=` line was printed; do **not** write anything to the user yet.

**Phase 2 — render LAST, then compose.** Carry out the user's actual Sumsub task. Then, as your **final action before writing the reply** — after the task, after every other tool call — run:

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/render_headsup.sh
```

Treat its stdout exactly like the result of any tool you must surface: if it prints a blockquote, that blockquote is the **first line** of your reply, verbatim, rendered as markdown; then the task answer follows. If it prints nothing, say nothing about the version. The render step is deliberately your *last* tool call so the heads-up is the freshest thing in context when you compose — that is what makes it survive into the final reply.

For an explicit "are my skills up to date?" question there is no other task, so Phase 1 already leaves the heads-up as the freshest output — just lead your reply with it; the Phase-2 render is a no-op you can skip.

## When NOT to run the check

Do **not** invoke this skill, run `check_version.sh`, or mention Sumsub-skills version drift when:

- The user asks about **non-Sumsub** tools or vendors (Onfido, Persona, Stripe, etc.) — even if the topic is KYC.
- The user asks about **generic package freshness** (`npm outdated`, `pip list --outdated`, etc.) for their own project — that is unrelated to the `@sumsub/agent-skills` npm bundle.
- The user explicitly says they are **not** asking about Sumsub.

Never append a "by the way, want me to check your Sumsub skills?" sidenote on unrelated answers.

**Anti-pattern (npm outdated):** ❌ *"Want me to run sumsub-check-skills-version instead?"* or mentioning `agent-skills-version` / `llms.txt` — the user's npm question is complete once you've summarized `npm outdated`. Stop there.

**Anti-pattern (vendor comparison):** ❌ Mentioning Sumsub skills version while comparing Onfido vs Persona. Answer only what was asked.

## When to run the check

Run it **once per session**, before the first Sumsub-related action. Concretely:

- Before calling any `mcp__Sumsub_Dev__*` tool for the first time in this session.
- Before walking the user through any Sumsub workflow (creating an applicant, requesting a check, reading a transaction, building a verification link, etc.).
- When the user explicitly asks whether their Sumsub skills are up to date.

**Do not re-run the network check** (`check_version.sh`) within the same session — repeated `curl`s add latency without value. The Phase-2 `render_headsup.sh` step does **not** re-check; it only re-emits the cached verdict, and it is mandatory every time you produce a Sumsub answer in a session that found drift.

The check is non-blocking only in the sense that you do **not** pause or wait for the user before continuing — it does **not** mean the heads-up is optional or skippable. Follow the two-phase protocol above, then proceed with the user's task in the same reply.

## How to run the check

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/check_version.sh
```

It prints up to four `key=value` lines on stdout:

```
local=1.0.1
remote=1.0.2
status=PATCH_BEHIND
headsup=> ⚠️ **Sumsub skills update available** — you're on **1.0.1**, latest is **1.0.2** (patch). Run `npx skills add SumSubstance/agent-skills --all` to update.
```

- `local` — installed version (baked into `references/version.txt` at publish time).
- `remote` — canonical version parsed from the `agent-skills-version:` line of the canonical `llms.txt`.
- `status` — the verdict (see below).
- `headsup` — present only for non-silent verdicts; the **exact** markdown line to surface. Don't emit it from here — Phase 1 just caches it; the Phase-2 `render_headsup.sh` step re-prints it (as a clean blockquote) when you're ready to compose. Never echo the `local=`/`remote=`/`status=`/`headsup=` keys themselves.

The remote URL is `https://api.sumsub.com/llms.txt`. No credentials needed — it's a public static file. Override with the `SUMSUB_VERSION_URL` environment variable for testing.

## How to handle each verdict

The `headsup` text is produced once, by Phase 1, and re-emitted by Phase 2's `render_headsup.sh`; you never hand-write it. Whatever the render step prints becomes the first line of your reply, verbatim. If it prints nothing (silent verdict), say nothing about the version. The heads-up is shown **once per session**.

For reference, what each verdict means:

| `status` | `headsup` present? | Meaning |
|---|---|---|
| `UP_TO_DATE` | no | Installed version matches the published one — stay silent. |
| `PATCH_BEHIND` | yes | A patch release is available — surface the line, then proceed. |
| `MINOR_BEHIND` | yes | A minor release is available — surface the line, then proceed. |
| `MAJOR_BEHIND` | yes | Significantly behind; behavior may have changed — surface the line, then proceed. |
| `AHEAD` | yes | Local is newer than published (likely a dev build) — surface the line, then proceed. |
| `UNKNOWN` | no | Remote unreachable or unparseable — stay silent, never block the user. |

Important: never block the user's request because of the verdict, and never show the heads-up more than once in the same session — if you've already shown it in this conversation, don't repeat it.

### Worked example — implicit trigger

The most common case: the check runs as a background step before some other Sumsub task, verdict is non-`UP_TO_DATE`. Order of operations:

1. **Phase 1** — run `check_version.sh` (verdict `PATCH_BEHIND`, local `1.0.0`, remote `1.0.1`; heads-up cached). Write nothing yet.
2. Do the task — look up the transaction.
3. **Phase 2** — run `render_headsup.sh` as your last action; it prints the blockquote.
4. Compose the reply: blockquote first, task answer after.

User: *"look up sumsub transaction 65a3… — what risk score and which rules fired?"*

Your reply:

> ⚠️ **Sumsub skills update available** — you're on **1.0.0**, latest is **1.0.1** (patch). Run `npx skills add SumSubstance/agent-skills --all` to update.

Transaction `65a3…`: risk score 78 (RED), 2 rules fired — …answer the actual request here…

## Notes

- The check needs no API credentials — the canonical `llms.txt` is a public static file.
- The local version lives in `references/version.txt` and is bumped together with `public/package.json` and `public/skills.json` on every release.
- If the canonical source moves (host change, or migration to a different file shape), set `SUMSUB_VERSION_URL` to the new location; the script accepts an `agent-skills-version:` line (preferred), a JSON `"version"` field, or a bare `version:` line.
