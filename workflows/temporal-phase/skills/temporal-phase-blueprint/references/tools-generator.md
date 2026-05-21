# Tools — Delegate to the Temporal Stage Package Generator

The actual blueprint producer is the work-repo-registered Codex skill
`temporal-stage-package-generator`. This lane is only the coord-side
pointer.

## 1. The Generator's contract (authoritative source)

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

## 2. Invocation paths

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

## 3. coord-side product (what this lane writes)

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
