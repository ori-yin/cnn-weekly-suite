# CNN Weekly Suite — 交接文档（HANDOFF）

> 新 session 从这里接手即可。本文件说明项目现状、结构、怎么跑、当前待办、以及踩过的坑。
> 改坏了随时 `git checkout -- .` 回退到任意 commit（见 §12 Git）。

---

## 1. 这是什么

把桌面上两个逻辑相似的 Streamlit 看板合并成的**一个工具**，两个老项目原封不动：

- 源项目（未改动，仅作参考）：
  - `C:\Users\a952462\Desktop\cnn-performance-weekly-main`（周度复盘：评分 + LLM AI 分析，4 Tab）
  - `C:\Users\a952462\Desktop\cnn-emergency-weekly-main`（应急补量：看 DAU Gap，4 Section + 环图）
- 合并结果（当前工作目录）：`C:\Users\a952462\Desktop\cnn-weekly-suite`

**形态**：单应用双模式。侧边栏 `View` 单选切 `Performance` / `Emergency`，**上传一次 xlsx 两模式共用**，各自独立导出 HTML。两模式共用同一份数据（`cnn0629.xlsx` / `cnn0630.xlsx`：Sheet1 Plan 明细 + Sheet2 去重 DAU）。

---

## 2. 怎么跑

```
cd C:\Users\a952462\Desktop\cnn-weekly-suite
setup_and_run.bat          # 或： streamlit run app.py --server.port 8505
```
浏览器开 http://localhost:8505 ，左侧上传 xlsx。端口 8505，与老项目 8503/8504 不冲突。

**注意**：`setup_and_run.bat` 已改纯 ASCII（原中文注释在 cmd/GBK 下乱码报错）。

---

## 3. 目录结构

```
cnn-weekly-suite/
├── app.py                # 唯一入口：set_page_config(仅此一次) + View 切换 + 统一上传 + 分派
├── shared/               # 两模式公共层
│   ├── theme.py          # 品牌色 / THEME_* tokens / COLUMN_MAPPING / ENCODINGS（11 色极简调色板）
│   ├── data.py           # 数据读取清洗（fuzzy 列名 + 多编码 + 衍生指标）
│   ├── header.py         # 全宽固定顶栏（JS 注入 parent.body，徽章+标题左 / logo 右）
│   ├── footer.py         # 页面底部部门版权条（JS 注入，全宽，position: relative 在文档流末尾）
│   └── styles.py         # _common_css_inner / _performance_css_inner / _emergency_css_inner / get_css(mode)
├── performance/          # 周度复盘模式
│   ├── config.py         # from shared.theme import * + 评分权重 / CHANNELS(4 个) / API_PROVIDERS
│   ├── page.py           # render_page(raw_df, dau_df) —— 由 app.py 调用
│   ├── scoring.py llm_service.py components.py export.py channel_health.py
│   └── tabs/ tab_summary/operational/bu/plan/topics.py
└── emergency/            # 应急补量模式
    ├── config.py         # from shared.theme import * + Gap阈值 / CHANNEL_COLORS / CHANNELS(5 个含公众号)
    ├── page.py           # render_page(raw_df, dau_df) —— nav 已砍到 2 项（只 H2 章节，不要 H3）
    ├── styles.py export.py
    ├── components/ ring / kpi_card / day_table / nudge_grid / fmt
    └── sections/ section1_overview / section2_dau / section3_aarr / section4_channels
    └── sections/topbar.py   # 导出用：render_topbar_html + render_footer_html
```

---

## 4. 关键约定（改代码前必读）

- **子包导入必须带前缀**：`from performance.xxx` / `from emergency.xxx` / `from shared.xxx`。不要写裸 `from config import`（会撞车）。
- **`st.set_page_config` 只能在 `app.py` 调一次**，两个 page.py 里都不能有。
- **两模式 CHANNELS 不同**（Performance 4 个、Emergency 5 个含"公众号"），各自 config 保留，别强行统一。
- **主题/列名/编码等公共常量**统一在 `shared/theme.py`。
- 数据在 `app.py` 用 `@st.cache_data` 按文件内容缓存，切模式不重复解析。
- **顶栏和页脚都用 JS 注入**（`shared/header.py` 和 `shared/footer.py`），不要在 page.py 里用 `st.markdown` 或 `st.html` 直接渲染。

---

## 5. 调色板（11 色极简）

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

