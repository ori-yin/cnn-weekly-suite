"""
llm_service.py - CNN Performance Weekly：LLM 内容分析服务
参考 mcd-content-rank 项目实现
"""

import json
import math
import re
import openai
import anthropic
import dirtyjson
from concurrent.futures import ThreadPoolExecutor
from performance.config import API_PROVIDERS


ANALYSIS_DIMENSIONS = """请从以下3个维度逐条分析：

1. 核心亮点：
- 这条文案表现好的主要原因是什么？
- 是文案吸引力、人群匹配度、利益点强度，还是后续的落地页转化能力（落地页转化能力需要同步考虑GC、Sales，要注意那些CTR点击高但转化低的内容）？

2. 可借鉴点
- 标题是否直接表达利益点？
- 是否有场景感（早餐、午餐、下午茶、晚餐、周末、会员日）？
- 是否有紧迫感（今日限定、最后一天、限时、即将结束）？
- 人群匹配是否精准（内容—人群—场景一致）？
- 以及是否可以沉淀出可复用的模板供后续投放

3. 可优化（不作为必须输出项）
- 这不是"找茬"环节，有优化点就输出，没有就留空，不要硬说
- 如果文案本身已经很好（CTR高、转化好、标题利益点明确），就输出空字符串，不要为了输出而输出
- 只有在数据和文案都指向明确问题时才输出（如CTR高但转化低、标题模糊、利益点不清晰等）
- 基于各项数据结果以及具体的内容文案本身做分析

补充说明：
- 如果看到同一天有两条相同文案，可能是针对不同人群的投放（如新客vs沉默用户），并非重复投放，请注意区分"""


def build_analysis_prompt(items: list, is_good: bool = True, good_cases: list = None) -> str:
    """构建批量分析 prompt：高分走 Good Case，需提升走诊断室（带 Good Case 对比）"""
    lines = []
    for i, item in enumerate(items, 1):
        lines.append(
            f"【{i}】标题：{item['标题']}"
            f"｜正文：{item['内容']}"
            f"｜渠道：{item['渠道']}"
            f"｜触达：{item['触达成功']}"
            f"｜点击：{item['点击人次']}"
            f"｜CTR：{item['CTR']:.2f}%"
            f"｜GC：{item['订单GC']}"
            f"｜GC转化率：{item['订单GC转化率']:.2f}%"
            f"｜综合评分：{item['综合评分']:.2f}"
            f"｜排名：第{item['排名']}名"
        )
    body = chr(10).join(lines)

    if is_good:
        return f"""你是麦当劳中国内容营销分析专家。以下是本周 TOP3 表现优异的 Plan（Good Case），请逐条给出3行解读：

{ANALYSIS_DIMENSIONS}

请在上述维度基础上，每条输出以下字段（每个字段30字左右）：
- "why_good"：为什么好（一句话，点出关键成功因素）
- "template"：可复用模板（具体公式，能直接套用的内容结构）
- "scenario"：适用场景（什么投放场景还能再用）

每条都必须完整包含上述 3 个字段，缺一不可；若某字段确实无内容，输出"无明显发现"而非省略字段。

严格输出 JSON 数组，不要输出其他任何文字、不要用markdown代码块。共{len(items)}条：
{body}"""

    # 诊断室：需提升内容，带同类 Good Case 作对比参照
    ref_lines = []
    if good_cases:
        for j, g in enumerate(good_cases, 1):
            ref_lines.append(
                f"  Good{j}｜标题：{g['标题']}｜正文：{g['内容']}"
                f"｜CTR：{g['CTR']:.2f}%｜GC转化率：{g['订单GC转化率']:.2f}%"
            )
    ref_block = chr(10).join(ref_lines) if ref_lines else "（无同类 Good Case）"

    # 按当前渠道动态生成渠道约束（只保留当前渠道的，去掉范例和跨渠道冗余）
    ch_name = items[0].get("渠道", "") if items else ""
    if ch_name == "APP Push":
        ch_constraints = (
            "- 标题字数：14-18 字（含标点），超出即不合格\n"
            "- emoji：最多 1 个，自然嵌入开头可做色彩断点\n"
            "- 调性：朋友式口吻，像麦麦跟你说话，自然亲切不生硬"
        )
    elif ch_name == "企微1v1":
        ch_constraints = (
            "- 标题字数：精炼即可，避免拉成长段\n"
            "- emoji：最多 1 个，自然嵌入\n"
            "- 调性：朋友式私聊，寒暄温和有人情味；禁用\"宝子/亲/尊敬的麦粉\"等固定称呼"
        )
    else:
        ch_constraints = "- 调性：精炼自然"

    return f"""你是麦当劳中国内容营销分析专家。以下是 {ch_name} 渠道的 {len(items)} 条表现需提升 Plan，请逐条诊断并改写。

【同类 Good Case 参照（仅供把握该渠道好文案的写法）】
{ref_block}

【{ch_name} 改写约束】
{ch_constraints}
- 标题要利益点明确、场景感强（补足砍掉范例后的引导）
- 不编造原文未出现的具体数字/价格/折扣
- 不拉踩竞品（不写"比XX好/便宜"等对比句式）；只讲自身产品利益
- 禁用空喊词：立即/马上/快来/惊喜/钜惠/不容错过/火爆

【输出格式】每条输出 4 个字段（共 {len(items)} 条）：
- "diagnosis"：问题诊断（20 字内）
- "rewrite_title"：改写后的标题（≤ 18 字，含标点，遵守渠道约束）
- "rewrite_body"：改写后的正文（精炼自然，遵守渠道约束）
- "logic"：改写逻辑（20 字内）

⚠️ 必须严格输出 JSON 数组，禁止任何解释/前言/markdown 代码块。即使某条 Plan 无法分析，也要输出完整 3 字段（用"无明显发现"占位），绝不省略条目。

{body}"""


