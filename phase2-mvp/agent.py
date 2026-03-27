#!/usr/bin/env python3
"""
agent.py — Intelligence Digest · Phase 2 MVP
Mirrors the logic of news_agent_v3_5.html for server-side batch delivery.

Flow:
  1. Load subscribers.json  (who to send to)
  2. Load dedup_history.json  (what was already sent)
  3. Call Claude API with web_search tool  (same prompt as v3_5.html)
     — OR use demo data if DEMO=1 env var is set (skips API, free)
  4. Filter duplicates; update dedup_history.json
  5. Build HTML email  (same layout as v3_5.html → showEmail())
  6. Send via Resend to every subscriber

Required env vars:
  ANTHROPIC_API_KEY
  RESEND_API_KEY

Optional env vars:
  FROM_EMAIL   (default: onboarding@resend.dev)
  STORY_COUNT  (default: 7)
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
DEDUP_MAX        = 40

# ── config ─────────────────────────────────────────────────────────────────────
MODEL       = "claude-sonnet-4-20250514"
TOPICS      = "AI/High-tech, Geopolitics, Macro/Markets, Career/AI pivot, Policy/Regulation"
STORY_COUNT = int(os.environ.get("STORY_COUNT", "7"))
FROM_EMAIL  = os.environ.get("FROM_EMAIL", "onboarding@resend.dev")

TOPIC_LABEL = {
    "tech":   "AI/Tech",
    "geo":    "Geopolitics",
    "macro":  "Macro",
    "career": "Career",
    "policy": "Policy",
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


# ── helpers ────────────────────────────────────────────────────────────────────
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


# ── Claude API call ────────────────────────────────────────────────────────────
def fetch_news(recent_keys: list) -> list:
    today     = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    keys_str  = ", ".join(recent_keys) if recent_keys else "none"

    SYS = f"""You are an elite intelligence analyst. Your task is to find today's most important news and return a strict JSON array — bilingual English + Chinese — with English as the primary language.

SOURCE PRIORITY RULES (mandatory):
T1 (highest): Government official statements, White House/State Council/Parliament releases, central bank announcements (Fed/PBOC/ECB), regulatory official notices, military official statements.
T2: Major corporate IR pages, earnings calls, official press releases (Apple Newsroom, NVIDIA IR, Huawei official site), exchange filings, SEC/HKEX/SSE documents.
T3: Reuters, Bloomberg, Xinhua, FT, Nikkei, WSJ, SCMP.
T4: Other media, blogs, opinion pieces — must note T4 in output, confidence never exceeds MED.

Rules:
- T4 sources: confidence MAX is MED, never HIGH.
- If same event has T1/T2 source available, use that and ignore T4.
- sourceUrl must be the original official URL, not an aggregator.
- newsDate must be the actual publication/announcement date in YYYY-MM-DD format.
- isMajorUpdate: set true ONLY if this story is a significant new development on a previously known topic (e.g. policy announced before, now signed into law). Otherwise false.

DEDUPLICATION: The following story keys were already sent recently — do NOT include them unless isMajorUpdate is true:
{keys_str}

