# V1.1 公开工程评测：可用测试版证据报告

**报告类型：历史实测汇总（不调用模型）**。已接入原版 SWE-bench Java/Vue/JS 案例及官方测试；不能作为稳定模型排行榜。

| 原版任务 | 模型 / 档位 | 质量分 | 模型耗时 | 输入 Token | 数据状态 | 来源运行 |
|---|---|---:|---:|---:|---|---|
| axios__axios-5316 | gpt-6-luna / high | 0 | 189s | - | 有效 | 37759079285 |
| google__gson-1014 | gpt-6-luna / high | 100 | 142s | 79829 | 有效 | 37873035557 |
| google__gson-1093 | gpt-6-luna / high | 100 | 130s | 47193 | 有效 | 37875421942 |
| google__gson-2134 | gpt-6-luna / high | 100 | 80s | 44525 | 有效 | 37873035557 |
| google__gson-2158 | gpt-6-luna / high | 0 | 95s | - | 有效 | 37758488863 |
| google__gson-2311 | gpt-6-luna / high | 100 | 128s | - | 有效 | 37759079285 |
| vuejs__core-11589 | gpt-6-luna / high | 0 | 161s | - | 有效 | 37759079285 |
| vuejs__core-11589 | gpt-6.1-sol / high | 100 | 199s | 221050 | 有效 | 37761041016 |
| vuejs__core-11739 | gpt-6-luna / high | - | 237s | 443692 | 无效 / 不计分 | 37875421942 |
| vuejs__core-11870 | gpt-6-luna / high | 100 | 105s | 78631 | 有效 | 37873035557 |
| vuejs__core-11899 | gpt-6-luna / high | 0 | 519s | - | 有效 | 37759079285 |
| vuejs__core-11899 | gpt-6.1-sol / high | 0 | 240s | 92136 | 有效 | 37761041016 |
| vuejs__core-11915 | gpt-6-luna / high | 100 | 98s | 88658 | 有效 | 37873035557 |

## 目前可以确认什么

- 公共工程历史样本：12 个有效、1 个无效；无效数据不会被记为 0 分。
- 四道容易任务（Coverage）：100 分。该分数仅表示单轮覆盖，不用于证明模型差异。
- 同题 Vue 双样本初步对照：Luna High 0，Sol High 50，分差 50；每题每模型只有一次，**未经稳定复验**。
- 思考档位 Medium/High/X High 能力区分 **待验证**，Astra 目标 **待验证**。

## 实际使用与下一步

V1 已有的手动 Core 模型评测入口保持可用。本 V1.1 报告仅汇总此前通过实际测试的公开工程题、Token、耗时及数据有效性；不自动触发任何付费运行。
后续题目扩充、档位验证和 60/80/95 目标属于持续优化，不影响测试版的使用。

### 重要限制

- Historical runs from different rounds are not a same-condition model ranking.
- Two matched Vue cases give a provisional, unrepeated difference only.
- A budget-confounded or infrastructure-invalid case has score=null, not zero.
- Prior Gson/Axios source agent tests had missing dependencies; the corrected grader result is reported with provenance.
- No Medium/X High comparison has yet been established on a stable public-task cohort.
