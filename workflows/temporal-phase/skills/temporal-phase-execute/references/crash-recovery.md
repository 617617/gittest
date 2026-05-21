# Resume after crash mid-execution

If your CLI dies (network drop, session killed) while you were
executing — possibly after some work-repo commits/pushes but before
the coord-side execution-report was written — recovery on next
session start is:

1. `/temporal-phase-codex-sync` will report baton state still
   `EXECUTING` (or whichever earlier state, because no
   execution-report has landed in coord yet).
2. In the work repo, run
   `cd $(temporal:) && git log --oneline -20` to find your most recent
   commits. Confirm they were already pushed
   (`git status -sb`; look for `[ahead N]` — if N>0, push them now).
3. If the package execution is **complete in the work repo** but the
   coord-side report was never written: write
   `from-codex/<phase-id>__execution-report.md` now per the §3 product
   structure in `tools-runner.md`, citing the actual work-repo commits,
   then follow the push order above (coord-only push since work is
   already pushed).
4. If execution is **partial in the work repo** (e.g., only the
   first stage was committed before the crash): resume the Runner
   from where it stopped — `stage-loop-auto` is internally serial,
   you can restart the package and it picks up the next pending
   stage. Only after the package finishes do you write the
   coord-side report.

Do not write a coord-side execution-report claiming work that you
have not actually committed to the work repo. The
`verify_cross_repo_refs.py` check will catch fabricated SHAs at
audit time.
