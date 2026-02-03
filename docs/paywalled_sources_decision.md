# Paywalled Sources Removal Decision

**Date:** 2026-01-12  
**Decision:** Remove NYT and WSJ sources from RSS feed configuration

## Background

As part of building a RAG-based tourism trend prediction system, we collected news articles from ~60 RSS feeds across multiple source markets. The scraping process uses ScrapingBee API credits to fetch full article content.

## Problem Identified

Analysis of multiple scraping runs revealed that certain sources consistently failed due to paywall restrictions:

| Source | Total Attempts | Successes | Failures | Success Rate |
|--------|---------------|-----------|----------|--------------|
| `WSJ` | 20 | 0 | 20 | **0%** |
| `NYT_TRAVEL` | 17 | 6 | 11 | **35%** |
| `NYT_WORLD` | 311 | 150 | 161 | **48%** |

## Cost Analysis

ScrapingBee charges per API request regardless of whether the request returns usable content. Failed requests to paywalled sources result in:

- **192+ wasted API credits** per scraping cycle
- Polluted dataset with incomplete/empty articles
- Reduced signal-to-noise ratio in the knowledge base

## Decision

**Remove the following sources from `00__rss_feeds.py`:**
1. `WSJ` (Wall Street Journal) - Hard paywall, 0% success
2. `NYT_TRAVEL` (New York Times Travel) - Metered paywall, 35% success
3. `NYT_WORLD` (New York Times World) - Metered paywall, 48% success

## Sources Retained

The following sources were initially suspected to have paywall issues but empirical testing showed they work well:

| Source | Success Rate | Status |
|--------|-------------|--------|
| `LE_MONDE` | 100% | ✅ Retained |
| `FAZ` | 100% | ✅ Retained |
| `DIE_ZEIT` | 100% | ✅ Retained |
| `TELEGRAPH` | 95% | ✅ Retained |
| `WASHINGTON_POST` | 100% | ✅ Retained |

## Impact

- **Reduced scraping costs** by eliminating ~192 wasted credits per cycle
- **Improved data quality** by removing incomplete articles
- **Maintained coverage** through 50+ other high-quality sources including:
  - CNN Travel, CNBC Travel (USA)
  - BBC, Guardian, Telegraph (UK)
  - El País, El Mundo (Spain)
  - Le Monde, Le Figaro (France)
  - Die Zeit, FAZ, Spiegel (Germany)

## Implementation

Change made to `original_code/00__rss_feeds.py`:
- Removed 3 feed entries
- Added comment documenting the removal reason
