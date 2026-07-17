# CNN Performance Weekly — 产品需求文档 (PRD)

> **版本**：v0.1
> **创建日期**：2026-06-23
> **作者**：Ori
> **目标读者**：Estella Zhu + 各 BU 负责人

---

## 1. 项目概述

**项目名称**：CNN Performance Weekly
**定位**：周度数据复盘看板，用于回顾上一周 CNN Push 触达数据表现，定位问题，沉淀 Good/Bad Case。
**技术栈**：Streamlit + pandas + Plotly
**部署方式**：本地运行（后续可部署 Streamlit Cloud）

---

## 2. 核心需求

### 2.1 数据输入

| 项目 | 说明 |
|---|---|
| 数据文件 | 用户上传 Excel（.xlsx）或 CSV（.csv） |
| 文件内容 | Plan 级触达数据（每行 = 一个 Plan 一天的数据） |
| Target | 用户在 Sidebar 手动输入一个全局日均 DAU Target（整数） |
| 编码支持 | UTF-8、GBK、GB2312、Latin-1（参考 mcd-content-rank） |
| 列名映射 | Fuzzy match，中英文列名自动映射到标准字段 |

**标准字段映射**：

| 标准字段名 | 可能的列名 | 类型 |
|---|---|---|
| 发送日期 | 发送日期、日期、date、send_date | datetime |
| 计划类型 | 计划类型、plan_type | str（AARRPlan / 常规Plan） |
| 渠道 | 渠道、channel | str |
| Plan ID | Plan ID、plan_id | str |
| Plan名称 | Plan名称、plan_name | str |
| 预算owner | 预算owner、owner、BU | str |
| 是否用券 | 是否用券、coupon | str（是/否） |
| 预计触达 | 预计触达、expected_reach | int |
| 触达成功 | 触达成功、reach、触达 | int |
| 点击人次 | 点击人次、clicks、点击 | int |
| 点击后下单人次 | 点击后下单人次、orders | int |
| 订单GC | 订单GC、GC | int |
| 订单Sales | 订单Sales、Sales、sales | float |

### 2.2 衍生指标

| 指标 | 计算公式 | 说明 |
|---|---|---|
| CTR | 点击人次 / 触达成功 × 100% | 点击率 |
| GC 转化率 | 订单GC / 点击人次 × 100% | 点击→下单转化率 |
| 触达率 | 触达成功 / 预计触达 × 100% | 触达完成率 |
| DAU（日） | 当天所有 Plan 的「点击人次」之和 | 日活口径 |
| DAU 达成率 | DAU / Target × 100% | 日完成率 |
| 周完成天数 | DAU ≥ Target 的天数 / 7 | X/7 天完成 |

---

## 3. 页面框架（4 层）

### 第一层：Executive Summary（一屏看完）

**核心问题**：本周 DAU 完成情况如何？

#### 3.1.1 KPI Cards

| Card | 内容 |
|---|---|
| Weekly DAU Target | 用户输入的日均 Target |
| Weekly DAU Actual | 本周日均 DAU（点击人次总和 / 7） |
| 达成率 | Actual / Target × 100% |
| 完成天数 | X/7 天 DAU ≥ Target |
| 周环比 | vs 上一周（如有历史数据） |

#### 3.1.2 每日 DAU 趋势图

- **图表类型**：折线图
- **X 轴**：日期（周一~周日）
- **Y 轴**：DAU（点击人次）
- **Target 线**：水平虚线，值 = 用户输入的 Target
- **完成标记**：DAU ≥ Target 的点标绿，< Target 的点标红

#### 3.1.3 Nudge Type 每日拆分

- Nudge Type = **Operational** / On-demand / Responsive
- On-demand / Responsive 暂不纳入（无数据），后续有数据再加
- 仅展示 Operational 的每日 DAU 折线

---

### 第二层：Operational 分析（计划类型 × 渠道）

**核心问题**：哪类计划、哪个渠道拖后腿？

