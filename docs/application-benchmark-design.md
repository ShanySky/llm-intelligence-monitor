# 应用型智能评测设计

## 目标

本题库主要服务于真实使用场景：

1. 编程方案讨论 / 架构取舍；
2. Coding / Debug / Code Review；
3. Agent 工具使用与调查路径；
4. 压缩版长程任务：目标保持、阶段依赖、修正与验证。

单题目标 3–5 分钟，绝对上限 10 分钟。难度来自决策密度、约束冲突、验证意识和多步依赖，而不是单纯增加计算量。

## 外部设计参考

### SWE-Lancer Manager
借鉴“给出真实工程上下文 + 多个可行实现方案，由模型选择最佳方案”的形式。
重点测：约束理解、方案权衡、风险识别、工程判断。
不复制公开任务，自己构造代码库背景与候选方案。

### SWE-bench / SWE-rebench
借鉴“真实 bug / feature + 可执行验收”的形式。
我们的日常版压缩成小代码片段或微型仓库；最终成熟版可加入少量真实可运行 micro-repo 任务。
重点测：根因定位、最小充分修改、避免回归、验证意识。

### Terminal-Bench / LoopsBench
借鉴“环境有状态 + 允许工具调用 + 最终结果由 verifier 判断”的形式。
由于日测单题必须控制在 5 分钟级，先设计压缩版 Agent 路径题；后续再加入少量可执行 micro-agent 任务。

### SWE-EVO / RoadmapBench
借鉴多目标、跨文件、需求演化、阶段间依赖。
我们的做法是把数小时长程任务压缩成若干关键检查点：
理解目标 -> 选择方案 -> 实施关键步骤 -> 根据新证据修正 -> 验证最终目标。

## 评分原则

- 优先 deterministic grading，不依赖 LLM judge。
- 不奖励“说得漂亮”，只奖励真正满足约束的选择/结果。
- 方案题必须存在多个表面合理的候选项，避免常识题。
- Coding 题优先测根因和最小充分修复，而不是语法记忆。
- Agent 题测“下一步最有信息价值的动作”，避免无脑多查。
- 长程题测是否维持原始目标、处理新证据、避免漏项并最终验证。
- 同一题型通过校准后再参数化生成多个实例，降低污染和记忆影响。

## 经过首轮原型后的调整

首轮文字型应用题暴露出两个问题：

1. 只做方案/补丁选择，即使加入多个约束，Sol Medium 仍容易封顶（当前常驻为 GPT-6.1 Sol；此前 GPT-6 Sol 校准也出现同类现象）；
2. 严格字符串 equals 会把逗号后的无关空格误判成智力错误。

因此后续正式设计采用两层评分：

- semantic score：忽略无意义格式差异，只看工程结论/最终行为是否正确；
- instruction-format score：单独记录格式遵循，不混入核心智力分。

## 推荐的混合题库结构

### A. 可执行微型仓库任务（核心）
- 真实读文件、改代码、跑测试；
- 隐藏 verifier 判定最终结果；
- 单题目标 2–5 分钟，硬上限 10 分钟；
- 主要覆盖 Coding、Debug、Agent 工具使用、压缩长程执行；
- 不做中英文镜像，避免无意义翻倍成本。

### B. 仓库上下文方案决策题
- 采用 SWE-Lancer Manager 思路；
- 提供真实感较强的代码库片段、issue 和多个接近可行的方案；
- 重点测架构取舍、方案讨论、风险识别、实施顺序；
- 用客观 checklist / 决策集合评分，不只做简单四选一。

### C. 快速诊断题
- 保留少量高区分度抽象推理、状态追踪、代码语义题；
- 用于快速发现异常和维持低成本日测；
- 只有经实测证明有区分度的题才能进入正式题库。

### D. 压缩长程任务
- 不是让模型跑数小时；
- 用 3–5 分钟内的多阶段仓库任务模拟：目标保持、阶段依赖、新证据修正、验证闭环；
- 通过多个隐藏检查点给部分分，避免单一 pass/fail 丢失信息。

## 日常运行原则

日测不全量跑所有可执行任务。采用“少量固定锚点 + 轮换应用任务”：
- 每日只抽少数可执行微型仓库任务；
- 其余使用低成本快速题；
- 更重的完整应用套件只在校准、模型变更或人工触发时运行。

这样既保持真实应用相关性，又控制时间和 Token。

## Frontier 校准后的题目设计约束

新一轮可执行任务校准表明，仅仅把要求分散到多个文件，或者加入并发、重试、
恢复等关键词，并不足以形成有效区分。若这些要求彼此独立、可以逐项直接恢复，
Luna High 也可能稳定封顶。

后续 frontier 候选题优先满足：

- **因果耦合而非清单堆叠**：一个修改会改变另一个模块的行为，模型必须恢复跨层不变量；
- **验证驱动修正**：第一次合理修复后，新的验证结果应暴露下一层问题，要求模型继续调查和修正；
- **冲突约束**：兼容性、并发、事务、幂等、生成源/派生文件等约束需要共同满足，而不是独立打勾；
- **真实 source of truth**：需要识别应该修改源文件、生成器、配置源或运行时实现中的哪一层；
- **Harness 上限不得制造质量差**：正式确认 reasoning-effort 差异前，turn/shell 上限应足够宽松，
  主要由单题 wall-clock 硬上限约束；撞到预算上限的单次大分差只能算诊断信号；
