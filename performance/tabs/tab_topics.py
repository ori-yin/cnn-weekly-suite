"""
tab_topics.py - 实验专题
Markdown 自由编辑区，本周展示用户自定义内容（实验数据/结论等）。
"""

import streamlit as st
import markdown as _md
from performance.components import section_header

SESSION_KEY = "topics_md"
EDITOR_KEY = "topics_md_editor"


def _default_md() -> str:
    return (
        "# 本周专题\n\n"
        "暂无实验专题，请编辑下方 Markdown。\n\n"
        "- 支持标题、列表、表格\n"
        "- 支持 **加粗** *斜体* `代码`\n"
    )


def _on_change():
    """text_area 失焦/Enter 时把内容同步到 SESSION_KEY。"""
    st.session_state[SESSION_KEY] = st.session_state[EDITOR_KEY]


def _is_empty(md_src: str) -> bool:
    s = md_src.strip()
    return (not s) or s == _default_md().strip()


def render() -> str:
    """UI 渲染 + 返回渲染版 HTML 供导出。无参数。

    返回空串表示未填，导出端不渲染此 section。
    """
    if SESSION_KEY not in st.session_state:
        st.session_state[SESSION_KEY] = _default_md()

    md_src = st.session_state[SESSION_KEY]
    empty = _is_empty(md_src)

    # 预览区（始终渲染）
    with st.container(border=True):
        st.markdown(section_header("实验专题", number=5, subtitle=""), unsafe_allow_html=True)
        if empty:
            st.info("暂无实验专题，请在下方编辑 Markdown 内容。")
        else:
            html = _md.markdown(md_src, extensions=["tables", "fenced_code"])
            st.markdown(html, unsafe_allow_html=True)

    # 编辑区（on_change 模式，keystroke 不触发 rerun）
    st.markdown('<div class="section-subheader">编辑 Markdown</div>', unsafe_allow_html=True)
    st.text_area(
        "Markdown 源",
        value=md_src,
        height=320,
        label_visibility="collapsed",
        key=EDITOR_KEY,
        on_change=_on_change,
    )

    if empty:
        return ""
    return _md.markdown(md_src, extensions=["tables", "fenced_code"])
