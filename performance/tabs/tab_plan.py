"""
tab_plan.py - 第四层：内容分析
每个渠道 Top 3 + Bottom 3，综合评分，含文案标题和正文
"""

import json
import re
import numpy as np
import streamlit as st
import pandas as pd
from performance.config import MCD_RED, MCD_GOLD, MCD_GREEN, MCD_DARK_RED, CHANNELS, THEME_INK, THEME_INK2, THEME_MUTED, THEME_LINE, THEME_PAPER, THEME_TAG_BG, THEME_TAG_BORDER, THEME_RADIUS_S, THEME_RADIUS_M
from performance.components import section_header
from shared.data import add_rate_metrics, data_is_v2, _normalize_unit_column


# 内容分析渠道列表：仅 APP Push + 企微1v1（与 AI_CHANNELS 对齐）
PLAN_CHANNELS = [ch for ch in CHANNELS if ch not in ("短信", "微信小程序订阅消息")]

# AI 解读渠道列表：仅 APP Push + 企微1v1。
# 短信/小程序样本少、改写意义不大，从 AI 循环里排除（卡片仍展示）。
AI_CHANNELS = [ch for ch in CHANNELS if ch not in ("短信", "微信小程序订阅消息")]

# AI key 维度枚举（与 page.py handler 算 AI 时一致）
_AI_DIMS = ("score", "ctr", "sales")
_AI_TIERS = ("top", "bot")


# ─── 内容分析排除规则（仅影响第4部分，不干预其他 section）──────────
# 匹配规则：Plan名称 OR 消息标题 任一字段包含任一关键词 → 剔除（不区分大小写）
# 设计意图：礼品卡 / 入群礼 / 团餐 这类文案不适合做营销内容分析
#   - 「礼品卡」：过期提醒、权益通知等纯服务型文案
#   - 「入群礼」：群裂变场景的钩子文案
#   - 「团餐」：B 端场景，CTA 与 C 端营销差异大
# 调用方：
#   - tab_plan.render() 在解析消息内容后立即过滤（影响 UI 卡片 + 导出 HTML）
#   - page.py AI handler 在 df_ai.copy() 后立即过滤（影响 LLM 入参）
_CONTENT_EXCLUDE_KWS = ("礼品卡", "入群礼", "团餐")


def _content_exclusion_mask(df: pd.DataFrame) -> pd.Series:
    """返回 True 表示该行应该被排除（命中 Plan名称 或 消息标题 任一关键词）。

    空 df 或关键词列表为空 → 全 False（不过滤）。下游用 df[~mask] 拿保留行。
    """
    if df.empty or not _CONTENT_EXCLUDE_KWS:
        return pd.Series(False, index=df.index)

    parts = []
    if "Plan名称" in df.columns:
        parts.append(df["Plan名称"].astype(str).fillna(""))
    if "消息标题" in df.columns:
        parts.append(df["消息标题"].astype(str).fillna(""))
    if not parts:
        return pd.Series(False, index=df.index)

    text = parts[0]
    for p in parts[1:]:
        text = text.str.cat(p, sep=" ")
    pattern = "|".join(re.escape(k) for k in _CONTENT_EXCLUDE_KWS)
    return text.str.contains(pattern, case=False, na=False)


def _purge_plan_ai(plan_id: str):
    """从 ai_results 移除某 Plan 的所有 (channel, dim, tier) key。

    每个 Plan 在 handler 算 AI 时会产生 AI_CHANNELS × 3 dim × 2 tier = 12 个 key
    （实际只属于 1 个 channel，但防御性扫所有 channel）。配合"移除"按钮的 callback
    调用，保证 ai_results 不残留被删 Plan 的旧解读。
    """
    ai_results = st.session_state.get("ai_results", {})
    for ch_clear in AI_CHANNELS:
        for dim_id_clear in _AI_DIMS:
            for tier in _AI_TIERS:
                ai_results.pop(f"{plan_id}_{ch_clear}_{dim_id_clear}_{tier}", None)
    st.session_state["ai_results"] = ai_results


