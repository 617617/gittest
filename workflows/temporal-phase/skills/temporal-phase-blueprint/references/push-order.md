# Push order (cross-repo consistency)

You write commits in **two repos** (work repo for the Generator
package, coord repo for the pointer). To avoid dangling references —
where the coord-side `PackageCommit: temporal@<sha>` points at a
commit only on your local machine — push in this strict order:

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

If the **first push fails** (work-repo push rejected — network drop,
conflict, branch protection): do **not** push the coord repo. On
next `/temporal-phase-codex-sync` you will see baton state still
`DRAFTING_BLUEPRINT` (no blueprint pointer in coord); retry the
work-repo push first, then write/push the coord pointer. Pointer/SHA
stays consistent.

Worst case if your **second push fails** (work pushed, coord push
rejected): you have an already-pushed work repo commit and an
unpushed coord-side pointer. On next `/temporal-phase-codex-sync`
you will see baton state has not advanced (no blueprint pointer in
coord); simply retry the coord push. Pointer/SHA stays consistent.

Worst case if push order is reversed: the coord-side pointer is on
`origin/master` referencing a `temporal@<sha>` that CC's `temporal:`
remote does not have. CC's audit lane cannot resolve the reference;
audit stops with an error and the user has to fix it manually. Avoid
this by following the order above.

If you suspect a cross-repo inconsistency between coord pointers and
work-repo SHAs, the standalone check `scripts/verify_cross_repo_refs.py`
walks both mailboxes + archive and flags any unreachable
`temporal@<sha>` reference; the consumer-side audit lane will fail with
a `CROSS_REPO_MISSING_REF` error if it cannot resolve a pointer.
