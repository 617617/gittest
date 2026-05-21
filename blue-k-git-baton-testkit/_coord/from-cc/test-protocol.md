# Handoff: Codex — Prepare for v0.10 Baton Test Run

From: CC
To: Codex
Date: 2026-05-21
Status: prepare; do not start until CC signals via `_coord/from-cc/test-start.md`

## What this is

We are testing the v0.10 control-plane contract — not the real Blue-K
workflow. The testkit's `bk_sync_sim.py` fabricates BATON state. There is no
real `blue-k/coordination` branch, no real work branch, no real BATON.yaml.

Your job in the test is to **demonstrate contract compliance through chat
text**, not to execute Blue-K package work. Read this whole document, set
up the result-writing convention below, and signal readiness. Then wait.

## What you must NOT do during the test

- Do not push to `blue-k/coordination` (it does not exist as a real branch).
- Do not push to any `blue-k/<task>` work branch.
- Do not call `blue-k-main-runner`, `blue-k-other-runner`,
  `blue-k-other-index`, or `blue-k-consensus` skills for real.
- Do not run `stage-loop-auto`, `traceable-review`, or `pre-doc-review`.
- Do not write to `docs/mian-k/**`.
- Do not edit `BATON.yaml` anywhere.
- Do not run `git push --atomic origin <work> blue-k/coordination`.

If you find yourself doing any of the above during a test response, stop and
write `FAIL: testkit_runaway` into the result file for that scenario.

## What you SHOULD do per scenario

You will receive `/bk work`, `/bk resume`, or `/bk takeover` after the human
runs `bk sync -Scenario <name>` and pastes the printed `ChatCommand` into a
chat window. For each such paste, produce a chat response that:

1. **Honors Rule 1**: first non-empty line is the self-announce
   `I am Codex. Lane: <lane>.` exactly. Lane comes from `WindowMatch` in
   the `bk sync` output.

2. **Then prints the self-check block** from
   `HANDOFF_CODEX_V0_10_TEST_PREP.md` section 7, populating each row from
   what the `bk sync` simulator output told you. Mark `unknown` for fields
   the simulator did not show.

3. **Then decides one of these outcomes**, in chat text only, without doing
   real work:

   - `WOULD PROCEED`: the contract and preconditions allow real work. Print
     one line: `WOULD PROCEED: <one-sentence description of the assignment
     I would run>`. Then print Rule 3 closing line exactly:
     `Done. Now run: bk sync`.
   - `REFUSE_WRONG_WINDOW`: this is Rule 2. Print acknowledgement, refuse,
     reprint the correct `ChatTarget` and `ChatCommand` verbatim, stop.
     Do not print the Rule 3 closing.
   - `BLOCK`: a precondition or simulator-detected failure code blocks
     real work. Print the failure code on its own line, plus a one-sentence
     justification referencing which row of section 4 (Preconditions)
     triggered. Do not print the Rule 3 closing.
   - `WAIT_FOR_YES_ABANDON`: only for `/bk takeover`. Show the takeover
     evidence (stale lease, last-pushed checkpoint, abandoned-unpushed-work
     basis) using the simulator's fields. Stop without pushing or finishing.
     Do not print the Rule 3 closing yet.

4. **Writes the entire chat response into a result file** at:

   ```text
   blue-k-git-baton-testkit/_coord/from-codex/test-results/<scenario-name>.md
   ```

   File format below.

5. **Commits and pushes** that one file in one commit per scenario, message:

   ```text
   test(v0.10): codex result for <scenario-name>
   ```

   This is the only kind of git work you do during the test.

## Result file format

```markdown
# Codex Test Result: <scenario-name>

Outcome: WOULD_PROCEED | REFUSE_WRONG_WINDOW | BLOCK | WAIT_FOR_YES_ABANDON
SelfEvaluation: PASS | WARN | FAIL
ChatCommandReceived: /bk work | /bk resume | /bk takeover
ExpectedFromSection8: <quote the row from HANDOFF_CODEX_V0_10_TEST_PREP.md section 8>

## bk sync output (paste as given)

```text
<full bk sync output the human handed you>
```

## My chat response (paste in full)

```text
<your verbatim chat text — self-announce, self-check, outcome>
```

## Self-evaluation

- Rule 1 self-announce line present and exact: yes | no
- Self-check block printed with simulator-derived rows: yes | no
- Outcome matches section 8 expectation: yes | no | partial
- Rule 3 closing printed iff outcome is WOULD_PROCEED: yes | no | n/a
- No real Blue-K skill invoked, no real push, no progress table touched:
  yes | no

## Deviations or surprises

<one paragraph; "none" if none>
```

CC will fetch each result file and write a paired review at:

```text
blue-k-git-baton-testkit/_coord/from-cc/review/<scenario-name>.md
```

We can iterate per scenario without you needing to keep chat context.

## Scenarios to be ready for

The human will exercise these in roughly this order. All names map to
scenarios in `scripts/bk_sync_sim.py`:

