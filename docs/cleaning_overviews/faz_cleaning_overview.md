# FAZ Cleaning Overview & Decisions

**Status**: Verified Clean (Truncated)
**Date**: 2026-01-15
**Feed**: FAZ RSS
**Relevance**: Limited (Teaser Only - High Prestige Source)

## 1. Core Decisions

### Strategy: Aggressive Header/Paywall Trimming
FAZ has arguably the "noisiest" raw HTML of all sources processed so far.
- **Problem 1 (Header)**: A 60-line navigation menu appears before every article.
- **Problem 2 (Paywall)**: The full text is hidden behind a hard paywall. Only 1-3 paragraphs are available.
- **Problem 3 (Pollution)**: Immediately after the paywall cutoff, the page displays teasers for 5-10 *other* articles ("Das Beste von FAZ+"), which pollutes the vector search context.

### Solution: The "Teaser Only" Compromise
We decided to keep FAZ because it is a high-authority source, but we accept that we only get the introduction.
- **Action**: We aggressively cut off text at the first sign of the paywall (`FAZ+`, `WEITER`). This ensures **zero pollution** from unrelated articles, even though the text is short.

## 2. Cleaner Implementation (`clean_faz.py`)

### Structural Cleaning
- **Header Trimming (Smart Title Search)**:
  - We search for the *Article Title* within the first 300 lines of the body.
  - If found, we cut everything before it.
  - If not found, we use backup markers like "SportÖffnen" or "Direkt zum Hauptinhalt".
  - **Result**: The massive navigation menu is 100% removed.

- **Footer/Paywall Extraction (Hard Stop)**:
  - Instead of standard footer trimming, we implement a **HARD STOP (`break`)**.
  - **Triggers**:
    - `FAZ+\n### Zugang zu allen FAZ+ Beiträgen`
    - `* Mit einem Klick online kündbar`
    - `WEITER\nWEITER`
    - `Login`
  - **Result**: Text ends cleanly at the paywall. No cross-article contamination.

- **Functional Links**:
  - Removed top-of-article links: `Anhören`, `Merken`, `Teilen`.

## 3. Verification Results
- **Cleanliness**: Excellent. No menu, no footer, no "Read More" blocks.
- **Completeness**: Low (~200 to ~3000 chars).
- **Verdict**: Safe for RAG (no noise), but low information density.

## 4. Relevance Assessment
FAZ is a Tier 1 source for German politics/finance. Despite being truncated, the teasers often contain the core news lead ("Lead Paragraph"). For a "News Briefing" use case, this is acceptable. For "Deep Research", it is insufficient.