def _extract_title_from_forms(forms):
    """从 forms 列表中提取标题（三级 fallback：thing1 → 任意 thingX → 非 time 任意）"""
    if not isinstance(forms, list):
        return None
    for item in forms:
        if item.get("code") == "thing1" and item.get("value"):
            return item["value"]
    for item in forms:
        code = item.get("code", "")
        value = item.get("value")
        if code.startswith("thing") and value:
            return value
    for item in forms:
        code = item.get("code", "")
        value = item.get("value")
        if not code.startswith("time") and value:
            return value
    return None


def _extract_text_from_forms(forms):
    """从 forms 列表中提取正文（二级 fallback：thing5/short_thing5 → 任意 thingX 但非 thing1）"""
    if not isinstance(forms, list):
        return None
    for item in forms:
        code = item.get("code", "")
        value = item.get("value")
        if code in ("thing5", "short_thing5") and value:
            return value
    for item in forms:
        code = item.get("code", "")
        value = item.get("value")
        if code.startswith("thing") and code != "thing1" and value:
            return value
    return None


def parse_message_content(raw, strip_question_marks=False):
    """
    解析消息内容 JSON，提取标题和正文。
    参考 mcd-content-rank 的 data_cleaning.py（parse_message）。
    返回 (title, text) 元组，保持与 3 处调用方（tab_plan/tab_bu/page）兼容。
    （旧名 _parse_message_content 保留为 alias 兼容 tab_plan.py 内部调用）
    """
    if pd.isna(raw) or not isinstance(raw, str):
        return "", ""

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return "", ""

    # 防御：JSON 解出来不是 dict（list/str/number 都见过）—— 当空返回
    if not isinstance(data, dict):
        return "", ""

    # 标题：title 字段 → forms 兜底 → attachments.name 兜底
    title = data.get("title")
    if not title:
        title = _extract_title_from_forms(data.get("forms"))
    if not title:
        attachments = data.get("attachments")
        if isinstance(attachments, list) and len(attachments) > 0:
            title = attachments[0].get("name", "")

    # 正文：text 字段 OR content 字段 → forms 兜底
    # 兼容钉钉/企微/短信 webhook——多种 payload schema 里正文可能是 text 或 content
    text = data.get("text") or data.get("content")
    if not text:
        text = _extract_text_from_forms(data.get("forms"))

    # 极端兜底：从正文里切第一句当标题
    if not title and text:
        first_part = re.split(r'[。！？\n]', str(text).strip())[0].strip()
        title = first_part if first_part else str(text)[:20]

    title = str(title).strip() if title else ""
    text = str(text).strip() if text else ""

    # 清洗三种换行符（保留 emoji 等 Unicode）
    title = title.replace('\r\n', '').replace('\n', '').replace('\r', '')
    text = text.replace('\r\n', '').replace('\n', '').replace('\r', '')

    # CSV 路径：清理 GBK 编码残留的连续 ? 字符（单个问号保留，避免吞合法问号）
    if strip_question_marks:
        title = re.sub(r'\?{2,}', '', title)
        text = re.sub(r'\?{2,}', '', text)

    return title, text


# 旧名 alias（保留 tab_plan.py 内部调用与下游兼容）
_parse_message_content = parse_message_content


