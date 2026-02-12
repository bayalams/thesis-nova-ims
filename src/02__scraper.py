"""
02__scraper.py - Step 2: Article Scraper
=========================================

This script reads the JSONL files from Step 1 and scrapes the full article content.

WHAT IT DOES:
1. Reads the JSONL files from data/links/
2. For each article link, calls ScrapingBee API to get the content
3. Saves each article as a JSON file

HOW TO RUN:
    # First, set your ScrapingBee API key
    export SCRAPINGBEE_API_KEY="your_api_key_here"
    
    # Then run the scraper
    python 02__scraper.py

    # Limit TOTAL articles to scrape
    python 02__scraper.py --limit 10

    # Limit articles PER SOURCE (great for calibration!)
    python 02__scraper.py --per-source 2

    # Re-scrape articles even if they already exist
    python 02__scraper.py --per-source 2 --no-skip-existing

OUTPUT:
    data/articles/<fingerprint>.json
"""

# =============================================================================
# IMPORTS
# =============================================================================

import argparse    # Built-in library to parse command line arguments
import hashlib     # Built-in library for creating hashes
import json        # Built-in library to work with JSON data
import os          # Built-in library to work with files and folders
import time        # Built-in library to add delays between requests
import requests    # Library to make HTTP requests (pip install requests)
from datetime import datetime  # Built-in library to work with dates and times
from pathlib import Path       # Built-in library for file path handling

# =============================================================================
# CONFIGURATION
# =============================================================================

# Directory containing the JSONL files from Step 1
INPUT_DIR = "data/links"

# Directory where we'll save the scraped articles
OUTPUT_DIR = "data/articles"

# ScrapingBee API endpoint
SCRAPINGBEE_URL = "https://app.scrapingbee.com/api/v1"

# Delay between requests (in seconds) to avoid hitting rate limits
DELAY_BETWEEN_REQUESTS = 1.0

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_api_key():
    """
    Get the ScrapingBee API key from environment variable.
    
    WHY WE USE ENVIRONMENT VARIABLES:
    - API keys are secret and should not be in the code
    - Environment variables keep secrets out of version control
    
    RETURNS:
    - The API key string
    
    RAISES:
    - SystemExit if the API key is not set
    """
    api_key = os.environ.get("SCRAPINGBEE_API_KEY")
    
    if not api_key:
        print("[ERROR] ScrapingBee API key not found!")
        print()
        print("Please set the SCRAPINGBEE_API_KEY environment variable:")
        print()
        print("  On Mac/Linux:")
        print("    export SCRAPINGBEE_API_KEY='your_api_key_here'")
        print()
        print("  On Windows:")
        print("    set SCRAPINGBEE_API_KEY=your_api_key_here")
        print()
        raise SystemExit(1)
    
    return api_key


def find_latest_jsonl_files(input_dir):
    """
    Find all JSONL files in the input directory (including subfolders).
    
    The indexer saves files in source-specific subfolders:
    - data/links/PUBLICO/20260101_152601.jsonl
    - data/links/EXPRESSO/20260101_152602.jsonl
    
    PARAMETERS:
    - input_dir: Base directory to search for JSONL files
    
    RETURNS:
    - A list of file paths
    """
    print(f"[INFO] Looking for JSONL files in: {input_dir}")
    
    # Check if the directory exists
    if not os.path.exists(input_dir):
        print(f"[WARNING] Directory does not exist: {input_dir}")
        return []
    
    # Find all .jsonl files recursively (using **/ to search subfolders)
    jsonl_files = list(Path(input_dir).glob("**/*.jsonl"))
    
    print(f"[INFO] Found {len(jsonl_files)} JSONL files")
    
    return jsonl_files


def load_articles_from_jsonl(jsonl_path):
    """
    Load articles from a JSONL file.
    
    PARAMETERS:
    - jsonl_path: Path to the JSONL file
    
    RETURNS:
    - A list of article dictionaries
    """
    print(f"[INFO] Loading articles from: {jsonl_path}")
    
    articles = []
    
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:  # Skip empty lines
                article = json.loads(line)
                articles.append(article)
    
    print(f"[INFO]   Loaded {len(articles)} articles")
    
    return articles


def create_article_id(link):
    """
    Create a unique ID for an article based on its link.
    
    We use SHA-256 hash of the link to create a unique filename.
    
    PARAMETERS:
    - link: The article URL
    
    RETURNS:
    - A 64-character hexadecimal string
    """
    return hashlib.sha256(link.encode("utf-8")).hexdigest()


