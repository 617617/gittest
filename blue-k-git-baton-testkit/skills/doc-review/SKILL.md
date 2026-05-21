---
name: doc-review
description: >-
  Pre-execution review of plan / EXECUTE.md / scope.md artifacts produced by
  traceable-plan or any structured planning workflow. Forces convergence so
  plan iteration terminates and execution starts. Detects BDUF,
  Design-by-Committee, and Iteration-Fatigue anti-patterns. Uses a 3-round
  default rhythm, atomic Definition-of-Ready checklist, and termination protocol
  that produces REVIEW_TERMINATION.md.
  TRIGGER when: user asks "review the plan", "audit the EXECUTE doc", "is this
  plan ready"; or when a traceable plan directory, such as `.claude/plan/PLAN_NAME/`
  or `docs/mian-k/PACKAGE/`, exists with EXECUTE.md but no executed commits;
  or when a plan has been iterated 2+ times without execution; or when a plan
  has CONTRACT_LOCK / NO-GO / BLOCKED status that has not cleared.
  DO NOT TRIGGER when: the plan already has commits referencing it (use
  traceable-review instead); the user is asking to GENERATE a plan (use
  traceable-plan or blueprint); the user is asking to review code, not docs.
---

# Doc Review

Pre-execution review of `EXECUTE.md` and surrounding plan artifacts. Mission:
force convergence so plan review stops and execution starts.

Do not confuse this with `traceable-review`: this skill reviews documents before
code is written; `traceable-review` reviews commits after code is written.

## Dirty Worktree Checkpoint Gate

Whenever this skill or its calling protocol requires a clean worktree, first
inspect `git status --short --branch` in the repository containing the reviewed
plan directory. If the worktree is dirty, create exactly one full-repository
checkpoint commit before continuing:

```powershell
git add -A
git commit -m "chore(worktree): checkpoint before doc-review"
git status --short --branch
```

Continue only if the follow-up status is clean. If the commit fails or the
worktree remains dirty, stop with:

```text
DOC_REVIEW_BLOCKED_DIRTY_AFTER_CHECKPOINT
```

Do not treat a dirty worktree as an immediate blocker until this checkpoint
attempt has been made.

## Output Language

All artifacts written by this skill must be English-only with ASCII punctuation.
This includes review findings, severity labels, `REVIEW_TERMINATION.md`, notes
appended to `audit_trace.md`, and inline comments in plan files. Conversation
with the user may use the user's language.

## Activation

Use this skill when:

- A plan directory exists with `EXECUTE.md` but no executed commits yet.
- The user asks "review the plan", "audit the EXECUTE doc", or "is this plan ready".
- A plan has iterated 2+ times without execution.
- A plan has stale `CONTRACT_LOCK`, `NO-GO`, or `BLOCKED` status.

Before reviewing, confirm the plan exists and has not already been executed:

```bash
ls <plan-dir>/EXECUTE.md 2>/dev/null || ls <plan-dir>/**/EXECUTE.md
git log --all --grep="<plan-name>" --oneline | head -5
```

If commits already reference this plan, switch to `traceable-review`.

## Core Rule

Review for executable readiness, not perfection. After R3 with no BLOCKING
items, approve. Further plan review is forbidden until execution produces a
commit.

Only these outputs are valid:

1. `APPROVE`: plan is ready; execution starts.
2. `FIX-AND-RERUN`: 1-2 BLOCKING items; fix them and rerun only the same round.
3. `SPLIT`: plan is too large to converge; approve or replan the smallest viable packet.
4. `TERMINATE`: iteration fatigue has set in; run the termination protocol.

There is no "continue iterating" verdict.

## Definition Of Ready

A plan is READY only when all 9 checks are true:

- [ ] Single owner: one person/agent owns execution.
- [ ] Smallest packet identified: at least one packet has Goal, Allowed Files,
  Steps, and Acceptance Checks small enough that the executor will read it. Use
  about 150 lines as a guide, not a hard cap.
- [ ] Walking skeleton present: the smallest packet can ship end-to-end in one
  commit, including code, tests, and evidence.
- [ ] Allowed Files exhaustive: every file the executor may touch is listed.
- [ ] Acceptance Checks tool-checkable: each check can be verified by command.
- [ ] Stop Conditions concrete: at least 3 explicit conditions halt execution.
- [ ] Read Anchors verified: every cited `file:line`, function, or symbol exists
  at HEAD.
