# -*- coding: utf-8 -*-
"""渠道健康度（导出 HTML 用）

基期 = 现期之前所有（df 发送日期 < 现期最早）；现期 = 周日均
指标：每渠道「点击人次（周日均）+ CTR」各算 p5/p25/p50/p75/p95 分位数
颜色：pct_band 5 档（左偏 <p5 红/异常，<p25 黄/预警；正常区间 p25~p75 绿；右偏 >p75 黄/较高，>p95 红/较好）
样式：复刻 mcd-reach-trend kpi_card_with_bar 的五段分布条 + 现期值圆点
渠道范围：只渲染基期或现期任一有触达数据的渠道
"""
import numpy as np
import pandas as pd

from performance.config import (
    MCD_GREEN, MCD_GOLD, MCD_RED,
    THEME_PAPER, THEME_LINE, THEME_INK, THEME_INK2, THEME_MUTED,
)

GREEN = MCD_GREEN; YELLOW = MCD_GOLD; RED = MCD_RED
# 5 档分左右：指标越高越好，左侧（低）=异常/预警，右侧（高）=较好/较高
BAND_COLOR = {
    'low_bad':   RED,        # <p5   异常
    'low_warn':  YELLOW,     # p5~p25 预警
    'normal':    GREEN,      # p25~p75 正常
    'high_ok':   YELLOW,     # p75~p95 较高
    'high_good': RED,        # >p95   较好
}
BAND_LABEL = {
    'low_bad':   '异常',
    'low_warn':  '预警',
    'normal':    '正常',
    'high_ok':   '较高',
    'high_good': '较好',
}
CARD = THEME_PAPER; BORDER = THEME_LINE; TEXT = THEME_INK; TEXT_SUB = THEME_INK2; WEAK = THEME_MUTED
WEAK_BG = '#EDEDED'


def pct_band(val, p5, p25, p75, p95):
    # 指标越高越好：左偏 = 异常/预警，右偏 = 较好/较高，中间 = 正常
    if val < p5:
        return 'low_bad'
    if val < p25:
        return 'low_warn'
    if val > p95:
        return 'high_good'
    if val > p75:
        return 'high_ok'
    return 'normal'


def _fmt_num(v):
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    return f"{v:.0f}"


def _fmt_ctr(v):
    return f"{v:.3f}%"


def _bar_html(cur, p5, p25, p50, p75, p95, unit):
    full_min = p5 * 0.8
    full_max = p95 * 1.2
    span = full_max - full_min
    if span <= 0:
        pos = 50.0
        p5p, p25p, p50p, p75p, p95p = 10.0, 25.0, 50.0, 75.0, 90.0
    else:
        def _pct(v):
            return max(0.0, min(100.0, (v - full_min) / span * 100))
        pos = _pct(cur); p5p = _pct(p5); p25p = _pct(p25)
        p50p = _pct(p50); p75p = _pct(p75); p95p = _pct(p95)
    vc = BAND_COLOR[pct_band(cur, p5, p25, p75, p95)]
    fmt = _fmt_ctr if unit == '%' else _fmt_num
    tooltip = f"P5:{fmt(p5)} | P25:{fmt(p25)} | P50:{fmt(p50)} | P75:{fmt(p75)} | P95:{fmt(p95)}"
    return (
        f'<div title="{tooltip}" style="position:relative;height:6px;background:{WEAK_BG};border-radius:3px;overflow:visible;margin-top:6px;">'
        f'<div style="position:absolute;left:0%;width:{p5p:.1f}%;top:0;bottom:0;background:rgba(218,41,28,0.25);border-radius:3px 0 0 3px;"></div>'
        f'<div style="position:absolute;left:{p5p:.1f}%;width:{p25p - p5p:.1f}%;top:0;bottom:0;background:rgba(255,199,44,0.3);"></div>'
        f'<div style="position:absolute;left:{p25p:.1f}%;width:{p75p - p25p:.1f}%;top:0;bottom:0;background:rgba(0,160,74,0.25);"></div>'
        f'<div style="position:absolute;left:{p75p:.1f}%;width:{p95p - p75p:.1f}%;top:0;bottom:0;background:rgba(255,199,44,0.3);"></div>'
        f'<div style="position:absolute;left:{p95p:.1f}%;width:{100 - p95p:.1f}%;top:0;bottom:0;background:rgba(218,41,28,0.25);border-radius:0 3px 3px 0;"></div>'
        f'<div style="position:absolute;left:{pos:.1f}%;top:50%;transform:translate(-50%,-50%);width:10px;height:10px;background:{vc};border-radius:50%;border:1.5px solid {CARD};box-shadow:0 1px 3px rgba(0,0,0,0.2);z-index:2;"></div>'
        f'</div>'
    )


def _metric_row(label, m, unit, fmt):
    band = m['band']
    color = BAND_COLOR[band]
    lbl = BAND_LABEL[band]
    cur = m['cur']; mean = m['mean']
    delta = cur - mean
    dcolor = GREEN if delta > 0 else RED
    sign = '+' if delta > 0 else ('-' if delta < 0 else '')
    val_s = fmt(cur)
    if unit == '%':
        mean_s = f"{mean:.3f}%"; delta_s = f"{sign}{abs(delta):.3f}pp"
    else:
        mean_s = _fmt_num(mean); delta_s = sign + _fmt_num(abs(delta))
    return (
        f'<div style="margin-bottom:14px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;">'
        f'<span style="font-size:11px;font-weight:600;color:{TEXT_SUB};">{label}</span>'
        f'<span style="font-size:11px;color:{color};font-weight:600;">● {lbl}</span>'
        f'</div>'
        f'<div style="font-size:20px;font-weight:800;color:{TEXT};line-height:1.2;margin-top:2px;">{val_s}</div>'
        f'<div style="font-size:11px;color:{WEAK};margin-top:2px;">vs 基期日均 {mean_s} &nbsp;<span style="color:{dcolor};">{delta_s}</span></div>'
        f'{_bar_html(cur, m["p5"], m["p25"], m["p50"], m["p75"], m["p95"], unit)}'
        f'</div>'
    )


