# 智力/思考档位区分题型研究

目标不是收集“难题”，而是找到能稳定区分：
1. 不同模型能力；
2. 同一模型不同 reasoning effort；
的题目结构。

## 外部参考与吸收原则

### ARC-AGI-2
参考：
- https://arcprize.org/arc-agi/2
- https://arcprize.org/blog/arc-agi-2-technical-report

重点吸收：
- symbolic interpretation：符号意义由题内定义，而不是依赖先验知识；
- compositional reasoning：多个规则需要同时、连续应用；
- contextual rule application：同一操作在不同上下文下切换规则；
- 任务必须有客观唯一答案，避免主观评分。

不直接复制 ARC 网格题；转换成纯文本、可程序验证的新题。

### MuSR / BIG-Bench Hard
参考：
- https://huggingface.co/datasets/TAUR-Lab/MuSR
- https://github.com/google/BIG-bench

重点吸收：
- 多步状态追踪；
- 对象位置变化；
- 团队/角色分配；
- 长链条件约束；
- 算法生成实例，降低题目污染风险。

### AIME / GPQA / HLE / Codeforces
参考：
- OpenAI gpt-oss model card reasoning-level evaluations
- https://deploymentsafety.openai.com/gpt-oss/a2
- https://www.lastexam.ai/blog/hle-diamond

这些基准在不同 reasoning effort 下存在明显分差。吸收的不是现成题，
而是“需要搜索、验证、回溯或多步推导才能稳定答对”的结构。

### LiveBench
参考：
- https://livebench.ai/
- https://arxiv.org/abs/2406.19314

重点吸收：
- 自动客观评分；
- 持续更新/生成新题，降低训练污染；
- 同时覆盖 reasoning / math / coding / instruction following；
- 难度应随模型能力持续校准，而不是永久固定标签。

## 第一批探索题型族

| ID | 题型族 | 核心能力 | 主要困难来源 |
|---|---|---|---|
| X01 | 符号语义 + 组合变换 | 抽象推理 | 先从示例识别符号语义，再连续组合多个规则 |
| X02 | 上下文规则切换 | 控制流推理 | 每一步使用哪套规则取决于动态状态 |
| X03 | 条件式对象追踪 | 长链状态维护 | 多步位置变化 + 中途条件分支 |
| X04 | 多约束唯一分配 | 约束满足 | 多条局部关系联合才能得到唯一解 |
| X05 | 组合计数 | 数学搜索 | 多个约束同时作用，不能靠单一公式直接得到答案 |
| X06 | 有状态代码语义 | 代码推理 | alias、closure、mutation、finally 等语义叠加 |

## 探索策略

1. 每个题型族先只放 1 道探针题。
2. 第一轮只跑 GPT-6 Sol Medium 与 X High，英文单版本，repeat=1。
3. 两档结果相同的题型暂不扩展。
4. Medium 错 / X High 对，或出现明显成功率差异的题型进入下一轮。
5. 候选题型先 repeat=3 验证稳定性。
6. 稳定后再补 High，确认 Medium → High → X High 的梯度。
7. 一个题型族通过后，再参数化生成多个难度阶梯实例。
8. 找到多个有效题型族后，才运行 Luna / Sol / Astra / 5.6 Sol 做全模型验收。

核心原则：先验证“题型是否有信息量”，再为它花 Token。
