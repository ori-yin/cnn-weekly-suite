"""
tab_bu.py - 第三层：BU 分析
按预算 owner 聚合，不拆 AARR/常规
"""

import streamlit as st
import pandas as pd
from performance.config import MCD_DARK_RED, MCD_RED, MCD_GREEN, THEME_INK, THEME_INK2, THEME_MUTED, THEME_PAPER, THEME_LINE, THEME_ROW_ALT, THEME_RADIUS_M
from performance.components import section_header, insight_block
from performance.tabs.tab_plan import parse_message_content


# Plan 计划类型 → 显示文案（中文简写）
_PT_DISPLAY = {
    "AARRPlan": "AARR",
    "常规Plan": "常规",
    "On-demand": "按需",
    "Responsive": "响应",
}


def _format_plan_type(values) -> str:
    """聚合列的去重取值，转中文短名后用 / 分隔。空 = 破折号。"""
    seen = []
    for v in values:
        if pd.isna(v) or v == "":
            continue
        s = str(v)
        if s not in seen:
            seen.append(s)
    if not seen:
        return "—"
    return " / ".join(_PT_DISPLAY.get(s, s) for s in seen)


def _format_channels(values) -> str:
    """聚合列的渠道去重，用 · 分隔；保留原始渠道名（已短）。空 = 破折号。"""
    seen = []
    for v in values:
        if pd.isna(v) or v == "":
            continue
        s = str(v)
        if s not in seen:
            seen.append(s)
    return " · ".join(seen) if seen else "—"


def _compute_bu_metrics(df: pd.DataFrame) -> dict:
    """计算 BU 的核心指标"""
    return {
        "Plan数": df["Plan ID"].nunique() if "Plan ID" in df.columns else len(df),
        "触达成功": int(df["触达成功"].sum()),
        "点击人次": int(df["点击人次"].sum()),
        "CTR": df["点击人次"].sum() / df["触达成功"].sum() * 100 if df["触达成功"].sum() > 0 else 0,
        "订单GC": int(df["订单GC"].sum()),
        "GC转化率": df["订单GC"].sum() / df["点击人次"].sum() * 100 if df["点击人次"].sum() > 0 else 0,
        "订单Sales": round(df["订单Sales"].sum(), 2) if "订单Sales" in df.columns else 0,
    }


def _prior_metrics_by_bu(prior_df: pd.DataFrame, n_days: int = 1) -> dict:
    """按 BU 聚合上周 CTR + 日均触达，返回 {BU: {ctr, reach_daily}}；过滤无效 BU 名。
    唯一的「上周 BU 基线」来源；表格环比列用 ctr、BU AI 解读额外用 reach_daily。"""
    out = {}
    if prior_df is None or prior_df.empty:
        return out
    for bu, g in prior_df.groupby("预算owner"):
        if pd.isna(bu) or bu == "[NULL]" or bu == "":
            continue
        reach = g["触达成功"].sum()
        clicks = g["点击人次"].sum()
        if reach > 0:
            out[bu] = {
                "ctr": clicks / reach * 100,
                "reach_daily": reach / n_days if n_days > 0 else 0,
            }
    return out


def _prior_ctr_by_bu(prior_df: pd.DataFrame) -> dict:
    """按 BU 聚合上周 CTR（百分比单位），返回 {BU: ctr_pct}；表格环比列用。"""
    return {bu: m["ctr"] for bu, m in _prior_metrics_by_bu(prior_df).items()}


def _ctr_delta_cell(curr_ctr: float, prior_ctr) -> str:
    """CTR 环比 cell HTML。delta 单位 = 百分点（pp）。绿涨红跌。"""
    if prior_ctr is None:
        return '<span style="color:#999;">—</span>'
    delta = curr_ctr - prior_ctr
    if abs(delta) < 0.005:
        return f'<span style="color:{THEME_MUTED};">{delta:+.2f}pp</span>'
    if delta > 0:
        return f'<span style="color:{MCD_GREEN};font-weight:700;">▲ {delta:.2f}pp</span>'
    return f'<span style="color:{MCD_RED};font-weight:700;">▼ {abs(delta):.2f}pp</span>'


