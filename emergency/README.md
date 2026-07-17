# CNN Emergency Weekly · 交接说明

> 你昨天看到的样子就是这个文档诞生的原因。读完再上手。

---

## 1. 一句话定位

**看本周决定要不要补量** — 共用 `cnn0629.xlsx`，与 Performance Weekly 互补。

---

## 2. 启动

```bash
cd C:\Users\a952462\Desktop\cnn-emergency-weekly-main
streamlit run app.py
```

打开 http://localhost:8504，上传 `cnn0629.xlsx` 即可。

---

## 3. 文件结构（21 个文件）

```
app.py                       Streamlit 主入口
config.py                    颜色 token + 阈值 + 5 渠道配色
data.py                      从 Performance Weekly 复制（fuzzy 列名映射 + 多编码）
export.py                    自包含 HTML 导出（Plotly.js CDN + anime.js CDN）
styles.py                    暖色纸质 CSS（从 Performance 复制）

sections/
├── topbar.py                红渐变 + 金拱门 + 红灯 badge
├── section1_overview.py     总览：环 + 周进度 + Nudge
├── section2_dau.py          目标拆解：4 KPI + 每日柱状图
├── section3_aarr.py         AARR/Normal 堆积
└── section4_channels.py     5 渠道堆积

components/
├── ring.py                  单 iframe 渲染整张卡（card + canvas + anime.js）
├── kpi_card.py              扁平白底卡片（无左色条）
├── day_table.py             周一~周日表格（含达标 badge）
├── nudge_grid.py            Nudge 4 类拆解
├── alert_bar.py             绿/黄/红告警条（**当前未启用**）
└── fmt.py                   数字格式化 + status helper

mcdonalds.svg / favicon.png  复用 Performance 的资源
requirements.txt             streamlit / pandas / openpyxl / plotly
```

---

## 4. **重要设计决策**（明天可能想调整的）

### 4.1 Section 1 左 vs 右 数字不同（这是设计不是 bug）

| 位置 | 指标 | 数据源 | 说明 |
|------|------|--------|------|
| Section 1 左（环/KPI） | **DAU Actual（去重）** | Sheet 2 | 用户去重后的真实 DAU |
| Section 1 右（Nudge Operational） | **点击人次（日均）** | Sheet 1 | Plan-渠道累加，不去重 |

两数**会不同**，标签都标了：「Operational 点击人次 / 日均」「累计 XX,XXX」。**不要尝试对齐**。

### 4.2 Gap 阈值固定 10% / 20%（Sidebar 不可滑动了）

为了让侧边栏精简，阈值改成静态展示。要恢复可调，把 `app.py` 里的：

```python
st.markdown(
    f"<div style='...'>绿灯 ≤ {GREEN_GAP*100:.0f}% · 黄灯 ≤ ...</div>"
)
```

换成 `st.slider` 即可。

### 4.3 Nudge 4 类标签样式完全统一（仅颜色不同）

AARR `#DB0005` / 常规 `#A87B00` / On-demand + Responsive `#8a7e72`

### 4.4 三个柱状图固定 7 天 X 轴占位

少数据时未来天空着。X 轴从 `week_start`（用户选的周一）起 7 天。

### 4.5 三栏卡片统一高度 480px

环 / 周进度 / Nudge 全部 480px。日不会被截断了。

### 4.6 HTML 渲染统一用 `st.html()` 而非 `st.markdown(unsafe_allow_html=True)`

Streamlit 1.56 上后者会把长 HTML 当代码块渲染，前者不会。9 个文件全切了。

---

## 5. 当前任务清单（Status）

| # | 任务 | 状态 |
|---|------|------|
| 1-13 | 初版 13 个任务 | ✅ |
| 14-19 | 第一轮修复（去掉 emoji / favicon / 自动加载） | ✅ |
| 20-23 | 第二轮修复（emoji 全清 / KPI 卡片无色条） | ✅ |
| 24-28 | 第三轮（阈值锁定 / On-demand+Responsive 加回 / 数据口径对齐 / 告警条删除 / Section 1 等宽） | ✅ |
| 29-32 | 第四轮（DAU/点击人次分开 / Nudge 4 类统一 / 高度 380 → 480 / 删 ① ②） | ✅ |
| 33-35 | 第五轮（HTML 显示为代码诊断 / 环单 iframe 内嵌 / 删 ① 数字徽章） | ✅ |
| 36-39 | 第六轮（高度 480 / Section 2 改名 / 删副标题 / 日期默认本周一~本周日） | ✅ |
| 40 | 第七轮（柱状图固定 7 天 X 轴占位） | ✅ |

