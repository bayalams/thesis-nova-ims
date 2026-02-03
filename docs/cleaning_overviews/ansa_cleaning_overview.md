# ANSA_VIAGGI Cleaning Overview

## Targeted Source
- **Source Key:** `ANSA_VIAGGI`
- **Script:** `clean_ansa.py`
- **Integration:** Registered in `prio_cleaning_draft.py`

## Cleaning Strategy
The cleaning strategy for `ANSA_VIAGGI` focuses on robustly identifying the article body by bypassing heavy header noise, including paywall overlays, and stripping extensive navigation footers.

### 1. Header Cleaning
- **Start Markers:** Prioritizes finding `RIPRODUZIONE RISERVATA` or `Redazione ANSA` within the first **400 lines**.
  - This deep scan is necessary because the raw text often includes a lengthy paywall/cookie consent message at the very top, pushing the actual content down.
- **Fallback Logic:** If no marker is found, it uses a strict list of `header_noise_patterns` to strip navigation menus, metrics, related links, and paywall prompts ("Sei già abbonato ad ANSA.it...").

### 2. Header Cleanup
- **Post-Marker Skip:** Immediately after the start marker, the script iteratively removes "junk lines" that often follow, such as `Condividi`, `* Link copiato`, or separator lines, ensuring the text starts cleanly with the article body.

### 3. Footer Cleaning
- **Triggers:** Identifies the footer using specific phrases:
  - `^Ultima ora\s*-+\s*\d{2}:\d{2}` (Timestamped breaking news)
  - `^Ultima ora$`
  - `^Condividi articolo$`
  - `^Condividi$`
  - `^Ansa\.it\s*Newsletter ANSA`
- **Logic:** Truncates the text at the *first* occurrence of any valid footer trigger found within the body.

### 4. Inline Cleaning
- Removes artifacts like `* Link copiato` or long separator lines (`=====`) that may remain within the body.
- Collapses multiple newlines to ensure readability.

## Verification Results
- **Report:** `project_documentation/ansa_verification.md`
- **Outcome:** The cleaner successfully extracts the core article text while removing:
  - Paywall/Cookie consent overlays.
  - "Ultima Ora" news feeds.
  - Social sharing buttons and "Link copiato" artifacts.
  - Massive navigation menus in the footer.
- **Metrics:**
  - Original lengths: ~27k - 30k characters (highly bloated).
  - Cleaned lengths: ~2k - 4k characters (concise content).

## Usage
The cleaner is automatically invoked by `prio_cleaning_draft.py` when identifying `ANSA_VIAGGI` articles.
