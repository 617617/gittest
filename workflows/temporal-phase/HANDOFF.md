# HANDOFF — temporal-phase workflow · for Codex

Read this file first. It is the Codex entry point for the temporal-phase
preset.

> **CC-side shortcut for the user:** `/temporal-phase-start` is a CC
> orchestrator skill that diagnoses the current baton state and emits
> the right next action automatically (including the Codex-side
> bootstrap text). The user does not need to remember any other command
> on the CC side. This HANDOFF is what *you* (Codex) read; the user's
> path through CC is `/temporal-phase-start`.

## 1. Where you are

- Coord repo (this directory's repo): your machine's `gittest` repo root.
  Your absolute path lives in `PATHS.md`.
- Work repo (where the Phase actually changes code): your machine's
  `temporal` project root. Your absolute path lives in `PATHS.md`.
- Collaboration mode: **path X** — coord artifacts live in the coord
  repo, code changes happen in the work repo, the two are linked by
  commit SHA (details in §5).

Machine paths are maintained **only** in `PATHS.md`. Everywhere else,
documents use prefix references (`gittest:...` / `temporal:...` /
`temporal@<sha>`) to avoid cross-host inconsistency.

## 2. Required reading (in order)

1. `PATHS.md` (host path table + prefix convention)
2. `CHARTER.md` (goals / completion criteria / isolation from testkit)
3. `ROLES.md` (16-step responsibility matrix + product names + mailboxes)
4. `BATON.schema.md` (25 states + legal transitions + 5 invariants)
5. The lane skill matching the current baton state:
   `skills/temporal-phase-<lane>/SKILL.md` — do not read all 15; look up
   by state (see §3.1).

The authoritative source document:
`E:/code/temporal/docs/skill-temporal-reorchestration/current/execution/PHASE_COLLABORATIVE_EXECUTION_WORKFLOW_ZH_2026-05-21.md`

When the source changes, sync ROLES and BATON.schema first.

## 2.1 Registered skill list

All 16 skills are registered in `.codex/skills.json` and loaded by the
Codex CLI at startup. Registration is validated by
`scripts/verify_temporal_phase_skills.py` (`PASS: temporal-phase skills
verified` means healthy).

Codex sees 10 Codex **lane** skills (each writes a baton artifact when
its trigger state is current):
`temporal-phase-blueprint`, `temporal-phase-pre-audit-codex`,
`temporal-phase-execute`, `temporal-phase-postexec-subagent-review`,
`temporal-phase-postexec-synthesize`, `temporal-phase-postexec-fix`,
`temporal-phase-second-audit-decision`, `temporal-phase-second-audit-codex`,
`temporal-phase-second-audit-fix`, `temporal-phase-close`.

Plus 1 Codex **operational** skill (no baton artifact; informational):
`temporal-phase-codex-sync`. See §2.2 below for how to use it.

The 5 CC-only lanes are also registered (`temporal-phase-pre-audit-cc`,
`temporal-phase-pre-audit-synthesize`, `temporal-phase-blueprint-revise`,
`temporal-phase-postexec-cc`, `temporal-phase-second-audit-cc`) — you
should **not** execute them. Their `default_prompt` is marked "Codex
must refuse". When asked to take one of these lanes, refuse and indicate
that it is a CC lane.

## 2.2 Boot procedure (every Codex session)

On every Codex CLI startup on Host B (and any time you want to confirm
state), run:

```text
/temporal-phase-codex-sync
```

That skill (a) pulls origin, (b) runs the verifiers, (c) inspects the
mailbox, and (d) reports your next action. If a kickoff or an
unresponded CC product is waiting, it will name the exact lane you
should open. If nothing is pending, it reports "waiting on CC" or "no
Phase open" and you can stop. You do not need to keep your Codex
session open between Phases — `/temporal-phase-codex-sync` is how you
catch up on anything you missed while offline.

## 3. Your role in this preset

- Creative output owner: blueprint, execution, repair — all driven by
  you.
- Self-driven multi-subagent review: after execution, you launch
  subagents for the integrated review.
- Final repair owner: any audit finding to be adopted is repaired by you.

CC is the independent-viewpoint auditor, cross-side synthesizer, and
flow-closure judge. CC **will not** write blueprints or change code.
Symmetrically, you must **not** write any of the following (authority
refusal, BATON.schema invariant §4): `pre-audit-cc-r*`,
`pre-audit-synthesis-r*`, `blueprint-revision-r*`, `postexec-cc-review`,
`second-audit-cc`.

## 3.1 State → lane lookup

| Baton state | Lane to use |
|-------------|-------------|
| `DRAFTING_BLUEPRINT` | `temporal-phase-blueprint` |
| `PRE_AUDIT_R{1,2,3}` | `temporal-phase-pre-audit-codex` |
| `EXECUTING` | `temporal-phase-execute` |
| `POSTEXEC_SUBAGENT_REVIEW` | `temporal-phase-postexec-subagent-review` |
| `POSTEXEC_SYNTHESIS` | `temporal-phase-postexec-synthesize` |
| `POSTEXEC_FIX` | `temporal-phase-postexec-fix` |
| `SECOND_AUDIT_DECISION` | `temporal-phase-second-audit-decision` |
| `SECOND_AUDIT_CODEX` | `temporal-phase-second-audit-codex` |
| `SECOND_AUDIT_FIX` | `temporal-phase-second-audit-fix` |
| `PHASE_CLOSING` | `temporal-phase-close` |

The CC-driven states (`PRE_AUDIT_SYNTHESIS_R*`, `BLUEPRINT_REVISION_R*`,
`POSTEXEC_CC_REVIEW`, `SECOND_AUDIT_CC`) advance under CC; you only wait
for the matching products to appear in `from-cc/`.

## 4. Where your products go

Write path: `workflows/temporal-phase/_coord/from-codex/`

Filename pattern: `<phase-id>__<step-tag>.md` (`step-tag` per ROLES Step
Matrix: `blueprint`, `pre-audit-codex-r1`, `execution-report`, etc.).

**The first line of every product must be:**

```text
BatonNext: <STATE>
```

`<STATE>` is one of the state names in `BATON.schema.md`. Readers
advance the baton based on this line. Products without a `BatonNext:`
line are treated as drafts and do not trigger any state transition.

## 5. How "coord here, code there" links under path X

When a blueprint or execution report references code, use these anchors
to avoid coord/work drift:

- Work-repo path reference: `temporal:<relative>`, e.g.
  `temporal:src/foo/bar.go`.
- Work-repo commit reference: `temporal@<short-sha>`, e.g.
  `temporal@a1b2c3d`.
- Work-repo range reference: `temporal@<base>..<head>`.
- Do not copy work-repo code changes into the coord repo. Reference only.

Blueprint template fragment (`<phase-id>__blueprint.md`):

```markdown
BatonNext: PRE_AUDIT_R1

# Phase <id> — Blueprint

Goal: ...
Scope:
  - temporal:src/foo/
  - temporal:docs/<...>/
Out-of-scope: ...
AllowedFiles:
  - temporal:src/foo/bar.go
  - temporal:src/foo/baz.go
Validation:
  - cd $(temporal:) && pytest tests/foo/
ExpectedArtifacts:
  - temporal:src/foo/<new-files>
  - gittest:workflows/temporal-phase/_coord/from-codex/<phase-id>__execution-report.md
RiskBoundary: ...
BaseCommit: temporal@<short-sha>
```

When an execution report lists "actual changes", give the work-repo
commit list:

```markdown
ActualChanges:
  - temporal@a1b2c3d  feat(foo): add bar
  - temporal@e4f5g6h  test(foo): cover bar edge cases
```

## 6. Getting started

Your Phase start signal is **always a kickoff file**, never a chat
instruction.

When CC writes `workflows/temporal-phase/_coord/from-cc/<phase-id>__kickoff.md`
and pushes it, your watcher fires and you enter `DRAFTING_BLUEPRINT`.
The kickoff carries:

- `PhaseId:` — the phase id matching `phase-\d+` (this is your phase
  id; do not invent your own).
- `Goal:` — what this Phase aims to do.
- `SourceAnchor:` — optional section pointer into the source workflow
  document.
- `PreviousPhaseClose:` — optional pointer to the previous Phase's
  close.md (use it as predecessor context).

Procedure:

1. Read the kickoff completely.
2. Resolve `SourceAnchor` (if any) and read that section of the source
   document.
3. Resolve `PreviousPhaseClose` (if any) and read it.
4. Open the blueprint lane:
   `workflows/temporal-phase/skills/temporal-phase-blueprint/SKILL.md`.
   Its `## Tools` section delegates the real generation work to the
   work-repo skill `temporal-stage-package-generator`. Follow its
   procedure.
5. Write the coord-side pointer file
   `from-codex/<phase-id>__blueprint.md` with first line
   `BatonNext: PRE_AUDIT_R1`.
6. Commit to the coord repo and push to `origin/master`.

CC's side will pick up your blueprint on the next monitor tick.

**Do not** start a Phase without seeing the kickoff. If the user asks
in chat to "start a Phase" without a kickoff in `from-cc/`, redirect
them to run `/temporal-phase-start` on the CC side — that is the only
sanctioned entry point.

## 7. Hard rules

- **No scope creep.** Execution stays strictly inside `AllowedFiles:`.
  When a significant gap shows up or the code state contradicts blueprint
  assumptions, stop, write a note, and transition to
  `BLOCKED_BLUEPRINT` — do not widen the change.
- **Three-round cap.** Pre-execution audit caps at `PRE_AUDIT_R3`. If
  round 3 is still not acceptable, the blueprint repair lane (CC) will
  write `BatonNext: BLOCKED_BLUEPRINT`. Do not try to open an R4.
- **Second dual audit is one-shot.** After `SECOND_AUDIT_FIX` you only
  go to `PHASE_CLOSING` or `BLOCKED_POSTEXEC`. There is no loop back to
  `SECOND_AUDIT_DECISION`.
- **Completion-criteria gate.** `close.md` must enumerate every
  completion criterion from CHARTER and tag each pass/fail. Any failure
  means `COMPLETED` is not allowed.
- **Subagents do not decide.** Multi-subagent review emits opinions; the
  final disposition is yours.
- **Isolation.** Do not read or write anything under
  `blue-k-git-baton-testkit/`.

## 8. Relationship to the testkit

Unrelated. The testkit is a separate simulator for the Blue-K git baton
protocol. This preset borrows the "git mailbox" idea from it, but the
state machine, mailbox directories, HANDOFF, and skill set are
independent. A change on either side should not trigger a change on the
other.
