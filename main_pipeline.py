import json
import html
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SUMMARY_PATH = BASE_DIR / "summary.json"
REPORT_MD_PATH = BASE_DIR / "weekly_report.md"
REPORT_HTML_PATH = BASE_DIR / "weekly_report.html"
CHARTS_DIR = BASE_DIR / "charts"


def load_summary():
    if not SUMMARY_PATH.exists():
        raise FileNotFoundError("summary.json not found. Run 04_weekly_kpi_analysis.ipynb first.")
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_narrative():
    if REPORT_MD_PATH.exists():
        text = REPORT_MD_PATH.read_text(encoding="utf-8").strip()
        if text:
            return text
    return "AI summary not found. Please run 05_llm_narrative_generation.ipynb."


def format_inr(value):
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"


def format_pct(value):
    try:
        value = float(value)
        sign = "+" if value > 0 else ""
        return f"{sign}{value:.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def format_int(value):
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"


def delta_class(value):
    try:
        return "positive" if float(value) >= 0 else "negative"
    except (TypeError, ValueError):
        return "neutral"


def build_kpi_cards(summary):
    total_revenue = summary.get("total_revenue", 0)
    revenue_pct_change = summary.get("revenue_pct_change", 0)

    total_orders = summary.get("total_orders", 0)
    orders_pct_change = summary.get("orders_pct_change", 0)

    aov = summary.get("aov", 0)
    aov_pct_change = summary.get("aov_pct_change", 0)

    new_customers = summary.get("new_customers", 0)
    returning_customers = summary.get("returning_customers", 0)

    return f"""
    <div class="kpi-grid">
        <div class="kpi-card revenue-card">
            <div class="kpi-label">Net Revenue</div>
            <div class="kpi-value">{format_inr(total_revenue)}</div>
            <div class="kpi-delta {delta_class(revenue_pct_change)}">{format_pct(revenue_pct_change)} vs previous week</div>
        </div>

        <div class="kpi-card orders-card">
            <div class="kpi-label">Orders</div>
            <div class="kpi-value">{format_int(total_orders)}</div>
            <div class="kpi-delta {delta_class(orders_pct_change)}">{format_pct(orders_pct_change)} vs previous week</div>
        </div>

        <div class="kpi-card aov-card">
            <div class="kpi-label">Average Order Value</div>
            <div class="kpi-value">{format_inr(aov)}</div>
            <div class="kpi-delta {delta_class(aov_pct_change)}">{format_pct(aov_pct_change)} vs previous week</div>
        </div>

        <div class="kpi-card customer-card">
            <div class="kpi-label">New Customers</div>
            <div class="kpi-value">{format_int(new_customers)}</div>
            <div class="kpi-delta neutral">Current week</div>
        </div>

        <div class="kpi-card customer-card">
            <div class="kpi-label">Returning Customers</div>
            <div class="kpi-value">{format_int(returning_customers)}</div>
            <div class="kpi-delta neutral">Current week</div>
        </div>
    </div>
    """


def build_chart_card(title, subtitle, image_name):
    return f"""
    <div class="chart-card">
        <div class="chart-text">
            <h3>{html.escape(title)}</h3>
            <p>{html.escape(subtitle)}</p>
        </div>
        <img src="charts/{html.escape(image_name)}" alt="{html.escape(title)}" class="chart-image">
    </div>
    """


def build_charts_section():
    charts = [
        ("Revenue Week over Week", "Compares current-week revenue with the previous week.", "revenue_wow.png"),
        ("Daily Revenue Trend", "Shows day-level revenue movement within the reporting week.", "daily_revenue.png"),
        ("Revenue Share by Channel", "Highlights which channels contributed the most revenue.", "channel_share.png"),
        ("Orders Week over Week", "Compares order volume against the previous week.", "orders_wow.png"),
        ("Top Products by Revenue", "Shows the products driving the strongest weekly sales.", "top_products.png"),
    ]

    cards = []
    for title, subtitle, image_name in charts:
        image_path = CHARTS_DIR / image_name
        if image_path.exists():
            cards.append(build_chart_card(title, subtitle, image_name))

    if not cards:
        return """
        <div class="empty-state">
            Chart images were not found. Please run charts.py before generating the dashboard.
        </div>
        """

    return '<div class="chart-grid">' + "".join(cards) + "</div>"


def build_product_tags():
    tags = ["Lipstick", "Foundation", "Concealer", "Blush", "Gloss", "Compact"]
    return "".join([f'<span class="tag">{html.escape(tag)}</span>' for tag in tags])


def parse_narrative_sections(narrative):
    target_headings = [
        "AI Summary",
        "Executive Summary",
        "Key Metrics",
        "Top-Performing Products",
        "Notable Anomalies",
        "Actionable Recommendations",
        "Charts",
    ]

    lines = [line.strip() for line in narrative.splitlines() if line.strip()]
    sections = {}
    current_heading = None
    buffer = []

    for line in lines:
        normalized = line.replace("**", "").strip().rstrip(":")
        if normalized in target_headings:
            if current_heading:
                sections[current_heading] = "\n".join(buffer).strip()
            current_heading = normalized
            buffer = []
        else:
            buffer.append(line.replace("**", "").strip())

    if current_heading:
        sections[current_heading] = "\n".join(buffer).strip()

    if not sections:
        sections["AI Summary"] = narrative.strip()

    return sections


