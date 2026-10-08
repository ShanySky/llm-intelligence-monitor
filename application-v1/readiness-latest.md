# 应用评测 V1 Core（试用版）

**状态：可用（试用版）**。这是 2 道核心应用题 × 4 模型 / High 的一次性对照，不是完整五场景终验。

| 模型 | 题目 | 得分 | 耗时 | 样本 |
|---|---|---:|---:|---|
| gpt-6-astra | frontier-review-deep | 100 | 117s | 有效 |
| gpt-6-astra | hard-incident | 100 | 43s | 有效 |
| gpt-6.1-sol | frontier-review-deep | 100 | 188s | 有效 |
| gpt-6.1-sol | hard-incident | 100 | 63s | 有效 |
| gpt-6-luna | frontier-review-deep | 90 | 80s | 有效 |
| gpt-6-luna | hard-incident | 90 | 51s | 有效 |
| gpt-5.6-sol | frontier-review-deep | 90 | 136s | 有效 |
| gpt-5.6-sol | hard-incident | 80 | 40s | 有效 |

Model Core 注册表确认：已满足；可比模型：gpt-6-astra、gpt-6.1-sol、gpt-6-luna、gpt-5.6-sol；有效样本：8/8。

> V1 最低可用门槛是 GPT-6.1 Sol 与至少一个其他模型均完成两道 Core 题；缺失配置不参与比较，四模型完整状态单独显示。单轮样本不应作为稳定排名、Effort 档位结论或降智判断。
> Effort Core 未确认、完整当前模型纪元终验尚未完成；正式 maturity 判定不因 V1 可用而改变。
