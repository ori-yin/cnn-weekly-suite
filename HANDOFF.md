# CNN Weekly Suite - 交接文档（HANDOFF）

> 新 session 从这里接手。本文件只保留**长期有效**的信息：怎么跑、代码约定、口径定义、已知坑。
> 历史变更流水由 `git log` 承载，不要在本文件堆会话记录。改坏了 `git checkout -- .` 回退。

**项目路径**：`C:\ideon\cnn-weekly-suite`（VM 同步副本，git remote = GitHub `ori-yin/cnn-weekly-suite`）

---

## 1. 这是什么

单应用双模式的 Streamlit 看板。侧边栏 `View` 切 **Performance**（周度复盘：评分 + LLM AI 解读，5 Tab）/ **Emergency**（应急补量：看 DAU Gap 决定补量，4 Section）。**上传一次 xlsx 两模式共用**，各自独立导出 HTML。

数据契约：同一个 xlsx 两张 sheet
- **Sheet 1** = Plan 明细（必需：`发送日期` / `触达成功` / `点击人次`）
- **Sheet 2** = 按天去重 DAU（2 列 `日期,DAU` 或 3 列 `日期,渠道,DAU`，3 列时只取 `渠道=ALL/all`）

两个口径**本就不同，不要"对齐"**：Emergency 概览的 Actual 是 Sheet 2 去重 DAU；Nudge 拆解里的 Operational 是 Sheet 1 点击人次（不去重）。

---

## 2. 怎么跑

```
cd C:\ideon\cnn-weekly-suite
setup_and_run.bat          # 或： streamlit run app.py --server.port 8505
```
浏览器开 http://localhost:8505 。端口 8505，与老项目 8503/8504 不冲突。

`setup_and_run.bat` 必须**纯 ASCII**（中文注释在 cmd/GBK 下会乱码报错）。

---

## 3. 目录结构

```
cnn-weekly-suite/
├── app.py                # 唯一入口：set_page_config(仅此一次) + View 切换 + 统一上传 + 分派
├── shared/               # 两模式公共层
│   ├── theme.py          # 品牌色 / THEME_* / COLUMN_MAPPING / NUMERIC_COLS / ENCODINGS
│   ├── data.py           # 读取清洗（fuzzy 列名 + 多编码 + ID 保护 + 衍生指标）
│   ├── header.py         # 全宽固定顶栏（JS 注入 parent.body）
│   ├── footer.py         # 页面底部部门版权条（JS 注入，position: relative 在文档流末尾）
│   └── styles.py         # get_css(mode) -> _common / _performance / _emergency
├── performance/          # 周度复盘模式
│   ├── page.py           # render_page(raw_df, dau_df)
│   ├── config.py scoring.py llm_service.py components.py export.py channel_health.py
│   └── tabs/ tab_summary / tab_operational / tab_bu / tab_plan / tab_topics
└── emergency/            # 应急补量模式
    ├── page.py           # render_page(raw_df, dau_df)，nav 只 2 项（只 H2，不要 H3）
    ├── config.py export.py
    ├── components/ ring / kpi_card / day_table / nudge_grid / fmt
    └── sections/ section1_overview / section2_dau / section3_aarr / section4_channels / topbar
```

---

## 4. 关键约定（改代码前必读）

- **子包导入必须带前缀**：`from performance.xxx` / `from emergency.xxx` / `from shared.xxx`。不要写裸 `from config import`（会撞车）。
- **`st.set_page_config` 只能在 `app.py` 调一次**，两个 page.py 里都不能有。
- **两模式 CHANNELS 不同**（Performance 4 个、Emergency 5 个含"公众号"），各自 config 保留，别强行统一。
- **主题/列名/编码等公共常量**统一在 `shared/theme.py`。
- 数据在 `app.py` 用 `@st.cache_data` 按文件内容缓存，切模式不重复解析。
- **顶栏和页脚都用 JS 注入**（`shared/header.py` / `shared/footer.py`），不要在 page.py 里用 `st.markdown` / `st.html` 直接渲染。
- **渲染逻辑要复用于导出**。页面和 export 共用同一个 render 函数，导出才不会出现"页面改了、导出没改"。
- **`st.data_editor` 的 `key` 必须带区间标识**，否则切换日期后残留上一区间的行。

---

## 5. 日期区间口径（两模式共用 `filter_week_data`）

两个 page 的侧边栏都有 `开始日期` / `结束日期`，默认值不同：
- **Performance 默认上一个自然周**（周一~周日）
- **Emergency 默认本周**，与数据范围取交集

`shared/data.py::filter_week_data(df, start, end)` 按任意区间筛选，**不校验周一/周日**——所以两个模式都支持非自然周临时报告。

