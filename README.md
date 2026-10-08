# LLM Intelligence Monitor

> **V1.1 公开基准优先：** 已整理并核对 [20 道 Java/Vue/JS 官方候选](docs/V1.1-PUBLIC-BENCHMARK-SCREEN.md)；20 道仅确认元数据，其中 Gson #2311 已完成官方 Docker baseline→gold 验证（46 秒）；其余候选环境及所有模型表现尚未验证。原先自造题探索已止损，开发仍在 Draft PR，日测仍关闭。

> **V1.1 区分度研发中：** 已新增三实例跨边界故障恢复候选、客观隐藏检查与免费参考自检。当前仅开发分支 [v1.1-discrimination-upgrade](https://github.com/ShanySky/llm-intelligence-monitor/tree/v1.1-discrimination-upgrade)，**尚未证明模型/档位分差或发布 V1.1**。详见 [V1.1 记录](docs/V1.1-CALIBRATION.md)。V1 Core 与自动日测关闭状态不变。

## V1 Core 可用试用版（2026-10-08）

**先上线、后完善。** 默认通过 [Final application benchmark validation](https://github.com/ShanySky/llm-intelligence-monitor/actions/workflows/application-final-validation.yml) 手动运行 `v1-core`：两个 Model Core 题型 × 四模型 High，结果独立写入 `application-v1-results`，不覆盖原完整评测。V1 最低可用不要求 Effort Core 已成熟，单次成绩不能作为稳定排名。详见 [V1 快速开始](docs/V1-QUICKSTART.md)。自动日测仍关闭。

用于长期监控 GPT 等大模型是否出现能力下降的轻量回归测试项目。

## 快速监控策略

完整题库保留大量中英文镜像题，但单次快速监控不会全量运行。自 2026-10-05 起，自动日测 `schedule` 已停用；该通道保留为按需人工运行，`monitor-config.json` 中的 `daily` 字段继续作为兼容性的快速监控参数名。

默认快速监控配置：

- 固定锚点题：8 道
- 分层轮换题：8 道
- 每道原始题同时测试中文和英文版本
- 每模型每题默认只运行 1 次
- 因此默认每个模型每轮执行：16 道原始题 × 2 种语言 = 32 次测试

固定锚点用于保证不同日期之间有稳定可比基准；轮换题用于扩大题库覆盖面，降低模型对固定题集适配造成的失真。

轮换抽题不是纯随机，而是同时考虑：

- 难度：标准 / 困难 / 极限 / 超高难
- 能力：推理 / 数学 / 代码 / 指令遵循

同一天使用中国日期作为确定性种子，因此当天重复运行会抽到同一批轮换题，方便复测和问题定位；第二天才会轮换。

## 题目健康度与锚点退役

历史正式日测已按单题累计健康度判断题目是否还有信息量；当前按需快速监控继续读取已有健康度数据进行选题：

- 长期接近全模型满分、模型间差异很小的题标记为 `stable-ceiling`；长期接近全模型全错且无模型差异的题标记为 `stable-floor`。两类低信息题都会自动降权；
- 能拉开模型差异的题提高轮换权重；
- 难度处在有效中间区间的题适度提高权重；
- 高波动但缺少稳定模型差异的题降权，避免随机噪声主导日报。

固定锚点不会因为一天结果自动更换，避免破坏跨日期基线。若固定锚点在至少 3 个正式样本日后持续处于 `stable-ceiling` 或 `stable-floor`，健康度报告会将其标记为“下一次 anchor 版本切换的退役候选”，由题库版本升级时集中替换。


## 参数调整

快速监控参数集中在根目录：

`monitor-config.json`

默认：

```json
{
  "daily": {
    "anchorCount": 8,
    "rotatingCount": 8,
    "repeat": 1
  }
}
```

以后需要改成 7+7、8+8，只需要修改：

- `anchorCount`
- `rotatingCount`

不需要修改抽题代码或 GitHub Actions。

手动运行 GitHub Actions 时，也可以临时覆盖这三个参数，而不修改仓库配置。

## 中英文镜像

每个原始题必须同时存在：

- 中文版本
- 英文版本

两者使用完全相同的数据、约束和标准答案。

报告分别统计：

- 总成绩
- 中文成绩
- 英文成绩
- 同题中英文表现差异
- 每个模型输入 / 输出 / 推理 / 总令牌（Token）

## 运行方式

自 **2026-10-05** 起，自动日测已停用，仓库当前没有快速监控的 `schedule`。

需要检查模型状态时，通过 **Actions → LLM intelligence manual monitor → Run workflow** 按需运行；也可以只修改专用的 `.github/triggers/daily-monitor.txt` 触发一次受控运行。普通代码、文档或评分器提交不会触发模型评测。

按需运行会：

1. 生成固定锚点 + 分层轮换题清单；
2. 使用 Promptfoo / Responses API 执行测试；
3. 汇总正确率、错误、超时、Token 与响应时间；
4. 上传 JSON / HTML / Markdown 报告；
5. 发送“手动测试”邮件报告。

按需运行**不写入正式历史基线，也不参与自动降质/路由异常判定**。历史 `history` 分支继续保留旧正式日测结果，供题目健康度和趋势研究使用。

## 每周深度测试

配置中预留了 `deepTest`，但当前：

```json
"enabled": false
```

目前没有任何每周深度测试定时任务，也不会自动执行。后续只有确认有价值时再开启。

## 必需的 GitHub Actions Secrets

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_TO`

模型请求仍通过实际使用的 OpenAI-compatible 中转链路运行，以尽量贴近真实使用环境。


## 四模型 X High 并行测试

当前快速监控默认支持四个模型：

- GPT-6 Astra X High
- GPT-6.1 Sol X High
- GPT-6 Luna X High
- GPT-5.6 Sol X High

GitHub Actions 使用模型矩阵并行运行：四个模型分别在独立 job 中同时执行同一批题；每个模型内部最多并发 2 个请求，因此峰值约为 8 个并发模型请求。

默认快速监控为 8 道固定锚点 + 8 道分层轮换题。每道原始题同时运行中文、英文镜像版本，因此每个模型每轮默认执行 32 个测试。

报告额外统计固定锚点上的正确率、平均响应时间、平均输出令牌、平均推理令牌（Reasoning Token）和平均总令牌，用于辅助识别“正确率下降 + 思考变少 + 响应变快”的异常模式。

GPT-6.1 Sol 作为新的模型纪元与旧 GPT-6 Sol 历史严格分离。历史趋势按 provider 名精确匹配，不会把旧 GPT-6 Sol 样本并入 GPT-6.1 Sol；当前按需运行不写入正式趋势基线，旧结果仅保留用于历史对照。


## 超时与错误统计

快速监控报告区分：

- 普通答错：模型正常返回答案，但答案不正确；
- 超时：模型在单题超时上限内未完成；
- API 错误：接口、网关或其他请求错误。

“有效回答正确率”只统计实际返回答案的测试。超时/API 错误不会再被当作普通答错，但超时率会作为独立异常指标进入趋势监控。

H03、U03 等高成本长链计算题保留在完整题库中，但不再作为快速监控固定锚点或轮换题。


## 评分与重试策略

默认每个模型每轮固定执行 32 个测试，横向比较始终使用固定题目分母：

- 正确：计 1 分；
- 普通答错：计 0 分；
- 超时：该题计 0 分，并额外按 0.25 道题等价值扣分；
- API / 网络 / 5xx 等执行错误：由 Promptfoo 最多重试 1 次。

报告同时展示：

- 基础正确率：正确题数 / 全部 32 道测试；
- 综合分：基础得分减去超时额外惩罚；
- 正确 / 答错 / 超时 / API错误数量；
- 中文、英文基础正确率；
- 固定锚点上的响应时间与 Reasoning Token。

如果重试后仍存在 API 错误，该模型本轮综合分标记为“数据不完整”，不参与模型间横向比较，也不作为降质判定样本。


## Selective manual model runs

Manual runs can execute all configured models or only selected models.

In **Actions → LLM intelligence manual monitor → Run workflow**, set `models` to:

- `all` — run every configured model;
- `gpt-6-luna` — run only GPT-6 Luna X High;
- `gpt-6-1-sol,gpt-6-luna` — run multiple selected models.

Manual runs do not write formal history and do not participate in degradation or routing-anomaly judgments.

Email delivery uses an HTML body for normal reading, includes a plain-text fallback, and attaches the complete Markdown report.


## History branch

Historical formal monitoring results are stored on the dedicated `history` branch under `history/YYYY-MM-DD.json`. Automatic daily monitoring is currently disabled, so manual runs do not append new formal history.

The `main` branch contains only source code and configuration; historical formal monitoring never wrote result history back to `main`, and current manual runs do not write formal history.

If the complete history directory ever needs to be restored into `main`, do it explicitly instead of merging the whole history branch:

```bash
git switch main
git restore --source=history -- history/
git add history/
git commit -m "Restore monitor history from history branch"
```

This restores every retained history file, including files that are intentionally absent from `main`.


## High manual run mode

A controlled manual run can execute all configured models at reasoning effort `high` without changing the default X High configuration or writing formal history.


## 应用型智能评测

除了原有的低成本固定题/轮换题，本项目增加一条独立的应用型评测通道，用于更贴近实际开发工作地衡量模型能力。

重点覆盖：

- 编程方案讨论与架构取舍；
- Coding / Debug / 多文件修改；
- Code Review 与生产可靠性分析；
- Agent 工具使用与证据驱动排障；
- 压缩版长程任务：跨阶段目标保持、发现新证据后的修正、最终验证闭环。

### 执行方式

正式应用型评测使用项目内的轻量 Agent Harness：

- Responses API；
- 受控 shell 工具；
- 隔离的微型仓库工作区；
- 模型不能读取 GitHub Secrets；
- 每题目标 3–5 分钟；
- 单题硬上限 10 分钟。

完整 Codex CLI Harness 仅作为研发/对照工具，不是正式评测的依赖。

### 评分原则

应用题优先使用客观隐藏检查点，而不是 LLM Judge：

- 最终代码/行为是否正确；
- 是否满足隐藏边界场景；
- 是否保持兼容性；
- 是否遗漏关键故障窗口；
- 是否完成必要验证；
- API / 网络 / Harness 故障单独记为数据不完整，不当作模型答错。

文字型方案/评审题采用语义域检查，忽略无意义格式差异。只有重复验证后仍表现出稳定区分度的任务，才允许被标记为正式的模型/思考档位区分题。

### 运行分层

- **快速智能监控**：继续使用 Promptfoo 低成本题库，当前按需人工运行；
- **应用型校准**：使用轻量 Agent Harness，小规模筛选候选任务；
- **最终应用验收**：`Final application benchmark validation` 工作流，对多个模型以及 GPT-6.1 Sol Medium / High / X High 做完整对照；
- **稳定性复测**：只重复真正有区分信号的任务，不整套重跑。

应用型任务不加入快速监控，避免 Agent 工具调用和长上下文显著放大 Token 成本。仅在模型版本验收、疑似降智或题库校准时按漏斗运行必要套件。

### 应用题选择规则

候选题必须同时满足：

1. 难度来自真实工程能力，而不是故意刁钻或纯粹增加工作量；
2. 需求和代码库足以确定正确行为，隐藏测试不能考未说明的实现细节；
3. 单题在 10 分钟硬预算内；
4. 评分可客观复现；
5. 模型间区分可由完整横向验收确认；
6. 同模型思考档位区分必须有重复试验支持，单次分差只算候选信号。

当前应用型评测的详细设计见 `docs/application-benchmark-design.md`。

### Frontier 题目注册表

`benchmarks/frontier-registry.json` 记录每道应用候选题的当前成熟度和实测证据，包括：

- `screening`：仍在 Luna / 低成本筛选；
- `model-discriminator-confirmed`：已通过重复跨模型验证，可进入正式应用套件；
- `coverage-only-ceiling`：对当前前沿模型已封顶，只保留覆盖/回归价值；
- `needs-opaque-rescreen`：旧证据受 Harness/validator 隔离问题影响，需要重新验证；
- effort 信号单独记录，不能用单次分差或预算触顶冒充。

核心漏斗只继续消耗尚未定性的候选；已封顶题不反复进入昂贵校准。固定 coverage 题仍可保留用于回归，但不占 reasoning-effort 区分题权重。

### Core Signal 与 Coverage 分离

完整应用套件不再把所有题简单平均后当作“智能分”。

- `core`：已经经过重复验证、确认具有稳定模型区分信息的题型；
- `candidate`：有信号但尚未完成重复验证；
- `coverage`：对真实场景重要，但当前模型容易封顶，主要承担回归覆盖。

报告同时显示 Overall Quality 与 Core Signal。只有至少 2 个已确认 core 题型族完整存在时，Core Signal 才标记为 mature。当前已确认的 core 包括跨文件可靠性 Code Review 与 Agent incident investigation；单次 Final Suite 分差不能直接把 coverage 题晋级为 core。

Agent 调查题支持 opaque `probe` 工具。模型只能看到 probe 返回的运行时证据，不能读取 probe 实现；Harness 会记录实际 query + observation，证据分根据真实返回结果判定，而不是根据“问过哪些关键词”判定。后续更难题优先要求控制变量/反事实实验来证明因果，而不是把所有组件静态查一遍。

### 应用评测成熟度

正式应用报告把信息分成三层，避免大量容易封顶的 coverage 题掩盖真正的能力差异：

- **Coverage**：保证方案、Coding、Review、Agent、长程任务等真实场景都有行为回归覆盖；
- **Model Core**：只包含经过重复横向验证、能够稳定区分模型的题型族；当前成熟门槛为至少 2 个独立题型族；
- **Effort Core**：只包含跨多个实例重复验证后，能够稳定体现 reasoning effort 质量差异的题型族；可以是 Medium → X High 正向提升，也可以是稳定的非单调/反向敏感，但必须达到配置的质量 spread 阈值并明确标注方向；当前成熟门槛为至少 1 个。

只有 Model Core 和 Effort Core 都达到门槛，应用评测才标记为整体 mature。单次 Final Suite 的分差只能作为诊断信号，不能自动晋级。

题目研发状态统一记录在 `benchmarks/frontier-registry.json`。已经确认封顶的任务可以继续作为 coverage，但不会重复进入昂贵的 effort / cross-model 漏斗。

### Reasoning Effort 低成本筛选

Medium / High / X High 的前置筛选不再只使用整题 pass/fail。对于可拆分的方案、Review、Agent 和长程决策题，Promptfoo assertion 可返回 0～1 的**客观部分分数**，分别反映关键约束召回、错误决策、必要顺序等可验证子目标。

报告同时保留：

- 完全通过率；
- 平均客观分；
- Medium → X High 分差；
- 重复样本数与方向形状。

正式 Effort Core 仍要求跨实例、重复、非预算混淆的稳定质量差异；部分分数只是提高测量分辨率，不降低晋级门槛，也不使用 LLM Judge。

### Frontier 候选漏斗

新应用题不直接进入完整多模型套件，而按成本漏斗推进：

1. Luna High 先筛；非预算受限情况下得分 ≥95 的任务默认只保留为 coverage，不再进入昂贵 effort 校准；
2. 自然落在 20–95 分区间的任务进入 Sol Medium / High / X High；
3. 单次分差必须进入重复稳定性验证，预算触顶样本先按 Harness 混淆处理；
4. 质量差异与效率差异分开统计，不能用更慢、更多 Token 的高档思考冒充能力提升；
5. 只有稳定信号才进入 Astra / Sol / Luna / 5.6 Sol 横向验收。

Frontier 任务允许使用受限黑盒 validator 作为运行时证据，也支持 staged Harness 在后续阶段动态揭示新的仓库文件和验证证据。未来阶段内容在揭示前不可被 Agent 读取，避免把长程任务退化成“一次读完全部 checklist”。

### Real-repo replay

Reasoning-effort validation now includes a real-history replay lane. Each replay task
starts from the parent of a real maintenance commit in this repository, extracted
without `.git`; the model cannot inspect the target commit or reference diff.

Hidden fixtures first score behavioral equivalence. Once the correctness gate passes,
objective Patch Quality measures whether the implementation stayed inside the intended
repair surface without test edits or unnecessary footprint. Target commits must pass
the same hidden fixture at 100% before a replay task is accepted.

This lane is the preferred Effort Core source when synthetic micro-repositories
saturate at Medium/High/X High. Synthetic tasks remain valuable as coverage and Model
Core tests.


## GitHub Actions 触发治理

为避免研发阶段的 benchmark Workflow 在每次普通提交时全部创建 `skipped` run：

- 当前快速监控 `schedule` 已停用；若未来恢复周期运行，也只允许快速监控通道使用 `schedule`；
- benchmark / calibration / report refresh 默认使用 `workflow_dispatch`；
- 需要从提交触发时，只允许监听各自的 `.github/triggers/*.txt` 专用触发文件；
- 禁止重新使用“所有 `main` push 都创建 run，再靠 job-level `if` 跳过”的模式；
- funnel 判断为 coverage-only / retired 时应正常 skip，不应使用非零退出码制造 failure 邮件；
- 历史 Actions 清理只删除 skipped / cancelled，成功结果和失败诊断默认保留。

### Real-repo replay 漏斗（v2）

`benchmarks/real-repo-replay/config.json` 的 `mode=screen` 表示只运行 GPT-6 Luna High，每个 v2 历史 replay case 一个样本。结果分支的 `replay/latest.json` 同时包含 `screening.decisions`：`coverage-only-ceiling` 不再进入 Sol 校准；`invalid-or-budget-confounded` 先修正环境/预算；只有 `effort-calibration-candidate` 才值得进一步运行 GPT-6.1 Sol Medium/High/X High。此筛选结果**不能**直接确认 Effort Core，必须经过跨实例、重复的 Sol 校准。v1 replay 的 440 秒预算触顶结果不作为能力区分证据。

### Replay v2 筛题记录（2026-10-08）

Luna High 参考自检 3/3 为 100 分；模型筛题分：`core-signal-summary` 45、`repeat-sample-policy` 25、`quick-monitor-floor-health` 100。前两题进入 GPT‑6.1 Sol M/H/XH **单轮候选诊断**；100 分题仅保留 coverage/reference self-check，不加入付费校准。单轮分差不得进入正式 Effort Core，正式晋级还要求更多独立变体与同变体重复验证。

### Replay v2 校准结论（2026-10-08）

单轮 GPT‑6.1 Sol Medium/High/X High 校准（现有 Actions run `37713197713`）共有 6 个样本：**正常完成 1 / 模型或请求超时 5**。`core-signal-summary` 的补丁原始得分为 100/96/25，`repeat-sample-policy` 为 25/25/25，但**不能据此解释档位能力差距**，因为前者三档均超时，后者 Medium/X High 超时。正式结论为 `budget-confounded`、`do-not-promote`，不存在已确认 Effort Core。当前 `real-repo-replay/config.json` 已设置 `enabled: false`，避免对已判定无效的题族继续自动/误触发付费运行。待新短程、有隐藏依赖的真实历史题通过 reference self-check，再按 Luna→Sol 漏斗启动。

### 应用报告的质量证据有效性

`Overall Quality` 和 `Core Signal` 仅统计**正常完成且未触及执行预算**的任务。隐藏测试即使给未完成的补丁较高分，也只保留为诊断产物，不得冒充模型质量或思考档位信号。超时的执行轨迹、Token、耗时继续保留，并单独计入完成可靠性；相应模型配置的 `data_complete=false`，最终 maturity 检查必须显示 `final_quality_evidence_complete=false`。两项无 API 费用回归测试由现有 replay Workflow 的 prepare 统一验证。

### 短程跨文件 Contract 微型仓库（候选）

新增三个 Java 17 微型仓库，分别考核多租户消息幂等、可靠 Outbox 投递、租约 epoch fencing。难点来自 `TASK.md`、`contracts/` 和多源文件之间的真实约束，而非增加代码体量。

- 模型只得到各题 `workspace/`。筛题时使用隔离 Docker（无网络、只挂载工作区、只读系统文件、无 Docker 控制面），隐藏测试和参考修复留在容器外的仓库目录。
- `python3 scripts/selfcheck-compact-contract.py` 是**零模型费用**验收：基线必须可编译、通过可见测试但隐藏不满分；参考修复必须隐藏测试满分。
- `Frontier batch candidate screen` 只在人工触发或专用 trigger 变更时执行。先用 Luna High 单轮筛题，只有有效、未超时、未封顶且在 3–5 分钟目标内有足够信号的题才考虑 Sol 后续档位校准；单轮结果从不直接算 Effort Core。
- 当前日测 `schedule` 继续停用；旧 coverage-only/retired 题不得自动加入付费筛选。

### Compact 筛选隔离修正（2026-10-08）

首次 3 题 Luna High 因 Docker 运行用户与 GitHub Runner 挂载目录 owner 不一致，工作区在容器内不可写，模型 14 轮均没有补丁，全部结果判为 **Harness invalid/budget-confounded**，不作为模型能力证据。诊断任务的无模型 shell smoke 明确返回 `Permission denied`。当前容器使用 `--user "$(id -u):$(id -g)"` 对齐 UID/GID，模型调用前必须先成功创建、检查并删除工作区测试文件。下一轮只在 smoke + 隐藏参考自检全部通过后执行 Luna High 三题筛选。

### Compact Java 漏斗结论（2026-10-08）

新题的参考提交在三题隐藏测试上均为 100。纠正 Docker 工作区权限后，Luna High 的实际修复质量为：幂等 100/45s、Outbox 100/49s、租约 fencing 80/55s，均为无超时的真实修改结果。前两题进入 Coverage（不再消耗 Sol）；只对 Lease 跑了一次 GPT-6.1 Sol Medium，取得 **100 分 / 40s / 4 次 Responses / 3 次 Shell**，所有隐藏行为检查通过。

因此 Lease 只能作为**待重复验证的单轮模型区分候选**（Luna High 80、Sol Medium 100），不能进入正式 Model Core；对同一个 Lease 题的 Sol Medium 已经封顶，不再触发 High/X High。三题均**未证明 reasoning-effort 差异**，Effort Core 仍不成熟。当前 `benchmarks/frontier-batch-screen.json` 设置 `enabled:false`，避免误点引起无效付费运行。下一批题需要从真实隐藏依赖发现与多模块决策中寻找仍能区分 Sol 档位的短任务，不再重复已封顶的简单实现题。

### 真实因果调查题筛选（2026-10-08）

复用现有 `frontier-runtime-diagnosis-capacity` 和 `frontier-runtime-diagnosis-cache-db` 两个未验证任务。新的因果证据分只承认 Harness 实际执行并返回的定向对照实验：API 扩容/回滚、消费者重复投递、缓存双键失效、连接池干预。仅“问过相关关键词”、普通观测或失败的工具调用不再得证据分。

每轮 Actions 在付费模型调用前运行 `python3 tests/runtime-probe-evidence.test.py`，验证“查询但没证据/只有相关性观察”不能获得虚假证据加分。先只运行 Luna High 两题；无效或封顶不进入 Sol 档位校准。

### 因果诊断漏斗结果（2026-10-08）

新评分器的因果证据回归通过后，仅运行两道 Luna High：`frontier-runtime-diagnosis-capacity` 得 95/100、58 秒、14 响应与 12 次 Probe，属于高分 Coverage；`frontier-runtime-diagnosis-cache-db` 得 85/100、90 秒，但耗尽 17 次模型响应与 20 次 Probe，且没有有效受控实验，因此按预算混淆淘汰。**两题都不进入 Sol 校准**。通用批量筛题目标已关闭，后续不再反复运行这组题。

### 无稳定 Effort 信号的旧候选收口

`frontier-dynamic-diagnosis-v2` 已完成 3 次/档重复，思考档位分差最大 6.7（低于 10 分晋级阈值），不再投入付费校准；`frontier-review-family` 经过等价标签和重复域修正后 Medium/High/XHigh 均接近封顶（98.3/95/98.3），转为 Coverage。这两组的旧实验不得作为 Effort Core 证据。当前 Effort Core 仍为 0/1，下一阶段只接受新的、可重复、非预算混淆的质量信号。

### 新 Effort 研究候选：跨模块 Delivery 故障恢复

仅新增一个原始 Java 微型仓库 `frontier-compact-delivery`，考察同一消息在发送前失败、发送后回执丢失、业务身份跨租户/版本/行项目不重合、并发重放和分区 checkpoint 不能倒退等相互影响的条件。实现需从 `contracts/delivery-identity.md`、`contracts/acknowledgement.md` 和三个实现模块综合推断；模型可见目录不包含隐藏 verifier 和参考补丁。先执行零费用基线/参考修复自检，再只跑 Luna High 单题。封顶直接留作 Coverage，只有非预算混淆且有区分空间的题才进入 Sol Medium 校准；这仍只是题型族的第一个实例，不能单题晋级 Effort Core。

### Multi-failure Delivery 候选结论（2026-10-08）

`frontier-compact-delivery` 的基线/参考修复分别为 20/100。Luna High 首轮真实修复获得 **100/100，84 秒，7 次 Responses、8 次 Shell**，四项隐藏失败窗口检查（发送前故障、回执丢失、业务身份、并发检查点）全部通过，无预算混淆。因此只保留为 Coverage，不运行 Sol Medium/High/X High。由此确认：仅增加跨文件数、故障窗口数量和实现约束仍不足以形成可重复 Effort 区分；下一轮优先选择动态证据、反事实决策与遇错修正，而不是继续堆普通代码修复题。