**已废除**（之前存在的暖色，全清理）：`#fffdf8 / #fcfaf3 / #e4d9bf / #e8e0d4 / #F8F7F5 / #fde9ea / #2b2620 / #5a5048 / #8a7e72 / #a8001a / #b5a893 / #F0E8D6`

**5 个搭配色**（备用，按用户决定暂不启用）：`#C2945C / #6863A0 / #8F95A2 / #006BAE / #8D4430`

**保留**（用户明确不改）：`tab_bu.py:182` 奖牌金 `#FFF8E1` / 奖牌红 `#FBE9E7`

---

## 6. 顶栏 / 导航 / 页脚结构

### 顶栏（`shared/header.py`）
- **全宽固定**，JS 注入到 `parent.document.body`（按 id 替换）
- 左侧：`date-badge`（深灰底 + 金字 + 大字距全大写）+ 标题 20px 黑 + 副标题 11.5px 白 65%
- 右侧：56×56 金色 logo
- 顶栏高度 ≈84px（含 3px 金色下边线），nav-bar 紧随其后

### 导航（`render_header(... nav_links=...)`）
- **Performance（5 项全中文）**：综合分析 / 运营分析 / BU 分析 / 计划分析 / 专题分享
- **Emergency（2 项，砍掉了 H3 小标题）**：应急概览 / 目标拆解

### 标题结构（参照 preview_v7）
- **H2 大标题** = 红色方块徽章（34×34 圆角 + 白数字 + MCD_RED 底）+ 黑标题 19px
- **H3 小标题** = 金色左竖条 4px + 灰字 15px（用户不要棕色，要灰）
- 详见 `shared/styles.py` 的 `.section-header` / `.sec-num` / `.section-subheader`

### 页脚（`shared/footer.py`）
- 页面最底，position: relative（**不**是 fixed，避免一直显示）
- 深底 `#1A1A1A` + 白 70% + 9.5px

---

## 7. 顶部留白

- `shared/styles.py` 的 `.block-container { padding-top: 144px !important }`
- `shared/styles.py` 的 `.nav-bar { top: 103px }`（topbar 84 + 金边 3 + nav 35 ≈ 122-128 区间）
- 改高度时**只动一个数字**

---

## 8. 本次会话已完成的调整