def scrape_article(api_key, url):
    """
    Scrape an article using ScrapingBee API.
    
    WHAT IS SCRAPINGBEE?
    - ScrapingBee is a web scraping API service
    - It handles proxies, captchas, and JavaScript rendering
    - Returns the page content as markdown
    
    PARAMETERS:
    - api_key: Your ScrapingBee API key
    - url: The URL to scrape
    
    RETURNS:
    - A dictionary with the scraping result
    """
    print(f"[INFO]   Scraping: {url[:80]}...")
    
    # Build the request parameters
    params = {
        "api_key": api_key,
        "url": url,
        "render_js": "true",  # Render JavaScript (required for some sites, slower)
        "return_page_markdown": "true",  # Return content as markdown
    }
    
    try:
        # Make the request to ScrapingBee
        response = requests.get(SCRAPINGBEE_URL, params=params, timeout=30)
        
        # Build the result dictionary
        result = {
            "success": response.ok,
            "status_code": response.status_code,
            "content": response.text,
            "headers": dict(response.headers),
        }
        
        if response.ok:
            print(f"[INFO]   Success! Got {len(response.text)} characters")
        else:
            print(f"[WARNING]   Failed with status code: {response.status_code}")
        
        return result
        
    except requests.RequestException as e:
        print(f"[ERROR]   Request failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def save_article(article_data, output_dir):
    """
    Save the scraped article to a JSON file.
    
    PARAMETERS:
    - article_data: Dictionary containing the article data
    - output_dir: Directory to save the file
    
    RETURNS:
    - The path to the saved file
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the filename using the article ID
    article_id = article_data["id"]
    filename = f"{article_id}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Save to JSON file
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(article_data, f, ensure_ascii=False, indent=2)
    
    return filepath


def article_already_scraped(article_id, output_dir):
    """
    Check if an article has already been scraped.
    
    This helps us avoid re-scraping the same articles.
    
    PARAMETERS:
    - article_id: The article's unique ID
    - output_dir: Directory where scraped articles are saved
    
    RETURNS:
    - True if the article already exists, False otherwise
    """
    filepath = os.path.join(output_dir, f"{article_id}.json")
    return os.path.exists(filepath)


def should_scrape(article):
    """
    Check if an article should be scraped based on its metadata.
    
    This implements filtering BEFORE making the API call, saving resources.
    User Request:
    - Exclude 'Opinião', 'Blitz', 'Economia', 'Sport', 'Culture', 'Obituário', 'Religião'
    - Include specific 'Allowed Tags' + 'Mapped Tags' for Expresso.
    - Exclude videos/podcasts.
    
    PARAMETERS:
    - article: Dictionary containing article metadata (link, tags, source)
    
    RETURNS:
    - True if it should be scraped, False otherwise.
    """
    source = article.get("source", "").upper()
    link = article.get("link", "")
    tags = [t.strip() for t in (article.get("tags") or [])]
    
    # 1. GLOBAL VIDEO/PODCAST EXCLUSION
    # ---------------------------------
    # Check for video/podcast keywords in tags (case-insensitive)
    if tags and any(x in t.lower() for t in tags for x in ['vídeo', 'videos', 'podcast', 'multimédia', 'galeria']):
        return False
        
    # Check for video URL patterns
    video_patterns = ['/video/', '/videos/', '/cmtv/', 'www.nytimes.com/video', '/podcasts/', 'multimedia']
    if any(pat in link for pat in video_patterns):
        return False
    
    
    # 2. EXPRESSO SPECIFIC FILTERING
    # ---------------------------------
    if 'EXPRESSO' in source:
        # A. Strict Allowlist & Meaningful Mapping (Mirrors clean_expresso.py logic)
        
        target_categories = {
            "Política",
            "Sociedade", 
            "Internacional",
            "Boa Cama Boa Mesa"
        }

        # Tag Mapping (Specific -> Target)
        tag_map = {
            # Politics
            "Presidenciais 2026": "Política",
            "Governo": "Política",
            "Parlamento": "Política",
            "Partidos": "Política",
            "Justiça": "Política",
            
            # International
            "Venezuela": "Internacional",
            "Guerra na Ucrânia": "Internacional",
            "Médio Oriente": "Internacional",
            "América Latina": "Internacional",
            "União Europeia": "Internacional",
            "EUA": "Internacional",
            "Brasil": "Internacional",
            "Espanha": "Internacional",
            "França": "Internacional",
            "Reino Unido": "Internacional",
            "Mundo": "Internacional",
            "Europa": "Internacional",
            "Guerra Fria": "Internacional",
            
            # Society
            "Saúde": "Sociedade",
            "Transportes": "Sociedade",
            "Meteorologia": "Sociedade",
            "Segurança": "Sociedade",
            "Imobiliário": "Sociedade",
            "Habitação": "Sociedade",
            "Lisboa": "Sociedade",
            # Explicitly Excluded: "Obituário", "Religião" (will fail default check)
        }
        
        is_allowed = False
        effective_tags = set()
        
        for t in tags:
            t_clean = t.strip()
            effective_tags.add(t) # Add original
            if t_clean in tag_map:
                effective_tags.add(tag_map[t_clean]) # Add mapped
                
        # Check intersection with Target Categories
        # (Using case-insensitive check for robustness)
        for et in effective_tags:
            if any(tc.lower() == et.lower() for tc in target_categories):
                is_allowed = True
                break
        
        if not is_allowed:
            # print(f"[SKIP] Expresso (Not Allowed): {tags} -> {link}")
            return False
    
    # 3. OBSERVADOR SPECIFIC FILTERING
    # ---------------------------------
    if 'OBSERVADOR' in source:
        # Filter out podcasts, radio shows, lab content, and newsletters
        exclude_tags = ['Rádio Observador', 'Observador Lab', 'Newsletter']
        if any(et in t for t in tags for et in exclude_tags):
            return False

    # 4. SAPO_VIAGENS SPECIFIC FILTERING
    # ----------------------------------
    if source == 'SAPO_VIAGENS':
        # User Request: "exclusively keep the travel section"
        # We allow both 'viagens.sapo.pt' (main portal) and 'travelmagg.sapo.pt' (new focused feed)
        if 'viagens.sapo.pt' not in link and 'travelmagg.sapo.pt' not in link:
            return False

    # 5. ECO_SAPO SPECIFIC FILTERING (Tourism Business Only)
    # -----------------------------------------------------
    if source == 'ECO_SAPO':
        # We only want business news related to Tourism, Aviation, and Hospitality.
        # We check the Link URL (which usually contains the slug)
        keywords = [
            'turismo', 'hotel', 'aviacao', 'aeroporto', 'tap', 'ryanair', 'easyjet',
            'alojamento', 'viajar', 'hospedagem', 'companhia-aerea', 'voos',
            'greve', 'sata', 'ana-aeroportos', 'nave',
        ]
        # Normalize link for checking
        link_lower = link.lower()
        
        if not any(k in link_lower for k in keywords):
            # If link doesn't match, check tags if available
            if not tags or not any(k in t.lower() for t in tags for k in keywords):
                return False

    # 6. TELEGRAPH SPECIFIC FILTERING (DEPRECATED)
    # -----------------------------------------------------------
    if source == 'TELEGRAPH':
        # Decision 2026-01-20: Source dropped due to low relevance and high noise.
        # See project_documentation/telegraph_deprecation_report.md
        return False

    return True

def main():
    """
    Main function that runs the scraper.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Scrape articles using ScrapingBee")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum TOTAL number of articles to scrape"
    )
    parser.add_argument(
        "--per-source",
        type=int,
        default=None,
        help="Maximum number of articles to scrape PER SOURCE (useful for calibration)"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip articles that have already been scraped (default: True)"
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        default=False,
        help="Re-scrape articles even if they already exist"
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Only scrape articles from this source (e.g. AL_JAZEERA)"
    )
    args = parser.parse_args()
    
    # Handle skip-existing flags
    skip_existing = not args.no_skip_existing
    
    print("=" * 60)
    print("ARTICLE SCRAPER - Starting")
    print("=" * 60)
    print()
    
    # Show what options are active
    if args.per_source:
        print(f"[INFO] Mode: Scrape up to {args.per_source} articles PER SOURCE")
    elif args.limit:
        print(f"[INFO] Mode: Scrape up to {args.limit} articles TOTAL")
    else:
        print("[INFO] Mode: Scrape ALL articles")
    print()
    
    # Step 1: Get the API key
    api_key = get_api_key()
    print("[INFO] ScrapingBee API key loaded")
    print()
    
    # Step 2: Find all JSONL files
    jsonl_files = find_latest_jsonl_files(INPUT_DIR)
    
    if not jsonl_files:
        print("[ERROR] No JSONL files found. Run 01__indexer.py first!")
        return
    
    print()
    
    # Step 3: Load articles and organize by source
    # We'll use a dictionary: { "PUBLICO": [article1, article2, ...], ... }
    articles_by_source = {}
    
    for jsonl_path in jsonl_files:
        articles = load_articles_from_jsonl(jsonl_path)
        for article in articles:
            source = article.get("source", "UNKNOWN")
            if source not in articles_by_source:
                articles_by_source[source] = []
            articles_by_source[source].append(article)
    
    print()
    print(f"[INFO] Found {len(articles_by_source)} sources:")
    for source, articles in articles_by_source.items():
        print(f"[INFO]   - {source}: {len(articles)} articles")
    print()
    
    # Filter to specific source if --source is given
    if args.source:
        source_upper = args.source.upper()
        if source_upper not in articles_by_source:
            print(f"[ERROR] Source '{args.source}' not found. Available: {', '.join(sorted(articles_by_source.keys()))}")
            return
        articles_by_source = {source_upper: articles_by_source[source_upper]}
        print(f"[INFO] Filtered to source: {source_upper} ({len(articles_by_source[source_upper])} articles)")
        print()
    
    # Step 4: Build list of articles to scrape, respecting per-source limit
    articles_to_scrape = []
    
    for source, articles in articles_by_source.items():
        source_count = 0
        
        for article in articles:
            link = article.get("link")
            if not link:
                continue

            # SKIP CHECK (User Request: Exclusions before scraping)
            if not should_scrape(article):
                # print(f"[INFO] Skipping excluded article: {link}")
                continue
            
            article_id = create_article_id(link)
            
            # Skip if already scraped (unless --no-skip-existing)
            if skip_existing and article_already_scraped(article_id, OUTPUT_DIR):
                continue
            
            # Check per-source limit
            if args.per_source and source_count >= args.per_source:
                break
            
            articles_to_scrape.append((article, article_id, source))
            source_count += 1
        
        if args.per_source:
            print(f"[INFO] {source}: selected {source_count} articles (limit: {args.per_source})")
    
    print()
    print(f"[INFO] Total articles to scrape: {len(articles_to_scrape)}")
    
    # Apply global limit if specified
    if args.limit and len(articles_to_scrape) > args.limit:
        articles_to_scrape = articles_to_scrape[:args.limit]
        print(f"[INFO] Limited to: {len(articles_to_scrape)} articles (global limit)")
    
    if len(articles_to_scrape) == 0:
        print("[INFO] No new articles to scrape!")
        return
    
    print()
    print("-" * 60)
    print()
    
    # Step 5: Scrape articles in parallel
    print(f"[INFO] Starting parallel scraping with 5 workers...")
    print(f"[INFO] JavaScript rendering: ENABLED (slower)")
    print()

    scraped_count = 0
    error_count = 0
    results_by_source = {}  # Track success/failure by source
    
    # We use ThreadPoolExecutor to run multiple requests at the same time
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Cleaning logic removed - moved to 03__cleaner.py 

    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all tasks to the executor
        future_to_article = {
            executor.submit(scrape_article, api_key, article["link"]): (article, article_id, source)
            for article, article_id, source in articles_to_scrape
        }
        
        # Process results as they complete
        for i, future in enumerate(as_completed(future_to_article), start=1):
            article, article_id, source = future_to_article[future]
            
            try:
                scrape_result = future.result()
                
                # Build the full article data
                article_data = {
                    "id": article_id,
                    "link": article["link"],
                    "source": source,
                    "metadata": article,
                    "scraped_at": datetime.now().isoformat(),
                    "scrapingbee": scrape_result,
                    # We NO LONGER clean here. 
                    # "text" field is omitted or can be raw content if needed for downstream compatibility mostly
                    # But the new cleaner will generate the "text" field.
                    # For now, let's just save the raw structure.
                }
                
                # Track results by source
                if source not in results_by_source:
                    results_by_source[source] = {"success": 0, "error": 0}
                
                # Save the article
                if scrape_result.get("success"):
                    filepath = save_article(article_data, OUTPUT_DIR)
                    print(f"[{i}/{len(articles_to_scrape)}] [SUCCESS] {source}: {article['link'][:60]}...")
                    scraped_count += 1
                    results_by_source[source]["success"] += 1
                else:
                    filepath = save_article(article_data, OUTPUT_DIR)
                    print(f"[{i}/{len(articles_to_scrape)}] [ERROR] {source}: {article['link'][:60]}...")
                    error_count += 1
                    results_by_source[source]["error"] += 1

            except Exception as exc:
                print(f"[{i}/{len(articles_to_scrape)}] [EXCEPTION] {source}: {exc}")
                error_count += 1

    
    # Step 6: Print summary
    print("-" * 60)
    print()
    print("=" * 60)
    print("ARTICLE SCRAPER - Finished")
    print("=" * 60)
    print()
    print(f"Total articles processed: {scraped_count + error_count}")
    print(f"  Successful: {scraped_count}")
    print(f"  Errors: {error_count}")
    print()
    print("Results by source:")
    for source, counts in sorted(results_by_source.items()):
        print(f"  {source}: {counts['success']} success, {counts['error']} errors")
    print()
    print("Output directory:", OUTPUT_DIR)
    print()


# =============================================================================
# RUN THE SCRIPT
# =============================================================================

if __name__ == "__main__":
    main()
