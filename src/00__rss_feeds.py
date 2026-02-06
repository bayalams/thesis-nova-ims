"""
00__rss_feeds.py - Step 0: RSS Feed Configuration
==================================================

This file contains the list of RSS feeds we want to monitor for Portuguese Tourism news.
Each feed has a "name" (used for file naming) and a "url" (the RSS feed URL).

HOW THIS WORKS:
- RSS (Really Simple Syndication) is a way websites publish their latest articles
- Each feed URL returns an XML file with a list of recent articles
- We parse this XML to extract article titles, links, and summaries

To add a new feed:
1. Find the RSS feed URL for the website you want to monitor
2. Add a new dictionary with "name" and "url" to the RSS_FEEDS list below
"""

# =============================================================================
# LIST OF RSS FEEDS TO MONITOR
# =============================================================================
# Each feed is a dictionary with:
#   - "name": A short identifier (used in output file names, no spaces!)
#   - "url": The RSS feed URL
# =============================================================================

RSS_FEEDS = [
    # =========================================================================
    # 🇵🇹 PORTUGAL - General News
    # =========================================================================
    {"name": "PUBLICO", "url": "https://feeds.feedburner.com/PublicoRSS"},
    {"name": "EXPRESSO", "url": "https://feeds.feedburner.com/expresso-geral"},
    # CORREIO_MANHA removed (Paywalled/Video-heavy)
    {"name": "DIARIO_NOTICIAS", "url": "https://www.dn.pt/feed"},
    {"name": "JORNAL_NOTICIAS", "url": "https://feeds.feedburner.com/jn-ultimas"},
    {"name": "OBSERVADOR", "url": "https://observador.pt/feed/"},

    {"name": "EL_PAIS_GENERAL", "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada"},
    {"name": "EL_MUNDO", "url": "https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml"},
    {"name": "RTP_NOTICIAS", "url": "https://www.rtp.pt/noticias/rss"},
    # {"name": "SIC_NOTICIAS", "url": "https://sicnoticias.pt/feed/"}, # BROKEN (404)
    # {"name": "TSF_RADIO", "url": "https://www.tsf.pt/rss/"}, # BROKEN (404)
    {"name": "PORTUGAL_NEWS", "url": "https://www.theportugalnews.com/rss"},
    {"name": "PORTUGAL_RESIDENT", "url": "https://www.portugalresident.com/feed/"},

    # =========================================================================
    # 🇵🇹 PORTUGAL - Economy & Business
    # =========================================================================
    {"name": "ECO_SAPO", "url": "https://eco.sapo.pt/rss"},
    {"name": "JORNAL_NEGOCIOS", "url": "https://www.jornaldenegocios.pt/rss"},
    {"name": "JORNAL_ECONOMICO", "url": "https://jornaleconomico.pt/rss"},

    # =========================================================================
    # 🇵🇹 PORTUGAL - Regional & Lifestyle
    # =========================================================================
    # {"name": "ACORIANO_ORIENTAL", "url": "https://www.acorianooriental.pt/rss"}, # BROKEN (404)
    # {"name": "TIME_OUT_LISBOA", "url": "https://www.timeout.pt/lisboa/feed"}, # BROKEN (404)
    # {"name": "TIME_OUT_PORTO", "url": "https://www.timeout.pt/porto/feed"}, # BROKEN (404)
    {"name": "SAPO_VIAGENS", "url": "https://travelmagg.sapo.pt/rss"},

    # =========================================================================
    # 🇵🇹 PORTUGAL - Tourism Trade & B2B
    # =========================================================================
    # {"name": "PUBLITURIS", "url": "https://www.publituris.pt/feed"}, # PAUSED (User Request)
    {"name": "AMBITUR", "url": "https://www.ambitur.pt/feed"},

    # =========================================================================
    # 🇪🇸 SPAIN - News & Travel
    # =========================================================================
    {"name": "EL_PAIS_GENERAL", "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada"},
    {"name": "EL_PAIS_VIAJERO", "url": "https://feeds.elpais.com/mrss-s/list/ep/site/elpais.com/section/elviajero"},
    {"name": "EL_PAIS_ECONOMIA", "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/economia/portada"}, 
    {"name": "EL_PAIS_ESPANA", "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/espana/portada"},
    {"name": "EL_PAIS_INTERNACIONAL", "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada"}, 
    {"name": "EL_MUNDO", "url": "https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml"},
    {"name": "ABC_ESPANA", "url": "https://www.abc.es/rss/2.0/viajar/"},
    {"name": "HOSTELTUR", "url": "https://www.hosteltur.com/feed"},

    # =========================================================================
    # 🇬🇧 UK - News & Travel
    # =========================================================================
    {"name": "BBC", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    {"name": "BBC_TRAVEL", "url": "https://www.bbc.com/travel/feed.rss"},
    {"name": "GUARDIAN_GENERAL", "url": "https://www.theguardian.com/uk/rss"},
    {"name": "GUARDIAN_TRAVEL", "url": "https://www.theguardian.com/uk/travel/rss"},
    # {"name": "TELEGRAPH", "url": "https://www.telegraph.co.uk/rss.xml"},
    {"name": "HUFFPOST_WORLD_NEWS", "url": "https://www.huffpost.com/news/world-news/feed"},
    {"name": "HUFFPOST_TRAVEL", "url": "https://www.huffpost.com/section/travel/feed"},

    # =========================================================================
    # 🇩🇪 GERMANY - News & Travel
    # =========================================================================
    {"name": "SPIEGEL_REISE", "url": "https://www.spiegel.de/reise/index.rss"},
    {"name": "SUEDDEUTSCHE_REISE", "url": "https://rss.sueddeutsche.de/rss/Reise"},
    {"name": "DIE_ZEIT", "url": "https://newsfeed.zeit.de/index"},
    {"name": "FAZ", "url": "https://www.faz.net/rss/aktuell/"},
    {"name": "TOURISTIK_AKTUELL", "url": "https://www.touristik-aktuell.de/rss/news.xml"},

    # =========================================================================
    # 🇫🇷 FRANCE - News & Travel
    # =========================================================================
    {"name": "LE_MONDE", "url": "https://www.lemonde.fr/rss/une.xml"},
    {"name": "LE_FIGARO_GENERAL", "url": "https://www.lefigaro.fr/rss/figaro_actualites.xml"},
    {"name": "LE_FIGARO_VOYAGES", "url": "https://www.lefigaro.fr/rss/figaro_voyages.xml"},
    {"name": "TOURMAG", "url": "https://www.tourmag.com/xml/syndication.rss"},
    {"name": "LECHO_TOURISTIQUE", "url": "https://www.lechotouristique.com/feed"},

    # =========================================================================
    # 🇮🇹 ITALY - Travel
    # =========================================================================
    {"name": "ANSA_VIAGGI", "url": "https://www.ansa.it/canale_viaggi/notizie/viaggiart_rss.xml"},

    # =========================================================================
    # 🇺🇸 USA - News & Travel
    # =========================================================================
    # NOTE: NYT_TRAVEL, NYT_WORLD, and WSJ removed due to paywall issues (0-48% success rate)
    {"name": "CNN_TRAVEL", "url": "http://rss.cnn.com/rss/edition_travel.rss"},
    {"name": "CNBC", "url": "https://www.cnbc.com/id/10000664/device/rss/rss.html"},
    {"name": "CNBC_TRAVEL", "url": "https://www.cnbc.com/id/10000739/device/rss/rss.html"},
    {"name": "WASHINGTON_POST", "url": "https://feeds.washingtonpost.com/rss/world"},


    # =========================================================================
    # 🌍 INTERNATIONAL - Travel Publications
    # =========================================================================
    {"name": "CONDE_NAST_TRAVELER", "url": "https://www.cntraveler.com/feed/rss"},
    {"name": "TRAVEL_LEISURE", "url": "https://feeds-api.dotdashmeredith.com/v1/rss/google/bee1a82b-9ca0-42a2-b07a-12eed31f7ec3"},
    # {"name": "LONELY_PLANET", "url": "https://www.lonelyplanet.com/feed.xml"}, # BROKEN (404)
    {"name": "SKIFT", "url": "https://skift.com/feed/"},

    # =========================================================================
    # 🌍 INTERNATIONAL - General News
    # =========================================================================
    {"name": "AL_JAZEERA", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    # {"name": "AP_NEWS", "url": "https://feedx.net/rss/ap.xml"},  # DISABLED: 3rd-party proxy, scraping blocked, no usable content
    {"name": "EURONEWS_NEWS", "url": "https://pt.euronews.com/rss?format=mrss&level=theme&name=news"},
    {"name": "EURONEWS_TRAVEL", "url": "https://pt.euronews.com/rss?format=mrss&level=vertical&name=travel"},
    # {"name": "REUTERS", "url": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best"},  # DISABLED: No official RSS since 2020
    {"name": "FRANCE24", "url": "https://www.france24.com/en/rss"},
    {"name": "DW_NEWS", "url": "https://rss.dw.com/rdf/rss-en-all"},

    # =========================================================================
    # ✈️ AVIATION & TRANSPORT
    # =========================================================================
    # {"name": "ANA_AEROPORTOS", "url": "https://www.ana.pt/pt/feed"}, # BROKEN (404)
    {"name": "SIMPLE_FLYING", "url": "https://simpleflying.com/feed/"},
    # {"name": "IATA", "url": "https://www.iata.org/en/pressroom/news/rss/"}, # BROKEN (404)
    # {"name": "ICAO", "url": "https://www.icao.int/Newsroom/Pages/NewsRSS.aspx"}, # BROKEN (404)

    # =========================================================================
    # 🏛️ INSTITUTIONAL & POLICY
    # =========================================================================
    # {"name": "UNWTO", "url": "https://www.unwto.org/news/format/rss"}, # BROKEN (404)

    # =========================================================================
    # 📰 TRAVEL INDUSTRY NEWS (NEW 2026-01-21) - NO CLEANERS YET
    # =========================================================================
    {"name": "BREAKING_TRAVEL_NEWS", "url": "https://feeds.feedburner.com/breakingtravelnews"},
    {"name": "ETURBONEWS", "url": "https://www.eturbonews.com/feed/"},
    {"name": "TRAVELPULSE", "url": "https://www.travelpulse.com/rss"},
    {"name": "AIR_CURRENT", "url": "https://theaircurrent.com/feed/"},


    # =========================================================================
    # 🇵🇹 PORTUGAL - Regional (Algarve) - NO CLEANER YET
    # =========================================================================
    # {"name": "SUL_INFORMACAO", "url": "https://www.sulinformacao.pt/feed/"},

    # =========================================================================
    # 🇩🇪 GERMANY - Travel Trade - NO CLEANER YET
    # =========================================================================
    {"name": "FVW", "url": "https://www.fvw.de/feed"},

    # =========================================================================
    # 🇬🇧 UK - Additional Travel - NO CLEANER YET
    # =========================================================================
    {"name": "INDEPENDENT_TRAVEL", "url": "https://www.independent.co.uk/travel/rss"},

    # =========================================================================
    # 🇳🇴🇸🇪 SCANDINAVIA (Key Origin Markets) - NO CLEANERS YET
    # =========================================================================
    # {"name": "AFTENPOSTEN_REISE", "url": "https://www.aftenposten.no/rss/reise"},
    # {"name": "VAGABOND_SE", "url": "https://www.vagabond.se/feed/"},
]

# =============================================================================
# HELPER FUNCTION TO CHECK IF FEEDS ARE WORKING
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("RSS FEEDS CONFIGURED")
    print("=" * 60)
    print()
    
    for i, feed in enumerate(RSS_FEEDS, start=1):
        print(f"{i:2}. {feed['name']}")
        print(f"    URL: {feed['url']}")
        print()
    
    print("=" * 60)
    print(f"Total feeds configured: {len(RSS_FEEDS)}")
    print("=" * 60)