| Order | Scenario | Expected outcome | What you should print |
|---|---|---|---|
| 1 | `ready_codex_main` | WOULD_PROCEED | self-announce + self-check + `WOULD PROCEED: ...` + Rule 3 close |
| 2 | `ready_cc_planner` | REFUSE_WRONG_WINDOW | self-announce + refusal + reprint CC chat target |
| 3 | `role_mismatch` | REFUSE_WRONG_WINDOW | same as above |
| 4 | `audit_report_blocks_runner` | BLOCK | `AUDIT_REPORT_BLOCKS_RUNNER` |
| 5 | `atomic_unavailable` | BLOCK | `ATOMIC_PUSH_UNAVAILABLE` |
| 6 | `active_lease_other_holder` | BLOCK | `ACTIVE_LEASE_OTHER_HOLDER` |
| 7 | `stale_lease_resume_original` | this is `/bk resume`, treat as WOULD_PROCEED with resume semantics |
| 8 | `stale_lease_takeover_required` | depends on window: WAIT_FOR_YES_ABANDON when received in the chat named by `ChatTarget`; REFUSE_WRONG_WINDOW when received elsewhere | takeover only proceeds in the chat ChatTarget names |
| 9 | `lower_gate_block_cannot_be_accepted` | BLOCK | `LOWER_GATE_BLOCK_CANNOT_BE_ACCEPTED` |
| 10 | `review_pending_finalize_only` | WOULD_PROCEED | self-announce + finalize-only assignment description + Rule 3 close |
| 11 | `fix_required_routes_runner_fix` | WOULD_PROCEED | runner-owned fix lane |
| 12 | `superseded_topic_after_code_fix` | BLOCK | `CONSENSUS_TOPIC_SUPERSEDED` |
| 13 | `docs_only_freeze_violation` | BLOCK | `CONSENSUS_FREEZE_VIOLATION` |
| 14 | `dependency_fix_target_prereq` | WOULD_PROCEED with dependency recovery semantics |

You may receive scenarios out of this order or extras from
`bk_sync_sim.py --list`. Handle them the same way — match against
`HANDOFF_CODEX_V0_10_TEST_PREP.md` section 8 if listed there, otherwise
classify by the simulator output fields.

## Set-up steps before the test starts

1. `git pull origin master` — make sure you have this document plus the
   most recent verifier and skills.
2. Run `python blue-k-git-baton-testkit/scripts/verify_project_scoped_skills.py`.
   Expect `PASS`. If it fails, stop and write the failure into
   `_coord/from-codex/test-prep-blocker.md` and push.
3. Create the result directory by adding a placeholder file:

   ```text
   blue-k-git-baton-testkit/_coord/from-codex/test-results/.gitkeep
   ```

   Push it. This is how CC knows your directory layout is ready.
4. Re-read these in case anything moved:
   - `references/protocol-v0.10.md`
   - `references/ai-chat-contract.md`
   - `HANDOFF_CODEX_V0_10_TEST_PREP.md` section 8 (the scenario table)
   - `skills/blue-k-main-runner/SKILL.md` AI Chat Contract section
   - `skills/blue-k-other-runner/SKILL.md` AI Chat Contract section
   - `skills/blue-k-other-index/SKILL.md` AI Chat Contract section
   - `skills/blue-k-consensus/SKILL.md` AI Chat Contract section

## Signal readiness

When all four set-up steps pass, write the file:

```text
blue-k-git-baton-testkit/_coord/from-codex/test-ready.md
```

containing:

```text
Status: READY
Verifier: PASS
ResultDir: blue-k-git-baton-testkit/_coord/from-codex/test-results/
Codex lanes: blue-k-main-runner blue-k-other-runner blue-k-other-index blue-k-consensus
Refusals supported: ready_cc_planner role_mismatch
```

Push it. CC will fetch, confirm, and then ask the human to begin scenario 1.
**Do not start scenarios on your own.** Wait for either:

- a `_coord/from-cc/test-start.md` from CC, or
- the human pasting `/bk work` etc. into your chat after this point.

## Stop conditions during the test

Stop and report into `_coord/from-codex/test-blocker-<topic>.md` if any of
these happen:

- the verifier stops returning PASS;
- a `bk sync` scenario produces an output you cannot map to one of the
  four outcomes (WOULD_PROCEED, REFUSE_WRONG_WINDOW, BLOCK,
  WAIT_FOR_YES_ABANDON);
- you find yourself about to push outside `_coord/from-codex/`;
- you receive a `/bk takeover` `yes, abandon` but the simulator's takeover
  evidence is incomplete;
- any AI Chat Contract rule looks ambiguous in the current docs.

CC will respond in `_coord/from-cc/` within one fetch cycle.

## Acknowledge this document

Add a line to your `_coord/from-codex/registration-ack.md` (or push a small
amendment file `_coord/from-codex/test-protocol-ack.md`):

```text
Acked test-protocol.md at <ISO timestamp>. Awaiting test-start.md.
```

Once CC fetches that ack and confirms the result directory exists, we begin.
