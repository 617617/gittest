# temporal-phase — BATON state schema

The baton state machine for this preset. Every product file's first line
`BatonNext: <STATE>` declares the transition target; readers advance the
baton based on that line. State names are SCREAMING_SNAKE_CASE with a
semantic suffix to distinguish rounds and optional branches.

## State enumeration

```text
DRAFTING_BLUEPRINT             # Codex is drafting the blueprint, not yet delivered
PRE_AUDIT_R1                   # round 1 pre-execution audit (CC + Codex in parallel)
PRE_AUDIT_SYNTHESIS_R1         # CC synthesizes round 1
BLUEPRINT_REVISION_R1          # CC repairs blueprint after round 1
PRE_AUDIT_R2                   # round 2 (if needed)
PRE_AUDIT_SYNTHESIS_R2
BLUEPRINT_REVISION_R2
PRE_AUDIT_R3                   # round 3 (if needed; this is the cap)
PRE_AUDIT_SYNTHESIS_R3
BLUEPRINT_REVISION_R3
BLUEPRINT_ACCEPTED             # blueprint passed the pre-execution audit
EXECUTING                      # Codex is executing the Phase
EXECUTION_REPORTED             # Codex delivered the execution report
POSTEXEC_SUBAGENT_REVIEW       # Codex multi-subagent integrated review
POSTEXEC_CC_REVIEW             # CC post-execution independent review
POSTEXEC_SYNTHESIS             # Codex synthesizes the two post-exec audits
POSTEXEC_FIX                   # Codex absorbs and repairs
SECOND_AUDIT_DECISION          # Codex decides whether to run the second dual audit
SECOND_AUDIT_CC                # (optional) second dual audit, CC side
SECOND_AUDIT_CODEX             # (optional) second dual audit, Codex side
SECOND_AUDIT_FIX               # (optional) repair after the second dual audit
PHASE_CLOSING                  # Codex is checking the completion criteria
COMPLETED                      # terminal: Phase met all completion criteria
BLOCKED_BLUEPRINT              # terminal: still blocked after 3 pre-exec rounds
BLOCKED_POSTEXEC               # terminal: still blocked after the second dual audit
```

## Legal transitions

```text
(no prior state)            -> DRAFTING_BLUEPRINT           (CC writes from-cc/<phase-id>__kickoff.md)

DRAFTING_BLUEPRINT          -> PRE_AUDIT_R1                 (Codex delivers blueprint)

PRE_AUDIT_R1                -> PRE_AUDIT_SYNTHESIS_R1       (both CC + Codex audits delivered)
PRE_AUDIT_SYNTHESIS_R1      -> BLUEPRINT_REVISION_R1        (CC synthesis says repair)
PRE_AUDIT_SYNTHESIS_R1      -> BLUEPRINT_ACCEPTED           (CC synthesis says no repair needed, blueprint is acceptable)
BLUEPRINT_REVISION_R1       -> BLUEPRINT_ACCEPTED           (repair complete and acceptable)
BLUEPRINT_REVISION_R1       -> PRE_AUDIT_R2                 (repair complete but another round needed)

PRE_AUDIT_R2                -> PRE_AUDIT_SYNTHESIS_R2
PRE_AUDIT_SYNTHESIS_R2      -> BLUEPRINT_REVISION_R2
PRE_AUDIT_SYNTHESIS_R2      -> BLUEPRINT_ACCEPTED
BLUEPRINT_REVISION_R2       -> BLUEPRINT_ACCEPTED
BLUEPRINT_REVISION_R2       -> PRE_AUDIT_R3

PRE_AUDIT_R3                -> PRE_AUDIT_SYNTHESIS_R3
PRE_AUDIT_SYNTHESIS_R3      -> BLUEPRINT_REVISION_R3
PRE_AUDIT_SYNTHESIS_R3      -> BLUEPRINT_ACCEPTED
BLUEPRINT_REVISION_R3       -> BLUEPRINT_ACCEPTED
BLUEPRINT_REVISION_R3       -> BLOCKED_BLUEPRINT            (cap reached and still blocked)

BLUEPRINT_ACCEPTED          -> EXECUTING                    (Codex starts execution)
EXECUTING                   -> EXECUTION_REPORTED           (Codex delivers execution report)
EXECUTING                   -> BLOCKED_BLUEPRINT            (significant gap discovered, abort)

EXECUTION_REPORTED          -> POSTEXEC_SUBAGENT_REVIEW     (Codex launches subagent review)
POSTEXEC_SUBAGENT_REVIEW    -> POSTEXEC_CC_REVIEW           (subagent review delivered, awaits CC)
POSTEXEC_CC_REVIEW          -> POSTEXEC_SYNTHESIS           (CC review delivered, Codex synthesizes)
POSTEXEC_SYNTHESIS          -> POSTEXEC_FIX                 (repair needed)
POSTEXEC_SYNTHESIS          -> PHASE_CLOSING                (no repair needed, go straight to close)
POSTEXEC_FIX                -> SECOND_AUDIT_DECISION

SECOND_AUDIT_DECISION       -> PHASE_CLOSING                (NO: small repair, core path untouched)
SECOND_AUDIT_DECISION       -> SECOND_AUDIT_CC              (YES: enter second dual audit)
SECOND_AUDIT_CC             -> SECOND_AUDIT_CODEX           (CC second-audit delivered, awaits Codex)
SECOND_AUDIT_CODEX          -> SECOND_AUDIT_FIX
SECOND_AUDIT_FIX            -> PHASE_CLOSING                (repair passes)
SECOND_AUDIT_FIX            -> BLOCKED_POSTEXEC             (still blocked, no further loop)

PHASE_CLOSING               -> COMPLETED                    (all completion criteria satisfied)
PHASE_CLOSING               -> BLOCKED_POSTEXEC             (completion criteria not satisfied)
```

