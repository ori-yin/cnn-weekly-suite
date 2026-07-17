"""
page.py - CNN Emergency Weekly 模式渲染（由 suite/app.py 调用）
应急看板：看 Gap 决定要不要补量。
数据（raw_df, dau_df）由入口统一上传后传入，本模块不再自行读取文件。
"""
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from emergency.config import (
    TARGET_DEFAULT_DAU,
    GREEN_GAP, YELLOW_GAP,
)
from shared.data import filter_week_data
from shared.header import render_header, clear_header
from shared.footer import render_footer
from shared.styles import get_css
from emergency.components.fmt import gap_status
from emergency.sections import section1_overview, section2_dau, section3_aarr, section4_channels
from emergency.export import build_export_html


def render_page(raw_df, dau_df):
    """Emergency 模式主渲染。raw_df / dau_df 由 suite/app.py 统一上传后传入。"""
    st.html(get_css("emergency"))

    # ─── Sidebar ────────────────────────────────────────
    with st.sidebar:
        st.markdown("---")
        target_dau = st.number_input(
            "Target DAU（日均）",
            min_value=0,
            value=TARGET_DEFAULT_DAU,
            step=1000,
            help="本周每日目标点击人次（DAU 核心口径）",
        )

    # 阈值固定（仅 UI 简化，业务逻辑不变）
    green_th = GREEN_GAP
    yellow_th = YELLOW_GAP

    # ─── 主体 ─────────────────────────────────────────
    if raw_df is None or raw_df.empty:
        clear_header()
        _render_placeholder()
        return

    # ─── 日期范围选择 ─────────────────────────────────
    data_min = raw_df["发送日期"].min().date()
    data_max = raw_df["发送日期"].max().date()

    # 默认本周一~本周日（与数据范围取交集，可手动调整）
    today = date.today()
    days_since_monday = today.weekday()
    this_monday = today - timedelta(days=days_since_monday)
    this_sunday = this_monday + timedelta(days=6)
    default_start = max(this_monday, data_min)
    default_end = min(this_sunday, data_max)

    # 兜底：start > end → 退到 data_max 单天
    if default_start > default_end:
        default_start = default_end

    with st.sidebar:
        st.markdown("---")
        st.markdown("##### 日期范围")
        start_date = st.date_input("开始日期", value=default_start, min_value=data_min, max_value=data_max)
        end_date = st.date_input("结束日期", value=default_end, min_value=data_min, max_value=data_max)

    if start_date > end_date:
        st.error("开始日期不能晚于结束日期")
        return

    # 筛选数据
    df = filter_week_data(raw_df, start_date, end_date)
    if df.empty:
        st.warning(f"[{start_date} ~ {end_date}] 范围内无数据")
        return

    # ─── 计算关键指标 ─────────────────────────────────
    metrics = _compute_weekly_metrics(df, dau_df, start_date, end_date, target_dau)

    (
        actual_daily, completion, gap_pct, status,
        days_elapsed, days_remaining, hit_days, need_daily,
        total_clicks, daily_clicks, week_start,
    ) = metrics

    # ─── 备注：从 session_state 读取 7 天的备注（缺失则初始化为空） ───
    day_notes: dict = {}
    for i in range(7):
        d = week_start + timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        note_key = f"note_{d_str}"
        if note_key not in st.session_state:
            st.session_state[note_key] = ""
        day_notes[d_str] = st.session_state[note_key]

    # ─── 顶部栏 + 导航栏（与 Performance 统一风格）─────────
    period_str = f"{start_date} ~ {end_date}"
    render_header("CNN Emergency", "周度 DAU 应急看板", badge=period_str, nav_links=[
        ("sec-overview", "应急概览"),
        ("sec-dau", "目标拆解"),
    ])

    # ─── 4 个 Section（带锚点，供导航跳转）─────────────────
    st.markdown('<div id="sec-overview"></div>', unsafe_allow_html=True)
    section1_overview.render(df, target_dau, daily_clicks, pd.Timestamp(week_start),
                              actual_daily, completion, notes=day_notes)

    # week_start（pd.Timestamp）传给所有 section，让柱状图固定 7 天 X 轴
    week_start_ts = pd.Timestamp(week_start)

    st.markdown('<div id="sec-dau"></div>', unsafe_allow_html=True)
    fig2 = section2_dau.render(df, target_dau, daily_clicks, gap_pct, completion,
                                actual_daily, hit_days, days_elapsed, days_remaining,
                                need_daily, status, week_start=week_start_ts)

    st.markdown('<div id="sec-aarr"></div>', unsafe_allow_html=True)
    fig3 = section3_aarr.render(df, target_dau, week_start=week_start_ts)
    st.markdown('<div id="sec-channels"></div>', unsafe_allow_html=True)
    fig4 = section4_channels.render(df, target_dau, week_start=week_start_ts)

    # ─── 本周备注编辑面板已挪到 Section 1 内部（紧贴 day table） ───

    # ─── Sidebar 导出按钮 ─────────────────────────────
    with st.sidebar:
        st.markdown("---")
        period_str = f"{start_date} ~ {end_date}"
        today_str = date.today().strftime("%Y-%m-%d")
        try:
            html_content = build_export_html(
                df=df,
                target_daily=target_dau,
                actual_daily=int(actual_daily),
                completion=float(completion),
                gap_pct=float(gap_pct),
                status=status,
                daily_clicks=daily_clicks,
                week_start=week_start,
                week_end=start_date + timedelta(days=6),
                days_elapsed=days_elapsed,
                days_remaining=days_remaining,
                hit_days=hit_days,
                need_daily=int(need_daily),
                green_th=green_th,
                yellow_th=yellow_th,
                fig2=fig2,
                fig3=fig3,
                fig4=fig4,
                period_str=period_str,
                day_notes=day_notes,
            )
        except Exception as e:
            html_content = ""
            st.caption(f"导出构建失败：{e}")

        st.download_button(
            label="下载html",
            data=html_content or "<html><body>请先刷新页面</body></html>",
            file_name=f"cnn_emergency_{today_str}.html",
            mime="text/html",
            use_container_width=True,
            disabled=not html_content,
        )

    # ─── 页脚部门版权 ─────────────────────────────────────
    render_footer()


