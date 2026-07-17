"""
sections/topbar.py - 顶部栏（黑底 + 金色 logo + 徽章/标题/副标左 / logo 右）
部门版权已挪到 render_footer_html()，由导出端在 </body> 前注入。
"""
import base64
from pathlib import Path

# 项目元信息（顶部栏固定文案）
PROJECT_NAME = "CNN Emergency"
PROJECT_SUB = "周度 DAU 应急观察"
DEPARTMENT = "McDonald's China · IT Operating · Traffic"


def _get_logo_data_url() -> str:
    """读取本地 mcdonalds.svg，编码为 data URL（原始 fill=#fc0 金色，不做白化反转）"""
    svg_path = Path(__file__).parent.parent.parent / "assets" / "mcdonalds.svg"
    try:
        svg_bytes = svg_path.read_bytes()
        b64 = base64.b64encode(svg_bytes).decode()
        return f"data:image/svg+xml;base64,{b64}"
    except Exception:
        return ""


_LOGO_DATA_URL = _get_logo_data_url()


def render_topbar_html(period_str: str = "") -> str:
    """导出用：返回纯 HTML（SVG 用 base64 inline）"""
    logo_html = (
        f'<img src="{_LOGO_DATA_URL}" class="header-logo" alt="McDonald\'s"/>'
        if _LOGO_DATA_URL else ""
    )

    date_badge = (
        f'<span class="date-badge">{period_str}</span>'
        if period_str else ""
    )

    return f"""
<div class="topbar">
  <div class="header-left">
    {date_badge}
    <h1 class="header-title">{PROJECT_NAME}</h1>
    <div class="header-sub">{PROJECT_SUB}</div>
  </div>
  <div class="header-right">
    {logo_html}
  </div>
</div>
"""


def render_footer_html() -> str:
    """导出用：返回页脚部门版权（深色条）"""
    return f'<div class="page-footer">{DEPARTMENT}</div>'
