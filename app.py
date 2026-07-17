"""
app.py - CNN Weekly Suite 统一入口
一个应用，两个视角：周度复盘（Performance）/ 应急补量（Emergency）。
上传一次数据，两模式共用；各模式各自导出独立 HTML。
"""
from pathlib import Path
from types import SimpleNamespace

import streamlit as st

from shared.data import read_data, read_dau_sheet
import performance.page as perf_page
import emergency.page as emerg_page


@st.cache_data(show_spinner=False)
def _load_data(file_bytes: bytes, filename: str):
    """解析上传文件为 (raw_df, dau_df)，按文件内容缓存，切换模式不重复解析。"""
    shim = SimpleNamespace(name=filename)
    raw_df = read_data(shim, file_bytes=file_bytes)
    dau_df = None
    if filename.lower().endswith((".xlsx", ".xls")):
        dau_df = read_dau_sheet(file_bytes)  # 第二个 sheet：按天去重 DAU
    return raw_df, dau_df


def main():
    favicon = Path(__file__).parent / "assets" / "favicon.png"
    st.set_page_config(
        page_title="CNN Weekly Suite",
        page_icon=str(favicon) if favicon.exists() else "M",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # ─── 侧边栏：模式切换 + 统一上传 ───────────────────────
    with st.sidebar:
        st.markdown("### CNN Weekly Suite")
        mode = st.radio(
            "View",
            ["Performance", "Emergency"],
            index=0,
            help="Performance＝周度评分 / AI 分析；Emergency＝看 DAU Gap 决定补量",
        )
        st.markdown("---")
        st.markdown("### 数据设置")
        uploaded = st.file_uploader(
            "上传 Excel / CSV",
            type=["xlsx", "xls", "csv"],
            help="两个视角共用同一份数据（Sheet1 Plan 明细 + Sheet2 去重 DAU）",
        )

    # ─── 统一读取数据（两模式共用）────────────────────────
    raw_df, dau_df = None, None
    if uploaded is not None:
        try:
            file_bytes = uploaded.read()
            raw_df, dau_df = _load_data(file_bytes, uploaded.name)
        except Exception as e:
            st.error(f"数据读取失败：{e}")
            return

    # ─── 按模式分派 ───────────────────────────────────────
    if mode == "Performance":
        perf_page.render_page(raw_df, dau_df)
    else:
        emerg_page.render_page(raw_df, dau_df)


if __name__ == "__main__":
    main()