## Driver authority

| Transition | Driver | Note |
|------------|--------|------|
| `(no prior state) -> DRAFTING_BLUEPRINT` | CC | CC writes the kickoff artifact (`<phase-id>__kickoff.md` in `from-cc/`) carrying `BatonNext: DRAFTING_BLUEPRINT`; that is the only way a Phase legitimately starts |
| `* -> PRE_AUDIT_R*`, `BLUEPRINT_REVISION_R*`, `PRE_AUDIT_SYNTHESIS_R*` | CC | CC is the pre-execution loop closure judge |
| `* -> BLUEPRINT_ACCEPTED` | CC | the synthesizer signs the "acceptable" verdict |
| `BLUEPRINT_ACCEPTED -> EXECUTING` | Codex | execution begins |
| `EXECUTING -> EXECUTION_REPORTED` | Codex | main executor delivers |
| `EXECUTION_REPORTED -> POSTEXEC_SUBAGENT_REVIEW`, `* -> POSTEXEC_SYNTHESIS`, `POSTEXEC_FIX`, `SECOND_AUDIT_DECISION` | Codex | the post-exec main path is Codex-driven |
| `POSTEXEC_SUBAGENT_REVIEW -> POSTEXEC_CC_REVIEW` (waits for CC) and `SECOND_AUDIT_CC` | CC | CC's post-exec independent review / second-audit CC side |
| `PHASE_CLOSING -> COMPLETED \| BLOCKED_POSTEXEC` | Codex | close judgment |

## Invariants

1. **Three-round cap.** `PRE_AUDIT_R3` is the maximum round of
   pre-execution audit. If `BLUEPRINT_REVISION_R3` is still not
   acceptable, it **must** transition to `BLOCKED_BLUEPRINT`. There is no
   `R4` state.
2. **Completion-criteria gate.** A transition from `PHASE_CLOSING` to
   `COMPLETED` must explicitly enumerate every completion criterion from
   source-document §11 with a pass/fail tag; all must be passing.
3. **Second dual audit is one-shot.** From `POSTEXEC_FIX` into the second
   dual audit can happen at most once. `SECOND_AUDIT_FIX` cannot loop
   back to `SECOND_AUDIT_DECISION`.
4. **Authority refusal.** CC cannot write Codex-driven products such as
   `EXECUTION_REPORTED` / `POSTEXEC_FIX`. Codex cannot write CC-driven
   products such as `PRE_AUDIT_SYNTHESIS_*` / `BLUEPRINT_REVISION_*`.
   The reader of an out-of-authority product must ignore it and request
   the correct sender to resend.
5. **Isolation.** This state machine does not reference, read, or depend
   on any state, mailbox, or script under `blue-k-git-baton-testkit/`.
