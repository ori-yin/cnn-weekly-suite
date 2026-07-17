"""
sections/section3_aarr.py - Section 3：AARR / Normal 拆解（Plotly 堆积柱状图）
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from emergency.config import MCD_RED, MCD_GOLD, THEME_BG


def _build_aarr_figure(df: pd.DataFrame, week_start: pd.Timestamp, target: int, days_total: int = 7) -> go.Figure:
    """构建 AARR/Normal 堆积柱状图，固定 7 天 X 轴"""
    if df.empty or week_start is None:
        return go.Figure()

    df_op = df[df["计划类型"].isin(["AARRPlan", "常规Plan"])].copy()

    # 构造完整 7 天
    all_dates = [(week_start + pd.Timedelta(days=i)).date() for i in range(days_total)]

    if df_op.empty:
        aarr_vals = [0] * days_total
        normal_vals = [0] * days_total
    else:
        daily = df_op.groupby([df_op["发送日期"].dt.date, "计划类型"]).agg(
            DAU=("点击人次", "sum")
        ).reset_index()
        daily.columns = ["日期", "计划类型", "DAU"]

        aarr = daily[daily["计划类型"] == "AARRPlan"].set_index("日期")["DAU"]
        normal = daily[daily["计划类型"] == "常规Plan"].set_index("日期")["DAU"]

        aarr = aarr.reindex(all_dates, fill_value=0)
        normal = normal.reindex(all_dates, fill_value=0)

        # reindex 后索引是 Timestamp，转回 date 用于计算
        aarr_vals = [int(aarr.get(d, 0) or 0) if hasattr(aarr, 'get') else int(v) for d, v in zip(all_dates, aarr.values)] \
            if len(aarr) > 0 else [0] * days_total
        normal_vals = [int(normal.get(d, 0) or 0) if hasattr(normal, 'get') else int(v) for d, v in zip(all_dates, normal.values)] \
            if len(normal) > 0 else [0] * days_total

        if not hasattr(aarr, 'get') or len(aarr) == 0:
            aarr_vals = [0] * days_total
        if not hasattr(normal, 'get') or len(normal) == 0:
            normal_vals = [0] * days_total

    total = [a + n for a, n in zip(aarr_vals, normal_vals)]

    aarr_pct = [f"{v:,.0f}" if v >= 500 else "" for v in aarr_vals]
    normal_pct = [f"{v:,.0f}" if v >= 500 else "" for v in normal_vals]
    x_labels = [d.strftime("%m/%d\n%a") for d in all_dates]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=x_labels,
        y=aarr_vals,
        name="AARR",
        marker_color=MCD_RED,
        opacity=0.95,
        text=aarr_pct,
        textposition="inside",
        textfont=dict(size=11, color="#fff"),
    ))

    fig.add_trace(go.Bar(
        x=x_labels,
        y=normal_vals,
        name="常规",
        marker_color=MCD_GOLD,
        opacity=0.95,
        text=normal_pct,
        textposition="inside",
        textfont=dict(size=11, color="#5a1a00"),
    ))

    for d, t in zip(all_dates, total):
        if t > 0:
            fig.add_annotation(
                x=d.strftime("%m/%d\n%a"),
                y=t,
                text=f"{t:,.0f}",
                showarrow=False,
                yshift=10,
                font=dict(size=11, color="#1A1A1A"),
            )

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
        xaxis=dict(title="", gridcolor="#E8E8E8"),
        yaxis=dict(title="DAU（点击人次）", gridcolor="#E8E8E8", tickformat=","),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=12)),
        font=dict(family="Microsoft YaHei, PingFang SC, -apple-system, sans-serif"),
    )
    return fig


def render(df: pd.DataFrame, target_daily: int, week_start: pd.Timestamp = None) -> go.Figure:
    """渲染 Section 3（"目标拆解" 子标题，灰字极简）"""
    st.html(f"""
<div style="font-size:14px;font-weight:600;color:#6B6B6B;
  padding:6px 0 6px 0;margin:6px 0 12px 0;letter-spacing:.2px;">
  AARR / Normal 拆解
</div>
""")

    # 计算日累计
    fig = _build_aarr_figure(df, week_start, int(target_daily))
    if not fig.data:
        st.info("暂无 Operational 数据（AARRPlan / 常规Plan）")
        return fig
    st.plotly_chart(fig, use_container_width=True)
    return fig


def render_html(df: pd.DataFrame, target_daily: int, fig: go.Figure) -> str:
    """导出用：返回 HTML 片段（"目标拆解" 子标题，灰字极简）"""
    h2_title = '<h2 style="display:flex;align-items:center;gap:12px;font-size:19px;font-weight:800;color:#1A1A1A;letter-spacing:.3px;margin:0 0 14px 0;"><span style="display:flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:9px;background:#DB0005;color:#fff;font-size:15px;font-weight:800;flex-shrink:0;">3</span>AARR / Normal 拆解</h2>'

    if not fig.data:
        return f"""
<div id="sec-aarr"></div>
<section style="background:#FFFFFF;border:1px solid #E0E0E0;border-radius:14px;padding:24px 28px;margin-bottom:22px;">
  {h2_title}
  <p style="color:#6B6B6B;">暂无 Operational 数据</p>
</section>
"""

    fig_html = fig.to_html(include_plotlyjs=False, full_html=False, default_width="100%", default_height="320px")
    return f"""
<div id="sec-aarr"></div>
<section style="background:#FFFFFF;border:1px solid #E0E0E0;border-radius:14px;padding:24px 28px;margin-bottom:22px;box-shadow:0 1px 3px rgba(120,90,30,.05);">
  {h2_title}
  {fig_html}
</section>
"""
