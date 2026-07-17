"""
export.py - 导出看板为独立 HTML 文件
"""

import base64
import json
from pathlib import Path
from datetime import date

import plotly.graph_objects as go

from performance.components import _fmt_number


def _get_css() -> str:
    """导出用的 CSS（暖色纸质主题）"""
    return """
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
  a { color: inherit; text-decoration: none; }

  /* ─── 顶部栏（layout 参照 preview_v7：徽章+标题+副标左 / logo 右）─── */
  .topbar {
    position: sticky;
    top: 0;
    z-index: 100;
    background: #1A1A1A;
    border-bottom: 3px solid var(--mcd-gold);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    padding: 14px 32px;
    min-height: 70px;
    box-shadow: 0 2px 14px rgba(0,0,0,.18);
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

  /* ─── 导航栏 ─── */
  .nav-bar {
    position: sticky;
    top: 103px;
    z-index: 90;
    background: rgba(255,253,248,.96);
    backdrop-filter: blur(6px);
    border-bottom: 1px solid var(--line);
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    padding: 8px 20px;
  }
  .nav-link {
    font-size: 11.5px;
    font-weight: 700;
    color: var(--ink2);
    padding: 4px 11px;
    border-radius: 16px;
    text-decoration: none;
    transition: .15s;
    white-space: nowrap;
  }
  .nav-link:hover { background: #F5F5F5; color: var(--mcd-red); }

  /* ─── 内容区 ─── */
  .wrap { max-width: 1160px; margin: 0 auto; padding: 26px 24px 60px; }
  section {
    background: var(--paper);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 24px 28px;
    margin-bottom: 22px;
    box-shadow: 0 1px 3px rgba(120,90,30,.05);
  }
  .sec-head { display: flex; align-items: center; gap: 12px; margin-bottom: 6px; }
  .sec-num {
    background: var(--mcd-red);
    color: #fff;
    font-weight: 800;
    font-size: 15px;
    min-width: 34px;
    height: 34px;
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .sec-head h2 { font-size: 19px; font-weight: 800; color: var(--mcd-dark); letter-spacing: .3px; }

  /* ─── KPI 卡片 ─── */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    margin: 12px 0;
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
    letter-spacing: 0.1em;
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
  .kpi-sub { font-size: 12px; color: var(--ink2); }

  /* ─── 表格 ─── */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0 16px;
    background: #fff;
    border-radius: 9px;
    overflow: hidden;
    font-size: 12px;
    box-shadow: 0 1px 2px rgba(0,0,0,.04);
  }
  th {
    background: #1A1A1A;
    color: #fff;
    padding: 9px 11px;
    text-align: left;
    font-weight: 700;
    font-size: 11.5px;
  }
  td { padding: 8px 11px; border-bottom: 1px solid #E0E0E0; vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  tr:nth-child(even) td { background: #F5F5F5; }

  /* ─── Section 大标题 H2：红色方块徽章 + 黑标题（参照 preview_v7）─── */
  .section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 19px;
    font-weight: 800;
    color: var(--ink);
    margin: 24px 0 6px 0;
    letter-spacing: 0.3px;
  }
  .section-header h2 { font-size: inherit; font-weight: inherit; color: inherit; margin: 0; }
  .section-header .sec-num {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: 9px;
    background: var(--mcd-red);
    color: #fff;
    font-size: 15px;
    font-weight: 800;
    flex-shrink: 0;
  }

  /* ─── Section 副标题 H3：金色左竖条 + 灰字 ─── */
  .section-subheader {
    font-size: 15px;
    font-weight: 800;
    color: var(--ink2);
    border-left: 4px solid var(--mcd-gold);
    padding-left: 11px;
    margin: 22px 0 10px 0;
    letter-spacing: 0.02em;
  }

  /* ─── Plotly 图表 ─── */
  .plotly-graph-div {
    width: 100% !important;
    min-height: 300px;
  }

  /* ─── 锚点跳转偏移（补偿固定 header 高度）─── */
  [id^="sec-"] {
    scroll-margin-top: 115px;
  }

  /* ─── 分隔线 ─── */
  .divider {
    border: none;
    border-top: 1px solid var(--line);
    margin: 28px 0;
  }

  /* ─── Plan 卡片 ─── */
  .plan-card {
    background: #fff;
    border: 1px solid #E8E8E8;
    border-left: 3px solid var(--mcd-red);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
  }
  .plan-card.good { border-left-color: #5a8a50; }
  .plan-card .plan-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .plan-card .plan-tag {
    font-size: 11px;
    font-weight: 600;
  }
  .plan-card .plan-tag.good { color: #5a8a50; }
  .plan-card .plan-tag.bad { color: var(--mcd-red); }
  .plan-card .plan-score {
    font-size: 18px;
    font-weight: 800;
  }
  .plan-card .plan-name {
    font-size: 13px;
    font-weight: 600;
    margin: 6px 0 2px;
  }
  .plan-card .plan-metrics {
    font-size: 12px;
    color: #666;
  }
  .plan-card .plan-msg {
    margin-top: 8px;
    padding: 8px 10px;
    background: #FAFAFA;
    border-radius: 6px;
    border-left: 2px solid #E0E0E0;
    font-size: 12px;
    line-height: 1.5;
  }
  .plan-card .plan-msg-title {
    font-weight: 600;
    color: #1a1a1a;
    margin-bottom: 2px;
  }
  .plan-card .plan-msg-text { color: #666; }

  /* ─── Plan Tab 切换（纯 CSS，支持双层嵌套）─── */
  .plan-ch-tabs, .plan-dim-tabs { margin-bottom: 16px; }
  .plan-ch-input, .plan-dim-input { display: none; }
  .plan-tab-label {
    display: inline-block;
    font-size: 12px;
    font-weight: 600;
    color: var(--ink2);
    padding: 5px 14px;
    border-radius: 16px;
    cursor: pointer;
    transition: .15s;
    margin-right: 4px;
    margin-bottom: 4px;
  }
  .plan-tab-label:hover { background: #F5F5F5; color: var(--mcd-red); }
  .plan-ch-input:checked + .plan-tab-label,
  .plan-dim-input:checked + .plan-tab-label {
    background: var(--mcd-red);
    color: #fff;
  }
  .plan-ch-panel, .plan-dim-panel { display: none; }
  /* 渠道：第N个radio checked → 第N个panel显示 */
  .plan-ch-input:nth-of-type(1):checked ~ .plan-ch-panel:nth-of-type(1),
  .plan-ch-input:nth-of-type(2):checked ~ .plan-ch-panel:nth-of-type(2),
  .plan-ch-input:nth-of-type(3):checked ~ .plan-ch-panel:nth-of-type(3),
  .plan-ch-input:nth-of-type(4):checked ~ .plan-ch-panel:nth-of-type(4) { display: block; }
  /* 维度：同理 */
  .plan-dim-input:nth-of-type(1):checked ~ .plan-dim-panel:nth-of-type(1),
  .plan-dim-input:nth-of-type(2):checked ~ .plan-dim-panel:nth-of-type(2),
  .plan-dim-input:nth-of-type(3):checked ~ .plan-dim-panel:nth-of-type(3) { display: block; }

  /* ─── AI 折叠 ─── */
  details { margin-top: 8px; }
  details summary {
    font-size: 12px;
    font-weight: 600;
    color: var(--mcd-dark);
    cursor: pointer;
    padding: 4px 0;
  }
  details summary:hover { color: var(--mcd-red); }
  details[open] summary { margin-bottom: 4px; }

  /* ─── Plan 药丸豆腐块 ─── */
  .plan-metrics { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
  .plan-metric-tag {
    background: #F5F5F5;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 12px;
    color: #888;
    font-weight: 500;
  }

  /* ─── BU 详情浮层（:target 触发）──── */
  .bu-link { color: inherit; text-decoration: none; border-bottom: 1px dashed #1A1A1A; cursor: pointer; }
  .bu-link:hover { background: #F5F5F5; color: #DB0005 !important; }
  .bu-pop { display: none; position: fixed; inset: 0; z-index: 9999; background: rgba(0,0,0,.35); align-items: center; justify-content: center; }
  .bu-pop:target { display: flex; }
  .bu-pop-card { background: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 12px; padding: 20px 24px; max-width: 960px; width: 90vw; max-height: 80vh; overflow: auto; box-shadow: 0 8px 32px rgba(0,0,0,.25); }
  .bu-pop-card .pop-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid #E0E0E0; }
  .bu-pop-card .pop-close { text-decoration: none; color: #999; font-size: 20px; padding: 0 8px; line-height: 1; }
  .bu-pop-card .pop-close:hover { color: #DB0005; }
  /* 浮层卡片里的 Plan 子表（覆盖通用 th 的白字规则） */
  .bu-plan-table { width: 100%; font-size: 12px; border-collapse: collapse; }
  .bu-plan-table th { background: #1A1A1A; color: #fff; font-weight: 700; padding: 8px 10px; text-align: left; border-bottom: 1px solid #E0E0E0; }
  .bu-plan-table th.right { text-align: right; }
  .bu-plan-table td { padding: 6px 8px; border-bottom: 1px solid #E0E0E0; color: #1A1A1A; }
  .bu-plan-table td.right { text-align: right; }

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


def _get_logo_base64() -> str:
    """获取 logo 的 base64 编码（SVG 格式）"""
    logo_path = Path(__file__).parent.parent / "assets" / "mcdonalds.svg"
    return base64.b64encode(logo_path.read_bytes()).decode()


def _render_topbar(period_str: str) -> str:
    """渲染顶部栏 HTML（layout: 徽章+标题+副标左 / logo 右）"""
    logo_b64 = _get_logo_base64()
    return f"""
