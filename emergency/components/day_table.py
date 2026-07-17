"""
components/day_table.py - 天数表
显示：周一~周日（7天）已过 N / 剩余 N / 达标 M/N
"""
import pandas as pd
from datetime import timedelta
from emergency.config import MCD_GREEN, MCD_RED, MCD_GOLD


def render_day_table_html(
    week_start: pd.Timestamp,
    daily_clicks: dict,  # {date: clicks}
    target: int,
    notes: dict | None = None,  # {date_str: note_text}
) -> str:
    """渲染 7 天表格 HTML（周一到周日）"""
    week_end = week_start + timedelta(days=6)
    days_zh = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    today = pd.Timestamp.today().normalize()
    elapsed = 0
    hit = 0

    notes = notes or {}

    rows = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        d_date = d.date()
        d_str = d_date.strftime("%Y-%m-%d")
        clicks = int(daily_clicks.get(d_date, 0) or 0)
        is_elapsed = d_date < today.date()
        is_hit = clicks >= target and target > 0
        if is_elapsed:
            elapsed += 1
            if is_hit:
                hit += 1
        rows.append({
            "dow": days_zh[i],
            "date": d_date,
            "d_str": d_str,
            "clicks": clicks,
            "is_elapsed": is_elapsed,
            "is_hit": is_hit,
            "is_today": d_date == today.date(),
            "note": (notes.get(d_str) or "").strip(),
        })

    remaining = 7 - elapsed
    need_target = target  # 警示
    # 剩余需日均补足
    if remaining > 0 and target > 0:
        total_actual = sum(r["clicks"] for r in rows if r["is_elapsed"])
        need_daily = max(0, (target * 7 - total_actual) / remaining)
    else:
        need_daily = 0

    def td_style(r, extra: str = ""):
        base = "padding:8px 12px;border-bottom:1px solid #E0E0E0;text-align:center;"
        if r["is_today"]:
            return base + "background:#fff8e1;font-weight:700;" + extra
        if not r["is_elapsed"]:
            return base + "color:#AAAAAA;" + extra
        return base + extra

    th_style = "background:#1A1A1A;color:#fff;padding:10px 12px;font-weight:700;font-size:12px;text-align:center;"

    rows_html = ""
    for r in rows:
        status_badge = ""
        if not r["is_elapsed"]:
            status_badge = '<span style="color:#AAAAAA;font-size:11px;">—</span>'
        elif r["is_hit"]:
            status_badge = f'<span style="background:{MCD_GREEN};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:700;">达标</span>'
        else:
            status_badge = f'<span style="background:{MCD_RED};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:700;">未达</span>'

        click_text = f"{r['clicks']:,.0f}" if r["is_elapsed"] else "—"
        note_text = r["note"] or ""
        if note_text:
            # 备注单元格：左对齐、灰字、自动换行
            note_cell = f'<span style="color:#1A1A1A;font-size:12px;text-align:left;display:block;line-height:1.4;">{note_text}</span>'
        else:
            note_cell = '<span style="color:#AAAAAA;font-size:11px;">—</span>'

        rows_html += (
            f"<tr>"
            f"<td style='{td_style(r)}'>{r['dow']}</td>"
            f"<td style='{td_style(r)}'>{r['date']}</td>"
            f"<td style='{td_style(r)}font-weight:600;font-variant-numeric:tabular-nums;'>{click_text}</td>"
            f"<td style='{td_style(r)}'>{status_badge}</td>"
            f"<td style='{td_style(r, 'text-align:left;max-width:160px;')}'>{note_cell}</td>"
            f"</tr>"
        )

    table_html = f"""
<div style="background:#FFFFFF;border:1px solid #E0E0E0;border-radius:10px;overflow:hidden;
            box-shadow:0 1px 3px rgba(120,90,30,.06);height:400px;box-sizing:border-box;
            display:flex;flex-direction:column;">
  <div style="padding:14px 16px;border-bottom:1px solid #E0E0E0;display:flex;justify-content:space-between;align-items:center;">
    <div style="font-size:11px;font-weight:600;color:#888888;letter-spacing:.08em;text-transform:uppercase;">周维度进度</div>
    <div style="font-size:11.5px;color:#6B6B6B;">
      已过 <b style="color:#00A04A;">{elapsed}</b> / 剩余 <b style="color:#FF9500;">{remaining}</b> 天 ·
      达标 <b style="color:#DB0005;">{hit}/{elapsed}</b>
    </div>
  </div>
  <div style="flex:1;overflow:auto;">
    <table style="width:100%;border-collapse:collapse;font-size:13px;table-layout:fixed;">
      <colgroup>
        <col style="width:14%">
        <col style="width:20%">
        <col style="width:18%">
        <col style="width:16%">
        <col>
      </colgroup>
      <thead>
        <tr>
          <th style="{th_style}text-align:left;">星期</th>
          <th style="{th_style}">日期</th>
          <th style="{th_style}">DAU</th>
          <th style="{th_style}">状态</th>
          <th style="{th_style}text-align:left;">备注</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>
  <div style="padding:10px 16px;font-size:11.5px;color:#6B6B6B;border-top:1px solid #E0E0E0;background:#F5F5F5;">
    剩余 {remaining} 天需日均 <b style="color:#DB0005;font-weight:800;">{need_daily:,.0f}</b> 才能完成周目标 {target * 7:,.0f}
  </div>
</div>
"""
    return table_html


