# RAG System Improvements - Requirements & Solutions

> Last updated: 2026-02-02

This document tracks identified issues, required improvements, and potential solutions for the Portuguese Tourism RAG system.

---

## 1. Retrieval Quality: Semantic Gap Problem

### Problem
Queries with abstract/analytical language fail to retrieve articles with descriptive/practical language.

**Example:** Query "What destinations compete with Portugal?" does NOT retrieve "Eight affordable beach holidays in Europe" even though it compares Portugal to Crete, Croatia, and Spain.

### Impact
- Weekly reports miss competitive intelligence
- Semantic search requires query-content language alignment
- Users must phrase queries "just right" to get results

### Potential Solutions

| Solution | Description | Effort | Accuracy |
|----------|-------------|--------|----------|
| **Topic Tagging (Zero-shot)** | LLM classifies each article into topics at embedding time. Reports pull by topic tag. | 1-2 days | Medium-High |
| **Topic Tagging (Supervised)** | Manually label 100+ articles, train classifier | 1 week | High |
| **Hybrid Search (BM25 + Semantic)** | Combine keyword and semantic search | 2-3 days | Medium |
| **Multi-Query Retrieval** | Generate 5 query variations, merge results | 1 day | Medium |
| **Query Expansion** | Automatically add related terms to queries | 1 day | Low-Medium |

### Recommended Approach
**Topic Tagging (Supervised)** for highest accuracy:
1. Define 8-10 topic categories
2. Manually label 100 training articles
3. Train classifier on labeled data
4. Apply to all articles during embedding
5. Weekly reports pull by topic

---

## 2. Chunking Strategy

### Current Implementation
- **Method:** Fixed-size character chunking
- **Chunk size:** 2,000 characters (~500 tokens)
- **Overlap:** 200 characters
- **Location:** `10__embedder.py` lines 173-205

### Known Issues
- Chunks may split mid-sentence or mid-paragraph
- No awareness of natural text boundaries

### Options Considered

| Method | Description | Problem |
|--------|-------------|---------|
| Fixed-size (current) | Cut at 2000 chars | Splits mid-sentence |
| Sentence-based | Group sentences until size limit | Chunks too small |
| Paragraph-based (no limit) | Split at `\n\n` only | Chunks too large |
| LLM-based | Ask LLM to identify sections | Expensive, doesn't scale |
| **Recursive Character** | Try `\n\n` → `\n` → `. ` → ` ` with size limit | ✅ Best balance |

### Recommended: RecursiveCharacterTextSplitter

