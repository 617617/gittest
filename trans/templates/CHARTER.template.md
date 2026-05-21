# <PRESET> — Charter

## Source document

`<absolute or temporal:-style path to the authoritative source workflow doc>`

This preset is the operational distillation of that source. The source
remains the single authoritative text; this directory turns its prose
into a baton state machine. When the source changes, update ROLES and
BATON.schema first.

## Unit of work

`<Phase | Sprint | Release | Ticket>`. A unit closes only after the full
lifecycle (define the lifecycle stages in one or two lines) has run.

## Flow highlights

1. `<step 1 with driver and product>`
2. `<step 2 ...>`
3. `<...>`
N. **Completion criteria.** See §Completion criteria below.

## Completion criteria

A unit closes only if **all** the following hold. Each criterion carries
a stable ID `CC-NN`; the closing lane SKILL's product template and
`scripts/verify_<preset>_skills.py` reference the same IDs.

- **CC-01** — `<criterion text>`.
- **CC-02** — `<criterion text>`.
- **CC-03** — `<criterion text>`.
- **CC-NN** — `<criterion text>`.

## Unit-id naming and concurrency

- **Format.** Every unit carries an id matching the regex
  `<unit-id-regex, e.g. phase-\d+>`.
- **One open unit at a time.** A unit is "open" from the moment its
  first artifact lands in either mailbox until the matching
  `<unit-id>__close.md` lands in `from-codex/`. Two unit-ids may not
  both be open at the same time.
- **Enforcement.** `scripts/check_baton_artifacts.py` enforces format,
  filename pattern, mailbox routing, and one-open-unit count. The
  `<preset>-watch` skill runs the checker on every session boot.

## Isolation from other presets

- This preset does **not** depend on any other preset's scripts,
  skills, `_coord/`, or protocol files.
- This preset does **not** modify any file inside other presets.
- Multiple presets coexist; none reads another's `_active.md` or
  internal state.

## Out of scope for this preset

- `<things this preset will not handle, e.g. running the actual app>`.
- Cross-preset generic abstractions.
