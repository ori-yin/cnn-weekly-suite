"""
shared/header.py - 两模式统一的固定顶栏 + 导航栏（全宽、吸顶）

header 节点由 JS 自行 createElement 后插入 parent.document.body（带固定 id），
不搬动 React 管理的节点，因此不会触发 removeChild 崩溃；切换模式时按 id 替换。
顶部留白由各 styles.py 的 .block-container padding-top 一个数字控制。
"""
import base64
import json
from pathlib import Path

import streamlit.components.v1 as components

_ASSETS = Path(__file__).parent.parent / "assets"


def _logo_b64() -> str:
    return base64.b64encode((_ASSETS / "mcdonalds.svg").read_bytes()).decode()


def _build_html(title: str, subtitle: str, badge: str, nav_links) -> str:
    # 左侧：徽章 + 标题 + 副标题 三段堆叠
    date_badge = (
        f'<span class="date-badge">{badge}</span>' if badge else ""
    )
    left = (
        '<div class="header-left">'
        f'{date_badge}'
        f'<h1 class="header-title">{title}</h1>'
        f'<div class="header-sub">{subtitle}</div>'
        '</div>'
    )
    # 右侧：logo
    right = (
        '<div class="header-right">'
        f'<img src="data:image/svg+xml;base64,{_logo_b64()}" class="header-logo" alt="McDonald\'s">'
        '</div>'
    )
    topbar = f'<div class="topbar" id="suite-topbar" style="left:280px;">{left}{right}</div>'
    nav = ""
    if nav_links:
        items = "".join(
            f'<a class="nav-link" href="#{aid}">{label}</a>' for aid, label in nav_links
        )
        nav = f'<div class="nav-bar" id="suite-nav" style="left:280px;">{items}</div>'
    return topbar + nav


_INJECT_JS = """
<script>
(function(){
  var doc = parent.document, body = doc.body;
  ['suite-topbar','suite-nav'].forEach(function(id){ var e = doc.getElementById(id); if (e) e.remove(); });
  var holder = doc.createElement('div');
  holder.innerHTML = __HTML__;
  while (holder.firstChild) body.appendChild(holder.firstChild);
})();
</script>
"""

_CLEAR_JS = """
<script>
(function(){
  var doc = parent.document;
  ['suite-topbar','suite-nav'].forEach(function(id){ var e = doc.getElementById(id); if (e) e.remove(); });
})();
</script>
"""


def render_header(title: str, subtitle: str, badge: str = "", nav_links=None):
    """注入全宽固定顶栏（+可选导航栏）。每次调用替换上一份。"""
    html = _build_html(title, subtitle, badge, nav_links)
    components.html(_INJECT_JS.replace("__HTML__", json.dumps(html)), height=0)


def clear_header():
    """移除已注入的顶栏（无数据 / 占位场景用）。"""
    components.html(_CLEAR_JS, height=0)
