# CNN Performance Weekly

CNN Push 触达数据周度复盘看板。

## 功能

- **Executive Summary**：KPI Cards + 每日 DAU 趋势图 + Nudge Type 拆分
- **Operational 分析**：AARR / 常规 × 渠道，折叠展开
- **BU 分析**：按预算 owner 聚合
- **内容分析**：每个渠道 Top 3 / Bottom 3（按综合评分）

## 运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动
streamlit run app.py
```

## 数据格式

上传 CSV 或 XLSX 文件，需包含以下字段：

| 字段 | 说明 |
|---|---|
| 发送日期 | 日期 |
| 计划类型 | AARRPlan / 常规Plan |
| 渠道 | APP Push / 企微1v1 / 短信 / 微信小程序订阅消息 |
| Plan ID | 计划唯一标识 |
| Plan名称 | 计划名称 |
| 预算owner | BU 名称 |
| 触达成功 | 触达人数 |
| 点击人次 | 点击人数 |
| 订单GC | 下单数 |

### 数据源升级：2026-07-28 起新增 2 列

| 字段 | 说明 |
|---|---|
| Unit ID | 千人千面分组（缺失填 `[NULL]`），业务等同空值 |
| Message ID | 文案唯一标识（18 位数字），与 Plan ID 配合定位内容卡片 |

列名支持模糊匹配（中英文均可）。

### 卡片粒度（一张卡片 = Plan × Message）

- 一 Plan 一文案 → 1 张卡
- 一 Plan 多 Unit 同文案（千人千面）→ 1 张卡，副标 `N组 Unit`
- 一 Plan 多文案（实验/分时）→ 每条文案各 1 张卡

Unit 不参与内容排行榜聚合（Unit 间 CTR 差异来自人群/落地页不是文案差异，合并避免污染排行）。

旧数据（无 Message ID）自动退化按 Plan 聚合，向后兼容。

## 技术栈

- Streamlit
- pandas + Plotly
- 品牌色：麦当劳红 #DB0005 / 金 #FFBC0D / 绿 #00A04A