<div class="topbar">
  <div class="header-left">
    <span class="date-badge">{period_str}</span>
    <h1 class="header-title">Performance Review</h1>
    <div class="header-sub">周度数据复盘看板</div>
  </div>
  <div class="header-right">
    <img src="data:image/svg+xml;base64,{logo_b64}" class="header-logo" alt="McDonald's">
  </div>
</div>
"""


def _render_footer() -> str:
    """渲染页脚部门版权（深色条）"""
    return """
<div class="page-footer">McDonald's China &middot; IT Operating &middot; Traffic</div>
"""


def _render_nav(has_topics: bool = False) -> str:
    """渲染导航栏 HTML。has_topics=False 时省略「实验专题」链接（避免跳到不存在的锚点）。"""
    topics_link = '  <a class="nav-link" href="#sec-topics">实验专题</a>\n' if has_topics else ""
    return f"""
<div class="nav-bar">
  <a class="nav-link" href="#sec-summary">综合分析</a>
  <a class="nav-link" href="#sec-operational">运营分析</a>
  <a class="nav-link" href="#sec-bu">BU 分析</a>
  <a class="nav-link" href="#sec-plan">内容分析</a>
{topics_link}</div>
"""


def _render_kpi_card(label: str, value, sub: str = "", status: str = "", unit: str = "") -> str:
    """渲染 KPI 卡片"""
    status_cls = f" {status}" if status else ""

    # Target 为 0 时显示 "/"
    if isinstance(value, (int, float)) and value == 0 and "Target" in label:
        value_str = "/"
    elif isinstance(value, (int, float)):
        value_str = _fmt_number(value, unit=unit)
    else:
        value_str = str(value)

    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""
<div class="kpi-card{status_cls}">
  <div class="kpi-label">{label}</div>
  <div class="kpi-value">{value_str}</div>
  {sub_html}
</div>
"""