> Operational 按 `计划类型` 拆分为 **AARR** 和 **常规** 两个子分类，每个子分类下再按渠道展开。
> 展示方式：默认显示 AARR / 常规 的汇总行，**点击可折叠展开**查看分渠道明细。

#### 3.2.1 AARR 汇总（点击展开）

**汇总行**：

| 计划类型 | 触达成功 | 点击人次 | CTR | 订单GC | GC转化率 | 状态 |
|---|---|---|---|---|---|---|
| ▶ AARR | XX | XX | XX% | XX | XX% | 绿/黄/红 |

**展开后渠道明细**：

| 渠道 | 触达成功 | 点击人次 | CTR | 订单GC | GC转化率 | 状态 |
|---|---|---|---|---|---|---|
| APP Push | XX | XX | XX% | XX | XX% | 绿/黄/红 |
| 企微1v1 | XX | XX | XX% | XX | XX% | 绿/黄/红 |
| 短信 | XX | XX | XX% | XX | XX% | 绿/黄/红 |
| 微信小程序订阅 | XX | XX | XX% | XX | XX% | 绿/黄/红 |

#### 3.2.2 常规 汇总（点击展开）

结构同上，按渠道展开。

#### 3.2.3 未完成天数高亮

- DAU < Target 的天数，在对应行标红/标黄
- 可展开查看具体哪些天未完成

---

### 第三层：BU 分析

**核心问题**：哪个 BU 贡献最大 / 拖后腿？

#### 3.3.1 BU 总览表

| BU（预算owner） | Plan 数 | 触达成功 | 点击人次 | CTR | 订单GC | GC转化率 | 状态 |
|---|---|---|---|---|---|---|---|
| BF | XX | XX | XX% | XX | XX% | XX% | 绿/黄/红 |
| MDS | XX | XX | XX% | XX | XX% | XX% | 绿/黄/红 |
| McCafe | XX | XX | XX% | XX | XX% | XX% | 绿/黄/红 |
| ... | ... | ... | ... | ... | ... | ... | ... |

#### 3.3.2 BU 详细分析（选 Top + Bottom 展开）

- 按综合评分选出 Top 2 / Bottom 2 BU
- 展开显示该 BU 的渠道分布、Plan 数量、主要贡献 Plan

---

### 第四层：内容分析（分渠道 Good/Bad Case）

**核心问题**：每个渠道哪些 Plan 表现好/差？可复用什么？优化什么？

> 按渠道分组，每个渠道展示 **Top 3**（综合评分最高）和 **Bottom 3**（综合评分最低）。

#### 3.4.1 综合评分体系

| 评分维度 | 权重 | 计算口径 |
|---|---|---|
| 触达规模得分 | 30% | 触达成功 / 目标（或分位数） |
| CTR 得分 | 40% | CTR / 渠道 Q3 阈值（参考 mcd-content-rank） |
| GC 转化率得分 | 30% | GC率 / 渠道 Q3 阈值 |
| **综合评分** | **100%** | 加权求和（0–100），含置信度惩罚 |

> 置信度惩罚：触达 < 100 → ×0.1，< 500 → ×0.3，< 1000 → ×0.5，< 5000 → ×0.8，≥ 5000 → ×1.0

#### 3.4.2 每个渠道 Top 3 Good Case

以 APP Push 为例（其他渠道结构相同）：

**APP Push — Top 3**

| 排名 | Plan ID | 文案 | BU | 触达 | CTR | GC率 | 综合评分 | 可复用点 |
|---|---|---|---|---|---|---|---|---|
| 1 | ... | ... | ... | ... | ... | ... | ... | ... |
| 2 | ... | ... | ... | ... | ... | ... | ... | ... |
| 3 | ... | ... | ... | ... | ... | ... | ... | ... |

#### 3.4.3 每个渠道 Bottom 3 Bad Case

**APP Push — Bottom 3**

