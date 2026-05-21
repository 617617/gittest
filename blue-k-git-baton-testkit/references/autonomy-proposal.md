# Blue-K Baton — Two-AI Autonomy via Git

Status: draft
Author: CC (chat)
Depends on: `human-ergonomics-proposal.md` (P2.2 safe auto-advance whitelist)
Target protocol: v0.10 → v0.11

## Goal

Let CC and Codex advance the baton **without a human relay step**, using git itself as the message bus, while keeping every real decision human-gated.

Today the human:
1. Reads `bk sync` output.
2. Switches to the named AI chat window.
3. Pastes `/bk work`.
4. Waits for the AI to push.
5. Returns to step 1.

Steps 1–4 are pure relay. We remove them. Step 5 stays — but only fires at real decision points (consensus disagreement, takeover, BLOCK), not on every handoff.

## Non-goals

- **Not** removing human authority over: takeover, cross-side ownership transfer, consensus dispute, lower-gate BLOCK overrides, merge-to-main.
- **Not** rewriting the control-plane / business-plane split. Coordination branch + work branch stay as-is.
- **Not** adding a new control-truth source. Git remains the only one.
- **Not** introducing auto-merge, auto-rebase, or auto force-push.

## Core concept

```
                git push                       git push
   CC runtime  ─────────► origin/blue-k/coordination ◄───────── Codex runtime
       ▲                  (BATON.yaml + audit.log)                  ▲
       │                                                            │
       └────────── pulls & wakes on holder == self ──────────────────┘
```

Each AI side runs an **agent loop** that:
1. Fetches the coordination branch.
2. Reads `BATON.yaml`.
3. If `holder == self.lane` AND `status` is in the safe-advance whitelist → executes one assignment and pushes both branches atomically.
4. Otherwise sleeps.

Git is the only synchronization primitive. No extra service required for Phase 1.

## BATON.yaml additions

New fields the protocol must define before autonomy is turned on:

```yaml
# existing fields (lane, work_branch_head, status, ...)

autonomy:
  enabled: true                     # master switch; false = current human-relay mode
  kill_switch: false                # any actor flips to true → all AI loops stop on next tick
  cycle_count: 0                    # increments on every auto-advance
  cycle_limit: 50                   # hard cap; exceeded → BLOCK + notify human
  budget:
    tokens_used: 0
    tokens_limit: 2_000_000
    commits_pushed: 0
    commits_limit: 100
  last_actor: cc                    # cc | codex | human
  last_advance_at: 2026-05-21T14:30:00Z

human_authorized_by: null           # required non-null for: takeover, consensus override, BLOCK release
                                    # value is a git-verifiable signature or signed commit SHA
```

Plus a sibling `audit.log` file on the coordination branch — append-only, one line per advance:

```
2026-05-21T14:30:00Z  cc  plan-audit-pass  →  main-runner-ready  a1b2c3d
2026-05-21T14:31:12Z  codex  main-runner-ready  →  runner-checkpoint  d4e5f6a
```

## Safe-advance whitelist (must be defined in protocol)

| From state | To state | Allowed actor | Auto? |
|---|---|---|---|
| `planner-ready` | `plan-audit-pending` | CC | ✅ |
| `plan-audit-pass` | `main-runner-ready` | CC → Codex | ✅ |
| `main-runner-checkpoint` | `code-consensus-pending` | Codex | ✅ |
| `code-consensus-pass` | `main-runner-finalize` | Codex | ✅ |
| `other-runner-checkpoint` | `code-consensus-pending` | Codex | ✅ |
| anything → `takeover` | — | — | ❌ human only |
| anything → consensus override | — | — | ❌ human only |
| any `BLOCK` → release | — | — | ❌ human only |
| any → merge to main | — | — | ❌ human only |

If a transition is not in the whitelist, the AI runtime **must** stop and write `requires_human: <reason>` into BATON.

## Architecture A — local agent loop (Phase 1)

