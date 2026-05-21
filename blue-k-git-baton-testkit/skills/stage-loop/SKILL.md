---
name: stage-loop
description: >-
  Single-stage closed-loop orchestrator for traceable plans. Runs one approved
  stage through doc-review, execute, and traceable-review by spawning mandatory
  isolated subagents with layer-appropriate documents only. Enforces context
  isolation, hard git/filesystem verification, one execution commit, and the
  bounded review/fix loop. Use when a traceable-plan stage is approved and ready
  to execute end-to-end, or when the user says "run stage N" or "execute stage
  N". Do not use when doc-review has not approved the stage, previous-stage
  admission has not passed, the user wants to generate a plan, or the user wants
  review without execution.
---

# Stage Loop

Single-stage closed-loop orchestrator. One invocation runs exactly one stage of a traceable plan through doc-review -> execute -> traceable-review with strict context isolation between phases.

## Output Language Rule (MANDATORY)

ALL artifacts produced by this skill and by every subagent it spawns MUST be **English-only with ASCII punctuation**. This applies to:

- The final stage-loop report
- Phase-1 doc-review verdict block
- Phase-2 commit message body and `evidence.md` content
- Phase-3 traceable-review findings and fix-execute notes
- Any markdown persisted to the plan directory

Rules:
1. **English-only**. All prose, headings, severity labels, structured fields -- English.
2. **ASCII quotes only**. Straight `"` and `'`.
3. **No Unicode punctuation**. Use `--`, `...`, `-`.

Every subagent prompt issued by this skill MUST include this rule verbatim near the top so the subagent inherits it. The conversation with the user may be in any language; the rule applies only to written artifacts.

## Mandatory Subagent Gate

This skill requires subagents for every phase. The main agent is the orchestrator
only; it must not replace a doc-review, execute, traceable-review, or fix-execute
subagent with direct main-agent work.

Mandatory subagents:

- Phase 1: doc-review subagent.
- Phase 2: execute subagent.
- Phase 3: traceable-review subagent.
- Fix loop: fix-execute subagent whenever review requires a fix.

If any required subagent cannot be spawned, stop with `STAGE_LOOP_BLOCKED_NO_SUBAGENT`.

Before reporting `STAGE_LOOP_BLOCKED_NO_SUBAGENT`, actually attempt the required
spawn for the current phase. If the spawn fails because too many subagents are
open, close completed or no-longer-needed subagents from this stage-loop
execution context when tool support is available, then retry the required spawn
once. Only block after that retry fails. Do not preemptively block only because
capacity might be low.

Run strictly serial inside this skill. Spawn only the subagent required for the
current phase or fix attempt, wait for it to finish, verify its result, and only
then move to the next phase. Do not run doc-review, execute, traceable-review,
or fix-execute subagents in parallel.

## Dirty Worktree Checkpoint Gate

Whenever this skill or a calling protocol requires a clean worktree, first
inspect `git status --short --branch` in the repository containing the stage
directory. If the worktree is dirty, create exactly one full-repository
checkpoint commit before continuing:

```powershell
git add -A
git commit -m "chore(worktree): checkpoint before stage-loop"
git status --short --branch
```

Continue only if the follow-up status is clean. If the commit fails or the
worktree remains dirty, stop with:

```text
STAGE_LOOP_BLOCKED_DIRTY_AFTER_CHECKPOINT
```

Do not treat a dirty worktree as an immediate blocker until this checkpoint
attempt has been made.

## Position in the System

```
Main agent loop:
  for stage in [01, 02, 03, 04, ...]:
    1. main agent runs Admission Checklist (5 shell commands)
    2. if all pass:
         $stage-loop <plan-dir> <stage-id>
       else:
         STOP and report
    3. parse stage-loop final report
    4. if verdict == ACCEPT: continue to next stage
       else: STOP and report
```

The skill is invoked **once per stage**. Cross-stage gating belongs to the main agent, not to this skill.

## When to Use

