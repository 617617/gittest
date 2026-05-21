# Codex Test Result: superseded_topic_after_code_fix

Outcome: BLOCK
SelfEvaluation: PASS
ChatCommandReceived: - (none; bk sync said Do not run /bk work)
ExpectedFromSection8: `superseded_topic_after_code_fix` | Reject the old acceptance; topic is stale

## bk sync output (paste as given)

```text
DeveloperDiagnostic: -Scenario is for internal debugging; user tests should use bk sync or bk sync -Coverage
SCENARIO: superseded_topic_after_code_fix
------------------------------------------------------------------------
NEXT: Do not run /bk work
Task: blue-k/k1
Holder: Codex (blue-k-main-runner) state=ready; progress=review_pending
Last: origin/blue-k/k1@1111111
ChatTarget: -
ChatCommand: -
HERE: BK_ROLE=codex
WHY: a newer SubjectCommit superseded this consensus topic
UNIT: runner finalize current review_pending row only, then stop
LOCK: no active lease
SAFE_POINT: origin/blue-k/k1@1111111
STOP_IF: blocked until failure is resolved
ConsensusKind: code
ConsensusMode: light
ConsensusStatus: accepted
TopicStatus: superseded
SubjectCommit: 3333333
AcceptanceSubjectCommit: 1111111
AutoAccepted: false
ReviewStatus: review_pending
ProgressRowId: main:03
FailureCode: CONSENSUS_TOPIC_SUPERSEDED
Lane: blue-k-main-runner
ProgressFile: docs/mian-k/MAIN_PACKAGE_PROGRESS.md
ProgressIndex: -
ProgressStatus: review_pending
BatonState: ready
LeaseToken: -
RemoteHead: 1111111
LastPushedCommit: 1111111
LastLocalCommit: 1111111
UnpushedCommits: none
LocalDirty: false
RemoteTakeoverAllowed: no
TakeoverBasis: not requested
Next command: -
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
  competing lease:     no active lease
  atomic push:         unknown
  audit verdict:       unknown
  consensus state:     accepted

CONSENSUS_TOPIC_SUPERSEDED
BLOCK: the consensus topic is superseded by a newer SubjectCommit.
```

## Self-evaluation

- Rule 1 self-announce line present and exact: yes
- Self-check block printed with simulator-derived rows: yes
- Outcome matches section 8 expectation: yes
- Rule 3 closing printed iff outcome is WOULD_PROCEED: yes
- No real Blue-K skill invoked, no real push, no progress table touched:
  yes

## Deviations or surprises

none
