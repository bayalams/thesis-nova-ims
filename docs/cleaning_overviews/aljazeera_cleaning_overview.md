# AL_JAZEERA Cleaning Overview

This document details the specific cleaning logic applied to `AL_JAZEERA` articles to prepare them for the RAG pipeline.

## 1. Video Page Handling
*   **Identification**: Articles with `/video/` in their URL are identified as video pages.
*   **Action**: These are **skipped completely** (return empty string) as they typically contain minimal text content and are handled by the generic video filter in the dispatcher.

## 2. Structural Cleaning

### Header Trimming
Al Jazeera articles derived from Scrapingbee often contain a large, recurring header block containing navigation links, "Advertisement" markers, and social sharing prompts.

*   **Strategy**: We look for a definitive "end of header" marker.
    *   **Primary Marker**: The word **"Save"** appearing on its own line (usually follows the "Share" buttons).
    *   **Fallback Marker**: The line starting with **"Published On"**.
    *   **Action**: We discard everything preceding this marker.

### Footer Trimming
*   **Constraint**: We remove the large "Cookie Consent" footprint that appears at the bottom of many pages.
    *   **Pattern**: Starts with *"You rely on Al Jazeera for truth and transparency"* and continues with *"We and our ... partners"*.

## 3. Inline Noise Removal

### "Recommended Stories" Lists
Interrupting lists of related articles are inserted into the middle of the text body.
*   **Pattern**:
    ```
    Recommended Stories
    -------------------
    list of X items
    ...
    end of list
    ```
    OR "More from the same show" blocks.
*   **Action**: These blocks are removed entirely using regex.

### Navigation Menus
If header trimming fails to catch them, we specifically remove blocks wrapped in `Navigation menucaret-left ... caret-right`.

### Social Sharing & Interactive Elements
*   **image credits**: `![Image](URL)` are stripped.
*   **Social Buttons**: Text like `click here to share`, `share2`, `Toggle Play` is removed.
*   **Inline Links**: Flattened to plain text (`[Text](URL)` -> `Text`). Standalone link lines are removed.
*   **Separators**: Lines consisting of dashes, underscores, or equals signs (`---`, `___`, `===`) are flushed out.

## 4. Final Output Format
The resulting text block is enriched with metadata and formatted as:
```text
DATE: YYYY-MM-DD
TAGS: Tag1, Tag2 (from metadata)
TITLE: Article Title

[Cleaned Body Text...]
```
