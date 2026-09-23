import json
import os
import smtplib
import ssl
from datetime import datetime, timezone
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

if summary_path.exists():
    summary_text = summary_path.read_text(encoding="utf-8")
else:
    summary_text = "No Promptfoo summary was produced."

status = "OK" if summary_path.exists() and promptfoo_outcome in ("success", "unknown") else "FAILED"

subject_bits = [f"[LLM Monitor] {status}"]
if summary_json_path.exists():
    try:
        data = json.loads(summary_json_path.read_text(encoding="utf-8"))
        providers = data.get("providers", [])
        brief = []
        for p in providers:
            name = p.get("provider", "model")
            pass_rate = float(p.get("passRate", 0)) * 100
            total_tokens = int((p.get("tokenUsage") or {}).get("total", 0) or 0)
            brief.append(f"{name} {pass_rate:.1f}%/{total_tokens:,}tok")
        if brief:
            subject_bits.append(" | ".join(brief))
    except Exception:
        pass

subject = " — ".join(subject_bits)

plain = f"""LLM Intelligence Monitor

Run status: {status}
Trigger: {event_name}
Promptfoo outcome: {promptfoo_outcome}
Promptfoo exit code: {promptfoo_exit_code}
Run: {run_url}

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

print(f"Report email sent to {recipient}")