Trigger when:
- doc-review has APPROVED the target stage (a `REVIEW_TERMINATION.md` listing the stage in "Approved for Execution", OR an explicit doc-review pass with verdict APPROVE)
- The previous stage (if any) has a `Stage: <prev>` commit in git log
- The plan directory layout matches the traceable-plan format (audit / execution / reference layers)

## Admission Checklist (MANDATORY before invocation)

The calling agent MUST run these five shell commands and confirm all pass before invoking this skill. Paste the raw output. No skipping.

```bash
# 1. Target stage's EXECUTE.md must exist
ls <plan-dir>/<stage-id>/EXECUTE.md
#    -> exit 0

# 2. (Skip for first stage) Previous stage must have a Stage: commit
git log --oneline --grep="Stage: <prev-stage-id>" -- <plan-dir>/<prev-stage-id>/
#    -> >=1 commit listed

# 3. (Skip for first stage) Previous stage's evidence must not be PENDING
grep -c "PENDING EXECUTION" <plan-dir>/<prev-stage-id>/evidence.md
#    -> 0

# 4. (Skip for first stage) Previous stage's evidence must show ACCEPT/PASS
grep -E "verdict|Verdict|verdict:" <plan-dir>/<prev-stage-id>/evidence.md | grep -iE "PASS|ACCEPT"
#    -> >=1 match

# 5. (If REVIEW_TERMINATION.md exists) Target stage must be in approved list
grep "<stage-id>" <plan-dir>/REVIEW_TERMINATION.md
#    -> >=1 match (or file does not exist, which is fine)
```

If any check fails -> STOP. Do not invoke this skill. Report the failure to the user.

This checklist is the human-review substitute. It works because git/fs/grep do not lie about commits, evidence file contents, or termination-report contents. The calling agent cannot skip these and pretend they passed; the raw output must be in the conversation.

## Document Layer Isolation Rules

The traceable-plan format declares three layers. Each phase pass sees only its layer plus narrowly necessary cross-layer reads:

| Layer | Files | Phase 1 (doc-review) | Phase 2 (execute) | Phase 3 (traceable-review) |
|---|---|---|---|---|
| Audit | `00_master.md`, root `scope.md`, `audit_trace.md`, `HANDOFF_review.md`, `NN_<name>.md` | YES (full) | NO | NO |
| Execution | `<stage>/EXECUTE.md`, `HANDOFF_execute.md` | YES | YES | YES (contract only) |
| Reference | `<stage>/scope.md`, `SHARED_VOCABULARY.md` | YES | YES (limited sections) | YES |
| Evidence | `<stage>/evidence.md` | NO (empty pre-exec) | YES (write target) | YES (read commit-time content) |
| Other stages | `NN_<other>/*` | filenames only (fan-out count) | NO | NO |
| Source code | project Java/SQL files | only Read Anchor grep checks | YES (per Read Anchors in EXECUTE.md) | YES (per git diff) |

Each subagent prompt explicitly lists "MUST READ" and "MUST NOT READ" filenames. Any subagent that violates isolation MUST stop and report; the orchestrator must not paper over violations.

## Code Graph Consumption Rule

Follow the repository Code Graph Contract in `AGENTS.md`; detailed graph
commands live in `scripts/code_graph/README.md`. If graph tooling exists, every
phase may use the current graph only to choose what source to read next. It is
not a truth source.

Short rule for all subagent prompts:

```text
You may use the current code graph as navigation evidence only. Before making
or reviewing a claim, verify it against source code and the stage/package
contracts. Do not edit graph.db directly. Dynamic overlay acceptance belongs to
the package-level code graph gate.
```

## Phase 1: doc-review

### Goal
Verify the stage is READY for execution. Run the doc-review skill protocol against the stage.

### Subagent
- Codex agent type: `default` with isolated context
- Skill injection: full doc-review SKILL.md content embedded in prompt header
- No direct main-agent substitute is allowed

