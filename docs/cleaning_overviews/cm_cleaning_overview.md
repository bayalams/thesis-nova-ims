# cleaning_overview_correio_manha

**Source ID:** `CORREIO_MANHA`
**Status:** ✅ Implemented & Verified

## Identified Issues
1.  **Massive Footer Noise**:
    - "Comentários" section followed by "Regras da Comunidade", "Termos e Condições", etc. covering 50%+ of the file content.
    - Login prompts ("Para usar esta funcionalidade deverá efetuar login").
    - Radio promotion ("Ouça a Correio da Manhã Rádio").
    - "Recomendados" / "Mais lidas" sections.
2.  **Navigation Artifacts**:
    - "Previous" / "Next" links with images at the top of the file.
    - Specific markdown link blocks: `[Title](Link)` followed by `-----`.
3.  **Video Content**:
    - Users requested to exclude video articles (tagged "Vídeos" or in `/cmtv/`).
4.  **UI Artifacts**:
    - "Seguir Autor", "Guardar", "Ouvir", "Comentar", "Partilhar".
    - "Para si" recommendation headers.
4.  **Repeated Titles**:
    - Titles appearing 2-3 times at the start of the body.

## Cleaning Strategy (`clean_cm.py`)

1.  **Header Trimming**:
    - Removes "CMTV...", "A carregar o vídeo...", and "Previous/Next" blocks found at the start.
    - Uses `trim_header_by_title` to slice content before the main title.
    - Removes duplicate title lines if they persist after slicing.

2.  **Footer Slicing (Aggressive)**:
    - Cuts text immediately upon finding any of these markers:
        - `Comentários`
        - `Tem sugestões ou notícias...`
        - `Para usar esta funcionalidade deverá efetuar login`
        - `Ouça a Correio da Manhã Rádio`
        - `Termos e Condições`
        - `Mais notícias` / `CM ao minuto`
    
3.  **Regex Cleaning**:
    - **Navigation Blocks**: Removes multi-line markdown links `[Title \n --- ](Link)`.
    - **Images**: Removes all markdown images `![Alt](Url)` and multi-line captioned images.
    - **UI Elements**: Strips "Seguir Autor", "Guardar", "Para si", etc.
    - **Separation Markers**: Removes `===` and `---` lines.

## Verification Results
- **Problematic File (`cef47a83...`)**: Successfully reduced from ~20k chars of noise to ~250 chars of valid content (Title + short summary body).
- **Navigation**: Top navigation links and "Previous" artifacts successfully removed.
- **Footers**: Login prompts and massive rules text completely stripped.
