# CNN Weekly Suite

把 **CNN Performance Weekly**（周度复盘）和 **CNN Emergency Weekly**（应急补量）合并成的单一 Streamlit 工具。上传一次数据，侧边栏切换两个视角，各自导出独立 HTML 看板。

## 快速开始

```bash
# Windows 一键
setup_and_run.bat

# 或手动
pip install -r requirements.txt
streamlit run app.py --server.port 8505
```

浏览器打开 http://localhost:8505 ，左侧上传 `cnn0629.xlsx`。

> 端口 8505，与两个老项目（8503/8504）互不冲突，可并存运行。

## 两个视角

| 视角 | 对应老项目 | 内容 |
|---|---|---|
| **周度复盘** | Performance Weekly | 4 个 Tab：Executive Summary / Operational / BU / Plan，含综合评分算法 + LLM AI 解读 |
| **应急补量** | Emergency Weekly | 4 个 Section：环图 Gap / DAU 拆解 / AARR / 渠道，看 Gap 决定要不要补量 |

侧边栏「视角」单选切换。**上传一次数据两视角共用**，切换时无需重传。各视角侧边栏底部有各自的「下载 HTML」按钮，导出两份独立报告。

## 数据契约

沿用老项目：上传 `.xlsx / .xls / .csv`。
- **Sheet 1** — Plan 级触达明细（发送日期 / 计划类型 / 渠道 / Plan ID / 预算owner / 触达成功 / 点击人次 / 订单GC / 订单Sales / 消息标题 / 消息内容 …）
- **Sheet 2** — 按天去重 DAU（第 1 列日期、第 2 列 DAU，按位置读取）

列名走 fuzzy 匹配（见 `shared/theme.py::COLUMN_MAPPING`），CSV 多编码兜底。

## 目录结构

```
cnn-weekly-suite/
├── app.py                # 唯一入口：set_page_config + 模式切换 + 统一上传
├── shared/               # 两模式共用底层
│   ├── theme.py          # 品牌色 / THEME_* tokens / COLUMN_MAPPING / ENCODINGS
│   └── data.py           # 数据读取 + 清洗（fuzzy 列名 + 多编码 + 衍生指标）
├── performance/          # 周度复盘（config/scoring/llm_service/components/styles/export/tabs + page.py）
├── emergency/            # 应急补量（config/styles/export/components/sections + page.py）
└── assets/               # mcdonalds.svg / favicon.png
```

- 各模式的 `config.py` 顶部 `from shared.theme import *`，只保留自己专属常量（评分权重 / API_PROVIDERS ；Gap 阈值 / CHANNEL_COLORS / PLAN_TYPES 等）。
- 两模式渠道数不同（Performance 4 个、Emergency 5 个含公众号），各自保留互不影响。

## 与老项目的关系

本工具是**副本合并**，两个老项目目录 `cnn-performance-weekly-main` / `cnn-emergency-weekly-main` 未做任何改动，仍可独立运行。
