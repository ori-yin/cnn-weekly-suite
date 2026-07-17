"""
components/ring.py - Canvas 环（单 iframe 内嵌卡片 + 动画）
- 提供 render_ring()：单 st.components.v1.html() 同时渲染 card + canvas + JS
  → 解决了「st.markdown → st.components → 逃出列布局」的问题
- 提供 render_ring_static_html()：导出用纯 HTML（SVG 版本，无动画）
"""
import streamlit.components.v1 as components

ANIME_CDN = "https://cdn.jsdelivr.net/npm/animejs@3.2.2/lib/anime.min.js"


def render_ring(actual: int, target: int, completion: float, size: int = 260, card_height: int = 480) -> None:
    """
    单 iframe 渲染：card border + title + canvas + JS 全部在同一个 HTML blob 内。
    避免 st.components.v1.html() 跳出 Streamlit 列容器边界的问题。
    """
    pct = max(0.0, completion)
    if pct > 1.5:
        pct = 1.5

    actual_str = f"{actual:,.0f}"
    target_str = f"{target:,.0f}"
    rate_str = f"{completion * 100:.1f}%"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><base href="about:blank">
<style>
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; background: transparent; }}
  .ring-card {{
    background: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 10px;
    padding: 16px;
    box-shadow: 0 1px 3px rgba(120,90,30,.06);
    height: {card_height}px;
    display: flex;
    flex-direction: column;
  }}
  .ring-card-title {{
    font-size: 11px; font-weight: 600; color: #888888;
    letter-spacing: .08em; text-transform: uppercase;
    margin-bottom: 10px;
  }}
  .ring-stage {{
    flex: 1;
    display: flex; align-items: center; justify-content: center;
  }}
  .ring-wrap {{
    position: relative;
    width: {size}px;
    height: {size}px;
  }}
  .ring-num-actual {{
    position: absolute; left: 50%; top: 38%;
    transform: translate(-50%,-50%);
    font-size: 38px; font-weight: 800; color: #1A1A1A;
    font-variant-numeric: tabular-nums; letter-spacing: -.02em; line-height: 1;
    white-space: nowrap;
  }}
  .ring-num-target {{
    position: absolute; left: 50%; top: 56%;
    transform: translate(-50%,-50%);
    font-size: 13px; font-weight: 600; color: #6B6B6B;
    white-space: nowrap;
  }}
  .ring-num-rate {{
    position: absolute; left: 50%; top: 70%;
    transform: translate(-50%,-50%);
    font-size: 14px; font-weight: 700; color: #DB0005;
    white-space: nowrap;
  }}
</style>
</head>
<body>
<div class="ring-card">
  <div class="ring-card-title">完成度</div>
  <div class="ring-stage">
    <div class="ring-wrap">
      <canvas id="ringCanvas" width="{size}" height="{size}"></canvas>
      <div class="ring-num-actual" id="actualNum">{actual_str}</div>
      <div class="ring-num-target">Target {target_str}</div>
      <div class="ring-num-rate" id="rateNum">{rate_str}</div>
    </div>
  </div>
</div>
<script src="{ANIME_CDN}"></script>
<script>
(function() {{
  const canvas = document.getElementById('ringCanvas');
  const ctx = canvas.getContext('2d');
  const W = {size}, H = {size};
  const cx = W / 2, cy = H / 2;
  const r = W / 2 - 18;
  const lineW = 22;
  const targetPct = {pct};

  function draw(progress) {{
    ctx.clearRect(0, 0, W, H);
    ctx.beginPath();
    ctx.arc(cx, cy, r, -Math.PI / 2, Math.PI * 1.5);
    ctx.lineWidth = lineW;
    ctx.strokeStyle = "#E0E0E0";
    ctx.lineCap = "round";
    ctx.stroke();
    const fillAngle = Math.min(progress, 1) * Math.PI * 2;
    if (fillAngle > 0) {{
      ctx.beginPath();
      ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + fillAngle);
      ctx.lineWidth = lineW;
      ctx.strokeStyle = "#DB0005";
      ctx.lineCap = "round";
      ctx.stroke();
    }}
    if (progress > 1) {{
      const overAngle = Math.min(progress - 1, 0.5) * Math.PI * 2;
      if (overAngle > 0) {{
        ctx.beginPath();
        ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + overAngle);
        ctx.lineWidth = lineW;
        ctx.strokeStyle = "#FFBC0D";
        ctx.lineCap = "round";
        ctx.stroke();
      }}
    }}
  }}

  draw(0);

  const obj = {{ v: 0 }};
  anime({{
    targets: obj, v: targetPct,
    duration: 1800, easing: 'easeOutExpo',
    update: function() {{ draw(obj.v); }},
  }});

  const actualTarget = {actual};
  const actualObj = {{ v: 0 }};
  anime({{
    targets: actualObj, v: actualTarget,
    duration: 1800, easing: 'easeOutExpo', round: 1,
    update: function() {{
      document.getElementById('actualNum').textContent = Math.round(actualObj.v).toLocaleString();
    }},
  }});
}})();
</script>
</body></html>"""
    components.html(html, height=card_height + 30)


def render_ring_static_html(actual: int, target: int, completion: float, size: int = 260) -> str:
    """导出用 SVG 版本（无动画）"""
    pct = max(0.0, completion)
    if pct > 1.5:
        pct = 1.5

    actual_str = f"{actual:,.0f}"
    target_str = f"{target:,.0f}"
    rate_str = f"{completion * 100:.1f}%"

    fill_angle = min(pct, 1) * 360
    over_angle = max(0, min(pct - 1, 0.5)) * 360

    r = size/2 - 18
    circ = 2 * 3.14159 * r

    over_svg = ""
    if over_angle > 0:
        over_svg = (
            f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="#FFBC0D" stroke-width="22" '
            f'stroke-dasharray="{over_angle/360 * circ} {circ}" '
            f'transform="rotate(-90 {size/2} {size/2})" stroke-linecap="round"/>'
        )

    return f"""
<div style="position:relative;width:{size}px;height:{size}px;margin:0 auto;">
  <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
    <circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="#E0E0E0" stroke-width="22"/>
    <circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="#DB0005" stroke-width="22"
      stroke-dasharray="{fill_angle/360 * circ} {circ}"
      transform="rotate(-90 {size/2} {size/2})" stroke-linecap="round"/>
    {over_svg}
  </svg>
  <div style="position:absolute;left:50%;top:38%;transform:translate(-50%,-50%);font-size:38px;font-weight:800;color:#1A1A1A;font-variant-numeric:tabular-nums;line-height:1;">{actual_str}</div>
  <div style="position:absolute;left:50%;top:56%;transform:translate(-50%,-50%);font-size:13px;font-weight:600;color:#6B6B6B;">Target {target_str}</div>
  <div style="position:absolute;left:50%;top:70%;transform:translate(-50%,-50%);font-size:14px;font-weight:700;color:#DB0005;">{rate_str}</div>
</div>
"""