- [ ] Constitution locked: constraint docs such as `AGENTS.md`, `CLAUDE.md`, or
  `CONTRACT_LOCK.md` are frozen for this plan; new constraints are amendments.
- [ ] Global Context populated: `EXECUTE.md` has substantive Plan-level Goal,
  Architecture Invariant, Stage Sequence Position, System-level Non-Goals, and
  Plan-level Accept.

Decision:

- 9/9: `APPROVE`.
- 8/9: one fix round, then approve if the missing item is fixed.
- 7/9 or below: structural gap; enter R1 or `SPLIT`.

## Severity

Classify every finding into exactly one bucket:

| Severity | Meaning | Action |
|---|---|---|
| `BLOCKING` | Allowed Files misses a critical file, an Acceptance Check is not tool-checkable, a Read Anchor does not exist, or execution would fail before producing evidence. | Fix before execution. |
| `IMPROVEMENT` | Plan is executable but could be clearer or better organized. | Record as deferred; do not block. |
| `FOLLOW-UP` | Real concern answerable only by running code. | Convert to an execution evidence question. |

Only `BLOCKING` can hold execution.

Do not treat naming polish, cross-reference completeness, wording, optional
extra tests, speculative scenarios, or structural preferences as BLOCKING unless
they make execution fail now.

## Three-Round Protocol

R1 Structural Review:

- Check Definition of Ready.
- Check walking skeleton and smallest executable packet.
- Report only BLOCKING items.

R2 Evidence Review:

- Run only after R1 BLOCKING items are resolved.
- Verify Read Anchors exist.
- Verify Acceptance Checks can be run.
- Verify Allowed Files completeness by dry-running the execution path.
- Report only BLOCKING items.

R3 Final Sweep:

- Run only after R2 BLOCKING items are resolved.
- Check whether code changed since R1 in a way that invalidates the plan.
- Check whether R1/R2 fixes introduced new BLOCKING items.

After R3:

- 0 BLOCKING: `APPROVE`.
- 1-2 BLOCKING: `FIX-AND-RERUN`, then rerun only R3.
- 3+ BLOCKING: `SPLIT`.

A fourth round is allowed only for narrow, clearly fixable BLOCKING items and
only if `audit_trace.md` records why splitting was rejected.

## Iteration Fatigue

Consider `TERMINATE` when any signal is present:

- `CONTRACT_LOCK.md` or equivalent is `LOCKED` or `BLOCKED`.
- 5+ unresolved `NO-GO` / `BLOCKED` items.
- Plan edited recently but no commits reference it.
- 3+ review rounds keep producing new finding categories.
- 10+ sub-stages, sub-packets, or sub-scopes.

If iteration fatigue is suspected, first ask whether the plan can be split into
a smaller approvable packet. If not, load
`references/termination-protocol.md` and write `REVIEW_TERMINATION.md`.

## Reviewer Guardrails

- Do not invent extra severity tiers.
- Do not reclassify `IMPROVEMENT` as `BLOCKING` unless execution fails now.
- Do not ask the plan to answer questions only execution can answer.
- Do not demand cross-reference polish when grep can find the content.
- Do not suggest structural rewrites in R2 or R3.
- Do not measure review quality by number of findings.

## Quick Card

```text
1. Activation pre-check.
   - Plan has commits? use traceable-review.

2. Iteration fatigue?
   - Yes: split if possible; otherwise load termination protocol.

3. Definition of Ready.
   - 9/9: APPROVE.
   - 8/9: one fix round, then approve.
   - <=7/9: R1 or SPLIT.

4. Three rounds.
   - R1: structural BLOCKING only.
   - R2: evidence BLOCKING only.
   - R3: regression BLOCKING only.

5. Exit.
   - APPROVE, FIX-AND-RERUN, SPLIT, or TERMINATE.
```

## References

- Load `references/termination-protocol.md` only when using `TERMINATE`.
- Load `references/rationale-and-sources.md` only when the user asks why this
  review policy exists or when changing the skill itself.

## Integration

| Skill | Relationship |
|---|---|
| `traceable-plan` | Produces the plan this skill reviews. |
| `stage-loop` | Embeds this skill as Phase 1 before execution. |
| `traceable-review` | Runs only after this skill approves and execution produces commits. |
