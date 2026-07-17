"""
shared/theme.py - 两模式共用的设计系统与数据契约常量
（抽自 performance/config.py 与 emergency/config.py 完全相同的部分）
"""

# ─── 品牌色（红/金/绿/黄，McDonald's）─────────────────────────────
MCD_RED = "#DB0005"          # 品牌红（McDonald's 官方）：CTA、警示、APP Push
MCD_DARK_RED = "#1A1A1A"     # 标题/表头：黑（替代旧 #a8001a 暗红）
MCD_GOLD = "#FFBC0D"         # 品牌金（McDonald's 官方）：强调、企微
MCD_GREEN = "#00A04A"        # 达标

# ─── 极简调色板（暖色→冷/中性）───────────────────────────────────
THEME_BG = "#F0F0F0"         # 页面背景
THEME_PAPER = "#FFFFFF"      # 卡片/表格主行背景
THEME_INK = "#1A1A1A"        # 主文字（黑）
THEME_INK2 = "#6B6B6B"       # 副文字（中深灰）
THEME_LINE = "#E0E0E0"       # 边框线（冷灰）
THEME_ROW_ALT = "#F5F5F5"    # 交替行背景（浅灰）

# ─── 设计系统 tokens ───────────────────────────────────────────────
THEME_HOVER = "#F5F5F5"      # hover 态背景（冷灰，替代旧 #fde9ea 粉）
THEME_MUTED = "#888888"      # 弱化文字（冷中灰，替代旧 #8a7e72 暖灰）
THEME_TAG_BG = "#F5F5F5"     # 药丸/标签背景（替代旧 #F8F7F5）
THEME_TAG_BORDER = "#E0E0E0" # 标签边框（替代旧 #e8e0d4）
THEME_SHADOW_1 = "0 1px 3px rgba(120,90,30,.06)"   # 卡片
THEME_SHADOW_2 = "0 2px 8px rgba(120,90,30,.10)"   # 悬浮/弹出
THEME_RADIUS_S = "6px"       # 小圆角（标签、按钮）
THEME_RADIUS_M = "10px"      # 中圆角（卡片）

# ─── 列名映射（Fuzzy match）──────────────────────────────────────
# key = 标准字段名, value = 可能出现的列名关键词列表
COLUMN_MAPPING = {
    "发送日期": ["发送日期", "日期", "date", "send_date", "send"],
    "计划类型": ["计划类型", "plan_type", "nudge", "类型"],
    "渠道": ["渠道", "channel"],
    "Plan ID": ["Plan ID", "plan_id", "planid"],
    "Plan名称": ["Plan名称", "plan_name", "planname", "名称"],
    "预算owner": ["预算owner", "owner", "BU", "bu", "预算"],
    "是否用券": ["是否用券", "coupon", "用券"],
    "预计触达": ["预计触达", "expected_reach", "expected", "预计"],
    "触达成功": ["触达成功", "reach", "触达"],
    "点击人次": ["点击人次", "clicks", "点击"],
    "点击后下单人次": ["点击后下单人次", "orders", "下单人次"],
    "订单GC": ["订单GC", "GC", "gc"],
    "订单Sales": ["订单Sales", "Sales", "sales", "订单sales"],
    "消息标题": ["消息标题", "title", "标题"],
    "消息内容": ["消息内容", "content", "内容", "text"],
}

# ─── 数值列 ──────────────────────────────────────────────────
NUMERIC_COLS = [
    "预计触达", "触达成功", "点击人次", "点击后下单人次", "订单GC", "订单Sales"
]

# ─── 编码尝试顺序 ──────────────────────────────────────────────
ENCODINGS = ["utf-8", "utf-8-sig", "gbk", "gb2312", "latin1"]
