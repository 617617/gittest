# Handoff: Codex Test-Prep for Blue-K Baton v0.10

Audience: the Codex agent that will participate in v0.10 baton testing on the
617617/gittest repository.

Purpose: a single document the human can hand to Codex so that, after Codex
reads it, Codex is fully prepared to run, refuse, resume, take over, and
finalize one safe assignment without further instruction.

If this document and `references/protocol-v0.10.md` disagree on any normative
rule, the protocol wins. This document is a preparation checklist, not a new
spec.

## 1. Identity and scope

You are Codex. In Blue-K baton terms, you own these lanes:

```text
blue-k-main-runner
blue-k-other-runner
blue-k-other-index
```

You do not own:

```text
blue-k-planner          (CC / Claude lane)
blue-k-plan-audit       (CC / Claude lane)
```

If `bk sync` selects a CC lane, you must refuse to act and tell the human to
paste the printed `ChatCommand` into the CC chat. See Rule 2 below.

## 2. Read these files, in this order, before doing anything

```text
AGENTS.md
blue-k-git-baton-testkit/SKILL.md
blue-k-git-baton-testkit/HANDOFF.md
blue-k-git-baton-testkit/HANDOFF_BLUE_K_WORKFLOW_SKILL_BUNDLE.md
blue-k-git-baton-testkit/references/protocol-v0.10.md
blue-k-git-baton-testkit/references/ai-chat-contract.md
blue-k-git-baton-testkit/references/scenario-matrix.md
```

Then read your lane SKILL.md when an assignment lands:

```text
blue-k-git-baton-testkit/skills/blue-k-main-runner/SKILL.md
blue-k-git-baton-testkit/skills/blue-k-other-runner/SKILL.md
blue-k-git-baton-testkit/skills/blue-k-other-index/SKILL.md
```

Each of those lane skills now contains an `AI Chat Contract (v0.10)` section
at the top. The three rules in that section are the same three rules
restated below. Do not skip them.

## 3. On every invocation: three hard rules

These are normative in `references/ai-chat-contract.md`. The summaries here
are operational reminders — if anything conflicts, the canonical file wins.

### Rule 1 — First reply self-announce

Before any tool call, before any repo read, before reading BATON, your first
non-empty reply line must be exactly:

```text
I am Codex. Lane: <one of: blue-k-main-runner | blue-k-other-runner | blue-k-other-index>.
```

If the invocation legitimately owns more than one of these lanes in the same
session, list them space-separated on the same line. Do not invent lanes.
Do not abbreviate.

The human matches this line to the `WindowMatch` hint printed by `bk sync` to
confirm the paste landed in the correct window. If the human does not see
this line, they will treat the paste as broken.

### Rule 2 — Refuse wrong-window input

You may receive `/bk work`, `/bk resume`, or `/bk takeover` in a chat the
latest `bk sync` did not select. This happens when the human pastes into the
wrong window. When it happens you must:

1. Print Rule 1 self-announce as usual so the human can see what window they
   pasted into.
2. Acknowledge the wrong-window paste in plain words.
3. Refuse to acquire a coordination lease, refuse to edit files, refuse to
   call any Blue-K skill, refuse to write progress tables, refuse to push.
4. Reprint, verbatim where possible, the most recent `bk sync` `ChatTarget`,
   `WindowMatch`, and `ChatCommand` so the human can re-paste correctly.
5. Stop.

For `/bk takeover` in the correct window, you may show takeover evidence on
the first reply (stale lease, last pushed checkpoint, abandoned-unpushed-work
basis) but you must not commit, push, or write progress until the human
types exactly `yes, abandon` in this chat.

### Rule 3 — Finalize with the fixed closing line

After completing exactly one safe assignment:

1. Push work branch and coordination branch atomically:

   ```text
   git push --atomic origin <work-branch> blue-k/coordination
   ```

   If the remote refuses or does not guarantee atomic push, stop with
   `ATOMIC_PUSH_UNAVAILABLE`. Do not push. Do not mark the assignment done.
   Do not print the closing line.

2. Write the next holder into `BATON.yaml` on the coordination branch before
   signing off.

3. End your reply with this line, byte-for-byte, as the final non-empty line:

   ```text
   Done. Now run: bk sync
   ```

   No emojis, no trailing punctuation, no follow-up sentence.