def _plan_card_html(row: pd.Series, rank: int, is_good: bool, ai_result: dict = None) -> str:
    """生成单个 Plan 卡片的 HTML，可选 AI 解读"""
    # 高分用红花、需提升用成长苗（取代原金银铜奖牌）
    icon = "🌺" if is_good else "🌱"

    score = row.get("综合评分", 0)
    score_color = MCD_GREEN if score >= 75 else (MCD_GOLD if score >= 60 else MCD_RED)

    plan_name = str(row.get("Plan名称", "—"))
    if len(plan_name) > 50:
        plan_name = plan_name[:50] + "..."

    plan_id = str(row.get("Plan ID", ""))
    bu = str(row.get("预算owner", "—"))
    send_date = str(row.get("发送日期", ""))
    if send_date and len(send_date) > 10:
        send_date = send_date[:10]

    msg_title = str(row.get("消息标题", "")).strip()
    msg_text = str(row.get("消息内容", "")).strip()

    # 文案区域（无边框，直接展示）
    msg_html = ""
    if msg_title:
        msg_html += f'<div style="font-weight:600;color:{THEME_INK};font-size:12px;margin-top:6px;">{msg_title}</div>'
    if msg_text:
        display_text = msg_text[:100] + "..." if len(msg_text) > 100 else msg_text
        msg_html += f'<div style="color:{THEME_MUTED};font-size:12px;line-height:1.5;margin-top:2px;">{display_text}</div>'

    # 数据豆腐块（药丸样式，参考 mcd-content-rank）
    metrics = [
        ("触达", f'{int(row.get("触达成功", 0)):,}'),
        ("点击", f'{int(row.get("点击人次", 0)):,}'),
        ("CTR", f'{row.get("CTR", 0):.2f}%'),
        ("GC", f'{int(row.get("订单GC", 0)):,}'),
        ("GC率", f'{row.get("GC转化率", 0):.1f}%'),
        ("Sales", f'{row.get("订单Sales", 0):,.2f}'),
    ]
    # 新数据（>=7/28）多 Unit 同文案时显示 Unit 数副标；旧数据无该列时跳过
    unit_n = int(row.get("Unit数") or 0)
    if "Unit数" in row.index and unit_n > 1:
        metrics.insert(0, ("Unit", f"{unit_n}组"))
    metrics_html = ""
    for label, val in metrics:
        metrics_html += (
            f'<span style="background:{THEME_TAG_BG};padding:3px 10px;border-radius:{THEME_RADIUS_S};font-size:12px;color:{THEME_MUTED};font-weight:500;">'
            f'{label} {val}</span>'
        )

    # 高分显示 BU，需提升隐藏 BU
    bu_span = (
        f'<span style="color:{THEME_TAG_BORDER};">·</span>'
        f'<span style="color:{THEME_INK2};">{bu}</span>'
    ) if is_good else ""

    return (
        f'<div style="background:#fff;border:1px solid {THEME_LINE};border-radius:{THEME_RADIUS_M};padding:14px 16px;margin-bottom:10px;position:relative;">'
        f'<div style="display:flex;align-items:center;gap:6px;font-size:12px;margin-bottom:6px;">'
        f'<span>{icon}</span>'
        f'<span style="color:{THEME_INK2};">{plan_id}</span>'
        f'{bu_span}'
        f'<span style="color:{THEME_TAG_BORDER};">·</span>'
        f'<span style="color:{THEME_MUTED};">{send_date}</span>'
        f'<span style="margin-left:auto;font-size:16px;font-weight:800;color:{score_color};">{score:.0f}</span>'
        f'</div>'
        f'<div style="font-size:13px;font-weight:700;color:{THEME_INK};margin-bottom:4px;">{plan_name}</div>'
        f'{msg_html}'
        f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;">'
        f'{metrics_html}'
        f'</div>'
        f'{_ai_inline_html(ai_result, is_good)}'
        f'</div>'
    )