def _metric_dict(cur, series, mean):
    """series → p5/p25/p50/p75/p95 分位数 + mean/cur/band，供 _metric_row 用"""
    q = {v: float(series.quantile(v)) for v in (0.05, 0.25, 0.5, 0.75, 0.95)}
    return {'p5': q[0.05], 'p25': q[0.25], 'p50': q[0.5], 'p75': q[0.75], 'p95': q[0.95],
            'mean': mean, 'cur': cur,
            'band': pct_band(cur, q[0.05], q[0.25], q[0.75], q[0.95])}


def _daily_channel_ctr(df):
    """按 发送日期×渠道 聚合并补 CTR 列（点击/触达*100，除零填 0）"""
    daily = df.groupby(['发送日期', '渠道']).agg(
        点击人次=('点击人次', 'sum'), 触达成功=('触达成功', 'sum')).reset_index()
    daily['CTR'] = (daily['点击人次'] / daily['触达成功'].replace(0, np.nan) * 100).fillna(0)
    return daily


def render_channel_health(df: pd.DataFrame, raw_df: pd.DataFrame | None = None, channels: list | None = None,
                          start_date=None, end_date=None) -> str:
    """生成渠道健康度模块 HTML 片段（subheader + grid）。
    df: 现期 DataFrame（已按 start_date~end_date 过滤）
    raw_df: 完整历史 DataFrame；基期 = 发送日期 < start_date 的所有行
            （None / 空 / 无早于 start_date 数据 → 模块不渲染）
    channels: 渠道列表；None 则取 df 出现的渠道
    start_date / end_date: 现期日期范围（标题短格式显示用）
    """
    if df is None or df.empty or '发送日期' not in df.columns:
        return ''
    if '渠道' not in df.columns or '触达成功' not in df.columns or '点击人次' not in df.columns:
        return ''

    if channels is None:
        channels = sorted([ch for ch in df['渠道'].dropna().unique() if ch not in ('', '[NULL]')])

    # 拼接日期范围字符串（短格式 6/29-7/5，空时回退到占位文字）
    def _short_period(s, e):
        if not (s and e):
            return "现期" if not s else f"{s} 起"
        sm, sd = str(s).split("-")[1:] if "-" in str(s) else (None, None)
        em, ed = str(e).split("-")[1:] if "-" in str(e) else (None, None)
        if sm and em and sm == em:
            return f"{int(sm)}/{int(sd)}-{int(ed)}"
        return f"{int(sm) if sm else s}/{int(sd) if sd else ''}-{int(em) if em else e}/{int(ed) if ed else ''}"

    cur_period = _short_period(start_date, end_date) if start_date and end_date else "现期"
    # 基期 = 现期之前所有历史（发送日期 < start_date），分位才有意义
    if raw_df is not None and not raw_df.empty and '发送日期' in raw_df.columns and start_date is not None:
        send_dates = raw_df['发送日期'].dt.date          # 整列物化一次，过滤与 min/max 复用
        base = raw_df[send_dates < start_date]
        if not base.empty:
            base_period = _short_period(base['发送日期'].min().date(), base['发送日期'].max().date())
        else:
            base_period = '基期（无历史）'
    else:
        base = None
        base_period = '基期'
    click_label = f'点击人次（{cur_period} 日均）'
    section_title = f'渠道健康度（{cur_period} vs {base_period} 分位）'

    n_cur = int(df['发送日期'].nunique()) or 1
    base_daily = _daily_channel_ctr(base) if (base is not None and len(base) > 0) else None

    cur_daily = _daily_channel_ctr(df)

    cards = []
    for ch in channels:
        sub_cur = cur_daily[cur_daily['渠道'] == ch]
        if sub_cur.empty:
            continue
        click_total = float(sub_cur['点击人次'].sum())
        reach_total = float(sub_cur['触达成功'].sum())
        cur_click_daily = click_total / n_cur
        cur_ctr = click_total / reach_total * 100 if reach_total > 0 else 0

        if base_daily is None:
            continue
        sub_base = base_daily[base_daily['渠道'] == ch]
        if len(sub_base) < 3:
            continue

        click_mean = float(sub_base['点击人次'].mean())
        ctr_mean = float(sub_base['点击人次'].sum() / sub_base['触达成功'].sum() * 100) if sub_base['触达成功'].sum() > 0 else 0

        click_m = _metric_dict(cur_click_daily, sub_base['点击人次'], click_mean)
        ctr_m = _metric_dict(cur_ctr, sub_base['CTR'], ctr_mean)

        click_row = _metric_row(click_label, click_m, '', _fmt_num)
        ctr_row = _metric_row('CTR', ctr_m, '%', _fmt_ctr)
        card = (
            f'<div style="background:{CARD};border:1px solid {BORDER};border-radius:10px;padding:14px 16px;">'
            f'<div style="font-size:13px;font-weight:700;color:{TEXT};margin-bottom:12px;border-bottom:1px solid {BORDER};padding-bottom:8px;">{ch}</div>'
            f'{click_row}{ctr_row}'
            f'</div>'
        )
        cards.append(card)

    if not cards:
        return ''

    return (
        f'<div class="section-subheader">{section_title}</div>'
        f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px;">{"".join(cards)}</div>'
    )
