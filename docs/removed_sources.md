# Removed Sources Registry

This document tracks all RSS feed sources that have been removed from the pipeline since project inception.

**Last Updated:** 2026-01-23

---

## Summary

| Category | Count |
|----------|-------|
| Paywall Issues | 3 |
| Low Relevance / Off-Topic | 8 |
| High Noise / Low Value | 1 |
| Broken Feeds (404) | 10 |
| No Cleaner / Paused | 12 |
| **Total Removed** | **34** |

---

## 1. Paywall Issues

**Decision Date:** 2026-01-12  
**Documentation:** `paywalled_sources_decision.md`

| Source | Reason | Success Rate |
|--------|--------|--------------|
| WSJ | Hard paywall | 0% |
| NYT_TRAVEL | Metered paywall | 35% |
| NYT_WORLD | Metered paywall | 48% |

---

## 2. Low Relevance / Off-Topic

**Decision Date:** 2026-01-12  
**Documentation:** `feed_optimization_decision.md`

| Source | Reason |
|--------|--------|
| VOGUE_US_TRAVEL | Fashion-focused, minimal actual travel content |
| VOGUE_UK_TRAVEL | Fashion-focused, minimal actual travel content |
| POINTS_GUY_NEWS | Credit card/loyalty program focus, not strategic tourism |
| POINTS_GUY_DEALS | Deals/promotions, low analytical value |
| EURONEWS_CULTURE | Culture content, tangential to travel trends |
| EUROPEAN_COMMISSION | Institutional press, slow-updating, low signal |
| EUROSTAT | Statistical releases, better accessed via API |
| TOURISTIK_AKTUELL | German trade publication, niche market |

---

## 3. High Noise / Low Value

**Decision Date:** 2026-01-20  
**Documentation:** `telegraph_deprecation_report.md`

| Source | Reason |
|--------|--------|
| TELEGRAPH | <0.1% relevant content after filtering; high noise (sports, recipes, gardening); redundant coverage by BBC/Guardian |

---

## 4. Broken Feeds (404 Errors)

**Status:** Feed URLs return HTTP 404 or are otherwise inaccessible.

| Source | Original URL |
|--------|--------------|
| SIC_NOTICIAS | `https://sicnoticias.pt/feed/` |
| TSF_RADIO | `https://www.tsf.pt/rss/` |
| ACORIANO_ORIENTAL | `https://www.acorianooriental.pt/rss` |
| TIME_OUT_LISBOA | `https://www.timeout.pt/lisboa/feed` |
| TIME_OUT_PORTO | `https://www.timeout.pt/porto/feed` |
| LONELY_PLANET | `https://www.lonelyplanet.com/feed.xml` |
| ANA_AEROPORTOS | `https://www.ana.pt/pt/feed` |
| IATA | `https://www.iata.org/en/pressroom/news/rss/` |
| ICAO | `https://www.icao.int/Newsroom/Pages/NewsRSS.aspx` |
| UNWTO | `https://www.unwto.org/news/format/rss` |

---

## 5. No Cleaner / Paused

**Status:** Sources without dedicated cleaning logic or paused by user request.

| Source | Reason | Status |
|--------|--------|--------|
| CORREIO_MANHA | Paywalled / Video-heavy | Removed |
| PUBLITURIS | User request | Paused |
| BREAKING_TRAVEL_NEWS | No cleaner developed | Commented out |
| ETURBONEWS | No cleaner developed | Commented out |
| TRAVELPULSE | No cleaner developed | Commented out |
| AIR_CURRENT | No cleaner developed | Commented out |
| SUL_INFORMACAO | No cleaner developed | Commented out |
| FVW | No cleaner developed | Commented out |
| INDEPENDENT_TRAVEL | No cleaner developed | Commented out |
| AFTENPOSTEN_REISE | No cleaner developed | Commented out |
| VAGABOND_SE | No cleaner developed | Commented out |
| AP_NEWS | No cleaner developed | Commented out |

---

## Notes

- Sources in categories 1-3 have formal decision documents in `project_documentation/`.
- Broken feeds (category 4) may be re-evaluated periodically in case URLs are restored.
- Sources without cleaners (category 5) can be re-activated once appropriate cleaning logic is developed.
