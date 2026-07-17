"""
shared/styles.py - 两模式共用 CSS + 模式专属 CSS 拼装

合并自 performance/styles.py 与 emergency/styles.py（90%+ 重复，差异仅
Performance 专属的 .section-header 与 Plan 列框）。

- _common_css_inner(): 顶栏/侧边栏/KPI/表格/导航/留白等共享部分
- _performance_css_inner(): .section-header + Plan 列框（仅 Performance）
- _emergency_css_inner(): 当前为空，预留扩展位
- get_css(mode): 返回完整 <style> 块（common + mode 专属）
"""
from shared.theme import (
    MCD_RED, MCD_GOLD,
    THEME_BG, THEME_PAPER, THEME_INK, THEME_INK2, THEME_LINE, THEME_ROW_ALT,
    THEME_HOVER, THEME_MUTED, THEME_TAG_BORDER,
    THEME_SHADOW_1, THEME_SHADOW_2, THEME_RADIUS_S, THEME_RADIUS_M,
)


def _common_css_inner() -> str:
    """两模式共享的 CSS 规则（不含 <style> 包裹）"""
    return f"""
  /* ─── 全局 ─── */
  html {{ scroll-behavior: smooth; }}
  html, body, .stApp {{
    font-family: 'Microsoft YaHei', 'PingFang SC', -apple-system, sans-serif !important;
    background: {THEME_BG};
    color: {THEME_INK};
    font-size: 14px;
    line-height: 1.6;
  }}

  /* ─── 侧边栏（与右边卡片风格统一：白底 + 灰边 + 顶部金线）─── */
  [data-testid="stSidebar"] {{
    background: #FFFFFF !important;
    border-right: 1px solid #e0e0e0;
    border-top: 3px solid {MCD_GOLD};
  }}
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] p {{
    color: {THEME_INK} !important;
    font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif !important;
    font-size: 13px;
  }}
  [data-testid="stSidebar"] .stRadio label,
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stTextInput label,
  [data-testid="stSidebar"] .stNumberInput label,
  [data-testid="stSidebar"] .stDateInput label {{
    color: {THEME_INK2} !important;
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.02em;
    margin-bottom: 4px;
  }}
  [data-testid="stSidebar"] hr {{
    border-color: {THEME_LINE} !important;
    margin: 16px 0;
  }}
  [data-testid="stSidebar"] .stSelectbox > div > div,
  [data-testid="stSidebar"] .stTextInput > div > div,
  [data-testid="stSidebar"] .stNumberInput > div > div,
  [data-testid="stSidebar"] .stDateInput > div > div,
  [data-testid="stSidebar"] .stFileUploader > div {{
    background: {THEME_PAPER} !important;
    border: 1.5px solid {THEME_TAG_BORDER} !important;
    border-radius: {THEME_RADIUS_S} !important;
    color: {THEME_INK} !important;
  }}
  [data-testid="stSidebar"] .stFileUploader {{
    border: 1.5px solid {THEME_TAG_BORDER} !important;
    border-radius: {THEME_RADIUS_S} !important;
    padding: 8px !important;
  }}

  /* ─── Sidebar multiselect ─── */
  [data-testid="stSidebar"] [data-baseweb="tag"] {{
    background-color: {THEME_HOVER} !important;
    border: 1px solid {MCD_RED}40 !important;
    border-radius: 4px !important;
    color: {MCD_RED} !important;
    font-size: 12px !important;
    font-weight: 500 !important;
  }}
  [data-testid="stSidebar"] [data-baseweb="tag"] span {{
    color: {MCD_RED} !important;
  }}
  [data-testid="stSidebar"] [data-baseweb="select"] {{
    border: 1px solid {THEME_TAG_BORDER} !important;
    border-radius: {THEME_RADIUS_S} !important;
  }}
  [data-testid="stSidebar"] [data-baseweb="select"]:focus-within {{
    border-color: {MCD_RED} !important;
    box-shadow: 0 0 0 1px {MCD_RED}40 !important;
  }}

  /* ─── Sidebar date input ─── */
  [data-testid="stSidebar"] [data-baseweb="input"] {{
    border: 1px solid {THEME_TAG_BORDER} !important;
    border-radius: {THEME_RADIUS_S} !important;
  }}
  [data-testid="stSidebar"] [data-baseweb="input"]:focus-within {{
    border-color: {MCD_RED} !important;
    box-shadow: 0 0 0 1px {MCD_RED}40 !important;
  }}

  /* ─── Section 副标题 / H3 子节标题：金色左竖条 + 灰字（参照 preview_v7，灰色非棕色）─── */
  .section-subheader {{
    font-size: 15px;
    font-weight: 800;
    color: {THEME_INK2};
    border-left: 4px solid {MCD_GOLD};
    padding-left: 11px;
    margin: 22px 0 10px 0;
    letter-spacing: 0.02em;
  }}

  /* ─── KPI Card（无左侧色条，与两模式扁平风格一致）─── */
  .kpi-card {{
    background: #FFFFFF;
    border: 1px solid #e0e0e0;
    border-radius: {THEME_RADIUS_M};
    padding: 16px;
    display: flex;
    flex-direction: column;
    box-shadow: {THEME_SHADOW_1};
    transition: box-shadow .15s;
  }}
  .kpi-card:hover {{
    box-shadow: {THEME_SHADOW_2};
  }}

  .kpi-label {{
    font-size: 12px;
    font-weight: 600;
    color: {THEME_MUTED};
    margin-bottom: 6px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }}
  .kpi-value {{
    font-size: 28px;
    font-weight: 800;
    color: {THEME_INK};
    letter-spacing: -0.02em;
    line-height: 1;
    margin-bottom: 4px;
    font-variant-numeric: tabular-nums;
  }}
  .kpi-sub {{
    font-size: 12px;
    color: {THEME_MUTED};
    font-variant-numeric: tabular-nums;
  }}
  .kpi-sub .up {{ color: #5a8a50; }}
  .kpi-sub .down {{ color: {MCD_RED}; }}

  /* ─── 表格 ─── */
  .dataframe {{
    font-size: 13px !important;
    font-variant-numeric: tabular-nums;
  }}
  .dataframe th {{
    font-weight: 700 !important;
    color: #fff !important;
    background: #1A1A1A !important;
    font-size: 12px !important;
    padding: 10px 12px !important;
  }}
  .dataframe td {{
    padding: 8px 12px !important;
    border-bottom: 1px solid {THEME_LINE} !important;
  }}
  .dataframe tr:nth-child(even) td {{
    background: {THEME_ROW_ALT} !important;
  }}

  /* ─── 锚点跳转偏移 ─── */
  [id^="sec-"] {{ scroll-margin-top: 98px; }}

  /* ─── 分隔线 ─── */
  .divider {{
    border: none;
    border-top: 1px solid {THEME_LINE};
    margin: 32px 0;
  }}

  /* ─── 顶部栏（全宽固定；layout 参照 preview_v7：徽章+标题+副标左 / logo 右）─── */
  .topbar {{
    background: #1A1A1A;
    border-bottom: 3px solid {MCD_GOLD};
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    padding: 14px 32px;
    box-shadow: 0 2px 12px rgba(0,0,0,.15);
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 100;
    min-height: 70px;
  }}
  .topbar-left, .topbar-right {{ display: contents; }}
  .header-left {{ flex: 1; min-width: 0; }}
  .header-right {{ flex-shrink: 0; }}
  .header-title {{
    font-size: 20px;
    font-weight: 800;
    color: #fff;
    letter-spacing: .3px;
    line-height: 1.2;
    margin: 0;
  }}
  .header-sub {{
    font-size: 11.5px;
    color: rgba(255,255,255,.65);
    margin-top: 2px;
  }}
  .header-logo {{
    width: 56px;
    height: 56px;
    display: block;
  }}
  .date-badge {{
    display: inline-block;
    background: #2e2e2e;
    color: #FFBC0D;
    border: 1px solid #444;
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 8px;
  }}

  /* ─── 导航栏（全宽固定）─── */
  .nav-bar {{
    position: fixed;
    top: 103px; left: 0; right: 0;
    z-index: 90;
    background: rgba(255,253,248,.96);
    backdrop-filter: blur(6px);
    border-bottom: 1px solid {THEME_LINE};
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    padding: 4px 20px;
  }}
  .nav-bar a.nav-link,
  .nav-bar a.nav-link:link,
  .nav-bar a.nav-link:visited,
  .nav-bar a.nav-link:active {{
    font-size: 12px !important;
    font-weight: 700 !important;
    color: {THEME_INK2} !important;
    background: transparent !important;
    padding: 3px 12px !important;
    border-radius: 16px !important;
    text-decoration: none !important;
    border-bottom: none !important;
    transition: background .15s, color .15s;
    white-space: nowrap;
  }}
  .nav-bar a.nav-link:hover {{
    background: {THEME_HOVER} !important;
    color: {MCD_RED} !important;
    text-decoration: none !important;
  }}

  /* ─── 顶部留白 = 固定 header 高度（topbar 100 + 金边 3 + nav 约 35 + 安全 6 = 144）─── */
  /* 底部留白 = footer 在文档流末尾，加 1rem 间距避免贴最后一行 ─ */
  .block-container,
  [data-testid="stMainBlockContainer"],
  [data-testid="stAppViewBlockContainer"] {{
    padding-top: 144px !important;
    padding-bottom: 1rem !important;
  }}
  [data-testid="stVerticalBlock"] > div {{ margin-bottom: 0 !important; }}
  [data-testid="stHorizontalBlock"] {{ gap: 0.4rem !important; }}

  /* ─── 隐藏侧边栏折叠按钮 ─── */
  [data-testid="stSidebarCollapseButton"],
  [data-testid="stSidebarCollapseButton"] button {{
    display: none !important;
  }}
  [data-testid="stSidebar"] {{
    min-width: 280px !important;
    max-width: 280px !important;
  }}

  /* ─── 调整 Streamlit 默认 header ─── */
  header[data-testid="stHeader"] {{
    background: transparent !important;
    box-shadow: none !important;
  }}
  header[data-testid="stHeader"] button[kind="header"] {{
    display: none !important;
  }}

  /* ─── 卡片删除按钮（小号低调）─── */
  .stButton button {{
    font-size: 12px !important;
    padding: 2px 12px !important;
    min-height: 28px !important;
    border-radius: {THEME_RADIUS_S} !important;
    font-weight: 500 !important;
    transition: all .15s !important;
  }}

  /* ─── 隐藏 Streamlit footer ─── */
  footer {{ visibility: hidden; }}
"""


