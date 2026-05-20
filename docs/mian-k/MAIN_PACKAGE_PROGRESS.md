# Blue-K Main Package Progress

| Id | Package | Status | RunnerCheckpoint | Notes |
| --- | --- | --- | --- | --- |
| main:01 | docs/mian-k/main/01_setup | done | 1111111 | Initial setup complete |
| main:02 | docs/mian-k/main/02_prereq | running | 2222222 | In progress |
| main:03 | docs/mian-k/main/03_rules | pending | - | Waiting for main:02 |

## Runner State Machine

```text
pending -> running -> review_pending -> done
running -> checkpoint -> review_pending
review_pending + accepted consensus -> finalize -> done
review_pending + fix_required -> fix lane -> new checkpoint -> review_pending
```