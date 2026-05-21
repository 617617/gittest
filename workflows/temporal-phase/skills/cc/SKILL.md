---
name: temporal-phase-cc
description: CC 在 temporal-phase 工作流下的所有 lane 索引。本 skill 是占位骨架,每个 lane 给出触发态、读什么、写什么、产物的 BatonNext 值,真正的提示词与子流程在落地时再填。
---

# temporal-phase — CC Lanes

本预设下 CC 负责的所有 lane。结构按 `BATON.schema.md` 的状态展开:每
个 lane 只有在 baton 处于"触发态"时才该被调用;每次完成都要写一份
带 `BatonNext:` 的产物到 `../../_coord/from-cc/`。

约定:

- 邮箱写入路径:`workflows/temporal-phase/_coord/from-cc/`。
- 文件名模式见 `../../ROLES.md` 的 Step Matrix。
- 越权检查:本 side 不得写出"Codex 驱动"类产物(见 BATON.schema 不
  变量 §4)。

## Lane: pre-audit-cc

- Trigger: `PRE_AUDIT_R1` / `PRE_AUDIT_R2` / `PRE_AUDIT_R3`(当前 baton
  处于其中之一,且 from-cc/ 还未交付对应轮次的 CC 审核)。
- Reads: `from-codex/<phase-id>__blueprint.md`(R1)或最近一轮
  `from-cc/<phase-id>__blueprint-revision-r<N-1>.md`(R2/R3)。
- Writes: `<phase-id>__pre-audit-cc-r<N>.md`。
- Product structure:`Findings:` / `Risks:` / `Open Questions:` /
  `Recommendation: ACCEPT | REVISE | ABANDON`。
- BatonNext: 无独立转移(本 lane 是 R<N> 的"半边",等 Codex 侧也交付
  后才进入 synthesis);文件首行写 `BatonNext: PRE_AUDIT_SYNTHESIS_R<N>`。

## Lane: pre-audit-synthesize

- Trigger: `PRE_AUDIT_R<N>` 阶段下,from-cc/ 与 from-codex/ 都已交付
  本轮审核。
- Reads:本轮 `pre-audit-cc-r<N>.md` + `pre-audit-codex-r<N>.md`。
- Writes: `<phase-id>__pre-audit-synthesis-r<N>.md`。
- Product structure:`Adopted:`(吸收并将进入修复)/ `Recorded:`(记
  录但不动)/ `Out-of-scope:`(超范围或留后续 Phase)。
- BatonNext:`BLUEPRINT_REVISION_R<N>`(若 Adopted 非空)
  或 `BLUEPRINT_ACCEPTED`(若 Adopted 为空且蓝图整体可接受)。

## Lane: blueprint-revise

- Trigger: `BLUEPRINT_REVISION_R<N>`。
- Reads:对应轮次的 `pre-audit-synthesis-r<N>.md` + 当前蓝图。
- Writes: `<phase-id>__blueprint-revision-r<N>.md`(含 Diff 摘要 +
  剩余风险评估)。
- BatonNext:
  - `BLUEPRINT_ACCEPTED` —— 修复后可接受。
  - `PRE_AUDIT_R<N+1>` —— 修复后仍需再审(N+1 ≤ 3)。
  - `BLOCKED_BLUEPRINT` —— 当 N=3 且仍存在阻塞性问题。

## Lane: postexec-cc

- Trigger: `POSTEXEC_CC_REVIEW`(`POSTEXEC_SUBAGENT_REVIEW` 已交付,
  CC 该独立审核)。
- Reads: `from-codex/<phase-id>__execution-report.md` +
  `<phase-id>__postexec-subagent-review.md`(对照参考,不替代独立判
  断)。
- Writes: `<phase-id>__postexec-cc-review.md`。
- Product structure:`ScopeConformance:` / `BlueprintAlignment:` /
  `MissedRisks:` / `BlockersForNextPhase:` / `Recommendation:`。
- BatonNext: `POSTEXEC_SYNTHESIS`。

## Lane: second-audit-cc

- Trigger: `SECOND_AUDIT_CC`(由 `SECOND_AUDIT_DECISION = YES` 进入)。
- Reads: `<phase-id>__postexec-fix.md` 与 §10 的汇总记录。
- Writes: `<phase-id>__second-audit-cc.md`。
- Product structure:`FixSufficiency:` / `RegressionRisk:` /
  `RemainingBlockers:` / `Recommendation:`。
- BatonNext: `SECOND_AUDIT_CODEX`。

## 不在 CC 范围内的 lane

下列产物只能由 Codex 写出,CC 不得越权:`blueprint`、
`pre-audit-codex-r*`、`execution-report`、`postexec-subagent-review`、
`postexec-synthesis`、`postexec-fix`、`second-audit-decision`、
`second-audit-codex`、`second-audit-fix`、`close`。
