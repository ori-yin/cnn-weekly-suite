"""
components/fmt.py - 数字格式化与辅助工具
"""


def fmt_number(val, unit: str = "") -> str:
    """格式化数字：大数 K / M，百分比 1 位"""
    if unit == "%":
        return f"{val:.1f}%"
    if val is None:
        return "—"
    try:
        val = float(val)
    except (TypeError, ValueError):
        return str(val)

    if abs(val) >= 1_000_000:
        return f"{val / 1_000_000:.1f}M"
    if abs(val) >= 1_000:
        return f"{val / 1_000:.1f}K"
    return f"{val:,.0f}"


def fmt_int(val) -> str:
    """千分位整数"""
    if val is None or val == "":
        return "—"
    try:
        return f"{int(val):,}"
    except (TypeError, ValueError):
        return str(val)


def gap_status(gap_pct: float, green_th: float, yellow_th: float) -> str:
    """根据 Gap 百分比判定状态，返回 'green'/'yellow'/'red'"""
    g = abs(gap_pct)
    if g <= green_th:
        return "green"
    if g <= yellow_th:
        return "yellow"
    return "red"


def status_emoji(status: str) -> str:
    """状态 → 中文色字标签（无 emoji）"""
    return {"green": "绿灯", "yellow": "黄灯", "red": "红灯"}.get(status, "—")


def status_label(status: str) -> str:
    """状态 → 完整中文标签"""
    return {"green": "绿灯", "yellow": "黄灯预警", "red": "红灯告警"}.get(status, "—")
