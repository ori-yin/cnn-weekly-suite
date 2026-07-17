"""
components/nudge_grid.py - Nudge Type 拆解（4 类）

**关键口径说明**：
- 这里的 "Operational 日均 = 点击人次 / 周期天数"，与 Section 1 KPI 的 "DAU 去重" 是
  两个**不同**指标。前者按 Plan-渠道行累加（不去重），后者来自 Sheet 2 已去重的 DAU。
- 不要尝试让两边数值相等，它们会不同；这是设计，而非 bug。
"""
import streamlit as st


def _compute(df, plan_type_filter, days_in_df: int):
    """sum 点击人次，分母 = days_in_df（与 Section 1 同样的全周期天数）"""
    sub = df[df["计划类型"].isin(plan_type_filter)] if isinstance(plan_type_filter, list) else df[df["计划类型"] == plan_type_filter]
    if sub.empty or days_in_df == 0:
        return 0, 0
    clicks = int(sub["点击人次"].sum())
    daily = clicks / days_in_df
    return clicks, daily


# ─── 横排版本（用于 Section 1 下方，4 类卡片并列） ───

def render_nudge_horizontal_html(df, days_in_df: int) -> str:
    """横排 Nudge Type 拆解（3 张卡：Operational 合并 / On-demand / Responsive）

    层级：
      Operational = AARR + 常规（有 Target，活跃）
      On-demand / Responsive = 其他（无 Target）
    """
    op_clicks, op_daily = _compute(df, ["AARRPlan", "常规Plan"], days_in_df)
    aarr_clicks, aarr_daily = _compute(df, "AARRPlan", days_in_df)
    normal_clicks, normal_daily = _compute(df, "常规Plan", days_in_df)
    od_clicks, od_daily = _compute(df, "On-demand", days_in_df)
    rp_clicks, rp_daily = _compute(df, "Responsive", days_in_df)

    def value_html(daily: float, has_data: bool) -> str:
        if not has_data or daily <= 0:
            return '<span style="color:#AAAAAA;font-size:22px;font-weight:700;">—</span>'
        return f'<span style="font-size:22px;font-weight:800;color:#1A1A1A;font-variant-numeric:tabular-nums;letter-spacing:-0.02em;">{daily:,.0f}</span>'

    def total_html(total: int, has_data: bool) -> str:
        if not has_data or total <= 0:
            return '<span style="color:#AAAAAA;font-size:11px;">暂无</span>'
        return f'<span style="font-size:11px;color:#888888;">累计 {total:,}</span>'

    def simple_card(label: str, label_color: str, daily: float, total: int, has_data: bool) -> str:
        return f"""
<div style="background:#FFFFFF;border:1px solid #E0E0E0;border-radius:10px;padding:12px 14px;box-shadow:0 1px 3px rgba(120,90,30,.06);">
  <div style="font-size:12px;font-weight:700;color:{label_color};letter-spacing:.02em;margin-bottom:6px;">{label}</div>
  <div style="display:flex;align-items:baseline;gap:4px;margin-bottom:4px;">{value_html(daily, has_data)}<span style="font-size:11px;color:#888888;font-weight:500;">/ 日均</span></div>
  <div>{total_html(total, has_data)}</div>
</div>
"""

    def operational_card() -> str:
        """Operational 合并卡：合并 AARR + 常规，下方展示子项"""
        sub_row = ""
        if aarr_daily > 0 or normal_daily > 0:
            aarr_str = f'<span style="color:#1A1A1A;font-weight:700;">AARR</span> <b style="font-variant-numeric:tabular-nums;color:#1A1A1A;">{aarr_daily:,.0f}</b>' if aarr_daily > 0 else '<span style="color:#AAAAAA;">AARR —</span>'
            normal_str = f'<span style="color:#1A1A1A;font-weight:700;">常规</span> <b style="font-variant-numeric:tabular-nums;color:#1A1A1A;">{normal_daily:,.0f}</b>' if normal_daily > 0 else '<span style="color:#AAAAAA;">常规 —</span>'
            sub_row = f"""
<div style="margin-top:8px;padding-top:8px;border-top:1px dashed #E0E0E0;font-size:11.5px;color:#6B6B6B;line-height:1.7;display:flex;gap:14px;flex-wrap:wrap;">
  <span>{aarr_str}</span>
  <span>{normal_str}</span>
</div>
"""
        elif aarr_daily == 0 and normal_daily == 0:
            sub_row = f"""
<div style="margin-top:8px;padding-top:8px;border-top:1px dashed #E0E0E0;font-size:11px;color:#AAAAAA;">
  暂无 AARR / 常规 数据
</div>
"""

        return f"""
<div style="background:#FFFFFF;border:1px solid #E0E0E0;border-radius:10px;padding:12px 14px;box-shadow:0 1px 3px rgba(120,90,30,.06);">
  <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
    <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#DB0005;"></span>
    <span style="font-size:12px;font-weight:700;color:#DB0005;letter-spacing:.02em;">OPERATIONAL</span>
  </div>
  <div style="display:flex;align-items:baseline;gap:4px;margin-bottom:4px;">{value_html(op_daily, op_daily > 0)}<span style="font-size:11px;color:#888888;font-weight:500;">/ 日均</span></div>
  <div>{total_html(op_clicks, op_clicks > 0)}</div>
  {sub_row}
</div>
"""

    cards_html = (
        operational_card()
        + simple_card("On-demand", "#888888", od_daily, od_clicks, od_daily > 0)
        + simple_card("Responsive", "#888888", rp_daily, rp_clicks, rp_daily > 0)
    )

    op_daily_str = f"{op_daily:,.0f}" if op_daily > 0 else "—"

    return f"""
<div style="margin-top:18px;padding-top:18px;border-top:1px solid #E0E0E0;">
  <div style="margin-bottom:12px;">
    <div style="font-size:11px;font-weight:600;color:#888888;letter-spacing:.08em;text-transform:uppercase;">Nudge Type 拆解</div>
  </div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
    {cards_html}
  </div>
  <div style="font-size:10.5px;color:#AAAAAA;margin-top:10px;line-height:1.5;">
    注：此口径为 Plan 级点击人次累计（不去重）；与左侧 Section 1 的去重 DAU 不可比。
  </div>
</div>
"""


def render_nudge_horizontal(df) -> None:
    """Streamlit 版：横排 4 类卡片"""
    days_in_df = df["发送日期"].dt.date.nunique() if not df.empty else 0
    html = render_nudge_horizontal_html(df, days_in_df)
    st.html(html)
