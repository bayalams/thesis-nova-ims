# RTP Notícias Cleaning Overview

## 1. Source Characteristics
**Source:** RTP Notícias (`RTP_NOTICIAS`)  
**Type:** Public Broadcaster / General News  
**Structure:**
-   **Header:** contains an extensive navigation menu ("Notícias", "Entrar", "ESPECIAIS", etc.) before the actual content.
-   **Metadata:** Date and Agency (e.g., "Lusa /") often appear as standalone lines at the start of the body.
-   **Footer:** Contains "Tópicos", "PUB" (advertising), and related links.
-   **Multimedia:** Many articles are video/audio clips with no text, characterized by player controls.

## 2. Cleaning Strategy (`clean_rtp.py`)

### A. Video/Audio Filtering
We aggressively filter out articles that contain video player artifacts to avoid polluting the database with empty or low-quality content.
-   **Triggers:** "10s Retroceder (j)", "Entrar em tela cheia (f)", "Reproduzir (k)".
-   **Action:** Returns empty string `""`.
-   **Scraper Behavior:** The scraper (`02__scraper.py`) now detects this empty result and **skips saving** the file entirely.

### B. Header Trimming
The huge navigation menu is removed using two methods:
1.  **Title Match (`trim_header_by_title`)**: We identify the article title in the raw text and cut everything before it.
2.  **Copyright Fallback**: If title matching fails, we look for "© RTP, Rádio e Televisão de Portugal" and cut everything before it.

### C. Body Cleanup
-   **Date/Agency Removal:** Regex patterns remove lines like `8 Janeiro 2026, 11:00`, `atualizado...`, `Lusa /`, and isolated years (`2026`).
-   **Markdown Artifacts:** specific regex removes broken markdown links like `[Title... ===](link)`.
-   **Inline Noise:** Standard `remove_inline_noise` cleans social media embeds and promo text.

### D. Footer Trimming
We truncate the text when encountering:
-   "Tópicos"
-   "PUB"
-   "Instale a app RTP Notícias"

## 3. Known Limitations
-   **Multimedia Context:** Some text articles might have embedded videos; we keep the text but remove the player controls. If an article is *only* a video with a title, it is correctly skipped.
-   **Complex Layouts:** "Great Reports" or "Specials" might have different structures, but the generic cleaner fallback or title trimmer usually handles them adequately.