def render_day_table_editable(week_start, daily_clicks, target, notes: dict | None = None) -> None:
    """Streamlit 版：st.data_editor 表格，备注列可原地编辑（其他列 disabled）

    编辑后自动同步到 session_state[f"note_{YYYY-MM-DD}"]，供下载 HTML 复用
    """
    import pandas as pd
    import streamlit as st
    from datetime import timedelta

    days_zh = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    today = pd.Timestamp.today().normalize()

    # 汇总统计（头部 + 尾部用）
    elapsed = 0
    hit = 0
    total_actual = 0
    for i in range(7):
        d = week_start + timedelta(days=i)
        d_date = d.date()
        clicks = int(daily_clicks.get(d_date, 0) or 0)
        is_elapsed = d_date < today.date()
        is_hit = clicks >= target and target > 0
        if is_elapsed:
            elapsed += 1
            total_actual += clicks
            if is_hit:
                hit += 1

    remaining = 7 - elapsed
    if remaining > 0 and target > 0:
        need_daily = max(0, (target * 7 - total_actual) / remaining)
    else:
        need_daily = 0

    # 编辑器数据
    rows = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        d_date = d.date()
        d_str = d_date.strftime("%Y-%m-%d")
        clicks = int(daily_clicks.get(d_date, 0) or 0)
        is_elapsed = d_date < today.date()
        is_hit = clicks >= target and target > 0

        if is_hit:
            status = "达标"
        elif is_elapsed:
            status = "未达"
        else:
            status = "—"

        rows.append({
            "星期": days_zh[i],
            "日期": d_date.strftime("%m-%d"),
            "DAU": f"{clicks:,.0f}" if is_elapsed else "—",
            "状态": status,
            "备注": (notes or {}).get(d_str, ""),
        })

    df = pd.DataFrame(rows)

    # 卡片容器（含 border，匹配暖色纸质风）
    with st.container(border=True):
        st.html(f"""
<div style="padding:12px 16px;border-bottom:1px solid #E0E0E0;display:flex;justify-content:space-between;align-items:center;">
  <div style="font-size:11px;font-weight:600;color:#888888;letter-spacing:.08em;text-transform:uppercase;">周维度进度</div>
  <div style="font-size:11.5px;color:#6B6B6B;">
    已过 <b style="color:#00A04A;">{elapsed}</b> / 剩余 <b style="color:#FF9500;">{remaining}</b> 天 ·
    达标 <b style="color:#DB0005;">{hit}/{elapsed}</b>
  </div>
</div>
""")
        edited = st.data_editor(
            df,
            column_config={
                "星期": st.column_config.TextColumn(disabled=True, width="small"),
                "日期": st.column_config.TextColumn(disabled=True, width="small"),
                "DAU":  st.column_config.TextColumn(disabled=True, width="small"),
                "状态": st.column_config.TextColumn(disabled=True, width="small"),
                "备注": st.column_config.TextColumn(width="large"),
            },
            hide_index=True,
            use_container_width=True,
            key="day_notes_editor",
            height=280,
        )
        # 同步到 session_state，下载 HTML 时从这里取
        for i, row in edited.iterrows():
            d = week_start + timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            st.session_state[f"note_{d_str}"] = row["备注"]
        st.html(f"""
<div style="padding:8px 16px;font-size:11.5px;color:#6B6B6B;border-top:1px solid #E0E0E0;background:#F5F5F5;">
  剩余 {remaining} 天需日均 <b style="color:#DB0005;font-weight:800;">{need_daily:,.0f}</b> 才能完成周目标 {target * 7:,.0f}
</div>
""")
