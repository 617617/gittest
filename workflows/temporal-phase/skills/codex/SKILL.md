---
name: temporal-phase-codex
description: Codex 在 temporal-phase 工作流下的所有 lane 索引。本 skill 是占位骨架,每个 lane 给出触发态、读什么、写什么、产物的 BatonNext 值,真正的提示词与子流程在落地时再填。
---

# temporal-phase — Codex Lanes

本预设下 Codex 负责的所有 lane。结构按 `BATON.schema.md` 的状态展开。
每次完成都要写一份带 `BatonNext:` 的产物到 `../../_coord/from-codex/`。

约定:

- 邮箱写入路径:`workflows/temporal-phase/_coord/from-codex/`。
- 文件名模式见 `../../ROLES.md` 的 Step Matrix。
- 越权检查:本 side 不得写出"CC 驱动"类产物(见 BATON.schema 不变量
  §4)。

## Lane: blueprint

- Trigger: `DRAFTING_BLUEPRINT`(新 Phase 起手,或前一 Phase 收尾 →
  下一 Phase 开始)。
- Reads:源文档 + 上一 Phase 的 `close.md`(若有)。
- Writes: `<phase-id>__blueprint.md`。
- Product structure:`Goal:` / `Scope:` / `Out-of-scope:` /
  `AllowedFiles:` / `Validation:` / `ExpectedArtifacts:` /
  `RiskBoundary:`。
- BatonNext: `PRE_AUDIT_R1`。

## Lane: pre-audit-codex

- Trigger: `PRE_AUDIT_R1` / `PRE_AUDIT_R2` / `PRE_AUDIT_R3`(本轮
  Codex 半边尚未交付)。
- Reads: 当前蓝图(R1: 原蓝图;R2/R3: 上一轮 `blueprint-revision-r*.md`)。
- Writes: `<phase-id>__pre-audit-codex-r<N>.md`。
- Product structure:与 CC 侧对称,`Findings:` / `Risks:` /
  `Open Questions:` / `Recommendation: ACCEPT | REVISE | ABANDON`。
- BatonNext: `PRE_AUDIT_SYNTHESIS_R<N>`(实际状态推进由 CC 的 synthesis
  lane 推动,本文件 BatonNext 只是声明等待汇总)。

## Lane: execute

- Trigger: `EXECUTING`(由 `BLUEPRINT_ACCEPTED` 转入,且尚未交付执行
  报告)。
- Reads: `BLUEPRINT_ACCEPTED` 对应的最终蓝图(原蓝图或最后一次
  `blueprint-revision-r*.md`)。
- 执行约束:严格按蓝图范围,不擅自扩张;遇到"蓝图重大缺口"或"代
  码状态与蓝图假设明显不一致"时立即停止并记录,转 `BLOCKED_BLUEPRINT`。
- Writes: `<phase-id>__execution-report.md`。
- Product structure:`ActualChanges:` / `ValidationResults:` /
  `ResidualRisks:` / `EvidenceArtifacts:` / `NextStepSuggestions:`。
- BatonNext: `EXECUTION_REPORTED`。

## Lane: postexec-subagent-review

- Trigger: `EXECUTION_REPORTED` 后,Codex 启动多 subagent 综合审核。
- Reads: 执行报告 + 实际改动 diff。
- 子流程建议(源文档 §7 多角度):
  - 是否按蓝图范围执行;
  - 修改是否符合项目边界;
  - 测试/验证是否充分;
  - 证据产物是否完整;
  - 是否存在遗漏、回归风险、不一致;
  - 是否需要补充修复。
- Writes: `<phase-id>__postexec-subagent-review.md`。
  - 多个 subagent 结论汇为一份文件,标注每条意见的提出者与权重。
- BatonNext: `POSTEXEC_CC_REVIEW`(交棒给 CC 做独立审核)。

## Lane: postexec-synthesize

- Trigger: `POSTEXEC_SYNTHESIS`(`postexec-subagent-review` 与
  `postexec-cc-review` 都已交付)。
- Reads: 两份执行后审核文件。
- Writes: `<phase-id>__postexec-synthesis.md`。
- Product structure:`Adopted:` / `Recorded:`(不成立/重复但需留底)
  / `Out-of-scope:`(留到后续 Phase,需明确归属)。
- BatonNext:`POSTEXEC_FIX`(Adopted 非空)或
  `PHASE_CLOSING`(Adopted 为空,直接收尾)。

## Lane: postexec-fix

- Trigger: `POSTEXEC_FIX`。
- Reads: `postexec-synthesis.md` 的 Adopted 段。
- Writes: `<phase-id>__postexec-fix.md`(实际修改 + 重新验证结果 +
  处理结论)。
- BatonNext: `SECOND_AUDIT_DECISION`。

## Lane: second-audit-decision

- Trigger: `SECOND_AUDIT_DECISION`(`POSTEXEC_FIX` 已交付)。
- Reads: 修复规模与影响面。
- 判定:修复"较少且不影响核心路径/重要边界/关键验证" → NO;反之 → YES。
- Writes: `<phase-id>__second-audit-decision.md`(`YES/NO + 依据`)。
- BatonNext: `PHASE_CLOSING`(NO) 或 `SECOND_AUDIT_CC`(YES)。

## Lane: second-audit-codex

- Trigger: `SECOND_AUDIT_CODEX`(CC 二审已交付)。
- Reads: `postexec-fix.md` + `second-audit-cc.md`。
- 子流程:Codex 用 subagent 再审一次修复后的结果。
- Writes: `<phase-id>__second-audit-codex.md`。
- BatonNext: `SECOND_AUDIT_FIX`。

## Lane: second-audit-fix

- Trigger: `SECOND_AUDIT_FIX`。
- Reads: 二次双审两边意见。
- Writes: `<phase-id>__second-audit-fix.md`(最终修复 + 验证结论)。
- BatonNext: `PHASE_CLOSING`(通过) 或 `BLOCKED_POSTEXEC`(仍阻塞,不
  再循环)。

## Lane: close

- Trigger: `PHASE_CLOSING`。
- Reads: 本 Phase 全部产物。
- 必做:逐条核对 `CHARTER.md` "完成标准"小节,每条标注满足/未满足。
- Writes: `<phase-id>__close.md`(`COMPLETED | BLOCKED_POSTEXEC` +
  逐条核对 + 剩余风险归属 + 下一 Phase 建议)。
- BatonNext: `COMPLETED` 或 `BLOCKED_POSTEXEC`。

## 不在 Codex 范围内的 lane

下列产物只能由 CC 写出,Codex 不得越权:`pre-audit-cc-r*`、
`pre-audit-synthesis-r*`、`blueprint-revision-r*`、`postexec-cc-review`、
`second-audit-cc`。
