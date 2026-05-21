# Codex Test Result: role_mismatch

DecisionRevision: 3
Outcome: REFUSE_WRONG_WINDOW
SelfEvaluation: PASS
ChatCommandReceived: /bk work
ExpectedFromSection8: `role_mismatch` | Rule 2 refusal - the BATON owner is not you

## bk sync output (paste as given)

```text
DeveloperDiagnostic: -Scenario is for internal debugging; user tests should use bk sync or bk sync -Coverage
SCENARIO: role_mismatch
------------------------------------------------------------------------
NEXT: In Codex chat, send: /bk work
Task: blue-k/k1
Holder: Codex (blue-k-main-runner) state=ready; progress=pending
Last: origin/blue-k/k1@1111111
ChatTarget: Codex chat
ChatCommand: /bk work
WindowMatch: paste into the chat whose first reply says Lane: blue-k-main-runner
AfterWork: Done. Now run: bk sync
HERE: BK_ROLE=cc
WHY: BATON Owner=codex; current role is cc
UNIT: blue-k-main-runner will select/resume from MAIN_PACKAGE_PROGRESS.md
LOCK: no active lease
SAFE_POINT: origin/blue-k/k1@1111111
STOP_IF: do not run from the wrong role window
```

## My chat response (paste in full)

```text
I am Codex. Lane: blue-k-main-runner blue-k-other-runner blue-k-other-index blue-k-consensus.
self-check:
  lane:                blue-k-main-runner
  BATON.OwnerRole:     Codex
  WorkBranchHead:      1111111
  origin/<work>:       origin/blue-k/k1@1111111
  local HEAD:          1111111
  worktree clean:      yes
  competing lease:     no active lease
  atomic push:         available
  audit verdict:       PASS
  consensus state:     none

REFUSE_WRONG_WINDOW: This Codex chat must not advance the baton because the simulator context says HERE: BK_ROLE=cc.
Correct ChatTarget: Codex chat
Correct ChatCommand: /bk work
WindowMatch: paste into the chat whose first reply says Lane: blue-k-main-runner
```

## Self-evaluation

- Rule 1 self-announce line present and exact: yes
- Self-check block printed with simulator-derived rows: yes
- Outcome matches section 8 expectation: yes
- Rule 3 closing printed iff outcome is WOULD_PROCEED: yes
- No real Blue-K skill invoked, no real push, no progress table touched:
  yes

## Deviations or surprises

DecisionRevision 3 changed the Rule 1 convention after scenario 2. This result announces Codex-owned lanes rather than the requested lane, even though `WindowMatch` names only `blue-k-main-runner`.
