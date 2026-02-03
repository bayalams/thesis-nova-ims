# Prompt Examples for Tourism Report Generation

These prompts are designed for the RAG web app to generate tourism news reports for stakeholders in Portugal.

---

## Simple Version

```
Summarize the key tourism news from Portugal in the last 7 days. Include developments in hotel industry, airline routes, visitor statistics, and government policies affecting tourism.
```

---

## Detailed Executive Report Version

```
Generate an executive briefing on Portuguese tourism news from the past week. 

Structure the report as follows:

1. **Key Headlines** - The 3-5 most important developments a tourism stakeholder should know

2. **Market Trends** - Visitor numbers, booking patterns, seasonal trends, source markets

3. **Infrastructure & Transport** - New airline routes, airport updates, hotel openings, transport developments

4. **Policy & Regulation** - Government announcements, visa changes (ETIAS/EES), tax policies, environmental regulations

5. **Regional Focus** - Notable developments in the Algarve, Lisbon, Porto, Madeira, and Azores

6. **Competitive Landscape** - How Portugal compares to competing destinations (Spain, Greece, etc.)

7. **Outlook** - Upcoming events, forecasts, and risks to watch

For each item, cite the source and date. Prioritize information most relevant to hotel operators, tour companies, and destination marketers.
```

---

## Short Weekly Digest Version

```
Create a bullet-point summary of this week's Portuguese tourism news. Focus on: 
- Visitor arrivals and trends
- New flights and hotel developments  
- Government policies affecting tourism
- Any challenges or risks (strikes, weather, economic)

Keep it concise - one paragraph per topic with sources cited.
```

---

## Tips for Better Results

- **Be specific**: More focused prompts get better retrieval results
- **Break down broad topics**: Instead of one large report, try multiple focused queries
- **Include time frames**: Specify "last 7 days" or date ranges when relevant
- **Name the audience**: "For a hotel operator" or "for a destination marketer" helps tailor the response
