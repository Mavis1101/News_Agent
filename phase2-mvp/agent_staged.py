#!/usr/bin/env python3
"""
agent_staged.py — Intelligence Digest · Phase 2 MVP (Staged Prompting, V2)

Identical to agent.py in all orchestration, dedup, HTML, and send logic.
The only difference is fetch_news() is replaced by fetch_news_staged(),
which splits one large Claude call into two focused calls:

  Stage 1 — Web search + fact extraction  (skills/news_extractor_staged.md)
  Stage 2 — Analysis enrichment only      (skills/news_analyst.md)

Why two stages?
  • Stage 1 uses web_search; Stage 2 does not — cheaper and faster for analysis.
  • Smaller, focused prompts are more reliable and easier to debug independently.
  • If Stage 2 fails, the agent degrades gracefully: sends items without analysis
    rather than dropping the whole run.
  • Prompts can be iterated independently without touching search/extraction logic.

Required env vars:
  ANTHROPIC_API_KEY
  RESEND_API_KEY

Optional env vars:
  FROM_EMAIL   (default: digest@lensignal.com)
  STORY_COUNT  (default: 5)
  DEMO         (set to "1" to skip Claude API and use hardcoded demo data)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import resend  # pip install resend

# ── paths ──────────────────────────────────────────────────────────────────────
BASE_DIR         = Path(__file__).parent
SUBSCRIBERS_FILE = BASE_DIR / "subscribers.json"
DEDUP_FILE       = BASE_DIR / "dedup_history.json"
SKILLS_DIR       = BASE_DIR / "skills"
DEDUP_MAX        = 40

# ── config ─────────────────────────────────────────────────────────────────────
MODEL       = "claude-sonnet-4-20250514"
TOPICS      = "AI/High-tech, Geopolitics, Macro/Markets/Policy"
STORY_COUNT = int(os.environ.get("STORY_COUNT", "5"))
FROM_EMAIL  = os.environ.get("FROM_EMAIL", "digest@lensignal.com")

TOPIC_LABEL = {
    "tech":   "AI/Tech",
    "geo":    "Geopolitics",
    "macro":  "Macro/Policy",
}

TIER_COLOR = {
    "T1": "#c8a96e",
    "T2": "#4db8a0",
    "T3": "#6090d8",
    "T4": "#8a8880",
}

# ── feedback URLs (must match news_agent_v3_5.html exactly) ───────────────────
THANKYOU_BASE = "https://mavis1101.github.io/News_Agent/thankyou.html"
FORM_ID       = "1FAIpQLScN3lYHkYmg0tdXkPi9ofkhUKcIqdf2HTa5J6N2j9t-0Ov8zQ"
ENTRY_DATE    = "entry.763436474"
ENTRY_RATING  = "entry.771339392"
UNSUB_ID      = "1FAIpQLSc5y-sjQt7f3w18bqQT2rUVRQ8Ef5mJ9fCmufKlmiKqYcEFHw"

# ── analysis fields populated by Stage 2 ──────────────────────────────────────
ANALYSIS_FIELDS = ("investEn", "investCn", "geoEn", "geoCn", "careerEn", "careerCn")


# ── skill loader (identical to agent.py) ──────────────────────────────────────
def render_skill(name: str, **kwargs) -> str:
    """
    Load a skill file from skills/{name}.md, strip YAML frontmatter if present,
    and substitute %%PLACEHOLDER%% tokens with caller-supplied values.
    """
    path = SKILLS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(
            f"Skill file not found: {path}\n"
            f"Expected location: phase2-mvp/skills/{name}.md"
        )

    content = path.read_text(encoding="utf-8")

    # Strip YAML frontmatter (--- block at the top of the file)
    if content.startswith("---\n"):
        end = content.find("\n---\n", 4)
        if end != -1:
            content = content[end + 5:]

    content = content.strip()

    # Substitute %%KEY%% placeholders
    for key, value in kwargs.items():
        content = content.replace(f"%%{key.upper()}%%", str(value))

    return content


# ── helpers (identical to agent.py) ───────────────────────────────────────────
def headline_key(item: dict) -> str:
    """Stable short key derived from the English headline (mirrors JS headlineKey())."""
    h = item.get("headlineEn", "")
    return re.sub(r"[^a-z0-9]", "", h.lower())[:60]


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── JSON repair helpers (identical to agent.py) ───────────────────────────────
def _repair_json_quotes(json_str: str) -> str:
    """
    Fix the most common LLM JSON error: unescaped ASCII double-quote characters
    inside string values.
    """
    result: list[str] = []
    i = 0
    n = len(json_str)

    while i < n:
        c = json_str[i]

        if c != '"':
            result.append(c)
            i += 1
            continue

        result.append('"')
        i += 1

        while i < n:
            c = json_str[i]

            if c == '\\':
                result.append(c)
                i += 1
                if i < n:
                    result.append(json_str[i])
                    i += 1
                continue

            if c == '"':
                j = i + 1
                while j < n and json_str[j] in ' \t\n\r':
                    j += 1
                next_sig = json_str[j] if j < n else ''

                if next_sig in (':', ',', '}', ']'):
                    result.append('"')
                    i += 1
                    break
                else:
                    result.append('\\"')
                    i += 1
                continue

            result.append(c)
            i += 1

    return ''.join(result)


def _parse_json_array(raw: str, label: str = "response") -> list:
    """
    Extract and parse a JSON array from raw text, with repair fallback.
    `label` is only used in error messages to identify which stage failed.
    """
    start = raw.find('[')
    end   = raw.rfind(']')
    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            f"No JSON array found in {label}. Preview:\n{raw[:400]}"
        )

    json_str = raw[start:end + 1]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        ctx_start = max(0, e.pos - 120)
        ctx_end   = min(len(json_str), e.pos + 120)
        print(f"  [{label}] JSON parse error: {e.msg} at pos {e.pos}")
        print(f"  Context: ...{json_str[ctx_start:ctx_end]}...")

    print(f"  [{label}] Attempting inline JSON repair…")
    repaired = _repair_json_quotes(json_str)
    try:
        result = json.loads(repaired)
        print(f"  [{label}] Inline repair succeeded.")
        return result
    except json.JSONDecodeError as e2:
        raise ValueError(
            f"[{label}] JSON parse failed after repair: {e2.msg} at pos {e2.pos}"
        )


# ── Claude API call — STAGED VERSION ──────────────────────────────────────────
def fetch_news_staged(recent_keys: list) -> list:
    """
    Two-stage Claude pipeline:
      Stage 1: web search + fact extraction  → structured JSON (no analysis)
      Stage 2: analysis enrichment           → analysis fields merged in

    Graceful degradation: if Stage 2 fails, returns Stage 1 items with empty
    analysis fields rather than raising and dropping the entire run.
    """
    from datetime import timedelta
    now       = datetime.now(timezone.utc)
    today     = now.strftime("%Y-%m-%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    keys_str  = ", ".join(recent_keys) if recent_keys else "none"

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # ── Stage 1: Extract facts via web search ─────────────────────────────────
    print("  Stage 1: Extracting news facts via web search…")

    SYS_1 = render_skill(
        "news_extractor_staged",
        today=today,
        yesterday=yesterday,
        keys_str=keys_str,
    )
    USER_1 = (
        f"Today is {today}. Search for the {STORY_COUNT} most important news stories "
        f"published or announced between {yesterday} and {today} (last 24 hours only) "
        f"on topics: {TOPICS}.\n"
        f"Focus on: AI/semiconductors, US-China relations, geopolitics, macro, tech policy.\n"
        f"STRICT RULE: Every story's newsDate must be {yesterday} or {today}. "
        f"Reject any story whose underlying event occurred before {yesterday}.\n"
        f"Prioritise T1 (government/central bank official) and T2 (major corporate official) sources.\n"
        f"Leave analysis fields (investEn/Cn, geoEn/Cn, careerEn/Cn) as empty strings.\n"
        f"Return complete JSON array only."
    )

    resp1 = client.beta.messages.create(
        model=MODEL,
        max_tokens=8000,
        system=SYS_1,
        messages=[{"role": "user", "content": USER_1}],
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        betas=["web-search-2025-03-05"],
    )

    raw1 = "".join(block.text for block in resp1.content if hasattr(block, "text"))
    print(f"  Stage 1 response: {len(raw1)} chars")

    # Stage 1 parse — same repair chain as agent.py
    try:
        stage1_items = _parse_json_array(raw1, label="Stage 1")
    except ValueError:
        # Attempt Claude-assisted repair for Stage 1 (rare but matches agent.py safety net)
        print("  Stage 1 falling back to Claude JSON-repair call…")
        bad_json = raw1[raw1.find('['):raw1.rfind(']') + 1] if '[' in raw1 else raw1
        fix_resp = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            messages=[{
                "role": "user",
                "content": (
                    "The following JSON array is malformed — it contains unescaped "
                    "double-quote characters inside string values. "
                    "Please fix every unescaped quote (replace with \\\" or with single "
                    "quotes / Chinese 「」 brackets as appropriate) and return ONLY the "
                    "corrected JSON array with no explanation.\n\n" + bad_json
                ),
            }],
        )
        fixed_raw = fix_resp.content[0].text if fix_resp.content else ""
        stage1_items = _parse_json_array(fixed_raw, label="Stage 1 repair")

    print(f"  Stage 1 extracted: {len(stage1_items)} items")

    # ── Stage 2: Enrich with analysis (no web search) ─────────────────────────
    print("  Stage 2: Adding investment / geo / career analysis…")

    SYS_2 = render_skill("news_analyst")
    USER_2 = (
        f"Today is {today}. Here are {len(stage1_items)} extracted news items as JSON.\n"
        f"For each item, add the 6 analysis fields: "
        f"investEn, investCn, geoEn, geoCn, careerEn, careerCn.\n"
        f"Return a JSON array with one object per item containing "
        f"the item's rank plus those 6 fields only.\n\n"
        + json.dumps(stage1_items, ensure_ascii=False)
    )

    try:
        resp2 = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            system=SYS_2,
            messages=[{"role": "user", "content": USER_2}],
        )
        raw2 = resp2.content[0].text if resp2.content else ""
        print(f"  Stage 2 response: {len(raw2)} chars")

        analysis_items = _parse_json_array(raw2, label="Stage 2")

        # Merge by rank — explicit field-by-field for safety
        analysis_by_rank = {a["rank"]: a for a in analysis_items}
        for item in stage1_items:
            r = item.get("rank")
            if r in analysis_by_rank:
                a = analysis_by_rank[r]
                for field in ANALYSIS_FIELDS:
                    item[field] = a.get(field, "")
        print(f"  Stage 2 merged analysis into {len(stage1_items)} items")

    except Exception as exc:
        # Graceful degradation: send without analysis rather than fail the run
        print(f"  Stage 2 failed ({exc})")
        print("  Degrading gracefully — sending items without analysis fields.")
        for item in stage1_items:
            for field in ANALYSIS_FIELDS:
                item.setdefault(field, "")

    return stage1_items


# ── demo data (identical to agent.py) ─────────────────────────────────────────
def demo_news() -> list:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return [
        {
            "rank": 1, "sourceTier": "T1",
            "source": "Federal Reserve", "sourceCn": "美联储",
            "sourceUrl": "https://www.federalreserve.gov/newsevents/pressreleases.htm",
            "topic": "macro", "confidence": "HIGH",
            "newsDate": today, "isMajorUpdate": False, "updateNote": "",
            "headlineEn": "Fed holds rates steady; signals cuts pushed to Q4 2026",
            "headlineCn": "美联储维持利率不变，暗示降息推迟至Q4",
            "whoEn": "Fed Chair Jerome Powell, FOMC", "whoCn": "美联储主席鲍威尔",
            "whatEn": "Post-meeting statement holds federal funds rate unchanged",
            "whatCn": "会后声明维持利率不变",
            "whenEn": f"{today}, FOMC meeting", "whenCn": f"{today} FOMC会议",
            "whereEn": "Washington D.C.", "whereCn": "华盛顿特区",
            "whyEn": "Services inflation stickier than expected",
            "whyCn": "服务业通胀韧性超预期",
            "investEn": "[Analysis] Dollar strengthens short-term; rate-sensitive growth stocks face headwinds.",
            "investCn": "[分析] 美元短期走强，利率敏感型成长股承压。",
            "geoEn": "[Analysis] Sustained high rates reinforce dollar dominance.",
            "geoCn": "[分析] 高利率延续强化美元霸权。",
            "careerEn": "[Analysis] FinTech funding conditions remain tight.",
            "careerCn": "[分析] 金融科技融资环境持续收紧。",
        },
        {
            "rank": 2, "sourceTier": "T2",
            "source": "NVIDIA IR", "sourceCn": "英伟达投资者关系",
            "sourceUrl": "https://investor.nvidia.com/news-releases/news-release-details/",
            "topic": "tech", "confidence": "HIGH",
            "newsDate": today, "isMajorUpdate": False, "updateNote": "",
            "headlineEn": "NVIDIA announces next-gen Blackwell Ultra GPU for data centres",
            "headlineCn": "英伟达发布下一代Blackwell Ultra数据中心GPU",
            "whoEn": "NVIDIA CEO Jensen Huang", "whoCn": "英伟达CEO黄仁勋",
            "whatEn": "Unveiled Blackwell Ultra GPU with 2× the memory bandwidth of predecessor",
            "whatCn": "发布Blackwell Ultra GPU，内存带宽是上代两倍",
            "whenEn": f"{today}, GTC Conference", "whenCn": f"{today} GTC大会",
            "whereEn": "San Jose, California", "whereCn": "加州圣何塞",
            "whyEn": "Surging demand for AI training infrastructure",
            "whyCn": "AI训练基础设施需求激增",
            "investEn": "[Analysis] NVDA supply chain beneficiaries: TSMC, SK Hynix. Competitors face widening moat.",
            "investCn": "[分析] 英伟达供应链受益：台积电、SK海力士。竞争对手护城河差距扩大。",
            "geoEn": "[Analysis] US chip export controls likely to tighten around Blackwell Ultra.",
            "geoCn": "[分析] 美国芯片出口管制可能围绕Blackwell Ultra进一步收紧。",
            "careerEn": "[Analysis] Strong demand for CUDA engineers and AI infrastructure roles.",
            "careerCn": "[分析] CUDA工程师和AI基础设施岗位需求强劲。",
        },
    ]


# ── email HTML builder (identical to agent.py) ────────────────────────────────
def build_email_html(items: list, today: str) -> str:
    """
    Produces an HTML email that matches the showEmail() output in news_agent_v3_5.html:
    dark background, card layout, 5W bilingual table, analysis section, feedback footer.
    """
    submit_useful = f"{THANKYOU_BASE}?rating=useful&date={today}"
    submit_notrel = f"{THANKYOU_BASE}?rating=not_relevant&date={today}"
    open_issue    = (
        f"https://docs.google.com/forms/d/e/{FORM_ID}/viewform"
        f"?{ENTRY_DATE}={today}&{ENTRY_RATING}=issue"
    )
    open_unsub = f"https://docs.google.com/forms/d/e/{UNSUB_ID}/viewform"

    parts = []

    parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Intelligence Digest · {today}</title>
</head>
<body style="background:#22252a;color:#e8e4dc;font-family:Georgia,serif;
             max-width:700px;margin:0 auto;padding:24px 20px;font-size:15px">

<div style="border-bottom:1px solid #363a40;padding-bottom:18px;margin-bottom:28px">
  <div style="font-size:24px;color:#c8a96e;letter-spacing:0.06em;font-family:Georgia,serif">
    Intelligence Digest
  </div>
  <div style="font-size:12px;color:#7a7875;letter-spacing:0.16em;margin-top:4px;font-family:serif">
    今日情报简报
  </div>
  <div style="font-size:12px;color:#7a7875;margin-top:8px;font-family:monospace">
    {today} · {len(items)} stories · AI/Tech · Geopolitics · Macro
  </div>
</div>
""")

    for i, it in enumerate(items, 1):
        tier        = it.get("sourceTier", "T3")
        tier_color  = TIER_COLOR.get(tier, "#8a8880")
        date_str    = f" · {it['newsDate']}" if it.get("newsDate") else ""
        topic_label = TOPIC_LABEL.get(it.get("topic", ""), it.get("topic", ""))
        confidence  = it.get("confidence", "MED")
        is_major    = it.get("isMajorUpdate", False)
        update_note = it.get("updateNote", "")
        src_url     = it.get("sourceUrl", "")

        headline_en = it.get("headlineEn", "")
        headline_cn = it.get("headlineCn", "")
        headline_link = (
            f'<a href="{src_url}" style="color:#dedad2;text-decoration:none">{headline_en}</a>'
            if src_url else headline_en
        )

        major_badge = (
            ' · <span style="color:#4db8a0;font-family:monospace;font-size:10px">Major update</span>'
            if is_major else ""
        )
        update_note_html = (
            f'<div style="font-size:11px;color:#4db8a0;font-family:monospace;margin-top:4px">'
            f'Update: {update_note}</div>'
            if update_note else ""
        )

        def analysis_block(tag_en, tag_cn, tag_color, text_en, text_cn):
            if not text_en:
                return ""
            return (
                f'<div style="margin-bottom:10px">'
                f'<span style="background:rgba(0,0,0,0.3);color:{tag_color};'
                f'padding:2px 8px;border-radius:3px;font-size:10px;font-family:monospace">'
                f'{tag_en} · {tag_cn}</span><br>'
                f'<span style="color:#dedad2;font-size:14px">{text_en}</span><br>'
                f'<span style="color:#9a9890;font-size:12px">{text_cn}</span>'
                f'</div>'
            )

        invest_block = analysis_block(
            "Investment", "投资", "#6090d8",
            it.get("investEn", ""), it.get("investCn", ""),
        )
        geo_block = analysis_block(
            "Geopolitics", "地缘", "#c8a96e",
            it.get("geoEn", ""), it.get("geoCn", ""),
        )
        career_block = analysis_block(
            "Career", "职场", "#70b880",
            it.get("careerEn", ""), it.get("careerCn", ""),
        )

        source_link = (
            f'<div style="margin-top:10px">'
            f'<a href="{src_url}" style="color:#6090d8;font-size:12px;text-decoration:none">→ Source</a>'
            f'</div>'
            if src_url else ""
        )

        parts.append(f"""
<div style="border:1px solid #363a40;border-radius:8px;margin-bottom:18px;
            overflow:hidden;background:#2c3038">

  <div style="padding:18px 20px 0">
    <div style="font-size:12px;color:#7a7875;font-family:monospace;margin-bottom:10px">
      #{i} &nbsp;
      <span style="background:rgba(200,169,110,0.1);color:{tier_color};
                   border:1px solid rgba(200,169,110,0.2);padding:1px 5px;
                   border-radius:3px;font-size:10px">{tier}</span>
      &nbsp;{it.get('source', it.get('sourceCn', ''))} · {topic_label} · {confidence}{date_str}{major_badge}
    </div>
    <div style="font-size:18px;font-weight:400;line-height:1.5;margin-bottom:4px">
      {headline_link}
    </div>
    <div style="font-size:14px;color:#9a9890;font-family:serif;margin-bottom:4px">
      {headline_cn}
    </div>
    {update_note_html}
  </div>

  <div style="padding:14px 20px;font-size:13px">
    <div style="color:#7a7875;font-size:11px;font-family:monospace;margin-bottom:6px">English · 5W</div>
    <div style="margin-bottom:5px"><span style="color:#7a7875;display:inline-block;min-width:52px">WHO</span>{it.get('whoEn','—')}</div>
    <div style="margin-bottom:5px"><span style="color:#7a7875;display:inline-block;min-width:52px">WHAT</span>{it.get('whatEn','—')}</div>
    <div style="margin-bottom:5px"><span style="color:#7a7875;display:inline-block;min-width:52px">WHEN</span>{it.get('whenEn','—')}</div>
    <div style="margin-bottom:5px"><span style="color:#7a7875;display:inline-block;min-width:52px">WHERE</span>{it.get('whereEn','—')}</div>
    <div style="margin-bottom:14px"><span style="color:#7a7875;display:inline-block;min-width:52px">WHY</span>{it.get('whyEn','—')}</div>
    <div style="border-top:1px solid #363a40;margin-bottom:12px"></div>
    <div style="color:#7a7875;font-size:11px;font-family:monospace;margin-bottom:6px">中文 · 五要素</div>
    <div style="margin-bottom:5px"><span style="color:#7a7875;display:inline-block;min-width:52px">何人</span>{it.get('whoCn','—')}</div>
    <div style="margin-bottom:5px"><span style="color:#7a7875;display:inline-block;min-width:52px">何事</span>{it.get('whatCn','—')}</div>
    <div style="margin-bottom:5px"><span style="color:#7a7875;display:inline-block;min-width:52px">何时</span>{it.get('whenCn','—')}</div>
    <div style="margin-bottom:5px"><span style="color:#7a7875;display:inline-block;min-width:52px">何地</span>{it.get('whereCn','—')}</div>
    <div><span style="color:#7a7875;display:inline-block;min-width:52px">为何</span>{it.get('whyCn','—')}</div>
  </div>

  <div style="background:#22252a;padding:14px 20px">
    <div style="color:#7a7875;font-size:11px;font-family:monospace;margin-bottom:10px">
      Analysis · 分析
    </div>
    {invest_block}
    {geo_block}
    {career_block}
    {source_link}
  </div>

</div>
""")

    parts.append(f"""
<div style="margin-top:28px;padding-top:18px;border-top:1px solid #2a2a2a;text-align:center">
  <p style="font-size:13px;color:#666;margin-bottom:14px;font-family:Georgia,serif">
    How was today's digest?
  </p>
  <div style="display:inline-flex;gap:6px;flex-wrap:wrap;justify-content:center;margin-bottom:18px">
    <a href="{submit_useful}"
       style="display:inline-block;padding:8px 18px;border:1px solid #3a7a50;
              border-radius:6px;color:#70b880;text-decoration:none;
              font-size:13px;font-family:Georgia,serif">👍 Useful today</a>
    <a href="{submit_notrel}"
       style="display:inline-block;padding:8px 18px;border:1px solid #6a3a3a;
              border-radius:6px;color:#c86060;text-decoration:none;
              font-size:13px;font-family:Georgia,serif">👎 Not relevant</a>
    <a href="{open_issue}"
       style="display:inline-block;padding:8px 18px;border:1px solid #7a6030;
              border-radius:6px;color:#d4943a;text-decoration:none;
              font-size:13px;font-family:Georgia,serif">⚑ Report an issue</a>
  </div>
  <p style="font-size:11px;color:#555;font-family:Georgia,serif">
    Analysis sections are AI inference — not confirmed fact. Always verify before making decisions.<br>
    分析部分为AI推断，非确认事实。请在做出决策前自行核实。<br><br>
    <a href="{open_unsub}"
       style="color:#444;text-decoration:underline;font-size:11px">Unsubscribe</a>
  </p>
</div>

</body>
</html>""")

    return "".join(parts)