def build_narrative_cards(narrative):
    sections = parse_narrative_sections(narrative)

    ordered_sections = [
        "AI Summary",
        "Executive Summary",
        "Key Metrics",
        "Top-Performing Products",
        "Notable Anomalies",
        "Actionable Recommendations",
        "Charts",
    ]

    cards = []
    for section_name in ordered_sections:
        content = sections.get(section_name, "").strip()
        if content:
            safe_content = html.escape(content)
            safe_content = safe_content.replace("\n", "<br><br>")
            cards.append(
                f"""
                <div class="insight-card">
                    <div class="insight-title">{html.escape(section_name)}</div>
                    <div class="insight-body">{safe_content}</div>
                </div>
                """
            )

    if not cards:
        return """
        <div class="empty-state">
            AI narrative content was not found. Please run 05_llm_narrative_generation.ipynb before generating the dashboard.
        </div>
        """

    return '<div class="insight-grid">' + "".join(cards) + "</div>"


def build_html(summary, narrative, kpi_cards_html, charts_html, narrative_cards_html):
    tags_html = build_product_tags()

    week_start = html.escape(str(summary.get("week_start", "N/A")))
    week_end = html.escape(str(summary.get("week_end", "N/A")))
    previous_week_start = html.escape(str(summary.get("previous_week_start", "N/A")))
    previous_week_end = html.escape(str(summary.get("previous_week_end", "N/A")))

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Beauty Commerce Performance Brief</title>
    <style>
        :root {{
            --bg: #fff5f8;
            --panel: #ffffff;
            --border: #efcfdf;
            --text: #3c2634;
            --muted: #6f5a67;
            --shadow: 0 14px 40px rgba(98, 54, 79, 0.12);
            --strong-shadow: 0 18px 50px rgba(91, 43, 77, 0.16);
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            font-family: "Segoe UI", Arial, sans-serif;
            background:
                radial-gradient(circle at top right, rgba(255, 182, 212, 0.55) 0%, transparent 28%),
                radial-gradient(circle at top left, rgba(217, 199, 242, 0.55) 0%, transparent 26%),
                linear-gradient(180deg, #fff7fb 0%, #fff2f6 100%);
            color: var(--text);
        }}

        .container {{
            max-width: 1280px;
            margin: 0 auto;
            padding: 28px;
        }}

        .hero, .section {{
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 28px;
            padding: 26px;
            box-shadow: var(--shadow);
            margin-bottom: 24px;
        }}

        .hero {{
            background:
                linear-gradient(135deg, rgba(255,255,255,0.88), rgba(255,255,255,0.78)),
                linear-gradient(135deg, #ffd7e8 0%, #f3d7ff 48%, #ffd9c9 100%);
            padding: 38px;
            box-shadow: var(--strong-shadow);
        }}

        .eyebrow {{
            display: inline-block;
            font-size: 12px;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: #8E244D;
            margin-bottom: 14px;
            font-weight: 800;
        }}

        h1 {{
            margin: 0 0 12px 0;
            font-size: 46px;
            line-height: 1.05;
            color: #AA336A;
            font-weight: 900;
            letter-spacing: -0.03em;
        }}

        .hero-subtitle {{
            font-size: 18px;
            color: #674d5e;
            margin: 0 0 20px 0;
            max-width: 780px;
            line-height: 1.7;
            font-weight: 500;
        }}

        .period {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 18px;
        }}

        .period-pill {{
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid #ebcade;
            padding: 11px 15px;
            border-radius: 999px;
            font-size: 14px;
            color: #5e4353;
            font-weight: 700;
            box-shadow: 0 6px 18px rgba(129, 85, 109, 0.08);
        }}

        .tag-row {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}

        .tag {{
            background: linear-gradient(180deg, #ffffff 0%, #fff6fa 100%);
            border: 1px solid #ebd1df;
            color: #794f66;
            padding: 8px 12px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 700;
        }}

        .section-title {{
            margin: 0 0 10px 0;
            font-size: 30px;
            color: #8E244D;
            font-weight: 900;
            letter-spacing: -0.02em;
        }}

        .section-subtitle {{
            margin: 0 0 22px 0;
            color: var(--muted);
            line-height: 1.7;
            font-size: 15px;
            font-weight: 500;
            max-width: 900px;
        }}

        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 18px;
        }}

        .kpi-card {{
            border-radius: 22px;
            padding: 20px;
            border: 1px solid #edd2df;
            box-shadow: 0 10px 26px rgba(105, 66, 88, 0.08);
        }}

        .revenue-card {{
            background: linear-gradient(135deg, #fff0f6 0%, #ffdfe9 100%);
        }}

        .orders-card {{
            background: linear-gradient(135deg, #fff5ef 0%, #ffe2d4 100%);
        }}

        .aov-card {{
            background: linear-gradient(135deg, #f8f2ff 0%, #e9ddff 100%);
        }}

        .customer-card {{
            background: linear-gradient(135deg, #fffafc 0%, #ffeef5 100%);
        }}

        .kpi-label {{
            font-size: 12px;
            color: #7f6172;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 10px;
            font-weight: 800;
        }}

        .kpi-value {{
            font-size: 34px;
            font-weight: 900;
            color: #351f2d;
            margin-bottom: 12px;
            line-height: 1.1;
        }}

        .kpi-delta {{
            font-size: 14px;
            font-weight: 800;
        }}

        .positive {{ color: #2f8b5f; }}
        .negative {{ color: #c04b72; }}
        .neutral {{ color: #7b6170; }}

        .insight-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 18px;
        }}

        .insight-card {{
            background: linear-gradient(180deg, #ffffff 0%, #fff7fb 100%);
            border: 1px solid #edd2df;
            border-radius: 22px;
            padding: 22px;
            box-shadow: 0 10px 28px rgba(97, 64, 83, 0.08);
        }}

        .insight-title {{
            font-size: 18px;
            font-weight: 900;
            color: #4a2538;
            margin-bottom: 12px;
            letter-spacing: -0.01em;
        }}

        .insight-body {{
            color: #5f4a58;
            line-height: 1.8;
            font-size: 15px;
            font-weight: 500;
        }}

        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(460px, 1fr));
            gap: 18px;
        }}

        .chart-card {{
            background: linear-gradient(180deg, #ffffff 0%, #fff9fc 100%);
            border: 1px solid #ecd4e1;
            border-radius: 24px;
            padding: 18px;
            box-shadow: 0 10px 28px rgba(96, 64, 81, 0.08);
        }}

        .chart-text h3 {{
            margin: 0 0 8px 0;
            font-size: 22px;
            color: #412537;
            font-weight: 900;
            letter-spacing: -0.01em;
        }}

        .chart-text p {{
            margin: 0 0 16px 0;
            color: #735d6a;
            font-size: 14px;
            line-height: 1.7;
            font-weight: 500;
        }}

        .chart-image {{
            width: 100%;
            height: auto;
            display: block;
            border-radius: 18px;
            background: #ffffff;
            border: 1px solid #f1dde7;
        }}

        .empty-state {{
            background: linear-gradient(180deg, #ffffff 0%, #fff7fa 100%);
            border: 1px dashed #e5c7d8;
            border-radius: 22px;
            padding: 24px;
            color: #725a67;
            font-size: 15px;
            line-height: 1.7;
            font-weight: 500;
        }}

        .footer {{
            text-align: center;
            color: #866876;
            font-size: 13px;
            padding: 10px 0 24px 0;
            font-weight: 700;
        }}

        @media (max-width: 900px) {{
            .chart-grid {{
                grid-template-columns: 1fr;
            }}

            .insight-grid {{
                grid-template-columns: 1fr;
            }}

            h1 {{
                font-size: 34px;
            }}

            .container {{
                padding: 18px;
            }}

            .hero {{
                padding: 28px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">

        <section class="hero">
            <div class="eyebrow">Weekly beauty business dashboard</div>
            <h1>Beauty Commerce Performance Brief</h1>
            <p class="hero-subtitle">
                A bold weekly business dashboard covering revenue performance, orders, customer mix, product momentum, and chart-led commercial insights for the reporting period.
            </p>

            <div class="period">
                <div class="period-pill"><strong>Current Week:</strong> {week_start} to {week_end}</div>
                <div class="period-pill"><strong>Previous Week:</strong> {previous_week_start} to {previous_week_end}</div>
            </div>

            <div class="tag-row">
                {tags_html}
            </div>
        </section>

        <section class="section">
            <h2 class="section-title">Executive Metrics</h2>
            <p class="section-subtitle">
                Core weekly KPI signals for topline performance, order movement, average order value, and customer contribution.
            </p>
            {kpi_cards_html}
        </section>

        <section class="section">
            <h2 class="section-title">AI Summary</h2>
            <p class="section-subtitle">
                Structured AI-generated weekly commentary presented in business-ready sections for faster review and stakeholder communication.
            </p>
            {narrative_cards_html}
        </section>

        <section class="section">
            <h2 class="section-title">Performance Visuals</h2>
            <p class="section-subtitle">
                Revenue, channel, order, and product visuals designed for quick week-over-week interpretation.
            </p>
            {charts_html}
        </section>

        <div class="footer">
            Beauty Commerce Performance Brief • Generated from weekly KPI analysis, Python visualizations, and AI narrative output.
        </div>

    </div>
</body>
</html>
"""


def main():
    summary = load_summary()
    narrative = load_narrative()
    kpi_cards_html = build_kpi_cards(summary)
    charts_html = build_charts_section()
    narrative_cards_html = build_narrative_cards(narrative)

    final_html = build_html(summary, narrative, kpi_cards_html, charts_html, narrative_cards_html)
    REPORT_HTML_PATH.write_text(final_html, encoding="utf-8")

    print(f"weekly_report.html created successfully at: {REPORT_HTML_PATH}")


if __name__ == "__main__":
    main()