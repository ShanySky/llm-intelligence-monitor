# GPT-6 Sol 思考档位低成本校准

> 这是探索性筛选，不是最终定级。当前阶段优先用 Medium 与 X High 找最大跨度信号；只有候选题才补跑 High。

## 总体

| 档位 | 正确率 | 平均 Reasoning Token | 平均总 Token | 平均响应时间 |
|---|---:|---:|---:|---:|
| Medium | 4/6（67%） | 1,527.8 | 1,937.3 | 34.9s |
| X High | 5/6（83%） | 1,191.2 | 1,600.7 | 29.0s |

## 逐题

| 题目 | 能力 | 难度 | Medium | High | X High | XH-M | 分类 | 下一步 |
|---|---|---|---:|---:|---:|---:|---|---|
| H05 | reasoning | extreme | 33% | - | 67% | 33pp | effort-candidate | repeat-then-test-high |
| S01 | math | hard | 100% | - | 100% | 0pp | ceiling | drop-from-effort-calibration |

## 下一步

- 候选题：H05。
- 下一轮只对候选题做重复验证；确认稳定后才补跑 High。
- 题型和阈值稳定后，再进行四模型全量验证。
