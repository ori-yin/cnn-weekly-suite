"""
sections/section2_dau.py - Section 2：DAU 概览
- 4 个 KPI Cards（Target / Actual / 触达 / Sales 日均）
- 告警条（黄/绿/红）
- 每日 DAU 趋势图（Plotly 柱状图 + Target 虚线）
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from emergency.config import (
    MCD_RED, MCD_GREEN, MCD_GOLD,
    PLOT_LAYOUT, THEME_BG,
)
from emergency.components.kpi_card import kpi_card, kpi_row


def render(
    df: pd.DataFrame,
    target_daily: int,
    daily_clicks: dict,
    gap_pct: float,
    completion: float,
    actual_daily: int,
    hit_days: int,
    days_elapsed: int,
    days_remaining: int,
    need_daily: int,
    status: str,
    week_start: pd.Timestamp = None,
) -> go.Figure:
    """
    渲染 Section 2。
    返回 go.Figure 用于导出。
    """
    st.html(f"""
<div style="font-size:20px;font-weight:800;color:#1A1A1A;
  padding:8px 0 8px 0;border-bottom:2px solid #DB0005;margin:8px 0 16px 0;letter-spacing:.3px;">
  目标拆解
</div>
""")

    # ─── 4 个 KPI Cards ───
    total_clicks = int(df["点击人次"].sum())
    total_reach = int(df["触达成功"].sum()) if "触达成功" in df.columns else 0
    total_sales = float(df["订单Sales"].sum()) if "订单Sales" in df.columns else 0

    avg_reach = round(total_reach / days_elapsed) if days_elapsed > 0 else 0
    avg_sales = round(total_sales / days_elapsed) if days_elapsed > 0 else 0

    # 完成率（用于 KPI 副文本 + Actual 卡色条）
    kpi_status_actual = ""
    if target_daily > 0 and days_elapsed > 0:
        if completion >= 0.95:
            kpi_status_actual = "green"
        elif completion >= 0.85:
            kpi_status_actual = "yellow"
        else:
            kpi_status_actual = "red"

    # 副文本：完成天数 + 达成率
    target_sub = f"已达标 <b style='color:#00A04A'>{hit_days}/{days_elapsed}</b> 天" if days_elapsed > 0 else ""
    ach_sub = f"完成率 <b>{completion*100:.1f}%</b>" if target_daily > 0 else ""

    cards = [
        kpi_card("DAU Target（日均）", int(target_daily), sub=target_sub),
        kpi_card("DAU Actual（日均）", int(actual_daily), sub=ach_sub, status=kpi_status_actual),
        kpi_card("触达成功（日均）", int(avg_reach)),
        kpi_card("订单Sales（日均）", int(avg_sales) if avg_sales > 0 else 0),
    ]
    st.html(kpi_row(cards))

    # ─── 每日 DAU 趋势图（无副标题） ───
    fig = _build_daily_figure(daily_clicks, target_daily, week_start=week_start)
    st.plotly_chart(fig, use_container_width=True)

    return fig


def _build_daily_figure(daily_clicks: dict, target: int, week_start: pd.Timestamp = None, days_total: int = 7) -> go.Figure:
    """构建每日 DAU 柱状图，固定 7 天 X 轴，没数据的天 = 0（占位空柱）"""
    if week_start is None:
        # fallback：从 daily_clicks 推断起始日
        if daily_clicks:
            week_start = pd.Timestamp(min(daily_clicks.keys()))
        else:
            week_start = pd.Timestamp.today().normalize()

    # 构造完整的 7 天日期序列
    all_dates = [(week_start + pd.Timedelta(days=i)).date() for i in range(days_total)]
    x = all_dates
    y = [int(daily_clicks.get(d, 0) or 0) for d in all_dates]

    today = pd.Timestamp.today().normalize().date()

    fig = go.Figure()

    # 柱子颜色：达标=绿，未达标=红，未来/无数据=透明占位
    bar_colors = []
    for d, v in zip(x, y):
        if v == 0 or d > today:
            bar_colors.append("rgba(0,0,0,0)")
        elif target > 0 and v >= target:
            bar_colors.append(MCD_GREEN)
        else:
            bar_colors.append(MCD_RED)

    fig.add_trace(go.Bar(
        x=[d.strftime("%m/%d\n%a") if hasattr(d, "strftime") else str(d) for d in x],
        y=y,
        name="DAU",
        marker_color=bar_colors,
        marker_line=dict(color="#1A1A1A", width=1),
        text=[f"{v:,.0f}" if v > 0 else "" for v in y],
        textposition="outside",
        textfont=dict(size=11, color="#1A1A1A"),
    ))

    # Target 水平线
    if target > 0:
        fig.add_hline(
            y=target,
            line_dash="dash",
            line_color="#1a1a1a",
            line_width=2,
            annotation_text=f"Target: {target:,.0f}",
            annotation_position="top right",
            annotation_font=dict(size=12, color="#1a1a1a"),
        )

    fig.update_layout(
        height=320,
        margin=dict(l=60, r=20, t=30, b=40),
        plot_bgcolor=THEME_BG,
        paper_bgcolor=THEME_BG,
        xaxis=dict(title="", gridcolor="#E8E8E8"),
        yaxis=dict(title="DAU（点击人次）", gridcolor="#E8E8E8", tickformat=","),
        showlegend=False,
        font=dict(family="Microsoft YaHei, PingFang SC, -apple-system, sans-serif"),
        bargap=0.3,
    )
    return fig


def render_html(
    df: pd.DataFrame,
    target_daily: int,
    daily_clicks: dict,
    gap_pct: float,
    completion: float,
    actual_daily: int,
    hit_days: int,
    days_elapsed: int,
    days_remaining: int,
    need_daily: int,
    status: str,
    fig: go.Figure,
) -> str:
    """导出用：返回 HTML 片段"""
    total_reach = int(df["触达成功"].sum()) if "触达成功" in df.columns else 0
    total_sales = float(df["订单Sales"].sum()) if "订单Sales" in df.columns else 0
    avg_reach = round(total_reach / days_elapsed) if days_elapsed > 0 else 0
    avg_sales = round(total_sales / days_elapsed) if days_elapsed > 0 else 0

    kpi_status_actual = ""
    if target_daily > 0 and days_elapsed > 0:
        if completion >= 0.95:
            kpi_status_actual = "green"
        elif completion >= 0.85:
            kpi_status_actual = "yellow"
        else:
            kpi_status_actual = "red"

    target_sub = f"已达标 {hit_days}/{days_elapsed} 天" if days_elapsed > 0 else ""
    ach_sub = f"完成率 {completion*100:.1f}%" if target_daily > 0 else ""

    cards = [
        kpi_card("DAU Target（日均）", int(target_daily), sub=target_sub),
        kpi_card("DAU Actual（日均）", int(actual_daily), sub=ach_sub, status=kpi_status_actual),
        kpi_card("触达成功（日均）", int(avg_reach)),
        kpi_card("订单Sales（日均）", int(avg_sales) if avg_sales > 0 else 0),
    ]

    fig_html = fig.to_html(include_plotlyjs=False, full_html=False, default_width="100%", default_height="320px")

    return f"""
<div id="sec-dau"></div>
<section style="background:#FFFFFF;border:1px solid #E0E0E0;border-radius:14px;padding:24px 28px;margin-bottom:22px;box-shadow:0 1px 3px rgba(120,90,30,.05);">
  <h2 style="display:flex;align-items:center;gap:12px;font-size:19px;font-weight:800;color:#1A1A1A;letter-spacing:.3px;margin:0 0 14px 0;"><span style="display:flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:9px;background:#DB0005;color:#fff;font-size:15px;font-weight:800;flex-shrink:0;">2</span>目标拆解</h2>
  {kpi_row(cards)}
  <div style="font-size:13px;font-weight:600;color:#888888;margin:14px 0 8px 0;letter-spacing:.02em;">每日 DAU 趋势</div>
  {fig_html}
</section>
"""
