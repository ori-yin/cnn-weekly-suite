"""
components.py - CNN Performance Weekly：可复用 UI 组件
参考 mcd-reach-trend 的 KPI Card 组件
"""


import re as _re
import streamlit as st
import markdown as _md

# 行首的 # / ## / ### 后无空格时自动补一格（CommonMark 规范要求 # 后必须有空格才是 heading）
# lookahead 排除 # 和空白，避免 `## 一段` 被错误拆成 `# # 一段`
# 仅在渲染时归一化，session_state 里保留用户原文，方便继续编辑
_HEAD_RE = _re.compile(r'^(#+)(?=[^#\s])', _re.MULTILINE)


def _norm_md(md: str) -> str:
    return _HEAD_RE.sub(r'\1 ', md)


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


def insight_block(key: str, label: str = "本板块洞察") -> str:
    """
    AI 占位 markdown block：UI 跟 tab_topics 一致（容器预览 + text_area 编辑）。
    每个埋点用独立的 key，session_state 隔离内容。

    - key:    session_state 中存 markdown 的键（每个调用点不同）
    - label:  区块标题（默认 "本板块洞察"）
    - 返回:   渲染后的 HTML 字符串（用于导出 HTML）；未填时返回 ""
    """
    SESSION_KEY = key
    EDITOR_KEY = key + "_editor"

    DEFAULT_MD = (
        "# 本板块洞察\n\n"
        "让 AI 读取整页 HTML 后写在此处。\n\n"
        "- 支持标题、列表、表格\n"
        "- 支持 **加粗** *斜体* `代码`\n"
    )

    if SESSION_KEY not in st.session_state:
        st.session_state[SESSION_KEY] = DEFAULT_MD

    md_src = st.session_state[SESSION_KEY]
    empty = (not md_src.strip()) or md_src.strip() == DEFAULT_MD.strip()

    with st.container(border=True):
        st.markdown(section_header(label, number=None, subtitle=""), unsafe_allow_html=True)
        if empty:
            st.info("暂无内容，请在下方编辑 Markdown。AI 读取整页 HTML 后把洞察写在这里。")
        else:
            html_preview = _md.markdown(_norm_md(md_src), extensions=["tables", "fenced_code"])
            st.markdown(html_preview, unsafe_allow_html=True)

    st.markdown('<div class="section-subheader">编辑 Markdown</div>', unsafe_allow_html=True)
    st.text_area(
        f"{label} Markdown 源",
        value=md_src,
        height=180,
        label_visibility="collapsed",
        key=EDITOR_KEY,
        on_change=lambda: st.session_state.__setitem__(SESSION_KEY, st.session_state[EDITOR_KEY]),
    )

    if empty:
        return ""
    return _md.markdown(_norm_md(md_src), extensions=["tables", "fenced_code"])
