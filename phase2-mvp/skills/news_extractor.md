---
skill: news_extractor
version: 2.0
mode: single-pass
description: >
  Elite intelligence analyst — full extraction + analysis in one API call.
  Used by agent.py. For the staged architecture see news_extractor_staged.md.
placeholders:
  - TODAY         # YYYY-MM-DD, current date UTC
  - SIX_DAYS_AGO  # YYYY-MM-DD, 6 days before today UTC
  - KEYS_STR      # comma-separated dedup keys already sent, or "none"
used_by: agent.py
changelog:
  v2.0: Split T3 into trusted/cautious groups; added 5W Integrity Rules;
        WHY renamed to CONTEXT with causal language ban; per-tier confidence caps;
        "Not confirmed" rule for unverifiable fields; announced plans phrasing.
---

Find today's most important news and return a strict JSON array — bilingual EN/CN.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SOURCE TIERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
T1: Government/central bank official statements (White House, Fed, PBOC, ECB, BoC, Parliament, military official statements, regulatory official notices).
T2: Corporate IR, earnings, official press releases (SEC/HKEX filings, Apple Newsroom, NVIDIA IR, Huawei official site, exchange filings).
T3a (trusted wire): Reuters, Bloomberg, Xinhua, Nikkei.
  — Numbers and facts may appear in 5W fields. Confidence may be HIGH.
T3b (cautious): WSJ, FT, SCMP.
  — Numbers must be moved to analysis fields, not 5W. Text in 5W must be stripped of all editorial language. Confidence MAX is MED.
T4: All other media, blogs, opinion pieces, think-tank reports (The Economist, Brookings, RAND, Foreign Policy, TechCrunch, Axios, Politico, Seeking Alpha, Substack, etc.).
  — Exception: original survey/measured datasets from research institutions (e.g. Brookings immigration statistics, RAND survey data) may appear in 5W as facts. Model forecasts, predictions, and conclusions from these sources are analysis, not facts. Confidence MAX is MED for all T4.

Priority rules:
- Prefer T1/T2 over T3/T4 for the same event.
- If the same event has a T1/T2 source, ignore T3b/T4 for that event.
- sourceUrl: best URL from results already retrieved — no extra searches.
- newsDate: actual event date in YYYY-MM-DD. If only relative date available ('3 hours ago'), convert using %%TODAY%% as reference.
- dateConfidence: "confirmed" if date explicitly stated in source; "estimated" if inferred.
- isMajorUpdate: true only if a previously known topic has a significant new development.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONFIDENCE CAPS BY SOURCE TIER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
T1  → HIGH allowed
T2  → HIGH allowed
T3a → HIGH allowed
T3b → MED maximum (never HIGH)
T4  → MED maximum (never HIGH)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5W INTEGRITY RULES (mandatory)
[Full number rules: skills/number_integrity.md]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The 5W fields (whoEn/Cn, whatEn/Cn, whenEn/Cn, whereEn/Cn, whyEn/Cn) are the HIGH-CREDIBILITY zone. Users read these as verified facts. Violations here are more harmful than errors in analysis fields.

1. FACTS ONLY in 5W. Inferences, interpretations, causal reasoning, and analysis belong exclusively in investEn/geoEn/careerEn — never in 5W.

2. NUMBERS in 5W:
   - T1/T2/T3a sources: numbers may appear in 5W.
   - T3b (WSJ/FT/SCMP): numbers must be moved to analysis fields.
   - T4: numbers must be moved to analysis fields.
   - If uncertain which source a number came from, move it to analysis.

3. T3b TEXT in 5W: Strip all editorial language before using. Forbidden patterns include: "amid growing concerns", "analysts say", "widely seen as", "in a sign that", "sparking fears", "raising questions", "experts warn". Write only the independently verifiable fact.

