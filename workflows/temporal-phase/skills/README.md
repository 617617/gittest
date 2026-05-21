# skills/ — temporal-phase 的 lane skill 占位

当前为骨架版本:每个 AI side 一个 `SKILL.md`,内部用小节列出该 side
的全部 lane(触发态/读/写/BatonNext)。

骨架→正式的演进路径(后续可做):

1. 等本预设跑通至少一个完整 Phase 后,从邮箱中实际产物里提炼 prompt
   模板,放入各 lane 的 `instructions.md`。
2. 若某个 lane 的 prompt 逐渐变长,可将其单独拆出子目录:
   `skills/cc/pre-audit-cc/SKILL.md` 等。
3. 在 lane skill 趋稳后,再考虑提炼跨 preset 的 `workflow-onboard`
   元工具(把"读源文档 → 生成 CHARTER/ROLES/BATON.schema/skill 骨
   架"自动化)。**不要现在做。**
