# Feed Optimization Decision

**Date:** 2026-01-12  
**Decision:** Remove low-value RSS feeds to optimize for tourism relevance

## Background

The tourism trend prediction system initially included ~67 RSS feeds. Analysis identified 8 feeds with limited relevance to the project's core objective: predicting tourism trends for Portugal.

## Feeds Removed

| Feed | Reason for Removal |
|------|-------------------|
| `VOGUE_US_TRAVEL` | Fashion-focused, minimal actual travel content |
| `VOGUE_UK_TRAVEL` | Fashion-focused, minimal actual travel content |
| `POINTS_GUY_NEWS` | Credit card/loyalty program focus, not strategic tourism |
| `POINTS_GUY_DEALS` | Deals/promotions, low analytical value |
| `EURONEWS_CULTURE` | Culture content, tangential to travel trends |
| `EUROPEAN_COMMISSION` | Institutional press, slow-updating, low signal |
| `EUROSTAT` | Statistical releases, better accessed via API |
| `TOURISTIK_AKTUELL` | German trade publication, niche market |

## Impact

- **Reduced feed count**: ~67 → ~59 feeds
- **Reduced API costs**: Fewer ScrapingBee credits consumed
- **Improved signal-to-noise ratio**: Knowledge base focuses on tourism-relevant content

## Retained High-Value Categories

| Category | Examples |
|----------|----------|
| **Travel Publications** | CNN Travel, BBC Travel, Skift, Condé Nast Traveler |
| **Tourism Trade** | Hosteltur, Publituris, Ambitur |
| **Source Market News** | El País, Le Monde, FAZ, Telegraph |
| **Aviation** | Simple Flying, IATA, ICAO |
| **Institutional** | UNWTO (kept as authoritative source) |

## Rationale

For a RAG-based trend prediction system, content quality matters more than volume. The removed feeds either:
1. Provided off-topic content (fashion, credit cards)
2. Updated too infrequently to capture trends
3. Served niche audiences outside key source markets