OUTPUT FORMAT: Return ONLY a raw JSON array, no markdown, no prefix, no explanation. Each object:
{{
  "rank": number,
  "sourceTier": "T1"|"T2"|"T3"|"T4",
  "source": "Source name (English)",
  "sourceCn": "来源名称（中文）",
  "sourceUrl": "URL",
  "topic": "tech"|"geo"|"macro"|"career"|"policy",
  "confidence": "HIGH"|"MED"|"LOW",
  "newsDate": "YYYY-MM-DD",
  "isMajorUpdate": false,
  "updateNote": "",
  "headlineEn": "English headline (primary, concise and specific)",
  "headlineCn": "中文标题",
  "whoEn": "who",       "whoCn": "何人",
  "whatEn": "what",     "whatCn": "何事",
  "whenEn": "when",     "whenCn": "何时（含具体日期）",
  "whereEn": "where",   "whereCn": "何地",
  "whyEn": "why",       "whyCn": "为何/背景",
  "investEn": "[Analysis] Investment implications…",
  "investCn": "[分析] 投资影响…",
  "geoEn": "[Analysis] Geopolitical implications…",
  "geoCn": "[分析] 地缘政治影响…",
  "careerEn": "[Analysis] Career/AI job market implications…",
  "careerCn": "[分析] 对AI/科技职场的影响…"
}}"""

    USER = (
        f"Search for the {STORY_COUNT} most important news stories from the last 24 hours "
        f"on topics: {TOPICS}.\n"
        f"Focus on: AI/semiconductors, US-China relations, geopolitics, macro, tech policy.\n"
        f"Today's date: {today}. Include the exact newsDate for each story.\n"
        f"Prioritise T1 (government/central bank official) and T2 (major corporate official) sources.\n"
        f"Return complete JSON array only."
    )

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=8000,
        system=SYS,
        messages=[{"role": "user", "content": USER}],
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        betas=["web-search-2025-03-05"],
    )

    # Concatenate all text blocks in response
    raw = "".join(
        block.text for block in response.content if hasattr(block, "text")
    )
    print(f"  Raw response length: {len(raw)} chars")

    # Extract JSON array — find first '[' to last ']'
    start = raw.find("[")
    end   = raw.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON array found. Raw preview:\n{raw[:600]}")

    json_str = raw[start:end + 1]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Log context around the error so we can diagnose
        ctx_start = max(0, e.pos - 120)
        ctx_end   = min(len(json_str), e.pos + 120)
        print(f"  JSON parse error: {e.msg} at pos {e.pos}")
        print(f"  Context: ...{json_str[ctx_start:ctx_end]}...")
        raise ValueError(f"JSON parse failed: {e.msg} at pos {e.pos}")


# ── demo data (used when DEMO=1, no API call) ─────────────────────────────────
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


# ── email HTML builder ─────────────────────────────────────────────────────────
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

    # ── head / masthead ────────────────────────────────────────────────────────
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
    {today} · {len(items)} stories · AI/Tech · Geopolitics · Macro · Career · Bilingual EN/CN
  </div>
</div>
""")

    # ── news cards ─────────────────────────────────────────────────────────────
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

  <!-- card header -->
  <div style="padding:18px 20px 0">
    <div style="font-size:12px;color:#7a7875;font-family:monospace;margin-bottom:10px">
      #{i} &nbsp;
      <span style="background:rgba(200,169,110,0.1);color:{tier_color};
                   border:1px solid rgba(200,169,110,0.2);padding:1px 5px;
                   border-radius:3px;font-size:10px">{tier}</span>
      &nbsp;{it.get('source', it.get('sourceCn', ''))} · {topic_label} · {confidence}{date_str}{major_badge}
    </div>

    <!-- headline -->
    <div style="font-size:18px;font-weight:400;line-height:1.5;margin-bottom:4px">
      {headline_link}
    </div>
    <div style="font-size:14px;color:#9a9890;font-family:serif;margin-bottom:4px">
      {headline_cn}
    </div>
    {update_note_html}
  </div>

  <!-- 5W stacked: English on top, Chinese below -->
  <div style="padding:14px 20px;font-size:13px">

    <!-- English block -->
    <div style="color:#7a7875;font-size:11px;font-family:monospace;margin-bottom:6px">English · 5W</div>
    <div style="margin-bottom:5px"><span style="color:#7a7875;display:inline-block;min-width:52px">WHO</span>{it.get('whoEn','—')}</div>
    <div style="margin-bottom:5px"><span style="color:#7a7875;display:inline-block;min-width:52px">WHAT</span>{it.get('whatEn','—')}</div>
    <div style="margin-bottom:5px"><span style="color:#7a7875;display:inline-block;min-width:52px">WHEN</span>{it.get('whenEn','—')}{date_str}</div>
    <div style="margin-bottom:5px"><span style="color:#7a7875;display:inline-block;min-width:52px">WHERE</span>{it.get('whereEn','—')}</div>
    <div style="margin-bottom:14px"><span style="color:#7a7875;display:inline-block;min-width:52px">WHY</span>{it.get('whyEn','—')}</div>

    <!-- divider -->
    <div style="border-top:1px solid #363a40;margin-bottom:12px"></div>

    <!-- Chinese block -->
    <div style="color:#7a7875;font-size:11px;font-family:monospace;margin-bottom:6px">中文 · 五要素</div>
    <div style="margin-bottom:5px"><span style="color:#7a7875;display:inline-block;min-width:52px">何人</span>{it.get('whoCn','—')}</div>
    <div style="margin-bottom:5px"><span style="color:#7a7875;display:inline-block;min-width:52px">何事</span>{it.get('whatCn','—')}</div>
    <div style="margin-bottom:5px"><span style="color:#7a7875;display:inline-block;min-width:52px">何时</span>{it.get('whenCn','—')}</div>
    <div style="margin-bottom:5px"><span style="color:#7a7875;display:inline-block;min-width:52px">何地</span>{it.get('whereCn','—')}</div>
    <div><span style="color:#7a7875;display:inline-block;min-width:52px">为何</span>{it.get('whyCn','—')}</div>

  </div>

  <!-- analysis section -->
  <div style="background:#22252a;padding:14px 20px">
    <div style="color:#7a7875;font-size:11px;font-family:monospace;margin-bottom:10px">
      Analysis · 分析 &nbsp;(AI inference — not confirmed fact · AI推断，非确认事实)
    </div>
    {invest_block}
    {geo_block}
    {career_block}
    {source_link}
  </div>

