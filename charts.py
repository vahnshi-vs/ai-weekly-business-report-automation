import os
import json
import html
import mimetypes
import smtplib
from pathlib import Path
from email.message import EmailMessage
from email.utils import make_msgid
from dotenv import load_dotenv

BASE_DIR = Path.cwd()
ENV_PATH = BASE_DIR / ".env"
SUMMARY_PATH = BASE_DIR / "summary.json"
MD_REPORT_PATH = BASE_DIR / "weekly_report.md"
CHARTS_DIR = BASE_DIR / "charts"

load_dotenv(dotenv_path=ENV_PATH)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = os.getenv("GMAIL_SENDER")
SENDER_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("REPORT_RECIPIENT")


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load_summary():
    if not SUMMARY_PATH.exists():
        raise FileNotFoundError("summary.json not found. Run 04_weekly_kpi_analysis.ipynb first.")
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_narrative():
    if MD_REPORT_PATH.exists():
        return MD_REPORT_PATH.read_text(encoding="utf-8").strip()
    return "Weekly Beauty Business Report generated successfully."


def markdown_to_basic_html(markdown_text: str) -> str:
    lines = [line.strip() for line in markdown_text.splitlines() if line.strip()]
    html_parts = []
    in_list = False

    for line in lines:
        if line.startswith("### "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(
                f"<h3 style='margin:18px 0 8px; font-size:18px; color:#6b335f;'>{html.escape(line[4:])}</h3>"
            )
        elif line.startswith("## "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(
                f"<h2 style='margin:22px 0 10px; font-size:20px; color:#6b335f;'>{html.escape(line[3:])}</h2>"
            )
        elif line.startswith("# "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(
                f"<h1 style='margin:0 0 12px; font-size:24px; color:#6b335f;'>{html.escape(line[2:])}</h1>"
            )
        elif line.startswith("- ") or line.startswith("* "):
            if not in_list:
                html_parts.append("<ul style='margin:8px 0 16px 18px; padding:0; color:#4b3b4f;'>")
                in_list = True
            html_parts.append(
                f"<li style='margin:6px 0; line-height:1.6;'>{html.escape(line[2:])}</li>"
            )
        else:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(
                f"<p style='margin:0 0 14px; line-height:1.7; color:#4b3b4f;'>{html.escape(line)}</p>"
            )

    if in_list:
        html_parts.append("</ul>")

    return "\n".join(html_parts)


def build_chart_block(title, cid_name):
    return f"""
    <div style="margin:0 0 22px;">
      <div style="font-size:15px; font-weight:bold; color:#5e2d52; margin:0 0 8px;">{html.escape(title)}</div>
      <div style="background:#fffafc; border:1px solid #f1dfea; border-radius:14px; padding:12px;">
        <img src="cid:{cid_name}" alt="{html.escape(title)}" style="width:100%; max-width:680px; height:auto; display:block; border-radius:10px;">
      </div>
    </div>
    """


summary = load_summary()
narrative_md = load_narrative()
narrative_html = markdown_to_basic_html(narrative_md)

week_start = summary.get("week_start", "N/A")
week_end = summary.get("week_end", "N/A")
previous_week_start = summary.get("previous_week_start", "N/A")
previous_week_end = summary.get("previous_week_end", "N/A")

total_revenue = safe_float(summary.get("total_revenue"))
previous_total_revenue = safe_float(summary.get("previous_total_revenue"))
revenue_pct_change = safe_float(summary.get("revenue_pct_change"))

total_orders = safe_int(summary.get("total_orders"))
previous_total_orders = safe_int(summary.get("previous_total_orders"))
orders_pct_change = safe_float(summary.get("orders_pct_change"))

aov = safe_float(summary.get("aov"))
previous_aov = safe_float(summary.get("previous_aov"))
aov_pct_change = safe_float(summary.get("aov_pct_change"))

new_customers = safe_int(summary.get("new_customers"))
returning_customers = safe_int(summary.get("returning_customers"))
pct_new_customers = safe_float(summary.get("pct_new_customers"))
pct_returning_customers = safe_float(summary.get("pct_returning_customers"))
anomaly_days_count = safe_int(summary.get("anomaly_days_count"))

print("Using .env file from:", ENV_PATH)
print("GMAIL_SENDER loaded:", bool(SENDER_EMAIL))
print("REPORT_RECIPIENT loaded:", bool(RECIPIENT_EMAIL))
print("summary.json exists:", SUMMARY_PATH.exists())
print("weekly_report.md exists:", MD_REPORT_PATH.exists())
print("charts folder exists:", CHARTS_DIR.exists())

if not SENDER_EMAIL or not SENDER_PASSWORD or not RECIPIENT_EMAIL:
    raise ValueError(
        "Missing email settings. Please check your .env file for "
        "GMAIL_SENDER, GMAIL_APP_PASSWORD, and REPORT_RECIPIENT."
    )

chart_files = [
    ("Revenue Week over Week", CHARTS_DIR / "revenue_wow.png", "chart_revenue_wow"),
    ("Daily Revenue Trend", CHARTS_DIR / "daily_revenue.png", "chart_daily_revenue"),
    ("Revenue by Channel", CHARTS_DIR / "channel_share.png", "chart_channel_share"),
    ("Orders Week over Week", CHARTS_DIR / "orders_wow.png", "chart_orders_wow"),
    ("Top Products by Revenue", CHARTS_DIR / "top_products.png", "chart_top_products"),
]

available_charts = [(title, path, cid_name) for title, path, cid_name in chart_files if path.exists()]

plain_text = f"""
Weekly Beauty Business Report
Period: {week_start} to {week_end}
Previous Period: {previous_week_start} to {previous_week_end}

Revenue: ₹{total_revenue:,.2f}
Previous Revenue: ₹{previous_total_revenue:,.2f}
Revenue Change: {revenue_pct_change:.2f}%

Orders: {total_orders:,}
Previous Orders: {previous_total_orders:,}
Orders Change: {orders_pct_change:.2f}%

Average Order Value: ₹{aov:,.2f}
Previous AOV: ₹{previous_aov:,.2f}
AOV Change: {aov_pct_change:.2f}%

New Customers: {new_customers}
Returning Customers: {returning_customers}
New Customer %: {pct_new_customers:.2f}%
Returning Customer %: {pct_returning_customers:.2f}%
Anomaly Days: {anomaly_days_count}

Narrative:
{narrative_md}
""".strip()

charts_html = ""
if available_charts:
    charts_html = "".join(build_chart_block(title, cid_name) for title, _, cid_name in available_charts)
else:
    charts_html = """
    <p style="margin:0; color:#6f5a6b; line-height:1.7;">
      Chart images were not found in the charts folder at send time.
    </p>
    """

html_body = f"""
<!DOCTYPE html>
<html>
  <body style="margin:0; padding:24px; background-color:#fff7fb; font-family:Arial, Helvetica, sans-serif; color:#3d3140;">
    <div style="max-width:760px; margin:0 auto; background:#ffffff; border:1px solid #f0dbe7; border-radius:18px; overflow:hidden;">

      <div style="background:linear-gradient(135deg, #f8dce8 0%, #efe2f8 50%, #ffe6d9 100%); padding:28px 30px;">
        <div style="font-size:12px; letter-spacing:1px; text-transform:uppercase; color:#7b6278; margin-bottom:8px;">
          Weekly Makeup Business Report
        </div>
        <h1 style="margin:0; font-size:30px; color:#5e2d52;">
          Beauty Ecommerce Performance Update
        </h1>
        <p style="margin:10px 0 0; font-size:15px; color:#6d5a6f; line-height:1.6;">
          Reporting period: <strong>{html.escape(str(week_start))}</strong> to <strong>{html.escape(str(week_end))}</strong>
        </p>
        <p style="margin:6px 0 0; font-size:14px; color:#7d687a; line-height:1.6;">
          Previous period: {html.escape(str(previous_week_start))} to {html.escape(str(previous_week_end))}
        </p>
      </div>

      <div style="padding:26px 30px 10px;">
        <h2 style="margin:0 0 14px; font-size:20px; color:#6b335f;">Weekly KPIs</h2>

        <table role="presentation" style="width:100%; border-collapse:separate; border-spacing:12px;">
          <tr>
            <td style="width:50%; vertical-align:top; background:#fff4f8; border:1px solid #f3d8e5; border-radius:14px; padding:16px;">
              <div style="font-size:12px; color:#8a6f85; text-transform:uppercase; letter-spacing:0.8px;">Net Revenue</div>
              <div style="font-size:26px; font-weight:bold; color:#5e2d52; margin:8px 0 6px;">₹{total_revenue:,.2f}</div>
              <div style="font-size:13px; color:#6f5a6b;">Previous: ₹{previous_total_revenue:,.2f}</div>
              <div style="font-size:13px; color:#6f5a6b; margin-top:4px;">Change: {revenue_pct_change:.2f}%</div>
            </td>

            <td style="width:50%; vertical-align:top; background:#fff8f3; border:1px solid #f5dfd2; border-radius:14px; padding:16px;">
              <div style="font-size:12px; color:#8a6f85; text-transform:uppercase; letter-spacing:0.8px;">Orders</div>
              <div style="font-size:26px; font-weight:bold; color:#5e2d52; margin:8px 0 6px;">{total_orders:,}</div>
              <div style="font-size:13px; color:#6f5a6b;">Previous: {previous_total_orders:,}</div>
              <div style="font-size:13px; color:#6f5a6b; margin-top:4px;">Change: {orders_pct_change:.2f}%</div>
            </td>
          </tr>

          <tr>
            <td style="width:50%; vertical-align:top; background:#faf5ff; border:1px solid #eadcf8; border-radius:14px; padding:16px;">
              <div style="font-size:12px; color:#8a6f85; text-transform:uppercase; letter-spacing:0.8px;">Average Order Value</div>
              <div style="font-size:26px; font-weight:bold; color:#5e2d52; margin:8px 0 6px;">₹{aov:,.2f}</div>
              <div style="font-size:13px; color:#6f5a6b;">Previous: ₹{previous_aov:,.2f}</div>
              <div style="font-size:13px; color:#6f5a6b; margin-top:4px;">Change: {aov_pct_change:.2f}%</div>
            </td>

            <td style="width:50%; vertical-align:top; background:#fff9fc; border:1px solid #f0dfea; border-radius:14px; padding:16px;">
              <div style="font-size:12px; color:#8a6f85; text-transform:uppercase; letter-spacing:0.8px;">Customer Mix</div>
              <div style="font-size:15px; color:#5e2d52; margin:8px 0 4px;">New customers: {new_customers} ({pct_new_customers:.2f}%)</div>
              <div style="font-size:15px; color:#5e2d52; margin:0 0 4px;">Returning customers: {returning_customers} ({pct_returning_customers:.2f}%)</div>
              <div style="font-size:13px; color:#6f5a6b; margin-top:8px;">Anomaly days detected: {anomaly_days_count}</div>
            </td>
          </tr>
        </table>
      </div>

      <div style="padding:10px 30px 8px;">
        <h2 style="margin:0 0 14px; font-size:20px; color:#6b335f;">AI business narrative</h2>
        <div style="font-size:15px; color:#4b3b4f;">
          {narrative_html}
        </div>
      </div>

      <div style="padding:10px 30px 20px;">
        <h2 style="margin:0 0 14px; font-size:20px; color:#6b335f;">Charts</h2>
        {charts_html}
      </div>

      <div style="padding:16px 30px; background:#fff3f8; border-top:1px solid #f0dbe7; font-size:12px; color:#7c6878; line-height:1.6;">
        This is an automated weekly business update generated from the latest beauty ecommerce KPI pipeline.
      </div>
    </div>
  </body>
</html>
"""

msg = EmailMessage()
msg["Subject"] = f"Weekly Beauty Business Report | {week_start} to {week_end}"
msg["From"] = SENDER_EMAIL
msg["To"] = RECIPIENT_EMAIL

msg.set_content(plain_text)
msg.add_alternative(html_body, subtype="html")

for title, chart_path, cid_name in available_charts:
    mime_type, _ = mimetypes.guess_type(chart_path.name)
    if mime_type is None:
        maintype, subtype = "image", "png"
    else:
        maintype, subtype = mime_type.split("/", 1)

    with open(chart_path, "rb") as img:
        msg.get_payload()[1].add_related(
            img.read(),
            maintype=maintype,
            subtype=subtype,
            cid=f"<{cid_name}>"
        )

with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)

print("Weekly HTML email with charts sent successfully.")
print(f"Embedded charts: {len(available_charts)}")
for title, chart_path, _ in available_charts:
    print("-", chart_path.name)