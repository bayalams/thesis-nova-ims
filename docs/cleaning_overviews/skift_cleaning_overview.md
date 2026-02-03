# Skift Cleaning Overview

**Source**: Skift (Travel Industry News)
**Cleaner File**: `cleaners/clean_skift.py`
**Method**: Regex-based text processing with pre-emptive markdown cleaning.

## Summary
Skift articles contained significant navigational noise in their headers (menus, sector links) and footers (podcast players, related content), as well as pervasive markdown links (`[Text](URL)`). The cleaner was designed to strip this noise while preserving the core article text and the "Summary" section which provides valuable context.

## Key Cleaning Actions

1.  **Markdown & Image Removal (Pre-processing)**
    *   **Action**: Strips all markdown images (`![alt](url)`) and converts markdown links (`[text](url)`) to plain text (`text`).
    *   **Reasoning**: This is done *first* because the raw text often contained navigation items as markdown links (e.g., `* [Latest News](...)`). Removing the link syntax significantly simplified the regex required to match and remove these header lines.

2.  **Date Extraction**
    *   **Action**: Extracts publication date from relative time strings (e.g., `Author Name | 8 hours ago`) using the `scraped_at` timestamp as a reference.
    *   **Note**: Matches "Simple Flying" style date extraction.

3.  **Header Navigation & Summary Removal**
    *   **Action**: Removes ~30 specific navigation patterns.
    *   **Action**: Removes the "Summary" section header (plain text or markdown underline) while keeping the summary content.
    *   **Action**: Removes entire blocks (header + following list) for:
        *   `Articles Referenced:`
        *   `Follow the Hosts:`
        *   `Connect with Skift/Airline Weekly`
        *   `Curated by` / `Early Check-In`
    *   **patterns**:
        *   Main Menu: `* Latest News`, `* Events`, `* Sectors`
        *   Sub-menus: `+ Airlines`, `+ Hotels`, `+ Tourism`
        *   Account actions: `Login`, `Register`, `Subscribe`
    *   **Refinement**: Regex patterns use flexible whitespace matching (`^\s*PATTERN\s*$`) to handle varying indentation.

3.  **Paywall & Cookie Consent Stripping**
    *   **Action**: Removes cookie consent banners (`If you decline...`) and paywall prompts (`Get unlimited access`, `First read is on us`).

4.  **Social & Interactive Element Removal**
    *   **Action**: Removes:
        *   Social share blocks (`* LinkedIn`, `* X`, `* Facebook`)
        *   Audio player controls (`!Play`, `Forward 15 seconds`, `00:00:00`)
        *   Audio player controls (`!Play`, `Forward 15 seconds`, `00:00:00`)
        *   "Ask Skift" AI questions (`* What examples exist...?`)
        *   Podcast promos: `Airline Weekly Lounge`, `Save to Spotify`, `Follow the Hosts`

5.  **Footer Cleanup**
    *   **Action**: Trims content after known footer triggers like "In This Playlist" or "Please ensure Javascript".
    *   **Action**: Removes gibberish lines found in some footers (`mmMwWLli...`).

## Verification status
*   **Verification Script**: `scripts/debug_skift.py`
*   **Status**: Verified on 70 articles.
*   **Result**: 
    *   Headers are clean (no more `* Latest News` lists).
    *   Article body text is plain (no markdown links).
    *   Footers are consistent (ending at Summary or last paragraph).
    *   Noise like `!Play` buttons and `Login` prompts is successfully removed.
