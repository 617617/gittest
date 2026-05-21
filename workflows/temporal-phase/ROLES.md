# temporal-phase — Roles & Step Matrix

把源文档 §2–§10 的流程拆成步骤,标注每步的**驱动者**、**输入**、
**产物**、**送往的邮箱**。"驱动者"指本步骤的主要责任 AI;Codex 与
CC 同时出现表示需要双方各自交付一份产物。

约定:

- 邮箱位置:
  - CC → Codex 的写入路径 = `workflows/temporal-phase/_coord/from-cc/`
  - Codex → CC 的写入路径 = `workflows/temporal-phase/_coord/from-codex/`
- 命名建议:`<phase-id>__<step-tag>.md`,例:`phase-12__blueprint.md`。
- 每个产物文件首部都应包含一行 `BatonNext:` 指明下一个状态(状态名见
  `BATON.schema.md`),作为状态机转移的显式信号。

## Step Matrix

| # | 步骤 | 驱动者 | 输入 | 产物 | 落地邮箱 |
|---|------|--------|------|------|----------|
| 1 | 创建 Phase 执行蓝图 | Codex | 上一 Phase 收尾结论 + 源文档 | `<phase-id>__blueprint.md`(目标/范围/允许修改文件/验证/产物/风险) | from-codex/ |
| 2 | CC 侧执行前审核 | CC | 蓝图 | `<phase-id>__pre-audit-cc-r<N>.md` | from-cc/ |
| 3 | Codex 侧执行前审核 | Codex | 蓝图 | `<phase-id>__pre-audit-codex-r<N>.md` | from-codex/ |
| 4 | CC 汇总审核意见 | CC | 两份执行前审核 | `<phase-id>__pre-audit-synthesis-r<N>.md`(吸收/记录/暂不处理三段) | from-cc/ |
| 5 | CC 蓝图修复 | CC | 汇总意见 | `<phase-id>__blueprint-revision-r<N>.md` | from-cc/ |
| 6 | 判断是否再循环 | CC | 修复后蓝图 + 剩余意见 | `<phase-id>__pre-audit-verdict-r<N>.md`(ACCEPTED/RELOOP/ABANDON) | from-cc/ |
| 7 | Phase 执行 | Codex | 已接受蓝图 | `<phase-id>__execution-report.md`(实际修改/验证结果/遗留风险/证据/下一步建议) | from-codex/ |
| 8 | Codex 多 subagent 综合审核 | Codex | 执行报告 | `<phase-id>__postexec-subagent-review.md`(多 subagent 意见汇总) | from-codex/ |
| 9 | CC 执行后独立审核 | CC | 执行报告 | `<phase-id>__postexec-cc-review.md` | from-cc/ |
| 10 | Codex 汇总两边意见 | Codex | §8 + §9 两份 | `<phase-id>__postexec-synthesis.md`(吸收/记录/超范围三段) | from-codex/ |
| 11 | Codex 吸收修复 | Codex | 汇总意见 | `<phase-id>__postexec-fix.md`(修改 + 验证 + 处理结论) | from-codex/ |
| 12 | 决策是否二次双审 | Codex | 修复规模 / 风险评估 | `<phase-id>__second-audit-decision.md`(YES/NO + 依据) | from-codex/ |
| 13 | (可选)二次双审 — CC | CC | §11 修复结果 | `<phase-id>__second-audit-cc.md` | from-cc/ |
| 14 | (可选)二次双审 — Codex subagent | Codex | §11 修复结果 | `<phase-id>__second-audit-codex.md` | from-codex/ |
| 15 | (可选)二次双审汇总修复 | Codex | §13 + §14 | `<phase-id>__second-audit-fix.md` | from-codex/ |
| 16 | Phase 收尾 | Codex | 完成标准核对 | `<phase-id>__close.md`(COMPLETED 或 BLOCKED + 原因 + 后续归属) | from-codex/ |

## 角色边界(从源文档与 testkit 经验提炼)

- **Codex** 负责所有"创造性输出 + 自我多 subagent 审核":蓝图、执行、
  执行后综合审核、汇总、修复、收尾。Codex 是本 Phase 的最终修复责任方。
- **CC** 负责所有"独立视角审核 + 跨方汇总":执行前审核、执行前汇总、
  蓝图修复、执行后审核、(可选)二次双审审核。CC 是流程闭环判断者。
- subagent 的角色定位与源文档一致——提意见,不替代主执行者做最终决策
  (§7)。

## 失败 / 阻塞处理

- 执行前审核三轮后仍存在阻塞性问题 → 写 `pre-audit-verdict-r3.md` 标
  `ABANDON`,baton 进入 `BLOCKED_BLUEPRINT`,本 Phase 不强行执行。
- 二次双审仍有阻塞性问题 → 写 `close.md` 标 `BLOCKED`,记录原因与后
  续归属,baton 进入 `BLOCKED_POSTEXEC`(不再无限循环)。