def _ai_inline_html(ai_result: dict = None, is_good: bool = True) -> str:
    """生成卡片内 AI 解读折叠区域 HTML：高分 Good Case / 需提升 诊断室 两套"""
    if not ai_result:
        return ""
    if "error" in ai_result:
        return (
            f'<details style="margin-top:8px;">'
            f'<summary style="font-size:12px;font-weight:600;color:#c00;cursor:pointer;">AI 解读失败</summary>'
            f'<div style="background:{THEME_TAG_BG};border-radius:{THEME_RADIUS_S};padding:10px 12px;margin-top:4px;">'
            f'<div style="font-size:12px;color:#c00;">{ai_result["error"]}</div>'
            f'</div></details>'
        )
    # 按类型分两套字段渲染
    if is_good:
        content_parts = [
            f'为什么好：{ai_result.get("why_good", "—")}',
            f'可复用模板：{ai_result.get("template", "—")}',
            f'适用场景：{ai_result.get("scenario", "—")}',
        ]
    else:
        content_parts = [
            f'问题诊断：{ai_result.get("diagnosis", "—")}',
            f'改写标题：{ai_result.get("rewrite_title", "—")}',
            f'改写正文：{ai_result.get("rewrite_body", "—")}',
            f'改写逻辑：{ai_result.get("logic", "—")}',
        ]
    content_html = "<br>".join(content_parts)

    return (
        f'<details style="margin-top:8px;">'
        f'<summary style="font-size:12px;font-weight:600;color:{MCD_DARK_RED};cursor:pointer;">AI 解读</summary>'
        f'<div style="background:{THEME_TAG_BG};border-radius:{THEME_RADIUS_S};padding:10px 12px;margin-top:4px;">'
        f'<div style="font-size:12px;color:{THEME_INK2};line-height:1.7;">'
        f'{content_html}'
        f'</div></div></details>'
    )


def _aggregate_plans(ch_df: pd.DataFrame) -> pd.DataFrame:
    """按 Plan × Message 聚合单个渠道的数据。

    一张卡片 = 一个 Plan × 一条文案（Message）。
    同一文案按 Unit 拆分后投放（千人千面），Unit 不参与聚合。
    旧数据无 message_id 时退化为 (Plan, 消息标题)，等价于旧行为。

    Why 合并 Unit: 不合并会导致
      ① 一条文案按 Unit 数重复占榜（7/06 东北市场短信 7 个 Unit 占 7 个榜位）
      ② Unit 间 CTR 差异来自人群/落地页，不是文案差异，会污染内容排行
    Why 拆 Message: 一 Plan 多文案（实验/分时）每条文案是独立投放策略，必须各自一张卡。
    """
    agg_dict = {
        "Plan名称": "first",
        "预算owner": "first",
        "发送日期": "first",
        "触达成功": "sum",
        "点击人次": "sum",
        "订单GC": "sum",
        "消息标题": "first",
        "消息内容": "first",
    }
    # 综合评分：caller (render) 一般已 early-return，但单测直接调函数时可能缺列，保留守卫
    if "综合评分" in ch_df.columns:
        agg_dict["综合评分"] = "mean"
    if "订单Sales" in ch_df.columns:
        agg_dict["订单Sales"] = "sum"

    # 聚合键：新数据 (Plan, Message)，旧数据退化 (Plan, 消息标题)
    has_message = data_is_v2(ch_df)
    if has_message:
        keys = ["Plan ID", "Message ID"]
        # 预归一化 Unit ID（"[NULL]" / "" → NaN），groupby 后单独算 nunique + merge
        _normalize_unit_column(ch_df)
    else:
        keys = ["Plan ID", "消息标题"]

    plan_agg = ch_df.groupby(keys, dropna=False, as_index=False).agg(agg_dict)

    # Unit数：单独算（nunique _unit_norm）+ left merge（避免 pandas agg_dict 不支持 named agg）
    if has_message:
        unit_n = ch_df.groupby(keys, dropna=False)["_unit_norm"].nunique().reset_index(name="Unit数")
        plan_agg = plan_agg.merge(unit_n, on=keys, how="left")

    plan_agg = plan_agg[plan_agg["触达成功"] > 0]
    # 聚合后必须先求和再算率（CTR/GC 转化率），避免按行先算率再平均的精度坑
    return add_rate_metrics(plan_agg)


