# <PRESET> — BATON state schema

The baton state machine. Every product file's first line
`BatonNext: <STATE>` declares the transition target. Readers advance
the baton based on that line. State names are SCREAMING_SNAKE_CASE.

## State enumeration

```text
<INITIAL_STATE>
<round-1 review states>
<round-2 review states (if bounded iteration)>
<...>
<execution states>
<post-execution states>
<close states>
<terminal: ACCEPTED state>
<terminal: BLOCKED_<reason> states>
```

(Define every distinct state. If iteration rounds exist, give each
round its own state — do not define a state past the cap. E.g., if
the cap is 3, do not define `REVIEW_R4`.)

## Legal transitions

```text
<FROM_STATE> -> <TO_STATE>    (<condition>)
<...>
```

(One per line. Make sure every transition is reachable; every state
has at least one entry and one exit, except terminal states.)

## Driver authority

| Transition | Driver | Note |
|------------|--------|------|
| `<from> -> <to>` | `Codex \| CC` | `<short note>` |

## Invariants

Number these and enforce each one in either a verifier or the artifact
checker:

1. **<bounded-iteration cap>.** If applicable, e.g. "review caps at
   round 3; round 4 state does not exist; transition past round 3
   without acceptance must lead to BLOCKED".
2. **<completion-criteria gate>.** Transition into `COMPLETED` must
   enumerate every completion criterion with a pass/fail tag; all
   must be passing.
3. **<one-shot branch>.** If applicable, e.g. "second audit cannot
   loop back to its decision state".
4. **Authority refusal.** Each side cannot write the other side's
   products. Readers of out-of-authority products must ignore them.
5. **Isolation.** This state machine does not reference, read, or
   depend on any other preset's mailbox or scripts.
