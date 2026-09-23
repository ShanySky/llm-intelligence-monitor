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

if summary_path.exists():
    summary_text = summary_path.read_text(encoding="utf-8")
else:
    summary_text = "本次没有生成 Promptfoo 测试摘要。"

ok = summary_path.exists() and promptfoo_outcome in ("success", "unknown")
status = "正常" if ok else "异常"

subject_parts = [f"[大模型智能监控] {status}"]
if summary_json_path.exists():
    try:
        data = json.loads(summary_json_path.read_text(encoding="utf-8"))
        brief = []
        for p in data.get("providers", []):
            name = p.get("provider", "未知模型")
            overall = p.get("overall", {})
            pass_rate = float(overall.get("passRate", 0)) * 100
            total_tokens = int((overall.get("tokenUsage") or {}).get("total", 0) or 0)
            brief.append(f"{name} {pass_rate:.1f}% / 总令牌（Token）{total_tokens:,}")
        if brief:
            subject_parts.append("；".join(brief))
    except Exception:
        pass

subject = " — ".join(subject_parts)

outcome_text = {
    "success": "成功",
    "failure": "失败",
    "cancelled": "已取消",
    "skipped": "已跳过",
    "unknown": "未知",
}.get(promptfoo_outcome, promptfoo_outcome)

plain = f"""大模型智能水平监控日报

运行状态：{status}
触发方式：{trigger_text}
Promptfoo 执行状态：{outcome_text}
Promptfoo 退出码：{promptfoo_exit_code}
GitHub 自动化运行（GitHub Actions）地址：{run_url}

{summary_text}
"""

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