| 排名 | Plan ID | 文案 | BU | 触达 | CTR | GC率 | 综合评分 | 优化方向 |
|---|---|---|---|---|---|---|---|---|
| 1 | ... | ... | ... | ... | ... | ... | ... | ... |
| 2 | ... | ... | ... | ... | ... | ... | ... | ... |
| 3 | ... | ... | ... | ... | ... | ... | ... | ... |

> 企微1v1、短信、微信小程序订阅 结构相同，各自独立展示 Top 3 / Bottom 3。

---

## 4. 技术方案

### 4.1 项目结构

```
cnn-performance-weekly/
├── app.py                  # Streamlit 主入口
├── config.py               # 全局配置（品牌色、阈值、列名映射）
├── data.py                 # 数据读取（fuzzy mapping、多编码支持）
├── scoring.py              # 综合评分算法
├── components.py           # 可复用 UI 组件（KPI Card、进度条等）
├── styles.py               # CSS 样式
├── tabs/
│   ├── __init__.py
│   ├── tab_summary.py      # 第一层：Executive Summary
│   ├── tab_operational.py  # 第二层：Operational 分析
│   ├── tab_bu.py           # 第三层：BU 分析
│   └── tab_plan.py         # 第四层：内容分析
├── requirements.txt
├── PRD.md
└── README.md
```

### 4.2 数据读取方案

参考 mcd-content-rank 的 `data_cleaning.py`：
- 支持 CSV / XLSX 两种格式
- 多编码尝试（UTF-8 → UTF-8-sig → GBK → GB2312 → Latin-1）
- Fuzzy column name mapping
- 数值列自动转换
- XLSX 用 openpyxl 保证 emoji 完整

### 4.3 评分算法

参考 mcd-content-rank 的 `scoring.py`：
- CTR/GC 使用分段函数（Q3 阈值以下幂次归一化，以上满分）
- 置信度惩罚基于触达规模
- 综合评分 = 触达规模×30% + CTR×40% + GC率×30%

### 4.4 UI 风格

- 品牌色：麦当劳红 `#DB0005`、金 `#FFBC0D`、绿 `#00A04A`
- 参考 mcd-reach-trend 的 KPI Card 组件（HTML 注入方式）
- 状态指示：绿（达成）/ 黄（落后 5-15%）/ 红（落后 15%+）

---

## 5. 开发计划

| 阶段 | 内容 | 优先级 |
|---|---|---|
| P0 | 数据读取 + Sidebar（文件上传 + Target 输入） | 高 |
| P1 | 第一层：KPI Cards + 每日趋势图 + Nudge Type 拆分 | 高 |
| P2 | 第二层：AARR/常规 × 渠道分析 | 高 |
| P3 | 第三层：BU 分析 | 中 |
| P4 | 第四层：Plan 综合评分 + Good/Bad Case | 中 |
| P5 | 样式优化 + README | 低 |

---

## 6. 决策记录

| 决策点 | 决策 | 决策人 | 时间 |
|---|---|---|---|
| DAU 口径 | 点击人次（不去重） | Ori 确认 | 2026-06-23 |
| Target 输入方式 | Sidebar 手动输入全局日均值 | Ori + Estella | 2026-06-23 |
| On-demand/Responsive | 暂不纳入（无数据） | Ori | 2026-06-23 |
| Nudge Type 定义 | Nudge Type = Operational/On-demand/Responsive；AARR/常规是计划类型子分类 | Ori 纠正 | 2026-06-23 |
| 渠道维度 | 作为第二层的子维度（AARR/常规点击展开看渠道） | Ori | 2026-06-23 |
| Plan 展示方式 | 每个渠道 Top 3 + Bottom 3（非全局 Top/Bottom 5） | Ori | 2026-06-23 |
| BU 维度 | 不拆 AARR/常规，看整体 | Ori | 2026-06-23 |
| 评分体系 | 综合评分（参考 mcd-content-rank） | Ori | 2026-06-23 |