Do not chain into the next package, lane, or assignment in the same
invocation, even if the BATON state would allow it. The human re-enters
through `bk sync`.

## 4. Preconditions before you do real work

Even after Rules 1–3, do not advance state unless all of these hold. If any
fails, stop with the matching failure code and print it on its own line.

| Check | Failure code on mismatch |
|---|---|
| `BK_ROLE == BATON.OwnerRole` and `OwnerRole` is one of your lanes | `ROLE_MISMATCH` |
| `local HEAD == origin/<work-branch> == BATON.WorkBranchHead` | `LOCAL_HEAD_NOT_AT_REMOTE` or `REMOTE_WORK_HEAD_CHANGED` |
| Working tree clean, including untracked non-ignored files | `LOCAL_DIRTY_ORDINARY_START` |
| No competing active lease on a different lane | `ACTIVE_LEASE_OTHER_HOLDER` |
| Atomic push available for work branch plus coordination branch | `ATOMIC_PUSH_UNAVAILABLE` |
| No lower-gate `BLOCK` pending acceptance | `LOWER_GATE_BLOCK_CANNOT_BE_ACCEPTED` |
| Audit verdict is not `BLOCK` and not `PENDING` | `AUDIT_REPORT_BLOCKS_RUNNER` / `PLAN_NEXT_BLOCKED_AUDIT_PENDING` |
| Consensus topic has not been superseded by a newer subject commit | `CONSENSUS_TOPIC_SUPERSEDED` |

The wrapper (`bk.ps1`) and the simulator (`bk_sync_sim.py`) already detect
most of these and print `NEXT: Do not run /bk work` when they fail. Your
job is to re-check them inside the chat before acting, because the wrapper
runs once and the chat may have been opened later.

## 5. Boundaries — never do these

These belong to other actors. Doing them from your chat invalidates the
baton:

- Do not select packages inside the outer wrapper.
- Do not write progress tables from the wrapper. Use only:
  - `blue-k-git-baton-testkit/skills/blue-k-main-runner/scripts/main_progress.py`
  - `blue-k-git-baton-testkit/skills/blue-k-other-index/scripts/other_progress.py`
- Do not invoke `stage-loop-auto` directly from the main agent.
- Do not run code graph package gates from the wrapper.
- Do not create runner checkpoint commits from the wrapper.
- Do not auto-merge, auto-rebase, force-push, or auto-takeover across sides.
- Do not convert lower-gate `BLOCK` to `PASS`.
- Do not write outside `docs/mian-k/_consensus/<topic-id>/` between
  `SubjectCommit` and `AcceptanceCommit`.
- Do not ask the human to run raw `git pull` during normal operation.

If a request would require any of the above, refuse and explain which rule
blocks it.

## 6. Headless mode via `codex exec`

When the human invokes you through `codex exec` instead of an interactive
chat, the three rules above still apply, mapped as follows:

- Rule 1 (self-announce): print the `I am Codex. Lane: <lane>.` line as the
  first line of the `--output-last-message` file. The wrapper reads that
  file and verifies the line.
- Rule 2 (wrong-window refuse): there is no chat window, but the wrapper
  selects the prompt. If you detect that the prompt's lane disagrees with
  `BATON.OwnerRole`, write the wrong-window refusal text into
  `--output-last-message` and exit non-zero.
- Rule 3 (closing line): the final non-empty line of
  `--output-last-message` must be `Done. Now run: bk sync`.

The shell wrapper owns the final push decision even in headless mode. Your
self-reported "I pushed" is not evidence. Expected invocation shape:

```powershell
Get-Content .blue-k\unattended_prompt.md |
  codex exec - `
    --cd . `
    --sandbox workspace-write `
    --ask-for-approval never `
    --json `
    --output-last-message .blue-k\unattended_result.md
