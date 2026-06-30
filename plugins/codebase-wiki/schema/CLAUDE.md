# Codebase-Wiki

一个基于 Karpathy LLM Wiki 模式构建的代码知识累积系统，以 Claude Code 插件形式分发。

## 这是什么

不是图谱数据库，不是一个有类型系统的知识工程。**是一个会生长的 markdown 目录。** 每次 ingest 一个代码仓库，LLM 不只是索引源码等以后检索——它读源码、提取关键信息、整合进已有的 wiki 页面、更新关联页面的交叉引用、标记新旧矛盾、强化或挑战已有的分析。知识编译一次然后持续保鲜，不是每次查询都重新推导。

核心机制是 **wikilink 网络**——entity 页链到 concept 页、concept 页链回 entity 页、overview 链到 entity。这个 wikilink 网络本身就是唯一的"图谱"：Obsidian Graph View 里看到的就是它，LLM 在回答查询时沿着它遍历的就是它。不需要额外一层结构化图谱数据。

## 架构

```
Raw Sources    →  代码仓库（不可变，LLM 只读）
The Wiki       →  LLM 拥有并维护的所有 markdown（wiki/ 目录）
The Schema     →  告诉 LLM 怎么结构化、什么约定、什么流程（schema/ + CLAUDE.md）
The Skills     →  每个 Claude Code skill（commands/*.md）是 LLM 的操作手册
```

## 管线

```
Source → Entity（源码中可定位的模块，有独立职责边界）
  → Problem Space Mapping（将单仓库 entity 翻译成跨仓库的"如何..."问题）
  → Concept（跨仓库的问题空间，含各框架解法 + 对比表，四条准则筛选）
  → Insights（按需：/query 存档 / /compare 存档）

演化层：
  → /evolve-apply（Wikipedia 风格 merge / split / redirect，Concept 页结构调整）
```

## Skills

| Skill | 职责 | 读/写 |
|-------|------|------|
| `/ingest` | 从源码提取 entity → 映射问题空间 → 匹配 concept → 写 concept 页。ingest 完成后 wiki 是完整更新的。 | 写 |
| `/query` | 回答问题：wikilink 遍历 + 检索升级链。有价值的结果存档为 insight。 | 读为主 |
| `/compare` | 多仓库在同一问题上的对比：Concept → Entity → 源码 三级升级链。 | 读为主 |
| `/lint` | 全量 wiki 结构性健康检查：wikilink 完整性 + frontmatter 合规 + repos 一致性 + 孤立页检测 + provenance 覆盖。用户手动触发。 | 读 |
| `/evolve-apply` | Wikipedia 风格 Concept 页演化：merge / split / redirect。独立工具，信号驱动或手动指定。 | 写 |
| `/completion-gate` | 共享质量门——所有写操作完成前必须通过。操作范围检查：本次写入文件正确性 + 维护文件同步 + frontmatter 合规 + 增量 wikilink 验证。不是用户直接调用，由其他 write skill 以 `REQUIRED SUB-SKILL` 引用。 | 质量门 |

**各 skill 职责独立，不互相合并。** 不要用"当前规模小"论证合并的合理性——工具职责由功能决定，不由当前数据量决定。

## 人机分工

| | 人 | LLM |
|------|-----|-----|
| 角色 | 策展来源、引导方向、提出好问题、思考意义 | 写一切：提取、分类、交叉引用、标记冲突、演化操作 |
| 动作 | 「这部分再展开」「比较 A 和 B」「这个方向值得深挖」 | 自主完成一轮工作，在暂停点汇报，告诉人做了什么、发现了什么、建议下一步 |
| ingest 中 | 暂停点介入：确认问题空间覆盖、候选清单、后续方向 | 暂停点之外自主执行 |

LLM 写、人读、人给方向、LLM 继续。不是人批准 LLM 的每一步产出。

## 关键设计原则

### 规模假设
**这个项目面向数百个仓库、数百个 concept、数百个 views/insights 的规模设计。** 永远不要用"当前只有 N 个仓库所以简单方案够用"来为设计决策辩护。每个决策必须回答"如果 500 个仓库，这个方案还能工作吗？"

### 知识组织
1. **知识累积性优先。** 每次 ingest 的产出归档为 wiki 页面，每次有价值的查询结果也归档。不能消失在聊天历史里。
2. **wikilink 网络就是图。** 不维护与 wikilink 重复的结构化图谱数据。
3. **Concept 页是主战场。** 跨仓库知识的真正累积发生在这里——新 repo 进来，更新已有 Concept 的实例列表、对比表。Concept 页的 depth 增长就是知识网的成长。
4. **index.md 只做路由。** 不列全部 concept——500 个 concept 时 index.md 仍然 < 600 行。LLM 读 index.md 后沿 wikilink 做语义路由。搜索靠 frontmatter + grep，不靠全量列表。

### Wikipedia 演化
5. **演化是内置机制。** 不是一次性提取完美的 concept，是靠有规则的持续演化（merge/split/redirect）。D 类信号在 ingest 暂停点当场处理，不推迟到另一个命令。
6. **/evolve-apply 是独立工具。** 既可以处理信号文件（信号驱动），也可以直接指定操作（用户手动），共享同一套前置判断+执行逻辑。