def _bu_summary_segments_html(bu_summary: dict) -> str:
    """BU AI 解读段内部 HTML（不含外层 border 容器）。空字符串 = 不渲染。
    被 UI 的 st.container(border=True) 和导出 HTML 外层 div 两处复用。"""
    if not bu_summary:
        return ""
    if "error" in bu_summary:
        return (
            f'<div style="font-size:13px;font-weight:700;color:{MCD_DARK_RED};margin-bottom:8px;">BU AI 解读</div>'
            f'<div style="font-size:12px;color:#c00;line-height:1.7;">{bu_summary["error"]}</div>'
        )
    overview = bu_summary.get("overview", "")
    risers = bu_summary.get("risers", "")
    fallers = bu_summary.get("fallers", "")
    if not (overview or risers or fallers):
        return ""

    html = f'<div style="font-size:13px;font-weight:700;color:{MCD_DARK_RED};margin-bottom:10px;">BU AI 解读</div>'
    if overview:
        html += (
            f'<div style="margin-bottom:10px;">'
            f'<div style="font-size:12px;font-weight:600;color:{THEME_INK2};margin-bottom:4px;">整体趋势</div>'
            f'<div style="font-size:12px;color:{THEME_INK};line-height:1.7;">{overview}</div>'
            f'</div>'
        )
    if risers:
        html += (
            f'<div style="margin-bottom:10px;">'
            f'<div style="font-size:12px;font-weight:600;color:{MCD_GREEN};margin-bottom:4px;">上涨关注 BU</div>'
            f'<div style="font-size:12px;color:{THEME_INK};line-height:1.7;">{risers}</div>'
            f'</div>'
        )
    if fallers:
        html += (
            f'<div>'
            f'<div style="font-size:12px;font-weight:600;color:{MCD_RED};margin-bottom:4px;">下跌关注 BU</div>'
            f'<div style="font-size:12px;color:{THEME_INK};line-height:1.7;">{fallers}</div>'
            f'</div>'
        )
    return html


