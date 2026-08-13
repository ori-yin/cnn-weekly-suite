"""
scoring.py - CNN Performance Weekly：综合评分算法
参考 mcd-content-rank 的评分体系
"""

import numpy as np
import pandas as pd
from performance.config import (
    CTR_THRESHOLDS, CVR_THRESHOLDS,
    CTR_UNKNOWN_THRESHOLD, CVR_UNKNOWN_THRESHOLD,
    SCORING_EXP, W_REACH, W_CTR, W_CVR,
    CONFIDENCE_THRESHOLDS, CONFIDENCE_DEFAULT,
)


def _confidence_penalty(reach) -> np.ndarray:
    """置信度惩罚：触达规模越小，惩罚越重（向量化版：返回与 reach 等长的 ndarray）"""
    out = np.full(len(reach), CONFIDENCE_DEFAULT, dtype=float)
    for threshold, penalty in sorted(CONFIDENCE_THRESHOLDS, reverse=True):
        out = np.where(reach < threshold, penalty, out)
    out = np.where((reach <= 0) | np.isnan(reach), 0.0, out)
    return out


def _reach_score(reach, max_reach: float) -> np.ndarray:
    """触达规模得分：幂次归一化（向量化）"""
    if max_reach <= 0:
        return np.zeros(len(reach))
    safe = np.where((reach > 0) & ~np.isnan(reach), reach, 0.0)
    return 100.0 * (safe / max_reach) ** 0.3


def _piecewise_score_arr(value, threshold: np.ndarray, exp: float = SCORING_EXP) -> np.ndarray:
    """分段评分向量化版：threshold 是与 value 等长的 ndarray"""
    valid = (threshold > 0) & (value >= 0) & ~np.isnan(value)
    base = np.where(valid, value / np.where(threshold > 0, threshold, 1.0), 0.0) ** exp
    return np.where(valid & (value >= threshold), 100.0, 100.0 * base)


def compute_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    为每个 Plan 计算综合评分（向量化版）。

    输入 df 需包含：渠道、触达成功、点击人次、点击后下单人次
    输出新增列：CTR得分、下单转化得分、触达得分、综合评分
    """
    df = df.copy()

    max_reach = df["触达成功"].max() if len(df) > 0 else 1
    if max_reach <= 0:
        max_reach = 1

    channels = df.get("渠道", pd.Series([""] * len(df))).fillna("")
    ctr_thr = channels.map(CTR_THRESHOLDS).fillna(CTR_UNKNOWN_THRESHOLD).to_numpy(dtype=float)
    cvr_thr = channels.map(CVR_THRESHOLDS).fillna(CVR_UNKNOWN_THRESHOLD).to_numpy(dtype=float)

    ctr = df.get("CTR", pd.Series(np.zeros(len(df)))).to_numpy(dtype=float)
    cvr_rate = df.get("下单转化率", pd.Series(np.zeros(len(df)))).to_numpy(dtype=float)
    reach = df["触达成功"].to_numpy(dtype=float)

    ctr_score = _piecewise_score_arr(ctr, ctr_thr)
    cvr_score = _piecewise_score_arr(cvr_rate, cvr_thr)
    reach_score = _reach_score(reach, max_reach)
    penalty = _confidence_penalty(reach)

    raw = W_REACH * reach_score + W_CTR * ctr_score + W_CVR * cvr_score
    final = raw * penalty

    df["触达得分"] = np.round(reach_score, 1)
    df["CTR得分"] = np.round(ctr_score, 1)
    df["下单转化得分"] = np.round(cvr_score, 1)
    df["综合评分"] = np.round(final, 1)

    return df
