# Codex Test Result: stale_lease_resume_original

Outcome: WOULD_PROCEED
SelfEvaluation: PASS
ChatCommandReceived: /bk resume
ExpectedFromSection8: `stale_lease_resume_original` | Tell human to use `/bk resume` in original holder chat; test-protocol scenario 7 treats received `/bk resume` as WOULD_PROCEED with resume semantics

## bk sync output (paste as given)

```text
DeveloperDiagnostic: -Scenario is for internal debugging; user tests should use bk sync or bk sync -Coverage
SCENARIO: stale_lease_resume_original
------------------------------------------------------------------------
NEXT: Resume in original holder chat: /bk resume
Task: blue-k/k1
Holder: Codex (blue-k-main-runner) stale lease; progress=pending
Last: origin/blue-k/k1@1111111
ChatTarget: original holder chat
ChatCommand: /bk resume
WindowMatch: paste into the chat whose first reply says Lane: blue-k-main-runner
AfterWork: Done. Now run: bk sync
HERE: BK_ROLE=codex
WHY: matching holder should re-enter runner recovery gate
UNIT: blue-k-main-runner will select/resume from MAIN_PACKAGE_PROGRESS.md
LOCK: stale lease held by codex/machine-a
SAFE_POINT: origin/blue-k/k1@1111111
STOP_IF: wrapper must not repair dirty state directly
FailureCode: STALE_LEASE_SAME_HOLDER
Lane: blue-k-main-runner
ProgressFile: docs/mian-k/MAIN_PACKAGE_PROGRESS.md
ProgressIndex: -
ProgressStatus: pending
BatonState: ready
LeaseToken: sim-token
RemoteHead: 1111111
LastPushedCommit: 1111111
LastLocalCommit: 1111111
UnpushedCommits: none
LocalDirty: false
RemoteTakeoverAllowed: no
TakeoverBasis: same holder recovery preferred
Next command: /bk resume
Log path: blue-k-git-baton-testkit/logs/simulated.log
```

## My chat response (paste in full)

```text
I am Codex. Lane: blue-k-main-runner.
self-check:
  lane:                blue-k-main-runner
  BATON.OwnerRole:     Codex
  WorkBranchHead:      1111111
  origin/<work>:       origin/blue-k/k1@1111111
  local HEAD:          1111111
  worktree clean:      yes
  competing lease:     stale lease held by codex/machine-a
  atomic push:         available
  audit verdict:       unknown
  consensus state:     none

WOULD PROCEED: I would re-enter the original Codex holder's blue-k-main-runner resume gate from the last pushed safe point, without auto-cleaning local state.
Done. Now run: bk sync
```

## Self-evaluation

- Rule 1 self-announce line present and exact: yes
- Self-check block printed with simulator-derived rows: yes
- Outcome matches section 8 expectation: yes
- Rule 3 closing printed iff outcome is WOULD_PROCEED: yes
- No real Blue-K skill invoked, no real push, no progress table touched:
  yes

## Deviations or surprises

Section 8 phrases this as telling the human to use /bk resume; this result exercises the post-paste /bk resume path requested by test-protocol.md.
