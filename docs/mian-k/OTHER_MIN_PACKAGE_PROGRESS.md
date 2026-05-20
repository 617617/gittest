# Blue-K Other Min Package Progress

| Id | Package | Status | RunnerCheckpoint | Notes |
| --- | --- | --- | --- | --- |
| other:01 | docs/mian-k/other/01_side | done | 1111111 | Side task complete |
| other:02 | docs/mian-k/other/02_quest | pending | - | Waiting for prerequisite |

## Dependency Recovery

When other-runner encounters a dependency failure, the consensus must bind:

```yaml
SubjectPackage:
ActivePackage:
DependencyRecoveryTarget:
FixTarget: active_package | dependency_recovery_target | both
ProgressFile:
ProgressRowId:
FindingSetCommit:
```