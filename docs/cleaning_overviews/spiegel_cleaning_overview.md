# Spiegel Reise Cleaning Overview

## Challenge
Spiegel Reise articles presented severe noise challenges, primarily due to:
1.  **Massive Navigation**: Articles often started with 50+ lines of menu items ("Menü", "* Politik", etc.).
2.  **Paywall Blocks**: Aggressive overlay text ("Diesen Artikel weiterlesen mit SPIEGEL+").
3.  **Multimedia Artifacts**: Numerous `__proto__` placeholders and audio player controls.
4.  **Ad Banners**: "EILMELDUNG" and "Suche starten" injected at the top.

## Solution: `clean_spiegel.py`
A dedicated cleaner was implemented with the following logic:
*   **Smart Header Trimming**: Cuts everything before the title/summary to bypass the initial menu block.
*   **Regex Suppression**: Targeted removal of "EILMELDUNG", "Suche starten", and paywall blocks.
*   **Proto Cleaning**: Specific patterns to remove `__proto_headline__`, `__proto_text__`, etc.
*   **Footer Trimming**: Cuts off the article at known footer markers like "Menü Politik aufklappen" or copyright notices.

## Verification
*   **Script**: `scripts/debug_spiegel_reise.py`
*   **Report**: `project_documentation/debug_spiegel_reise.md`
*   **Results**: The cleaner successfully strips the massive menus and paywalls, leaving clean, readable article text.
