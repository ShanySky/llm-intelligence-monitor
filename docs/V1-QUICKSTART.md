# V1 Core 试用版：快速开始

**定位：先可用，再逐步提高区分度。** V1 不等待 Effort Core 成熟；快速监控、两项已确认的 Model Core 题型和报告形成可用闭环。V1 与完整研究级别 maturity 是两个不同指标。

## 直接使用

1. 进入 [Actions → Final application benchmark validation](https://github.com/ShanySky/llm-intelligence-monitor/actions/workflows/application-final-validation.yml)。
2. 点 **Run workflow**，选择 `v1-core`（默认），运行两道 Core 任务 × 4 模型 High。总共最多八个任务，四个 job 并行，无定时自动运行。
3. 打开该次 Actions 的 **Summary** 先看「应用评测 V1 Core」，再看原始评分与耗时；下载 `application-v1-core-summary-<run_id>` Artifact。
4. 结果独立持久化到 [application-v1-results 分支](https://github.com/ShanySky/llm-intelligence-monitor/tree/application-v1-results) 的 `application-v1/latest.md`、`application-v1/readiness-latest.md`。完整研究套件的数据在原来的 `application-final-results`，不会被 V1 覆盖。
5. 如需日常快速推理/指令/代码语义监控，继续通过 [LLM intelligence manual monitor](https://github.com/ShanySky/llm-intelligence-monitor/actions/workflows/intelligence-smoke.yml) 按需运行；每日自动监控保持关闭。

首次 V1 运行在满足最低门槛后创建 `v0.1.0-beta.1` 预发布版本；没满足门槛则仍保存报告并指出无效样本，不冒充发布成功。重复手动运行会更新结果分支，但不会自动产生新版本号。

## V1 最低验收

- 两道已确认的 Core 题型：`frontier-review-deep`（代码审核）、`hard-incident`（Agent 故障调查）。
- `gpt-6.1-sol` High 与至少一个其他模型 High，两题均正常完成、有完整 runner 遥测、无预算耗尽和超时。
- 四模型均完成时标记 `full_matrix_complete=true`；有少量不完整时，只比较完整模型、标注缺失，不阻止 V1 的有限试用。
- 各模型分数、任务耗时、Token、失败原因可查，失败或不完整数据不得进入质量分。

## 现阶段不能据此宣称的结论

- **单轮 Core 对比不是稳定模型排名**。已有的 Model Core 题型确认来自过去的独立重复验证；本轮四模型 High 是初步横向对照。
- **Effort Core 仍为 0/1**，暂不比较 Medium / High / X High 的能力差距。不要为了发布版本而人为制造 Effort 分差。
- V1 两题仅覆盖 Review 和 Agent 的核心区分能力，方案、Coding、长程任务目前仍由现有完整应用套件承担覆盖，不是此轻量 V1 回合的必跑项目。

## 后续升级

保持 `v1-core` 可用入口稳定。先观察正常使用中的结果与成本，再按需扩充一个真正有区分度的题型族。完整五场景、六模型/档位矩阵仍可在同一 Workflow 选择 `full` 手动运行，原有 maturity 门槛不降低。