def _render_plan_cards(top_n: pd.DataFrame, ch: str, dim_id: str = "score", ai_results: dict = None):
    """Streamlit 渲染 6 卡片（左 3 高分，右 3 需提升），支持删除"""
    # 初始化删除列表
    if "deleted_plans" not in st.session_state:
        st.session_state["deleted_plans"] = set()

    # 过滤掉被删除的Plan
    deleted = st.session_state["deleted_plans"]
    filtered = top_n[~top_n["Plan ID"].isin(deleted)]

    # 高分 3 张（top_n 已经按当前维度 desc 排好序）
    top3 = filtered.head(3).reset_index(drop=True)

    # 需提升 3 张：先排除 top3 的 Plan ID，再从剩余池里按升序取前 3
    # 避免渠道 Plan 数 ≤ 6 时 bot3 与 top3 完全重叠
    # 二级 tie-break by "Plan ID" asc，与 handler 算 AI、_render_plan_cards、_export_channel_tabs 三端完全一致
    sort_col_map = {"score": "综合评分", "ctr": "CTR", "sales": "订单Sales"}
    sort_col = sort_col_map.get(dim_id, "综合评分")
    top_plan_ids = set(top3["Plan ID"])
    bot_pool = filtered[~filtered["Plan ID"].isin(top_plan_ids)]
    if sort_col in bot_pool.columns:
        bot3 = bot_pool.sort_values([sort_col, "Plan ID"], ascending=[True, True], na_position="last").head(3).reset_index(drop=True)
    else:
        bot3 = bot_pool.sort_values("Plan ID", ascending=True).head(3).reset_index(drop=True)

    if len(top3) == 0 and len(bot3) == 0:
        st.info("当前渠道没有可显示的 Plan")
        return

    # 两列布局：左 高分，右 需提升（每列用 border 容器，框必然包住卡片+按钮；
    # 旧实现用 st.markdown('<div>') ... st.markdown('</div>') 拆开的开/闭标签，
    # 中间的卡片和按钮会变成 div 的兄弟节点而非子节点，导致框只框住标题、卡片掉到框外）
    col_l, col_r = st.columns(2)

    with col_l:
        with st.container(border=True):
            st.markdown('<div class="section-subheader" style="margin:0 0 10px 0;">高分文案</div>', unsafe_allow_html=True)
            for i, (_, row) in enumerate(top3.iterrows(), 1):
                # 新数据（≥7/28 带 Message ID）key 跟 page.py:_build_items 对齐：PlanID_MsgID_ch_dim_tier
                msg_id = str(row.get("Message ID", "")).strip() if "Message ID" in row.index else ""
                key_pid = f"{row['Plan ID']}_{msg_id}" if msg_id else str(row["Plan ID"])
                ai_key = f"{key_pid}_{ch}_{dim_id}_top"
                ai = ai_results.get(ai_key) if ai_results else None
                plan_id = row['Plan ID']
                st.markdown(_plan_card_html(row, i, is_good=True, ai_result=ai), unsafe_allow_html=True)
                # 删除按钮 key 跟 ai_key 同步带 msg_id，一 Plan 多文案时 key 不冲突
                if st.button("移除", key=f"del_top_{key_pid}_{ch}_{dim_id}", help="移除此Plan"):
                    st.session_state["deleted_plans"].add(plan_id)
                    _purge_plan_ai(plan_id)
                    st.rerun()

    with col_r:
        with st.container(border=True):
            st.markdown('<div class="section-subheader" style="margin:0 0 10px 0;">需提升</div>', unsafe_allow_html=True)
            for i, (_, row) in enumerate(bot3.iterrows(), 1):
                # 新数据 key 跟 page.py:_build_items 对齐：PlanID_MsgID_ch_dim_tier
                msg_id = str(row.get("Message ID", "")).strip() if "Message ID" in row.index else ""
                key_pid = f"{row['Plan ID']}_{msg_id}" if msg_id else str(row["Plan ID"])
                ai_key = f"{key_pid}_{ch}_{dim_id}_bot"
                ai = ai_results.get(ai_key) if ai_results else None
                plan_id = row['Plan ID']
                st.markdown(_plan_card_html(row, i, is_good=False, ai_result=ai), unsafe_allow_html=True)
                # 删除按钮 key 跟 ai_key 同步带 msg_id，一 Plan 多文案时 key 不冲突
                if st.button("移除", key=f"del_bot_{key_pid}_{ch}_{dim_id}", help="移除此Plan"):
                    st.session_state["deleted_plans"].add(plan_id)
                    _purge_plan_ai(plan_id)
                    st.rerun()


