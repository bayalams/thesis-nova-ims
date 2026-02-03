# Die Zeit Cleaning Strategy (DIE_ZEIT)

## Overview
**Source ID**: `DIE_ZEIT`
**Status**: Implemented & Verified
**Cleaner**: `original_code/cleaners/clean_zeit.py`

## Identified Noise Patterns
1.  **Header Noise**:
    - German UI elements: "Benachrichtigung", "Merkliste", "Abspielen", "Wiederholen".
    - "Aktuelles" navigation block appearing before the main title.
    - Navigation arrows ("Pfeil nach links").

2.  **Footer Noise**:
    - **Cookie/Legal**: "Welcome to zeit.de", "Read with advertising".
    - **Navigation**: "### Seitennavigation", "Startseite".
    - **Engagement**: "Antwort schreiben", "Beitrag melden", "Mehr laden", "Link kopieren", "Teilen".
    - **Audio Controls**: "0.5x 0.75x 1.0x".
    - **Reactions**: Emoji strings (`* ⭐️ * ❤️`).

3.  **Inline Noise**:
    - Agency credits: "© dpa-infocom", "Quelle: AFP".
    - Markdown artifacts: Text underline separators (`-----`).
    - Markdown links: Flattened from `[Text](URL)` to `Text`.

## Metadata Enrichment
- **Tags**: Extracted from the footer list (lines starting with `* `).
    - **Filtering**:
        - Removed Generic/UI tags ("Aktuelle Themen", "Facebook").
        - Removed GDPR/Consent strings (long sentences).
        - Removed Emojis.
    - **Result**: Rich tags like "Oberbayern", "Schneefall", "Landtagswahl" extracted.

## Verification
- **Sample Size**: 20 articles.
- **Reduction**: Typically 40-80% reduction in character count.
- **Quality**:
    - Header/Footer cleanly sliced.
    - Body text free of links and UI markers.
    - Metadata field contains rich domain-specific tags.

## Code Location
- `original_code/cleaners/clean_zeit.py`: Contains `clean_die_zeit` and `extract_zeit_tags`.
- `original_code/cleaners/dispatcher.py`: Registered `DIE_ZEIT`.
