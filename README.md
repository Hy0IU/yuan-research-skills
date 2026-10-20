# yuan-research-skills

论文 Idea 研究流程系统的 Skill 总仓库，以 Git 管理。

系统设计以《设计论文Idea工作流》的讨论方案为基线，逐步讨论并实现。

项目目标、协作原则及质量与 Token 消耗要求见 [AGENTS.md](AGENTS.md)。

## 系统范围

- 论文理解与研究者见解。
- 方法机制知识积累与关联。
- 结合研究基座进行 Idea 探索与方法迁移。
- Idea 演化、决策记录与跨会话恢复。

## 当前进度

已实现首个 Skill：[yuan-paper-explainer](skills/yuan-paper-explainer/SKILL.md)（参考论文说明），后续通过实际论文使用继续完善。

Skill 源码统一放在 `skills/<skill-name>/` 下，每个 Skill 可独立使用。当前仓库保存源码，尚未安装到全局 Skill 目录。

使用时向 Agent 提供上述 `SKILL.md` 路径，以及论文原文与目标研究目录。Skill 将生成或更新一份精简说明；仅询问局部内容时直接回答对应部分。
