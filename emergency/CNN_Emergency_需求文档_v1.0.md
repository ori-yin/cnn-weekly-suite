# CNN Emergency Weekly — 应急看板 开发需求文档

> 版本 v1.0 · 2026-06-30
> 需求方：Ori（Push 产品经理）
> 开发方：Claude Code

---

## 一、项目定位

### 1.1 是什么

CNN 周度 DAU 缺口应急看板。**核心问题只有一个**：本周 DAU 差多少？要不要补量？

### 1.2 与 Performance Weekly 的关系

两个看板共用同一个 Excel 数据源，作用不同：

```
Excel 上传 → Emergency（看 Gap，决定补不补）
           → Performance（复盘为什么好/差，沉淀方法论）
```

Emergency 更轻量——只有 4 个 Section，不展开 BU/Plan 深度分析。

### 1.3 技术栈

- **框架**：Streamlit（与 Performance 一致）
- **图表**：Plotly（Section 3/4 堆积柱状图）+ ECharts（Section 2 每日趋势，通过 `st.components.html` 嵌入）
- **环组件**：Canvas + anime.js（`st.components.html` 嵌入）
- **导出**：生成静态 HTML（含 Plotly.js CDN）
- **独立项目**：不合并到 Performance Weekly，减小代码量

---

## 二、数据输入

### 2.1 Excel 格式

与 Performance Weekly 用同一个 Excel，列结构完全一样：

| 列名 | 类型 | 说明 |
|------|------|------|
| 发送日期 | datetime | 日期 |
| 渠道 | string | APP Push / 企微1v1 / 短信 / 公众号 / 微信小程序订阅消息 |
| 计划类型 | string | AARRPlan / 常规Plan / On-demand / Responsive |
| Plan ID | string | 计划 ID |
| Plan名称 | string | 计划名称 |
| 预算owner | string | BU 名 |
| 触达成功 | int | 触达成功人次 |
| 点击人次 | int | DAU 核心指标 |
| 订单GC | int | 订单 GC |
| 订单Sales | float | 订单金额 |

### 2.2 时间范围

- **统计周期**：本周（周一~周日），进行中
- **数据天数**：可能只过了 2-5 天，后几天为空
- **日均口径**：Actual 日均 = 已有数据的累计值 / 已有数据天数，Target 是日均目标值
- 侧边栏可筛选周、日期范围

### 2.3 Sidebar 设置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| 上传 Excel | — | 文件上传 |
| 日期范围 | 本周一到周日 | 可手动调整 |
| Target 日均 | 50,000 | 可编辑，只影响 Operational |
| 绿灯阈值 | 10% | Gap ≤ 10% 绿灯 |
| 黄灯阈值 | 20% | 10% < Gap ≤ 20% 黄灯 |
| 红灯阈值 | >20% | Gap > 20% 红灯 |

---

## 三、页面结构

### 顶部栏

麦当劳红色渐变顶栏：
- 左侧：标题「CNN Emergency」+ 副标题（日期范围）
- 右侧：触发灯 badge（绿🟢/黄🟡/红🔴）

### Section 1：总览（环 + 天数 + Nudge Type）

#### 1a. 环组件

Canvas 圆环，动画展示完成进度：

```
      ┌──────────┐
      │   灰色底环  │  ← 未完成部分
      │  ┌────┐  │
      │  │35,000│  │  ← Actual 日均（最大字号，主数字）
      │  │Target │  │  ← Target 50,000（小字）
      │  │ 50k  │  │
      │  │70.0% │  │  ← 完成率（红色）
      │  └────┘  │
      │   红色弧   │  ← 已完成进度（70% = Actual/Target）
      └──────────┘
```

规则：
- 完成率 < 100%：灰色底环 + 红色已完成弧
- 完成率 = 100%：整圈红色
- 完成率 > 100%：整圈红色 + 超额部分金色弧

#### 1b. 天数表格

| 时期 | 说明 | 备注 |
|------|------|------|
| 周一 ~ 周日（7天） | 完整统计周期 | — |
| 已过 N 天 | 数据已出 | 🟢 正常 |
| 剩余 N 天 | 日均需 XX,XXX 补足 | 🟡/🔴 状态灯 |
| 达标天数 | M / N 天 | 列出具体哪天达标/未达标 |

- 达标判断：该日 DAU ≥ Target 即为达标
- 剩余日均补足 = (Target×7 - 累计Actual) / 剩余天数

#### 1c. Nudge Type 拆解

两列横排：

