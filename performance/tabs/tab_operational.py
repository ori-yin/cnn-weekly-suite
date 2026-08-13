"""
tab_operational.py - 第二层：Operational 分析
AARR / 常规 × 渠道，堆积柱状图 + 折叠展开
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from performance.config import MCD_RED, MCD_GOLD, MCD_GREEN, MCD_DARK_RED, THEME_BG, THEME_INK, THEME_PAPER, THEME_LINE, THEME_ROW_ALT, CHANNELS
from performance.components import section_header, kpi_card, kpi_row


def _compute_metrics(df: pd.DataFrame) -> dict:
    """计算一组数据的核心指标"""
    return {
        "触达成功": df["触达成功"].sum(),
        "点击人次": df["点击人次"].sum(),
        "CTR": df["点击人次"].sum() / df["触达成功"].sum() * 100 if df["触达成功"].sum() > 0 else 0,
        "订单GC": df["订单GC"].sum(),
        "下单转化率": (df["点击后下单人次"].sum() / df["点击人次"].sum() * 100) if ("点击后下单人次" in df.columns and df["点击人次"].sum() > 0) else 0,
        "Plan数": df["Plan ID"].nunique() if "Plan ID" in df.columns else len(df),
        "订单Sales": round(df["订单Sales"].sum(), 2) if "订单Sales" in df.columns else 0,
    }


def _channel_detail_table(df_sub: pd.DataFrame, plan_type_label: str, days_count: int) -> str:
    """渲染单个计划类型的渠道明细表（日均），返回 HTML"""
    rows = []
    for ch in CHANNELS:
        ch_df = df_sub[df_sub["渠道"] == ch]
        if len(ch_df) == 0:
            continue
        m = _compute_metrics(ch_df)
        rows.append({
            "渠道": ch,
            "触达成功": int(m["触达成功"] / days_count) if days_count > 0 else 0,
            "点击人次": int(m["点击人次"] / days_count) if days_count > 0 else 0,
            "CTR": m["CTR"],
            "订单GC": int(m["订单GC"] / days_count) if days_count > 0 else 0,
            "下单转化率": m["下单转化率"],
            "Plan数": m["Plan数"],
            "订单Sales": round(m["订单Sales"] / days_count, 2) if days_count > 0 else 0,
        })

    if not rows:
        st.info(f"没有 {plan_type_label} 的渠道数据")
        return ""

    TH = f"background:#1A1A1A;color:#fff;padding:10px 12px;font-weight:700;font-size:12px;"
    TD = f"padding:8px 12px;border-bottom:1px solid #e0e0e0;"
    TD_EVEN = f"padding:8px 12px;border-bottom:1px solid #e0e0e0;background:{THEME_ROW_ALT};"

    rows_html = ""
    for i, r in enumerate(rows):
        td_style = TD_EVEN if i % 2 == 1 else TD
        rows_html += (
            f"<tr>"
            f"<td style='{td_style}'>{r['渠道']}</td>"
            f"<td style='{td_style}text-align:right;'>{r['Plan数']}</td>"
            f"<td style='{td_style}text-align:right;'>{r['触达成功']:,}</td>"
            f"<td style='{td_style}text-align:right;'>{r['点击人次']:,}</td>"
            f"<td style='{td_style}text-align:right;'>{r['CTR']:.2f}%</td>"
            f"<td style='{td_style}text-align:right;'>{r['订单GC']:,}</td>"
            f"<td style='{td_style}text-align:right;'>{r['下单转化率']:.1f}%</td>"
            f"<td style='{td_style}text-align:right;'>{r['订单Sales']:,.2f}</td>"
            f"</tr>"
        )

    table_html = (
        f'<div style="font-size:13px;font-weight:600;color:{THEME_INK};margin:12px 0 8px;">{plan_type_label}</div>'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px;background:#FFFFFF;border-radius:9px;overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,.04);">'
        f'<thead><tr>'
        f'<th style="{TH}text-align:left;">渠道</th>'
        f'<th style="{TH}text-align:right;">Plan数</th>'
        f'<th style="{TH}text-align:right;">触达成功（日均）</th>'
        f'<th style="{TH}text-align:right;">点击人次（日均）</th>'
        f'<th style="{TH}text-align:right;">CTR</th>'
        f'<th style="{TH}text-align:right;">订单GC（日均）</th>'
        f'<th style="{TH}text-align:right;">下单转化率</th>'
        f'<th style="{TH}text-align:right;">订单Sales（日均）</th>'
        f'</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table>'
    )

    st.markdown(table_html, unsafe_allow_html=True)
    return table_html


def render(df: pd.DataFrame, target: int):
    """渲染 Operational 分析层"""

    st.markdown(section_header("Operational 分析", number=2, subtitle=""), unsafe_allow_html=True)

    # 筛选 Operational 数据
    df_op = df[df["计划类型"].notna()].copy()

    if len(df_op) == 0:
        st.info("当前筛选条件下没有 Operational 数据")
        return

    # ─── 汇总 KPI（日均）─────────────────────────────────
    days_count = df_op["发送日期"].dt.date.nunique()
    m_total = _compute_metrics(df_op)
    m_aarr = _compute_metrics(df_op[df_op["计划类型"] == "AARRPlan"])
    m_normal = _compute_metrics(df_op[df_op["计划类型"] == "常规Plan"])

    cards = [
        kpi_card("触达成功（日均）", int(m_total["触达成功"] / days_count) if days_count > 0 else 0),
        kpi_card("点击人次（日均）", int(m_total["点击人次"] / days_count) if days_count > 0 else 0),
        kpi_card("AARR 占比", m_aarr["点击人次"] / m_total["点击人次"] * 100 if m_total["点击人次"] > 0 else 0, unit="%"),
        kpi_card("常规 占比", m_normal["点击人次"] / m_total["点击人次"] * 100 if m_total["点击人次"] > 0 else 0, unit="%"),
    ]
    st.markdown(kpi_row(cards), unsafe_allow_html=True)

    # ─── 每日堆积柱状图（AARR + 常规 vs Target）──────────
    st.markdown('<div class="section-subheader">每日 DAU：AARR + 常规 堆积</div>', unsafe_allow_html=True)

    daily_type = df_op.groupby([df_op["发送日期"].dt.date, "计划类型"]).agg(
        DAU=("点击人次", "sum"),
    ).reset_index()
    daily_type.columns = ["日期", "计划类型", "DAU"]

    daily_aarr = daily_type[daily_type["计划类型"] == "AARRPlan"].set_index("日期")["DAU"]
    daily_normal = daily_type[daily_type["计划类型"] == "常规Plan"].set_index("日期")["DAU"]

    # 合并，确保所有日期都有
    all_dates = sorted(daily_type["日期"].unique())
    daily_aarr = daily_aarr.reindex(all_dates, fill_value=0)
    daily_normal = daily_normal.reindex(all_dates, fill_value=0)
    daily_total = daily_aarr.values + daily_normal.values

    # 百分比文本（柱子内部）
    aarr_pct = [f"{a / t * 100:.0f}%" if t > 0 else "" for a, t in zip(daily_aarr.values, daily_total)]
    normal_pct = [f"{n / t * 100:.0f}%" if t > 0 else "" for n, t in zip(daily_normal.values, daily_total)]

    fig = go.Figure()

    # AARR 柱（底部）
    fig.add_trace(go.Bar(
        x=all_dates,
        y=daily_aarr.values,
        name="AARR",
        marker_color=MCD_RED,
        opacity=0.85,
        text=aarr_pct,
        textposition="inside",
        textfont=dict(size=10, color="#fff"),
    ))

    # 常规柱（堆叠在上面）
    fig.add_trace(go.Bar(
        x=all_dates,
        y=daily_normal.values,
        name="常规",
        marker_color=MCD_GOLD,
        opacity=0.85,
        text=normal_pct,
        textposition="inside",
        textfont=dict(size=10, color="#5a1a00"),
    ))

    # 柱子顶部显示具体数值（annotations）
    for i, date in enumerate(all_dates):
        total = daily_total[i]
        if total > 0:
            fig.add_annotation(
                x=date,
                y=total,
                text=f"{total:,.0f}",
                showarrow=False,
                yshift=8,
                font=dict(size=10, color="#1A1A1A"),
            )

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
        barmode="stack",
        height=320,
        margin=dict(l=60, r=20, t=30, b=40),
        plot_bgcolor=THEME_BG,
        paper_bgcolor=THEME_BG,
        xaxis=dict(title="", gridcolor="#E8E8E8", tickformat="%m/%d\n%a"),
        yaxis=dict(title="DAU（点击人次）", gridcolor="#E8E8E8", tickformat=","),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        font=dict(family="'Microsoft YaHei', 'PingFang SC', -apple-system, sans-serif"),
    )

    st.plotly_chart(fig, use_container_width=True)

    # ─── 分渠道堆积柱状图（vs Target，含渠道占比）──────────
    st.markdown('<div class="section-subheader">分渠道堆积（vs Target）</div>', unsafe_allow_html=True)

    daily_ch = df_op.groupby([df_op["发送日期"].dt.date, "渠道"]).agg(
        DAU=("点击人次", "sum"),
    ).reset_index()
    daily_ch.columns = ["日期", "渠道", "DAU"]

    ch_colors = {
        "APP Push": MCD_RED,
        "企微1v1": MCD_GOLD,
        "短信": MCD_GREEN,
        "微信小程序订阅消息": "#5B5BD6",
    }
    # 浅色柱子用深色字，深色柱子用白色字
    ch_text_color = {
        "APP Push": "#fff",
        "企微1v1": "#5a1a00",
        "短信": "#fff",
        "微信小程序订阅消息": "#fff",
    }

    # 计算每天总 DAU，用于算百分比
    daily_total = daily_ch.groupby("日期")["DAU"].sum().to_dict()

    fig_ch_stack = go.Figure()
    for ch in CHANNELS:
        subset = daily_ch[daily_ch["渠道"] == ch].copy()
        if len(subset) > 0:
            subset["pct"] = subset.apply(
                lambda r: f"{r['DAU'] / daily_total[r['日期']] * 100:.0f}%" if daily_total.get(r["日期"], 0) > 0 else "",
                axis=1,
            )
            fig_ch_stack.add_trace(go.Bar(
                x=subset["日期"],
                y=subset["DAU"],
                name=ch,
                marker_color=ch_colors.get(ch, "#999"),
                opacity=0.85,
                text=subset["pct"],
                textposition="inside",
                textfont=dict(size=10, color=ch_text_color.get(ch, "#fff")),
            ))

    # 柱子顶部显示具体数值（annotations）
    for date in daily_total:
        total = daily_total[date]
        if total > 0:
            fig_ch_stack.add_annotation(
                x=date,
                y=total,
                text=f"{total:,.0f}",
                showarrow=False,
                yshift=8,
                font=dict(size=10, color="#1A1A1A"),
            )

    if target > 0:
        fig_ch_stack.add_hline(
            y=target, line_dash="dash", line_color="#1a1a1a", line_width=2,
            annotation_text=f"Target: {target:,.0f}",
            annotation_position="top right",
            annotation_font=dict(size=12, color="#1a1a1a"),
        )

    fig_ch_stack.update_layout(
        barmode="stack",
        height=320,
        margin=dict(l=60, r=20, t=30, b=40),
        plot_bgcolor=THEME_BG,
        paper_bgcolor=THEME_BG,
        xaxis=dict(title="", gridcolor="#E8E8E8", tickformat="%m/%d\n%a"),
        yaxis=dict(title="DAU（点击人次）", gridcolor="#E8E8E8", tickformat=","),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        font=dict(family="'Microsoft YaHei', 'PingFang SC', -apple-system, sans-serif"),
    )
    st.plotly_chart(fig_ch_stack, use_container_width=True)

    # ─── 分渠道明细 ──────────────────────────────────────
    st.markdown('<div class="section-subheader">分渠道明细</div>', unsafe_allow_html=True)

    df_aarr = df_op[df_op["计划类型"] == "AARRPlan"]
    df_normal = df_op[df_op["计划类型"] == "常规Plan"]

    detail_html = ""
    if len(df_aarr) > 0:
        detail_html += _channel_detail_table(df_aarr, "AARR", days_count)

    if len(df_normal) > 0:
        detail_html += _channel_detail_table(df_normal, "常规", days_count)

    # ─── 返回数据供导出（用 JSON 序列化避免 deepcopy 问题）─────
    fig_json = fig.to_json()
    fig_ch_stack_json = fig_ch_stack.to_json()

    kpis = {
        "avg_reach": int(m_total["触达成功"] / days_count) if days_count > 0 else 0,
        "avg_clicks": int(m_total["点击人次"] / days_count) if days_count > 0 else 0,
        "aarr_pct": round(m_aarr["点击人次"] / m_total["点击人次"] * 100, 1) if m_total["点击人次"] > 0 else 0,
        "normal_pct": round(m_normal["点击人次"] / m_total["点击人次"] * 100, 1) if m_total["点击人次"] > 0 else 0,
    }
    figs = [fig_json, fig_ch_stack_json]
    return figs, kpis, detail_html
