# Publico Cleaning Overview

**Source**: Publico (General News)
**Cleaner**: `cleaners/clean_publico.py`
**Date Refined**: 2026-01-19

## Scraping Difficulties & Challenges
Publico proved to be one of the more challenging sources due to a combination of persistent header noise, extensive footer sections that mimicked content, and inconsistent metadata.

1.  **Audio & Sponsor Noise at Start**:
    *   Articles frequently begin with "Com o apoio", "Ouça este artigo", or audio player timestamps (e.g., "00:00").
    *   These elements are not standardized in a single block, requiring a line-by-line "seeking" approach to find the first paragraph of real content.

2.  **Deceptive Footers**:
    *   The footer sections are vast and text-heavy, including "Fórum Público", "Tópicos disponíveis", "Notificações bloqueadas", and extensive "Em destaque" lists.
    *   Crucially, these often use headers (e.g., `##### Lazer`) that look like legitimate article subheaders, making simple cutoff logic risky without specific triggers.

3.  **Metadata Specificity**:
    *   The `tags` provided in the JSON are often hyper-specific (e.g., "Anthony Bourdain") rather than useful categories (e.g., "Fugas", "Mundo").
    *   This required a fallback strategy of parsing the URL (e.g., `.../fugas/entrevista/...`) to extract the broader section name.

4.  **Content Separation & Paywalls**:
    *   Inline paywall prompts ("Para continuar a ler este artigo assine o PÚBLICO") appear midway or at the end.
    *   Visual separation markers (e.g., `=======`) were present in the text body, requiring specific regex removal.

5.  **Exclusive Content & Subscription Gates**:
    *   A significant portion of articles are marked as "Exclusivo".
    *   **Data limitation**: Analysis shows these articles are significantly shorter on average (~7k chars vs ~21k chars for normal articles), confirming that for many "Exclusivo" items, we are likely only capturing a teaser or truncated portion of the text before the hard paywall cuts it off.
    *   They also frequent "Assine já" calls to action which require strict filtering.

6.  **Non-Article Content**:
    *   A significant number of items were "Opinião", "Crónica", or "Newsletters" (branded as "Despertador"), which are not suitable for the knowledge base and needed strict filtering.

## Cleaning Strategy implementation

### 1. Dedicated `clean_publico.py`
We moved away from the generic cleaner to a dedicated module to handle the specific "seeking" logic required for the header and the multi-trigger list required for the footer.

### 2. Header "Seeking" Logic
Instead of a simple skip, the cleaner iterates through the first lines of the text. It identifies known noise phrases ("Com o apoio", "Ouça este artigo") and **skips** them. It considers the article to have "started" only when it encounters a line that is NOT noise and is of substantial length (avoiding short navigation links).

### 3. Aggressive Footer Truncation
We implemented a "shortest cutoff" strategy using a comprehensive list of triggers:
*   **Phrases**: "Fórum Público", "Continuar a ler", "Seguintes tópicos", "Notificações bloqueadas".
*   **Patterns**: `##### ` headers (often used for footer lists like "Lazer"), `* Aprovados` comments sections, and markdown image links `![]`.

### 4. Tag Enrichment
To fix the specific tags issue, we added logic to parse the URL path.
*   *Input*: URL `.../fugas/entrevista/zamir-gotta...` + Tag `['Anthony Bourdain']`
*   *Output*: Tags `['Fugas', 'Anthony Bourdain']`

### 5. Filtering & Sanitization
*   **Filters**: Explicitly drop articles with "Opinião", "Crónica", "Newsletter", "Briefing" in tags or title.
*   **Sanitization**:
    *   Remove all Markdown links `[text](url)` -> `text`.
    *   Remove all Markdown images `![]()`.
    *   Remove separation lines `-------` or `=======`.

## Verification
A specialized debug script `scripts/debug_publico.py` was used to verify 20 random articles.
*   **Result**: Clean content with no header audio prompts, no footer lists, and improved, broader tags.
*   **Report**: `project_documentation/debug_publico.md`
