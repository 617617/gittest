# Blue-K Git Baton Protocol v0.5

This protocol is a testable control-plane wrapper for cross-machine CC/Codex
coordination. It is designed for the DND backend Blue-K workflow, but this
testkit runs only lightweight simulations.

## Entries

```text
bk sync   - shell command, read-only remote inspection
/bk work  - AI chat command, assignment execution wrapper
```

Shell `bk work` must not execute Blue-K work. It may print:

```text
Send /bk work in the CC or Codex chat window named by bk sync.
```

## Branches

```text
blue-k/coordination  - control state only
blue-k/<task>        - business work branch
```

Only `origin/blue-k/coordination:.blue-k/BATON.yaml` is the control truth.
Work-branch copies of BATON are snapshots only and cannot authorize work.

The work branch is the business truth source: docs, progress tables, evidence,
runner checkpoint commits, and simulated source changes live there.

## Required Remote Protections

Both branches must reject:

- force push;
- branch delete;
- non-fast-forward rewrite.

Unattended work also requires remote support for atomic push:

```text
git push --atomic origin <work-branch> blue-k/coordination
```

If atomic push is unavailable, stop with `ATOMIC_PUSH_UNAVAILABLE`.

## Ordinary Start Gate

Before ordinary `/bk work`:

```text
git fetch origin
local HEAD == origin/<work-branch> == BATON.WorkBranchHead
working tree clean, including untracked non-ignored files
BK_ROLE matches BATON.OwnerRole
no active competing lease
```

If `origin/<work-branch> != BATON.WorkBranchHead`, stop with
`REMOTE_WORK_HEAD_CHANGED`.

## Lease Gate

Acquire a lease only through CAS on `blue-k/coordination`:

1. Fetch coordination branch.
2. Read current coordination head.
3. Write structured BATON lease commit with the observed head.
4. Push to the same coordination branch.
5. If push is rejected, exit. Another actor won.

Coordination branch read/write must use an isolated coordination worktree or
Git plumbing. The execution worktree must never checkout the coordination
branch and must not contain dirty `.blue-k/BATON.yaml` before runner lanes.

## Assignment Loop

`/bk work` may run multiple same-side assignments, but every assignment must
finish with a pushed safe point and a fresh lease cycle.

Each loop:

```text
fetch remote refs
read BATON from origin/blue-k/coordination
verify work branch head against BATON.WorkBranchHead
acquire fresh lease by CAS
run exactly one assignment
atomic push work branch plus coordination handoff
refetch before deciding whether to continue
```

Do not cache package lists or progress-table decisions across loops.

## Lanes

```text
blue-k-planner
blue-k-plan-audit
blue-k-main-runner
blue-k-other-runner
```

CC normally owns planner/audit/review lanes. Codex normally owns main/other
runner lanes.

### Planner Lane

Requires durable human authorization:

```yaml
AuthorizedAction: inspect_only | plan_next_requested | advance_requested
```

No authorization means inspect only.

Plan Next must complete its mandatory `blue-k-plan-audit` gate or stop as:

```text
PLAN_NEXT_BLOCKED_AUDIT_PENDING
```

This is not runner-ready.

### Audit Lane

Use for:

- audit continuation after planner interruption;
- plan-audit recovery/rerun;
- legacy plan audit.

### Main Runner Lane

The wrapper must not preselect packages. It must call the runner with:

```text
Run exactly one selected/resumed package only, then stop after the runner-owned
clean checkpoint gate. Refresh and select/resume from MAIN_PACKAGE_PROGRESS.md
yourself.
```

The runner owns progress table writes, stage-loop-auto invocation, subagents,
code graph package gate, and full-repository clean checkpoint commit.

### Other Runner Lane

The wrapper must not preselect packages. It must call the runner with:

```text
Run exactly one selected/resumed other package only, plus runner-owned
dependency recovery if required, then stop after the runner-owned clean
checkpoint gate. Refresh and select/resume from OTHER_MIN_PACKAGE_PROGRESS.md
yourself.
```

During dependency recovery, display both the active selected package and the
dependency recovery target.

## Takeover

`LeaseExpiresAt` is a hint only. It does not authorize takeover.

Same-holder resume may use local dirty/unpushed state only by re-entering the
runner recovery gate.

Cross-side takeover can only resume from the last pushed work-branch checkpoint
and requires an explicit command:

```text
/bk work --takeover --from-last-pushed --abandon-unpushed-ok
```

A matching `running` row is a takeover target, not a blocker. A competing
different running lane/package is a blocker.

## Sync Decision Sheet

`bk sync` must read remote content, not local stale files. First line must be
the only recommended action.

```text
NEXT: In Codex chat, send: /bk work
HERE: BK_ROLE=cc
WHY: BATON Owner=codex; audit verdict=PASS; main progress has pending package
UNIT: blue-k-main-runner will select/resume from MAIN_PACKAGE_PROGRESS.md
LOCK: no active lease
SAFE_POINT: origin/blue-k/k1@<sha>
STOP_IF: local dirty, branch mismatch, remote head changed
```

Failure output must include:

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