**Why:** Respects natural boundaries (paragraphs, sentences) while enforcing size limits.

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""]
)
```

### Implementation
Modify `10__embedder.py` to replace the `chunk_text()` function with LangChain's splitter.

---

## 3. Sources Without Cleaners

### Active Feeds Using Generic Cleaner (5 feeds)

These feeds are ACTIVE but fall back to the generic cleaner (less accurate):

| Feed | Category | Priority | Notes |
|------|----------|----------|-------|
| **BBC** | UK General News | Medium | BBC_TRAVEL has cleaner, but general BBC doesn't |
| **DIARIO_NOTICIAS** | Portuguese News | High | Major PT newspaper |
| **JORNAL_ECONOMICO** | Portuguese Economy | Medium | Economic focus |
| **JORNAL_NEGOCIOS** | Portuguese Business | Medium | Business focus |
| **JORNAL_NOTICIAS** | Portuguese News | High | Major PT newspaper |

### Commented-Out Feeds Needing Cleaners (9 feeds)

These feeds are in `00__rss_feeds.py` but disabled because they need cleaners:

| Feed | Category | Priority | Notes |
|------|----------|----------|-------|
| **BREAKING_TRAVEL_NEWS** | Travel Industry | High | Global travel news |
| **ETURBONEWS** | Travel Industry | High | Industry publication |
| **TRAVELPULSE** | Travel Industry | Medium | US-focused |
| **AIR_CURRENT** | Aviation | High | Deep aviation analysis |
| **SUL_INFORMACAO** | Portugal Regional | High | Algarve-specific news |
| **FVW** | Germany Travel Trade | Medium | German market insights |
| **INDEPENDENT_TRAVEL** | UK Travel | High | UK market perspective |
| **AFTENPOSTEN_REISE** | Scandinavia | Medium | Norwegian market |
| **VAGABOND_SE** | Scandinavia | Medium | Swedish market |

### Existing Dedicated Cleaners (34 source patterns → 44 feeds)

```
Portuguese: Público, Observador, Expresso, RTP, Portugal News, Portugal Resident, SAPO, Ambitur
Spanish: El País (5 feeds), El Mundo, ABC, Hosteltur
UK: Guardian (2 feeds), BBC Travel
US: CNN Travel, CNBC (2 feeds), Washington Post, Condé Nast, Travel+Leisure, Skift
French: Le Monde, Le Figaro (2 feeds), Tourmag, L'Echo Touristique
German: FAZ, Spiegel, Sueddeutsche, Zeit, Touristik Aktuell
Other: Al Jazeera, Euronews (2 feeds), ANSA, Simple Flying
```

### Recommended Priority for New Cleaners

1. **DIARIO_NOTICIAS** - Major Portuguese source, currently using generic
2. **JORNAL_NOTICIAS** - Major Portuguese source, currently using generic
3. **BBC** - UK general news (Travel already has cleaner)
4. **INDEPENDENT_TRAVEL** - Fills UK market gap
5. **SUL_INFORMACAO** - Algarve-specific content

---

## 4. Embedding Model

### Current Implementation
- **Model:** `text-embedding-3-small` (OpenAI)
- **Dimensions:** 1536

### Potential Upgrades

| Model | Cost | Quality | Notes |
|-------|------|---------|-------|
| `text-embedding-3-small` (current) | $0.02/1M tokens | Good | Current choice |
| `text-embedding-3-large` | $0.13/1M tokens | Better | 6.5x more expensive |
| `text-embedding-ada-002` | $0.10/1M tokens | Good | Legacy |
| Open-source (e5-large, bge) | Free | Variable | Self-hosted |

### Recommendation
**Keep current model.** The semantic gap is NOT an embedding quality issue - it's a query-content language mismatch that topic tagging will solve.

---

## 5. Database Issues Identified

### Issue: HOSTELTUR Cleaner Failure (FIXED)
- **Problem:** 96% of Hosteltur articles had empty text
- **Cause:** Header trimming couldn't find title in 5000+ char navigation block
- **Fix applied:** 2026-02-02 - Custom header trimming in `clean_hosteltur.py`
- **Result:** 350 articles now cleaned (96.4% success rate)

### Issue: Skift Cleaner Noise (FIXED)
- **Problem:** Skift chunks contained subscription CTAs and podcast content
- **Fix applied:** 2026-02-02 - More aggressive footer trimming
- **Result:** Skift articles now clean

---

## 6. Weekly Report Generation

### Current State
No automated report generation exists. User manually queries the RAG app.

### Required for Weekly Reports
1. **Topic-based retrieval** (not query-based)
2. **Date filtering** (articles from past 7 days)
3. **Section templates** (Competitive Intel, Trends, Aviation, etc.)
4. **LLM summarization** per section

### Proposed Pipeline
```
1. Pull articles by topic + date range
2. Group by topic/section
3. LLM summarizes each section
4. Format into report template
5. Export as PDF/HTML
```

---

## Summary: Recommended Priority

| # | Improvement | Impact | Effort |
|---|-------------|--------|--------|
| 1 | **Topic Tagging (Supervised)** | Fixes retrieval gaps | 1 week |
| 2 | **Semantic Chunking** | Better context preservation | 1 day |
| 3 | **Add INDEPENDENT_TRAVEL cleaner** | UK market coverage | 2 hours |
| 4 | **Add SUL_INFORMACAO cleaner** | Algarve coverage | 2 hours |
| 5 | **Weekly Report Generator** | Automation | 3-4 days |
