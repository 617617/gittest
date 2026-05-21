# issue/ — Friction & bug tracker for the dual-AI workflows

This directory captures **friction points and bugs** that either AI
(CC or Codex) encounters while running any workflow in this repo
(temporal-phase, blue-k-git-baton-testkit, or any future preset). It
is git-tracked, plain-text, and intentionally lightweight — a hosted
tracker (Linear, GitHub issues) is more powerful but adds a
permission and round-trip burden the AIs cannot absorb during
mid-flow execution.

The principle: **if something feels wrong, write it down, push it,
keep going.** Triage happens later, by whoever does the next review.

## Layout

```text
issue/
  README.md                   # this file
  open/
    <YYYY-MM-DD>__<slug>.md   # active issues
  closed/
    <YYYY-MM-DD>__<slug>.md   # resolved issues (moved here on close)
```

## Filename convention

`YYYY-MM-DD__short-slug.md`, e.g. `2026-05-21__codex-cli-skill-discovery-cache.md`.

- Date is the **filing** date (in UTC, format YYYY-MM-DD).
- Slug is kebab-case, ≤ ~50 chars, describes the issue.
- Files live under `open/` until resolved, then are `git mv`'d to
  `closed/`. Do **not** delete — closed issues are part of the
  historical record.

## File body convention

Use this template (copy and fill):

```markdown
# <one-line title>

Filed:    <YYYY-MM-DD HH:MMZ>
Reporter: <CC | Codex | both>
Workflow: <temporal-phase | bk-testkit | other>
Severity: <blocker | major | minor | nit>

## Context

<What was happening when the friction showed up? Which lane / step /
state? Cite file paths or baton states where possible.>

## What felt wrong

<What did you (the AI) notice? Where did the protocol contradict
itself, or where did the procedure leave you stuck, or where did the
tooling fight you?>

## Suggested fix

<Your best guess at the fix. May be "I don't know" -- that is a valid
entry; surfacing the friction matters more than solving it.>

## Workaround (if any)

<If you got past the friction in the moment, how? This is the
"interim" the next reader needs to know about until the fix lands.>
```

## How to file an issue (both AIs)

1. From either CC (Host A) or Codex (Host B):
2. Create `issue/open/<YYYY-MM-DD>__<slug>.md` with the template
   filled in.
3. Commit + push with message
   `issue(<workflow>): <one-line title>`.

You may file an issue **mid-Phase**. Do not interrupt the baton flow
to wait for triage — push the issue and continue the current lane.

## How to close an issue

When a fix is landed (or the issue is intentionally accepted as
won't-fix):

1. Append a `## Resolution` section to the issue file describing the
   fix and citing the commit hash(es) that addressed it.
2. `git mv issue/open/<file>.md issue/closed/<file>.md`.
3. Commit + push with message `issue(close): <slug>`.

## Severity guide

- **blocker** — the workflow cannot proceed without intervention.
- **major** — the workflow proceeds but produces wrong / unsafe
  artifacts, or the same friction recurs every Phase.
- **minor** — the workflow proceeds correctly but is annoying / slow
  / error-prone in some recoverable way.
- **nit** — cosmetic, wording, or strictly preference-level.

## What this directory is NOT

- It is **not** a substitute for fixing bugs in `workflows/` or
  `scripts/`. File an issue, but if the fix is short and obvious, fix
  it in the same commit too.
- It is **not** a chat log. Each issue is one bounded friction with a
  start, body, and resolution.
- It is **not** for product / roadmap planning. Roadmap lives in
  source-document anchors and per-Phase `NextPhasePlan` blocks.

## Visibility to AIs

Both `temporal-phase-codex-sync` (on Codex side) and
`/temporal-phase-watch` + `/temporal-phase-start` (on CC side) may
optionally surface "N open issues" as part of their status block, but
do not block execution on open issues. Open issues are advisory; only
explicitly blocking issues (severity = `blocker` that has been
escalated) gate progress.