def _export_plan_cards(top_n: pd.DataFrame, ch: str, dim_id: str = "score", ai_results: dict = None) -> str:
    """导出 HTML：6 卡片（左 3 高分，右 3 需提升），过滤掉被删除的Plan"""
    # 过滤掉被删除的Plan
    deleted = st.session_state.get("deleted_plans", set())
    filtered = top_n[~top_n["Plan ID"].isin(deleted)]

    top3 = filtered.head(3).reset_index(drop=True)
    sort_col_map = {"score": "综合评分", "ctr": "CTR", "sales": "订单Sales"}
    sort_col = sort_col_map.get(dim_id, "综合评分")
    # 与 handler 算 AI、_render_plan_cards 三端完全一致：bot3 从排除 top3 后的池里取
    top_plan_ids = set(top3["Plan ID"])
    bot_pool = filtered[~filtered["Plan ID"].isin(top_plan_ids)]
    if sort_col in bot_pool.columns:
        bot3 = bot_pool.sort_values([sort_col, "Plan ID"], ascending=[True, True], na_position="last").head(3).reset_index(drop=True)
    else:
        bot3 = bot_pool.sort_values("Plan ID", ascending=True).head(3).reset_index(drop=True)

    def _column(rows, label, is_good):
        # 套框：与 UI 一致的轻量卡片样式（border + 背景 + 圆角）
        html = (
            f'<div style="background:{THEME_PAPER};border:1px solid {THEME_LINE};'
            f'border-radius:{THEME_RADIUS_M};padding:12px;">'
            f'<div style="font-size:14px;font-weight:700;color:#1A1A1A;'
            f'margin:0 0 10px 0;padding-bottom:6px;border-bottom:1px solid {THEME_LINE};">{label}</div>'
        )
        tier = "top" if is_good else "bot"
        for i, (_, row) in enumerate(rows.iterrows(), 1):
            # 新数据 key 跟 page.py:_build_items 对齐：PlanID_MsgID_ch_dim_tier
            msg_id = str(row.get("Message ID", "")).strip() if "Message ID" in row.index else ""
            key_pid = f"{row['Plan ID']}_{msg_id}" if msg_id else str(row["Plan ID"])
            ai_key = f"{key_pid}_{ch}_{dim_id}_{tier}"
            ai = ai_results.get(ai_key) if ai_results else None
            html += _plan_card_html(row, i, is_good=is_good, ai_result=ai)
        html += '</div>'
        return html

    html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">'
    html += f'<div>{_column(top3, "高分文案", True)}</div>'
    html += f'<div>{_column(bot3, "需提升", False)}</div>'
    html += '</div>'
    return html