# ── email sender (identical to agent.py) ──────────────────────────────────────
def send_emails(subscribers: list, subject: str, html: str) -> None:
    resend.api_key = os.environ["RESEND_API_KEY"]
    for sub in subscribers:
        email = sub.get("email", "").strip()
        name  = sub.get("name", "").strip()
        if not email:
            print(f"  [skip] Entry with no email: {sub}")
            continue
        resend.Emails.send({
            "from":    f"Intelligence Digest <{FROM_EMAIL}>",
            "to":      email,
            "subject": subject,
            "html":    html,
        })
        print(f"  ✓ Sent → {name} <{email}>")


# ── main (identical to agent.py except fetch_news → fetch_news_staged) ────────
def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"\n── Intelligence Digest (Staged) · {today} ──────────────────────")

    subscribers = load_json(SUBSCRIBERS_FILE, [])
    dedup       = load_json(DEDUP_FILE, {})
    print(f"  Subscribers   : {len(subscribers)}")
    print(f"  Dedup history : {len(dedup)} stories")

    if not subscribers:
        print("  No subscribers — exiting.")
        sys.exit(0)

    recent_keys = list(dedup.keys())[-DEDUP_MAX:]

    if os.environ.get("DEMO") == "1":
        print("  [DEMO MODE] Skipping Claude API — using hardcoded demo data")
        raw_items = demo_news()
    else:
        print(f"  Fetching {STORY_COUNT} stories via Claude API + web search (2-stage)…")
        try:
            raw_items = fetch_news_staged(recent_keys)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            sys.exit(1)
    print(f"  Received {len(raw_items)} stories")

    new_dedup = dict(dedup)
    filtered  = []
    for it in raw_items:
        k = headline_key(it)
        if k in new_dedup and not it.get("isMajorUpdate", False):
            print(f"  [dedup] skip: {it.get('headlineEn','')[:60]}")
            continue
        new_dedup[k] = {
            "date":          it.get("newsDate", today),
            "isMajorUpdate": bool(it.get("isMajorUpdate", False)),
        }
        filtered.append(it)

    items = filtered if filtered else raw_items

    tier_order = {"T1": 0, "T2": 1, "T3": 2, "T4": 3}
    items.sort(key=lambda x: tier_order.get(x.get("sourceTier", "T4"), 3))
    print(f"  After dedup   : {len(items)} stories")

    if len(new_dedup) > DEDUP_MAX:
        keys      = list(new_dedup.keys())
        new_dedup = {k: new_dedup[k] for k in keys[-DEDUP_MAX:]}

    save_json(DEDUP_FILE, new_dedup)
    print("  Dedup history saved")

    subject = f"Intelligence Digest · {today}"
    html    = build_email_html(items, today)
    print(f"  HTML size     : {len(html):,} chars")
    print(f"  Sending to {len(subscribers)} subscriber(s)…")
    send_emails(subscribers, subject, html)

    print(f"\n  ✓ Done — {len(items)} stories → {len(subscribers)} subscriber(s).")
    print("─" * 58)


if __name__ == "__main__":
    main()
