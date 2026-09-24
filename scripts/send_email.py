import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

username = os.environ["MAIL_USERNAME"]
password = os.environ["MAIL_PASSWORD"]
recipient = os.environ["MAIL_TO"]

summary_path = Path("results/summary.md")
summary_json_path = Path("results/summary.json")
trend_json_path = Path("results/trend.json")

run_url = f'{os.environ.get("GITHUB_SERVER_URL","https://github.com")}/{os.environ.get("GITHUB_REPOSITORY","")}/actions/runs/{os.environ.get("GITHUB_RUN_ID","")}'
event_name = os.environ.get("GITHUB_EVENT_NAME", "unknown")
promptfoo_outcome = os.environ.get("PROMPTFOO_OUTCOME", "unknown")
promptfoo_exit_code = os.environ.get("PROMPTFOO_EXIT_CODE", "unknown")

trigger_map = {
    "schedule": "每日定时任务",
    "workflow_dispatch": "手动触发",
    "push": "代码提交触发",
}
trigger_text = trigger_map.get(event_name, event_name)

outcome_text = {
    "success": "成功",
    "failure": "失败",
    "cancelled": "已取消",
    "skipped": "已跳过",
    "unknown": "未知",
}.get(promptfoo_outcome, promptfoo_outcome)

execution_ok = summary_path.exists() and promptfoo_outcome in ("success", "unknown")
execution_status = "正常" if execution_ok else "异常"

if summary_path.exists():
    summary_text = summary_path.read_text(encoding="utf-8")
else:
    summary_text = "本次没有生成 Promptfoo 测试摘要。"

summary_data = {}
if summary_json_path.exists():
    try:
        summary_data = json.loads(summary_json_path.read_text(encoding="utf-8"))
    except Exception:
        summary_data = {}

trend_data = {}
if trend_json_path.exists():
    try:
        trend_data = json.loads(trend_json_path.read_text(encoding="utf-8"))
    except Exception:
        trend_data = {}

quality_priority = {
    "高度疑似降质/路由异常": 4,
    "疑似降质，建议复测": 3,
    "超时率显著上升，检查模型/链路": 3,
    "推理投入显著下降，继续观察": 2,
    "数据不完整，等待复测": 1,
}
normal_signals = {"未见明显异常", "基线积累中"}

trend_models = trend_data.get("models", []) if isinstance(trend_data, dict) else []
attention_models = [
    m for m in trend_models
    if m.get("signal") not in normal_signals
]
attention_models.sort(
    key=lambda m: (-quality_priority.get(m.get("signal"), 0), str(m.get("provider", "")))
)

def fmt_pct(value):
    if value is None:
        return "—"
    return f"{float(value) * 100:.1f}%"

def fmt_delta_pct(value):
    if value is None:
        return "—"
    value = float(value)
    return f"{value:+.1f}%"

def fmt_delta_pp(value):
    if value is None:
        return "—"
    value = float(value)
    return f"{value:+.1f} 个百分点"

def fmt_num(value, digits=1):
    if value is None:
        return "—"
    return f"{float(value):.{digits}f}"

def evidence_lines(model):
    current = model.get("current", {})
    baseline = model.get("baseline", {})
    deltas = model.get("deltas", {})
    lines = [
        f"  - 判断：{model.get('signal', '未知')}",
        (
            "  - 固定锚点基础正确率："
            f"当前 {fmt_pct(current.get('anchorPassRate'))}；"
            f"历史基线 {fmt_pct(baseline.get('passRate'))}；"
            f"变化 {fmt_delta_pp(deltas.get('anchorScorePctPoints'))}"
        ),
        (
            "  - 超时率："
            f"当前 {fmt_pct(current.get('anchorTimeoutRate'))}；"
            f"历史基线 {fmt_pct(baseline.get('timeoutRate'))}；"
            f"变化 {fmt_delta_pp(deltas.get('timeoutPctPoints'))}"
        ),
        (
            "  - 平均推理令牌（Reasoning Token）："
            f"当前 {fmt_num(current.get('anchorReasoningTokens'))}；"
            f"历史基线 {fmt_num(baseline.get('reasoning'))}；"
            f"变化 {fmt_delta_pct(deltas.get('reasoningTokenPct'))}"
        ),
        (
            "  - 平均总令牌（Token）："
            f"当前 {fmt_num(current.get('anchorTotalTokens'))}；"
            f"历史基线 {fmt_num(baseline.get('total'))}；"
            f"变化 {fmt_delta_pct(deltas.get('totalTokenPct'))}"
        ),
        (
            "  - 正常回答平均响应时间："
            f"当前 {fmt_num((current.get('anchorLatencyMs') or 0) / 1000, 2)} 秒；"
            f"历史基线 {fmt_num((baseline.get('latency') or 0) / 1000, 2)} 秒；"
            f"变化 {fmt_delta_pct(deltas.get('latencyPct'))}"
        ),
    ]
    return lines

# 邮件标题：先反映执行异常，再反映模型质量异常。
if not execution_ok:
    subject = "【大模型智能监控】【执行异常】本次测试流程未正常完成"
elif attention_models:
    worst = attention_models[0]
    highest = quality_priority.get(worst.get("signal"), 0)
    if highest >= 3:
        tag = "质量异常"
    elif highest == 2:
        tag = "需关注"
    else:
        tag = "数据异常"

    names = "、".join(m.get("provider", "未知模型") for m in attention_models[:2])
    suffix = "等" if len(attention_models) > 2 else ""
    subject = f"【大模型智能监控】【{tag}】{names}{suffix}：{worst.get('signal', '需关注')}"
else:
    subject = "【大模型智能监控】【正常】今日未发现明显质量异常"

top_lines = ["大模型智能水平监控日报", ""]

if not execution_ok:
    top_lines += [
        "🚨 今日结论：本次测试执行异常",
        "",
        f"执行状态：{execution_status}",
        f"Promptfoo 执行状态：{outcome_text}",
        f"Promptfoo 退出码：{promptfoo_exit_code}",
        "本次结果可能不完整，请优先检查 GitHub 自动化运行（GitHub Actions）。",
    ]
elif attention_models:
    highest = quality_priority.get(attention_models[0].get("signal"), 0)
    if highest >= 3:
        top_lines += ["🚨 今日结论：发现模型质量异常", ""]
    elif highest == 2:
        top_lines += ["⚠️ 今日结论：发现需要持续关注的模型变化", ""]
    else:
        top_lines += ["⚠️ 今日结论：发现数据异常，本轮不宜直接判断模型降质", ""]

    top_lines.append("异常/关注模型：")
    for model in attention_models:
        top_lines.append(f"- {model.get('provider', '未知模型')}")
        top_lines.extend(evidence_lines(model))
else:
    top_lines += [
        "✅ 今日结论：未发现明显模型质量异常",
        "",
        "当前各模型未触发降质、路由异常、显著超时上升或推理投入显著下降信号。",
    ]

top_lines += [
    "",
    f"触发方式：{trigger_text}",
    f"执行状态：{execution_status}",
    f"GitHub 自动化运行（GitHub Actions）地址：{run_url}",
    "",
    "----------------------------------------",
    "",
    "以下为本次完整测试结果（模型已按综合分从高到低排序）：",
    "",
    summary_text,
]

plain = "\n".join(top_lines)

msg = EmailMessage()
msg["Subject"] = subject
msg["From"] = username
msg["To"] = recipient
msg.set_content(plain)

context = ssl.create_default_context()
with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=30) as smtp:
    smtp.login(username, password)
    smtp.send_message(msg)

print("测试报告邮件发送成功。")
