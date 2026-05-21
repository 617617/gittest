# Primary workflow focus (informational only)

PrimaryFocus: temporal-phase

This file is **informational**. It records which workflow has the user's
primary focus right now, as a hint for new conversations. It is **not**
read by any watcher, verifier, or hook, and does **not** gate anything.

Multiple workflows may be enabled in parallel — every workflow with a
subdirectory under `workflows/` (or `blue-k-git-baton-testkit/` for the
testkit) is "enabled" by virtue of existing. Each has its own watcher
skill (`/temporal-phase-watch`, `/bk-watch`, etc.) that arms
independently and only touches its own coord directory.

To redirect the user's primary focus, just edit the `PrimaryFocus:`
line — no other file needs to change.
