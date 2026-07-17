"""
sections/section4_channels.py - Section 4：渠道 DAU 拆解（5 渠道堆积）
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from emergency.config import THEME_BG, CHANNEL_COLORS, CHANNEL_TEXT_COLOR, CHANNELS


def _build_channels_figure(df: pd.DataFrame, week_start, target: int, days_total: int = 7) -> go.Figure:
    """构建 5 渠道堆积柱状图，固定 7 天 X 轴"""
    if week_start is None:
        return go.Figure()

    # 构造完整 7 天
    all_dates = [(week_start + pd.Timedelta(days=i)).date() for i in range(days_total)]

    if not df.empty:
        daily_ch = df.groupby([df["发送日期"].dt.date, "渠道"]).agg(
            DAU=("点击人次", "sum")
        ).reset_index()
        daily_ch.columns = ["日期", "渠道", "DAU"]
        daily_total = daily_ch.groupby("日期")["DAU"].sum().to_dict()
    else:
        daily_total = {}

    fig = go.Figure()

    for ch in CHANNELS:
        # 按渠道生成 7 天数据（缺数据为 0）
        if not df.empty:
            subset = daily_ch[daily_ch["渠道"] == ch] if "daily_ch" in dir() else None
            ch_by_date = subset.set_index("日期")["DAU"].reindex(all_dates, fill_value=0) if subset is not None else [0]*days_total
        else:
            ch_by_date = [0] * days_total

        ch_values = list(ch_by_date.values) if hasattr(ch_by_date, 'values') else list(ch_by_date)

        # 柱内文字
        text_labels = []
        for d, v in zip(all_dates, ch_values):
            t = daily_total.get(d, 0)
            if v == 0 or t == 0:
                text_labels.append("")
            elif v >= 500:
                text_labels.append(f"{v:,.0f}")
            else:
                text_labels.append("")

        fig.add_trace(go.Bar(
            x=[d.strftime("%m/%d\n%a") for d in all_dates],
            y=ch_values,
            name=ch,
            marker_color=CHANNEL_COLORS.get(ch, "#999"),
            opacity=0.95,
            text=text_labels,
            textposition="inside",
            textfont=dict(size=10, color=CHANNEL_TEXT_COLOR.get(ch, "#fff")),
        ))

    # 柱子顶部总数
    for d in all_dates:
        t = daily_total.get(d, 0)
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
        height=360,
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
    """渲染 Section 4（"目标拆解" 子标题，灰字极简）"""
    st.html(f"""
<div style="font-size:14px;font-weight:600;color:#6B6B6B;
  padding:6px 0 6px 0;margin:6px 0 12px 0;letter-spacing:.2px;">
  渠道 DAU
</div>
""")

    fig = _build_channels_figure(df, week_start, int(target_daily))
    if not fig.data:
        st.info("暂无渠道数据")
        return fig
    st.plotly_chart(fig, use_container_width=True)
    return fig


def render_html(df: pd.DataFrame, target_daily: int, fig: go.Figure) -> str:
    """导出用：返回 HTML 片段（"目标拆解" 子标题，灰字极简）"""
    h2_title = '<h2 style="display:flex;align-items:center;gap:12px;font-size:19px;font-weight:800;color:#1A1A1A;letter-spacing:.3px;margin:0 0 14px 0;"><span style="display:flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:9px;background:#DB0005;color:#fff;font-size:15px;font-weight:800;flex-shrink:0;">4</span>渠道 DAU</h2>'

    if not fig.data:
        return f"""
<div id="sec-channels"></div>
<section style="background:#FFFFFF;border:1px solid #E0E0E0;border-radius:14px;padding:24px 28px;margin-bottom:22px;">
  {h2_title}
  <p style="color:#6B6B6B;">暂无渠道数据</p>
</section>
"""

    fig_html = fig.to_html(include_plotlyjs=False, full_html=False, default_width="100%", default_height="360px")
    return f"""
<div id="sec-channels"></div>
<section style="background:#FFFFFF;border:1px solid #E0E0E0;border-radius:14px;padding:24px 28px;margin-bottom:22px;box-shadow:0 1px 3px rgba(120,90,30,.05);">
  {h2_title}
  {fig_html}
</section>
"""