def _extract_json_robust(raw: str):
    """
    稳健的 JSON 提取：先尝试标准解析（数组或对象），失败后用正则逐条提取。
    返回 list 或 dict；调用方按需取用。
    """
    # 清理 markdown 代码块
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    # 尝试提取 JSON 数组
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match:
        raw = match.group(0)

    # 方案1：dirtyjson 解析
    try:
        result = dirtyjson.loads(raw)
        if isinstance(result, (list, dict)):
            return result
    except Exception:
        pass

    # 方案2：标准 json 解析
    try:
        result = json.loads(raw)
        if isinstance(result, (list, dict)):
            return result
    except Exception:
        pass

    # 方案3：正则逐条提取 {"key": "value", ...}
    items = re.findall(r'\{[^{}]*\}', raw)
    results = []
    for item_str in items:
        item = {}
        # 提取每个 key-value 对
        pairs = re.findall(r'"(\w+)"\s*:\s*"((?:[^"\\]|\\.)*)"', item_str)
        for key, value in pairs:
            item[key] = value
        # 也尝试提取空字符串的情况
        pairs_empty = re.findall(r'"(\w+)"\s*:\s*""', item_str)
        for key in pairs_empty:
            if key not in item:
                item[key] = ""
        if item:
            results.append(item)
    if results:
        return results

    # 方案4：终极兜底 - 返回空列表
    return []


def call_llm(api_key: str, provider: str, model: str, prompt: str):
    """调用 LLM API 并返回解析后的结果"""
    provider_config = API_PROVIDERS.get(provider)
    if not provider_config:
        return []

    # MiniMax 走 Anthropic 协议（其他 provider 走 OpenAI 协议）
    if provider == "MiniMax":
        base_url = provider_config["base_url"]
        client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        resp = client.messages.create(
            model=model,
            max_tokens=4000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )
        # 过滤 text block 拼成字符串，thinking 块跳过（看板用不到）
        text_parts = [b.text for b in resp.content if isinstance(b, anthropic.types.TextBlock)]
        raw = "\n".join(text_parts).strip()
        return _extract_json_robust(raw)

    base_url = provider_config["base_url"]
    client = openai.OpenAI(api_key=api_key, base_url=base_url) if base_url else openai.OpenAI(api_key=api_key)

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=4000,
    )
    raw = resp.choices[0].message.content.strip()
    return _extract_json_robust(raw)


