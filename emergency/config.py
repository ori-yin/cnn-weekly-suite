"""
config.py - CNN Emergency Weekly：Emergency 模式专属配置（看 Gap）
（品牌色 / 主题 tokens / 列名映射 / 数值列 / 编码 / 状态常量 见 shared.theme）
"""

from shared.theme import *  # noqa: F401,F403 — 复用共享设计系统与数据契约常量
from shared.theme import THEME_BG, MCD_RED, MCD_GOLD, MCD_GREEN  # 显式引用，供下方使用

# ─── Emergency 业务阈值（Gap 判定）──────────────────────────────────
TARGET_DEFAULT_DAU = 50000   # 默认 Target 日均
GREEN_GAP = 0.10             # Gap ≤ 10% 绿灯
YELLOW_GAP = 0.20            # 10% < Gap ≤ 20% 黄灯
# Gap > 20% 红灯

# ─── 渠道（5 类，比 Performance 多 1 个 公众号）──────────────────
CHANNELS = ["APP Push", "企微1v1", "短信", "公众号", "微信小程序订阅消息"]
# 注意：CHANNELS 在 Section 4 渠道堆积图里**只显示**这 5 类；
# 实际数据中如出现其他渠道，会被归入空集合，DataFrame groupby 会自动忽略。

# ─── 渠道配色（5 类，左→红→金→绿→紫→深金）─────────────────────
CHANNEL_COLORS = {
    "APP Push":              MCD_RED,
    "企微1v1":                MCD_GOLD,
    "短信":                  MCD_GREEN,
    "公众号":                "#7B3FF2",
    "微信小程序订阅消息":     "#A87B00",
}
# 渠道柱内文字色（深色柱用白字，浅色柱用深色字）
CHANNEL_TEXT_COLOR = {
    "APP Push":              "#fff",
    "企微1v1":                "#5a1a00",
    "短信":                  "#fff",
    "公众号":                "#fff",
    "微信小程序订阅消息":     "#fff",
}

# ─── 计划类型（4 类）──────────────────────────────────────────────
PLAN_TYPES = ["AARRPlan", "常规Plan", "On-demand", "Responsive"]

# 计划类型配色：Operational 类（AARR/Normal）活跃，On-demand/Responsive 灰色
PLAN_TYPE_COLORS = {
    "AARRPlan":   MCD_RED,
    "常规Plan":    MCD_GOLD,
    "On-demand":  "#9AA0A6",
    "Responsive": "#9AA0A6",
}
# 是否「活跃」（有 Target）：只有 Operational 类
PLAN_TYPE_ACTIVE = {
    "AARRPlan": True,
    "常规Plan":  True,
    "On-demand": False,
    "Responsive": False,
}

# ─── Plotly 图表统一布局 ───────────────────────────────────────
PLOT_HEIGHT = 320
PLOT_BGCOLOR = THEME_BG
PLOT_PAPER_COLOR = THEME_BG
PLOT_GRID = "#E8E8E8"

PLOT_FONT = "Microsoft YaHei, PingFang SC, -apple-system, sans-serif"

PLOT_LAYOUT = dict(
    height=PLOT_HEIGHT,
    margin=dict(l=60, r=20, t=30, b=40),
    plot_bgcolor=PLOT_BGCOLOR,
    paper_bgcolor=PLOT_PAPER_COLOR,
    xaxis=dict(title="", gridcolor=PLOT_GRID, tickformat="%m/%d\n%a"),
    yaxis=dict(gridcolor=PLOT_GRID, tickformat=","),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
    font=dict(family=PLOT_FONT),
)
