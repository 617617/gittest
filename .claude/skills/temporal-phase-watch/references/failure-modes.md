# Failure modes

How `temporal-phase-watch` reacts when a step in SKILL.md fails.

| Symptom | Required behavior |
|---|---|
| Pull conflict / diverged | Stop. Surface error. Do not arm watcher. |
| Either verifier FAIL | Stop. Surface error. Do not arm watcher. |
| `check_baton_artifacts.py` FAIL | Stop. Surface the list of issues. Do not arm watcher. Fixes typically need human triage. |
| Monitor start error | Surface error and stop. |
| TaskList unavailable | Skip step 1 (deduplication check); start the Monitor unconditionally. |

The general principle: never arm watchers against a broken baseline.
The only exception is TaskList unavailability, which only affects
deduplication — a duplicate Monitor is cheap to reap later, but a
Monitor armed against a corrupt baton state can cause CC to react to
malformed artifacts.