def _export_channel_tabs(ch: str, plan_agg: pd.DataFrame, ai_results: dict = None, ch_summary: dict = None) -> str:
    """导出 HTML：单个渠道的 3 个维度 tab 切换"""
    prefix = ch.replace(" ", "-").replace("/", "-")

    # 渠道总结
    summary_html = ""
    if ch_summary and "error" not in ch_summary:
        why_good = ch_summary.get("why_good", "")
        content_framework = ch_summary.get("content_framework", "")
        if why_good or content_framework:
            summary_html = f'<div style="background:{THEME_PAPER};border:1px solid {THEME_LINE};border-radius:{THEME_RADIUS_M};padding:16px;margin:12px 0;">'
            summary_html += f'<div style="font-size:13px;font-weight:700;color:{MCD_DARK_RED};margin-bottom:10px;">渠道总结</div>'
            if why_good:
                summary_html += (
                    f'<div style="margin-bottom:10px;">'
                    f'<div style="font-size:12px;font-weight:600;color:{THEME_INK2};margin-bottom:4px;">为什么好</div>'
                    f'<div style="font-size:12px;color:{THEME_INK};line-height:1.7;">{why_good}</div>'
                    f'</div>'
                )
            if content_framework:
                summary_html += (
                    f'<div>'
                    f'<div style="font-size:12px;font-weight:600;color:{THEME_INK2};margin-bottom:4px;">内容框架</div>'
                    f'<div style="font-size:13px;font-weight:700;color:{MCD_DARK_RED};">{content_framework}</div>'
                    f'</div>'
                )
            summary_html += '</div>'

    dims = [
        ("score", "综合评分", "综合评分"),
        ("ctr", "CTR", "CTR"),
        ("sales", "Sales", "订单Sales"),
    ]
    tabs_html = ""
    panels_html = ""
    for idx, (dim_id, label, sort_col) in enumerate(dims):
        checked = "checked" if idx == 0 else ""
        tabs_html += (
            f'<input type="radio" name="dim-{prefix}" id="dim-{prefix}-{dim_id}" {checked} class="plan-dim-input">'
            f'<label for="dim-{prefix}-{dim_id}" class="plan-tab-label">{label}</label>'
        )
        # 用完整 plan_agg（与 handler 算 AI、UI 渲染三端一致），_export_plan_cards 内部再 head(3)
        # 二级 tie-break by "Plan ID" asc，保证与 page.py:237 同算法，避免同 Sales 值时两端 Plan ID 顺序分歧
        if sort_col in plan_agg.columns:
            sorted_df = plan_agg.sort_values([sort_col, "Plan ID"], ascending=[False, True]).reset_index(drop=True)
        else:
            sorted_df = plan_agg.sort_values(["综合评分", "Plan ID"], ascending=[False, True]).reset_index(drop=True)
        panels_html += f'<div class="plan-dim-panel">{_export_plan_cards(sorted_df, ch, dim_id, ai_results)}</div>'
    return f'{summary_html}<div class="plan-dim-tabs">{tabs_html}{panels_html}</div>'


def _channel_summary_html(summary: dict) -> str:
    """生成渠道总结 HTML"""
    if not summary or "error" in summary:
        return ""

    why_good = summary.get("why_good", "")
    content_framework = summary.get("content_framework", "")

    if not why_good and not content_framework:
        return ""

    html = f'<div style="background:{THEME_PAPER};border:1px solid {THEME_LINE};border-radius:{THEME_RADIUS_M};padding:16px;margin:12px 0;">'
    html += f'<div style="font-size:13px;font-weight:700;color:{MCD_DARK_RED};margin-bottom:10px;">渠道总结</div>'

    if why_good:
        html += (
            f'<div style="margin-bottom:10px;">'
            f'<div style="font-size:12px;font-weight:600;color:{THEME_INK2};margin-bottom:4px;">为什么好</div>'
            f'<div style="font-size:12px;color:{THEME_INK};line-height:1.7;">{why_good}</div>'
            f'</div>'
        )

    if content_framework:
        html += (
            f'<div>'
            f'<div style="font-size:12px;font-weight:600;color:{THEME_INK2};margin-bottom:4px;">内容框架</div>'
            f'<div style="font-size:13px;font-weight:700;color:{MCD_DARK_RED};">{content_framework}</div>'
            f'</div>'
        )

    html += '</div>'
    return html


