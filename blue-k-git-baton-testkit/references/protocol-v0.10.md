# Blue-K Git Baton Protocol v0.10

This version extends v0.9 with a forget-safe human interface. The Git safety
model is unchanged: CC and Codex still coordinate only through Git, the
coordination branch is control truth, and the work branch is business truth.

## Forget-Safe Rule

At any point, the human may run only:

```text
bk sync
```

and receive one correct, non-destructive next action. No prior memory of role,
lane, resume state, takeover flags, or last handoff is required.

`bk sync` converts recall into recognition:

- print a one-line `NEXT`;
- print `Task`, `Holder`, and `Last`;
- print `ChatTarget` and `ChatCommand`;
- copy `ChatCommand` to the clipboard when the shell supports it;
- fail soft if clipboard is unavailable by still printing the command.

## User Surface

```text
bk sync   - shell command; safe sync, remote inspection, clipboard, decision sheet
/bk work  - normal AI chat execution command selected by bk sync
```

`/bk resume` and `/bk takeover` are short AI-chat verbs that `bk sync` may
print as `ChatCommand`. They are not additional commands the human must
remember.

Shell `bk work` is only a guard. If a user tries it, print that shell work does
not execute tasks and tell them to run `bk sync`, then paste its `ChatCommand`
into the named AI chat.

## Status Header

Every runnable `bk sync` decision must include:

```text
Task: <work branch or task id>
Holder: <CC|Codex> (<lane>) <state summary>
Last: <last pushed safe point>
ChatTarget: <target chat>
ChatCommand: </bk work|/bk resume|/bk takeover>
WindowMatch: paste into the chat whose first reply says Lane: <lane>
AfterWork: Done. Now run: bk sync
```

Blocked decisions must still include `NEXT: Do not run /bk work` plus the v0.9
failure evidence fields. They may set `ChatCommand: -`.

For `/bk takeover`, `WindowMatch` must name the takeover-confirming chat and
the lane being recovered. It must not imply ordinary runner execution before
the explicit `yes, abandon` confirmation.

## AI Chat Contract

Every AI chat that participates in the baton must self-announce on first reply:

```text
I am <CC|Codex>. Lane: <lane or owned lane set>.
```

When `/bk work`, `/bk resume`, or `/bk takeover` is pasted into the wrong AI
window, the AI must refuse to act and print the exact target window and command
that `bk sync` requires. Wrong-window input must not acquire a lease, edit
files, or run a Blue-K skill.

After one safe assignment, the AI must:

1. update and push the work branch and coordination branch atomically when
   supported;
2. write the next holder into BATON before signing off;
3. end with exactly:

```text
Done. Now run: bk sync
```

It must not chain into the next package or next lane in the same invocation.

## Resume And Takeover Verbs

`/bk resume` means same-holder recovery. It may re-enter the runner recovery
gate for matching dirty/unpushed same-holder state. It must not cross machines
or roles.

`/bk takeover` means cross-side takeover from the last pushed checkpoint only.
It replaces the long v0.9 flag chain:

```text
/bk work --takeover --from-last-pushed --abandon-unpushed-ok
```

The shorter verb does not relax safety. Before any destructive recovery, the
AI chat must show current remote evidence, the stale lease, the last pushed
checkpoint, and the abandoned-unpushed-work basis, then require the human to
type:

```text
yes, abandon
```

`LeaseExpiresAt` remains a hint only. A stale lease never authorizes automatic
takeover. A matching `running` or `review_pending` row is a takeover target,
not a blocker. A competing different running lane/package remains a blocker.

## Truth Sources

```text
blue-k/coordination  - control truth only
blue-k/<task>        - business truth only
```

`origin/blue-k/coordination:.blue-k/BATON.yaml` is the only control truth.
Work-branch copies of BATON are snapshots only and cannot authorize work.

Ordinary `/bk work` requires:

```text
local HEAD == origin/<work-branch> == BATON.WorkBranchHead
working tree clean, including untracked non-ignored files
BK_ROLE == BATON.OwnerRole
no active competing lease
```

Unattended completion must push the work branch and coordination branch
atomically:

```text
git push --atomic origin <work-branch> blue-k/coordination
```

If the remote cannot guarantee atomic push, stop with
`ATOMIC_PUSH_UNAVAILABLE`.

## Ownership Boundaries

The wrapper may:

- fetch remote refs;
- read BATON, progress, audit, review, and consensus artifacts;
- acquire a coordination lease through compare-and-swap;
- call the correct Blue-K skill in the correct chat window;
- publish one final handoff after the underlying skill reaches a safe point.

The wrapper must not:

- select packages;
- write progress tables;
- run `stage-loop-auto`;
- run code graph package gates;
- create runner checkpoint commits;
- convert lower-gate `BLOCK` to `PASS`;
- merge, rebase, force push, or auto-takeover across machines.

`blue-k-main-runner` and `blue-k-other-runner` own package selection, resume,
fix lanes, progress-table writes, package gates, and checkpoint commits.

## Consensus Rules

Every plan output needs one comprehensive discussion/synthesis before runner
execution. Every code/package output needs one comprehensive review/synthesis
before runner finalization.

Consensus is synthesis, not a bypass:

- `blue-k-plan-audit BLOCK` returns to planner repair.
- Traceable review / code graph / package gate `BLOCK` returns to runner fix.
- Human `accept_risk` may accept only lower-gate PASS or explicitly accepted
  WARN. It cannot override lower-gate BLOCK.
- Waiver means "allow missing substitute input"; it is not a PASS opinion.
- Waiver/substitute cases cannot use light auto-accept.

Between `SubjectCommit` and `AcceptanceCommit`, only files under:

```text
docs/mian-k/_consensus/<topic-id>/**
```

may change. Any new subject commit supersedes the previous consensus topic.

## Runner State Machine

```text
running -> review_pending
review_pending + accepted consensus -> runner finalize -> done
review_pending + fix_required -> runner fix lane -> new checkpoint -> review_pending
review_pending + human_blocked -> wait human decision
review_failed -> retry_fix | planner_repair | human_blocked
```

Runner finalization is its own assignment. It marks the current
`review_pending` row done and stops. It must not start the next package in the
same chat invocation.

## Auto-Advance

v0.10 does not enable automatic cross-window work. Future auto-advance may be
considered only through a signed whitelist, and only for pure relay transitions
where all lower gates have already passed. Takeover, consensus gate decisions,
BLOCK resolution, human-blocked states, and abandoned-unpushed-work recovery
remain human-gated.

The draft `references/autonomy-proposal.md` explores a v0.11 agent-loop model
that depends on this section. It is not active in v0.10.

## Required Failure Fields

Blocked `bk sync` output must include:

```text
NEXT:
FailureCode:
Lane:
ProgressFile:
ProgressIndex:
ProgressStatus:
BatonState:
LeaseToken:
RemoteHead:
LastPushedCommit:
LastLocalCommit:
UnpushedCommits:
LocalDirty:
RemoteTakeoverAllowed:
TakeoverBasis:
Next command:
Log path:
```

Consensus-related output should also include:

```text
ConsensusKind:
ConsensusMode:
ConsensusStatus:
TopicStatus:
SubjectCommit:
AcceptanceSubjectCommit:
AutoAccepted:
FixTarget:
ActivePackage:
DependencyRecoveryTarget:
FindingSetCommit:
```