```

Prefer `workspace-write`. Use `danger-full-access` only inside an isolated
runner or VM. Never commit or print credentials, tokens, or auth files.

Headless mode is for safe assignments only. Do not run headless when any of
these are present (the wrapper should refuse to launch you, but you must
also refuse to act if you observe them):

- `/bk takeover` semantics requested;
- audit `WARN` requiring human risk acceptance;
- lower-gate `BLOCK`;
- code graph high-risk overlay change;
- conflict, divergence, dirty worktree, missing upstream;
- credentials or destructive filesystem scope;
- ambiguous assignment scope.

## 7. Self-check before you act

Print this short block on the second reply (after Rule 1) when you start a
real assignment. It gives the human one line to verify each precondition:

```text
self-check:
  lane:                <your lane>
  BATON.OwnerRole:     <value>
  WorkBranchHead:      <BATON value>
  origin/<work>:       <git value>
  local HEAD:          <git value>
  worktree clean:      <yes|no>
  competing lease:     <none|details>
  atomic push:         <available|unavailable>
  audit verdict:       <PASS|WARN-accepted|BLOCK|PENDING>
  consensus state:     <none|needed|accepted|fix_required|human_blocked>
```

If any row would force a failure code from section 4, do not proceed past
this block. Print the failure code and stop.

## 8. Test scenarios you must handle

The human will exercise these by running:

```powershell
.\blue-k-git-baton-testkit\scripts\bk.ps1 sync
.\blue-k-git-baton-testkit\scripts\bk.ps1 sync -Coverage
.\blue-k-git-baton-testkit\scripts\bk.ps1 work
```

You must give correct behavior for each `bk sync` decision below. Every one
of them appears in `scripts/bk_sync_sim.py` and
`references/scenario-matrix.md`.

| Scenario family | Your required behavior |
|---|---|
| `ready_codex_main` | Rule 1, self-check, then one main-runner assignment, Rule 3 |
| `ready_cc_planner` | Rule 2 refusal — this is CC's lane |
| `role_mismatch` | Rule 2 refusal — the BATON owner is not you |
| `audit_pending_blocks_runner` | Print failure code; do not act |
| `audit_report_blocks_runner` | Print failure code; do not act |
| `work_head_mismatch` / `local_behind_origin` | Print failure code; do not act |
| `atomic_unavailable` | Stop with `ATOMIC_PUSH_UNAVAILABLE` |
| `active_lease_other_holder` | Print failure code; do not act |
| `stale_lease_resume_original` | Tell human to use `/bk resume` in original holder chat |
| `stale_lease_takeover_required` | Show takeover evidence; wait for `yes, abandon` |
| `same_holder_dirty_resume` | Re-enter runner recovery gate; do not auto-clean |
| `competing_running_conflict` | Block, even on takeover request |
| `other_dependency_recovery` | Show `DependencyRecoveryTarget`; honor the fix-target ownership |
| `review_pending_finalize_only` | Finalize only the current row; do not start the next package |
| `fix_required_routes_runner_fix` | Open the runner-owned fix lane; new checkpoint creates a new topic |
| `superseded_topic_after_code_fix` | Reject the old acceptance; topic is stale |
| `lower_gate_block_cannot_be_accepted` | Refuse — lower-gate `BLOCK` cannot be `PASS` |
| `consensus_dirty_blocks_runner` | Refuse — dirty/unpushed consensus draft cannot authorize start |
| `docs_only_freeze_violation` | Refuse — only the topic dir may change between subject and acceptance |
| `human_blocked_request_*` | Open the requested lane; create a new topic |

## 9. What "ready for test" looks like

Before the human runs the first `bk sync`, confirm each item:

- [ ] You have pulled the latest `master` of 617617/gittest.
- [ ] You have read every file in section 2.
- [ ] You have read your three lane SKILL.md files.
- [ ] You can print the Rule 1 line for each lane.
- [ ] You know the exact byte-for-byte closing line for Rule 3.
- [ ] You can list every failure code in section 4 from memory and know
      which condition triggers it.
- [ ] If you run headless, you have `codex exec` available on PATH and a
      writable `.blue-k\unattended_result.md` location.

Acknowledge to the human by replying with exactly:

```text
I am Codex. Lane: blue-k-main-runner blue-k-other-runner blue-k-other-index.
v0.10 test-prep acknowledged.
```

That single message tells the human you read this document, you can produce
the Rule 1 line, and you are ready for `bk sync` to drive the first test.

Do not start any baton work in that acknowledgement message. Wait for the
human to run `bk sync` and paste the printed `ChatCommand`.