def render(df: pd.DataFrame, prior_df: pd.DataFrame | None = None, bu_summary: dict = None):
    """渲染 BU 分析层。prior_df 若提供则增加 CTR (环比) 列；bu_summary 提供则在总览表下方加 AI 解读块。"""

    st.markdown(section_header("BU 分析", number=3, subtitle=""), unsafe_allow_html=True)

    # 初始化 session_state.deleted_plans（与 tab_plan 一致）
    if "deleted_plans" not in st.session_state:
        st.session_state["deleted_plans"] = set()
    deleted_plans = st.session_state["deleted_plans"]

    # 按 BU 聚合
    bu_groups = df.groupby("预算owner")
    bu_rows = []

    for bu, bu_df in bu_groups:
        if pd.isna(bu) or bu == "[NULL]" or bu == "":
            continue
        m = _compute_bu_metrics(bu_df)
        bu_rows.append({"BU": bu, **m})

    if not bu_rows:
        st.info("当前筛选条件下没有 BU 数据")
        return

    bu_df = pd.DataFrame(bu_rows)
    bu_df = bu_df.sort_values("点击人次", ascending=False).reset_index(drop=True)
    days_count = df["发送日期"].dt.date.nunique()

    # 上周 CTR（按 BU），供环比列使用
    prior_ctr_map = _prior_ctr_by_bu(prior_df)
    show_wow = bool(prior_ctr_map)

    # ─── BU 综合评分 ────────────────────────────────────────
    # 触达归一化（幂律压缩）
    reach_max = bu_df["触达成功"].max()
    if reach_max > 0:
        bu_df["触达_norm"] = (bu_df["触达成功"] / reach_max) ** 0.3 * 100
    else:
        bu_df["触达_norm"] = 0

    # CTR 归一化（Q3 阈值）
    ctr_q3 = bu_df["CTR"].quantile(0.75)
    if ctr_q3 > 0:
        bu_df["CTR_norm"] = bu_df["CTR"].apply(lambda x: 100 if x >= ctr_q3 else 100 * (x / ctr_q3) ** 1.5)
    else:
        bu_df["CTR_norm"] = 50

    # GC转化率 归一化（Q3 阈值）
    gc_q3 = bu_df["GC转化率"].quantile(0.75)
    if gc_q3 > 0:
        bu_df["GC_norm"] = bu_df["GC转化率"].apply(lambda x: 100 if x >= gc_q3 else 100 * (x / gc_q3) ** 1.5)
    else:
        bu_df["GC_norm"] = 50

    # 置信度惩罚
    def _penalty(reach):
        if reach < 100: return 0.1
        if reach < 500: return 0.3
        if reach < 1000: return 0.5
        if reach < 5000: return 0.8
        return 1.0

    bu_df["惩罚"] = bu_df["触达成功"].apply(_penalty)
    bu_df["评分"] = (bu_df["CTR_norm"] * 0.50 + bu_df["触达_norm"] * 0.25 + bu_df["GC_norm"] * 0.25) * bu_df["惩罚"]
    bu_df["评分"] = bu_df["评分"].round(1)

    # IT-Traffic 是裁判部门，只在 BU 总览表 + 详情浮层隐藏（排行榜照常展示）
    # 聚合数据 bu_df 完整保留，不影响排行榜与上层计算
    _HIDDEN_BUS = ("IT-Traffic",)
    display_bu_df = bu_df[~bu_df["BU"].isin(_HIDDEN_BUS)].reset_index(drop=True)

    # ─── BU 排行榜（4 个榜单横排）──────────────────────────
    st.markdown('<div class="section-subheader">BU 排行榜</div>', unsafe_allow_html=True)

    def _fmt_val(val, unit=""):
        if unit == "%":
            return f"{val:.2f}%"
        if val >= 1_000_000:
            return f"{val/1_000_000:.1f}M"
        if val >= 1_000:
            return f"{val/1_000:.1f}K"
        return f"{val:,.0f}"

    def _rank_html(title, sorted_df, metric_col, unit=""):
        medal_bg = ["#FFF8E1", "#F5F5F5", "#FBE9E7"]
        medal_icon = ["🥇", "🥈", "🥉"]
        rows = ""
        for i, (_, row) in enumerate(sorted_df.head(5).iterrows()):
            bg = medal_bg[i] if i < 3 else "#fff"
            icon = medal_icon[i] if i < 3 else f'<span style="color:{THEME_MUTED};font-size:11px;">{i+1}.</span>'
            val = _fmt_val(row[metric_col], unit)
            rows += (
                f'<div style="display:flex;align-items:center;gap:8px;padding:6px 10px;background:{bg};border-radius:6px;margin-bottom:3px;">'
                f'<span style="width:22px;text-align:center;flex-shrink:0;">{icon}</span>'
                f'<span style="flex:1;font-size:12px;font-weight:600;color:{THEME_INK};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{row["BU"]}</span>'
                f'<span style="font-size:12px;color:{THEME_INK2};font-variant-numeric:tabular-nums;flex-shrink:0;">{val}</span>'
                f'</div>'
            )
        return (
            f'<div style="background:{THEME_PAPER};border:1px solid {THEME_LINE};border-radius:{THEME_RADIUS_M};padding:12px;">'
            f'<div style="font-size:13px;font-weight:700;color:{MCD_DARK_RED};margin-bottom:8px;">{title}</div>'
            f'{rows}</div>'
        )

    rank_plan = bu_df.sort_values("Plan数", ascending=False)
    rank_reach = bu_df.sort_values("触达成功", ascending=False)
    rank_ctr = bu_df[bu_df["触达成功"] >= 10000].sort_values("CTR", ascending=False)
    rank_sales = bu_df.sort_values("订单Sales", ascending=False)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(_rank_html("Plan数 TOP5", rank_plan, "Plan数"), unsafe_allow_html=True)
    with c2:
        st.markdown(_rank_html("触达成功 TOP5", rank_reach, "触达成功"), unsafe_allow_html=True)
    with c3:
        st.markdown(_rank_html("CTR TOP5", rank_ctr, "CTR", unit="%"), unsafe_allow_html=True)
    with c4:
        st.markdown(_rank_html("Sales TOP5", rank_sales, "订单Sales"), unsafe_allow_html=True)

    # 排行榜 HTML（供导出）
    bu_rank_html = (
        '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">'
        + _rank_html("Plan数 TOP5", rank_plan, "Plan数")
        + _rank_html("触达成功 TOP5", rank_reach, "触达成功")
        + _rank_html("CTR TOP5", rank_ctr, "CTR", unit="%")
        + _rank_html("Sales TOP5", rank_sales, "订单Sales")
        + '</div>'
    )

    # ─── BU 总览表（构建一次，显示+导出共用）─────────────────
    st.markdown('<div class="section-subheader">BU 总览</div>', unsafe_allow_html=True)

    TH = f"background:#1A1A1A;color:#fff;padding:10px 12px;font-weight:700;font-size:12px;"
    TD = f"padding:8px 12px;border-bottom:1px solid #e0e0e0;"
    TD_EVEN = f"padding:8px 12px;border-bottom:1px solid #e0e0e0;background:{THEME_ROW_ALT};"

    # 注入 :target 浮层 CSS（与 BU 表同页：点 BU 名 → 屏幕中央弹出浮层，不滚动）
    st.markdown(f"""
<style>
.bu-link {{ color: inherit; text-decoration: none; border-bottom: 1px dashed {MCD_DARK_RED}; cursor: pointer; }}
.bu-link:hover {{ background: #F5F5F5; color: {MCD_RED} !important; }}
.bu-pop {{ display: none; position: fixed; inset: 0; z-index: 9999; background: rgba(0,0,0,.35); align-items: center; justify-content: center; }}
.bu-pop:target {{ display: flex; }}
.bu-pop-card {{ background: {THEME_PAPER}; border: 1px solid {THEME_LINE}; border-radius: 12px; padding: 20px 24px; max-width: 960px; width: 90vw; max-height: 80vh; overflow: auto; box-shadow: 0 8px 32px rgba(0,0,0,.25); }}
.bu-pop-card .pop-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid {THEME_LINE}; }}
.bu-pop-card .pop-close {{ text-decoration: none; color: #999; font-size: 20px; padding: 0 8px; line-height: 1; }}
.bu-pop-card .pop-close:hover {{ color: {MCD_RED}; }}
</style>
""", unsafe_allow_html=True)

    rows_html = ""
    bus_with_sub = []
    for i, (_, row) in enumerate(display_bu_df.iterrows()):
        td_style = TD_EVEN if i % 2 == 1 else TD
        d = days_count if days_count > 0 else 1
        wow_cell = _ctr_delta_cell(row["CTR"], prior_ctr_map.get(row["BU"])) if show_wow else ""
        # BU 名 cell：包 <a href="#bu-pop-X"> 锚链，点 → URL hash 变 → :target 命中 → 浮层显示
        rows_html += (
            f"<tr>"
            f"<td style='{td_style}font-weight:600;'>"
            f"<a href='#bu-pop-{row['BU']}' class='bu-link'>{row['BU']}</a>"
            f"</td>"
            f"<td style='{td_style}text-align:right;'>{row['Plan数']}</td>"
            f"<td style='{td_style}text-align:right;'>{int(row['触达成功'] / d):,}</td>"
            f"<td style='{td_style}text-align:right;'>{int(row['点击人次'] / d):,}</td>"
            f"<td style='{td_style}text-align:right;'>{row['CTR']:.2f}%</td>"
            + (f"<td style='{td_style}text-align:right;'>{wow_cell}</td>" if show_wow else "")
            + f"<td style='{td_style}text-align:right;'>{int(row['订单GC'] / d):,}</td>"
            f"<td style='{td_style}text-align:right;'>{row['GC转化率']:.1f}%</td>"
            f"<td style='{td_style}text-align:right;'>{row['订单Sales'] / d:,.2f}</td>"
            f"<td style='{td_style}text-align:right;'>{row['评分']:.1f}</td>"
            f"</tr>"
        )
        bus_with_sub.append((row["BU"], row["Plan数"]))

    bu_table_html = (
        f'<table id="bu-table-top" style="width:100%;border-collapse:collapse;font-size:13px;background:{THEME_PAPER};border-radius:9px;overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,.04);">'
        f'<thead><tr>'
        f'<th style="{TH}text-align:left;">BU</th>'
        f'<th style="{TH}text-align:right;">Plan数</th>'
        f'<th style="{TH}text-align:right;">触达成功（日均）</th>'
        f'<th style="{TH}text-align:right;">点击人次（日均）</th>'
        f'<th style="{TH}text-align:right;">CTR</th>'
        + (f'<th style="{TH}text-align:right;">CTR (环比)</th>' if show_wow else "")
        + f'<th style="{TH}text-align:right;">订单GC（日均）</th>'
        f'<th style="{TH}text-align:right;">GC转化率</th>'
        f'<th style="{TH}text-align:right;">订单Sales（日均）</th>'
        f'<th style="{TH}text-align:right;">评分</th>'
        f'</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table>'
    )
    # ─── BU 详情浮层（每个有数据 BU 一个 div，靠 :target 触发显示）────
    # 纯 CSS 实现：URL hash 变 #bu-pop-X → 该 div :target 命中 → display:flex 居中弹出
    # 关闭：点 ✕ 跳 # 清空 hash。拼到 bu_table_html 末尾 → UI 一次渲染 + 导出 HTML 同步含浮层
    popover_layers = []
    for bu_name, n_plan in bus_with_sub:
        bu_sub_df = df[df["预算owner"] == bu_name] if "预算owner" in df.columns else pd.DataFrame()
        # BU 详情浮层显示该 BU 的全部 Plan（不被内容分析 的"删除"操作影响）
        plan_rows = _aggregate_bu_plans(bu_sub_df)
        popover_layers.append(
            f'<div id="bu-pop-{bu_name}" class="bu-pop">'
            f'<div class="bu-pop-card">'
            f'<div class="pop-head">'
            f'<div style="font-size:15px;font-weight:700;color:{MCD_DARK_RED};">📊 {bu_name} 发送明细（{len(plan_rows)} 个 Plan）</div>'
            f'<a href="#bu-table-top" class="pop-close" title="关闭">✕</a>'
            f'</div>'
            + _render_plan_rows_html(plan_rows) +
            f'</div></div>'
        )
    bu_table_html += "".join(popover_layers)
    st.markdown(bu_table_html, unsafe_allow_html=True)

    # ─── BU AI 解读（BU 总览表下方，border 容器装）──────────────
    # UI 用 st.container(border=True) 真容器；导出 HTML 不经 Streamlit，单独 div+border 包装。
    # 两处复用 _bu_summary_segments_html，内容相同。bu_summary 为 falsy 时不显示。
    bu_summary_export = ""
    if bu_summary:
        with st.container(border=True):
            st.markdown(_bu_summary_segments_html(bu_summary), unsafe_allow_html=True)
        bu_summary_export = (
            f'<div style="background:{THEME_PAPER};border:1px solid {THEME_LINE};'
            f'border-radius:{THEME_RADIUS_M};padding:16px;margin-top:16px;">'
            + _bu_summary_segments_html(bu_summary)
            + '</div>'
        )

    # ─── 本板块洞察（BU 总览表下面）────────────────────
    bu_insight_html = insight_block("insight_bu", label="BU 分析洞察")

    return [], bu_rank_html + bu_table_html + bu_summary_export + bu_insight_html


