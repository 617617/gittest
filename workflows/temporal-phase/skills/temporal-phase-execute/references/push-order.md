# Push order (cross-repo consistency)

Execution writes commits in **two repos** (work repo for the actual
code changes; coord repo for the execution-report pointer). To avoid
dangling references — where the coord-side `ActualChanges:` cites a
`temporal@<sha>` that exists only on your local machine — push in
this strict order:

1. **First**, push the work repo (Temporal):
   ```bash
   cd $(temporal:)
   git push origin <work-branch>
   ```
   Confirm exit 0 before continuing.

2. **Only then**, push the coord repo (gittest):
   ```bash
   cd $(gittest:)
   git push origin master
   ```

If the first push fails (network drop, lock, conflict): do **not**
push the coord repo. On next `/temporal-phase-codex-sync` you will
see baton state still `EXECUTING` (no execution-report in coord);
retry the work-repo push first, then write/push the coord pointer.

If somehow the coord push happened but the work-repo push failed:
CC's `postexec-subagent-review` lane will fail to resolve the
`ActualChanges:` SHAs and surface a `CROSS_REPO_MISSING_REF` error;
recovery is "push the work repo, then have CC retry the audit". A
standalone check exists: `scripts/verify_cross_repo_refs.py` walks
both mailboxes + archive and flags any pointer whose `temporal@<sha>`
is unreachable from the local work-repo clone.
