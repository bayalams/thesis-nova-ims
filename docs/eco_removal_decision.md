# Decision Report: Removal of ECO (ECO_ONLINE) Source

## 1. Executive Summary
The **ECO (Economia Online)** source has been **removed** from the active RAG pipeline.
**Reason**: Strict lack of relevance to the project's core domain (**Tourism**). Analysis revealed the source is almost exclusively focused on **Corporate Finance, Stock Markets, and General Economics**, with negligible coverage of the tourism sector.

## 2. Context & Objective
The RAG pipeline is designed to answer user queries related to **Tourism**, **Travel**, and **Hospitality** in Portugal and Europe.
We evaluated ECO as a potential source for "business-side" tourism news (e.g., hotel chains, airline mergers).

## 3. Analysis Findings
We performed a verification run on a random sample of 20 articles (`eco_verification.md`).
- **Relevance Score**: **0/20** articles were directly relevant to Tourism.
- **Content Breakdown**:
    - **Stock Markets**: Galp/Moeve merger, Nvidia, PSI-20.
    - **Macroeconomics**: ECB interest rates, inflation data.
    - **Politics**: Government budget, election campaigns.
    - **Corporate**: Executive appointments, banking regulations.

While ECO is a high-quality source for financial news, it acts as **noise** in a specialized Tourism knowledge base. Any major tourism-economic events (e.g., TAP privatization) are sufficiently covered by generalist newspapers like *Expresso* or *Público*, which are already in the pipeline.

## 4. Technical Actions Taken
1.  **Cleaner Logic**: The specialized cleaner (`clean_eco.py`) was developed and successfully debugged to handle ECO's complex headers and footers. The code remains in the codebase for potential future use but is inactive.
2.  **Dispatcher**: The `clean_eco` function was explicitly disabled in `dispatcher.py` to prevent ingestion of future articles.
3.  **Task Tracking**: The source has been marked as "SKIPPED/REMOVED" in the project roadmap (`task.md`).

## 5. Conclusion
Removing ECO improves the **signal-to-noise ratio** of the Tourism RAG pipeline and reduces processing costs. Future efforts will focus on sources with higher domain density (e.g., *Publituris* or *Ambitur*).