def _compute_weekly_metrics(df, dau_df, start_date, end_date, target_daily):
    """
    计算周维度关键指标。

    重要：这里的「actual / Gap」是 **去重 DAU**（Sheet 2）；
    Nudge 拆解里的「Operational」是 **点击人次**（Sheet 1，不去重）。
    两个数字本就不同，是不同口径，不要"对齐"。

    返回: (actual_daily, completion, gap_pct, status, days_elapsed, days_remaining,
           hit_days, need_daily, total_clicks, daily_clicks, week_start)
    """
    # ── 去重 DAU：优先 Sheet 2，回退 Sheet 1 ──
    if dau_df is not None and not dau_df.empty and "DAU" in dau_df.columns:
        dau_filtered = dau_df[(dau_df["日期"].dt.date >= start_date) & (dau_df["日期"].dt.date <= end_date)].copy()
        daily_clicks = {d.date(): float(v) for d, v in dau_filtered[["日期", "DAU"]].itertuples(index=False)}
        dau_source = "Sheet 2 去重 DAU"
    else:
        # 回退：用 Sheet 1 点击人次（不去重）
        daily = df.groupby(df["发送日期"].dt.date)["点击人次"].sum().to_dict()
        daily_clicks = {pd.Timestamp(k).date() if hasattr(k, "date") else k: float(v) for k, v in daily.items()}
        dau_source = "Sheet 1 点击人次（无去重）"

    days_elapsed = len(daily_clicks)
    days_total = 7
    days_remaining = max(0, days_total - days_elapsed)

    total_clicks = sum(int(v) for v in daily_clicks.values())
    actual_daily = total_clicks / days_elapsed if days_elapsed > 0 else 0
    completion = actual_daily / target_daily if target_daily > 0 else 0
    gap_pct = (actual_daily - target_daily) / target_daily if target_daily > 0 else 0

    hit_days = sum(1 for v in daily_clicks.values() if target_daily > 0 and v >= target_daily) if target_daily > 0 else 0

    if days_remaining > 0 and target_daily > 0:
        need_daily = max(0, (target_daily * days_total - total_clicks) / days_remaining)
    else:
        need_daily = 0

    status = gap_status(gap_pct, GREEN_GAP, YELLOW_GAP) if target_daily > 0 else "green"

    week_start = start_date

    return (
        actual_daily, completion, gap_pct, status,
        days_elapsed, days_remaining, hit_days, need_daily,
        total_clicks, daily_clicks, week_start,
    )


def _render_placeholder():
    """未上传数据时的占位"""
    import base64
    logo_path = Path(__file__).parent.parent / "assets" / "mcdonalds.svg"
    logo_html = ""
    if logo_path.exists():
        b64 = base64.b64encode(logo_path.read_bytes()).decode()
        logo_html = f'<img src="data:image/svg+xml;base64,{b64}" style="height:54px;width:auto;margin-bottom:14px;" alt="McDonald\'s"/>'

    st.html(f"""
<div style="background:#FFFFFF;border:1px solid #E0E0E0;border-radius:14px;padding:48px;text-align:center;margin:40px 0;box-shadow:0 1px 3px rgba(120,90,30,.05);">
  {logo_html}
  <div style="font-size:18px;font-weight:700;color:#1A1A1A;margin-bottom:8px;">CNN Emergency</div>
  <div style="font-size:14px;color:#6B6B6B;line-height:1.8;">
    请上传 <code>cnn0629.xlsx</code>（与 Performance Weekly 共用）<br>
    看完 4 个 Section 的 Gap 大小，决定要不要补量<br>
    一键导出静态 HTML 报告
  </div>
</div>
""")
