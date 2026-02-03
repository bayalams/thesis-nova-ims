"""
03__wiki_fetcher.py - Step 3: Wikipedia Article Fetcher
========================================================

This script fetches Wikipedia articles related to Portuguese tourism and economy.

WHAT IT DOES:
1. Uses a curated seed list of important tourism/economy articles
2. Optionally crawls Wikipedia categories to find more articles
3. Fetches full article content using the free Wikipedia API
4. Saves articles to data/wiki/

HOW TO RUN:
    # Fetch seed articles only
    python 03__wiki_fetcher.py

    # Also crawl categories for more articles
    python 03__wiki_fetcher.py --crawl-categories

    # Limit articles per category
    python 03__wiki_fetcher.py --crawl-categories --per-category 10

OUTPUT:
    data/wiki/<article_title>.json

WHY WIKIPEDIA API?
    - It's FREE! No API key needed
    - Returns clean, structured content
    - No scraping or rate limit worries
    - Official and reliable
"""

# =============================================================================
# IMPORTS
# =============================================================================

import argparse    # Built-in library to parse command line arguments
import hashlib     # Built-in library for creating hashes
import json        # Built-in library to work with JSON data
import os          # Built-in library to work with files and folders
import re          # Built-in library for regular expressions
import time        # Built-in library to add delays between requests
import requests    # Library to make HTTP requests (pip install requests)
from datetime import datetime  # Built-in library to work with dates and times

# =============================================================================
# CONFIGURATION
# =============================================================================

# Directory where we'll save the Wikipedia articles
OUTPUT_DIR = "data/wiki"

# Wikipedia API endpoint (no authentication needed!)
WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"

# User-Agent header (REQUIRED by Wikipedia API)
# Wikipedia blocks requests without a proper User-Agent
# See: https://meta.wikimedia.org/wiki/User-Agent_policy
USER_AGENT = "PortugueseTourismRAG/1.0 (Educational project; contact@example.com)"

# Delay between requests (in seconds) to be nice to Wikipedia
DELAY_BETWEEN_REQUESTS = 0.5

# =============================================================================
# SEED ARTICLES - CURATED LIST OF IMPORTANT ARTICLES
# =============================================================================
# These are the core articles we want to fetch.
# Organized by theme: Portugal (deep), Europe (broad), Trends (context)

SEED_ARTICLES = [
    # =========================================================================
    # 🇵🇹 PORTUGAL - TOURISM DESTINATIONS (Deep local knowledge)
    # =========================================================================
    "Tourism in Portugal",
    "Lisbon",
    "Porto",
    "Algarve",
    "Madeira",
    "Azores",
    "Sintra",
    "Évora",
    "Coimbra",
    "Faro, Portugal",
    "Cascais",
    "Funchal",
    "Fátima, Portugal",
    "Óbidos, Portugal",
    "Guimarães",
    "Braga",
    "Aveiro, Portugal",
    "Lagos, Portugal",
    "Albufeira",
    "Nazaré, Portugal",
    
    # =========================================================================
    # 🇵🇹 PORTUGAL - REGIONS AND HERITAGE
    # =========================================================================
    "Douro Valley",
    "Alentejo",
    "Costa Vicentina",
    "Ria Formosa",
    "Belém Tower",
    "Jerónimos Monastery",
    "Pena Palace",
    "Castelo de São Jorge",
    "University of Coimbra",
    "Historic Centre of Porto",
    
    # =========================================================================
    # 🇵🇹 PORTUGAL - ECONOMY AND CULTURE
    # =========================================================================
    "Economy of Portugal",
    "Portugal",
    "Port wine",
    "Portuguese wine",
    "Portuguese cuisine",
    "TAP Air Portugal",
    "Lisbon Airport",
    "Porto Airport",
    "Fado",
    "Portuguese language",
    "History of Portugal",
    
    # =========================================================================
    # 🌍 EUROPEAN TOURISM & DESTINATIONS
    # =========================================================================
    "Tourism in Europe",
    "Sustainable tourism",
    "Cultural tourism",
    "Urban tourism",
    "Rural tourism",
    "Ecotourism",
    "Adventure tourism",
    "Mass tourism",
    "Overtourism",
    
    # =========================================================================
    # 💶 ECONOMY, TRAVEL & INFRASTRUCTURE
    # =========================================================================
    "Travel and tourism industry",
    "Air transport in Europe",
    "Rail transport in Europe",
    "Low-cost carrier",
    "Tourism economics",
    "Hospitality industry",
    "Hotel",
    "Airline",
    "European Union",
    
    # =========================================================================
    # 🌱 SOCIAL, CULTURAL & ENVIRONMENTAL SHIFTS
    # =========================================================================
    "Sustainable development",
    "Effects of climate change on tourism",
    "Digital nomad",
    "Impact of the COVID-19 pandemic on tourism",
    "Responsible travel",
    "Cultural heritage",
    "Creative tourism",
    "Wellness tourism",
    "Medical tourism",
    "Slow travel",
    
    # =========================================================================
    # 🏛️ UNESCO & HERITAGE
    # =========================================================================
    "World Heritage Site",
    "UNESCO",
    "World Heritage Sites in Portugal",
]

