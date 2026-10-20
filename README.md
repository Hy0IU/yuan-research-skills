# yuan-research-skills

论文 Idea 研究流程系统的 Skill 总仓库，以 Git 管理。

系统设计以《设计论文Idea工作流》的讨论方案为基线，逐步讨论并实现。

项目目标、协作原则及质量与 Token 消耗要求见 [AGENTS.md](AGENTS.md)。

## 系统范围

- 论文理解与研究者见解。
- 方法机制知识积累与关联。
- 结合研究背景、直觉与参考方法进行 Idea 探索和架构设计。
- Idea 演化、决策记录与跨会话恢复。

## 当前进度

已实现三个 Skill，后续通过实际研究使用继续完善：

- [yuan-paper-explainer](yuan-paper-explainer/SKILL.md)：参考论文说明，支持首次生成和补充见解后的再次分析。
- [yuan-mechanism-builder](yuan-mechanism-builder/SKILL.md)：分析论文设计、抽象并比较机制，构建与持续维护机制知识库；支持研究者在过程中讨论和纠偏。
- [yuan-idea-explorer](yuan-idea-explorer/SKILL.md)：结合研究者直觉与参考方法，探索独特模块和丰富候选架构，保存 Idea 并持续讨论更新。

每个 Skill 的文件夹直接放在仓库根目录，即 `<skill-name>/`，可独立使用。当前仓库保存源码，尚未安装到全局 Skill 目录。

使用时向 Agent 提供相应 `SKILL.md` 路径、论文或机制材料与指定工作目录。默认组织为：

```text
工作目录/
├── research-context.md
├── references/
│   └── 论文标题/
│       ├── paper.md
│       └── paper.pdf
├── mechanisms/
│   └── 机制名称.md
└── ideas/
    ├── INDEX.md
    └── IDEA-001-方向名称/
        ├── idea.md
        ├── decisions.md
        └── experiments/
```

先生成说明初稿，由研究者填写“我的理解与研究启发”，再让 Agent 重新分析并更新相关章节，尤其是第3、4、7节。同一论文复用目录与文件；仅询问局部内容时直接回答对应部分。

完成研究者补充和再次分析后，才可进入机制库。机制 Skill 主动分析、抽象、比较并形成机制认识；研究者可随时指出方向偏移，讨论确定后更新相关内容，保留重要决策原因。

Idea 探索可直接从研究者想法和指定论文开始，机制库作为辅助。组内 base 仅为可选参考；默认充分发展有启发性的复杂架构，由研究者判断取舍。每条独立路线一份主文档，局部变体在其中展开，大幅改写时按需保存旧版。

`idea.md` 保存当前方案，`decisions.md` 持续保存关键选择、依据和替代关系，支持新会话恢复研究。`experiments/` 为各 Idea 预留，实际结果按 `EXP-001-实验名称/experiment.md` 组织，关联所用架构版本并保留原始材料与原因分析；没有实验时不生成结果记录。