### Prompt Template
```
You are a pre-execution reviewer for stage <stage-id> of plan at <plan-dir>.

Apply the doc-review skill protocol below in full:
<EMBED doc-review SKILL.md content>

MUST READ:
- <plan-dir>/00_master.md
- <plan-dir>/scope.md
- <plan-dir>/audit_trace.md
- <plan-dir>/<stage-id>/EXECUTE.md
- <plan-dir>/<stage-id>/scope.md

MAY READ (only if needed for Read Anchor verification, one-shot grep):
- Project source files cited in EXECUTE.md Read Anchors

MUST NOT READ:
- Other stages' EXECUTE.md / scope.md / evidence.md content
  (you may `ls` to count fan-out, but do not read content)
- HANDOFF_review.md (this skill replaces it)
- Project source code beyond targeted anchor checks

Output a structured verdict block:
VERDICT: APPROVE | SPLIT | TERMINATE | FIX-AND-RERUN
DEFINITION_OF_READY: <X>/9
BLOCKING_ITEMS:
- <item> (or "none")
NOTES: <one paragraph>
```

### Retry Policy
- Default: 1 attempt
- Repeat ONLY if the phase pass output is unparseable (transport / format failure where no verdict was actually rendered)
- Verdict of SPLIT / TERMINATE / FIX-AND-RERUN is NOT a retry case -- exit and report
- Substantive verdicts are never re-rolled. If the verdict suggests work is needed before this stage can run, prefer splitting the stage rather than re-spinning doc-review.

### Verdict Handling
- APPROVE -> proceed to Phase 2
- SPLIT -> exit skill, report "plan needs splitting before this stage"
- TERMINATE -> exit skill, surface the termination report path
- FIX-AND-RERUN -> exit skill, report "1-2 BLOCKING items, human decides next move"

## Phase 2: execute

### Goal
Implement the stage according to EXECUTE.md, run pre-commit code-reviewer, commit, fill evidence.md.

### Subagent
- Codex agent type: `worker` with ownership of only the stage Allowed Files
- No direct main-agent substitute is allowed
- No skill injection; the EXECUTE.md is its instruction set

### Prompt Template
```
=== SYSTEM PREAMBLE: EXECUTION DISCIPLINE (READ ONCE, APPLY THROUGHOUT) ===
These four anti-laziness rules are non-negotiable and apply to every step you
take in this stage. Violating any one = stage rejected at review. They are
injected here by stage-loop and are NOT duplicated in EXECUTE.md, so do not
look for them there.

1. Read Before Write: Before modifying ANY function, read the entire function
   body via the Read Anchors listed in EXECUTE.md. State to yourself in plain
   language what it currently does. If you cannot, you are NOT ready to modify
   it -- STOP and request additional anchors.
2. Pre-Change Behavioral Anchor: For each function you modify, BEFORE the edit
   record three lines: `BEFORE: <fn> does X, Y, Z. Invariant: <what must not
   change>` / `CHANGE: <lines> to achieve <goal>` / `AFTER: <fn> does X, Y, Z'.
   Invariant preserved.` Paste these into Evidence.
3. Tool-Grounded Evidence: Every claim in Evidence MUST be backed by raw
   command output. A test result of "PASS" with no pasted stdout is
   `[UNVERIFIED]`. NEVER paraphrase, NEVER fabricate -- if a tool was not run,
   mark `[UNVERIFIED]` explicitly.
4. No Tool-Failure Tunneling: If a tool call (test, read, grep) fails or times
   out, do NOT proceed as if it succeeded and do NOT fill in the result from
   prior knowledge. Mark the dependent step `[BLOCKED: tool failure]` and STOP.

=== END SYSTEM PREAMBLE ===

You are executing stage <stage-id> of a traceable plan. The plan has audit /
execution / reference layers; you are restricted to the EXECUTION and REFERENCE
layers only.

MUST READ (in this order):
1. <plan-dir>/HANDOFF_execute.md
2. <plan-dir>/<stage-id>/EXECUTE.md   (your full instruction set; read the Global Context section FIRST so you have the audit-layer perspective before touching local steps)
3. <plan-dir>/<stage-id>/scope.md     (acceptance checks)
4. doc/step/SHARED_VOCABULARY.md      (only sections referenced by HANDOFF_execute.md)
5. Read Anchors listed inside EXECUTE.md (project source files, per anchors)

MUST NOT READ:
- <plan-dir>/00_master.md
- <plan-dir>/scope.md (root scope)
- <plan-dir>/audit_trace.md
- <plan-dir>/HANDOFF_review.md
- <plan-dir>/<stage-id>.md (audit-layer stage card; the EXECUTE.md is the thin version)
- Other stages' files (NN_<other>/* and NN_<other>.md)

Before doing anything, echo your reading list and confirm you have not opened
any MUST NOT READ file.

Then execute EXECUTE.md step-by-step:
- Apply changes only within Allowed Files declared in EXECUTE.md
- Run baseline + post-change commands listed in EXECUTE.md
- Run banned-terms grep
- If code graph tooling exists, use the graph/search output only to locate
  relevant source, then verify the actual source before edits. Do not update
  overlay edges during stage execution.
- Run a code-reviewer agent on the staged diff; fix all CRITICAL/HIGH findings
- Make ONE commit using the structured message template in EXECUTE.md
- Fill <plan-dir>/<stage-id>/evidence.md with raw command output
  (Replace every [PENDING EXECUTION] block with actual stdout)

Final output (machine-parseable):
COMMIT_HASH: <full sha>
EVIDENCE_FILLED: yes | no
ACCEPTANCE_VERDICT: PASS | WARN | BLOCKED | UNVERIFIED
NOTES: <one paragraph if anything notable>
```