def _performance_css_inner() -> str:
    """Performance 专属 CSS 规则：.section-header + Plan 列框（Emergency 不需要）"""
    return f"""
  /* ─── Section 大标题 H2：红色方块徽章 + 黑标题（参照 preview_v7）─── */
  .section-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 19px;
    font-weight: 800;
    color: {THEME_INK};
    margin: 24px 0 6px 0;
    letter-spacing: 0.3px;
  }}
  .section-header h2 {{
    font-size: inherit;
    font-weight: inherit;
    color: inherit;
    margin: 0;
  }}
  .section-header .sec-num {{
    display: flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: 9px;
    background: {MCD_RED};
    color: #fff;
    font-size: 15px;
    font-weight: 800;
    flex-shrink: 0;
  }}

  /* ─── Plan 列框（高分文案 / 需提升）：border 容器染成纸色，与 FRAME / HTML 导出端一致 ─── */
  [data-testid="stVerticalBlockBorderWrapper"] {{
    background: {THEME_PAPER};
    border: 1px solid {THEME_LINE} !important;
    border-radius: {THEME_RADIUS_M};
    padding: 12px !important;
  }}
"""


def _emergency_css_inner() -> str:
    """Emergency 专属 CSS 规则（当前为空，预留扩展位；section-header 走 inline 样式）"""
    return ""


def get_css(mode: str) -> str:
    """
    主入口：返回指定模式需要的完整 <style> 块（common + 模式专属）。

    Args:
        mode: 'performance' 或 'emergency'

    Returns:
        完整 CSS 字符串（含 <style> 包裹），可直接 st.markdown(..., unsafe_allow_html=True)
    """
    common = _common_css_inner()
    if mode == "performance":
        return f"<style>{common + _performance_css_inner()}</style>"
    elif mode == "emergency":
        return f"<style>{common + _emergency_css_inner()}</style>"
    else:
        raise ValueError(f"Unknown mode: {mode!r}, expected 'performance' or 'emergency'")
