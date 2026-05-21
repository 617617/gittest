# Handoff: Portable Blue-K Workflow Skill Bundle

Audience: the Claude/Codex agent taking over this repository from another
machine.

Purpose: preserve the user's real Blue-K workflow behind the simple Git baton
surface. The human should normally run one shell command, then one AI-chat
command selected by that shell command:

```text
bk sync
/bk work
```

The chat command may be `/bk resume` or `/bk takeover` when `bk sync` prints it,
but the human should not have to infer that manually.

## Portable Skill Location

All project-local copies live here:

```text
blue-k-git-baton-testkit/skills/
```

Use these copies instead of any user-machine skill path. All references inside
the copied skills are repo-relative. Do not assume paths under a global Codex,
Claude, or home-directory skill registry.

## Packaged Skill Closure

Direct Blue-K workflow skills:

- `blue-k-planner`
- `blue-k-plan-audit`
- `blue-k-main-runner`
- `blue-k-other-runner`
- `blue-k-other-index`

Skills required by those workflows:

- `traceable-plan`
- `pre-doc-review`
- `stage-loop-auto`
- `stage-loop`
- `doc-review`
- `traceable-review`

This is the minimum portable closure for the user's current workflow. Do not
drop the indirect skills: runner and audit workflows call them.

Not packaged by default:

- `blue-other-parallel-tracker`: template/reference, not a direct runtime
  dependency of this workflow.
- `bdd-workflow`: policy-adjacent but not directly referenced by the packaged
  skills.
- global principle skills: use the target repo's own `AGENTS.md` and governance
  docs as authority.

## User Workflow To Preserve

The user's intended loop is:

1. Create or repair the K plan with `blue-k-planner`.
2. Give the plan to Codex and Claude for separate review.
3. Claude synthesizes the plan-review opinions and repairs the plan when needed.
   If a critical issue exists, repeat review and repair until there is no
   critical issue.
4. Analyze dependency order between `main` and `other`, then recommend an
   execution route such as `main` through package 03, then `other` through
   package 04, then back to `main`.
5. Execute package work with `blue-k-main-runner`, `blue-k-other-index`, and
   `blue-k-other-runner`.
6. After each code/package checkpoint, Codex and Claude review separately.
7. Codex synthesizes the code-review opinions. If a critical issue exists,
   route back to a fix lane, then review again until there is no critical issue.

Treat "critical issue" as an existing protocol blocker, not as a new state:

```text
Plan side: BLOCK, lower-gate BLOCK, or consensus critical finding.
Code side: BLOCK, fix_required, subject mismatch, hash mismatch, or consensus
critical finding.
```

Lower-gate `BLOCK` cannot be overridden by consensus.

## Recommended Role Split

Keep the division close to the user's preferred CC/Claude plus Codex pairing:

- CC/Claude leads `blue-k-planner`, `blue-k-plan-audit`, and plan consensus
  synthesis.
- Codex leads `blue-k-main-runner`, `blue-k-other-index`,
  `blue-k-other-runner`, and code consensus synthesis.
- Both sides can provide independent plan-review and code-review opinions.
- The synthesizer is not allowed to weaken a lower gate. It only merges review
  opinions into `accepted`, `fix_required`, `planner_repair`, or
  `human_blocked`.

This preserves the earlier split: Claude/CC is strongest on planning,
coordination prose, and plan repair; Codex is strongest on execution, test/code
evidence, and code-review closure. The baton still owns mutual exclusion, so the
role split does not permit both sides to edit the same subject at once.

## Plan Consensus Loop

Plan state machine:

```text
blue-k-planner
  -> blue-k-plan-audit
  -> Codex plan review + Claude plan review
  -> Claude synthesis
  -> no critical? execution recommendation
  -> critical? repair with blue-k-planner and repeat
```

Required plan artifacts in the real project:

```text
docs/mian-k/BLUE_K_PLAN_AUDIT_REPORT.md
docs/mian-k/Kx_INDEX.md
docs/mian-k/PACKAGE_GENERATION_MAP.yaml
docs/mian-k/AUDIT_MANIFEST.yaml
```

If one side changes the plan subject after review starts, the old consensus is
stale. Start a new review topic for the new plan subject.

## Dependency Recommendation Loop

Before choosing execution order, inspect:

```text
docs/mian-k/Kx_INDEX.md
docs/mian-k/MAIN_PACKAGE_PROGRESS.md
docs/mian-k/OTHER_MIN_PACKAGE_PROGRESS.md
docs/mian-k/main/**/PACKAGE_SET_INDEX.md
docs/mian-k/other/**/PACKAGE_SET_INDEX.md
```