---

## 6. 明天想继续做的几个候选

### 6.1 测试新数据（不同日期范围、更长周期）

如果数据是「上周已结束」的状态，DAU Actual / Gap 数字有意义了；如果仍是「本周刚开始」，Target 虚线可能远高于柱高，UI 会显得很空。要不要给个 **Y 轴上限 = max(target, 实际峰值) × 1.15** 让柱图有画面感？

### 6.2 KPI 卡片精简

现在 KPI 卡片有 sub text（完成率、达标天数）。用户不一定需要，可以：

- 完全去掉 sub text（更简洁）
- 改成 1 行小字副文本，纯说明

### 6.3 增加 缓存

每次 sidebar 改动都触发 `_compute_weekly_metrics()` 重算。可以在 `app.py` 加 `@st.cache_data` 装饰该函数，按 `(df_hash, start, end, target)` 缓存。

### 6.4 增加 缺数据警告

当 `days_elapsed == 0` 时，环卡显示「暂无数据」而不是「0%」（虽然当前逻辑不会发生，但反脆弱）。

### 6.5 删除 `alert_bar.py`

已不再使用（告警条全删了）。可以删文件，或者保留作备用。

### 6.6 试用 Section 2 内嵌 gap 副信息

替代原来的「红灯告警 · ...」长文本，可以把 `gap_pct` / `need_daily` / `hit_days` 等关键数字放回 KPI 卡的 sub text 里（小字灰色）。

### 6.7 导出 HTML 同步新设计

导出走的还是老 `_render_section(num, title)` 会带 ① ②。是否需要同步更新？（其实我之前改过 export.py 调用的 `render_html`，需要再确认一次）。**明天先打开一个导出的 HTML 看一下就知道了。**

---

## 7. 容易踩的坑（明天记得）

1. **改完代码后 streamlit 热重载不生效** — 有时 streamlit 不重载，特别是 `components/ring.py` 这种嵌 iframe 的。**直接 Ctrl+C 重启 streamlit** 即可。

2. **环卡（iframe）不响应 st.markdown 包裹** — 必须在 `components/ring.py` 里把整个 card 嵌在 iframe 里，不能在外面包 markdown。这条已经改好了，记得不要回退。

3. **`st.html()` vs `st.markdown(unsafe_allow_html=True)`** — 前者永远是正确的选择，除非你专门想显示 markdown。

4. **Section 1 的 ring 用了 `card_height=480`** — 改高度时同步改 `components/ring.py` 的默认参数。

5. **导出 HTML 与 Streamlit 渲染是两个代码路径** — `render_html()` 函数在每个 section 的底部。要让两者同步，必须两边都改。

---

## 8. 数据库与口径备忘

`cnn0629.xlsx`：

| Sheet | 字段 | 用途 |
|-------|------|------|
| Sheet 1（Plan 级触达明细） | 发送日期 / 计划类型 / 渠道 / Plan ID / Plan名称 / 预算owner / 是否用券 / 预计触达 / 触达成功 / 点击人次 / 点击后下单人次 / 订单GC / 订单Sales / 消息标题 / 消息内容 | Nudge / 渠道图 / KPI |
| Sheet 2（按天去重 DAU） | 第 1 列 = 日期，第 2 列 = DAU | KPI / 环卡 |

**列名匹配走 fuzzy**（`data.py:_fuzzy_match_columns`）。改 EXCEL 列名不至于立即报错，但代码逻辑会失败。

---

## 9. 你明天回来第一件事

```bash
cd C:\Users\a952462\Desktop\cnn-emergency-weekly-main
streamlit run app.py
```

打开 http://localhost:8504，上传 `cnn0629.xlsx`，看页面是否如今天离开时一致。如果不一致，看 Streamlit 控制台报错再 debug。

— 交接完成，明天见 🎯
