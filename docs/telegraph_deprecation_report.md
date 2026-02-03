# Decision Report: Deprecation of The Telegraph as a Data Source
**Date:** 2026-01-20
**Status:** Deprecated

## Executive Summary
We have decided to **drop The Telegraph** from the data pipeline. This decision is based on a cost-benefit analysis revealing that the source contributes negligible value (<0.1% of dataset) while requiring disproportionately high maintenance due to aggressive anti-scraping measures and feed noise.

## Key Metrics & Analysis

| Metric | Value | Context |
| :--- | :--- | :--- |
| **Total Articles in Dataset** | ~7,370 | Across 40+ sources |
| **Telegraph Articles Found** | 20 | 0.27% of total |
| **Relevant Articles** | ~7 | **0.09% of total** (after filtering non-travel) |
| **Technical Complexity** | High | Required custom regex for nav menus, footer noise, and extensive filtering |

## Rationale for Deprecation

1.  **Low Relevance Yield**: The vast majority of scraped content was irrelevant (recipes, sports scores, football match reports, gardening), requiring complex filtering logic. Only ~7 articles were actual travel/global-health content.
2.  **High Noise Ratio**: The structure of Telegraph pages includes massive navigation menus (~3,000 characters) and dynamic footers that made clean text extraction difficult and fragile.
3.  **Redundant Coverage**: The travel and global news topics are already overwhelmingly covered by higher-quality, easier-to-scrape sources in our confirmed list:
    *   *Travel*: Condé Nast Traveler, BBC Travel, NYT Travel, Travel + Leisure
    *   *Global News*: BBC, The Guardian, NYT World, Al Jazeera

## Action Plan
1.  **Code Removal**: Delete `cleaners/clean_telegraph.py`.
2.  **Pipeline Update**: Remove Telegraph routing from `cleaners/dispatcher.py`.
3.  **Scraper Block**: Update `02__scraper.py` to explicitly ignore `TELEGRAPH` source to prevent future API credit usage.
4.  **Data Cleanup**: Existing Telegraph data will be ignored/archived.

**Conclusion:** Dropping this source significantly simplifies the codebase without any meaningful impact on the knowledge base's quality or coverage.
