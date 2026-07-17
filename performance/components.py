"""
components.py - CNN Performance Weekly：可复用 UI 组件
参考 mcd-reach-trend 的 KPI Card 组件
"""


def _fmt_number(val, unit=""):
    """格式化数字：大数用 K/M，百分比保留 1 位"""
    if unit == "%":
        return f"{val:.1f}%"
    if abs(val) >= 1_000_000:
        return f"{val / 1_000_000:.1f}M"
    elif abs(val) >= 1_000:
        return f"{val / 1_000:.1f}K"
    return f"{val:,.0f}"


def kpi_card(label: str, value, sub: str = "", status: str = "", unit: str = "") -> str:
    """
    KPI 卡片组件。
    - label: 指标名
    - value: 主数值
    - sub: 副文本（环比等）
    - status: green/yellow/red（左侧色条）
    - unit: 数值单位（如 "%"），传入时格式化为百分比
    """
    status_class = status if status in ("green", "yellow", "red") else ""

    # Target 为 0 时显示 "/"
    if isinstance(value, (int, float)) and value == 0 and "Target" in label:
        val_str = "/"
    elif unit:
        val_str = _fmt_number(value, unit=unit)
    elif isinstance(value, (int, float)):
        val_str = _fmt_number(value)
    else:
        val_str = str(value)

    sub_html = ""
    if sub:
        # 自动标记 ↑↓ 颜色
        if "↑" in sub:
            sub_html = f'<div class="kpi-sub"><span class="up">{sub}</span></div>'
        elif "↓" in sub:
            sub_html = f'<div class="kpi-sub"><span class="down">{sub}</span></div>'
        else:
            sub_html = f'<div class="kpi-sub">{sub}</div>'

    fallback_sub = '<div class="kpi-sub">&nbsp;</div>'
    return (
        f'<div class="kpi-card {status_class}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{val_str}</div>'
        f'{sub_html if sub_html else fallback_sub}'
        f'</div>'
    )


def kpi_row(cards: list) -> str:
    """将多个 KPI Card 排成一行，CSS Grid 等宽等高"""
    n = len(cards)
    items = "".join(f"<div>{c}</div>" for c in cards)
    return (
        f'<div style="display:grid;grid-template-columns:repeat({n},1fr);gap:10px;margin-bottom:12px;">'
        f'{items}'
        f'</div>'
    )


def section_header(title: str, number: int = None, subtitle: str = "") -> str:
    """Section 大标题 H2：红色方块徽章 + 黑标题（参照 preview_v7）"""
    if number is not None:
        head = f'<div class="section-header"><span class="sec-num">{number}</span><h2>{title}</h2></div>'
    else:
        head = f'<div class="section-header"><h2>{title}</h2></div>'
    sub = f'<div class="section-subheader">{subtitle}</div>' if subtitle else ""
    return head + sub
