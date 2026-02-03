# Freshness Filtering & RSS Feed Optimization

**Date:** 2026-01-12  
**Status:** Implemented

## 1. The Issue: Stale Content in RSS Feeds

During verification of the scraping pipeline, we identified a significant issue with data freshness. Specifically, the **CNN Travel** RSS feed was serving articles from **October 2022** (e.g., *"Hong Kong is opening up to tourism -- but is it too late?"*).

### Root Cause
Many "Travel" or "Lifestyle" RSS feeds are not strictly chronological news tickers. Instead, they often include **"evergreen"** or **"featured"** content that remains in the feed for long periods or stays pinned, regardless of the actual publication date.

## 2. The Solution: Date-Based Filtering

To ensure the knowledge base reflects current tourism trends and news, we implemented a **freshness filter** at the indexing stage.

### Implementation Details
Modified `original_code/01__indexer.py` to:
1.  **Parse Publication Dates**: accurate extraction of `published` timestamps from RSS entries.
2.  **Filter Logic**: Automatically skip any article older than a configurable threshold (default: **90 days**).
3.  **CLI Configuration**: Added a `--max-age-days` argument to control this window.

```bash
# Example: Index only articles from the last 30 days
python original_code/01__indexer.py --max-age-days 30
```

## 3. Verification Results

We ran the updated indexer with a 90-day threshold. The filter successfully intercepted stale content across multiple feeds:

| Feed Source | Total Entries | **Skipped (Stale)** | Action |
| :--- | :---: | :---: | :--- |
| **CNN_TRAVEL** | 30 | **30** | ✅ All 2022 articles removed |
| **FAZ** | 65 | **23** | ✅ Older archival news removed |
| **GUARDIAN_GENERAL** | 140 | **4** | ✅ Occasional old features removed |
| **LE_FIGARO_VOYAGES** | 20 | **4** | ✅ Old travel guides removed |

## 4. Impact

-   **Data Quality**: The dataset now strictly contains relevant, recent information specific to current tourism trends.
-   **Efficiency**: Eliminated wasted API credits on scraping outdated articles.
-   **Reliability**: The system is robust against "evergreen" feed behavior without requiring manual curation of sources.