```
┌─────────────────────┬──────────────────────┐
│ Operational · 35,000 │ On-demand / Responsive │
│ ┌───────┬───────┐   │ On-demand    暂无数据  │
│ │ AARR  │Normal │   │ Responsive   暂无数据  │
│ │18,000 │17,000 │   │                      │
│ └───────┴───────┘   │ (灰色，半透明)         │
└─────────────────────┴──────────────────────┘
```

- Operational：左侧大列，内含 AARR / Normal 两个并排子格
- On-demand / Responsive：右侧大列，竖排两行，灰色半透明（暂无 Target）
- 暂无数据时显示"—"，不显示 0

### Section 2：DAU 概览（KPI Cards + 每日趋势）

#### 2a. KPI Cards

| 指标 | 说明 |
|------|------|
| DAU Target（日均） | 侧边栏设定值 |
| DAU Actual（日均） | 已有数据均值 |
| 触达成功（日均） | 日均触达量 |
| 订单Sales（日均） | 日均销售额 |

样式：白底卡片，左侧 3px 红色竖条，上标签下数字（Performance 同款）

#### 2b. 告警条

黄色背景条，位于 KPI Cards 和图表之间：

> ⚠ -30% 日均缺口 15,000，仅周一达标。剩余 4 天需日均 61,250 补足。

- 绿灯时显示绿色条（Gap 在可接受范围）
- 红灯时有具体数字和建议

#### 2c. 每日 DAU 趋势图

ECharts 柱状图：
- X 轴：周一~周日（7天全显示，后几天柱高为 0）
- Actual 柱：红色柱，顶部标注数值（仅 >0 时显示）
- Target 线：黑色虚线水平线，最后一根柱子右侧标注「Target 50,000」
- 已过天数有实际柱高，未来天数为空

### Section 3：AARR / Normal 拆解

Plotly 堆积柱状图：
- X 轴：周一~周日
- AARR 柱（红色堆在底部）：数值标注在柱内（白色字）
- Normal 柱（金色堆在顶部）：数值标注在柱内（深色字）
- Target 虚线：黑色水平线
- 图例：底部横排

### Section 4：渠道 DAU

Plotly 堆积柱状图：
- X 轴：周一~周日
- 5 个渠道堆叠：APP Push（红）、企微1v1（金）、短信（绿）、公众号（紫）、小程序订阅（深金）
- 柱内标注（≥500 时显示）
- 图例：底部横排

---

## 四、颜色规范

与 Performance Weekly 保持一致：

| Token | 色值 | 用途 |
|-------|------|------|
| MCD_RED | #DB0007 | 主色、红灯、APP Push |
| MCD_DARK | #a8001a | 表头、深红 |
| MCD_GOLD | #FFBC0D | 金色、Normal、企微 |
| GREEN | #1f883d | 绿灯、达成 |
| YELLOW | #e6a817 | 黄灯、预警 |
| bg | #f4efe6 | 页面底色 |
| paper | #fffdf8 | 卡片底色 |

---

## 五、导出功能

- 按钮：「📥 下载静态报告」
- 导出为自包含 HTML 文件（含 Plotly.js CDN、ECharts CDN）
- 包含全部 4 个 Section
- 带顶部导航栏
- 文件名：`cnn_emergency_YYYY-MM-DD.html`

---

## 六、交互细节

1. **环动画**：页面首次加载时，环从 0% 动画到实际完成率（1.8s easeOutExpo）
2. **卡片入场**：各 Section 从下往上淡入（stagger 120ms）
3. **侧边栏**：上传 Excel 后实时更新所有图表
4. **KPI Cards**：完成率 ≥90% 绿条，80-90% 黄条，<80% 红条
5. **On-demand/Responsive**：始终灰色半透明，无 Target 时数值显示"—"
6. **达标天数**：自动计算每天是否达标，红/绿 badge 标记

---

## 七、参考文件

- Performance Weekly GitHub：`ori-yin/cnn-performance-weekly`（组件可复用：`components.py`、`config.py`、`styles.py`、`export.py`）
- 原始需求框架：`CNN/cnn_emergency_weekly_v0.1.md`
- v5 视觉 Demo：`/tmp/emergency_gap_v5.html`（最终确认版）
- 数据源示例：`CNN/CNN分析_原始数据.xlsx`

---

## 八、注意事项

1. Operational 拆 AARR + Normal，**不是** Campaign（领导纠正过）
2. On-demand / Responsive 前期先空着，预留结构即可
3. 项目独立部署，不要合并到 Performance Weekly 仓库
4. 4 个 Section 标题用 Emergency 风格（「DAU 概览」「AARR / Normal 拆解」「渠道 DAU」），不照搬 Performance 的命名
5. 环内数字顺序：Actual 主 → Target 副 → 完成率底部

---

*文档结束。如有疑问联系 Ori。*