### 5.1 Emergency：区间天数必须显式传下去（2026-10-12 修复）

历史设计错误：区间已参数化，但下游把 7 天当常量写死，导致非自然周报表**数字出错**。现在 `days_total = (end_date - start_date).days + 1`，并贯穿天数表 / 3 张图 / 导出 / 备注初始化。

新增约定：**任何按天循环或按天取目标的地方，都用 `days_total`，不许写 `7`**
- `day_table.py`：星期标签按真实日期取 `days_zh[d.weekday()]`，**不要用位置** `days_zh[i]`
- 补量口径 `(target * days_total - 已过实际) / remaining`
- 3 张图的 `days_total` 默认参数保留 7，但调用方必须显式传
- 非自然周时 topbar/页头副标题改「区间 DAU 应急观察」，避免被误读为周度

### 5.2 Performance：非自然周可直接用，但有两点要知道

Performance 对外指标**几乎全是日均**（`total / days_count`，见 `tab_summary.py` / `tab_operational.py` / `tab_bu.py`），日均对区间长度不敏感，所以**非自然周直接出报告即可，无需改代码**。但：
1. **文案写死「本周/周度」**（顶栏、`export.py` 页头、`tab_topics` 默认标题）。数字对，但业务方会以为是自然周——发出去时口头带一句区间。
2. **环比是「往前挪 7 天」**（`page.py` 的 `prior_start = start - 7d`），不是等长前窗。5 天窗口会比 `[start-5d, start-1d]`，中间空 2 天。对日均和 CTR 是合理对比，不是错数。

### 5.3 已结束的临时窗口

Emergency 的「剩余 N 天需日均补 X」语义上只对**进行中**的窗口成立。已结束的窗口 `remaining = 0`、`need_daily = 0`，属于如实反映，不是 bug。

---

## 6. 数据层约定

### 6.1 Unit ID / Message ID 业务语义（上游 15 列 -> 17 列）

Plan 不再是「一 Plan 一文案」，可能拆多 Unit + 多文案（千人千面 / 实验分时）。

**一张内容排行榜卡片 = `Plan x Message`**（Unit 不参与）
- 一 Plan 一文案 -> 1 张卡
- 一 Plan 多 Unit 同文案 -> 1 张卡（副标 `N组 Unit`，合并千人千面）
- 一 Plan 多文案 -> 每条文案各 1 张卡

Unit = **千人千面**分组，Unit 间 CTR 差异来自人群/落地页**不是文案差异**。
Message ID 18 位数字超过 float64 精度 2^53，**必须字符串化**（`ID_COLS` 保护）。
聚合要**先求和再算率**（CTR / 下单转化率），不要按行先算率再平均。

向后兼容：旧数据无 Message ID 时 `data_is_v2()` 判定为 False，按 Plan 退化聚合。

### 6.2 业务过滤规则（不要删）

- **IT-Traffic 是裁判部门**：只在 **BU 总览表 + 详情浮层**隐藏（`tab_bu.py::_HIDDEN_BUS`），**排行榜照常展示**；BU AI 解读也不解读它（`page.py`）。
- **计划分析 / AI 解读只跑 2 个渠道**：`PLAN_CHANNELS` / `AI_CHANNELS` = APP Push + 企1v1，短信和微信小程序不进 AI 循环（`tab_plan.py`）。

### 6.3 ⚠️ 已知隐患：`shared/data.py::_coerce_numeric_columns`

该函数在 `_parse_dates` **之前**把所有非 ID 列强转 `float64`。如果 Excel 里的「发送日期」存成**日期格式**而非文本，会被当 epoch 数字解析成 `1970-01-21`，全盘数据错乱且**不报错**。

现状：线上文件存的是文本日期，所以一直正常。修法是在该函数里跳过 datetime dtype。**动 `shared/` 前先确认这个**——`shared/` 是两模式公共层。

---

## 7. 视觉规范

### 7.1 调色板（11 色极简）

| 类别 | 色值 | 用途 |
|---|---|---|
| 品牌红 | `#DB0005` | CTA、警示、APP Push、徽章 |
| 品牌金 | `#FFBC0D` | 顶部金线、强调、H3 金竖条 |
| 品牌绿 | `#00A04A` | 达标 |
| 品牌黄 | `#FF9500` | 剩余/警告 |
| 黑色 | `#1A1A1A` | 顶栏 bg、表格 th、标题文字 |
| 白色 | `#FFFFFF` | 卡片 bg、表格主行 |
| 页底灰 | `#F0F0F0` | 页面背景 |
| 浅灰 | `#F5F5F5` | 交替行 / hover |
| 中灰 | `#E0E0E0` | 边框 |
| 副文字 | `#6B6B6B` | 副文字 |
| 弱化 | `#888888` | 弱化文字 |