def _friendly_error(e: Exception) -> str:
    """把裸 API 错误码转成可读中文，重点识别内容审查拦截。

    400 SensitiveContentDetected 是服务商内容安全审查拒绝（非并发/非 bug），
    一批 3 条拼一个 prompt，任一条触敏即整批 400。这里只改提示语让报错一眼可读，
    不做逐条降级重试（成本高，视触敏频率再议）。
    """
    msg = str(e)
    low = msg.lower()
    if "sensitivecontent" in low or "敏感" in msg or "content_filter" in low:
        return "内容被审查拦截（可能含敏感词），请检查文案后重试"
    if "400" in msg:
        return f"请求被拒（参数或内容问题）：{msg[:40]}"
    return f"API调用失败：{msg[:60]}"


def analyze_content(api_key: str, provider: str, model: str, items: list, is_good: bool = True, good_cases: list = None) -> list:
    """批量分析内容，返回结构化结果列表。高分走 Good Case，需提升走诊断室"""
    if not api_key:
        return [{"error": "请先填写 API Key"}] * len(items)

    prompt = build_analysis_prompt(items, is_good=is_good, good_cases=good_cases)

    # 诊断日志（Streamlit 终端可见）：调用规模 + 实际返回数 + 补齐数 + 真实结果数
    # 区分三种情况：✓ 全成 / ⚠️ LLM 返回条数不足被补齐 / ⚠️ LLM 返回足但字段空 / ✗ 异常
    ch_tag = items[0].get("渠道", "?") if items else "?"
    kind = "GoodCase" if is_good else "诊断室"
    print(f"[AI] {ch_tag} {kind} start: items={len(items)} prompt={len(prompt)}c")

    try:
        results = call_llm(api_key, provider, model, prompt)
        if not isinstance(results, list):
            results = [results]
        llm_n = len(results)
        # 补齐或截断；default 按类型给不同字段
        default = (
            {"why_good": "—", "template": "—", "scenario": "—"}
            if is_good
            else {"diagnosis": "—", "rewrite_title": "—", "rewrite_body": "—", "logic": "—"}
        )
        results = (results + [{**default} for _ in range(len(items))])[:len(items)]
        key_field = "why_good" if is_good else "diagnosis"
        n_padded = max(0, len(items) - llm_n)
        n_real = sum(1 for r in results[:llm_n] if r.get(key_field) not in (None, "", "—"))
        if n_padded > 0:
            print(f"[AI] {ch_tag} {kind} ⚠️ LLM returned {llm_n}/{len(items)} (padded {n_padded} with '—'), real={n_real}")
        elif n_real < len(items):
            print(f"[AI] {ch_tag} {kind} ⚠️ LLM returned {len(items)} but {len(items) - n_real} have empty '{key_field}', real={n_real}")
        else:
            print(f"[AI] {ch_tag} {kind} ✓ {n_real}/{len(items)} OK")
        for r in results:
            for k, v in default.items():
                r.setdefault(k, v)
            # 防御性清洗：字段值必须是 str（dirtyjson 可能把 AttributedDict/list 等塞进 value）
            for k in list(r.keys()):
                if not isinstance(r[k], str):
                    r[k] = str(r[k]) if r[k] is not None else ""
            # 二次校验：含 dirtyjson 内部表示痕迹（str 后仍出现 AttributedDict 字样）说明脏数据没洗干净
            # 整个 dict 当失败标记，用 default 占位覆盖，下次重试循环会重跑
            for k in list(r.keys()):
                v = r.get(k, "")
                if isinstance(v, str) and ("AttributedDict" in v or v.startswith("[(") or v.startswith("<")):
                    r.clear()
                    r.update(default)
                    break
        return results
    except json.JSONDecodeError as e:
        print(f"[AI] {ch_tag} {kind} ✗ JSONDecodeError: {str(e)[:80]}")
        return [{"error": f"JSON解析失败: {str(e)[:50]}"}] * len(items)
    except Exception as e:
        print(f"[AI] {ch_tag} {kind} ✗ {type(e).__name__}: {str(e)[:80]}")
        return [{"error": _friendly_error(e)}] * len(items)