# ─── BU 发送明细（嵌进 BU 表每行，作为 <details> 展开子表）────

def _aggregate_bu_plans(bu_df: pd.DataFrame) -> list:
    """单个 BU 的 df 按 Plan × Message 聚合，1 Plan × 1 文案 1 行，按 CTR 降序。
    计划类型 / 渠道多值时拼接为单一展示串（_format_*）。
    新数据按 (Plan, Message) 拆，旧数据退化 (Plan)。"""
    if bu_df is None or bu_df.empty:
        return []
    agg_dict = {
        "消息内容": "first",
        "预算owner": "first",
        "发送日期": "first",
        "触达成功": "sum",
        "点击人次": "sum",
        "订单GC": "sum",
        "计划类型": lambda s: _format_plan_type(s.tolist()),
    }
    if "订单Sales" in bu_df.columns:
        agg_dict["订单Sales"] = "sum"
    if "渠道" in bu_df.columns:
        agg_dict["渠道"] = lambda s: _format_channels(s.tolist())

    # 聚合键：新数据 (Plan, Message)，旧数据退化 (Plan)
    has_message = "Message ID" in bu_df.columns and bu_df["Message ID"].notna().any()
    if has_message:
        keys = ["Plan ID", "Message ID"]
        # Unit 数：nunique，忽略 NaN 和 "[NULL]" 占位符
        if "Unit ID" in bu_df.columns:
            agg_dict["Unit ID"] = lambda s: s.dropna().loc[lambda x: ~x.astype(str).isin(("[NULL]", ""))].nunique()
    else:
        keys = ["Plan ID"]

    plan_agg = bu_df.groupby(keys, dropna=False, as_index=False).agg(agg_dict)
    # rename Unit ID -> Unit数（仅新数据加过这列）
    if has_message and "Unit ID" in plan_agg.columns:
        plan_agg = plan_agg.rename(columns={"Unit ID": "Unit数"})
    parsed = plan_agg["消息内容"].apply(parse_message_content)
    plan_agg["消息标题"] = parsed.apply(lambda x: x[0])
    plan_agg["消息内容"] = parsed.apply(lambda x: x[1])
    # 聚合后必须先求和再算率
    plan_agg["CTR"] = plan_agg.apply(
        lambda r: r["点击人次"] / r["触达成功"] * 100 if r["触达成功"] > 0 else 0,
        axis=1,
    )
    return plan_agg.sort_values("CTR", ascending=False).reset_index(drop=True).to_dict("records")


