"""
shared/footer.py - 页面底部部门版权条（全宽固定，与 header 对齐）

render_footer() 用与 shared/header.py 同样的 JS 注入方式（插入 parent.body），
让 footer 跟 header 一样 position: fixed 全窗口宽度，避免 iframe 限宽。
"""
import json
import streamlit.components.v1 as components

DEPARTMENT = "McDonald's China &middot; IT Operating &middot; Traffic"

_FOOTER_HTML = f"""
<div id="suite-footer" class="page-footer">{DEPARTMENT}</div>
<style>
  .page-footer {{
    background: #1A1A1A;
    color: rgba(255,255,255,.7);
    font-size: 11px;
    padding: 14px 32px;
    text-align: left;
    letter-spacing: .3px;
    margin-top: 40px;
    box-sizing: border-box;
  }}
</style>
"""

_INJECT_JS = """
<script>
(function(){
  var doc = parent.document;
  var e = doc.getElementById('suite-footer');
  if (e) e.remove();
  var holder = doc.createElement('div');
  holder.innerHTML = __HTML__;
  while (holder.firstChild) doc.body.appendChild(holder.firstChild);
})();
</script>
"""


def render_footer():
    """注入全宽固定底栏（与 header 同方式）。"""
    components.html(_INJECT_JS.replace("__HTML__", json.dumps(_FOOTER_HTML)), height=0)