Two long-running processes on the user's machine (or a small VM). Coordinated entirely through `origin/blue-k/coordination`.

### Per-side runtime

```python
# pseudocode — same shape for CC and Codex sides
SELF_LANES = {"cc": ["blue-k-planner", "blue-k-plan-audit"],
              "codex": ["blue-k-main-runner", "blue-k-other-runner"]}[SELF]

while True:
    run("git fetch origin blue-k/coordination", quiet=True)
    baton = read_baton_yaml_from_remote_ref()

    if baton.autonomy.kill_switch:
        log("kill_switch tripped, exiting"); break
    if baton.autonomy.cycle_count >= baton.autonomy.cycle_limit:
        write_block(baton, "cycle_limit reached"); break
    if baton.autonomy.budget.over_limit():
        write_block(baton, "budget exceeded"); break

    if baton.holder in SELF_LANES[SELF] and baton.status in WHITELIST_FROM_STATES:
        next_state = WHITELIST_LOOKUP[baton.status]
        result = invoke_ai_headless(SELF, baton)        # claude --headless / codex headless
        baton = baton.advance_to(next_state,
                                 actor=SELF,
                                 cycle_count=baton.autonomy.cycle_count + 1)
        append_audit_log(baton, result)
        atomic_push(work_branch=result.work_branch_head,
                    coord_branch=baton)                  # --force-with-lease both
    else:
        sleep(15)
```

### Runtime choices

- **CC side**: `claude --headless` (Claude Code SDK) invoking the `blue-k-git-baton-testkit` skill with `/bk work` as initial input.
- **Codex side**: equivalent headless mode — **needs verification** that it exists with comparable git push capability. If not, fall back to a thin shim that calls Codex API in agent mode and applies its patches locally before pushing.
- Both processes live in tmux panes (or `systemd --user` services) on the same box for Phase 1. Cross-machine deferred to Phase 2.

### Atomic push

`atomic_push` must succeed or fail as a unit:

```bash
git push --atomic origin \
  blue-k/feat-x:blue-k/feat-x \
  blue-k/coordination:blue-k/coordination \
  --force-with-lease=blue-k/coordination:<expected-sha>
```

If atomic is unavailable on the remote → loop must refuse to advance and write `requires_human: atomic_push_unavailable`. This is already in the v0.9 protocol — autonomy just hits the condition more often.

### Kill switch UX

Human stops the world with one command:

```powershell
.\blue-k-git-baton-testkit\scripts\bk.ps1 stop
# → flips autonomy.kill_switch to true, pushes coordination branch, exits
```

Both AI loops notice on the next tick (≤15s) and exit. Restart with `bk.ps1 resume`.

## Guardrails — the must-haves before flipping `autonomy.enabled = true`

| Risk | Guardrail | Where implemented |
|---|---|---|
| Two AIs ping-pong a state forever | `cycle_limit` hard cap | BATON.yaml + runtime check |
| Runaway $$ | `tokens_limit` / `commits_limit` | BATON.yaml + runtime check |
| Concurrent push race | `--force-with-lease` + `--atomic` | runtime push step |
| Bad commit waved through self-review | Consensus + BLOCK rules unchanged; AI cannot release its own BLOCK | protocol invariant |
| Human can't stop it | `kill_switch` + `bk stop` | runtime first check each tick |
| Silent state corruption | Append-only `audit.log` per advance | runtime push step |
| Auth bypass | `human_authorized_by` required for takeover/override/BLOCK-release; absence → AI refuses | runtime precondition |
| Wrong AI claims a lane | `holder` field is the only entry gate; lane mismatch = no-op | runtime precondition |
| Loop survives a poisoned BATON | Schema validate BATON before acting; on parse error → exit + notify | runtime first step |

## Rollout plan