def _render_plan_rows_html(plan_rows: list) -> str:
    """单 BU 的 Plan 明细子表 HTML（嵌进浮层）。7 列 + 表头：标题 / 计划类型 / 渠道 / 正文 / 触达 / 点击 / CTR。
    标题与正文完整展示，不截断。"""
    if not plan_rows:
        return '<div style="padding:10px 16px;color:#999;font-size:12px;">本周无发送</div>'
    rows_html = ""
    for row in plan_rows:
        title = str(row.get("消息标题") or "—")
        text = str(row.get("消息内容") or "—")
        plan_type = str(row.get("计划类型") or "—")
        channel = str(row.get("渠道") or "—")
        reach = int(row.get("触达成功", 0) or 0)
        clicks = int(row.get("点击人次", 0) or 0)
        ctr = row.get("CTR", 0) or 0
        rows_html += (
            f'<tr>'
            f'<td style="padding:6px 8px;border-bottom:1px solid {THEME_LINE};color:{THEME_INK2};white-space:nowrap;">{channel}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid {THEME_LINE};color:{THEME_INK2};white-space:nowrap;">{plan_type}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid {THEME_LINE};font-weight:600;word-break:break-word;white-space:pre-wrap;">{title}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid {THEME_LINE};color:{THEME_INK2};word-break:break-word;white-space:pre-wrap;">{text}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid {THEME_LINE};text-align:right;">{reach:,}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid {THEME_LINE};text-align:right;">{clicks:,}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid {THEME_LINE};text-align:right;font-weight:700;">{ctr:.2f}%</td>'
            f'</tr>'
        )
    return (
        f'<table class="bu-plan-table" style="width:100%;margin:8px 0 4px;font-size:12px;border-collapse:collapse;table-layout:auto;">'
        f'<thead><tr style="background:#F5F5F5;">'
        f'<th style="text-align:left;padding:6px 8px;border-bottom:1px solid {THEME_LINE};">渠道</th>'
        f'<th style="text-align:left;padding:6px 8px;border-bottom:1px solid {THEME_LINE};">计划类型</th>'
        f'<th style="text-align:left;padding:6px 8px;border-bottom:1px solid {THEME_LINE};">标题</th>'
        f'<th style="text-align:left;padding:6px 8px;border-bottom:1px solid {THEME_LINE};">正文</th>'
        f'<th style="text-align:right;padding:6px 8px;border-bottom:1px solid {THEME_LINE};">触达</th>'
        f'<th style="text-align:right;padding:6px 8px;border-bottom:1px solid {THEME_LINE};">点击</th>'
        f'<th style="text-align:right;padding:6px 8px;border-bottom:1px solid {THEME_LINE};">CTR</th>'
        f'</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table>'
    )