def build_channel_summary_prompt(channel: str, items: list) -> str:
    """构建渠道总结 prompt"""
    lines = []
    for i, item in enumerate(items, 1):
        lines.append(
            f"【{i}】标题：{item['标题']}"
            f"｜正文：{item['内容']}"
            f"｜触达：{item['触达成功']}"
            f"｜CTR：{item['CTR']:.2f}%"
            f"｜GC：{item['订单GC']}"
            f"｜Sales：{item['订单Sales']}"
            f"｜综合评分：{item['综合评分']:.2f}"
        )

    return f"""你是麦当劳中国内容营销分析专家。请对以下 {channel} 渠道的 TOP4 Plan 进行渠道级总结分析。

{chr(10).join(lines)}

请从以下两个维度进行总结（不要使用emoji，用纯文字表述）：

1. **为什么好**（30-50字）：
- 抽象这4条内容的共同成功因素
- 它们在文案策略、人群定位、利益点设计、场景感等方面有什么共性
- 为什么这些因素能带来好的数据表现

2. **内容框架**（格式：XX+XX+XX）：
- 从这4条内容中提炼出可复用的内容框架模板
- 用3-4个关键词概括框架要素（如：强利益点+场景化+紧迫感）
- 这个框架可以指导后续在该渠道的内容创作

严格输出 JSON 对象，不要输出其他任何文字、不要用markdown代码块：
{{
  "why_good": "为什么好的总结",
  "content_framework": "XX+XX+XX"
}}"""


def analyze_channel_summary(api_key: str, provider: str, model: str, channel: str, items: list) -> dict:
    """渠道总结分析，返回结构化结果"""
    if not api_key:
        return {"error": "请先填写 API Key"}

    prompt = build_channel_summary_prompt(channel, items)

    try:
        result = call_llm(api_key, provider, model, prompt)
        # call_llm 返回的是列表，取第一个
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        elif isinstance(result, dict):
            return result
        else:
            return {"error": "AI返回格式异常"}
    except Exception as e:
        return {"error": _friendly_error(e)}


def build_bu_summary_prompt(items: list) -> str:
    """构建 BU CTR 环比解读 prompt。
    items = [{bu, curr_ctr, prior_ctr, delta_pp, reach, prior_reach}, ...]，调用方已按 |delta| 降序并截断 top 15。
    reach / prior_reach 均为日均触达（与 BU 总览表口径一致），两周对齐。"""
    lines = []
    for i, it in enumerate(items, 1):
        reach_delta_pct = ((it['reach'] - it['prior_reach']) / it['prior_reach'] * 100) if it['prior_reach'] > 0 else 0
        lines.append(
            f"【{i}】BU：{it['bu']}"
            f"｜本周CTR：{it['curr_ctr']:.2f}%"
            f"｜上周CTR：{it['prior_ctr']:.2f}%"
            f"｜CTR环比：{it['delta_pp']:+.2f}pp"
            f"｜本周日均触达：{it['reach']:,.0f}"
            f"｜上周日均触达：{it['prior_reach']:,.0f}"
            f"｜触达环比：{reach_delta_pct:+.1f}%"
        )
    body = chr(10).join(lines)

    return f"""你是麦当劳中国内容营销分析专家。以下是本周各 BU（预算 owner）的 CTR 与触达环比变动数据（仅含日均触达≥1.5万的 BU，两周数据对齐）：

{body}

请用自然语言对各 BU 的 CTR 与触达环比变动做总结分析，分三段输出（不要使用 emoji，用纯文字表述）：

1. **整体趋势**（30-50字）：
- 概括各 BU CTR 与触达环比变动的整体情况
- 大多数 BU 是涨是跌、幅度如何
- 是否存在明显的整体性趋势

2. **上涨关注 BU**（每个 BU 一句话，20字左右）：
- 点名 CTR 环比上涨明显的 BU
- 结合触达规模变化（日均触达环比）简要猜测可能原因（如内容质量提升、人群精准度变化、投放节奏调整等）
- 若无上涨 BU，输出"本周无显著上涨 BU"

3. **下跌关注 BU**（每个 BU 一句话，20字左右）：
- 点名 CTR 环比下跌明显的 BU
- 结合触达规模变化简要猜测可能原因
- 若无下跌 BU，输出"本周无显著下跌 BU"

严格输出 JSON 对象，不要输出其他任何文字、不要用 markdown 代码块：
{{
  "overview": "整体趋势总结",
  "risers": "上涨关注BU及原因",
  "fallers": "下跌关注BU及原因"
}}"""