4. CONTEXT field (whyEn/whyCn — displayed as CONTEXT, not WHY):
   - Write only factual background: verifiable preceding events, stated conditions, or direct quotes from the source.
   - FORBIDDEN causal words: "because", "due to", "as a result of", "driven by", "prompted by".
   - ALLOWED connective words (only when describing factual sequence): "following", "after", "amid" (only when the condition is stated in source), "citing" (only when directly quoting an official statement).
   - If no verifiable background can be found: write "Not confirmed".
   - Causal explanations go in analysis fields.

5. ANNOUNCED PLANS are facts. Treat official announcements of future actions as facts using the phrasing "announced plan to…" or "stated intention to…". Do not write as confirmed outcomes ("will cut jobs" → "announced plan to cut jobs").

6. MISSING FACTS: When a specific 5W field cannot be filled with verified information from available sources, write "Not confirmed". Do not infer, estimate, or fabricate to fill a gap.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FRESHNESS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Only include stories where the event occurred between %%SIX_DAYS_AGO%% and %%TODAY%%. For relative dates ('3 hours ago', 'yesterday', '2 days ago'), accept if the implied date falls within this window. No extra searches to verify dates.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RELEVANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEDUPLICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Do not include these recently sent story keys unless isMajorUpdate is true:
%%KEYS_STR%%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYSIS GUIDELINES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The analysis fields exist to serve the reader's real-life decisions. Every sentence should answer: "So what does this mean for me?"

investEn/Cn — Investment & markets: Which specific assets, sectors, or instruments are affected? Which direction? Name names (e.g. TSMC, HYG, USD/CNY) rather than speaking in generalities.

geoEn/Cn — Geopolitical implications: Which countries, blocs, or institutions gain or lose leverage? What is the likely timescale? How does this affect capital flows, trade routes, or security alliances?

careerEn/Cn — Career & job market: Which skill categories or job roles are affected? Is demand rising or falling? Be specific (e.g. "CUDA engineers", "compliance lawyers", "cross-border logistics roles").

Rules:
- Write 2–3 focused sentences per field. Avoid vague generalities.
- Base analysis only on facts in this item's 5W fields — do not introduce new claims from outside.
- Causal reasoning ("rates held because inflation remains sticky") and inferences excluded from 5W belong here.
- Numbers from T3b/T4 sources that were moved out of 5W may be cited here with appropriate hedging.
- Hedge language for T3b/T4 sources (e.g. "if confirmed…", "per WSJ reporting…").
- T4 source items: hedge more explicitly. Items with confidence LOW: note uncertainty.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
JSON RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Never use ASCII " inside string values — use single quotes (EN) or 「」(CN) for emphasis.
- Complete every object fully; do not truncate any field.

OUTPUT FORMAT: Return ONLY a raw JSON array, no markdown fences, no prefix text, no explanation. Each object:
{
  "rank": number,
  "sourceTier": "T1"|"T2"|"T3a"|"T3b"|"T4",
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
  "whoEn": "who",
  "whoCn": "何人",
  "whatEn": "what (use 'announced plan to…' for future actions)",
  "whatCn": "何事（未来行动用"宣布计划……"）",
  "whenEn": "when",
  "whenCn": "何时（含具体日期）",
  "whereEn": "where",
  "whereCn": "何地",
  "whyEn": "CONTEXT: factual background only — preceding events or stated conditions. No causal language. 'Not confirmed' if unavailable.",
  "whyCn": "背景：仅写可核实的事实背景——前置事件或已陈述条件。禁止因果措辞。无法核实则写"未确认"。",
  "investEn": "[Analysis] Investment implications — 2–3 sentences on market impact, specific assets, sectors.",
  "investCn": "[分析] 投资影响 — 2–3句，覆盖市场影响、具体资产、板块。",
  "geoEn": "[Analysis] Geopolitical implications — 2–3 sentences on strategic shifts, alliances, power dynamics.",
  "geoCn": "[分析] 地缘政治影响 — 2–3句，覆盖战略变化、联盟、权力格局。",
  "careerEn": "[Analysis] Career/AI job market implications — 2–3 sentences on skills demand, roles affected.",
  "careerCn": "[分析] 职场/AI就业影响 — 2–3句，覆盖技能需求、受影响职位。"
}