1. **合并 styles.py 到 shared/**（commit `0645672`）
   - 新建 `shared/styles.py`，拆出 `_common_css_inner` / `_performance_css_inner` / `_emergency_css_inner` / `get_css(mode)`
   - 两个老 `styles.py` 删除
   - 净减约 300 行

2. **emergency 导出 HTML 顶部/两侧间隙修复**（commit `34e1882`）
   - `emergency/export.py` body 去掉 `padding: 20px`；wrap div 改 `padding: 26px 24px 60px`

3. **header 颜色改黑 `#1A1A1A`**（3 处 topbar / th bg）

4. **header 布局重写**（参考 preview_v7）：
   - logo 移右侧 56px、徽章+标题+副标 左侧堆叠
   - 部门版权挪到页脚
   - nav-bar top / padding-top 调到 103/144

5. **footer 改为文档流末尾**（不 fixed）+ 颜色加亮到 70% 白 + 字号 11px

6. **THEME_BG 改 `#F0F0F0`**（页面背景从牛皮纸暖米色 → 中性浅灰）

7. **表头黑 / KPI 卡白 / 边灰**（11 色板第一批）：KPI 卡 bg / 边框、表头背景、3 个 export CSS 变量

8. **侧边栏白底 + 灰边 + 顶部金线**

9. **表格行色清理**：THEME_PAPER 改白、THEME_ROW_ALT 改 `#F5F5F5` 浅灰、3 个内联表格的米色全替换

10. **暖色全清理到 11 色极简板**（commit c28faed 风格，~18 个文件，净 -300+ 行）
    - 所有 `#fffdf8 / #fcfaf3 / #e4d9bf / #2b2620 / #5a5048 / #8a7e72 / #a8001a / #b5a893` 等暖色 → 冷/中性

11. **品牌色对齐 McDonald's 官方**：`MCD_RED #DA291C → #DB0005` / `MCD_GOLD #FFC72C → #FFBC0D`（18 处替换）

12. **标题层级结构**（参照 preview_v7）：
    - `.section-header` 改 flex 布局 + 红方块徽章 `.sec-num` 34×34
    - `.section-subheader` 改 H3 金竖条 4px + 灰字 15px
    - `performance/components.py::section_header()` 加 `number` 参数
    - 5 个 Performance tab + 4 个 Emergency section 全部对齐
    - Performance H2 标题用了 `Executive Summary / Operational 分析 / BU 分析 / Plan 分析 / 专题分享`（与 nav 综合分析/运营分析/BU分析/计划分析/专题分享 略有差异，**没完全一致**，如要对齐需再改一次 tab 文件里的 section_header 调用）

13. **Nav 全部改中文 + Emergency 砍到 2 项**（去掉 AARR Breakdown / Channel Breakdown 两个 H3 小标题）
    - Performance：综合分析 / 运营分析 / BU 分析 / 计划分析 / 专题分享
    - Emergency：应急概览 / 目标拆解

14. **AI prompt 优化**（commit a3f2e1c 之后）：
    - 加朋友口吻（APP Push 14-18 字硬约束、企微范例、禁用"宝子/亲"）
    - 拆 Good Case（why_good/template/scenario）和诊断室（diagnosis/rewrite/logic）
    - 全渠道通用约束（禁拉踩、不编造数字、禁空喊词）
    - **AI_CHANNELS** 常量 = APP Push + 企微1v1（短信/小程序不进 AI 循环）

15. **AI 解读修复**（commit 6e1a0a9）：
    - bot3 排除 top3：防止渠道 Plan ≤ 6 时高分/需提升卡片重复（`page.py` + `tab_plan.py` UI + export 三端一致）
    - 删除 Plan 时清 `ai_results` 12 个 key（`_purge_plan_ai` helper）
    - 诊断室 prompt 精简 1700c → 800c（-53%）：按当前渠道动态生成约束、砍范例、加 ⚠️ 强 JSON 输出
    - 诊断室字段改 4 个：diagnosis / rewrite_title / rewrite_body / logic
    - 3 轮自动重试（失败驱动）：`is_failed_plan / is_failed_summary / is_failed_bu_summary` + handler while-loop
    - AttributedDict 脏数据清洗：str() 后含 "AttributedDict" 字样整个 dict 当失败标记
    - 诊断日志：`[AI] ch kind start: items=N prompt=Nc` + ✓/⚠️/✗

16. **UI 精简**：
    - Plan 分析渠道只显示 APP Push + 企微1v1（`PLAN_CHANNELS` 旧代码注释掉）
    - BU 总览表 + 浮层隐藏 IT-Traffic（`display_bu_df` 过滤视图，聚合数据 `bu_df` 完整保留）
    - BU AI 解读也过滤 IT-Traffic（`bu_items` 收集时跳过）

17. **HTML 导出优化**：
    - nav 中文化（综合分析 / 运营分析 / BU 分析 / 计划分析）+ section 标题统一
    - 渠道健康度用具体日期：标题 `渠道健康度（6/29-7/5 vs 6/22-6/28 分位）`、卡片 `点击人次（6/29-7/5 日均）`
    - `channel_health.render_channel_health()` + `export.generate_html()` + `page.py` 调用处 3 处加日期参数

18. **HTML 卡片文案替换**（commit 6e1a0a9，桌面手工操作）：
    - `performance_review_20260708v3.html` 的综合评分维度 12 张卡片（APP Push 6 + 企微1v1 6）
    - 高分 6 张替换为老板手写分析（关键写法 / 迁移方式）
    - 需提升 6 张替换为老板手写分析（问题出在 / 改写 / 改写逻辑）
    - 备份在 `performance_review_20260708v3.bak.html`
    - 替换方式：Python 脚本 + unique 锚点定位 div 范围，括号配对找 `</div>` 收尾，**不破坏结构**

---

## 9. 当前问题（未解）

### 9.1 诊断室 prompt 复杂度过高（已解决 → §8.15）

- 旧 prompt 1700+ 字符含 3 模块 + 渠道范例 + 改写约束 + 全渠道约束 + 语气分工
- **2026-07-08 精简到 800c（-53%）**：按当前渠道动态生成约束、砍范例、加 ⚠️ 强 JSON 输出
- 精简后诊断室成功率从 0% 提升到大部分 3/3 OK

### 9.2 LLM 返回 AttributedDict 脏数据（已解决 → §8.15）

- dirtyjson 解析非标 JSON 时返回 `AttributedDict` 对象
- 修复：str() 后检测 "AttributedDict" 字样，整个 dict 当失败标记（用 default 占位覆盖，3 轮循环重跑）

### 9.3 失败任务不重跑烧 token（已解决 → §8.15）

- 旧：每次点 AI 全量跑 15 个 LLM 调用，成功的也重跑
- 新：3 轮失败驱动重试循环，最多 3 次（原始 + 重试 1 + 重试 2）
- 用户"等等回过神来再点按钮"自然只跑上次失败的

### 9.4 已知遗留

- 顶栏留白微调（如果需要"更靠上"）
- 缓存 groupby 优化（边际小，前两步已给 20-100× / 10-50×）
- API Key 明文 / GitHub PAT 明文（用户说"没事"）
- Emergency 导出 HTML 仍用独立 topbar（与 live UI 略有差异）
- `build_plan_items` 还在 page.py 局部（单条重试功能未实现，用户没要求）
- AI 卡片替换是手工一次性操作（每次新跑 AI 都会重新生成 AI 解读，覆盖老板内容）

---

## 10. 性能向量化（已完成，commit bdab9e8）

- `shared/data.py::_derive_metrics`：3 个 `df.apply` → 3 个 `np.where`
- `performance/scoring.py::compute_scores`：`df.apply(_score_row)` → 4 个独立向量化算子
- 冷路径预期快 20-100×，rerun 预期快 10-50×

---

## 11. AI 分析并发（参考）

`run_llm_batch(tasks, max_workers=3)`：限并发防打爆 API，串行 2-5 分钟 → 并发 1 分钟（4-5 轮 × 3 worker）。

---

## 12. Git

- 远程：`https://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@github.com/ori-yin/cnn-weekly-suite.git`
  - ⚠️ PAT 嵌在 URL 明文（HANDOFF 之前就有），用户电脑仅自用，暂不处理
- HEAD = 当前最新 commit（local only，remote 同步过几次）
- **`.git` 是新 init 的**（用户原来的 .git 丢失过，详见下节）

### 12.1 Git 历史断裂说明

重要：原 GitHub remote `cnn-weekly-suite` 上的历史是 `04d851ff`（仅 1 个 commit），用户工作目录 `.git` 缺失。
- 2026-07-08 新 init 了一个本地 repo
- 本地 3 个 commit 推到 remote，**remote 上的旧历史已完全覆盖**（force push）
- 如需查"原 HANDOFF"提到的 `41855c4 / bdab9e8 / c28faed` 等老 commit，**已不可恢复**（只在本会话的本地用过）

### 12.2 回退命令

```bash
git checkout -- .                    # 撤销未暂存的修改
git reset --hard fb4da36             # 暴力回到 fb4da36（最早 commit）
git reset --hard 0645672             # styles 合并后
git reset --hard 34e1882             # emergency 导出修复后
```

---

## 13. 当前最新 commit

```
1158080 feat(bu): 浮层明细加 GC/GC转化率/Sales/评分 4 列  ← HEAD（最新，见 §18）
e12add5 fix(plan): AI 解读 key 与删除按钮 key 同步带 Message ID
3049305 refactor(simplify): 抽 data_is_v2/add_rate_metrics/_normalize_unit_column 三个 helper 到 shared/data.py
35ba9fd feat: 数据列变更适配(15->17列)+ 内容级聚合(Plan x Message)
0dea3b6 docs: README - document DAU sheet 3-col (date/channel/DAU) format
9405b27 feat: read_dau_sheet supports 3-col (date/channel/DAU) format
4bc43f0 refactor: /simplify 渠道健康度去重 + 内容分析标签对齐
53703e6 迭代文案 & 渠道健康度
7dd8424 docs: 更新 HANDOFF，记录今日 AI 解读迭代
6e1a0a9 feat: AI 解读全面优化 + HTML 导出体验提升
```

- `1158080` = §18 BU 浮层明细 13 列（9→13）。
- `e12add5` = `tab_plan.py` AI key + 删除按钮 key 同步带 Message ID。
- `3049305` = 抽三个 helper 到 `shared/data.py`，避免 tab_bu/tab_plan 各写一份。
- `35ba9fd` = §17 数据列变更（15→17 列）+ 内容级聚合 (Plan × Message)。
- `4bc43f0` = §14.1 的 /simplify 清理（已提交）。
- `53703e6` = 渠道健康度 5 档 band + 基期改内部从 raw_df 派生 + 文案改「内容分析/实验专题」。
- `6e1a0a9` = §8.15-17（AI 修复 + UI 精简 + HTML 导出优化）。

---

## 14. 2026-07-09 晚会话（/simplify + bug 排查；改动未提交）

### 14.1 已完成（已提交于 `4bc43f0`；编译通过、行为不变）

/simplify 清理 `53703e6` 的 diff（channel_health 重构那批）：
- **F1+F2**：`render_channel_health` 改由 `page.py` 预渲染一次（`channel_health_html`），live UI + 导出共用，避免每次 rerun 跑两遍。`generate_html` 删 6 个死参数（`prior_df/prior_start/prior_end/start_date/end_date/raw_df`）+ 2 个死 import（`pandas`、`render_channel_health`），新增 `channel_health_html` 参数。
- **F3**：`channel_health.py` 基期过滤 `.dt.date` 物化 3 次 -> 1 次（`send_dates` 复用 + min/max 用标量 `.date()`）。
- **F5 标签对齐**：nav + 导出 section 标题「计划分析」->「内容分析」（`export.py:411,557`、`page.py:84`），与 tab_plan/PRD 对齐。
- 跳过：F4（BAND 双字典，可读性平手）、F6（`high_good=RED` 是有意设计，bar+dot 一致）。

### 14.2 🔴 未修 HIGH bug —— 明天第一优先

**`scoring.py:32-33` 置信度惩罚失效（活跃 bug，每次评分都中）**
`config.py:33-38` `CONFIDENCE_THRESHOLDS` 是**升序** `[(100,0.1),(500,0.3),(1000,0.5),(5000,0.8)]`，但 `_confidence_penalty` 升序遍历 + 每轮 `np.where` 整体覆盖 -> 最后一轮 `(5000,0.8)` 盖掉前面。结果：**所有 reach∈(0,5000) 的 Plan 一律 0.8**，本该 0.1/0.3/0.5/0.8 分档。reach=50 应 0.1× 实际 0.8×，评分放大 ~8 倍，污染 Top3/Bot3 + AI 选材。PRD §3.4.1 + `tab_bu.py:158-163` early-return 正确版可证意图。
**修复一行**：`for threshold, penalty in sorted(CONFIDENCE_THRESHOLDS, reverse=True):`（降序，最小阈值最后生效）。已验 reach=50->0.1 / 200->0.3 / 600->0.5 / 2000->0.8 / 6000->1.0 全对。

### 14.3 未修 MED/LOW bug（明天定）

**MED**
- `page.py` 下载按钮给过期 HTML：点 AI 后 `st.rerun()`(346) 在导出重算(384)前 -> 下一轮下载按钮还服务 AI 前旧 HTML。修：去掉 346 rerun（370 已读新 ai_results），需测。
- `data.py` fuzzy 列名无「已分配」去重（data.py:23-30 + theme.py:42-43）：短关键词偷别字段列（「触达」先命中「预计触达」）。**潜伏**，标准列名不触发。
- CSV 表头带空格 -> rename 静默失败（data.py:21,52）：xlsx strip 了表头(140)，CSV 没 -> 全零无报错。**潜伏**，用 xlsx 不触发。
- `read_dau_sheet` 返空 DataFrame vs `None` 不一致（data.py:158,165 vs app.py:21）：emergency 若 `is None` 判空会漏判空 DataFrame。待核 emergency 用法。

**LOW**
- `llm_service.py:248` `[default]*n` 共享同一 dict -> `[{**default} for _ in range(n)]`
- `read_dau_sheet:170` 1 列 sheet 时 `r[1]` IndexError
- `export.py generate_html` 的 `df` + `channel_summary` orphan 参数：`df` 是 14.1 /simplify 删 render_channel_health 调用后新产生的孤儿，`channel_summary` 早没用 -> 一起删
- `_coerce_numeric_columns`（data.py:35-47）盲转数字（>50% 像数字就转），可能把纯数字 Plan ID 转 float
- `ENCODINGS`（theme.py:58）utf-8-sig/gb2312 不可达、latin1 吞所有错（raise 不可达）

### 14.4 死代码（grep 验证过，明天可一起清）

- **performance**：`page.py:11 CHANNELS` import；`scoring.py:16 _piecewise_score` 标量版；`tab_bu.py:103 render(expand_all=)` orphan 参数；`tab_plan.py:16 # PLAN_CHANNELS` 注释死代码
- **shared**：`styles.py` 4 个死 import（MCD_GREEN/MCD_DARK_RED/THEME_TAG_BG/THEME_RADIUS_L）；`footer.py:57 clear_footer`；`theme.py MCD_YELLOW/THEME_RADIUS_L`
- **emergency**（老模块，大头）：`section2_dau` MCD_GOLD/PLOT_LAYOUT import；`export.py base64`；`kpi_card.py` 5 个 THEME_* import；`fmt.py status_emoji/status_label`；`config.py PLAN_TYPES/PLAN_TYPE_COLORS/PLAN_TYPE_ACTIVE/PLOT_LAYOUT + 5 个 PLOT_*`；`page.py dau_source×2`；`day_table need_target`

### 14.5 tab_plan 优化（待用户定）

卡片代码本身不复杂（`_plan_card_html` 一个线性模板，36 张=2渠道×3维度×6 循环生成）。复杂的是选牌逻辑抄 3 份：
- 抽 `select_top_bot(plan_agg, dim_id)->(top3,bot3)`：page.py handler / `_render_plan_cards` / `_export_plan_cards` 三端共用，治「三端必须一致」人肉约束（最高价值）
- `DIM_SORT_COL` 常量统一维度映射（现定义 3-4 次）
- 渠道总结 HTML 合并（`_channel_summary_html` 371-402 vs `_export_channel_tabs` 内联 324-346，~22 行重复）
- `_parse_message_content` alias 删除（page.py import 改名）
- 不建议碰：`_render_plan_cards`/`_export_plan_cards` 双胞胎（st.button vs HTML，框架不同硬合别扭）

### 14.6 未完成

- performance/tabs 的 bug agent 被中断（用户下班），**tabs 的 bug 发现未捕获**，明天重跑补上（tab_summary/operational/bu/plan/topics 的逻辑错误+bug）。
- 14.2 ~ 14.5 全部待明天处理。

---

## 15. 2026-07-09 晚家里 Mac 推送（已 merge 到 HEAD）

Mac 在公司电脑下班后基于同一份代码做了 4 个 bug 修复 + 10 处死代码清理，2026-07-09 19:17 推送到 GitHub（`a2bbcc4` 死代码清理 + `0d5df68` HANDOFF 记录）。公司电脑 2026-07-10 fetch + merge 已整合。

### 15.1 ✅ Mac 已修（落地于本 merge）

| Bug | 文件 | 修复 |
|---|---|---|
| HIGH Bug 1 | `performance/scoring.py:32` | `_confidence_penalty` 升序→降序（验证 reach=50→0.1, 200→0.3, 600→0.5, 2000→0.8, 6000→1.0 全对） |
| MED Bug 2 | `performance/page.py` | 删 `st.rerun()`，下载按钮不再拿到过期 HTML |
| LOW Bug 3 | `performance/llm_service.py:248` | `[default]*n` → `[{**default} for _ in range(n)]` |
| LOW Bug 4 | `shared/data.py:170` | `data_rows = [r for r in rows[1:] if len(r) >= 2]` 单列 sheet 保护 |

### 15.2 ✅ Mac 已清死代码（10 处）

- `shared/theme.py`: `MCD_YELLOW` / `THEME_RADIUS_L`
- `shared/styles.py`: `MCD_GREEN` / `MCD_DARK_RED` / `THEME_TAG_BG` / `THEME_RADIUS_L` 死 import
- `shared/footer.py`: `clear_footer()` 死函数
- `performance/tabs/tab_bu.py`: `render(expand_all=)` 死参数
- `performance/tabs/tab_plan.py`: 已注释旧代码
- `emergency/config.py`: `PLAN_TYPES` / `PLAN_TYPE_COLORS` / `PLAN_TYPE_ACTIVE` / `PLOT_*` 共 9 个常量
- `emergency/export.py`: `import base64`
- `emergency/components/fmt.py`: `status_emoji` / `status_label`
- `emergency/components/kpi_card.py`: 5 个 `THEME_*` 死 import
- `emergency/components/day_table.py`: `need_target` 死变量
- `emergency/page.py`: `dau_source` 死变量
- `emergency/sections/section2_dau.py`: `MCD_GOLD` / `PLOT_LAYOUT` 死 import

### 15.3 ⚠️ Mac 没碰的（公司电脑独有，merge 时保留 --ours）

Mac 的 `a2bbcc4` 是 root commit，**只推了 7 个 emergency 文件**（day_table/fmt/kpi_card/config/export/page/section2_dau）。Mac 上还有 11 个 emergency 文件没进 git：公司电脑有完整版（README、requirements、__init__、nudge_grid、ring、section1/3/4、topbar），merge 时全部保留。

**Mac 推的 emergency/page.py 实际是 Performance 模式的内容（错放文件）**——公司电脑的 emergency/page.py 是真正的 Emergency 模式，merge 时取 --ours。

### 15.4 剩余待办（合并自两份 HANDOFF）

> 已落地：`scoring.py:32` 置信度惩罚修复（`a2bbcc4`）、`page.py` rerun 移除（`0d5df68`）、`llm_service.py:248` `[default]*n` 修复（`a2bbcc4`）、`data.py:170` 单列 sheet 保护（`0d5df68`）、10 处死代码清理（`a2bbcc4`）、`tab_bu.py` 4 列扩到 13 列（`1158080`）。
>
> 未做（仍待办，按优先级）：

- `performance/tabs/tab_plan.py` 三端选牌逻辑去重（`select_top_bot(plan_agg, dim_id)`，最高价值）
- `performance/export.py` 的 `df` / `channel_summary` orphan 参数（Mac 已清，但公司电脑原 HANDOFF 也有这条）
- `shared/data.py` fuzzy 列名「已分配」去重（潜伏）
- `shared/data.py` CSV 表头空格静默失败（潜伏）
- `shared/data.py` `_coerce_numeric_columns` 盲转数字可能把 Plan ID 转 float
- `shared/data.py` `ENCODINGS` utf-8-sig/gb2312/latin1 不可达
- `shared/data.py` `read_dau_sheet` 返空 DataFrame vs `None` 不一致
- `app.py:21` vs `data.py:158,165` 判空不一致
- `tab_operational.py:131/232` 两次 `daily_total` 变量覆盖（Mac 标为风格问题，非 bug）
- `tab_operational.py:21` / `tab_bu.py:16` Plan ID 缺失时 `len(df)` 返回行数（潜伏）
- `tab_bu.py:209` rank_ctr 用 `触达成功 >= 10000` 过滤，其他榜单不过滤（设计选择）
- `scoring.py:16` `_piecewise_score` 标量版死代码
- `tab_bu.py` 等继承的 `rank_*` 不一致
- `performance/tabs` 全量 bug agent 复跑（昨晚被中断）

---

## 16. 2026-08-10 状态（已解决）

> §16 原 2026-07-16 写的「本地未 push + token 失效」问题，**已自然解决**。当时以为是 token 失效，其实是 git credential 缓存命中（也可能是 PAT 自动续期）。本地累积的所有改动（44 文件 + `parse_message_content` 对齐）都已推到 origin/main。当前远端 HEAD = `1158080`，本地 working tree clean。

**已推 commits（按时间）**

| commit | 内容 |
|---|---|
| `3049305` | refactor(simplify): 抽 data_is_v2/add_rate_metrics/_normalize_unit_column 三个 helper 到 shared/data.py |
| `35ba9fd` | feat: 数据列变更适配(15→17列) + 内容级聚合(Plan × Message) |
| `0dea3b6` | docs: README - document DAU sheet 3-col (date/channel/DAU) format |
| `9405b27` | feat: read_dau_sheet supports 3-col (date/channel/DAU) format |
| `e12add5` | fix(plan): AI 解读 key 与删除按钮 key 同步带 Message ID |
| `1158080` | feat(bu): 浮层明细加 GC/GC转化率/Sales/评分 4 列 |

**已对齐 mcd-content-rank**

- `performance/tabs/tab_plan.py:41-79` `parse_message_content` 对齐 `mcd-content-rank/data_cleaning.py:141-182`：拆出 `_extract_title_from_forms` 三级 fallback + `_extract_text_from_forms` 二级 fallback；标题新增 `attachments[0]["name"]` 兜底；换行清洗补 `\r`；新增 `strip_question_marks=False` 参数（CSV 路径清理 GBK `??`）。返回 `(title, text)` 元组，3 个调用方（`tab_plan:415`、`tab_bu:350`、`page:148`）零改动。11/11 回归测试通过。

**token / 同步现状**

- `.git/` 已 init，remote = `https://github.com/ori-yin/cnn-weekly-suite.git`
- token `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` **仍有效**（API 401 假警报，git credential 缓存命中能正常 push）
- OneDrive ReparsePoint 同步 `.git/` 暂未观察到锁文件打架，但 git 操作时如报 `.git/index.lock` 不消失可临时关 OneDrive 再跑。

---

## 17. 2026-07-29 数据列变更适配（Sheet 1: 15 列 → 17 列）

上游 SQL 导出格式变更，新增 `Unit ID`（列 5）+ `Message ID`（列 15）。Plan 不再是"一 Plan 一文案"——可能拆成多 Unit + 多文案（千人千面 / 实验分时）。

**改动文件**

| 文件 | 改动 |
|---|---|
| `shared/theme.py` | `COLUMN_MAPPING` 加 `Unit ID` / `Message ID` 别名 |
| `shared/data.py` | 新增 `ID_COLS = ("Plan ID","Unit ID","Message ID")`，18 位 ID 跳过数值化；新增 `_normalize_id_columns` strip 尾部 `\t`；`_coerce_numeric_columns` skip ID 列；`_read_xlsx` / `_read_csv` 调用 normalize |
| `performance/tabs/tab_plan.py::_aggregate_plans` | 聚合键 (Plan, Message) + Unit数；先求和再算率（CTR/GC 转化率）；`dropna=False, as_index=False` |
| `performance/tabs/tab_bu.py::_aggregate_bu_plans` | 同上（BU 浮层子表）|
| `performance/page.py` | AI handler groupby (Plan, Message)；AI key 带 Message ID 后缀避免撞 key；top/bot 排序二级 tie-break 加 Message ID |
| `performance/tabs/tab_plan.py::_plan_card_html` | 卡片数据豆腐块加 `Unit` 药丸（仅 Unit数>1 时显示）|

**业务语义（与 mcd-content-rank 一致）**

- 一张内容排行榜卡片 = `Plan × Message`（Unit 不参与）
- Unit 业务含义：**千人千面**分组（同文案不同投放批次/人群），Unit 间 CTR 差异来自人群/落地页不是文案差异
- 一 Plan 一文案 → 1 张卡
- 一 Plan 多 Unit 同文案 → 1 张卡（副标 `N组 Unit`，合并千人千面）
- 一 Plan 多文案 → 每条文案各 1 张卡（实验/分时是独立策略）

**向后兼容**

旧数据（无 Message ID）`read_data` 会自动填 None 列。判定走 `notna().any()`：
- 新数据 → 聚合 (Plan, Message)
- 旧数据 → 退化按 Plan 聚合

**ID 链路 sanity check**（基于 cnn0728.xlsx 1067 行）

- Plan 数 231，平均 Unit/Plan 1.37（max 10），平均 Message/Plan 1.18（max 6）
- `(Plan, Message)` 内 0/273 跨渠道/owner/标题 ✅
- Unit ID = `[NULL]` 占位 19%（业务等同空值）
- Message ID 18 位数字（超过 float64 精度 2^53，必须字符串化）

**端到端验证**（cnn0728.xlsx 503 行 → 167 Plan×Message，cnn0727.xlsx 451 行 → 166 Plan，全部测试通过）

**关联**

- 数据列变更流程模板：`~/桌面/数据列变更适配 Handoff.md`
- 业务语义沉淀：`project_cnn_weekly_suite_unit_id` memory
- 参考 commit：`mcd-content-rank/dbb785f`（同套路）

**遗留**

- emergency 模块**未同步**（B 方案不含）。如需要后续：emergency 各 section 加 Unit数量 KPI 即可，核心聚合（按 发送日期×计划类型/渠道）不受影响
- 评分算法阈值未针对新数据分布重算（Q3 校准待做）

---

## 18. 2026-08-10 BU 浮层明细 9 列 → 13 列

**业务诉求**：BU 总览点 BU 名弹出浮层后，只能看发送明细（Plan×Message），看不到 GC、GC转化率、Sales、评分，看不出这条文案值不值。补这 4 列。

**改动**（commit `1158080`，1 文件 +16/-1）

| 位置 | 改动 |
|---|---|
| `performance/tabs/tab_bu.py:11` | 加 `from performance.scoring import compute_scores` |
| `performance/tabs/tab_bu.py::_aggregate_bu_plans` | `add_rate_metrics(plan_agg)` 后调 `compute_scores(plan_agg)`，产出 Plan×Message 级「综合评分」列 |
| `performance/tabs/tab_bu.py::_render_plan_rows_html` | 表头 + 行数据加 4 列（订单GC / GC转化率 / 订单Sales / 评分），「评分」用 MCD_RED 加粗；9 列 → 13 列；docstring 同步 |

**评分含义**：用 Plan×Message 粒度算（与「内容分析」tab 同 `scoring.compute_scores`），**不是 BU 整体评分**。看的是「这条文案值多少分」。

**导出 HTML 同步**：`page.py:405` `tables["bu"] = bu_table_html` 直接复用 `render_bu()` 返回值（已含 popover 浮层 HTML），无需改 `export.py`，导出报告自动含 13 列。

**兼容性**：`compute_scores` 输入列 `渠道/触达成功/点击人次/订单GC` + `add_rate_metrics` 后的 `CTR/GC转化率` BU 浮层聚合已全部具备；`data_is_v2` 自动适配新旧数据（新数据按 `(Plan, Message)` 聚合，旧数据退化按 `Plan`）。