# =============================================================================
# WIKIPEDIA CATEGORIES TO CRAWL (OPTIONAL)
# =============================================================================
# When --crawl-categories is used, we'll get articles from these categories

CATEGORIES_TO_CRAWL = [
    # Portugal-specific
    "Category:Tourism in Portugal",
    "Category:World Heritage Sites in Portugal",
    "Category:Economy of Portugal",
    "Category:Portuguese cuisine",
    
    # European tourism
    "Category:Tourism in Europe",
    "Category:Sustainable tourism",
    "Category:World Heritage Sites in Europe",
    "Category:Transport in Europe",
    
    # Industry & trends
    "Category:Hospitality industry",
    "Category:Tourist attractions in Europe",
    "Category:Low-cost airlines",
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def clean_filename(title):
    """
    Convert a Wikipedia article title to a safe filename.
    
    Example: "Tourism in Portugal" -> "Tourism_in_Portugal"
    
    PARAMETERS:
    - title: The article title
    
    RETURNS:
    - A safe filename string
    """
    # Replace spaces with underscores
    filename = title.replace(" ", "_")
    # Remove characters that are not safe for filenames
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    return filename


def create_article_id(title):
    """
    Create a unique ID for an article based on its title.
    
    PARAMETERS:
    - title: The article title
    
    RETURNS:
    - A 64-character hexadecimal string
    """
    return hashlib.sha256(title.encode("utf-8")).hexdigest()


def fetch_article_content(title):
    """
    Fetch the full content of a Wikipedia article.
    
    Uses the Wikipedia API to get:
    - Full article text (in plain text format)
    - Article URL
    - Categories
    - Last revision info
    
    PARAMETERS:
    - title: The Wikipedia article title
    
    RETURNS:
    - A dictionary with article data, or None if not found
    """
    print(f"[INFO]   Fetching: {title}")
    
    # Build the API request parameters
    # See: https://www.mediawiki.org/wiki/API:Main_page
    params = {
        "action": "query",
        "titles": title,
        "prop": "extracts|info|categories",
        "explaintext": "true",      # Get plain text (not HTML)
        "exsectionformat": "plain", # Plain text sections
        "inprop": "url",            # Include article URL
        "cllimit": "50",            # Get up to 50 categories
        "format": "json",
    }
    
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(WIKIPEDIA_API_URL, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # The API returns pages in a nested structure
        pages = data.get("query", {}).get("pages", {})
        
        # Get the first (and only) page
        for page_id, page_data in pages.items():
            # Check if page exists (-1 means not found)
            if page_id == "-1":
                print(f"[WARNING]   Article not found: {title}")
                return None
            
            # Extract the data we need
            article = {
                "title": page_data.get("title"),
                "page_id": page_id,
                "url": page_data.get("fullurl"),
                "content": page_data.get("extract", ""),
                "categories": [
                    cat.get("title", "").replace("Category:", "")
                    for cat in page_data.get("categories", [])
                ],
                "last_revision": page_data.get("touched"),
            }
            
            content_length = len(article["content"])
            print(f"[INFO]   Success! Got {content_length} characters")
            
            return article
        
        return None
        
    except requests.RequestException as e:
        print(f"[ERROR]   Failed to fetch '{title}': {e}")
        return None


def fetch_category_members(category_name, limit=50):
    """
    Fetch all articles in a Wikipedia category.
    
    PARAMETERS:
    - category_name: The category (e.g., "Category:Tourism in Portugal")
    - limit: Maximum number of articles to return
    
    RETURNS:
    - A list of article titles
    """
    print(f"[INFO] Fetching category: {category_name}")
    
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category_name,
        "cmtype": "page",  # Only get pages, not subcategories
        "cmlimit": str(limit),
        "format": "json",
    }
    
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(WIKIPEDIA_API_URL, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        members = data.get("query", {}).get("categorymembers", [])
        titles = [member.get("title") for member in members]
        
        print(f"[INFO]   Found {len(titles)} articles in category")
        
        return titles
        
    except requests.RequestException as e:
        print(f"[ERROR]   Failed to fetch category '{category_name}': {e}")
        return []


def save_article(article, output_dir):
    """
    Save a Wikipedia article to a JSON file.
    
    PARAMETERS:
    - article: Dictionary containing the article data
    - output_dir: Directory to save the file
    
    RETURNS:
    - The path to the saved file
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the filename from the article title
    title = article["title"]
    filename = clean_filename(title) + ".json"
    filepath = os.path.join(output_dir, filename)
    
    # Add metadata
    article_with_metadata = {
        "id": create_article_id(title),
        "source": "wikipedia",
        "fetched_at": datetime.now().isoformat(),
        **article,
    }
    
    # Save to JSON file
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(article_with_metadata, f, ensure_ascii=False, indent=2)
    
    return filepath


def article_already_fetched(title, output_dir):
    """
    Check if an article has already been fetched.
    
    PARAMETERS:
    - title: The article title
    - output_dir: Directory where articles are saved
    
    RETURNS:
    - True if the article already exists, False otherwise
    """
    filename = clean_filename(title) + ".json"
    filepath = os.path.join(output_dir, filename)
    return os.path.exists(filepath)


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """
    Main function that runs the Wikipedia fetcher.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fetch Wikipedia articles about Portuguese tourism")
    parser.add_argument(
        "--crawl-categories",
        action="store_true",
        help="Also crawl Wikipedia categories to find more articles"
    )
    parser.add_argument(
        "--per-category",
        type=int,
        default=20,
        help="Maximum articles to fetch per category (default: 20)"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip articles that have already been fetched (default: True)"
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        default=False,
        help="Re-fetch articles even if they already exist"
    )
    args = parser.parse_args()
    
    # Handle skip-existing flags
    skip_existing = not args.no_skip_existing
    
    print("=" * 60)
    print("WIKIPEDIA FETCHER - Starting")
    print("=" * 60)
    print()
    print(f"[INFO] Output directory: {OUTPUT_DIR}")
    print(f"[INFO] Skip existing: {skip_existing}")
    print(f"[INFO] Crawl categories: {args.crawl_categories}")
    print()
    
    # Step 1: Build the list of articles to fetch
    articles_to_fetch = set()
    
    # Add seed articles
    print(f"[INFO] Loading {len(SEED_ARTICLES)} seed articles...")
    for title in SEED_ARTICLES:
        articles_to_fetch.add(title)
    
    # Crawl categories if requested
    if args.crawl_categories:
        print()
        print(f"[INFO] Crawling {len(CATEGORIES_TO_CRAWL)} categories...")
        print()
        
        for category in CATEGORIES_TO_CRAWL:
            members = fetch_category_members(category, limit=args.per_category)
            for title in members:
                articles_to_fetch.add(title)
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    print()
    print(f"[INFO] Total unique articles to process: {len(articles_to_fetch)}")
    print()
    
    # Step 2: Filter out already fetched articles
    if skip_existing:
        filtered = []
        for title in articles_to_fetch:
            if article_already_fetched(title, OUTPUT_DIR):
                print(f"[SKIP] Already fetched: {title}")
            else:
                filtered.append(title)
        articles_to_fetch = filtered
    else:
        articles_to_fetch = list(articles_to_fetch)
    
    print()
    print(f"[INFO] Articles to fetch: {len(articles_to_fetch)}")
    
    if len(articles_to_fetch) == 0:
        print("[INFO] No new articles to fetch!")
        return
    
    print()
    print("-" * 60)
    print()
    
    # Step 3: Fetch each article
    fetched_count = 0
    error_count = 0
    
    for i, title in enumerate(articles_to_fetch, start=1):
        print(f"[{i}/{len(articles_to_fetch)}] Processing...")
        
        # Fetch the article
        article = fetch_article_content(title)
        
        if article:
            # Save the article
            filepath = save_article(article, OUTPUT_DIR)
            print(f"[INFO]   Saved to: {filepath}")
            fetched_count += 1
        else:
            error_count += 1
        
        # Wait before the next request
        if i < len(articles_to_fetch):
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        print()
    
    # Step 4: Print summary
    print("-" * 60)
    print()
    print("=" * 60)
    print("WIKIPEDIA FETCHER - Finished")
    print("=" * 60)
    print()
    print(f"Total articles processed: {fetched_count + error_count}")
    print(f"  Fetched: {fetched_count}")
    print(f"  Not found: {error_count}")
    print()
    print("Output directory:", OUTPUT_DIR)
    print()


# =============================================================================
# RUN THE SCRIPT
# =============================================================================

if __name__ == "__main__":
    main()
