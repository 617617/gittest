# Blue-K Plan Audit Report

## Current Audit Status

| PlanId | SubjectCommit | Verdict | Auditor | Notes |
| --- | --- | --- | --- | --- |
| plan:01 | 1111111 | PASS | cc | Plan approved |
| plan:02 | 2222222 | pending | - | Audit in progress |

## Verdict Rules

- `PASS`: Plan is safe to proceed to consensus.
- `WARN`: Plan has minor issues; requires full consensus and human risk acceptance.
- `BLOCK`: Plan has critical issues; must return to planner repair.

## Lower Gate Precedence

Consensus cannot override a BLOCK verdict. Human `accept_risk` may accept only
PASS or explicitly accepted WARN.