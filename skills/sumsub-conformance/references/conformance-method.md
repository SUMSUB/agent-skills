# Conformance method — how the trace works and where to be careful

> **Artifacts MUST live beside the source regulation file**, named from its stem:
> `<stem>_regulations.json` (requirements), `<stem>_config.json` (resolved graph), `<stem>_report.md`
> (report). Derive the paths with `scripts/artifact_paths.py` (`$REQUIREMENTS`/`$CONFIG`/`$REPORT`) — never
> the cwd or improvised names. See SKILL.md → Procedure.

## The five steps

1. **Ingest** (agent, judgment). Read the regulation. **Default: Read the document with the Read tool —
   it reads PDFs natively (renders pages + extracts text), no library install required.** For a PDF over
   ~10 pages, Read it in page ranges (`pages` parameter, ≤20 pages per call). Visual reading is equal or
   better than a text extractor — it keeps tables/headings/layout that flat extraction drops.
   - *Optional accelerators (only if already installed — never block on a `pip install`, never fail if
     absent):*
     - **`pypdf`/`pdftotext`** — for a long, text-heavy PDF, grabs all the text in one shot instead of
       several Read calls. If the import fails, just Read the PDF directly (this is the observed,
       correct fallback). Most regulation/policy PDFs are text-based (e.g. the FIU-India guideline).
     - **`render_regulation.py`** (needs PyMuPDF) — pre-renders pages to PNG with explicit DPI for a
       scanned/image-only PDF. Rarely needed: the Read tool already renders PDF pages itself; reach for
       it only if native PDF reading struggles on a specific file (e.g. the CFD questionnaire — 27
       pages, ~483 extractable chars). If PyMuPDF is absent, Read the PDF directly.
   Extract requirements into **`$REQUIREMENTS`** (the `<stem>_regulations.json`; schema in
   [`requirements-schema.md`](requirements-schema.md)).
   **Show the extracted requirements to the user and get confirmation before tracing** — extraction
   is the highest-risk judgment step.
2. **Resolve** (deterministic). `resolve_graph.sh <levelNameOrId> > "$CONFIG"`: the level,
   referenced questionnaires **with per-option scores**, PoA/cross-check presets, the auto-found
   workflow (nodes/edges/conditions), and entitlements (`allowedChecks` keys).
3. **Map** (agent, judgment). **Inspect the graph with `graph_summary.py` first** (it prints
   questionnaire `[section]/[item]` indices + scores, docSets, fields, geo, workflow — do not hand-iterate
   the graph JSON; see the shape table in [`requirements-schema.md`](requirements-schema.md)). Then for
   each requirement pick the right `type` and fill its `match` — **not everything is a questionnaire
   question.** Map to whichever config dimension the requirement is about
   (questionnaire item, docSet + doc types, `data-field`, `country-eligibility`, `liveness`,
   `entitlement`), or set a discriminating `enforcementSignal` for `screening`/`routing-outcome`. The
   per-type `match` shapes are tabulated in [`requirements-schema.md`](requirements-schema.md). This is
   the one semantic step — be conservative; if unsure a thing exists, leave `match: null` (→ MISSING)
   rather than guess.
4. **Trace** (deterministic). `trace.py --requirements "$REQUIREMENTS" --graph "$CONFIG"` →
   findings bucketed MISSING / SCORING-MISMATCH / COLLECTED-NOT-ENFORCED / NOT-CONFIG-REPRESENTABLE
   / CONFORMANT, each with evidence + a `basis` (deterministic vs judgment).
5. **Report** (deterministic format). Render the trace with `report.py` — **do not hand-format**:
   `trace.py --requirements "$REQUIREMENTS" --graph "$CONFIG" | report.py > "$REPORT"` produces the
   canonical Markdown (headline status, fixed bucket-count table, findings grouped in fixed order with
   evidence + `basis`, fixed caveats footer). Present it verbatim. Two canonical formats: the `trace.py`
   JSON (for tooling) and the `report.py` Markdown (for humans). Append the optional hygiene sub-pass
   output below it.

## Guardrails (these exist because we hit the failure modes live)

- **Use the scripts; don't hand-roll the deterministic steps.** Resolve the graph ONLY via
  `resolve_graph.sh` (no direct `/resources/...` calls, manual level-listing, or HTTP-trailer
  stripping). Derive the bucket verdict ONLY from `trace.py`/`report.py` — never read the
  workflow/questionnaire JSON by eye and decide "enforced/not enforced" yourself (re-introduces
  variance + hallucination). If a script already ran, trust its output — don't re-verify with manual
  API calls. Agent judgment is for ingest + map only.
- **Separate fact from judgment.** Score compare + enforcement search are deterministic (cite them).
  Requirement extraction + question mapping are judgment (label them, get sign-off). Never present a
  judgment as a verified finding.
- **No reverse findings.** The trace only walks requirements → deployment. It never flags a deployed
  question as "extraneous" — that avoids the false-positive class (we nearly flagged a real,
  in-spec "How did you discover us?" question as extra). If you want to report extra deployed
  questions, do it as an explicit, separate, clearly-advisory note.
- **Discriminating enforcement signals.** See [`requirements-schema.md`](requirements-schema.md) — a
  generic token (`country`) matches catch-all edges and produces false CONFORMANT. Use a specific
  literal/threshold token.
- **Confidence/advisory.** The whole report is advisory and needs a human sign-off. State it.

## What is NOT config-representable (always bucket, never fail)

These outcomes live in the SDK / broker platform / CRM and cannot be verified from Sumsub config —
mark them `enforceable: sdk|platform`:

- Mandatory disclosure pop-ups (e.g. the CFD 25%/10% restriction notice, risk-acknowledgement,
  rejection letter, Cancel/Proceed + CRM timestamp).
- Account-state outcomes: Demo account creation, Live read-only mode, Live blocking.
- Anything keyed on UI/email/CRM rather than the applicant/level/workflow graph.

## Honest scope

This is a **conformance gap assistant**, not a compliance guarantee. It deterministically verifies
the config-representable parts (presence, scoring, routing enforcement) and **honestly delimits the
rest** (semantic intent = judgment; SDK/platform outcomes = out of scope). The optional hygiene
sub-pass (the bundled `lint_config.py` linter) catches silent misconfigurations alongside.
