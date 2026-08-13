"""
config.py - CNN Performance Weekly：Performance 模式专属配置
（品牌色 / 主题 tokens / 列名映射 / 数值列 / 编码 / 状态常量 见 shared.theme）
"""

from shared.theme import *  # noqa: F401,F403 — 复用共享设计系统与数据契约常量

# ─── 评分权重（综合评分体系）────────────────────────────────────
W_REACH = 0.30    # 触达规模
W_CTR = 0.40      # CTR
W_CVR = 0.30       # 下单转化率

# ─── CTR/CVR 渠道 Q3 阈值（来自历史数据统计）────────────────────
CTR_THRESHOLDS = {
    "APP Push": 0.24,
    "企微1v1": 1.62,
    "微信小程序订阅消息": 4.01,
    "短信": 0.46,
}
CVR_THRESHOLDS = {
    # 下单转化率口径（点击后下单人次 ÷ 点击人次 ×100），阈值取自 mcd-content-rank 校准
    "APP Push": 21.35,
    "企微1v1": 9.09,
    "微信小程序订阅消息": 26.81,
    "短信": 20.00,
}
CTR_UNKNOWN_THRESHOLD = 2.85
CVR_UNKNOWN_THRESHOLD = 20.31

# ─── 评分幂次 ──────────────────────────────────────────────
SCORING_EXP = 1.5

# ─── 置信度惩罚（触达规模）────────────────────────────────────
CONFIDENCE_THRESHOLDS = [
    (100, 0.1),
    (500, 0.3),
    (1000, 0.5),
    (5000, 0.8),
]
CONFIDENCE_DEFAULT = 1.0

# ─── 渠道列表 ──────────────────────────────────────────────
CHANNELS = ["APP Push", "企微1v1", "短信", "微信小程序订阅消息"]

# ─── API 配置（LLM 分析）──────────────────────────────────────
API_PROVIDERS = {
    "火山方舟": {
        "base_url": "https://ark.cn-beijing.volces.com/api/coding/v3",
        "models": ["minimax-m3"],
        "api_key": "k-897605b4-831b-494a-9e2e-d477d6b17158-fb2d1",
    },
    "百度千帆": {
        "base_url": "https://qianfan.baidubce.com/v2/coding",
        "models": ["qianfan-code-latest"],
        "api_key": "ce-v3/ALTAKSP-QmNPHghHzqzyoxZMVnzVo/c6b429d64ddc09c0c24d2c61a79ab30d1f1f5a55",
    },
    "麦当劳AI网关": {
        "base_url": "https://ai-gateway-test.mcdchina.net/v1",
        "models": ["gemini-3-flash-preview", "gemini-3-pro-image-preview", "deepseek-v3", "claude-sonnet-4.6", "claude-haiku-4.5"],
        "api_key": "",
    },
    "MiniMax": {
        "base_url": "https://api.minimaxi.com/anthropic",
        "models": ["MiniMax-M3"],
        "api_key": "",
    },
    "SiliconFlow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "models": ["deepseek-ai/DeepSeek-V3-0324", "Qwen/Qwen2.5-72B-Instruct"],
        "api_key": "",
    },
    "OpenAI": {
        "base_url": None,
        "models": ["gpt-4o-mini", "gpt-4o"],
        "api_key": "",
    },
}
