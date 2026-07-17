"""
export.py - 导出看板为独立 HTML 文件（含 Plotly CDN + Anime.js CDN）
"""
from datetime import date

import base64


CSS_EXPORT = """
<style>
  :root {
    --mcd-red: #DB0005;
    --mcd-dark: #1A1A1A;
    --mcd-gold: #FFBC0D;
    --ink: #1A1A1A;
    --ink2: #6B6B6B;
    --line: #E0E0E0;
    --bg: #F0F0F0;
    --paper: #FFFFFF;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    font-family: 'Microsoft YaHei', 'PingFang SC', -apple-system, sans-serif;
    background: var(--bg);
    color: var(--ink);
    font-size: 13.5px;
    line-height: 1.7;
  }
  .wrap { max-width: 1160px; margin: 0 auto; padding: 26px 24px 60px; }

  /* ─── 顶部栏（layout 参照 preview_v7：徽章+标题+副标左 / logo 右）─── */
  .topbar {
    background: #1A1A1A;
    border-bottom: 3px solid var(--mcd-gold);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    padding: 14px 32px;
    min-height: 70px;
    box-shadow: 0 2px 12px rgba(0,0,0,.15);
  }
  .topbar-left, .topbar-right { display: contents; }
  .header-left { flex: 1; min-width: 0; }
  .header-right { flex-shrink: 0; }
  .header-title { font-size: 20px; font-weight: 800; color: #fff; letter-spacing: .3px; line-height: 1.2; margin: 0; }
  .header-sub { font-size: 11.5px; color: rgba(255,255,255,.65); margin-top: 2px; }
  .header-logo { width: 56px; height: 56px; display: block; }
  .date-badge {
    display: inline-block;
    background: #2e2e2e;
    color: #FFBC0D;
    border: 1px solid #444;
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 8px;
  }

  /* ─── KPI Card（导出专用） ─── */
  .kpi-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 12px;
  }
  .kpi-card {
    background: #FFFFFF;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 14px 16px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(120,90,30,.05);
  }
  .kpi-label {
    font-size: 11px;
    font-weight: 600;
    color: var(--ink2);
    margin-bottom: 6px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  .kpi-value {
    font-size: 26px;
    font-weight: 800;
    color: var(--ink);
    letter-spacing: -0.02em;
    line-height: 1;
    margin-bottom: 4px;
    font-variant-numeric: tabular-nums;
  }
  .kpi-sub { font-size: 12px; color: #888888; }

  /* ─── Section 通用 ─── */
  .sec-head {
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 14px;
  }
  .sec-num {
    background: var(--mcd-red); color: #fff;
    font-weight: 800; font-size: 15px;
    min-width: 34px; height: 34px;
    border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
  }
  .sec-head h2 {
    font-size: 19px; font-weight: 800;
    color: var(--mcd-dark);
    letter-spacing: .3px; margin: 0;
  }
  section {
    background: var(--paper);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 24px 28px;
    margin-bottom: 22px;
    box-shadow: 0 1px 3px rgba(120,90,30,.05);
  }

  /* ─── Plotly 图占位 ─── */
  .plotly-graph-div { width: 100% !important; min-height: 300px; }

  /* ─── 页脚（部门版权深色条）─── */
  .page-footer {
    background: #1A1A1A;
    color: rgba(255,255,255,.7);
    font-size: 11px;
    padding: 14px 32px;
    margin-top: 40px;
    text-align: left;
    letter-spacing: .3px;
  }
</style>
"""

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"
ANIME_CDN = "https://cdn.jsdelivr.net/npm/animejs@3.2.2/lib/anime.min.js"


def build_export_html(
    df,
    target_daily: int,
    actual_daily: int,
    completion: float,
    gap_pct: float,
    status: str,
    daily_clicks: dict,
    week_start,
    week_end,
    days_elapsed: int,
    days_remaining: int,
    hit_days: int,
    need_daily: int,
    green_th: float,
    yellow_th: float,
    fig2,
    fig3,
    fig4,
    period_str: str = "",
    day_notes: dict | None = None,
) -> str:
    """
    构建完整可导出的 HTML 字符串。
    """
    from emergency.sections.topbar import render_topbar_html, render_footer_html
    from emergency.sections.section1_overview import render_html as render_s1
    from emergency.sections.section2_dau import render_html as render_s2
    from emergency.sections.section3_aarr import render_html as render_s3
    from emergency.sections.section4_channels import render_html as render_s4

    today_str = date.today().strftime("%Y-%m-%d")
    if not period_str:
        period_str = f"{week_start} ~ {week_end}"

    import pandas as pd
    week_start_ts = pd.Timestamp(week_start) if not isinstance(week_start, pd.Timestamp) else week_start

    topbar_html = render_topbar_html(period_str)
    s1_html = render_s1(df, target_daily, daily_clicks, week_start_ts,
                          actual_daily, completion, notes=day_notes)
    s2_html = render_s2(df, target_daily, daily_clicks, gap_pct, completion,
                          actual_daily, hit_days, days_elapsed, days_remaining,
                          need_daily, status, fig2)
    s3_html = render_s3(df, target_daily, fig3)
    s4_html = render_s4(df, target_daily, fig4)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CNN Emergency - {today_str}</title>
<script src="{PLOTLY_CDN}" charset="utf-8"></script>
<script src="{ANIME_CDN}"></script>
{CSS_EXPORT}
</head>
<body>

{topbar_html}

<div class="wrap" style="padding: 26px 24px 60px;">
  {s1_html}
  {s2_html}
  {s3_html}
  {s4_html}
</div>

{render_footer_html()}

</body>
</html>"""

    return html
