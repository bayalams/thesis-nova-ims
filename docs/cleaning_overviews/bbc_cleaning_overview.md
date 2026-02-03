# BBC_TRAVEL Cleaning Overview

## Source Characteristics
- **Source ID**: `BBC_TRAVEL`
- **Content Format**: Markdown (converted from HTML via ScrapingBee).
- **Key quirk**: The primary `text` field in the JSON is often empty or null. The valid content is found in `scrapingbee.content`.
- **Structure**:
  - **Header**: Massive navigation menu (Home, News, Sport, etc.) followed by a repeated Title and H1 underline (`=====`).
  - **Metadata**: Lines like "1 day ago", "Share", "Save", and Author credits appear between the header and the body.
  - **Body**: Standard Markdown with images (`![...]`), links, and some inline noise (e.g. "Follow live updates" blocks).
  - **Footer**: Sections like "More from the BBC", "Related", and "Top Stories" lists.

## Cleaning Strategy (`clean_bbc.py`)

1.  **Header Extraction**:
    - **Method**: Regex search for the H1 underline characteristic (`\nTitle Line\n=====`).
    - **Cut**: Everything before the end of the underline is discarded.
    - **Fallback**: If H1 pattern isn't found, falls back to searching for the metadata title.

2.  **Metadata Removal**:
    - Post-header lines are scanned and removed if they match noise patterns:
        - Timestamps ("1 day ago", "9 hours ago").
        - Social actions ("Share", "Save").
        - Lead images (`![...]`).
        - Author lines (heuristic based on length and keywords like "BBC", "Editor").

3.  **Footer Truncation**:
    - Truncates text at specific markers:
        - `^More from the BBC$`
        - `^Related$`
        - `^Copyright \d{4} BBC`
        - `^If it is safe to do so, you can get in touch`

4.  **Tag Extraction**:
    - Scans the bottom of the article (text immediately preceding the footer cut).
    - Extracts short lines that look like tags (e.g. "Asia", "South Korea").
    - Flattens markdown links in tags (e.g., `[Tag](url)` -> `Tag`).
    - Adds them to metadata and removes them from the body text.

5.  **Inline Cleaning**:
    - Removes images (`![...](...)`).
    - Removes "Getty Images" artifacts (including those starting with `!`).
    - Removes "Share"/"Save" buttons that repeat in the body.
    - Removes "Follow live updates" multiline link blocks.
    - Removes separator lines (`----`, `====`).
    - Flattens standard Markdown links to plain text.

## Verification
- Verified against a sample of 5 articles.
- Text length reduced by ~30-50% (removing huge menus/footers).
- Body text remains coherent with correctly stripped headers.