### Retry Policy
- Default: no retry
- If commit not produced or evidence not filled -> exit skill, report failure
- A single re-run is permitted ONLY when the failure is clearly environmental (transient tool failure, sandbox / timeout, infra glitch) AND the orchestrator records the cause in the final report. Genuine execution failures (logic, scope creep, missing context, design ambiguity) are NEVER retried -- exit and consider splitting the stage instead.

### Hard Verification (orchestrator runs after the execution subagent reports)
After the execution subagent claims completion, orchestrator MUST run:
```bash
git log --oneline --grep="Stage: <stage-id>" -- <plan-dir>/<stage-id>/
#   -> must list >=1 commit
grep -c "PENDING EXECUTION" <plan-dir>/<stage-id>/evidence.md
#   -> must be 0
git show <reported-hash> --stat
#   -> must show changes within Allowed Files only
```

If any verification fails -> exit skill, report. The subagent's claim is not trusted; only git/fs evidence is.

## Phase 3: traceable-review

### Goal
Verify the commit honors the contract: Allowed Files boundary, evidence is tool-grounded, scope creep absent, tests claimed pass actually pass.

### Subagent (review side)
- Codex agent type: `default` with isolated context
- Skill injection: full traceable-review SKILL.md content embedded in prompt header
- No direct main-agent substitute is allowed

### Subagent (fix side, if needed)
- Codex agent type: `worker` with ownership of only the original Allowed Files
- No direct main-agent substitute is allowed
- Receives: review findings + commit hash + EXECUTE.md Allowed Files list
- Constraint: may only modify files within the original commit's diff (no scope expansion)

### Loop Protocol (default 3 attempts; extra attempts require justification)

```
attempt = 1
while attempt <= 3:
    spawn traceable-review subagent with prompt below
    parse verdict:
        ACCEPT  -> done, exit Phase 3 with success
        WARN    -> done, exit Phase 3 with success + follow-up notes
        CHANGES_REQUESTED:
            if attempt < 3:
                spawn fix-execute subagent with review findings
                if fix-execute subagent reports "cannot fix" or commit not amended:
                    exit Phase 3 with BLOCK  (Q2 policy: B - immediate BLOCK)
                attempt += 1
                continue
            else:
                # default: exit BLOCK after 3 attempts.
                # Exception path (4th attempt) is permitted ONLY when:
                #   1. The remaining findings are narrow and clearly fixable
                #      (one or two specific items, not "rework the design")
                #   2. The orchestrator records WHY splitting the stage was
                #      rejected, in the final report
                # If both conditions hold, run one additional fix-execute +
                # traceable-review pass; otherwise:
                exit Phase 3 with BLOCK
        BLOCK   -> exit Phase 3 with BLOCK immediately
```

