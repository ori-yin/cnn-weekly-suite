"""
components/kpi_card.py - KPI Card 组件
白底 + 3px 左色条（绿/黄/红）+ 上标签下数字 + 副文本
"""
from emergency.config import THEME_PAPER, THEME_LINE, THEME_INK2, THEME_MUTED, THEME_RADIUS_M
from .fmt import fmt_number, fmt_int


def kpi_card(
    label: str,
    value,
    sub: str = "",
    status: str = "",
    unit: str = "",
) -> str:
    """
    KPI 卡片 HTML 片段。
    - label: 指标名
    - value: 主数值
    - sub: 副文本
    - status: green / yellow / red（影响左侧 3px 色条颜色）
    - unit: 数值单位（"%"/"次" 等）
    """
    status_class = f" kpi-status-{status}" if status in ("green", "yellow", "red") else ""

    if isinstance(value, (int, float)):
        if unit and unit != "次":
            val_str = fmt_number(value, unit=unit)
        else:
            val_str = fmt_int(value) if (unit == "次" or isinstance(value, int)) else fmt_number(value)
    else:
        val_str = str(value) if value not in (None, "") else "—"

    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else '<div class="kpi-sub">&nbsp;</div>'

    return f"""
<div class="kpi-card{status_class}">
  <div class="kpi-label">{label}</div>
  <div class="kpi-value">{val_str}</div>
  {sub_html}
</div>
"""


def kpi_row(cards: list, gap: str = "12px") -> str:
    """把多个 KPI 卡片排成一行（CSS Grid 等宽）"""
    items = "".join(c for c in cards)  # 直接平铺，避免外层 <div> 干扰
    return (
        f'<div style="display:grid;grid-template-columns:repeat({len(cards)},1fr);'
        f'gap:{gap};margin:0 0 12px 0;">'
        f'{items}'
        f'</div>'
    )