### 规模与性能
7. **增量更新是基础设施，不是优化。** 没有 delta tracking，每次 ingest 全量重读 500 个仓库源码的 token 成本不可接受。per-repo `.ingest-state.json` + SHA-256 content hash。
8. **搜索不靠全量扫描。** grep 能做精确匹配但做不了语义搜索。正确路径：index.md 路由 → wikilink 遍历 → frontmatter 定位 → LLM 判断相关性。不是把所有 concept 的 problem 字段都 grep 出来让 LLM 筛选。
9. **批量 ingest 可并行。** 用户一次扔多个仓库时，Step 1（Entity 提取）和 Step 2（问题空间映射）仅依赖单仓库源码，多仓库可并行执行。Step 3（匹配）需要等待所有仓库的 Step 2 完成后再统一处理——因为需要跨仓库对比。并行 vs 串行的分界线是"是否需要跨仓库信息"。

### Skill 调用模型
10. **Skill 是 LLM 的能力，不只是用户要记的命令。** 用户不需要显式输入 `/compare` 或 `/evolve-apply` 的完整语法。用户说"对比一下 A 和 B"、"把 memory 的两个 concept 合并"，LLM 应自动识别意图并调用对应 skill。Skill 文件中 Trigger 节的语法是给 LLM 认路用的，不是给用户背的。
11. **Skill 之间可以嵌套。** 用户在 `/compare` 过程中说"这两个 concept 合并"，就是在 compare 流程中插入了 evolve 操作。这是正常的——LLM 在执行一个 skill 时收到了另一个意图，应该暂停当前 skill、执行嵌套操作、然后回到原 skill 继续。不需要等第一个 skill 完整结束。log.md 记录操作来源（如 `[触发: /compare 对话中]`）。

### 仓库分类
12. **不设单一 category。** 仓库用 GitHub topics 做多标签（`ai-agent` `python` `event-driven`），tags 只帮发现，不限制对比范围。对比范围由 Concept 的 `repos:` 字段动态定义。

### 文件格式
13. **Frontmatter 为模型设计。** entity 页和 concept 页的 YAML frontmatter 包含 `type`、`problem`、`repos` 等字段，模型读前 10 行即可判断文件类型和内容，不必读全文。
14. **Wikilink 有语义。** 每个 wikilink 从"这里在提到什么，那个东西有独立页面"出发，不是为凑图而加。entity → concept、concept → entity、overview → entity 三类链接各有含义。

### 内容保鲜
15. **任何交互中发现不准确就必须修正，且修正是原子闭环。** `/compare`、`/query`、或日常对话中，当 LLM 从源码拿到比 Concept 页（或 Entity 页）更准确/更完整的信息时，必须：
   - (a) 主动展示 diff（旧描述 → 新描述），告知用户差异
   - (b) 用户确认后当场写入 wiki 页
   - (c) **如果是对比/查询过程中发现 → 修正后重新生成受影响的输出（如 `/compare` 重新计算对比、`/query` 刷新答案），不是修完就停**
   - (d) 日志标记触发来源：在父 command 的日志行尾追加 `[源码验证: <页名> <节名>修正]`
   
   这一条的全称是"wiki 知识保鲜闭环"，是所有读-写 skill（`/compare`、`/query`）的共同行为规范。各 skill 文件中必须覆盖此行为。

### 插件通用性
16. **这是个通用插件。** SKILL.md 中的所有路径使用相对于 wiki 根目录的相对路径（`wiki/concepts/`），绝不写死本地绝对路径如 `/Users/xxx/Work/codebase-wiki/`。

## 文件格式规范

### Entity 页 frontmatter
```yaml
---
type: entity
repo: <name>
slug: <slug>
problem: <问题层一句话，"如何..."形式>
generated: <YYYY-MM-DD>
source_files:
  - <repo-relative-path>
---
```

### Concept 页 frontmatter
```yaml
---
type: concept
concept: <slug>
problem: <核心问题，一句话>
concerns: [<关切1>, <关切2>]
repos: [<仓库列表>]
generated: <YYYY-MM-DD>
---
```

### 重定向页 frontmatter
```yaml
---
redirect_to: <slug-target>
reason: <一句话>
date: <YYYY-MM-DD>
---
```

### 维护文件
- `wiki/index.md`：路由页，Repos 表 + 搜索入口指引。不列全部 concept/view/insight
- `wiki/log.md`：只追加，每行 `[<ts>] <操作> <详情>`
- `wiki/hot.md`：覆盖写入，Last operation + Active repos + Concept count + Pending signals count

## 工具调用规范

每轮工具调用必须分批执行，每批不超过 3-4 个并行调用。发出一批、等结果回来、再发下一批。

读大文件时使用 `offset`/`limit` 参数只读需要的部分；Bash 命令输出加 `| head -N` 限制长度，避免大量 token 一次性追加到上下文。

## 测试与验证规范

**所有测试、验证、场景模拟必须在独立 subagent 中执行，绝不在主上下文中直接执行。**

原因：主上下文的 token 预算应留给决策、分析和编排。测试产生的噪音（大量的 lint 输出、文件读取、验证逻辑）会污染上下文，降低后续决策质量。subagent 有独立上下文窗口，测试在其内部完成，只把结论和摘要回报主 agent。

适用的操作类型：
- `/ingest` 的执行（Entity 提取、问题空间映射、Concept 写作）→ subagent
- `/lint` 的运行及结果分析 → subagent
- 场景模拟（如"模拟用户否决 Concept B 类"）→ subagent
- 对比验证（如"与实验基线比较 entity 数量"）→ subagent
- `pytest` 测试运行 → subagent
- 任何读取超过 10 个文件的操作 → subagent

不适用：单文件查询、用户直接提问、摘要性任务（如"这个 concept 讲了什么"）。

反例：`python scripts/lint.py 2>&1 | head -80` 直接在主上下文跑 → **禁止**。正确做法：启动 subagent 跑 lint，只返回摘要。
