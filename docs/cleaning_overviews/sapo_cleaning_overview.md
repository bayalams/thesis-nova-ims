# Sapo Notícias Cleaning Overview

## Source Characteristics
*   **Source Name**: `SAPO` (covers SAPO_VIAGENS, SAPO_NOTICIAS, ECO_SAPO, etc.)
*   **Content**: General news, technology, travel, economy.
*   **Structure**:
    *   Often starts with "Menu", "Inicie sessão", or navigation headers.
    *   Frequently includes AI-generated summaries ("Ler Resumo", "Ouvir Artigo") at the very top.
    *   Strong footer sections with "Tópicos", "Mais Recentes", "Comentários".
    *   Dates often appear in the body as "12 Janeiro 2026".

## Cleaning Strategy (`clean_sapo.py`)

### 1. Pre-Processing
*   **"Ler Artigo Completo" Trim**: Checks the first 2000 characters for the phrase "Ler Artigo Completo". If found, aggressively removes everything before it. This single step eliminates most AI summaries and header noise.

### 2. Header Cleaning
*   **Title Trimming**: Standard title-based trimming.
*   **Aggressive Regex**: Removes blocks starting with "### Menu", "Toggle navigation", "Inicie sessão" if they persist.

### 3. AI & Audio Artifacts
*   Specific regexes to remove:
    *   "Voz gerada por inteligência artificial"
    *   "Ouvir Resumo" / "Ouvir Artigo"
    *   "Este resumo foi criado com recurso a inteligência artificial"
    *   "SAPO](#)" artifacts.

### 4. Footer Trimming
*   Trims text after specific triggers:
    *   "### Tópicos"
    *   "#### Continua a fazer scroll"
    *   "TAMBÉM PODE GOSTAR"
    *   "Mais Recentes"
    *   "Comentários"
    *   "Veja também"

### 5. Video & Interactives
*   Removes "Beginning of dialog window" (video player modal text).
*   Removes "Partilha" buttons.

### 6. Date & Metadata
*   Removes isolated date lines (e.g., "12 Janeiro 2026", "2026/01/05").
*   Removes repeated source names like "Marketeer".

## Known Limitations
*   Some older articles might have different HTML structures not caught by the "Ler Artigo Completo" trigger.
*   Embedded social media posts (Tweets, Instagram) might leave residual text if not fully handled by the generic `remove_inline_noise`.