Use `blue-k-other-index` to refresh or inspect the minimum executable package
queue for `other`. Recommend an order that preserves:

- serial `main` dependencies;
- `other` prerequisites;
- required-before-merge constraints;
- active/running package resumption before new package starts;
- review-pending finalization before new package starts.

Example output shape:

```text
Recommended execution:
1. Run blue-k-main-runner until main index 03 reaches review_pending or done.
2. Run blue-k-other-index to refresh OTHER_MIN_PACKAGE_PROGRESS.md.
3. Run blue-k-other-runner until other index 04 reaches review_pending or done.
4. Return to blue-k-main-runner for the next unblocked main package.
```

This recommendation is advisory. The baton still selects exactly one active
assignment at a time.

## Code Consensus Loop

Code/package state machine:

```text
runner checkpoint
  -> review_pending
  -> Codex code review + Claude code review
  -> Codex synthesis
  -> accepted? finalize current package only, then stop
  -> critical/fix_required? route to runner-owned fix lane and repeat review
```

Accepted consensus finalizes only the package/commit under review. It must not
automatically start the next package.

Reject or restart consensus when any of these appear:

- subject commit changed;
- topic superseded or cancelled;
- docs-only freeze violated;
- canonical acceptance hash mismatch;
- lower gate or code graph gate says BLOCK;
- review is against a local unpushed commit that the other side cannot see.

## Runner Boundaries

`blue-k-main-runner` owns the main progress table:

```powershell
python "blue-k-git-baton-testkit/skills/blue-k-main-runner/scripts/main_progress.py" next --mian-k "docs/mian-k"
```

`blue-k-other-index` owns the other progress table:

```powershell
python "blue-k-git-baton-testkit/skills/blue-k-other-index/scripts/other_progress.py" next --mian-k "docs/mian-k"
```

Runners select or resume one package. A package-runner subagent may then invoke
`stage-loop-auto` for exactly that package. `stage-loop-auto` owns its internal
`stage-loop`, `doc-review`, execution, fix, and `traceable-review` phases.

The outer baton wrapper must not:

- choose packages inside the shell command;
- execute `stage-loop-auto` directly;
- write progress tables directly;
- bypass audit, consensus, or code graph gates;
- ask the human to run raw `git pull` during normal operation.

## Git Baton Integration

`bk sync` is the shell-side state synchronizer. It should fetch, safely
fast-forward when allowed, print one `NEXT:` line, and print/copy the exact
`ChatCommand`.

`/bk work`, `/bk resume`, and `/bk takeover` are chat-side execution entries.
They must re-check that local HEAD, origin work branch, and BATON work-branch
head match before starting.

If work is interrupted:

- same holder resumes with `/bk resume` only from the original holder chat;
- other side can use `/bk takeover` only from the last pushed checkpoint and
  only after explicit human confirmation such as `yes, abandon`;
- unpushed local work from the abandoned side is not assumed safe.

If the other side has not finished:

- active lease and holder mismatch must block ordinary `/bk work`;
- stale lease may suggest takeover, but must not auto-takeover;
- review_pending must route to consensus/finalization rather than starting new
  package work.

## Other Side Setup

When registering these skills in another project, copy the whole directory:

```text
blue-k-git-baton-testkit/skills/
```

Then register or expose each `SKILL.md` from the copied project-local paths.
Keep internal references relative to the target repository root. If the target
agent has a different skill registry format, adapt only the registry wrapper;
do not edit the workflow semantics.

Read these files first:

```text
AGENTS.md
blue-k-git-baton-testkit/SKILL.md
blue-k-git-baton-testkit/HANDOFF.md
blue-k-git-baton-testkit/HANDOFF_REGISTER_CLAUDE_PROJECT_SKILLS.md
blue-k-git-baton-testkit/references/protocol-v0.10.md
blue-k-git-baton-testkit/references/scenario-matrix.md
```

## Acceptance

The setup is acceptable when:

- `bk sync` is the only normal shell sync entry;
- `/bk work` is the normal chat work entry selected by `bk sync`;
- all packaged skills are available from project-local relative paths;
- plan review has a two-side review plus synthesis loop;
- code review has a two-side review plus synthesis loop;
- critical findings loop back to repair/fix and review again;
- runner finalization stops after the current package;
- no normal instruction asks the human to run manual `git pull`.