</div>
""")

    # ── feedback footer ────────────────────────────────────────────────────────
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
  <p style="font-size:11px;color:#444;font-family:Georgia,serif">
    Analysis sections are AI inference — not confirmed fact.
    Always verify before making decisions.<br>
    分析部分为AI推断，非确认事实。<br><br>
    <a href="{open_unsub}"
       style="color:#444;text-decoration:underline;font-size:11px">Unsubscribe</a>
  </p>
</div>

</body>
</html>""")

    return "".join(parts)


# ── email sender ───────────────────────────────────────────────────────────────
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


# ── main ───────────────────────────────────────────────────────────────────────
def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"\n── Intelligence Digest · {today} ──────────────────────")

    # Load data
    subscribers = load_json(SUBSCRIBERS_FILE, [])
    dedup       = load_json(DEDUP_FILE, {})
    print(f"  Subscribers   : {len(subscribers)}")
    print(f"  Dedup history : {len(dedup)} stories")

    if not subscribers:
        print("  No subscribers — exiting.")
        sys.exit(0)

    # Prepare dedup context (last DEDUP_MAX keys)
    recent_keys = list(dedup.keys())[-DEDUP_MAX:]

    # Fetch news — real API or demo mode
    if os.environ.get("DEMO") == "1":
        print("  [DEMO MODE] Skipping Claude API — using hardcoded demo data")
        raw_items = demo_news()
    else:
        print(f"  Fetching {STORY_COUNT} stories via Claude API + web search…")
        try:
            raw_items = fetch_news(recent_keys)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            sys.exit(1)
    print(f"  Received {len(raw_items)} stories")

    # Apply dedup filter
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

    items = filtered if filtered else raw_items   # fallback: send all if all duped
    print(f"  After dedup   : {len(items)} stories")

    # Trim dedup history
    if len(new_dedup) > DEDUP_MAX:
        keys      = list(new_dedup.keys())
        new_dedup = {k: new_dedup[k] for k in keys[-DEDUP_MAX:]}

    save_json(DEDUP_FILE, new_dedup)
    print("  Dedup history saved")

    # Build and send
    subject = f"Intelligence Digest · {today}"
    html    = build_email_html(items, today)
    print(f"  HTML size     : {len(html):,} chars")
    print(f"  Sending to {len(subscribers)} subscriber(s)…")
    send_emails(subscribers, subject, html)

    print(f"\n  ✓ Done — {len(items)} stories → {len(subscribers)} subscriber(s).")
    print("─" * 58)


if __name__ == "__main__":
    main()