Going past 3 attempts is the exception, not the rule. If after 3 attempts the verdict is still CHANGES_REQUESTED and the work is broad, ambiguous, or the executor keeps drifting, prefer **splitting the stage** rather than looping further. The numeric "3" is a default cadence for healthy convergence, not a hard cap.

### Review Subagent Prompt Template
```
You are post-execution reviewing commit <hash> for stage <stage-id>.

Apply the traceable-review skill protocol below:
<EMBED traceable-review SKILL.md content>

MUST READ:
- git show <hash> --stat
- git show <hash> -- <plan-dir>/<stage-id>/evidence.md
- git diff <hash>^..<hash>
- <plan-dir>/<stage-id>/EXECUTE.md   (the contract)
- <plan-dir>/<stage-id>/scope.md     (acceptance)
- If present for the reviewed diff, `.crg/gates/*/COMMIT_GRAPH_GATE.json`
  and the referenced `graph_diff.md`

MAY READ (only if review requires source-code semantic check):
- Project source files actually changed in <hash>

MUST NOT READ:
- Other stages' files
- <plan-dir>/00_master.md, root scope.md, audit_trace.md, HANDOFF_review.md

Output structured verdict:
VERDICT: ACCEPT | WARN | CHANGES_REQUESTED | BLOCK
BOUNDARY_CHECK: clean | breach (list extra files)
EVIDENCE_CHECK: tool-grounded | UNVERIFIED count = N
CODE_GRAPH_GATE: pass | warn | missing | stale | blocked
SCOPE_CREEP: none | <list>
FINDINGS:
- severity (BLOCK/HIGH/MEDIUM): <file:line> <issue> <suggested narrow fix>
NOTES: <one paragraph>
```

### Fix-Execute Subagent Prompt Template
```
Stage <stage-id> commit <hash> failed traceable-review with these findings:
<paste findings list>

Constraints:
- You may modify ONLY files in this Allowed Files list:
  <paste from EXECUTE.md>
- You may NOT change EXECUTE.md, scope.md, or other plan documents.
- You may amend the existing commit (git commit --amend) OR create a fix-up
  commit; either is acceptable.
- After fix, update <plan-dir>/<stage-id>/evidence.md to record what was fixed
  (append a "Fix Round N" section, do not rewrite earlier evidence).

Output:
NEW_COMMIT_HASH: <sha>  (or AMENDED_HASH: <sha>)
FIX_APPLIED: <one-line per finding>
NOTES: <if anything could not be fixed, say "cannot fix: <reason>" and stop>
```

If fix subagent reports "cannot fix" -> Phase 3 exits with BLOCK immediately (no further review attempt).

## Final Report Format

The skill emits one structured report at the end:

```markdown
# stage-loop report: <stage-id>

**Date**: YYYY-MM-DD
**Plan**: <plan-dir>
**Stage**: <stage-id>

## Phases

| Phase | Verdict | Attempts | Notes |
|---|---|---|---|
| doc-review | APPROVE / SPLIT / TERMINATE / FIX-AND-RERUN | 1 | ... |
| execute | success / failed | 1 | commit hash if success |
| traceable-review | ACCEPT / WARN / BLOCK | N (1-3; 4 only with rationale) | ... |

## Outcome

**FINAL VERDICT**: ACCEPT | WARN | BLOCK | EARLY_EXIT

**Commit**: <hash> (or "none, exited at phase X")

## Next Step

<one of:>
- Run admission checklist for stage <next-id> and re-invoke stage-loop
- Human review required: <specific issue>
- Plan needs splitting before this stage can re-execute
```

The calling agent MUST NOT auto-proceed to the next stage. The "Next Step" line is a recommendation; the calling agent re-runs its own admission checklist before invoking stage-loop again.

## Anti-Cheating Rules (For The Orchestrator)

The calling agent following this skill must avoid these patterns:

- **Skipping admission checklist**: every command output must be in the conversation. "Looks fine" is not acceptable.
- **Trusting subagent reports without verification**: Phase 2 hard verification (`git log` / `grep PENDING`) is non-negotiable.
- **Running stage-loop on a stage that doc-review has not approved**: Phase 1 inside this skill is the FINAL doc-review pass; if you ran an external doc-review and it gave APPROVE, Phase 1 should re-confirm. Do not skip Phase 1.
- **Auto-progressing to next stage without re-running checklist**: stage-loop returns; the calling agent restarts the cycle from admission checklist for the next stage. No skill chaining.
- **Letting fix-execute expand scope**: every fix attempt must stay inside the original commit's Allowed Files. Scope expansion is a BLOCK.
- **Inflating retry count without cause**: defaults are doc-review 1x (transport only), execute 0x (one re-run only for clearly environmental flake), traceable-review 3 attempts (1 review + 2 fix-and-recheck). Any extra attempt MUST be a documented exception in the final report (e.g., "transport failure on first call", "test infra glitch on first execute, re-run identical", "narrow residual lint finding after 3rd review"). Do NOT silently re-roll substantive verdicts. When in doubt, prefer splitting the stage over inflating the retry count.
- **Skipping Execution Discipline preamble injection**: Phase 2 prompts MUST prepend the 4-rule SYSTEM PREAMBLE (Read Before Write / Pre-Change Behavioral Anchor / Tool-Grounded Evidence / No Tool-Failure Tunneling) verbatim. The preamble is what enforces anti-laziness at execute time -- if it is missing, the executor has no honesty floor and the stage's evidence becomes uninterpretable. Treat preamble omission as a configuration error: re-spawn with corrected prompt rather than accepting the result. Verifying the executor echoed the preamble in its first message is a cheap self-check.

## Quick Reference

```
INVOCATION SEQUENCE

1. Calling agent runs admission checklist (5 shell commands).
   - All pass -> step 2
   - Any fail -> STOP, report

2. Calling agent invokes:
   $stage-loop <plan-dir> <stage-id>

3. Skill internally:
   Phase 1: doc-review subagent (1x)
     -> APPROVE -> Phase 2
     -> other  -> exit
   Phase 2: execute subagent (no retry)
     -> commit produced + evidence filled + verification passed -> Phase 3
     -> any failure -> exit
   Phase 3: traceable-review loop (default 3, extra attempts require justification)
     -> ACCEPT/WARN -> done
     -> BLOCK or 3 attempts exhausted -> exit BLOCK

4. Skill emits final report.

5. Calling agent reads report, decides:
   ACCEPT/WARN -> back to step 1 with next stage
   BLOCK/EARLY_EXIT -> STOP, surface report to user
```

## Integration with Other Skills

| Skill | Relationship |
|---|---|
| `traceable-plan` | Produces the plan this skill executes against. Plan layout (audit/execution/reference layers, EXECUTE.md / scope.md / evidence.md trio) is the contract. |
| `doc-review` | Embedded as Phase 1. The Phase 1 subagent runs the full doc-review protocol. If a separate doc-review pass produced REVIEW_TERMINATION.md, Phase 1 re-confirms the target stage is on the approved list. |
| `traceable-review` | Embedded as Phase 3. Same skill, run inside an isolated subagent against the just-produced commit. |

## Sources

The orchestration design synthesizes:
- Spec-Kit phase gates (4-phase workflow with explicit checkpoints): [github/spec-kit](https://github.com/github/spec-kit)
- Walking Skeleton / Tracer Bullet (one stage end-to-end before broadening): [Henrico Dolfing](https://www.henricodolfing.com/2018/04/start-your-project-with-walking-skeleton.html)
- Disagree and Commit / single-owner authority: Amazon principle, internalized via spec-kit
- Subagent context isolation: Codex delegated-agent context isolation; each subagent gets an independent context window and only the final report bubbles up to the orchestrator
- Tool-grounded verification (git/fs do not lie): doc-review SKILL.md anti-cheating rules
