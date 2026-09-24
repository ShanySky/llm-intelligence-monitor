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
