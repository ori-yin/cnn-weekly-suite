"""
sections/section1_overview.py - Section 1：总览
布局：环(1/3) | 周维度进度(2/3, 表格+备注编辑) · Nudge 横排在下方
"""
import pandas as pd
import streamlit as st

from emergency.config import MCD_DARK_RED
from emergency.components.ring import render_ring, render_ring_static_html
from emergency.components.day_table import render_day_table_editable, render_day_table_html
from emergency.components.nudge_grid import render_nudge_horizontal, render_nudge_horizontal_html


def _section_header(title: str) -> str:
    """Section 标题（无 ① 数字徽章，参考 Performance Weekly 风格）"""
    return f"""
<div style="font-size:20px;font-weight:800;color:{MCD_DARK_RED};
  padding:8px 0 8px 0;border-bottom:2px solid #DB0005;
  margin:8px 0 16px 0;letter-spacing:.3px;">{title}</div>
"""


def render(
    df: pd.DataFrame,
    target_daily: int,
    daily_clicks: dict,
    week_start: pd.Timestamp,
    actual_daily: int,
    completion: float,
    notes: dict | None = None,
):
    """渲染 Section 1（Streamlit）：环 + 周维度进度（表格+备注编辑）顶部，Nudge 横排底部"""
    st.html(_section_header("总览"))

    col_ring, col_day = st.columns([1, 2], vertical_alignment="top")

    with col_ring:
        render_ring(int(actual_daily), int(target_daily), float(completion), card_height=400)

    with col_day:
        render_day_table_editable(week_start, daily_clicks, int(target_daily), notes=notes)

    # Nudge 横排在 Section 1 下方
    render_nudge_horizontal(df)


def render_html(
    df: pd.DataFrame,
    target_daily: int,
    daily_clicks: dict,
    week_start: pd.Timestamp,
    actual_daily: int,
    completion: float,
    notes: dict | None = None,
) -> str:
    """导出用：返回完整 HTML 片段"""
    ring_html = render_ring_static_html(int(actual_daily), int(target_daily), float(completion))
    day_html = render_day_table_html(week_start, daily_clicks, int(target_daily), notes=notes)
    days_count = df["发送日期"].dt.date.nunique() if not df.empty else 0
    nudge_html = render_nudge_horizontal_html(df, days_count)

    return f"""
<div id="sec-overview"></div>
<section style="background:#FFFFFF;border:1px solid #E0E0E0;border-radius:14px;padding:24px 28px;margin-bottom:22px;box-shadow:0 1px 3px rgba(120,90,30,.05);">
  <h2 style="display:flex;align-items:center;gap:12px;font-size:19px;font-weight:800;color:#1A1A1A;letter-spacing:.3px;margin:0 0 14px 0;"><span style="display:flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:9px;background:#DB0005;color:#fff;font-size:15px;font-weight:800;flex-shrink:0;">1</span>总览</h2>
  <div style="display:grid;grid-template-columns:1fr 2fr;gap:18px;align-items:start;">
    <div style="background:#FFFFFF;border:1px solid #E0E0E0;border-radius:10px;padding:16px;box-shadow:0 1px 3px rgba(120,90,30,.06);height:400px;box-sizing:border-box;display:flex;flex-direction:column;">
      <div style="font-size:11px;font-weight:600;color:#888888;letter-spacing:.08em;text-transform:uppercase;margin-bottom:10px;">完成度</div>
      <div style="flex:1;display:flex;align-items:center;justify-content:center;">{ring_html}</div>
    </div>
    {day_html}
  </div>
  {nudge_html}
</section>
"""