def analyze_bu_summary(api_key: str, provider: str, model: str, items: list) -> dict:
    """BU 总览 AI 解读，返回 {overview, risers, fallers} 或 {error}。"""
    if not api_key:
        return {"error": "请先填写 API Key"}
    if not items:
        return {"error": "无达标 BU 数据（日均触达需≥1.5万）"}

    prompt = build_bu_summary_prompt(items)
    try:
        result = call_llm(api_key, provider, model, prompt)
        if isinstance(result, list) and len(result) > 0:
            r = result[0]
            default = {"overview": "—", "risers": "—", "fallers": "—"}
            for k, v in default.items():
                r.setdefault(k, v)
            return r
        elif isinstance(result, dict):
            default = {"overview": "—", "risers": "—", "fallers": "—"}
            for k, v in default.items():
                result.setdefault(k, v)
            return result
        else:
            return {"error": "AI返回格式异常"}
    except Exception as e:
        return {"error": _friendly_error(e)}


def run_llm_batch(tasks, max_workers=3):
    """并发执行一批 LLM 任务。

    每个 task 是 () -> result 的无参 callable（通常是对 analyze_* 的偏应用，
    已固化 api_key/provider/model/items 等入参）。返回与 tasks 等长的结果列表，
    保序——结果下标与 tasks 下标一一对应，调用方据此把结果映射回各自的 key。

    线程安全前提：analyze_content / analyze_channel_summary / analyze_bu_summary 均为
    无状态纯函数，内部 try/except 把异常转成 {"error": ...} 返回，不会抛出，因此
    ex.map 不会中途断。worker 只返回结果，不碰 st.session_state（那不是线程安全的）。

    max_workers=3：限并发防打爆 API，是吞吐与限流的平衡点。串行 ~15 次调用从
    2-5 分钟降到 ~1 分钟（约 4-5 轮，每轮 3 个并发）。
    """
    if not tasks:
        return []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        return list(ex.map(lambda f: f(), tasks))


def _safe_int(v, default=0):
    """NaN/None/非数 → default，避免 int(nan) 抛 ValueError 中断 handler 收集。

    数据清洗 pd.to_numeric(errors="coerce") 会把空单元格转 NaN；订单GC 等列在
    低 Sales plan 上常为 NaN，_build_items 里 int(row["订单GC"]) 会崩、中断
    整个 AI 收集（Sales 维度需提升卡因此空白无 AI）。
    """
    if v is None:
        return default
    try:
        if isinstance(v, float) and math.isnan(v):
            return default
        return int(v)
    except (TypeError, ValueError):
        return default


def _safe_float(v, default=0.0):
    """NaN/None/非数 → default，避免 float(nan) 类问题。"""
    if v is None:
        return default
    try:
        if isinstance(v, float) and math.isnan(v):
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def is_failed_plan(llm_result) -> bool:
    """plan task 是否有失败：返回结果非 list / 长度 0 / 任意条目有 error / 核心字段是 "—"。"""
    if not isinstance(llm_result, list) or len(llm_result) == 0:
        return True
    for r in llm_result:
        if not isinstance(r, dict):
            return True
        if "error" in r:
            return True
        # 高分看 why_good、需提升看 diagnosis，任一为占位 "—" 就算失败
        if r.get("why_good", "—") == "—" and r.get("diagnosis", "—") == "—":
            return True
    return False


def is_failed_summary(llm_result) -> bool:
    """渠道总结是否失败：非 dict / 含 error / why_good 是 "—"。"""
    if not isinstance(llm_result, dict):
        return True
    if "error" in llm_result:
        return True
    return llm_result.get("why_good", "—") == "—"


def is_failed_bu_summary(llm_result) -> bool:
    """BU 总结是否失败：非 dict / 含 error / overview 是 "—"。"""
    if not isinstance(llm_result, dict):
        return True
    if "error" in llm_result:
        return True
    return llm_result.get("overview", "—") == "—"