**已废除**（暖色全清理过，别加回来）：`#fffdf8 / #fcfaf3 / #e4d9bf / #e8e0d4 / #F8F7F5 / #fde9ea / #2b2620 / #5a5048 / #8a7e72 / #a8001a / #b5a893 / #F0E8D6`

**保留**（用户明确不改）：`tab_bu.py` 奖牌金 `#FFF8E1` / 奖牌红 `#FBE9E7`

语义色规则：**红/绿只用于下降/增长**，同层级实体保持一致；图表要表达量级和差距，不能只靠颜色。

### 7.2 顶栏 / 导航 / 页脚

**顶栏**（`shared/header.py`）：全宽固定，JS 注入 `parent.document.body`。左侧 `date-badge`（深灰底金字大字距全大写）+ 标题 20px 黑 + 副标题 11.5px 白 65%；右侧 56x56 金色 logo。高约 84px（含 3px 金色下边线）。

**导航**（`render_header(..., nav_links=...)`）
- Performance 5 项：综合分析 / 运营分析 / BU 分析 / 计划分析 / 专题分享
- Emergency 2 项（只有 H2，不要 H3 小标题）：应急概览 / 目标拆解

**标题层级**
- H2 大标题 = 红方块徽章（34x34 圆角 + 白数字 + `#DB0005` 底）+ 黑标题 19px
- H3 小标题 = 金色左竖条 4px + 灰字 15px（不要棕色，要灰）

**页脚**（`shared/footer.py`）：页面最底，position **relative**（不是 fixed，避免一直显示）；深底 `#1A1A1A` + 白 70%。

### 7.3 顶部留白（改高度只动一个数字）

`shared/styles.py`：`.block-container { padding-top: 144px !important }`，`.nav-bar { top: 103px }`（topbar 84 + 金边 3 + nav 35）。改一处要同时核对另一处，否则出现遮挡或空洞。

---

## 8. 性能与并发

- **已向量化**（commit `bdab9e8`）：`shared/data.py::_derive_metrics` 3 个 `df.apply` -> 3 个 `np.where`；`performance/scoring.py::compute_scores` -> 4 个独立向量化算子。冷路径快 20-100x。
- **AI 并发**：`run_llm_batch(tasks, max_workers=3)` 限并发防打爆 API，串行 2-5 分钟 -> 并发约 1 分钟。
- **缓存 groupby** 仍是可优化项（边际小）。

---

## 9. 当前问题（未解）

- **AI 卡片覆盖**：老板手写的高分/需提升分析是一次性手工替换，新跑一次 AI 解读就会被重新生成覆盖。备份 `performance_review_20260708v3.bak.html`（桌面）。
- **Emergency 导出用独立 topbar**（`sections/topbar.py`），与 live UI 略有差异。
- **API Key / GitHub PAT 明文**写在配置文件里（用户明确表示"没事"）。
- **`build_plan_items` 还在 page.py 局部**，单条重试功能未实现（用户没要求）。
- **评分阈值未按新数据分布重算**：`CTR_THRESHOLDS` / `CVR_THRESHOLDS` 的 Q3 阈值沿用旧分布。
- **`shared/data.py` datetime 隐患**（见 6.3），待修。
- 顶栏留白若需"更靠上"再微调。

---

## 10. Git

- Remote：`git@github.com:ori-yin/cnn-weekly-suite.git`（**SSH**，已验证可用；PAT 已于 2026-09-20 撤销，URL 不再嵌凭证）
- 共 22+ commit，历史连续完整，用 `git log` 查
- `.git` 曾丢失并在 2026-07-08 重新 init，当时做过一次 force push 覆盖 remote 旧历史；现在历史连续，无需担心

**回退**
```bash
git checkout -- .                # 撤销未暂存修改
git reset --hard <commit>        # 回到指定 commit
```

### 10.1 同步踩坑（务必先读）

1. **`core.autocrlf = true`**：checkout 时会把 HEAD tree 的 LF 转成 CRLF，`git status` **不显示**这个差异，但 working tree 字节和 HEAD tree 已经不同。
   - 写 HANDOFF.md 这类文档若在意字节一致，用 binary mode 写 LF：`open(path,'wb').write(text.encode('utf-8'))`
   - 校验：`git hash-object HANDOFF.md` 对比 `git ls-tree HEAD HANDOFF.md`
2. **本地 `origin/main` ref 可能过期**：`git diff origin/main..HEAD` 会显示大量误导性改动。先 `git fetch` 确认；fetch 不通时用 `git ls-remote origin` 取真实远端 HEAD。
3. **走 SSH 而不是 HTTPS**：SSH（22 端口）可用；历史踩坑里 github.com HTTPS 直连被墙，才绕道 GitHub API，那是下策。
