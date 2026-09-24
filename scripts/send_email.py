import html
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

run_url = (
    f'{os.environ.get("GITHUB_SERVER_URL","https://github.com")}/'
    f'{os.environ.get("GITHUB_REPOSITORY","")}/actions/runs/'
    f'{os.environ.get("GITHUB_RUN_ID","")}'
)
event_name = os.environ.get("GITHUB_EVENT_NAME", "unknown")
test_mode = os.environ.get("TEST_MODE", "正式日测" if event_name == "schedule" else "手动测试")
promptfoo_outcome = os.environ.get("PROMPTFOO_OUTCOME", "unknown")
promptfoo_exit_code = os.environ.get("PROMPTFOO_EXIT_CODE", "unknown")

trigger_map = {
    "schedule": "每日定时任务",
    "workflow_dispatch": "手动触发",
    "push": "手动测试触发",
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

summary_text = (
    summary_path.read_text(encoding="utf-8")
    if summary_path.exists()
    else "本次没有生成 Promptfoo 测试摘要。"
)

def load_json(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

summary_data = load_json(summary_json_path)
trend_data = load_json(trend_json_path)
providers = summary_data.get("providers", []) if isinstance(summary_data, dict) else []
selection = summary_data.get("selection") or {}

quality_priority = {
    "高度疑似降质/路由异常": 4,
    "疑似降质，建议复测": 3,
    "超时率显著上升，检查模型/链路": 3,
    "推理投入显著下降，继续观察": 2,
    "数据不完整，等待复测": 1,
}
normal_signals = {"未见明显异常", "基线积累中"}

formal_daily = test_mode == "正式日测" and not trend_data.get("manualTest", False)
trend_models = trend_data.get("models", []) if formal_daily and isinstance(trend_data, dict) else []
attention_models = [
    m for m in trend_models
    if m.get("signal") not in normal_signals
]
attention_models.sort(
    key=lambda m: (-quality_priority.get(m.get("signal"), 0), str(m.get("provider", "")))
)

def pct(value):
    return "—" if value is None else f"{float(value) * 100:.1f}%"

def number(value, digits=1):
    return "—" if value is None else f"{float(value):,.{digits}f}"

def integer(value):
    try:
        return f"{int(value):,}"
    except Exception:
        return "—"

def delta_pct(value):
    return "—" if value is None else f"{float(value):+.1f}%"

def delta_pp(value):
    return "—" if value is None else f"{float(value):+.1f} 个百分点"

def seconds(value_ms):
    if value_ms is None:
        return "—"
    return f"{float(value_ms) / 1000:.2f} 秒"

def esc(value):
    return html.escape(str(value))

def evidence_text(model):
    current = model.get("current", {})
    baseline = model.get("baseline", {})
    deltas = model.get("deltas", {})
    return [
        f"判断：{model.get('signal', '未知')}",
        (
            "固定锚点基础正确率："
            f"当前 {pct(current.get('anchorPassRate'))}；"
            f"历史基线 {pct(baseline.get('passRate'))}；"
            f"变化 {delta_pp(deltas.get('anchorScorePctPoints'))}"
        ),
        (
            "超时率："
            f"当前 {pct(current.get('anchorTimeoutRate'))}；"
            f"历史基线 {pct(baseline.get('timeoutRate'))}；"
            f"变化 {delta_pp(deltas.get('timeoutPctPoints'))}"
        ),
        (
            "平均推理令牌（Reasoning Token）："
            f"当前 {number(current.get('anchorReasoningTokens'))}；"
            f"历史基线 {number(baseline.get('reasoning'))}；"
            f"变化 {delta_pct(deltas.get('reasoningTokenPct'))}"
        ),
        (
            "平均总令牌（Token）："
            f"当前 {number(current.get('anchorTotalTokens'))}；"
            f"历史基线 {number(baseline.get('total'))}；"
            f"变化 {delta_pct(deltas.get('totalTokenPct'))}"
        ),
        (
            "正常回答平均响应时间："
            f"当前 {seconds(current.get('anchorLatencyMs'))}；"
            f"历史基线 {seconds(baseline.get('latency'))}；"
            f"变化 {delta_pct(deltas.get('latencyPct'))}"
        ),
    ]

# 邮件标题：执行异常 > 正式日测质量异常 > 手动测试 > 正常日测。
if not execution_ok:
    subject = "【大模型智能监控】【执行异常】本次测试流程未正常完成"
elif not formal_daily:
    if providers:
        names = "、".join(p.get("provider", "未知模型") for p in providers[:2])
        suffix = "等" if len(providers) > 2 else ""
        subject = f"【大模型智能监控】【手动测试】{names}{suffix} 测试结果"
    else:
        subject = "【大模型智能监控】【手动测试】测试结果"
elif attention_models:
    worst = attention_models[0]
    highest = quality_priority.get(worst.get("signal"), 0)
    tag = "质量异常" if highest >= 3 else ("需关注" if highest == 2 else "数据异常")
    names = "、".join(m.get("provider", "未知模型") for m in attention_models[:2])
    suffix = "等" if len(attention_models) > 2 else ""
    subject = f"【大模型智能监控】【{tag}】{names}{suffix}：{worst.get('signal', '需关注')}"
else:
    subject = "【大模型智能监控】【正常】今日未发现明显质量异常"

# 纯文本备用正文。
plain_lines = ["大模型智能水平监控报告", ""]
if not execution_ok:
    plain_lines += [
        "🚨 本次测试执行异常",
        f"执行状态：{execution_status}",
        f"Promptfoo 执行状态：{outcome_text}",
        f"Promptfoo 退出码：{promptfoo_exit_code}",
    ]
elif not formal_daily:
    plain_lines += [
        "🧪 本次为手动测试",
        "本次结果不会写入正式历史基线，也不参与模型降质或路由异常判断。",
    ]
elif attention_models:
    plain_lines += ["🚨 今日发现模型质量异常或需关注变化", ""]
    for model in attention_models:
        plain_lines.append(f"{model.get('provider', '未知模型')}")
        plain_lines.extend(f"- {line}" for line in evidence_text(model))
else:
    plain_lines += [
        "✅ 今日未发现明显模型质量异常",
        "当前各模型未触发降质、路由异常、显著超时上升或推理投入显著下降信号。",
    ]

plain_lines += [
    "",
    f"测试类型：{test_mode}",
    f"触发方式：{trigger_text}",
    f"GitHub 自动化运行（GitHub Actions）地址：{run_url}",
    "",
    "以下为完整 Markdown 文本；同一报告也已作为 .md 附件发送。",
    "",
    summary_text,
]
plain_body = "\n".join(plain_lines)

# HTML 顶部状态区。
if not execution_ok:
    banner_title = "本次测试执行异常"
    banner_text = "本次测试流程未正常完成，结果可能不完整，请优先检查 GitHub 自动化运行日志。"
    banner_bg = "#fff1f0"
    banner_border = "#ffccc7"
elif not formal_daily:
    banner_title = "本次为手动测试"
    banner_text = "本次结果仅用于临时验证，不写入正式历史基线，也不参与降质或路由异常判断。"
    banner_bg = "#e6f4ff"
    banner_border = "#91caff"
elif attention_models:
    banner_title = "发现模型质量异常或需关注变化"
    banner_text = "异常模型与判定依据已列在下方，请优先查看。"
    banner_bg = "#fff1f0"
    banner_border = "#ffccc7"
else:
    banner_title = "今日未发现明显模型质量异常"
    banner_text = "当前各模型未触发降质、路由异常、显著超时上升或推理投入显著下降信号。"
    banner_bg = "#f6ffed"
    banner_border = "#b7eb8f"

ranking_rows = []
for idx, p in enumerate(providers, 1):
    o = p.get("overall", {})
    zh = (p.get("languages") or {}).get("zh", {})
    en = (p.get("languages") or {}).get("en", {})
    composite = o.get("compositeScore")
    composite_text = "数据不完整" if composite is None else f"{float(composite):.1f}"
    ranking_rows.append(
        "<tr>"
        f"<td>{idx}</td>"
        f"<td><strong>{esc(p.get('provider', '未知模型'))}</strong></td>"
        f"<td>{esc(composite_text)}</td>"
        f"<td>{esc(pct(o.get('passRate')))}</td>"
        f"<td>{esc(pct(zh.get('passRate')))}</td>"
        f"<td>{esc(pct(en.get('passRate')))}</td>"
        f"<td>{esc(integer((o.get('tokenUsage') or {}).get('total')))}</td>"
        f"<td>{esc(seconds(o.get('averageLatencyMs')))}</td>"
        "</tr>"
    )

if ranking_rows:
    ranking_html = f"""
      <h2>模型排名</h2>
      <table>
        <thead>
          <tr>
            <th>排名</th><th>模型</th><th>综合分</th><th>基础正确率</th>
            <th>中文</th><th>英文</th><th>总令牌（Token）</th><th>平均响应时间</th>
          </tr>
        </thead>
        <tbody>{''.join(ranking_rows)}</tbody>
      </table>
    """
else:
    ranking_html = "<p>本次没有可展示的模型汇总结果。</p>"

anomaly_html = ""
if formal_daily and attention_models:
    blocks = []
    for model in attention_models:
        items = "".join(f"<li>{esc(line)}</li>" for line in evidence_text(model))
        blocks.append(
            f"<div class='alert-model'><h3>{esc(model.get('provider','未知模型'))}</h3><ul>{items}</ul></div>"
        )
    anomaly_html = "<h2>异常与关注信号</h2>" + "".join(blocks)

category_names = {
    "reasoning": "推理",
    "math": "数学",
    "coding": "代码",
    "instruction": "指令遵循",
    "stress": "压力题",
    "extreme": "极限题",
    "ultra": "超高难题",
    "uncategorized": "未分类",
}

detail_blocks = []
for p in providers:
    category_rows = []
    for key, c in (p.get("categories") or {}).items():
        all_stats = c.get("all", {})
        category_rows.append(
            "<tr>"
            f"<td>{esc(category_names.get(key, key))}</td>"
            f"<td>{esc(pct(all_stats.get('passRate')))}</td>"
            f"<td>{esc(all_stats.get('wrong', 0))}</td>"
            f"<td>{esc(all_stats.get('timeouts', 0))}</td>"
            f"<td>{esc(all_stats.get('apiErrors', 0))}</td>"
            "</tr>"
        )
    if category_rows:
        category_table = (
            "<table><thead><tr><th>能力类别</th><th>基础正确率</th>"
            "<th>答错</th><th>超时</th><th>API 错误</th></tr></thead>"
            f"<tbody>{''.join(category_rows)}</tbody></table>"
        )
    else:
        category_table = "<p>无分类明细。</p>"

    pair = p.get("pairComparison") or {}
    disagreements = pair.get("disagreementPairs") or []
    if disagreements:
        diff_text = "、".join(
            f"{x.get('pairId')}（{'中文更好' if x.get('better') == 'zh' else '英文更好'}）"
            for x in disagreements
        )
    else:
        diff_text = "无"

    detail_blocks.append(
        f"""
        <div class="model-card">
          <h3>{esc(p.get('provider','未知模型'))}</h3>
          <p>中英文分歧题：{esc(diff_text)}</p>
          {category_table}
        </div>
        """
    )

run_date = selection.get("runDate") or ""
selection_html = ""
if selection:
    anchors = ", ".join(selection.get("anchors") or [])
    rotating = ", ".join(selection.get("rotating") or [])
    selection_html = f"""
      <h2>本轮抽题</h2>
      <p>
        中国日期：{esc(run_date)}<br>
        固定锚点：{esc(selection.get('anchorCount', 0))} 道；
        轮换题：{esc(selection.get('rotatingCount', 0))} 道；
        中英文测试：{esc(selection.get('bilingualTestsSelected', 0))} 个<br>
        固定锚点 ID：{esc(anchors)}<br>
        轮换题 ID：{esc(rotating)}
      </p>
    """

html_body = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ margin:0; padding:0; background:#f5f5f5; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Arial,sans-serif; color:#1f1f1f; }}
  .wrap {{ max-width:900px; margin:0 auto; padding:24px; }}
  .card {{ background:#ffffff; border-radius:12px; padding:24px; box-shadow:0 1px 4px rgba(0,0,0,.08); }}
  h1 {{ font-size:24px; margin:0 0 8px; }}
  h2 {{ font-size:18px; margin:28px 0 12px; border-bottom:1px solid #eee; padding-bottom:8px; }}
  h3 {{ font-size:16px; margin:14px 0 8px; }}
  p, li {{ font-size:14px; line-height:1.65; }}
  .meta {{ color:#666; font-size:13px; }}
  .banner {{ background:{banner_bg}; border:1px solid {banner_border}; border-radius:10px; padding:16px 18px; margin:20px 0; }}
  .banner strong {{ font-size:17px; }}
  table {{ width:100%; border-collapse:collapse; margin:10px 0 18px; font-size:13px; }}
  th {{ background:#fafafa; font-weight:600; }}
  th, td {{ border:1px solid #e8e8e8; padding:9px 8px; text-align:left; vertical-align:top; }}
  .alert-model {{ border-left:4px solid #ff4d4f; background:#fff7f6; padding:10px 14px; margin:12px 0; }}
  .model-card {{ margin-top:18px; }}
  .button {{ display:inline-block; background:#1677ff; color:#fff !important; text-decoration:none; padding:10px 16px; border-radius:6px; margin-top:8px; }}
  .footer {{ color:#888; font-size:12px; margin-top:28px; }}
  @media (max-width:700px) {{
    .wrap {{ padding:10px; }}
    .card {{ padding:16px; }}
    table {{ font-size:12px; }}
    th, td {{ padding:6px 5px; }}
  }}
</style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>大模型智能水平监控报告</h1>
      <div class="meta">
        测试类型：{esc(test_mode)} ｜ 触发方式：{esc(trigger_text)}
        {f" ｜ 中国日期：{esc(run_date)}" if run_date else ""}
      </div>

      <div class="banner">
        <strong>{esc(banner_title)}</strong>
        <p>{esc(banner_text)}</p>
      </div>

      {anomaly_html}
      {ranking_html}
      {selection_html}

      <h2>能力明细</h2>
      {''.join(detail_blocks) if detail_blocks else '<p>无模型明细。</p>'}

      <h2>完整报告</h2>
      <p>完整 Markdown 报告已作为附件随本邮件发送，可直接下载后使用 Markdown 编辑器打开。</p>
      <a class="button" href="{esc(run_url)}">查看 GitHub 自动化运行（GitHub Actions）</a>

      <div class="footer">
        本邮件由 llm-intelligence-monitor 自动生成。
        正式日测才会写入历史基线并执行降质/路由异常判断；手动测试不会污染正式历史。
      </div>
    </div>
  </div>
</body>
</html>
"""

msg = EmailMessage()
msg["Subject"] = subject
msg["From"] = username
msg["To"] = recipient
msg.set_content(plain_body)
msg.add_alternative(html_body, subtype="html")

# 附加 Markdown 原始报告，解决不同邮件客户端/编辑器的渲染与复制问题。
if summary_path.exists():
    report_date = run_date or "manual"
    filename = f"llm-monitor-report-{report_date}.md"
    msg.add_attachment(
        summary_path.read_bytes(),
        maintype="text",
        subtype="markdown",
        filename=filename,
    )

context = ssl.create_default_context()
with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=30) as smtp:
    smtp.login(username, password)
    smtp.send_message(msg)

print("HTML 测试报告邮件发送成功。")