- **保留失败产物**：候选筛选和 effort 校准保留最终源码、Agent 元数据和关键执行产物，
  用于区分真实能力失败与评分/Harness 截断。

候选题仍先经过 Luna/Sol 低成本漏斗。Luna 已封顶的任务只作为覆盖检查，不再进入昂贵的
Sol Medium / High / X High effort 校准。



## 第二阶段候选题设计约束

近期校准已经反复出现一个现象：只要任务的关键约束能够通过“把静态文档全部读完”恢复成完整 checklist，Luna High 或 Sol Medium 很容易直接封顶。后续用于区分模型/思考档位的候选题必须进一步收紧。

### 禁止把困难做成提示词困难

- TASK 只描述真实的目标和可观察症状，不直接枚举所有正确实现条件。
- 不用更多文字、更多文件、更多步骤本身制造难度。
- 不允许隐藏 verifier 考察仓库和任务目标都无法合理推导的秘密要求。
- 工具调用次数和 turn 上限默认只作为安全护栏，不能作为制造模型分差的主要手段；一旦触顶且得分低，必须先按预算混淆处理并放宽后复测。

### 区分题至少包含一种“运行时发现”

候选题若以区分 frontier 模型为目标，至少一个关键约束必须通过以下证据之一才能可靠恢复，而不能只靠读 TASK/context 得到：

- 运行测试后出现的新失败；
- 诊断命令 / 日志暴露的第二阶段事实；
- 生成物与源定义不一致；
- 版本兼容样本与当前实现之间的冲突；
- 故障注入、重试、并发执行后才能出现的边界；
- 修改第一处问题后，验证结果迫使模型修正最初假设。

目标是模拟真实工程中的“调查 -> 假设 -> 修改 -> 验证 -> 新证据 -> 修正”，而不是“读需求 -> 一次性实现 checklist”。

### 筛题漏斗

1. Luna High 先筛明显简单题；非预算受限情况下 >=95 分默认标为 coverage-only ceiling。
2. 只有 20–95 分之间的候选，或存在明确非封顶行为证据的候选，才进入 Sol Medium / High / X High。
3. 任一档触及 turn / shell 上限且质量不满分时，先扩大到非绑定预算再判断，不把 Harness 截断误认为模型能力差异。
4. effort 差异必须至少重复两轮，并要求差异方向在多数复测中一致；单次 0/100 只算候选信号。
5. 正式区分题优先保留可解释的失败域：遗漏隐藏依赖、错误因果链、未验证、错误恢复、跨层不一致，而不是格式或措辞。

### 当前已确认的反例

以下困难来源已经实测不足以单独形成稳定 effort 区分：

- 仅把兼容性约束分散到多个静态 context 文件；
- 经典 outbox / lease fencing / single-flight 等模式，但所有所需事实都静态可见；
- 两阶段 incident，但每次 verify 直接明确告诉下一步根因；
- 仅靠较低 shell / turn budget 截断长工具轨迹。

这些题仍可保留为覆盖面或回归题，但不应占用 reasoning-effort 区分题的核心权重。

## Core Signal 与证据型 Agent 评分

应用套件明确区分三类角色：

- **core**：重复验证后确认有稳定信息量，可影响 Core Signal；
- **candidate**：正在验证中的潜在区分题；
- **coverage**：真实应用相关但前沿模型已容易封顶，仅用于防回归与能力覆盖。

正式晋级不接受单次分差。跨模型题要求重复横向验证；reasoning-effort 题要求重复 Medium / High / X High 校准并满足方向一致性。Final Suite 的单次结果只用于观察当前状态，晋级证据以 frontier registry 中的重复验证记录为准。

Agent 调查 Harness 增加 opaque `probe`：

- probe 源码和路径不暴露给模型；
- 模型必须主动提出诊断问题或控制实验；
- Harness 记录实际 query、返回 observation 和调用次数；
- scorer 可以要求模型真正获得某项因果证据，而不是只检查 query 关键词；
- probe 次数、耗时、Token 属于效率信号，不和质量分混淆。

下一阶段 effort 区分题优先采用**反事实/干预型调查**：观测相关性不足以确定根因，模型必须设计保持其它变量不变的实验，才能拿到完整证据分。



## Correctness Gate 与 Patch Quality

应用型 Coding 任务不再把“hidden tests 全过”直接等同于高质量完成。

正式评分分两层：

1. **Correctness Gate**：visible / hidden verifier、兼容性、恢复窗口、并发边界等行为检查。未达到行为门槛时，不讨论 patch quality。
2. **Patch Quality**：仅在行为门槛通过后，客观衡量补丁是否符合最小充分实现：
   - 是否修改了任务说明、visible tests 等禁止区域；
   - 是否触碰与故障域无关的源码；
   - 是否新增/删除不必要文件；
   - changed files / changed lines 是否明显超过参考修复域；
   - 公共接口与兼容路径是否仍由行为验证保证。

