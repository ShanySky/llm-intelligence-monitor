# LLM Intelligence Monitor

用于长期监控 GPT 等大模型是否出现能力下降的轻量回归测试项目。

## 日常监控策略

完整题库保留大量中英文镜像题，但每日不会全量运行。

默认日常配置：

- 固定锚点题：8 道
- 分层轮换题：8 道
- 每道原始题同时测试中文和英文版本
- 每模型每题默认只运行 1 次
- 因此默认每个模型每天执行：16 道原始题 × 2 种语言 = 32 次测试

固定锚点用于保证不同日期之间有稳定可比基准；轮换题用于扩大题库覆盖面，降低模型对固定题集适配造成的失真。

轮换抽题不是纯随机，而是同时考虑：

- 难度：标准 / 困难 / 极限 / 超高难
- 能力：推理 / 数学 / 代码 / 指令遵循

同一天使用中国日期作为确定性种子，因此当天重复运行会抽到同一批轮换题，方便复测和问题定位；第二天才会轮换。

## 题目健康度与锚点退役

正式日测会按单题累计健康度持续判断题目是否还有信息量：

- 长期接近全模型满分、模型间差异很小的题标记为 `stable-ceiling`，轮换抽样自动降权；
- 能拉开模型差异的题提高轮换权重；
- 难度处在有效中间区间的题适度提高权重；
- 高波动但缺少稳定模型差异的题降权，避免随机噪声主导日报。

固定锚点不会因为一天结果自动更换，避免破坏跨日期基线。若固定锚点在至少 3 个正式样本日后持续处于 `stable-ceiling`，健康度报告会将其标记为“下一次 anchor 版本切换的退役候选”，由题库版本升级时集中替换。


## 参数调整

日常参数集中在根目录：

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

## 定时运行

GitHub Actions 每天 **中国时间 08:30（Asia/Shanghai）** 自动运行。

每轮完成后：

1. 生成抽题清单；
2. 使用 Promptfoo 执行测试；
3. 汇总模型得分和令牌（Token）；
4. 上传完整 JSON / HTML / Markdown 报告；
5. 通过 Gmail 自动发送中文日报。

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

当前日测同时运行四个模型：

- GPT-6 Astra X High
- GPT-6 Sol X High
- GPT-6 Luna X High
- GPT-5.6 Sol X High

GitHub Actions 使用模型矩阵并行运行：四个模型分别在独立 job 中同时执行同一批题；每个模型内部最多并发 2 个请求，因此峰值约为 8 个并发模型请求。

默认日测为 8 道固定锚点 + 8 道分层轮换题。每道原始题同时运行中文、英文镜像版本，因此每个模型每天默认执行 32 个测试。

日报额外统计固定锚点上的正确率、平均响应时间、平均输出令牌、平均推理令牌（Reasoning Token）和平均总令牌，用于辅助识别“正确率下降 + 思考变少 + 响应变快”的异常模式。


## 超时与错误统计

日常报告区分：

- 普通答错：模型正常返回答案，但答案不正确；
- 超时：模型在单题超时上限内未完成；
- API 错误：接口、网关或其他请求错误。

“有效回答正确率”只统计实际返回答案的测试。超时/API 错误不会再被当作普通答错，但超时率会作为独立异常指标进入趋势监控。

H03、U03 等高成本长链计算题保留在完整题库中，但不再作为日常固定锚点或日常轮换题。


## 评分与重试策略

默认每个模型每天固定执行 32 个测试，横向比较始终使用固定题目分母：

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

In **Actions → LLM intelligence daily monitor → Run workflow**, set `models` to:

- `all` — run every configured model;
- `gpt-6-luna` — run only GPT-6 Luna X High;
- `gpt-6-sol,gpt-6-luna` — run multiple selected models.

Manual runs do not write formal history and do not participate in degradation or routing-anomaly judgments.

Email delivery uses an HTML body for normal reading, includes a plain-text fallback, and attaches the complete Markdown report.


## History branch

Formal daily monitoring history is stored on the dedicated `history` branch under `history/YYYY-MM-DD.json`.

The `main` branch contains only source code and configuration; scheduled monitoring never writes result history back to `main`.

If the complete history directory ever needs to be restored into `main`, do it explicitly instead of merging the whole history branch:

```bash
git switch main
git restore --source=history -- history/
git add history/
git commit -m "Restore monitor history from history branch"
```

This restores every retained history file, including files that are intentionally absent from `main`.


## High manual run mode

A controlled manual run can execute all configured models at reasoning effort `high` without changing the scheduled X High configuration or writing formal history.


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

- **日常快速监控**：继续使用 Promptfoo 低成本题库，适合每天运行；
- **应用型校准**：使用轻量 Agent Harness，小规模筛选候选任务；
- **最终应用验收**：`Final application benchmark validation` 工作流，对多个模型以及 GPT-6 Sol Medium / High / X High 做完整对照；
- **稳定性复测**：只重复真正有区分信号的任务，不整套重跑。

应用型任务默认不加入每天的全量定时运行，避免 Agent 工具调用和长上下文显著放大 Token 成本。需要模型版本验收、疑似降智、题库校准时再运行完整套件。

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
- **Effort Core**：只包含跨多个实例重复验证后，能够稳定体现 GPT-6 Sol Medium → X High 正向质量提升的题型族；当前成熟门槛为至少 1 个。

只有 Model Core 和 Effort Core 都达到门槛，应用评测才标记为整体 mature。单次 Final Suite 的分差只能作为诊断信号，不能自动晋级。

题目研发状态统一记录在 `benchmarks/frontier-registry.json`。已经确认封顶的任务可以继续作为 coverage，但不会重复进入昂贵的 effort / cross-model 漏斗。

### Frontier 候选漏斗

新应用题不直接进入完整多模型套件，而按成本漏斗推进：

1. Luna High 先筛；非预算受限情况下得分 ≥95 的任务默认只保留为 coverage，不再进入昂贵 effort 校准；
2. 自然落在 20–95 分区间的任务进入 Sol Medium / High / X High；
3. 单次分差必须进入重复稳定性验证，预算触顶样本先按 Harness 混淆处理；
4. 质量差异与效率差异分开统计，不能用更慢、更多 Token 的高档思考冒充能力提升；
5. 只有稳定信号才进入 Astra / Sol / Luna / 5.6 Sol 横向验收。

Frontier 任务允许使用受限黑盒 validator 作为运行时证据，也支持 staged Harness 在后续阶段动态揭示新的仓库文件和验证证据。未来阶段内容在揭示前不可被 Agent 读取，避免把长程任务退化成“一次读完全部 checklist”。

