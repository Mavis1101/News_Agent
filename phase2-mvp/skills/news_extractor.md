---
skill: news_extractor
version: 1.0
mode: single-pass
description: >
  Elite intelligence analyst — full extraction + analysis in one API call.
  Used by agent.py (V1 minimal). For the staged architecture see news_extractor_staged.md.
placeholders:
  - TODAY         # YYYY-MM-DD, current date UTC
  - SIX_DAYS_AGO  # YYYY-MM-DD, 6 days before today UTC
  - KEYS_STR      # comma-separated dedup keys already sent, or "none"
used_by: agent.py
---

Find today's most important news and return a strict JSON array — bilingual EN/CN.

SOURCE TIERS:
T1: Government/central bank official statements (White House, Fed, PBOC, ECB, BoC, Parliament).
T2: Corporate IR, earnings, official press releases (SEC/HKEX filings, Apple Newsroom, NVIDIA IR).
T3: Reuters, Bloomberg, Xinhua, FT, Nikkei, WSJ, SCMP.
T4: Other media, blogs, opinion — confidence MAX is MED.
- Prefer T1/T2 over T3/T4 for the same event.
- sourceUrl: best URL from results already retrieved — no extra searches.
- newsDate: actual event date in YYYY-MM-DD. If only a relative date is available ('3 hours ago'), convert using %%TODAY%% as reference.
- dateConfidence: "confirmed" if date is explicitly stated in source; "estimated" if inferred from relative time or context.
- isMajorUpdate: true only if a previously known topic has a significant new development.

FRESHNESS: Only include stories where the event occurred between %%SIX_DAYS_AGO%% and %%TODAY%%. For relative dates ('3 hours ago', 'yesterday', '2 days ago'), accept if the implied date falls within this window. No extra searches to verify dates.

RELEVANCE — include only stories serving one of these needs:

AI/Tech (topic: tech):
- New models, chips, or infrastructure with industry or investment impact
- M&A, strategic pivots, partnerships, leadership changes at leading AI/semiconductor companies
- Government policy or regulation targeting AI/tech
- EXCLUDE: incremental updates, dev tools with no business impact, research papers without near-term relevance

Geopolitics (topic: geo):
- Active conflicts, military moves, or treaty changes affecting global stability
- Alliance shifts (US-China, NATO, ASEAN) with trade, security, or capital flow consequences
- Sanctions, export controls, or diplomatic ruptures with economic consequences
- EXCLUDE: routine diplomatic statements with no policy outcome, regional disputes with no global spillover

Macro/Policy (topic: macro):
- Central bank decisions and signals (Fed, PBOC, ECB, BoC) on rates, liquidity, or currency
- Fiscal policy, tariffs, or trade rules affecting US, China, or Canada
- Macro data surprises (CPI, jobs, GDP) shifting market expectations
- Policy affecting life decisions: immigration, tax, cross-border mobility between US/China/Canada
- EXCLUDE: minor indicators with no market impact, local policy with no cross-border effect

DEDUPLICATION: Do not include these recently sent story keys unless isMajorUpdate is true:
%%KEYS_STR%%

JSON RULES:
- Never use ASCII " inside string values — use single quotes (EN) or 「」(CN) for emphasis.
- Complete every object fully; do not truncate any field.

ANALYSIS GUIDELINES:
- Write 2–3 sentences per analysis field on: specific assets/sectors (invest), strategic shifts (geo), skills/roles affected (career).
- Base analysis only on facts in the same item; hedge more for T4 sources.

OUTPUT FORMAT: Return ONLY a raw JSON array, no markdown fences, no prefix text, no explanation. Each object:
{
  "rank": number,
  "sourceTier": "T1"|"T2"|"T3"|"T4",
  "source": "Source name (English)",
  "sourceCn": "来源名称（中文）",
  "sourceUrl": "URL",
  "topic": "tech"|"geo"|"macro",
  "confidence": "HIGH"|"MED"|"LOW",
  "newsDate": "YYYY-MM-DD",
  "dateConfidence": "confirmed"|"estimated",
  "isMajorUpdate": false,
  "updateNote": "",
  "headlineEn": "English headline (primary, concise and specific)",
  "headlineCn": "中文标题",
  "whoEn": "who",       "whoCn": "何人",
  "whatEn": "what",     "whatCn": "何事",
  "whenEn": "when",     "whenCn": "何时（含具体日期）",
  "whereEn": "where",   "whereCn": "何地",
  "whyEn": "why",       "whyCn": "为何/背景",
  "investEn": "[Analysis] Investment implications — 2–3 sentences on market impact, specific assets, sectors.",
  "investCn": "[分析] 投资影响 — 2–3句，覆盖市场影响、具体资产、板块。",
  "geoEn": "[Analysis] Geopolitical implications — 2–3 sentences on strategic shifts, alliances, power dynamics.",
  "geoCn": "[分析] 地缘政治影响 — 2–3句，覆盖战略变化、联盟、权力格局。",
  "careerEn": "[Analysis] Career/AI job market implications — 2–3 sentences on skills demand, roles affected.",
  "careerCn": "[分析] 职场/AI就业影响 — 2–3句，覆盖技能需求、受影响职位。"
}
