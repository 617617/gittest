---
name: temporal-phase-blueprint
description: Codex creates the Phase execution blueprint. Trigger DRAFTING_BLUEPRINT; reads the source document and the previous Phase's close.md; writes from-codex/<phase-id>__blueprint.md; BatonNext = PRE_AUDIT_R1.
---

# temporal-phase / blueprint (Codex lane)

## Trigger
- Baton state: `DRAFTING_BLUEPRINT`, entered when a new
  `from-cc/<phase-id>__kickoff.md` lands carrying
  `BatonNext: DRAFTING_BLUEPRINT`. The kickoff artifact is the Phase
  start signal; do not draft a blueprint until you see one.

## Reads
- `workflows/temporal-phase/_coord/from-cc/<phase-id>__kickoff.md` —
  the kickoff carries the Phase id, goal, optional source-doc anchor,
  and (optional) reference to the previous Phase's close.md.
- Authoritative source document — see the anchor path at the top of
  `workflows/temporal-phase/CHARTER.md`, resolved via `PATHS.md`. Use
  the kickoff's `SourceAnchor` field to find the relevant section.
- Previous Phase's `from-codex/<prev-phase-id>__close.md` if the
  kickoff names one.
- You must follow the `## Tools` section below — **do not** hand-roll a
  blueprint from imagination.

## Tools — Delegate to the Temporal Stage Package Generator

The actual blueprint producer is the work-repo-registered Codex skill
`temporal-stage-package-generator`. This lane is only the coord-side
pointer.

### 1. The Generator's contract (authoritative source)

Generator SKILL.md location (resolved via the `temporal:` prefix in
`PATHS.md`):

```text
temporal:.codex/skills/temporal-stage-package-generator/SKILL.md
temporal:local-skill-bundles/temporal-skills-2026-05-21/local/temporal-stage-package-generator/SKILL.md
```

Read it before drafting. It defines:
- the allowed repository scope (`temporal:` only);
- the `pending/` exactly-one + `history/` archive rule;
- the package status enum (`READY` / `READY_TO_GENERATE` /
  `DRAFT_RESHAPE_REQUIRED` / etc.);
- the package shape (`PACKAGE_CHARTER` / `scope` / `HANDOFF_execute` /
  `HANDOFF_plan_review` / `GENERATION_REVIEW_REPORT` /
  `stage-NN/{EXECUTE,scope,evidence}`);
- the required-input list (roadmap, boundary principles, baseline
  manifest, etc.);
- the mandatory post-generation multi-agent review (at least four
  reviewers: queue / source / boundary / research-eval);
- the `BLOCK → GENERATION_BLOCKED` terminal status.

### 2. Invocation paths

Given that Codex-side `.codex/skills.json` currently keeps
`allowGlobalFallback: false`, pick one of:

- **Option A (recommended, no CWD switch).** This lane is "follow the
  Generator's SKILL.md procedure" — read the Generator SKILL.md, then
  in the work repo step through the procedure (create / reshape the
  package directory, place artifacts under `temporal:docs/...
  stage-loop-auto-packages/pending/<package-id>/`, run the
  post-generation multi-agent review). That is exactly what the
  Generator skill's prompt is doing.
- **Option B (explicit CWD switch).** Open a second Codex session with
  CWD = `temporal:` and run `/temporal-stage-package-generator` there.
  After it finishes, return to the coord repo to write this lane's
  coord product.

The Generator's actual work lands in the work repo. It does **not**
write anything into the coord repo.

### 3. coord-side product (what this lane writes)

The coord side carries one "package pointer + Phase metadata" file. It
does **not** copy package content:

```text
BatonNext: PRE_AUDIT_R1

# Phase <id> — Blueprint (pointer)

PackagePath: temporal:docs/skill-temporal-reorchestration/stage-loop-auto-packages/pending/<package-id>/
PackageCommit: temporal@<short-sha>
PackageStatus: READY | READY_WITH_MINOR_REVISIONS | DRAFT_RESHAPE_REQUIRED | GENERATION_BLOCKED
GenerationReviewVerdict: PASS | BLOCK_<reason>

# Summary (so coord-side reviewers can decide quickly)
Goal: ...
Scope:
  - temporal:<path>
Out-of-scope: ...
AllowedFiles:
  - temporal:<file>
Validation:
  - cd $(temporal:) && ...
RiskBoundary: ...
BaseCommit: temporal@<short-sha>
```

`PackageStatus` and `GenerationReviewVerdict` must be taken from the
Generator's actual `GENERATION_REVIEW_REPORT.md` output — do not
guess.

## Writes
- `workflows/temporal-phase/_coord/from-codex/<phase-id>__blueprint.md`
  (the pointer file described in §3 above)
- First line `BatonNext: PRE_AUDIT_R1`.
- The actual package directory is written by the Generator inside the
  work repo, not into this coord mailbox.

## Push order (cross-repo consistency)

You write commits in **two repos** (work repo for the Generator
package, coord repo for the pointer). To avoid dangling references —
where the coord-side `PackageCommit: temporal@<sha>` points at a
commit only on your local machine — push in this strict order:

1. **First**, push the work repo (Temporal):
   ```bash
   cd $(temporal:)
   git push origin <work-branch>
   ```
   Confirm exit 0 before continuing.

2. **Only then**, push the coord repo (gittest):
   ```bash
   cd $(gittest:)
   git push origin master
   ```

Worst case if your second push fails: you have an already-pushed work
repo commit and an unpushed coord-side pointer. On next
`/temporal-phase-codex-sync` you will see baton state has not
advanced (no blueprint pointer in coord); simply retry the coord push.
Pointer/SHA stays consistent.

Worst case if push order is reversed: the coord-side pointer is on
`origin/master` referencing a `temporal@<sha>` that CC's `temporal:`
remote does not have. CC's audit lane cannot resolve the reference;
audit stops with an error and the user has to fix it manually. Avoid
this by following the order above.

If you suspect a cross-repo inconsistency between coord pointers and
work-repo SHAs, the standalone check `scripts/verify_cross_repo_refs.py`
walks both mailboxes + archive and flags any unreachable
`temporal@<sha>` reference; the consumer-side audit lane will fail with
a `CROSS_REPO_MISSING_REF` error if it cannot resolve a pointer.

## Path rules
Code references use the `temporal:<rel>` / `temporal@<sha>` prefixes
**only**; never write absolute machine paths. See `PATHS.md` for the
prefix resolution table.

## Authority
This lane is Codex-only. CC must not write a blueprint into
`from-codex/`. CC contributions belong in the `pre-audit-cc` lane.

## See also
`CHARTER.md` · `ROLES.md` Step 1 · `BATON.schema.md` state
`DRAFTING_BLUEPRINT` · `HANDOFF.md`