### Milestone 0 — Protocol v0.10 draft (no code changes)
- [ ] Add `autonomy`, `kill_switch`, `cycle_*`, `budget`, `human_authorized_by` to BATON schema in `protocol-v0.10.md`.
- [ ] Define the safe-advance whitelist table as a normative section.
- [ ] Define `audit.log` format.
- [ ] Update `scenario-matrix.md` with new autonomous-mode scenarios (cycle exhaustion, kill switch trip, budget exceeded, atomic push unavailable mid-loop).

**Exit criterion**: protocol reviewed; no implementation yet.

### Milestone 1 — Simulator coverage for autonomy
- [ ] Extend `scripts/bk_sync_sim.py` with an `--autonomy` mode that walks transitions per the whitelist and asserts:
  - cycle_limit halts the loop
  - kill_switch halts on next tick
  - non-whitelisted transition writes `requires_human`
  - atomic_push_unavailable writes `requires_human`
- [ ] All current v0.9 scenarios still pass.

**Exit criterion**: simulator green; no real network or AI calls yet.

### Milestone 2 — Architecture A prototype (single machine, single task)
- [ ] `scripts/bk_loop.ps1` — the agent loop wrapper (one per side).
- [ ] CC side wired to `claude --headless` invoking the testkit skill.
- [ ] Codex side: verify headless availability; if unavailable, document the gap and use a manual relay just for Codex side as Phase-1.5.
- [ ] `bk stop` / `bk resume` commands implemented.
- [ ] Run one full toy task (e.g. "add a `--version` flag to `bk.ps1`") end-to-end with no human relay between safe-advance steps.

**Exit criterion**: one task ships with human only touching the keyboard at: kickoff, consensus gates, finalization.

### Milestone 3 — Soak test
- [ ] Run 10 toy tasks back-to-back with autonomy enabled.
- [ ] Audit log inspected — no surprises, no near-misses on cycle_limit, no off-whitelist attempts.
- [ ] Budget numbers measured → set realistic defaults for production.

**Exit criterion**: confidence to use autonomy for a real task in this repo.

### Milestone 4 — Architecture B (GitHub Actions), only if needed
- [ ] Webhook → Action → headless AI invocation.
- [ ] Secrets management for API keys.
- [ ] Cross-machine becomes free.

Only pursue if A's "must keep two loops running locally" becomes painful.

## Concrete first-week tasks (small, sequenced)

1. **Day 1** — Draft `protocol-v0.10.md` (Milestone 0). Pure spec writing.
2. **Day 2** — Extend simulator with autonomy scenarios (Milestone 1).
3. **Day 3** — Verify Codex headless capabilities; document findings. **Blocking gate** — if Codex can't push from headless, Phase 1 stalls and the proposal shifts to a CC-only autonomous side with Codex still human-relayed.
4. **Day 4** — Implement `bk_loop.ps1` for CC side only. Hand-relay Codex side.
5. **Day 5** — Toy task end-to-end with CC autonomous, Codex manual. Measure friction reduction.
6. **Day 6** — If Day 3 cleared Codex headless: enable Codex loop too. Otherwise, finalize "CC-autonomous + Codex-manual" as the stable v0.10 mode.

## Open questions for the human

1. **Codex headless** — do you have a confirmed way to run Codex non-interactively with git push rights? This is the single biggest uncertainty; the whole plan branches on the answer.
2. **Where does the loop run?** — your dev machine (always on?), a small home-lab VM, or a cloud VM?
3. **Budget defaults** — what's an acceptable per-task token + commit ceiling for you?
4. **Kill switch UX** — `bk stop` is one option; would you also want a "panic" file (`touch .blue-k/STOP`) that any process can drop to halt both sides without git access?
5. **Should `autonomy.enabled` be per-task (in BATON.yaml of each work branch) or global (one env var)?** Per-task lets you A/B mode; global is simpler.

## Relationship to the ergonomics proposal

This document depends on `human-ergonomics-proposal.md` P2.2 (safe auto-advance whitelist). If autonomy is too risky, the ergonomics proposal still stands alone and delivers most of the human-burden reduction with zero new runtime. Autonomy is the second-stage rocket; ergonomics is the first.