def _render_kpi_row(cards_html: list) -> str:
    """渲染 KPI 行"""
    return f'<div class="kpi-grid">{"".join(cards_html)}</div>'


def _fig_to_html(fig_json: str) -> str:
    """将 Plotly 图表 JSON 转为 HTML 片段（不含 Plotly JS，由 head 统一引入）"""
    # 从 JSON 重建图表
    fig = go.Figure(json.loads(fig_json))

    # 确保图表有明确的尺寸
    if fig.layout.height is None:
        fig.update_layout(height=300)

    # 生成 HTML（不含 plotlyjs，由 head 统一引入 CDN）
    return fig.to_html(include_plotlyjs=False, full_html=False)


def _render_section(num: int, title: str, content: str) -> str:
    """渲染一个 section"""
    return f"""
<div id="sec-{['summary', 'operational', 'bu', 'plan', 'topics'][num-1]}"></div>
<section>
  <div class="sec-head">
    <span class="sec-num">{num}</span>
    <h2>{title}</h2>
  </div>
  {content}
</section>
"""


def generate_html(target: int, figs: dict, tables: dict, kpis: dict, period_str: str = "", channel_health_html: str = "") -> str:
    """
    生成完整的 HTML 文件。

    参数:
        target: Target DAU
        figs: 各 tab 的图表字典 {"summary": [fig1, fig2], "operational": [fig1, fig2], ...}
        tables: 各 tab 的表格 HTML 字典
        kpis: 各 tab 的 KPI 数据字典
        period_str: 日期范围显示文本
        channel_health_html: 渠道健康度模块 HTML（由 page.py 预渲染传入，live 与导出共用）
    """
    if not period_str:
        period_str = date.today().strftime("%Y-%m-%d")
    today_str = date.today().strftime("%Y-%m-%d")

    # ─── Section 1: Executive Summary ───
    summary_kpis = kpis.get("summary", {})
    ach_rate = summary_kpis.get("achievement_rate", 0)
    ach_sub = f"{ach_rate:.1f}% 达成" if ach_rate > 0 else ""
    days_count = summary_kpis.get("days_count", 0)
    comp_str = summary_kpis.get("completion_str", "—")
    comp_sub = f"完成 {comp_str}（共 {days_count} 天）" if days_count > 0 else ""

    dau_label = summary_kpis.get("dau_label", "DAU Actual（日均）")
    cards = [
        _render_kpi_card("DAU Target（日均）", target, sub=comp_sub),
        _render_kpi_card(dau_label, summary_kpis.get("avg_dau", 0), sub=ach_sub, status=summary_kpis.get("status", "")),
        _render_kpi_card("触达成功（日均）", summary_kpis.get("avg_reach", 0)),
        _render_kpi_card("订单Sales（日均）", summary_kpis.get("avg_sales", 0)),
    ]

    summary_content = _render_kpi_row(cards)
    for fig in figs.get("summary", []):
        summary_content += _fig_to_html(fig)

    # ─── Section 2: Operational ───
    op_kpis = kpis.get("operational", {})
    op_cards = [
        _render_kpi_card("触达成功（日均）", op_kpis.get("avg_reach", 0)),
        _render_kpi_card("点击人次（日均）", op_kpis.get("avg_clicks", 0)),
        _render_kpi_card("AARR 占比", op_kpis.get("aarr_pct", 0), unit="%"),
        _render_kpi_card("常规 占比", op_kpis.get("normal_pct", 0), unit="%"),
    ]
    op_content = _render_kpi_row(op_cards)
    op_figs = figs.get("operational", [])
    # 第一个图：AARR + 常规 堆积
    if len(op_figs) > 0:
        op_content += _fig_to_html(op_figs[0])
    # 分渠道明细表格
    op_content += tables.get("operational", "")
    # 第二个图：分渠道堆积（vs Target）
    if len(op_figs) > 1:
        op_content += '<div class="section-subheader">分渠道堆积（vs Target）</div>'
        op_content += _fig_to_html(op_figs[1])
    # 渠道健康度（HTML 由 page.py 预渲染传入，live 与导出共用，避免重复计算）
    op_content += channel_health_html

    # ─── Section 3: BU ───
    bu_content = tables.get("bu", "")
    for fig in figs.get("bu", []):
        bu_content += _fig_to_html(fig)

    # ─── Section 4: Plan ───
    plan_content = tables.get("plan", "")

    # ─── 拼接完整 HTML ───
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Performance Review - {today_str}</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
{_get_css()}
</head>
<body>

{_render_topbar(period_str)}
{_render_nav(has_topics=bool(tables.get("topics")))}

<div class="wrap">
  {_render_section(1, "综合分析", summary_content)}
  {_render_section(2, "运营分析", op_content)}
  {_render_section(3, "BU 分析", bu_content)}
  {_render_section(4, "内容分析", plan_content)}
  {(_render_section(5, "实验专题", tables.get("topics", "")) if tables.get("topics") else "")}
</div>

{_render_footer()}

</body>
</html>"""

    return html
