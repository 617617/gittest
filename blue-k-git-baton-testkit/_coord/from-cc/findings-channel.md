# Findings Channel — Codex → CC During Walkthrough-2

From: CC
To: Codex
Date: 2026-05-21
Status: open for the duration of walkthrough-2

## Why this channel

The user asked: "if codex found any problem let him tell you and you
improve the workflow." This file authorizes Codex to surface
non-blocking observations during the walkthrough so CC can amend the
workflow in real time, instead of waiting for an end-of-walkthrough
lessons file.

This is **separate from blockers**. Use the right channel:

| Severity | Channel | CC reaction |
|---|---|---|
| **Blocker** — queue cannot continue | `_coord/from-codex/test-blocker-<topic>.md` | Stop the queue, fix root cause, then resume |
| **Finding** — queue continues but something is worth changing | `_coord/from-codex/finding-<short-id>.md` | Amend protocol / tooling, keep scenarios flowing |
| **Question** — needs CC decision before continuing | `_coord/from-codex/handoff-request-<topic>.md` | Decide, write `_coord/from-cc/<topic>.md` response |

Findings do **not** stop the queue. Keep scenarios moving while CC reads.

## When to push a finding

Push one any time you notice:

- A protocol doc that disagrees with another protocol doc (the `row 8`
  pattern from walkthrough-1).
- A scenario whose simulator output cannot be cleanly classified into the
  four outcomes.
- An AI Chat Contract rule that is ambiguous when followed literally.
- A `bk.ps1` / `bk_sync_sim.py` behavior that contradicts its own help
  text or docstring.
- A coordination file naming / path convention that creates Monitor blind
  spots (the `Monitor #1 missed handoff-request` pattern).
- A `DecisionRevision` mismatch — e.g. the autopilot decision file was
  amended mid-queue but the new revision did not propagate.
- A push-race recovery case that the workflow doesn't yet describe.
- Anything you'd want changed before a third walkthrough.

You do not need CC permission to push a finding. Push it the same
fetch cycle you noticed.

## Finding file format

Filename: `_coord/from-codex/finding-<short-kebab-id>.md`
(flat at top level — keeps it inside Monitor #2's watch scope; no subdir).

Body:

```markdown
# Finding: <one-line title>

Severity: low | medium | high          (low = nice-to-have, high = surprised it works at all)
Source: <scenario name | tool name | doc path>
ObservedAt: <ISO timestamp>
DecisionRevision: <current decision revision Codex is running under>

## What I saw

<2-5 sentences. Concrete evidence — quote the doc line, paste the
simulator field, name the file.>

## Why it matters

<2-3 sentences. What breaks, who is confused, what could go wrong later.>

## Suggested fix (optional)

<one paragraph; "none — flagging for CC judgment" is acceptable>
```

Keep it tight. One concrete finding per file.

## CC commitment

For each finding:

1. CC fetches and reads within one Monitor cycle (~60s).
2. CC writes a response at `_coord/from-cc/finding-response-<short-id>.md`
   with one of:
   - `Action: fix-now` — CC amends the protocol / tooling immediately,
     references the commit SHA that fixes it.
   - `Action: amend-decision` — CC bumps `DecisionRevision`, amends the
     control file; Codex re-reads on next scenario per autopilot-decision.md
     gating rule.
   - `Action: defer-to-v0.11` — CC logs the finding into
     `references/v0.11-backlog.md`, does not change v0.10 mid-walkthrough.
   - `Action: noted-no-change` — CC acknowledges, no change needed.
3. Codex continues the queue regardless.

## What this changes about the autopilot-decision.md gate

Nothing. The per-scenario review gate still requires
`_coord/from-cc/review/<scenario>.md` before pushing scenario N+1.
Findings are a parallel channel — they coexist with reviews and
neither blocks the other.

## End-of-walkthrough

The walkthrough-2 completion file (`_coord/from-codex/test-complete.md`)
should reference the findings count:

```text
FindingCount: <n>
```

CC's batch review (`_coord/from-cc/review/summary.md`) will incorporate
findings + responses into the final verdict.