Patch Quality 默认只作为独立维度展示，不静默混入 intelligence quality。只有经过跨实例重复验证，确认该维度能稳定反映 reasoning effort / model 差异后，才允许进入 Effort Core 或 Model Core。

这样做的目的，是避免当前前沿模型在行为测试上同时封顶后失去区分力，同时也避免使用主观 LLM Judge。对 real-repo replay 类型任务，测试通过是必要条件，补丁完整性、工程等价性与改动纪律才是 gate 之上的主要信息来源。

## Real-Repo Replay

Synthetic micro-repositories remain useful for coverage, hidden-edge regression and
cross-model Model Core tasks, but repeated calibration showed that frontier Sol
reasoning levels often saturate them.

Effort Core therefore prioritizes **real repository replay**:

- choose a small historical maintenance commit from this repository;
- build the agent workspace from the target commit's parent with `git archive`;
- do not copy `.git`, the target commit, target diff, hidden fixtures or reference
  patch into the agent workspace;
- present only the original maintenance objective in `TASK.md`;
- use hidden behavior fixtures as the correctness/equivalence gate;
- score patch discipline separately from behavior: touched files, forbidden areas,
  unnecessary files and excessive footprint;
- reference commits must pass a 100% hidden self-check before any model run;
- only cross-instance repeated resident-Sol evidence can enter Effort Core.

The replay family intentionally uses small real changes so individual tasks normally
fit the 3–5 minute target and remain below the 10 minute hard limit.


### Replay 超时与有效样本

Real-repo replay 的能力证据必须来自 runner 已写出遥测的样本。若外层 Workflow 在 runner 写出 `light-agent-result.json` 前终止，样本标记为 `pre_telemetry_timeout` / 数据不完整，不允许进入 Effort Core 统计。

runner 自身的 wall timeout 会在外层 timeout 前写出遥测，并以模型超时结束；这类样本可以用于可靠性/预算诊断，但在 reasoning-effort 晋级分析中视为 budget-confounded，不能把“某档更容易超时”伪装成稳定质量差异。

### Real-repo replay 主集与后备集

Real-repo replay 的正式 Effort Core 校准使用经过 reference self-check 的 **required cases**。每个 required case 的历史目标提交必须在隐藏行为 verifier 上自检为 100 分，否则整轮正式校准停止。

Backup replay cases 仅用于主集区分力不足时扩展样本。它们可以提前保存在仓库中并记录自检状态，但 **backup 自检失败不得阻断 required cases 的正式运行**；只有 backup 自身通过 reference self-check 后，才允许加入 Effort Core 证据。

### 防止单次变体造成 Effort 假确认

同一题型的 3 个不同变体只代表**覆盖度**，不能替代重复实验。`trial_mode=variants` 的正式 Effort Core 晋级必须为每个变体、每个思考档位保留至少 2 个独立的 `repeat` 轮次记录；任一变体缺少成对复测，整族只能保持 candidate。预算触顶、缺遥测或 API/Harness 故障样本不计入复测证据。Luna 单档筛题始终只能产生筛选信号，不能用于 Effort Core 晋级。

### 模型质量与请求超时分离

如果单次 Responses API 请求在 Agent 总 wall-clock 截止前触发客户端 timeout，无法确认根因是模型思考、网关排队还是网络传输；此时标记为 `infrastructure_error` / 数据不完整，不计入模型质量比较。若达到 Agent 任务总时限，标记为 `model_timeout`，在报告中单列完成率与耗时；即使工作区的隐藏测试已通过，该样本也属于 `budget-confounded`，不得用来确认 reasoning-effort 差异。Replay Markdown 报告同时展示 `Outcome` 和 `Quality evidence`，防止将未按时完成的补丁原始分误当成完成质量。

### v2 replay 退役记录

2026-10-08 的 v2 replay 使用 Luna High 先筛（45、25、100），随后仅对两道非封顶题跑 GPT‑6.1 Sol M/H/XH。六个 Sol 样本中有五个未按任务时限正常完成，结果为 `budget-confounded`，不可晋级 Effort Core。当前 v2 题族从付费验证漏斗退役并默认禁用；不应通过增加复测次数来掩盖任务体量/请求超时问题。后续重新选择更短、更密集的跨文件隐藏依赖场景，先完成无成本 reference self-check 和 Luna 低成本筛选。

### 最终应用报告有效样本门槛

`application-final` 的总体质量分和 Core Signal **仅**从 `outcome=completed`、具有完整遥测、没有 `model_timeout` / turn / shell budget saturation 的样本计算；未完成的工作区仍可保存原始 patch score 与 Token/耗时，但 `data_complete` 和 `core_data_complete` 不得宣称质量验证完整。应用差异分析不得把这样的样本晋级，maturity 验收必须确保当前全部模型配置的实际质量证据完整，而非只凭任务是否存在或历史 registry 状态。
