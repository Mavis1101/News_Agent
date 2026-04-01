---
skill: number_integrity
version: 1.0
description: >
  Rules governing which numbers may appear in 5W fields vs. analysis fields.
  Loaded by: news_extractor.md (single-pass), news_extractor_staged.md (Stage 1).
  NOT needed by: news_analyst.md (Stage 2 — analysis only, no 5W writing).
used_by: agent.py (via news_extractor.md), agent_staged.py Stage 1
---

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NUMBER INTEGRITY RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Numbers in 5W fields are read by users as verified facts. A wrong or unsourced number here is more harmful than an error in analysis, because users have no reason to question it.

WHICH SOURCES MAY PUT NUMBERS IN 5W:

  T1  → ✓ numbers allowed in 5W
  T2  → ✓ numbers allowed in 5W
  T3a (Reuters, Bloomberg, Xinhua, Nikkei) → ✓ numbers allowed in 5W
  T3b (WSJ, FT, SCMP) → ✗ numbers must go to analysis fields
  T4  → ✗ numbers must go to analysis fields

RESEARCH INSTITUTION EXCEPTION (T4):
  - Original survey/measured data (e.g. Brookings immigration survey counts,
    RAND field data) → may appear in 5W as facts.
  - Model outputs, forecasts, projections, index scores → analysis only.
  - The Economist numbers: treat as T4. Their figures are often model-derived
    or editorially adjusted — move to analysis unless explicitly sourced to
    a primary dataset.

WHEN YOU ARE UNCERTAIN which source a number came from:
  → Move it to analysis. Do not guess.

HOW TO CITE NUMBERS MOVED TO ANALYSIS:
  - Add source context: "per WSJ reporting…", "per FT estimates…"
  - Add hedging for T4: "if confirmed…", "according to Brookings projections…"

ANNOUNCED PLAN NUMBERS:
  - Numbers in official announcements of future actions are facts.
  - Write: "announced plan to invest $2B" not "will invest $2B"
  - The announcement is the verifiable fact; the outcome is not yet confirmed.
