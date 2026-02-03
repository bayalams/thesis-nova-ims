# Cleaning Overview: THE GUARDIAN

## 1. Source Analysis
- **Structure**: Guardian articles in the dataset have **null content** in the standard field but valid text in `scrapingbee.content`.
- **Noise Profile**:
    - **Header**: Massive navigation blocks ("Skip to main content", "Support the Guardian").
    - **Inline**: "Key events" blocks in live blogs, social media embed links `[Share](mailto:...)`, and image carousel artifacts ("Close dialogue", "Toggle caption").
    - **Footer**: "Explore more on these topics", "Most viewed", "Comments", and subscription pleas.

## 2. Cleaning Strategy (`clean_guardian.py`)
- **Content Extraction**: The dispatcher was updated to fallback to `scrapingbee.content` when `content` is null.
- **Header Trimming**:
    - **Title-Based**: Finds the title in the text and cut everything before it.
    - **Date Line Removal**: Aggressive regex (`^\w{3} \d{1,2} \w{3} \d{4}...`) cleans up the timestamp (e.g., "Mon 12 Jan 2026...") that often appears right after the title.
- **Footer Trimming**:
    - **Triggers**: Hard stop on "Explore more on these topics", "Most viewed", "Comments (…)", "Reuse this content".
- **Inline Noise Removal**:
    - **Live Blog TOC**: "Key events" tables are removed to avoid clutter.
    - **Interactives**: "Close dialogue", "Next image", "Toggle caption" artifacts are stripped.
    - **Share Links**: `[Share](mailto:...)` links are filtered out.

## 3. Content Filtering (Strict Allowlist)
**User Requirement**: "Focus on news and travel, nothing else." (Exclude Wellness, Nutrition, Sport).
- **Strategy**: 
    - **Step 1 (Allowlist)**: If tags include `Travel`, `News`, `Politics`, `World`, `UK`, `US`, `Europe`, `Business`, `Environment`, `Science` -> **KEEP** (Even if they also contain blocked tags).
    - **Step 2 (Blocklist)**: If tags include `Health`, `Wellness`, `Nutrition`, `Food`, `Sport`, `Culture`, `Life and style` -> **DROP**.
    - **Step 3 (Default)**: If neither -> **DROP**.
- **Result**: Successfully kept "Winter Walks" (Travel) while removing "Supplements" (Wellness) and "Recipes" (Food).

## 4. Verification
- **Sample Size**: 20 articles.
- **Results**:
    - Articles are now readable, starting immediately with the lead.
    - Footers are cleanly cut before the "Most viewed" or "Explore more" sections.
    - Live blogs retain their updates but lose the messy Table of Contents.
    - **Reduction**: Varies from 20% to 50% depending on the length of the comment section and noise.

## 4. Next Steps
- Monitor for changes in the "Date line" format as it seemed to have variations (e.g. timezones).
- Watch out for "Live" blog variations that might need stricter filtering of updates.
