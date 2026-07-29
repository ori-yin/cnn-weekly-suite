"""
page.py - CNN Performance Weekly 模式渲染（由 suite/app.py 调用）
数据（raw_df, dau_df）由入口统一上传后传入，本模块不再自行读取文件。
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from functools import partial

from performance.config import API_PROVIDERS
from performance.tabs.tab_plan import AI_CHANNELS
from shared.data import filter_week_data
from shared.header import render_header, clear_header
from shared.footer import render_footer
from performance.scoring import compute_scores
from shared.styles import get_css
from performance.components import insight_block
from performance.tabs.tab_summary import render as render_summary
from performance.tabs.tab_operational import render as render_operational
from performance.tabs.tab_bu import render as render_bu, _compute_bu_metrics, _prior_metrics_by_bu
from performance.tabs.tab_plan import render as render_plan
from performance.tabs.tab_topics import render as render_topics
from performance.export import generate_html
from performance.channel_health import render_channel_health
from performance.llm_service import analyze_content, analyze_channel_summary, analyze_bu_summary, run_llm_batch, _safe_int, _safe_float, is_failed_plan, is_failed_summary, is_failed_bu_summary


def render_page(raw_df, dau_df):
    """Performance 模式主渲染。raw_df / dau_df 由 suite/app.py 统一上传后传入。"""
    st.markdown(get_css("performance"), unsafe_allow_html=True)

    # ─── 侧边栏：Target ────────────────────────────────
    with st.sidebar:
        st.markdown("---")
        target_dau = st.number_input(
            "Target DAU（日均）",
            min_value=0,
            value=50000,
            step=1000,
            help="本周每日目标触达人次",
        )

    if raw_df is None or raw_df.empty:
        clear_header()
        return

    # ─── 侧边栏：日期范围（根据数据自动限定）─────────────────
    data_min = raw_df["发送日期"].min().date()
    data_max = raw_df["发送日期"].max().date()

    # 默认上一个自然周（周一~周日）
    today = date.today()
    days_since_monday = today.weekday()
    default_end = today - timedelta(days=days_since_monday + 1)  # 上周日
    default_start = default_end - timedelta(days=6)               # 上周一
    # 确保不超出数据范围
    default_start = max(default_start, data_min)
    default_end = min(default_end, data_max)

    with st.sidebar:
        st.markdown("---")
        st.markdown("##### 日期范围")
        start_date = st.date_input("开始日期", value=default_start, min_value=data_min, max_value=data_max)
        end_date = st.date_input("结束日期", value=default_end, min_value=data_min, max_value=data_max)

        # 导出按钮（HTML 内容由 session_state 提供，首次可能为空）
        st.markdown("---")
        export_html = st.session_state.get("export_html", "")
        today_str = date.today().strftime("%Y%m%d")
        st.download_button(
            label="下载 HTML 看板",
            data=export_html or "<html><body>请先刷新页面</body></html>",
            file_name=f"performance_review_{today_str}.html",
            mime="text/html",
            use_container_width=True,
            disabled=not export_html,
        )

    # ─── 顶部栏 + 导航栏（主内容区第一个元素）──────────────
    render_header("Performance Review", "周度数据复盘看板", badge=f"{start_date} ~ {end_date}", nav_links=[
        ("sec-summary", "综合分析"),
        ("sec-operational", "运营分析"),
        ("sec-bu", "BU 分析"),
        ("sec-plan", "内容分析"),
        ("sec-topics", "实验专题"),
    ])

    df = filter_week_data(raw_df, start_date, end_date)
    if df.empty:
        st.warning(f"所选日期范围 [{start_date} ~ {end_date}] 内无数据")
        return

    # 计算综合评分
    df = compute_scores(df)

    # ─── 维度筛选（折叠）─────────────────────────────────
    with st.sidebar:
        with st.expander("维度筛选", expanded=False):
            channels = sorted(df["渠道"].dropna().unique().tolist()) if "渠道" in df.columns else []
            plan_types = sorted(df["计划类型"].dropna().unique().tolist()) if "计划类型" in df.columns else []
            bus = sorted(df["预算owner"].dropna().unique().tolist()) if "预算owner" in df.columns else []

            selected_channels = st.multiselect("渠道", channels, default=channels)
            selected_plan_types = st.multiselect("计划类型", plan_types, default=plan_types)
            selected_bus = st.multiselect("预算 Owner (BU)", bus, default=bus)

    if selected_channels:
        df = df[df["渠道"].isin(selected_channels)]
    if selected_plan_types:
        df = df[df["计划类型"].isin(selected_plan_types)]
    if selected_bus:
        df = df[df["预算owner"].isin(selected_bus)]

    if df.empty:
        st.warning("筛选后无数据，请调整筛选条件")
        return

    # 上周数据（用于 BU 总览表的 CTR 环比列 + BU AI 解读），应用同侧边栏筛选保持口径一致
    prior_start = start_date - timedelta(days=7)
    prior_end = end_date - timedelta(days=7)
    prior_df = filter_week_data(raw_df, prior_start, prior_end)
    if selected_channels:
        prior_df = prior_df[prior_df["渠道"].isin(selected_channels)]
    if selected_plan_types:
        prior_df = prior_df[prior_df["计划类型"].isin(selected_plan_types)]
    if selected_bus:
        prior_df = prior_df[prior_df["预算owner"].isin(selected_bus)]

    # ─── 侧边栏：AI 配置（折叠）─────────────────────────────
    with st.sidebar:
        st.markdown("---")
        with st.expander("AI 解读配置", expanded=False):
            ai_provider = st.selectbox("AI 服务商", options=list(API_PROVIDERS.keys()), index=0)
            ai_models = API_PROVIDERS[ai_provider]["models"]
            ai_model = st.selectbox("模型", options=ai_models, index=0)
            ai_api_key = st.text_input(
                "API Key",
                value=API_PROVIDERS[ai_provider].get("api_key", ""),
                type="password",
            )

        if st.button("✨ AI 分析", use_container_width=True):
            # 三段式：先收集所有 LLM 任务入参 → 并发执行 → 主线程统一写回
            # 旧实现串行调 ~15 次 LLM（2-5 分钟），改 max_workers=3 并发后约 1 分钟。
            df_ai = df.copy()
            if "消息内容" in df_ai.columns:
                from performance.tabs.tab_plan import _parse_message_content
                parsed = df_ai["消息内容"].apply(_parse_message_content)
                df_ai["消息标题"] = parsed.apply(lambda x: x[0])
                df_ai["消息内容_parsed"] = parsed.apply(lambda x: x[1])

            ai_results = st.session_state.get("ai_results", {})
            channel_summary = st.session_state.get("channel_summary", {})

            # 3个排序维度
            DIMS = [
                ("score", "综合评分"),
                ("ctr", "CTR"),
                ("sales", "订单Sales"),
            ]

            # ─── 第一段：收集任务入参（不调 LLM，只算数据）──────────
            # 每项 (keys, callable)：callable 已固化所有入参（值拷贝），不受循环变量晚绑定影响
            plan_tasks = []        # [(top_keys 或 bot_keys, () -> list[结果])]
            summary_tasks = []     # [(ch, () -> dict)]

            def _build_items(rows_df, ch, dim_id, tier=""):
                items, keys = [], []
                for rank, (_, row) in enumerate(rows_df.iterrows(), 1):
                    msg_col = "消息内容_parsed" if "消息内容_parsed" in row.index else "消息内容"
                    content = str(row.get(msg_col, "")).strip() if msg_col in row.index else ""
                    items.append({
                        "标题": str(row.get("消息标题", "")),
                        "内容": content[:200],
                        "渠道": ch,
                        "触达成功": _safe_int(row.get("触达成功")),
                        "点击人次": _safe_int(row.get("点击人次")),
                        "CTR": _safe_float(row.get("CTR")),
                        "订单GC": _safe_int(row.get("订单GC")),
                        "订单GC转化率": _safe_float(row.get("GC转化率")),
                        "综合评分": _safe_float(row.get("综合评分")),
                        "排名": rank,
                    })
                    # AI key: 新数据带 Message ID（避免一 Plan 多文案撞 key），旧数据退化 Plan ID
                    msg_id = str(row.get("Message ID", "")).strip() if "Message ID" in row.index else ""
                    key_pid = f"{row['Plan ID']}_{msg_id}" if msg_id else str(row['Plan ID'])
                    keys.append(f"{key_pid}_{ch}_{dim_id}_{tier}")
                return items, keys

            for ch in AI_CHANNELS:
                ch_df = df_ai[df_ai["渠道"] == ch]
                if len(ch_df) < 2:
                    continue
                agg = {
                    "Plan名称": "first",
                    "触达成功": "sum",
                    "点击人次": "sum",
                    "订单GC": "sum",
                    "综合评分": "mean",
                    "消息标题": "first",
                }
                if "消息内容_parsed" in ch_df.columns:
                    agg["消息内容_parsed"] = "first"
                elif "消息内容" in ch_df.columns:
                    agg["消息内容"] = "first"
                if "订单Sales" in ch_df.columns:
                    agg["订单Sales"] = "sum"

                # 聚合键：新数据 (Plan, Message)，旧数据退化 (Plan)
                if "Message ID" in ch_df.columns and ch_df["Message ID"].notna().any():
                    group_keys = ["Plan ID", "Message ID"]
                else:
                    group_keys = ["Plan ID"]

                plan_agg = ch_df.groupby(group_keys, dropna=False, as_index=False).agg(agg)
                # 聚合后必须先求和再算率（CTR/GC转化率），避免按行先算率再平均的精度坑
                if "触达成功" in plan_agg.columns and "点击人次" in plan_agg.columns:
                    import numpy as _np
                    plan_agg["CTR"] = _np.where(
                        plan_agg["触达成功"] > 0,
                        plan_agg["点击人次"] / plan_agg["触达成功"] * 100,
                        0.0,
                    )
                    plan_agg["GC转化率"] = _np.where(
                        plan_agg["点击人次"] > 0,
                        plan_agg["订单GC"] / plan_agg["点击人次"] * 100,
                        0.0,
                    )

                plan_agg = plan_agg[plan_agg["触达成功"] > 0]
                if len(plan_agg) < 2:
                    continue

                # 过滤掉被删除的Plan
                deleted = st.session_state.get("deleted_plans", set())
                plan_agg = plan_agg[~plan_agg["Plan ID"].isin(deleted)]

                # 渠道总结：取综合评分TOP4
                summary_top = plan_agg.sort_values("综合评分", ascending=False).head(4)
                summary_items = []
                for _, row in summary_top.iterrows():
                    msg_col = "消息内容_parsed" if "消息内容_parsed" in row.index else "消息内容"
                    content = str(row.get(msg_col, "")).strip() if msg_col in row.index else ""
                    summary_items.append({
                        "标题": str(row.get("消息标题", "")),
                        "内容": content[:200],
                        "触达成功": _safe_int(row.get("触达成功")),
                        "CTR": _safe_float(row.get("CTR")),
                        "订单GC": _safe_int(row.get("订单GC")),
                        "订单Sales": _safe_float(row.get("订单Sales")),
                        "综合评分": _safe_float(row.get("综合评分")),
                    })
                # 固化入参
                summary_tasks.append((ch, partial(analyze_channel_summary, ai_api_key, ai_provider, ai_model, ch, summary_items)))

                for dim_id, sort_col in DIMS:
                    # 先按当前维度 desc 预排，二级 tie-break by "Plan ID" asc（+ Message ID 新数据），与 _export_channel_tabs 对齐
                    # 避免同 Sales 值时 handler/UI/导出 三端 Plan ID 顺序分歧导致 AI key 对不上
                    sort_col_eff = sort_col if sort_col in plan_agg.columns else "综合评分"
                    sort_keys = [sort_col_eff, "Plan ID"]
                    sort_asc = [False, True]
                    if "Message ID" in plan_agg.columns:
                        sort_keys.append("Message ID")
                        sort_asc.append(True)
                    plan_agg_sorted = plan_agg.sort_values(sort_keys, ascending=sort_asc)

                    # 高分 TOP3 → Good Case（已 desc 排，直接 head(3)）
                    dim_top = plan_agg_sorted.head(3)
                    top_items, top_keys = _build_items(dim_top, ch, dim_id, tier="top")
                    plan_tasks.append((top_keys, partial(analyze_content, ai_api_key, ai_provider, ai_model, top_items, True, None)))

                    # 需提升 BOT3 → 诊断室（带 top_items 作 Good Case 参照）
                    # 先排除 top3 的 Plan ID 再升序取前 3，避免渠道 Plan 数 ≤ 6 时与 top3 完全重叠
                    # 二级 tie-break by "Plan ID" asc，与 UI _render_plan_cards / _export_channel_tabs 完全一致
                    # 避免同 Sales 值时 handler/UI/导出 三端 Plan ID 顺序分歧导致 AI key 对不上
                    top_plan_ids = set(dim_top["Plan ID"])
                    bot_pool = plan_agg_sorted[~plan_agg_sorted["Plan ID"].isin(top_plan_ids)]
                    bot_sort_keys = [sort_col_eff, "Plan ID"]
                    bot_sort_asc = [True, True]
                    if "Message ID" in bot_pool.columns:
                        bot_sort_keys.append("Message ID")
                        bot_sort_asc.append(True)
                    dim_bot = bot_pool.sort_values(bot_sort_keys, ascending=bot_sort_asc, na_position="last").head(3)
                    bot_items, bot_keys = _build_items(dim_bot, ch, dim_id, tier="bot")
                    plan_tasks.append((bot_keys, partial(analyze_content, ai_api_key, ai_provider, ai_model, bot_items, False, top_items)))

            # BU AI 入参（循环外，只跑一次）
            n_days_cur = df["发送日期"].nunique() if "发送日期" in df.columns else 7
            n_days_prior = prior_df["发送日期"].nunique() if (prior_df is not None and not prior_df.empty and "发送日期" in prior_df.columns) else 7
            bu_prior_map = _prior_metrics_by_bu(prior_df, n_days_prior)
            bu_items = []
            for bu, bu_g in df.groupby("预算owner"):
                if pd.isna(bu) or bu == "[NULL]" or bu == "":
                    continue
                if bu == "IT-Traffic":    # 裁判部门，BU AI 解读不解读这个 BU
                    continue
                m = _compute_bu_metrics(bu_g)
                cur_reach_daily = m["触达成功"] / n_days_cur if n_days_cur > 0 else 0
                if cur_reach_daily < 15000:          # 日均触达阈值（等价原周总10万）
                    continue
                prior = bu_prior_map.get(bu)
                if prior is None:              # 无上周数据，无法算环比
                    continue
                bu_items.append({
                    "bu": bu,
                    "curr_ctr": m["CTR"],
                    "prior_ctr": prior["ctr"],
                    "delta_pp": m["CTR"] - prior["ctr"],
                    "reach": cur_reach_daily,            # 本周日均触达（与 BU 表口径一致）
                    "prior_reach": prior["reach_daily"],  # 上周日均触达（对齐补上）
                })
            bu_items.sort(key=lambda x: abs(x["delta_pp"]), reverse=True)
            bu_items = bu_items[:15]                # 防 prompt 过长，只解读变动最大的

            bu_callable = None
            bu_summary_result = None
            if bu_items:
                bu_callable = partial(analyze_bu_summary, ai_api_key, ai_provider, ai_model, bu_items)
            elif bu_prior_map:
                bu_summary_result = {"error": "本周无达标 BU（日均触达≥1.5万），跳过 BU 解读"}
            # else: 无上周数据 → bu_summary_result 保持 None，bu_callable 也为 None，不显示 BU 块

            has_work = bool(plan_tasks) or bool(summary_tasks) or bu_summary_result is not None or bu_callable is not None
            if not has_work:
                st.warning("没有可分析的 Plan / BU 数据")
            else:
                # ─── 第二段：失败驱动重试循环（最多 3 次尝试）────────────
                # 每轮跑完后检查失败任务，失败的进入下一轮，直到全部成功或达到上限
                # 第 N 轮失败的也写回 ai_results（显示 "—" / error），保证 UI 不留空白
                MAX_RETRIES = 3
                cur_plan = list(plan_tasks)
                cur_summary = list(summary_tasks)
                cur_bu_callable = bu_callable
                bu_last_result = bu_summary_result   # 保留最后一次的 BU 结果（含失败）

                for attempt in range(MAX_RETRIES):
                    if not cur_plan and not cur_summary and cur_bu_callable is None:
                        break   # 没失败任务，结束

                    n = len(cur_plan) + len(cur_summary) + (1 if cur_bu_callable else 0)
                    if attempt == 0:
                        label = f"AI 正在并发分析 {n} 个任务（max 3 并发，约 1 分钟）..."
                    else:
                        label = f"第 {attempt+1} 轮重试 {n} 个失败任务..."

                    with st.spinner(label):
                        plan_results = run_llm_batch([t for _, t in cur_plan], max_workers=3) if cur_plan else []
                        summary_results = run_llm_batch([t for _, t in cur_summary], max_workers=3) if cur_summary else []
                        bu_result = cur_bu_callable() if cur_bu_callable is not None else None

                    # 写回所有结果（含失败的——失败会显示 "—" 或 error，不留空白）
                    for (keys, _), r in zip(cur_plan, plan_results):
                        ai_results.update(dict(zip(keys, r)))
                    for (ch, _), r in zip(cur_summary, summary_results):
                        channel_summary[ch] = r
                    if cur_bu_callable is not None and bu_result is not None:
                        bu_last_result = bu_result

                    # 收集失败的进入下一轮
                    nxt_plan = [(keys, t) for (keys, t), r in zip(cur_plan, plan_results) if is_failed_plan(r)]
                    nxt_summary = [(ch, t) for (ch, t), r in zip(cur_summary, summary_results) if is_failed_summary(r)]
                    nxt_bu_callable = cur_bu_callable if (cur_bu_callable is not None and bu_result is not None and is_failed_bu_summary(bu_result)) else None

                    n_failed = len(nxt_plan) + len(nxt_summary) + (1 if nxt_bu_callable else 0)
                    if attempt < MAX_RETRIES - 1 and n_failed > 0:
                        st.toast(f"⚠️ {n_failed} 个任务失败，自动重试...", icon="🔄")

                    cur_plan, cur_summary, cur_bu_callable = nxt_plan, nxt_summary, nxt_bu_callable

                # ─── 第三段：写回 session_state（线程安全）────────────────
                st.session_state["ai_results"] = ai_results
                st.session_state["channel_summary"] = channel_summary
                if bu_last_result is not None:
                    st.session_state["bu_summary"] = bu_last_result
                else:
                    st.session_state.pop("bu_summary", None)   # 清旧值，避免显示过时数据

    # ─── 主体内容（单页滚动，4个 section）─────────────────────
    # 筛选 DAU sheet 的日期范围
    if dau_df is not None and not dau_df.empty and "日期" in dau_df.columns:
        dau_df = dau_df[(dau_df["日期"].dt.date >= start_date) & (dau_df["日期"].dt.date <= end_date)]

    st.markdown('<div id="sec-summary"></div>', unsafe_allow_html=True)
    summary_figs, summary_kpis, summary_insight_html = render_summary(df, target_dau, dau_df=dau_df)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div id="sec-operational"></div>', unsafe_allow_html=True)
    op_figs, op_kpis, op_detail_html = render_operational(df, target_dau)

    # 渠道健康度（基期=现期之前所有历史；live 与导出共用同一份 HTML，避免重复计算）
    channel_health_html = render_channel_health(df, raw_df=raw_df, start_date=start_date, end_date=end_date)
    st.markdown(channel_health_html, unsafe_allow_html=True)

    # ─── 本板块洞察（渠道健康度下面）─────────────
    channel_insight_html = insight_block("insight_channel", label="渠道健康度洞察")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div id="sec-bu"></div>', unsafe_allow_html=True)
    bu_summary = st.session_state.get("bu_summary", {})
    bu_figs, bu_table_html = render_bu(df, prior_df=prior_df, bu_summary=bu_summary)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div id="sec-plan"></div>', unsafe_allow_html=True)
    ai_results = st.session_state.get("ai_results", {})
    channel_summary = st.session_state.get("channel_summary", {})
    plan_html = render_plan(df, ai_results=ai_results, channel_summary=channel_summary)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div id="sec-topics"></div>', unsafe_allow_html=True)
    topics_html = render_topics()

    # ─── 导出 HTML ──────────────────────────────────────
    figs = {"summary": summary_figs, "operational": op_figs, "bu": bu_figs}
    kpis = {"summary": summary_kpis, "operational": op_kpis}
    tables = {"operational": op_detail_html, "bu": bu_table_html, "plan": plan_html, "topics": topics_html}
    insights = {
        "summary": summary_insight_html,
        "channel": channel_insight_html,
        "bu": "",  # 已合并到 tables["bu"]，导出端自动跟进
    }
    html_content = generate_html(target_dau, figs, tables, kpis, period_str=f"{start_date} ~ {end_date}", channel_health_html=channel_health_html, insights=insights)
    st.session_state["export_html"] = html_content

    # ─── 页脚部门版权 ─────────────────────────────────────
    render_footer()