def render(df: pd.DataFrame, ai_results: dict = None, channel_summary: dict = None):
    """渲染内容分析层，返回 plan_html 供导出用"""

    st.markdown(section_header("内容分析", number=4, subtitle=""), unsafe_allow_html=True)

    if "综合评分" not in df.columns:
        st.warning("数据中缺少综合评分，请检查评分算法")
        return ""

    # 预处理：解析消息内容 JSON → 标题 + 正文
    if "消息内容" in df.columns:
        df = df.copy()
        parsed = df["消息内容"].apply(_parse_message_content)
        df["消息标题"] = parsed.apply(lambda x: x[0])
        df["消息内容"] = parsed.apply(lambda x: x[1])
    elif "消息标题" not in df.columns:
        df = df.copy()
        df["消息标题"] = ""
        df["消息内容"] = ""

    # ─── 第4部分排除规则（仅影响内容分析，不干预其他 section）────────
    # 调用方已在 page.py 把全量 df 传进来；这里就地 copy + mask 过滤，
    # 不影响 render_summary / render_operational / render_bu 的入参
    if _CONTENT_EXCLUDE_KWS:
        excl_mask = _content_exclusion_mask(df)
        n_excluded = int(excl_mask.sum())
        if n_excluded:
            df = df[~excl_mask].copy()
            st.caption(
                f"已按内容分析排除规则剔除 {n_excluded} 条 Plan"
                f"（礼品卡 / 入群礼 / 团餐，不影响其他板块）"
            )

    # 检测可用渠道（至少 2 条 Plan）
    available_channels = []
    for ch in PLAN_CHANNELS:
        ch_df = df[df["渠道"] == ch]
        if len(ch_df) >= 2:
            plan_agg = _aggregate_plans(ch_df)
            if len(plan_agg) >= 2:
                available_channels.append(ch)

    if not available_channels:
        st.info("当前筛选条件下没有足够的 Plan 数据进行分析")
        return ""

    # ─── 渠道 + 维度选择器（左右横排）+ 重置按钮 ─────────────
    col_ch, col_dim, col_reset = st.columns([2, 2, 1])
    with col_ch:
        selected_ch = st.radio("渠道", options=available_channels, index=0, horizontal=True, key="plan_ch")
    with col_dim:
        sort_dim = st.radio("排序", options=["综合评分", "CTR", "Sales"], index=0, horizontal=True, key="plan_dim")
    with col_reset:
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)  # 对齐
        if st.button("重置", help="恢复所有被移除的Plan"):
            st.session_state["deleted_plans"] = set()
            st.rerun()

    # ─── 渠道总结（在渠道筛选下方）──────────────────────────
    if channel_summary and selected_ch in channel_summary:
        summary_html = _channel_summary_html(channel_summary[selected_ch])
        if summary_html:
            st.markdown(summary_html, unsafe_allow_html=True)

    # 按选中维度排序
    ch_df = df[df["渠道"] == selected_ch].copy()
    plan_agg = _aggregate_plans(ch_df)

    # 确定维度ID
    dim_id_map = {"综合评分": "score", "CTR": "ctr", "Sales": "sales"}
    dim_id = dim_id_map.get(sort_dim, "score")

    if sort_dim == "综合评分":
        plan_agg = plan_agg.sort_values(["综合评分", "Plan ID"], ascending=[False, True])
    elif sort_dim == "CTR":
        plan_agg = plan_agg.sort_values(["CTR", "Plan ID"], ascending=[False, True])
    elif sort_dim == "Sales":
        if "订单Sales" in plan_agg.columns:
            plan_agg = plan_agg.sort_values(["订单Sales", "Plan ID"], ascending=[False, True])
        else:
            plan_agg = plan_agg.sort_values(["综合评分", "Plan ID"], ascending=[False, True])

    # 取完整 plan_agg 传给 render/export，确保删除后 bot3 也能从完整集合里回填
    top_n = plan_agg.reset_index(drop=True)

    # ─── Streamlit 显示 ──────────────────────────────────
    _render_plan_cards(top_n, selected_ch, dim_id, ai_results)

    # ─── 导出 HTML（渠道 tab + 维度 tab，扁平结构）──────────
    plan_html = ""
    ch_tabs = ""
    ch_panels = ""
    for idx, ch in enumerate(available_channels):
        ch_df_exp = df[df["渠道"] == ch].copy()
        plan_agg_exp = _aggregate_plans(ch_df_exp)
        checked = "checked" if idx == 0 else ""
        ch_tabs += (
            f'<input type="radio" name="plan-ch" id="plan-ch-{idx}" {checked} class="plan-ch-input">'
            f'<label for="plan-ch-{idx}" class="plan-tab-label">{ch}</label>'
        )
        ch_summary = channel_summary.get(ch) if channel_summary else None
        ch_panels += f'<div class="plan-ch-panel">{_export_channel_tabs(ch, plan_agg_exp, ai_results, ch_summary)}</div>'
    plan_html += f'<div class="plan-ch-tabs">{ch_tabs}{ch_panels}</div>'

    return plan_html
