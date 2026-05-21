# Codex Test Result: stale_lease_takeover_required

Outcome: REFUSE_WRONG_WINDOW
SelfEvaluation: WARN
ChatCommandReceived: /bk takeover
ExpectedFromSection8: `stale_lease_takeover_required` | If `ChatTarget` is CC, refuse as wrong-window; if `ChatTarget` is Codex, show takeover evidence and wait for `yes, abandon`

## bk sync output (paste as given)

```text
DeveloperDiagnostic: -Scenario is for internal debugging; user tests should use bk sync or bk sync -Coverage
SCENARIO: stale_lease_takeover_required
------------------------------------------------------------------------
NEXT: In CC chat, send: /bk takeover
Task: blue-k/k1
Holder: Codex (blue-k-main-runner) stale lease; progress=running
Last: origin/blue-k/k1@1111111
ChatTarget: CC chat
ChatCommand: /bk takeover
WindowMatch: paste into the CC takeover chat; it must show takeover basis for Lane: blue-k-main-runner
AfterWork: Done. Now run: bk sync
HERE: BK_ROLE=cc
WHY: stale lease; takeover resumes only from last pushed checkpoint
UNIT: blue-k-main-runner will select/resume from MAIN_PACKAGE_PROGRESS.md
LOCK: stale lease held by codex/machine-z
SAFE_POINT: origin/blue-k/k1@1111111
STOP_IF: do not use local unpushed work from the unavailable holder
TakeoverConfirmation: AI chat must require "yes, abandon" after showing current remote evidence
FailureCode: STALE_LEASE_TAKEOVER_EXPLICIT
Lane: blue-k-main-runner
ProgressFile: docs/mian-k/MAIN_PACKAGE_PROGRESS.md
ProgressIndex: 03
ProgressStatus: running
BatonState: ready
LeaseToken: sim-token
RemoteHead: 1111111
LastPushedCommit: 1111111
LastLocalCommit: 1111111
UnpushedCommits: none
LocalDirty: false
RemoteTakeoverAllowed: yes
TakeoverBasis: matching running row from last pushed checkpoint
Next command: /bk takeover
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
  competing lease:     stale lease held by codex/machine-z
  atomic push:         available
  audit verdict:       unknown
  consensus state:     none

REFUSE_WRONG_WINDOW: This Codex chat must not advance the baton for the selected target/context.
Refusal basis: bk sync selected CC chat, not this Codex execution context.
Correct ChatTarget: CC chat
Correct ChatCommand: /bk takeover
WindowMatch: paste into the CC takeover chat; it must show takeover basis for Lane: blue-k-main-runner
```

## Self-evaluation

- Rule 1 self-announce line present and exact: yes
- Self-check block printed with simulator-derived rows: yes
- Outcome matches section 8 expectation: partial
- Rule 3 closing printed iff outcome is WOULD_PROCEED: yes
- No real Blue-K skill invoked, no real push, no progress table touched:
  yes

## Deviations or surprises

Cross-document tension: test-protocol.md scenario table says WAIT_FOR_YES_ABANDON, but HANDOFF_CODEX_V0_10_TEST_PREP.md section 8 says to refuse when ChatTarget is CC. This result follows the newer section-8 rule and marks WARN rather than FAIL.
