# AMBITUR Cleaning Overview

This document details the cleaning logic applied to `AMBITUR` articles.

## 1. Header Cleaning
*   **Repeated Titles**: Removal of Markdown link lines at the start that duplicate the title or link to images.
*   **Metrics**: Stripped lines containing strings like `PARTILHAS`, `VISUALIZAÇÕES`, `Tempo de leitura`.
*   **Artifacts**: Removal of `em`, `0`, and other standalone artifacts.

## 2. Footer Trimming
*   **Related Articles**: The massive lists of related links at the bottom (e.g. `### [Title](URL)`) are removed.
*   **Subscription/Login**: Removed "Welcome Back", "Login", "Register" widgets.
*   **Noise**: Removed "Sem resultado", "Ver todos os resultados".

## 3. Inline Noise
*   **Functional Links**: Lines that are just links (widgets) are removed.
*   **Inline Links**: Flattened to plain text (`[Text](URL)` -> `Text`).
*   **Markdown Images**: Completely stripped (`![...](...)`).

## 4. Final Output
Enriched with:
```text
DATE: YYYY-MM-DD
TAGS: Tag1, Tag2 (from metadata)
TITLE: Article Title

[Cleaned Body Text...]
```
