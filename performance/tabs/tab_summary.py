"""
tab_summary.py - 第一层：Executive Summary
KPI Cards + 每日 DAU 趋势图 + Nudge Type 堆积柱状图
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from performance.config import MCD_RED, MCD_GREEN, THEME_BG
from performance.components import kpi_card, kpi_row, section_header


def render(df: pd.DataFrame, target: int, dau_df: pd.DataFrame = None):
    """渲染 Executive Summary 层，返回 (figs, kpis) 供导出用。
    如果 dau_df 提供了去重 DAU 数据，则用它来显示 DAU Actual 和趋势图。
    """

    st.markdown(section_header("Executive Summary", number=1, subtitle=""), unsafe_allow_html=True)

    # ─── 计算汇总指标 ──────────────────────────────────────
    total_clicks = df["点击人次"].sum()
    total_reach = df["触达成功"].sum()
    total_gc = df["订单GC"].sum()
    total_sales = df["订单Sales"].sum() if "订单Sales" in df.columns else 0

    # 按天聚合（一次 groupby，覆盖两种情况）
    daily_all = df.groupby(df["发送日期"].dt.date).agg(
        DAU_fallback=("点击人次", "sum"),
        触达=("触达成功", "sum"),
        GC=("订单GC", "sum"),
    ).reset_index()
    daily_all.columns = ["日期", "DAU", "触达", "GC"]

    # DAU 数据：优先用第二个 sheet 的去重 DAU
    use_dau_sheet = dau_df is not None and not dau_df.empty and "DAU" in dau_df.columns
    if use_dau_sheet:
        dau_clean = dau_df[["日期", "DAU"]].copy()
        dau_clean["日期"] = dau_clean["日期"].dt.date
        daily = dau_clean.merge(daily_all[["日期", "触达", "GC"]], on="日期", how="left").fillna(0)
        daily["触达"] = daily["触达"].astype(int)
        daily["GC"] = daily["GC"].astype(int)
    else:
        daily = daily_all

    days_count = len(daily)

    # 完成天数
    if target > 0:
        completed_days = int((daily["DAU"] >= target).sum())
        completion_str = f"{completed_days}/{days_count}"
        avg_dau = daily["DAU"].mean()
        achievement_rate = avg_dau / target * 100
    else:
        completion_str = "—"
        avg_dau = daily["DAU"].mean()
        achievement_rate = 0

    # ─── KPI Cards（4 个日均指标一排）────────────────────
    status_actual = "green" if achievement_rate >= 95 else ("yellow" if achievement_rate >= 85 else "red") if target > 0 else ""
    avg_reach = round(total_reach / days_count) if days_count > 0 else 0
    avg_sales = round(total_sales / days_count) if days_count > 0 else 0

    # 达成率 → Actual 副文本；完成天数 → Target 副文本
    ach_sub = f"{achievement_rate:.1f}% 达成" if target > 0 else ""
    comp_sub = f"完成 {completion_str}（共 {days_count} 天）" if target > 0 else ""
    dau_label = "DAU Actual（日均·去重）" if use_dau_sheet else "DAU Actual（日均）"

    cards = [
        kpi_card("DAU Target（日均）", target, sub=comp_sub),
        kpi_card(dau_label, round(avg_dau), sub=ach_sub, status=status_actual),
        kpi_card("触达成功（日均）", avg_reach),
        kpi_card("订单Sales（日均）", avg_sales),
    ]

    st.markdown(kpi_row(cards), unsafe_allow_html=True)

    # ─── 每日 DAU 趋势图 ──────────────────────────────────
    dau_chart_label = "每日 DAU 趋势（去重）" if use_dau_sheet else "每日 DAU 趋势"
    st.markdown(f'<div class="section-subheader">{dau_chart_label}</div>', unsafe_allow_html=True)

    fig = go.Figure()

    # DAU 折线
    fig.add_trace(go.Scatter(
        x=daily["日期"],
        y=daily["DAU"],
        mode="lines+markers",
        name="DAU（点击人次）",
        line=dict(color=MCD_RED, width=2.5),
        marker=dict(size=6, color=MCD_RED),
        fill="tozeroy",
        fillcolor="rgba(218,41,28,0.05)",
    ))

    # Target 水平线（黑色）
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

        # 点颜色：绿=完成，红=未完成
        point_colors = [MCD_GREEN if v >= target else MCD_RED for v in daily["DAU"]]
        fig.data[0].marker.color = point_colors
        fig.data[0].marker.size = 8

    fig.update_layout(
        height=320,
        margin=dict(l=60, r=20, t=30, b=40),
        plot_bgcolor=THEME_BG,
        paper_bgcolor=THEME_BG,
        xaxis=dict(title="", gridcolor="#E8E8E8", tickformat="%m/%d\n%a"),
        yaxis=dict(title="DAU", gridcolor="#E8E8E8", tickformat=","),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        font=dict(family="'Microsoft YaHei', 'PingFang SC', -apple-system, sans-serif"),
    )

    st.plotly_chart(fig, use_container_width=True)

    # ─── 返回数据供导出 ──────────────────────────────────────
    fig_json = fig.to_json()

    kpis = {
        "avg_dau": round(avg_dau),
        "avg_reach": avg_reach,
        "avg_sales": avg_sales,
        "achievement_rate": round(achievement_rate, 1),
        "completion_str": completion_str,
        "days_count": days_count,
        "total_reach": total_reach,
        "total_sales": total_sales,
        "status": status_actual,
        "dau_label": dau_label,
    }
    figs = [fig_json]
    return figs, kpis
