# Expresso Cleaning Overview & Decisions

**Status**: Verified & Completed
**Date**: 2026-01-15
**Feed**: `https://feeds.feedburner.com/expresso-geral`

## 1. Core Decisions

### Strategy: Strict Allowlist + Tag Mapping
Instead of a blocklist (removing bad articles), we shifted to a **Strict Allowlist** approach to ensure high relevance.
- **Goal**: Only keep news related to Politics, Society, International affairs, and Lifestyle (Boa Cama Boa Mesa).
- **Reasoning**: The "Geral" feed is too broad, containing noise like "Opinião", "Blitz", "Economia" (stock market), and Podcasts which are not useful for RAG.

### Allowed Categories
1. **Política**
2. **Sociedade**
3. **Internacional**
4. **Boa Cama Boa Mesa**

### Tag Mapping (The "Rescue" Logic)
To prevent losing relevant articles that use specific sub-tags (e.g., "Venezuela") but lack the main category tag, we implemented a mapping system.

| Tag Found | Mapped To | Action |
| :--- | :--- | :--- |
| `Presidenciais 2026`, `Governo`, `Parlamento`, `Partidos`, `Justiça` | **Política** | ✅ Keep |
| `Venezuela`, `Ucrânia`, `EUA`, `Europa`, `Brasil` | **Internacional** | ✅ Keep |
| `Saúde`, `Transportes` (Metro), `Segurança` (Police), `Imobiliário` | **Sociedade** | ✅ Keep |
| `Obituário`, `Religião` | *None* | ❌ Remove |

## 2. Cleaner Implementation (`clean_expresso.py`)

### Structural Cleaning
- **Header Trimming**: Removes "Últimas Notícias", "Parceiros", and journalist metadata at the start.
- **Footer Trimming**: Removes "Mais Partilha", "Comentários", and subscription banners.
- **Noise Blocks**: Actively removes internal links like `* Blitz`, `* Opinião` that appear inside article bodies.
- **Audio/Video Artifacts**: Removes specific player controls:
  - `Aumentar o Volume↑`
  - `Diminuir o Volume↓`
  - `00:00 / 00:00` timestamps
  - `Ouvir este artigo`

### Content Redaction
- **Links/Images**: All Markdown links `[Text](Url)` and Images `![Alt](Url)` are stripped to keep only text.
- **Dates**: Removed dates like "8 de janeiro de 2026" from the body text to prevent staleness in vector search context.

## 3. Scraper Optimization (`should_scrape`)

**Crucial Optimization**:
We moved the filtering logic *upstream* to the Scraper (`02__scraper.py`).
- **Before**: Download everything -> Clean -> Discard 50% of articles.
- **After**: Check tags/URL **before** downloading.
  - If tag is `Opinião` or `Blitz`: **SKIP download**.
  - If URL contains `/video/` or `/podcast/`: **SKIP download**.
- **Benefit**: Saves API credits (ScrapingBee) and processing time.

## 4. Verification Results
- **Opinião**: 100% Removed.
- **Podcasts**: 100% Removed.
- **Venezuela/Transportes**: successfully kept via mapping.
- **Cleanliness**: Articles are dense text, free of "subscribe" buttons and navigation noise.
