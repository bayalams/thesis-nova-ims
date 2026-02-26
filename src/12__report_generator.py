"""
12__report_generator.py - Step 12: Daily Report Generator
=========================================================

This script generates structured daily tourism reports from recent news articles.

WHAT IT DOES:
1. Loads recent articles from data/articles/ (default: last 24 hours)
2. Generates a structured report using one of two modes:
   - SIMPLE: Single-pass report from new articles only
   - REACT: Iterative report using RAG to pull in historical context
3. Saves the report as markdown in data/reports/
4. Optionally starts a web viewer to browse all generated reports

HOW TO RUN:
    # Simple mode: generate a report from today's articles
    python 12__report_generator.py --provider openai --mode simple

    # ReAct mode: iterative report with RAG refinement
    python 12__report_generator.py --provider openai --mode react --max-iterations 3

    # Just view existing reports in the browser
    python 12__report_generator.py --web-only

    # Generate and immediately view
    python 12__report_generator.py --provider openai --mode simple --serve

COMMAND LINE OPTIONS:
    --mode simple|react       Generation mode (default: simple)
    --max-iterations N        Max ReAct iterations (default: 3)
    --hours N                 Look-back window for recent articles (default: 24)
    --provider auto|openai|azure   LLM provider selection
    --serve                   Start web viewer after generating
    --web-only                Only start the web viewer, skip generation

REQUIREMENTS:
    - Run 10__embedder.py first to create the vector database (for ReAct mode)
    - Articles in data/articles/ from the scraping pipeline
"""

# =============================================================================
# IMPORTS
# =============================================================================

import argparse   # Built-in library to parse command line arguments
import glob       # Built-in library to find files by pattern
import json       # Built-in library to read/write JSON files
import os         # Built-in library to work with files and folders
import re         # Built-in library for regex
import time       # Built-in library for timing operations
import uuid       # Built-in library to generate request IDs
from datetime import datetime, timedelta, timezone  # Built-in library for dates
from pathlib import Path                             # Built-in library for paths
from urllib.parse import urlparse                    # Built-in library to parse URLs

# External libraries (install with pip)
import chromadb
from flask import Flask, request, render_template_string, redirect, url_for
from openai import OpenAI, AzureOpenAI, BadRequestError

# =============================================================================
# CONFIGURATION
# =============================================================================

# Where articles are stored
ARTICLES_DIR = "data/articles"

# Where reports are saved
REPORTS_DIR = "data/reports"

# ChromaDB settings (same as embedder and web app)
CHROMA_DIR = os.environ.get("CHROMA_DIR", "data/vectordb")
COLLECTION_NAME = "tourism_knowledge"

# How many documents to retrieve per RAG query in ReAct mode
REACT_TOP_K = 8

# Runtime configuration is stored here after startup
APP_CONFIG = {}


# =============================================================================
# REPORT TEMPLATE
# =============================================================================

REPORT_SYSTEM_PROMPT = """You are a senior tourism intelligence analyst specializing in Portuguese and European tourism.

Your task is to produce a structured Daily Tourism Intelligence Report from the provided news articles.

FORMAT YOUR REPORT IN MARKDOWN USING EXACTLY THIS STRUCTURE:

# Daily Tourism Intelligence Report — {date}

## 1. Executive Summary
Write a 3-5 sentence overview of the most important developments from today's articles. Focus on what matters most for tourism stakeholders.

## 2. Key Themes & Trends
Group the articles by theme/topic. For each theme:
- Use bullet points
- Cite every fact using inline citations: [Source N]
- Identify patterns across multiple articles when possible

## 3. Notable Articles
Pick the 3-5 most significant articles. For each:
- **Title**: the article title
- **Source**: the news outlet
- **Why it matters**: 1-2 sentences on its significance

## 4. Market Signals
List any data points, statistics, visitor numbers, economic indicators, or forward-looking signals found in the articles. If none are present, write "No quantitative signals identified in today's coverage."

## 5. Analyst Notes
This is your free-form section. Provide deeper analysis, draw connections between articles, note emerging patterns, speculate on implications, or flag items that deserve follow-up. Be analytical and insightful.

IMPORTANT — CITATION RULES:
1. You MUST cite the source for EVERY piece of information you provide
2. Use inline citations in the format [Source N] after each fact or claim
3. Example: "Tourism arrivals in Lisbon grew 12% [Source 3] while the Algarve saw record hotel occupancy [Source 7]."
4. If multiple sources confirm the same fact, cite all of them: [Source 1, 3]
5. NEVER state a fact without a citation — this is critical for verification
6. The source numbers are GLOBALLY UNIQUE and PRE-ASSIGNED — use them EXACTLY as given with each article
7. Do NOT renumber or reassign source numbers — Source 42 must always refer to the article labeled [Source 42]
8. Do NOT add a sources/references section at the end — this will be generated automatically

ADDITIONAL RULES:
1. ONLY use information from the provided articles — do not invent facts
2. If there are too few articles to fill a section meaningfully, say so honestly
3. Write in English
4. Be concise but thorough
"""


# =============================================================================
# HELPER FUNCTIONS — PROVIDER / CONFIG
# =============================================================================

def build_request_id():
    """
    Build a short request ID so we can correlate logs.
    """
    return uuid.uuid4().hex[:8]


def mask_api_key(api_key):
    """
    Return a masked API key prefix for logs.
    """
    if not api_key:
        return "(none)"
    return api_key[:8] + "..."


def is_reasoning_model(model_name):
    """
    Return True for model families that require max_completion_tokens
    instead of max_tokens (e.g. gpt-5, o1, o3, o4).
    """
    name = (model_name or "").strip().lower()

    if name.startswith("gpt-5"):
        return True
    if name.startswith("o1") or name.startswith("o3") or name.startswith("o4"):
        return True
    if "reasoning" in name:
        return True

    return False


def build_chat_params(model_name, token_limit=4000):
    """
    Build chat completion parameters in a provider/model-safe way.

    Reasoning models (gpt-5, o-series) use max_completion_tokens and
    do not support temperature. Standard models use max_tokens + temperature.
    """
    params = {}

    if is_reasoning_model(model_name):
        # Reasoning models include thought tokens in the limit.
        # If the default 4000 is passed, bump it up (but not too high
        # to avoid exhausting Azure S0 rate limits per request).
        if token_limit == 4000:
            token_limit = 16000
        params["max_completion_tokens"] = token_limit
        params["reasoning_effort"] = "minimal"
    else:
        params["temperature"] = 0.7
        params["max_tokens"] = token_limit

    return params


def get_int_env(var_name, default_value):
    """
    Safely parse an integer environment variable.
    """
    raw = os.environ.get(var_name)
    if raw is None:
        return default_value

    try:
        return int(raw.strip())
    except Exception:
        print(f"[WARNING] Invalid integer for {var_name}: '{raw}' (using {default_value})")
        return default_value


def get_strategy_tuning(strategy_name, default_batch_size=30, default_chars_per_article=1500, default_token_limit=4000):
    """
    Return provider-aware tuning knobs for heavy report strategies.

    ENV OVERRIDES (optional):
    - REPORT_BATCH_SIZE
    - REPORT_MAX_CHARS_PER_ARTICLE
    - REPORT_TOKEN_LIMIT
    - <STRATEGY>_BATCH_SIZE (e.g., MAP_REDUCE_BATCH_SIZE)
    - <STRATEGY>_MAX_CHARS_PER_ARTICLE
    - <STRATEGY>_TOKEN_LIMIT
    """
    provider = APP_CONFIG.get("provider", "")
    model_name = APP_CONFIG.get("llm_model", "")
    reasoning = is_reasoning_model(model_name)

    batch_size = default_batch_size
    chars_per_article = default_chars_per_article
    token_limit = default_token_limit

    # Azure deployments (especially S0 + reasoning models) tend to hit
    # quota/context limits first on map-reduce/progressive prompts.
    if provider == "azure":
        if reasoning:
            batch_size = min(batch_size, 12)
            chars_per_article = min(chars_per_article, 900)
            token_limit = min(token_limit, 2200)
        else:
            batch_size = min(batch_size, 20)
            chars_per_article = min(chars_per_article, 1200)
            token_limit = min(token_limit, 2500)

    # Global overrides
    batch_size = get_int_env("REPORT_BATCH_SIZE", batch_size)
    chars_per_article = get_int_env("REPORT_MAX_CHARS_PER_ARTICLE", chars_per_article)
    token_limit = get_int_env("REPORT_TOKEN_LIMIT", token_limit)

    # Strategy-specific overrides
    strategy_key = (strategy_name or "").strip().upper().replace("-", "_")
    if strategy_key:
        batch_size = get_int_env(f"{strategy_key}_BATCH_SIZE", batch_size)
        chars_per_article = get_int_env(f"{strategy_key}_MAX_CHARS_PER_ARTICLE", chars_per_article)
        token_limit = get_int_env(f"{strategy_key}_TOKEN_LIMIT", token_limit)

    # Keep values in sane ranges
    batch_size = max(1, batch_size)
    chars_per_article = max(300, chars_per_article)
    token_limit = max(400, token_limit)

    return {
        "batch_size": batch_size,
        "chars_per_article": chars_per_article,
        "token_limit": token_limit,
    }


def adjust_bad_request_kwargs(current_kwargs, error_text, request_id="", label="LLM"):
    """
    Try to recover from known provider/model parameter mismatches.
    """
    adjusted = False
    error_lower = (error_text or "").lower()

    if "temperature" in error_lower and "temperature" in current_kwargs:
        print(f"[REQ {request_id}] [{label}] [WARNING] Removing unsupported 'temperature' and retrying")
        current_kwargs.pop("temperature", None)
        adjusted = True

    if "max_tokens" in error_lower and "max_completion_tokens" in error_lower and "max_tokens" in current_kwargs:
        print(f"[REQ {request_id}] [{label}] [WARNING] Switching max_tokens -> max_completion_tokens and retrying")
        current_kwargs["max_completion_tokens"] = current_kwargs.pop("max_tokens")
        adjusted = True

    if "max_completion_tokens" in error_lower and "max_tokens" in error_lower and "max_completion_tokens" in current_kwargs:
        print(f"[REQ {request_id}] [{label}] [WARNING] Switching max_completion_tokens -> max_tokens and retrying")
        current_kwargs["max_tokens"] = current_kwargs.pop("max_completion_tokens")
        adjusted = True

    if "reasoning_effort" in error_lower and "reasoning_effort" in current_kwargs:
        print(f"[REQ {request_id}] [{label}] [WARNING] Removing unsupported 'reasoning_effort' and retrying")
        current_kwargs.pop("reasoning_effort", None)
        adjusted = True

    tool_error = (
        "tool_choice" in error_lower
        or "function_call" in error_lower
        or "function call" in error_lower
        or ("tool" in error_lower and ("unsupported" in error_lower or "not support" in error_lower or "invalid" in error_lower))
    )
    if tool_error and ("tools" in current_kwargs or "tool_choice" in current_kwargs):
        print(f"[REQ {request_id}] [{label}] [WARNING] Disabling tools for this request and retrying")
        current_kwargs.pop("tools", None)
        current_kwargs.pop("tool_choice", None)
        adjusted = True

    context_error = (
        "maximum context length" in error_lower
        or "context length" in error_lower
        or "too many tokens" in error_lower
        or "is too long" in error_lower
    )
    if context_error:
        if "max_completion_tokens" in current_kwargs:
            old = int(current_kwargs["max_completion_tokens"])
            new = max(800, old // 2)
            if new < old:
                print(f"[REQ {request_id}] [{label}] [WARNING] Reducing max_completion_tokens {old} -> {new} after context error")
                current_kwargs["max_completion_tokens"] = new
                adjusted = True
        elif "max_tokens" in current_kwargs:
            old = int(current_kwargs["max_tokens"])
            new = max(400, old // 2)
            if new < old:
                print(f"[REQ {request_id}] [{label}] [WARNING] Reducing max_tokens {old} -> {new} after context error")
                current_kwargs["max_tokens"] = new
                adjusted = True

    return adjusted


def get_host_from_url(url):
    """
    Extract the host from a URL for cleaner logs.
    """
    try:
        parsed = urlparse(url)
        return parsed.hostname or url
    except Exception:
        return url


def resolve_provider(cli_provider):
    """
    Resolve which provider to use.

    Priority:
    1) --provider
    2) LLM_PROVIDER environment variable
    3) auto-detection
    """
    provider = cli_provider
    if not provider:
        provider = os.environ.get("LLM_PROVIDER", "auto")

    provider = provider.strip().lower()
    valid = {"auto", "azure", "openai"}

    if provider not in valid:
        print(f"[ERROR] Invalid provider '{provider}'.")
        print("[ERROR] Valid options: auto, openai, azure")
        raise SystemExit(1)

    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_key = os.environ.get("AZURE_OPENAI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if provider == "openai":
        if not openai_key:
            print("[ERROR] OPENAI_API_KEY is missing.")
            raise SystemExit(1)
        return "openai"

    if provider == "azure":
        if not azure_endpoint or not azure_key:
            print("[ERROR] Azure credentials are missing.")
            print("Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY.")
            raise SystemExit(1)
        return "azure"

    # Auto mode
    if openai_key:
        return "openai"
    if azure_endpoint and azure_key:
        return "azure"

    print("[ERROR] Could not auto-detect provider.")
    print("Provide one of:")
    print("  - OPENAI_API_KEY")
    print("  - AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY")
    raise SystemExit(1)


def get_model_names(provider):
    """
    Get LLM and embedding model names.
    """
    if provider == "azure":
        llm_model = os.environ.get("AZURE_LLM_DEPLOYMENT", "gpt-5")
        embedding_model = os.environ.get("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
    else:
        llm_model = os.environ.get("OPENAI_LLM_MODEL", "gpt-4o-mini")
        embedding_model = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

    return llm_model, embedding_model


def build_llm_client(provider):
    """
    Build the OpenAI/Azure client.
    """
    if provider == "azure":
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

        if not endpoint or not api_key:
            print("[ERROR] Azure OpenAI credentials not found.")
            print("Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY.")
            raise SystemExit(1)

        if api_version == "2024-02-15-preview":
            print("[WARNING] AZURE_OPENAI_API_VERSION is still using the old default (2024-02-15-preview).")
            print("[WARNING] If you use newer deployments/features, set a newer AZURE_OPENAI_API_VERSION explicitly.")

        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )
        return client, get_host_from_url(endpoint), api_version, api_key

    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "").strip()

    if not api_key:
        print("[ERROR] OpenAI API key not found.")
        print("Set OPENAI_API_KEY.")
        raise SystemExit(1)

    if base_url:
        client = OpenAI(api_key=api_key, base_url=base_url)
        endpoint_host = get_host_from_url(base_url)
    else:
        client = OpenAI(api_key=api_key)
        endpoint_host = "api.openai.com"

    return client, endpoint_host, "n/a", api_key


# =============================================================================
# HELPER FUNCTIONS — ARTICLE LOADING
# =============================================================================

def parse_article_date(article):
    """
    Extract a datetime from the article metadata.

    Tries multiple date fields in priority order.

    RETURNS:
    - A datetime object, or None if no date could be parsed
    """
    meta = article.get("metadata", {})

    # Try these fields in order
    date_fields = ["scraped_at", "date", "published", "published_at", "indexed_at"]

    for field in date_fields:
        value = meta.get(field)
        if not value:
            continue

        # Try ISO format first (e.g. "2026-02-18T10:30:00.123456")
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            # If no timezone info, assume UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass

        # Try date-only format (e.g. "2026-02-18")
        try:
            dt = datetime.strptime(value, "%Y-%m-%d")
            dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass

        # Try RSS date format (e.g. "Sat, 07 Feb 2026 08:01:17 +0100")
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass

    return None


def load_recent_articles(hours=24):
    """
    Load articles from data/articles/ that are within the last N hours.

    PARAMETERS:
    - hours: Number of hours to look back (default: 24)

    RETURNS:
    - A list of article dictionaries, sorted newest-first
    """
    print(f"[INFO] Loading articles from {ARTICLES_DIR}/ (last {hours} hours)")

    if not os.path.exists(ARTICLES_DIR):
        print(f"[WARNING] Articles directory not found: {ARTICLES_DIR}")
        return []

    # Calculate the cutoff time
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours)
    print(f"[INFO] Current time (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[INFO] Cutoff time (UTC):  {cutoff.strftime('%Y-%m-%d %H:%M:%S')}")

    # Find all JSON files
    json_files = glob.glob(os.path.join(ARTICLES_DIR, "*.json"))
    print(f"[INFO] Found {len(json_files)} total article files")

    # Load and filter
    recent_articles = []
    skipped_no_date = 0
    skipped_too_old = 0
    errors = 0

    for filepath in json_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                article = json.load(f)

            article_date = parse_article_date(article)

            if article_date is None:
                skipped_no_date = skipped_no_date + 1
                continue

            if article_date < cutoff:
                skipped_too_old = skipped_too_old + 1
                continue

            # Add the parsed date for sorting
            article["_parsed_date"] = article_date
            recent_articles.append(article)

        except Exception as e:
            errors = errors + 1
            if errors <= 3:
                print(f"[WARNING] Error reading {os.path.basename(filepath)}: {e}")

    # Sort by date, newest first
    recent_articles.sort(key=lambda a: a["_parsed_date"], reverse=True)

    print(f"[INFO] Recent articles: {len(recent_articles)}")
    print(f"[INFO] Skipped (no date): {skipped_no_date}")
    print(f"[INFO] Skipped (too old): {skipped_too_old}")
    if errors > 0:
        print(f"[WARNING] Errors reading files: {errors}")

    return recent_articles


def format_articles_for_prompt(articles, max_chars_per_article=2000, start_index=1):
    """
    Format a list of articles into a text block for the LLM prompt.

    PARAMETERS:
    - articles: List of article dicts
    - max_chars_per_article: Max characters of content per article
    - start_index: Starting source number (for global numbering across batches)

    RETURNS:
    - A formatted string with all articles
    """
    parts = []

    for i, article in enumerate(articles, start=start_index):
        meta = article.get("metadata", {})
        title = meta.get("title", "Untitled")
        source = meta.get("source", "Unknown")
        date = meta.get("date", "Unknown date")
        url = meta.get("link", "")

        # Get the article content (make sure it's never None)
        content = article.get("scraped_content", "") or ""
        if not content:
            content = article.get("content", "") or ""
        if not content:
            # Try to get summary from metadata
            content = meta.get("summary", "") or "(no content available)"

        # Truncate if too long
        if len(content) > max_chars_per_article:
            content = content[:max_chars_per_article] + "...(truncated)"

        parts.append(
            f"[Source {i}: {title}]\n"
            f"Outlet: {source}\n"
            f"Date: {date}\n"
            f"URL: {url}\n"
            f"Content:\n{content}\n"
        )

    return "\n".join(parts)


def format_article_titles(articles):
    """
    Format just the titles/source/date of articles for lightweight LLM context.

    This is much cheaper than full content — about 50-80 chars per article.
    Used by the triage and hybrid strategies.

    PARAMETERS:
    - articles: List of article dicts

    RETURNS:
    - A formatted string with numbered article titles
    """
    parts = []

    for i, article in enumerate(articles, start=1):
        meta = article.get("metadata", {})
        title = meta.get("title", "Untitled") or "Untitled"
        source = meta.get("source", "Unknown") or "Unknown"
        date = meta.get("date", "Unknown") or "Unknown"

        parts.append(f"[Source {i}] [{source}] ({date}) {title}")

    return "\n".join(parts)


def build_sources_section(articles, start_index=1):
    """
    Build a '## Sources' markdown section from the articles list.

    This is appended to the end of every generated report so that
    [Source N] inline citations can be traced back to the original articles.

    PARAMETERS:
    - articles: List of article dicts that were used in the report
    - start_index: Starting source number (must match format_articles_for_prompt)

    RETURNS:
    - A markdown string with a numbered sources section
    """
    lines = []
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Sources")
    lines.append("")

    for i, article in enumerate(articles, start=start_index):
        meta = article.get("metadata", {})
        title = meta.get("title", "Untitled") or "Untitled"
        source = meta.get("source", "Unknown") or "Unknown"
        date = meta.get("date", "Unknown") or "Unknown"
        url = meta.get("link", "") or ""

        if url:
            lines.append(f"{i}. **{title}** — {source}, {date} — [link]({url})")
        else:
            lines.append(f"{i}. **{title}** — {source}, {date}")

    lines.append("")
    return "\n".join(lines)


def strip_llm_sources_section(report_text):
    """
    Remove any ## Sources or ## References section that the LLM may have
    generated in its output.

    We auto-generate this section via build_sources_section(), so any
    LLM-generated version would create duplicates or mismatched numbering.

    PARAMETERS:
    - report_text: The LLM-generated report markdown

    RETURNS:
    - The report text with any trailing Sources/References section removed
    """

    # Match ## Sources or ## References (with optional leading ---)
    # at the end of the text, possibly followed by numbered items
    pattern = r'\n---\s*\n+##\s+(Sources|References)\s*\n.*'
    cleaned = re.sub(pattern, '', report_text, flags=re.DOTALL | re.IGNORECASE)

    # Also handle case without --- separator
    pattern2 = r'\n##\s+(Sources|References)\s*\n\s*\d+\.\s.*'
    cleaned = re.sub(pattern2, '', cleaned, flags=re.DOTALL | re.IGNORECASE)

    return cleaned.rstrip()


def validate_source_citations(report_text, num_articles, request_id=""):
    """
    Scan the report for [Source N] citations and warn if N exceeds the
    total number of articles. This detects LLM renumbering or hallucination.

    PARAMETERS:
    - report_text: The report markdown text (before sources section)
    - num_articles: Total number of articles in the source list
    - request_id: Correlation ID for log messages

    RETURNS:
    - None (logs warnings to stdout)
    """

    # Find all [Source N] or [Source N, M, ...] patterns
    citations = re.findall(r'\[Source\s+(\d+(?:\s*,\s*\d+)*)\]', report_text)

    all_nums = set()
    for citation in citations:
        nums = [int(n.strip()) for n in citation.split(',')]
        all_nums.update(nums)

    if not all_nums:
        print(f"[REQ {request_id}] [VALIDATE] No source citations found in report")
        return

    max_cited = max(all_nums)
    out_of_range = [n for n in sorted(all_nums) if n > num_articles or n < 1]

    print(f"[REQ {request_id}] [VALIDATE] Found {len(all_nums)} unique source numbers cited (range: 1-{max_cited})")
    print(f"[REQ {request_id}] [VALIDATE] Total articles in source list: {num_articles}")

    if out_of_range:
        print(f"[REQ {request_id}] [WARNING] {len(out_of_range)} citation(s) reference non-existent sources: {out_of_range}")
        print(f"[REQ {request_id}] [WARNING] This may indicate the LLM renumbered sources — verify report accuracy")
    else:
        print(f"[REQ {request_id}] [VALIDATE] All citations are within valid range ✓")


def call_llm(client, messages, tools=None, request_id="", label="LLM", token_limit=4000):
    """
    Shared wrapper for LLM calls with logging, error handling, and
    automatic retry on 429 rate-limit errors.

    PARAMETERS:
    - client: OpenAI/Azure client
    - messages: List of message dicts
    - tools: Optional list of tool definitions
    - request_id: Correlation ID for logs
    - label: Label for log messages (e.g. "MAP-REDUCE", "TRIAGE")

    RETURNS:
    - The response object, or None if failed
    """
    MAX_RETRIES = 3
    BASE_WAIT = 60  # seconds — Azure usually asks for 60s

    started = time.time()

    kwargs = {
        "model": APP_CONFIG["llm_model"],
        "messages": messages,
    }
    kwargs.update(build_chat_params(APP_CONFIG["llm_model"], token_limit=token_limit))

    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    current_kwargs = dict(kwargs)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(**current_kwargs)
            break  # success

        except BadRequestError as e:
            error_str = str(e)
            adjusted = adjust_bad_request_kwargs(current_kwargs, error_str, request_id, label)
            if adjusted and attempt < MAX_RETRIES:
                continue

            print(f"[REQ {request_id}] [{label}] [ERROR] BadRequestError: {e}")
            return None

        except Exception as e:
            error_str = str(e)

            # Retry on 429 rate limit
            if "429" in error_str or "RateLimitReached" in error_str:
                wait = BASE_WAIT * attempt  # 60s, 120s, 240s
                print(f"[REQ {request_id}] [{label}] [RATE-LIMIT] Attempt {attempt}/{MAX_RETRIES} — waiting {wait}s...")
                time.sleep(wait)
                if attempt == MAX_RETRIES:
                    print(f"[REQ {request_id}] [{label}] [ERROR] Rate limit exceeded after {MAX_RETRIES} retries")
                    return None
            else:
                print(f"[REQ {request_id}] [{label}] [ERROR] LLM call failed: {e}")
                return None

    elapsed_ms = (time.time() - started) * 1000

    # Log stats
    usage = getattr(response, "usage", None)
    prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
    completion_tokens = getattr(usage, "completion_tokens", None) if usage else None
    total_tokens = getattr(usage, "total_tokens", None) if usage else None
    print(f"[REQ {request_id}] [{label}] Latency: {elapsed_ms:.1f} ms")
    print(f"[REQ {request_id}] [{label}] Tokens: {prompt_tokens}/{completion_tokens}/{total_tokens}")
    print(f"[REQ {request_id}] [{label}] Params: {sorted(current_kwargs.keys())}")

    return response


def extract_content(response):
    """
    Extract the text content from an LLM response.

    RETURNS:
    - The content string, or empty string if not available
    """
    choices = getattr(response, "choices", []) or []
    if not choices:
        return ""

    return getattr(choices[0].message, "content", "") or ""


def extract_tool_calls(response):
    """
    Extract tool calls from an LLM response.

    RETURNS:
    - List of tool call objects, or empty list
    """
    choices = getattr(response, "choices", []) or []
    if not choices:
        return []

    tool_calls = getattr(choices[0].message, "tool_calls", None)
    return tool_calls or []


# =============================================================================
# HELPER FUNCTIONS — CHROMADB
# =============================================================================

def get_chromadb_collection():
    """
    Get the ChromaDB collection for RAG queries.
    """
    if not os.path.exists(CHROMA_DIR):
        print("[ERROR] Vector database not found!")
        print()
        print("Please run 10__embedder.py first to create the database.")
        print()
        raise SystemExit(1)

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(name=COLLECTION_NAME)

    return collection


def search_knowledge_base(collection, client, query, top_k, request_id):
    """
    Search the vector database for documents related to a query.

    PARAMETERS:
    - collection: ChromaDB collection
    - client: OpenAI/Azure client (for embeddings)
    - query: Search query string
    - top_k: Number of results to return
    - request_id: Correlation ID for logs

    RETURNS:
    - A formatted string of search results
    """
    print(f"[REQ {request_id}] [RAG] Searching: '{query[:80]}...'")

    # Step 1: Create embedding for the query
    response = client.embeddings.create(
        model=APP_CONFIG["embedding_model"],
        input=query,
    )
    question_embedding = response.data[0].embedding

    # Step 2: Search ChromaDB (news articles only)
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        where={"type": "news"},
    )

    # Step 3: Format results
    ids = results.get("ids") or [[]]
    docs = results.get("documents") or [[]]
    metas = results.get("metadatas") or [[]]

    if not ids or not ids[0]:
        print(f"[REQ {request_id}] [RAG] No results found")
        return "No relevant articles found in the knowledge base."

    print(f"[REQ {request_id}] [RAG] Found {len(ids[0])} results")

    formatted_parts = []
    for i in range(len(ids[0])):
        meta = metas[0][i]
        content = docs[0][i]
        title = meta.get("title", "Untitled")
        source = meta.get("source", "Unknown")
        date = meta.get("date", "Unknown")

        # Truncate content
        if len(content) > 1500:
            content = content[:1500] + "...(truncated)"

        formatted_parts.append(
            f"[Historical Article: {title}]\n"
            f"Source: {source} | Date: {date}\n"
            f"{content}\n"
        )

    return "\n---\n".join(formatted_parts)


# =============================================================================
# REPORT GENERATION — SIMPLE MODE
# =============================================================================

def generate_simple_report(client, articles, request_id):
    """
    Generate a report in a single LLM call.

    PARAMETERS:
    - client: OpenAI/Azure client
    - articles: List of recent article dicts
    - request_id: Correlation ID for logs

    RETURNS:
    - The report as a markdown string, or None if failed
    """
    # Cap the number of articles to avoid exceeding token limits
    # We keep the most recent ones (already sorted newest-first)
    MAX_ARTICLES = 30
    if len(articles) > MAX_ARTICLES:
        print(f"[REQ {request_id}] [SIMPLE] Capping articles from {len(articles)} to {MAX_ARTICLES} (most recent)")
        articles = articles[:MAX_ARTICLES]

    print(f"[REQ {request_id}] [SIMPLE] Generating report from {len(articles)} articles")

    # Step 1: Format articles for the prompt
    articles_text = format_articles_for_prompt(articles)

    # Step 2: Build the prompt
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    system_prompt = REPORT_SYSTEM_PROMPT.replace("{date}", today)

    user_prompt = f"""Here are today's tourism news articles:

{articles_text}

---

Please generate the Daily Tourism Intelligence Report based on these articles.
Use today's date: {today}
"""

    print(f"[REQ {request_id}] [SIMPLE] System prompt: {len(system_prompt)} chars")
    print(f"[REQ {request_id}] [SIMPLE] User prompt: {len(user_prompt)} chars")
    print(f"[REQ {request_id}] [SIMPLE] Model: {APP_CONFIG['llm_model']}")

    # Step 3: Call the LLM
    started = time.time()

    try:
        chat_params = build_chat_params(APP_CONFIG["llm_model"])
        response = client.chat.completions.create(
            model=APP_CONFIG["llm_model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **chat_params,
        )
    except Exception as e:
        print(f"[REQ {request_id}] [ERROR] LLM call failed: {e}")
        return None

    elapsed_ms = (time.time() - started) * 1000

    # Step 4: Extract the response
    choices = getattr(response, "choices", []) or []
    if not choices:
        print(f"[REQ {request_id}] [ERROR] Model returned no choices")
        return None

    content = getattr(choices[0].message, "content", "") or ""

    # Log stats
    usage = getattr(response, "usage", None)
    prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
    completion_tokens = getattr(usage, "completion_tokens", None) if usage else None
    total_tokens = getattr(usage, "total_tokens", None) if usage else None

    print(f"[REQ {request_id}] [SIMPLE] Latency: {elapsed_ms:.1f} ms")
    print(f"[REQ {request_id}] [SIMPLE] Tokens: {prompt_tokens}/{completion_tokens}/{total_tokens}")
    print(f"[REQ {request_id}] [SIMPLE] Report length: {len(content)} chars")

    if not content.strip():
        print(f"[REQ {request_id}] [ERROR] Model returned empty response")
        return None

    # Strip any sources section the LLM may have added, validate, then append correct sources
    content = strip_llm_sources_section(content)
    validate_source_citations(content, len(articles), request_id)
    content += build_sources_section(articles)

    return content


# =============================================================================
# REPORT GENERATION — REACT MODE
# =============================================================================

# The tool definition for the RAG search
REACT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the historical knowledge base for articles related to a query. "
                "Use this to find supporting evidence, historical context, related trends, "
                "or past coverage of topics mentioned in today's articles. "
                "This helps you write a more informed and contextual report."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant historical articles"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


def generate_react_report(client, articles, collection, max_iterations, request_id):
    """
    Generate a report using an iterative ReAct loop with RAG.

    The LLM can call search_knowledge_base() to pull historical articles,
    then refine its report with that extra context.

    PARAMETERS:
    - client: OpenAI/Azure client
    - articles: List of recent article dicts
    - collection: ChromaDB collection for RAG
    - max_iterations: Maximum number of tool-use iterations
    - request_id: Correlation ID for logs

    RETURNS:
    - The report as a markdown string, or None if failed
    """
    # Cap the number of seed articles to avoid exceeding token limits
    MAX_ARTICLES = 30
    if len(articles) > MAX_ARTICLES:
        print(f"[REQ {request_id}] [REACT] Capping seed articles from {len(articles)} to {MAX_ARTICLES} (most recent)")
        articles = articles[:MAX_ARTICLES]

    print(f"[REQ {request_id}] [REACT] Starting ReAct loop (max {max_iterations} iterations)")
    print(f"[REQ {request_id}] [REACT] Seed articles: {len(articles)}")

    # Step 1: Format today's articles
    articles_text = format_articles_for_prompt(articles)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    system_prompt = REPORT_SYSTEM_PROMPT.replace("{date}", today)

    # Add ReAct instructions to system prompt
    system_prompt += """

ADDITIONAL INSTRUCTIONS FOR RESEARCH MODE:
You have access to a tool called search_knowledge_base that lets you search our historical article database.
Use it to:
- Find past coverage of topics mentioned in today's articles
- Get historical context for trends
- Find supporting evidence or contradicting information
- Discover related articles that strengthen your analysis

You may call the tool multiple times. When you have enough context, produce the final report WITHOUT calling the tool.
"""

    user_prompt = f"""Here are today's tourism news articles:

{articles_text}

---

Please generate the Daily Tourism Intelligence Report based on these articles.
Use today's date: {today}

You may use the search_knowledge_base tool to look up historical articles for additional context before writing your final report.
"""

    # Step 2: Build the initial conversation
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    print(f"[REQ {request_id}] [REACT] System prompt: {len(system_prompt)} chars")
    print(f"[REQ {request_id}] [REACT] User prompt: {len(user_prompt)} chars")
    print(f"[REQ {request_id}] [REACT] Model: {APP_CONFIG['llm_model']}")

    # Step 3: ReAct loop
    total_started = time.time()

    for iteration in range(1, max_iterations + 1):
        print()
        print(f"[REQ {request_id}] [REACT] === Iteration {iteration}/{max_iterations} ===")

        # Call the LLM with tools
        started = time.time()

        try:
            chat_params = build_chat_params(APP_CONFIG["llm_model"])
            response = client.chat.completions.create(
                model=APP_CONFIG["llm_model"],
                messages=messages,
                tools=REACT_TOOLS,
                tool_choice="auto",
                **chat_params,
            )
        except Exception as e:
            print(f"[REQ {request_id}] [ERROR] LLM call failed: {e}")
            return None

        elapsed_ms = (time.time() - started) * 1000

        # Log stats
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
        completion_tokens = getattr(usage, "completion_tokens", None) if usage else None
        print(f"[REQ {request_id}] [REACT] Latency: {elapsed_ms:.1f} ms")
        print(f"[REQ {request_id}] [REACT] Tokens: {prompt_tokens}/{completion_tokens}")

        # Check the response
        choices = getattr(response, "choices", []) or []
        if not choices:
            print(f"[REQ {request_id}] [ERROR] Model returned no choices")
            return None

        message = choices[0].message
        finish_reason = getattr(choices[0], "finish_reason", None)
        tool_calls = getattr(message, "tool_calls", None)

        print(f"[REQ {request_id}] [REACT] Finish reason: {finish_reason}")
        print(f"[REQ {request_id}] [REACT] Tool calls: {len(tool_calls) if tool_calls else 0}")

        # If no tool calls, the model is done — extract the report
        if not tool_calls:
            content = getattr(message, "content", "") or ""
            print(f"[REQ {request_id}] [REACT] Final report length: {len(content)} chars")

            total_elapsed = (time.time() - total_started) * 1000
            print(f"[REQ {request_id}] [REACT] Total time: {total_elapsed:.1f} ms")
            print(f"[REQ {request_id}] [REACT] Completed in {iteration} iteration(s)")

            if not content.strip():
                print(f"[REQ {request_id}] [ERROR] Model returned empty response")
                return None

            # Strip any sources section the LLM may have added, validate, then append correct sources
            content = strip_llm_sources_section(content)
            validate_source_citations(content, len(articles), request_id)
            content += build_sources_section(articles)

            return content

        # Process tool calls
        # Add the assistant message to conversation history
        messages.append(message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            call_id = tool_call.id

            if function_name == "search_knowledge_base":
                # Parse the arguments
                try:
                    args = json.loads(tool_call.function.arguments)
                    query = args.get("query", "")
                except Exception as e:
                    print(f"[REQ {request_id}] [WARNING] Failed to parse tool args: {e}")
                    query = ""

                print(f"[REQ {request_id}] [REACT] Tool call: search_knowledge_base('{query[:60]}...')")

                # Execute the search
                if query:
                    result = search_knowledge_base(
                        collection, client, query, REACT_TOP_K, request_id
                    )
                else:
                    result = "Error: empty query provided"

                # Add the tool result to the conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": result,
                })
            else:
                print(f"[REQ {request_id}] [WARNING] Unknown tool: {function_name}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": f"Error: unknown tool '{function_name}'",
                })

    # If we exhausted all iterations, make one final call WITHOUT tools
    # to force the model to produce the report
    print()
    print(f"[REQ {request_id}] [REACT] Max iterations reached. Forcing final report...")

    messages.append({
        "role": "user",
        "content": "You have reached the maximum number of research iterations. Please produce the final report now based on all the information gathered.",
    })

    try:
        chat_params = build_chat_params(APP_CONFIG["llm_model"])
        response = client.chat.completions.create(
            model=APP_CONFIG["llm_model"],
            messages=messages,
            **chat_params,
        )
    except Exception as e:
        print(f"[REQ {request_id}] [ERROR] Final LLM call failed: {e}")
        return None

    choices = getattr(response, "choices", []) or []
    if not choices:
        print(f"[REQ {request_id}] [ERROR] Final call returned no choices")
        return None

    content = getattr(choices[0].message, "content", "") or ""

    total_elapsed = (time.time() - total_started) * 1000
    print(f"[REQ {request_id}] [REACT] Final report length: {len(content)} chars")
    print(f"[REQ {request_id}] [REACT] Total time: {total_elapsed:.1f} ms")
    print(f"[REQ {request_id}] [REACT] Completed (max iterations forced)")

    if not content.strip():
        print(f"[REQ {request_id}] [ERROR] Model returned empty response")
        return None

    # Strip any sources section the LLM may have added, validate, then append correct sources
    content = strip_llm_sources_section(content)
    validate_source_citations(content, len(articles), request_id)
    content += build_sources_section(articles)

    return content


# =============================================================================
# REACT STRATEGIES — TOOL DEFINITIONS
# =============================================================================

# Tool for the triage and hybrid strategies: read a specific article's full content
READ_ARTICLE_TOOL = {
    "type": "function",
    "function": {
        "name": "read_article",
        "description": (
            "Read the full content of a specific article by its index number "
            "from the article list. Use this to get detailed content for articles "
            "that seem most relevant to tourism analysis."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "index": {
                    "type": "integer",
                    "description": "The article index number from the list (1-based)"
                }
            },
            "required": ["index"]
        }
    }
}

# Tools for triage strategy: read_article + search_knowledge_base
TRIAGE_TOOLS = [READ_ARTICLE_TOOL, REACT_TOOLS[0]]


# =============================================================================
# REACT STRATEGY 1 — MAP-REDUCE
# =============================================================================

BATCH_SUMMARY_PROMPT = """You are a tourism intelligence analyst. Summarize the key tourism-related insights from the following batch of news articles.

Focus on:
- Tourism-relevant developments
- Market trends and signals
- Notable events or policy changes
- Any statistics or data points

Be concise but capture all important points.
CRITICAL: When citing facts, use the EXACT [Source N] numbers provided with each article. Do NOT renumber them.
If no articles are relevant to tourism, say "No tourism-relevant content in this batch."
"""


def generate_map_reduce_report(client, articles, collection, max_iterations, request_id):
    """
    Strategy 1: Map-Reduce.

    Batch articles into groups, summarize each batch with one LLM call,
    then synthesize all summaries into a final structured report.
    Optionally uses RAG to enrich with historical context.

    PARAMETERS:
    - client: OpenAI/Azure client
    - articles: List of ALL recent article dicts
    - collection: ChromaDB collection (or None)
    - max_iterations: Max ReAct iterations for final enrichment
    - request_id: Correlation ID for logs

    RETURNS:
    - The report as a markdown string, or None if failed
    """
    tuning = get_strategy_tuning(
        "map_reduce",
        default_batch_size=30,
        default_chars_per_article=1500,
        default_token_limit=3000,
    )
    BATCH_SIZE = tuning["batch_size"]
    BATCH_CHARS = tuning["chars_per_article"]
    TOKEN_LIMIT = tuning["token_limit"]
    REDUCE_TOKEN_LIMIT = get_int_env(
        "MAP_REDUCE_REDUCE_TOKEN_LIMIT",
        max(TOKEN_LIMIT, 4200 if is_reasoning_model(APP_CONFIG["llm_model"]) else TOKEN_LIMIT),
    )
    SUMMARY_CHAR_CAP = get_int_env(
        "MAP_REDUCE_BATCH_SUMMARY_CHAR_CAP",
        1200 if APP_CONFIG.get("provider") == "azure" else 2000,
    )
    label = "MAP-REDUCE"

    total_started = time.time()
    print(f"[REQ {request_id}] [{label}] Starting map-reduce over {len(articles)} articles")
    print(f"[REQ {request_id}] [{label}] Batch size: {BATCH_SIZE}")
    print(f"[REQ {request_id}] [{label}] Max chars/article: {BATCH_CHARS}")
    print(f"[REQ {request_id}] [{label}] Token limit/call: {TOKEN_LIMIT}")
    print(f"[REQ {request_id}] [{label}] Reduce token limit: {REDUCE_TOKEN_LIMIT}")
    print(f"[REQ {request_id}] [{label}] Batch summary char cap: {SUMMARY_CHAR_CAP}")

    # =========================================================================
    # PHASE 1: MAP — Summarize each batch
    # =========================================================================

    # Split articles into batches
    batches = []
    for i in range(0, len(articles), BATCH_SIZE):
        batches.append(articles[i : i + BATCH_SIZE])

    print(f"[REQ {request_id}] [{label}] Number of batches: {len(batches)}")

    batch_summaries = []

    for batch_num, batch in enumerate(batches, start=1):
        print()
        print(f"[REQ {request_id}] [{label}] --- Batch {batch_num}/{len(batches)} ({len(batch)} articles) ---")

        articles_text = format_articles_for_prompt(
            batch,
            max_chars_per_article=BATCH_CHARS,
            start_index=(batch_num - 1) * BATCH_SIZE + 1,
        )

        messages = [
            {"role": "system", "content": BATCH_SUMMARY_PROMPT},
            {"role": "user", "content": f"Here are the articles:\n\n{articles_text}"},
        ]

        response = call_llm(
            client,
            messages,
            request_id=request_id,
            label=label,
            token_limit=TOKEN_LIMIT,
        )
        if not response:
            print(f"[REQ {request_id}] [{label}] [WARNING] Batch {batch_num} failed, skipping")
            continue

        summary = extract_content(response)
        if summary.strip():
            if len(summary) > SUMMARY_CHAR_CAP:
                summary = summary[:SUMMARY_CHAR_CAP] + "...(truncated for reduce)"
            batch_summaries.append(f"--- Batch {batch_num} Summary ---\n{summary}")
            print(f"[REQ {request_id}] [{label}] Batch {batch_num} summary: {len(summary)} chars")

        # Cooldown between batches for reasoning models (high token usage)
        if is_reasoning_model(APP_CONFIG["llm_model"]) and batch_num < len(batches):
            print(f"[REQ {request_id}] [{label}] Cooling down 10s (reasoning model)...")
            time.sleep(10)

    if not batch_summaries:
        print(f"[REQ {request_id}] [{label}] [ERROR] All batches failed")
        return None

    print()
    print(f"[REQ {request_id}] [{label}] Map phase complete: {len(batch_summaries)} summaries")

    # =========================================================================
    # PHASE 2: REDUCE — Synthesize all summaries into final report
    # =========================================================================

    # Extra cooldown before the reduce call (largest single request)
    if is_reasoning_model(APP_CONFIG["llm_model"]):
        print(f"[REQ {request_id}] [{label}] Cooling down 30s before reduce (reasoning model)...")
        time.sleep(30)

    print()
    print(f"[REQ {request_id}] [{label}] Starting reduce phase...")

    all_summaries = "\n\n".join(batch_summaries)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    system_prompt = REPORT_SYSTEM_PROMPT.replace("{date}", today)

    user_prompt = f"""Below are summaries of {len(articles)} news articles analyzed in batches.
Synthesize these into the Daily Tourism Intelligence Report.

{all_summaries}

---

Use today's date: {today}
Total articles analyzed: {len(articles)}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # If we have a ChromaDB collection, let the LLM enrich with historical context
    if collection:
        system_prompt += "\n\nYou also have access to search_knowledge_base to find historical articles for context.\n"
        messages[0]["content"] = system_prompt

        for iteration in range(1, max_iterations + 1):
            print(f"[REQ {request_id}] [{label}] Reduce iteration {iteration}/{max_iterations}")

            response = call_llm(
                client,
                messages,
                tools=REACT_TOOLS,
                request_id=request_id,
                label=label,
                token_limit=REDUCE_TOKEN_LIMIT,
            )
            if not response:
                return None

            tool_calls = extract_tool_calls(response)
            if not tool_calls:
                content = extract_content(response)
                if not content.strip():
                    print(f"[REQ {request_id}] [{label}] [WARNING] Empty reduce output; forcing direct final report retry")
                    retry_messages = list(messages)
                    retry_messages.append({
                        "role": "user",
                        "content": "Return the final complete report now in markdown. Do not call tools.",
                    })
                    retry_response = call_llm(
                        client,
                        retry_messages,
                        request_id=request_id,
                        label=label,
                        token_limit=max(REDUCE_TOKEN_LIMIT, 5200),
                    )
                    content = extract_content(retry_response) if retry_response else ""
                break

            # Process tool calls
            messages.append(response.choices[0].message)
            for tool_call in tool_calls:
                if tool_call.function.name == "search_knowledge_base":
                    try:
                        args = json.loads(tool_call.function.arguments)
                        query = args.get("query", "")
                    except Exception:
                        query = ""

                    print(f"[REQ {request_id}] [{label}] RAG search: '{query[:60]}'")
                    result = search_knowledge_base(collection, client, query, REACT_TOP_K, request_id) if query else "Error: empty query"
                    messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
                else:
                    messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": "Error: unknown tool"})
        else:
            # Max iterations reached, force final
            messages.append({"role": "user", "content": "Please produce the final report now."})
            response = call_llm(
                client,
                messages,
                request_id=request_id,
                label=label,
                token_limit=REDUCE_TOKEN_LIMIT,
            )
            content = extract_content(response) if response else ""
    else:
        # No RAG available — simple synthesis
        response = call_llm(
            client,
            messages,
            request_id=request_id,
            label=label,
            token_limit=REDUCE_TOKEN_LIMIT,
        )
        content = extract_content(response) if response else ""

    total_elapsed = (time.time() - total_started) * 1000
    print()
    print(f"[REQ {request_id}] [{label}] Report: {len(content)} chars")
    print(f"[REQ {request_id}] [{label}] Total time: {total_elapsed:.1f} ms")

    if not content.strip():
        return None

    # Strip any sources section the LLM may have added, validate, then append correct sources
    content = strip_llm_sources_section(content)
    validate_source_citations(content, len(articles), request_id)
    content += build_sources_section(articles)

    return content


# =============================================================================
# REACT STRATEGY 2 — TRIAGE
# =============================================================================

def generate_triage_report(client, articles, collection, max_iterations, request_id):
    """
    Strategy 2: LLM-Guided Triage.

    The LLM sees ALL article titles (lightweight) and picks which ones to read
    in full using a read_article tool. It can also search the knowledge base.

    PARAMETERS:
    - client: OpenAI/Azure client
    - articles: List of ALL recent article dicts
    - collection: ChromaDB collection (or None)
    - max_iterations: Max tool-use iterations
    - request_id: Correlation ID for logs

    RETURNS:
    - The report as a markdown string, or None if failed
    """
    label = "TRIAGE"
    total_started = time.time()

    print(f"[REQ {request_id}] [{label}] Starting triage over {len(articles)} articles")
    print(f"[REQ {request_id}] [{label}] Max iterations: {max_iterations}")

    # Step 1: Format all article titles (lightweight)
    titles_text = format_article_titles(articles)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    system_prompt = REPORT_SYSTEM_PROMPT.replace("{date}", today)

    system_prompt += f"""

ADDITIONAL INSTRUCTIONS FOR TRIAGE MODE:
You are shown the titles of {len(articles)} articles. You have two tools:
1. read_article(index) — Read the full content of a specific article by its number
2. search_knowledge_base(query) — Search historical articles for context

YOUR WORKFLOW:
1. Scan all the article titles below
2. Identify the most tourism-relevant articles
3. Use read_article to read the full content of the most important ones (aim for 10-20 articles)
4. Optionally use search_knowledge_base for historical context
5. When you have enough information, produce the final report

Be strategic — read the articles that matter most first.
"""

    user_prompt = f"""Here are today's {len(articles)} article titles:

{titles_text}

---

Scan these titles, then use read_article to read the most relevant ones in full.
When ready, produce the Daily Tourism Intelligence Report for {today}.
"""

    # Build tool list (read_article + optionally search_knowledge_base)
    tools = [READ_ARTICLE_TOOL]
    if collection:
        tools.append(REACT_TOOLS[0])

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    print(f"[REQ {request_id}] [{label}] Article titles: {len(titles_text)} chars")
    print(f"[REQ {request_id}] [{label}] Tools available: {[t['function']['name'] for t in tools]}")

    # Step 2: ReAct loop
    articles_read = 0

    for iteration in range(1, max_iterations + 1):
        print()
        print(f"[REQ {request_id}] [{label}] === Iteration {iteration}/{max_iterations} ===")

        response = call_llm(client, messages, tools=tools, request_id=request_id, label=label)
        if not response:
            return None

        tool_calls = extract_tool_calls(response)

        # If no tool calls, the model is done
        if not tool_calls:
            content = extract_content(response)
            print(f"[REQ {request_id}] [{label}] Articles read in full: {articles_read}")
            break

        # Process tool calls
        messages.append(response.choices[0].message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            call_id = tool_call.id

            if function_name == "read_article":
                try:
                    args = json.loads(tool_call.function.arguments)
                    index = args.get("index", 0)
                except Exception:
                    index = 0

                print(f"[REQ {request_id}] [{label}] Reading article #{index}")

                # Validate index (1-based)
                if 1 <= index <= len(articles):
                    article = articles[index - 1]
                    # Format the single article's full content
                    article_text = format_articles_for_prompt([article], max_chars_per_article=3000)
                    articles_read = articles_read + 1
                    messages.append({"role": "tool", "tool_call_id": call_id, "content": article_text})
                else:
                    messages.append({"role": "tool", "tool_call_id": call_id,
                                     "content": f"Error: invalid article index {index}. Valid range: 1 to {len(articles)}"})

            elif function_name == "search_knowledge_base" and collection:
                try:
                    args = json.loads(tool_call.function.arguments)
                    query = args.get("query", "")
                except Exception:
                    query = ""

                print(f"[REQ {request_id}] [{label}] RAG search: '{query[:60]}'")
                result = search_knowledge_base(collection, client, query, REACT_TOP_K, request_id) if query else "Error: empty query"
                messages.append({"role": "tool", "tool_call_id": call_id, "content": result})

            else:
                messages.append({"role": "tool", "tool_call_id": call_id, "content": f"Error: unknown tool '{function_name}'"})
    else:
        # Max iterations reached
        print(f"[REQ {request_id}] [{label}] Max iterations reached, forcing final report")
        messages.append({"role": "user", "content": "Please produce the final report now based on all articles read."})
        response = call_llm(client, messages, request_id=request_id, label=label)
        content = extract_content(response) if response else ""

    total_elapsed = (time.time() - total_started) * 1000
    print(f"[REQ {request_id}] [{label}] Report: {len(content)} chars")
    print(f"[REQ {request_id}] [{label}] Total time: {total_elapsed:.1f} ms")

    if not content.strip():
        return None

    # Strip any sources section the LLM may have added, validate, then append correct sources
    content = strip_llm_sources_section(content)
    validate_source_citations(content, len(articles), request_id)
    content += build_sources_section(articles)

    return content


# =============================================================================
# REACT STRATEGY 3 — HYBRID
# =============================================================================

TRIAGE_SCORING_PROMPT = """You are a tourism relevance scorer. For each article title below, assign a tourism relevance score from 1-5:
1 = Not related to tourism at all
2 = Tangentially related (e.g. general economy, weather)
3 = Somewhat related (e.g. travel industry, hospitality)
4 = Directly related (e.g. tourism policy, visitor numbers, destinations)
5 = Highly relevant (e.g. Portugal tourism specifically, major tourism events)

Return ONLY a JSON array of objects with "index" and "score" fields.
Example: [{"index": 1, "score": 5}, {"index": 2, "score": 1}, ...]

Score ALL articles. Return nothing else but the JSON array.
"""


def generate_hybrid_report(client, articles, collection, max_iterations, request_id):
    """
    Strategy 3: Two-Phase Hybrid.

    Phase 1: Score all articles for tourism relevance using lightweight triage.
    Phase 2: Feed filtered articles (score >= 3) into a ReAct loop.

    PARAMETERS:
    - client: OpenAI/Azure client
    - articles: List of ALL recent article dicts
    - collection: ChromaDB collection (or None)
    - max_iterations: Max ReAct iterations for phase 2
    - request_id: Correlation ID for logs

    RETURNS:
    - The report as a markdown string, or None if failed
    """
    label = "HYBRID"
    total_started = time.time()

    print(f"[REQ {request_id}] [{label}] Starting hybrid strategy over {len(articles)} articles")

    # =========================================================================
    # PHASE 1: TRIAGE — Score all articles for tourism relevance
    # =========================================================================

    print()
    print(f"[REQ {request_id}] [{label}] === Phase 1: Triage Scoring ===")

    titles_text = format_article_titles(articles)

    # Process in batches to handle large article sets
    TRIAGE_BATCH = 100
    all_scores = {}  # index -> score

    title_lines = titles_text.split("\n")
    for batch_start in range(0, len(title_lines), TRIAGE_BATCH):
        batch_end = min(batch_start + TRIAGE_BATCH, len(title_lines))
        batch_titles = "\n".join(title_lines[batch_start:batch_end])

        print(f"[REQ {request_id}] [{label}] Scoring articles {batch_start + 1}-{batch_end}")

        messages = [
            {"role": "system", "content": TRIAGE_SCORING_PROMPT},
            {"role": "user", "content": batch_titles},
        ]

        response = call_llm(client, messages, request_id=request_id, label=label)
        if not response:
            continue

        content = extract_content(response)

        # Parse JSON scores
        try:
            # Look for JSON array in the response (might have extra text)
            json_start = content.find("[")
            json_end = content.rfind("]") + 1
            if json_start >= 0 and json_end > json_start:
                scores_list = json.loads(content[json_start:json_end])
                for item in scores_list:
                    idx = item.get("index", 0)
                    score = item.get("score", 0)
                    all_scores[idx] = score
                print(f"[REQ {request_id}] [{label}] Parsed {len(scores_list)} scores")
        except Exception as e:
            print(f"[REQ {request_id}] [{label}] [WARNING] Failed to parse scores: {e}")

    # Filter articles with score >= 3
    filtered_articles = []
    for i, article in enumerate(articles, start=1):
        score = all_scores.get(i, 0)
        if score >= 3:
            filtered_articles.append(article)

    print()
    print(f"[REQ {request_id}] [{label}] Triage results:")
    print(f"[REQ {request_id}] [{label}]   Total scored: {len(all_scores)}")
    print(f"[REQ {request_id}] [{label}]   Passed filter (score >= 3): {len(filtered_articles)}")

    if not filtered_articles:
        print(f"[REQ {request_id}] [{label}] [WARNING] No articles passed triage. Using top 30 by recency.")
        filtered_articles = articles[:30]

    # Cap at a reasonable number for the ReAct phase
    MAX_FILTERED = 50
    if len(filtered_articles) > MAX_FILTERED:
        print(f"[REQ {request_id}] [{label}] Capping filtered articles to {MAX_FILTERED}")
        filtered_articles = filtered_articles[:MAX_FILTERED]

    # =========================================================================
    # PHASE 2: REACT — Deep dive on filtered articles
    # =========================================================================

    print()
    print(f"[REQ {request_id}] [{label}] === Phase 2: ReAct Deep Dive ({len(filtered_articles)} articles) ===")

    # Use the existing ReAct function with the filtered set
    report = generate_react_report(
        client, filtered_articles, collection,
        max_iterations, request_id
    )

    total_elapsed = (time.time() - total_started) * 1000
    print(f"[REQ {request_id}] [{label}] Total time (both phases): {total_elapsed:.1f} ms")

    return report


# =============================================================================
# REACT STRATEGY 4 — PROGRESSIVE
# =============================================================================

PROGRESSIVE_DRAFT_PROMPT = """You are a tourism intelligence analyst building a report progressively.

CRITICAL CITATION RULE:
Each article has a pre-assigned, globally unique source number (e.g., [Source 42]).
You MUST use the EXACT source numbers provided with each article.
Do NOT renumber or reassign source numbers when updating the draft.
These numbers are permanent identifiers that correspond to the final source list.
When merging new batch content into the existing draft, PRESERVE ALL existing source numbers.

Below is your CURRENT DRAFT REPORT (may be empty if this is the first batch):

{current_draft}

---

And here is a NEW BATCH of articles to incorporate:

{batch_text}

---

YOUR TASK:
1. Read the new batch of articles
2. Update your draft report by incorporating any new tourism-relevant insights
3. Maintain the exact report structure below
4. Add new information from this batch while keeping the best content from the previous draft
5. If the new batch has no tourism-relevant content, keep the draft unchanged
6. ALWAYS use the exact [Source N] numbers from the articles — NEVER renumber them
7. Do NOT add a Sources or References section at the end — this is generated automatically

OUTPUT the updated FULL report in this exact markdown structure:

# Daily Tourism Intelligence Report — {date}

## 1. Executive Summary
## 2. Key Themes & Trends
## 3. Notable Articles
## 4. Market Signals
## 5. Analyst Notes
"""


def generate_progressive_report(client, articles, collection, max_iterations, request_id):
    """
    Strategy 4: Progressive Accumulation.

    Feed articles in batches, each updating a running draft report.
    After all batches, optionally enrich with RAG.

    PARAMETERS:
    - client: OpenAI/Azure client
    - articles: List of ALL recent article dicts
    - collection: ChromaDB collection (or None)
    - max_iterations: Max ReAct iterations for final enrichment
    - request_id: Correlation ID for logs

    RETURNS:
    - The report as a markdown string, or None if failed
    """
    tuning = get_strategy_tuning(
        "progressive",
        default_batch_size=30,
        default_chars_per_article=1500,
        default_token_limit=3000,
    )
    BATCH_SIZE = tuning["batch_size"]
    BATCH_CHARS = tuning["chars_per_article"]
    TOKEN_LIMIT = tuning["token_limit"]
    label = "PROGRESSIVE"
    total_started = time.time()

    print(f"[REQ {request_id}] [{label}] Starting progressive over {len(articles)} articles")
    print(f"[REQ {request_id}] [{label}] Batch size: {BATCH_SIZE}")
    print(f"[REQ {request_id}] [{label}] Max chars/article: {BATCH_CHARS}")
    print(f"[REQ {request_id}] [{label}] Token limit/call: {TOKEN_LIMIT}")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Split articles into batches
    batches = []
    for i in range(0, len(articles), BATCH_SIZE):
        batches.append(articles[i : i + BATCH_SIZE])

    print(f"[REQ {request_id}] [{label}] Number of batches: {len(batches)}")

    # =========================================================================
    # PHASE 1: Progressive drafting
    # =========================================================================

    current_draft = "(empty — this is the first batch, create the initial report)"

    for batch_num, batch in enumerate(batches, start=1):
        print()
        print(f"[REQ {request_id}] [{label}] --- Batch {batch_num}/{len(batches)} ({len(batch)} articles) ---")

        batch_text = format_articles_for_prompt(
            batch,
            max_chars_per_article=BATCH_CHARS,
            start_index=(batch_num - 1) * BATCH_SIZE + 1,
        )

        prompt_text = PROGRESSIVE_DRAFT_PROMPT.replace("{current_draft}", current_draft)
        prompt_text = prompt_text.replace("{batch_text}", batch_text)
        prompt_text = prompt_text.replace("{date}", today)

        messages = [
            {"role": "user", "content": prompt_text},
        ]

        response = call_llm(
            client,
            messages,
            request_id=request_id,
            label=label,
            token_limit=TOKEN_LIMIT,
        )
        if not response:
            print(f"[REQ {request_id}] [{label}] [WARNING] Batch {batch_num} failed, keeping current draft")
            continue

        content = extract_content(response)
        if content.strip():
            current_draft = content
            print(f"[REQ {request_id}] [{label}] Draft updated: {len(current_draft)} chars")

    # =========================================================================
    # PHASE 2: Optional RAG enrichment
    # =========================================================================

    if collection and max_iterations > 0:
        print()
        print(f"[REQ {request_id}] [{label}] === RAG Enrichment Phase ===")

        system_prompt = REPORT_SYSTEM_PROMPT.replace("{date}", today)
        system_prompt += "\n\nYou have access to search_knowledge_base to find historical articles for context. Enrich the report with historical context if useful.\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the current draft report built from {len(articles)} articles:\n\n{current_draft}\n\nPlease enhance this report with historical context using the search_knowledge_base tool if useful, then produce the final version."},
        ]

        for iteration in range(1, max_iterations + 1):
            print(f"[REQ {request_id}] [{label}] Enrichment iteration {iteration}/{max_iterations}")

            response = call_llm(
                client,
                messages,
                tools=REACT_TOOLS,
                request_id=request_id,
                label=label,
                token_limit=TOKEN_LIMIT,
            )
            if not response:
                break

            tool_calls = extract_tool_calls(response)
            if not tool_calls:
                enriched = extract_content(response)
                if enriched.strip():
                    current_draft = enriched
                break

            # Process tool calls
            messages.append(response.choices[0].message)
            for tool_call in tool_calls:
                if tool_call.function.name == "search_knowledge_base":
                    try:
                        args = json.loads(tool_call.function.arguments)
                        query = args.get("query", "")
                    except Exception:
                        query = ""

                    print(f"[REQ {request_id}] [{label}] RAG search: '{query[:60]}'")
                    result = search_knowledge_base(collection, client, query, REACT_TOP_K, request_id) if query else "Error: empty query"
                    messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
                else:
                    messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": "Error: unknown tool"})
        else:
            # Max iterations, force final
            messages.append({"role": "user", "content": "Please produce the final report now."})
            response = call_llm(
                client,
                messages,
                request_id=request_id,
                label=label,
                token_limit=TOKEN_LIMIT,
            )
            if response:
                enriched = extract_content(response)
                if enriched.strip():
                    current_draft = enriched

    total_elapsed = (time.time() - total_started) * 1000
    print()
    print(f"[REQ {request_id}] [{label}] Final report: {len(current_draft)} chars")
    print(f"[REQ {request_id}] [{label}] Total time: {total_elapsed:.1f} ms")

    if not current_draft.strip():
        return None

    # Strip any sources section the LLM may have added, validate, then append correct sources
    current_draft = strip_llm_sources_section(current_draft)
    validate_source_citations(current_draft, len(articles), request_id)
    current_draft += build_sources_section(articles)

    return current_draft


# =============================================================================
# REPORT SAVING
# =============================================================================

def save_report(report_content, mode, strategy="", model="", provider="", hours=24, max_iterations=3):
    """
    Save a report to data/reports/ as a markdown file.

    Filename encodes all generation parameters for easy identification:
    DATE_MODE-STRATEGY_MODEL_PROVIDER_HhNi_HHMMSS.md

    Example: 2026-02-19_react-triage_gpt5_azure_24h3i_001304.md

    PARAMETERS:
    - report_content: The markdown report string
    - mode: "simple" or "react"
    - strategy: Strategy name (used for react mode)
    - model: LLM model name
    - provider: LLM provider (azure/openai)
    - hours: Look-back window in hours
    - max_iterations: Max ReAct iterations

    RETURNS:
    - The filename of the saved report
    """
    # Create reports directory if needed
    os.makedirs(REPORTS_DIR, exist_ok=True)

    # Build the filename parts
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    timestamp = datetime.now(timezone.utc).strftime("%H%M%S")

    # Mode + strategy
    if strategy and mode == "react":
        mode_part = f"{mode}-{strategy}"
    else:
        mode_part = mode

    # Shorten model name for filename (e.g. "gpt-5" -> "gpt5", "chatgpt-o4-mini" -> "o4mini")
    model_short = (model or "unknown").lower()
    model_short = model_short.replace("chatgpt-", "").replace("gpt-", "gpt").replace("-", "")

    # Provider
    prov = (provider or "unknown").lower()

    # Hours and iterations
    params_part = f"{int(hours)}h{int(max_iterations)}i"

    filename = f"{today}_{mode_part}_{model_short}_{prov}_{params_part}_{timestamp}.md"
    filepath = os.path.join(REPORTS_DIR, filename)

    # Save the file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"[INFO] Report saved to: {filepath}")
    print(f"[INFO] Report size: {len(report_content)} chars")

    return filename


# =============================================================================
# WEB INTERFACE — HTML TEMPLATES
# =============================================================================


HTML_INDEX = """
<!DOCTYPE html>
<html>
<head>
    <title>Tourism Reports</title>
    <style>
        :root {
            --bg: #f5f5f5;
            --bg-card: #ffffff;
            --text: #333333;
            --text-muted: #555555;
            --text-dim: #999999;
            --heading: #2c3e50;
            --accent: #3498db;
            --accent-hover: #2980b9;
            --border: #ddd;
            --shadow: rgba(0,0,0,0.1);
            --shadow-sm: rgba(0,0,0,0.08);
            --input-bg: #ffffff;
            --input-text: #333333;
        }
        [data-theme="dark"] {
            --bg: #1a1a2e;
            --bg-card: #16213e;
            --text: #e0e0e0;
            --text-muted: #b0b0b0;
            --text-dim: #888888;
            --heading: #e0e0e0;
            --accent: #4fc3f7;
            --accent-hover: #29b6f6;
            --border: #2a2a4a;
            --shadow: rgba(0,0,0,0.3);
            --shadow-sm: rgba(0,0,0,0.2);
            --input-bg: #1a1a2e;
            --input-text: #e0e0e0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: var(--bg);
            color: var(--text);
            transition: background 0.3s, color 0.3s;
        }
        h1 {
            color: var(--heading);
            border-bottom: 3px solid var(--accent);
            padding-bottom: 10px;
        }
        h2 { color: var(--heading); }
        .theme-toggle {
            position: fixed;
            top: 16px;
            right: 20px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 6px 14px;
            cursor: pointer;
            font-size: 18px;
            box-shadow: 0 2px 8px var(--shadow-sm);
            z-index: 100;
            transition: background 0.3s;
        }
        .theme-toggle:hover { opacity: 0.8; }
        .generate-form {
            background: var(--bg-card);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px var(--shadow);
            margin-bottom: 30px;
        }
        .generate-form h2 {
            margin-top: 0;
            color: var(--heading);
        }
        .form-row {
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        .form-row label {
            font-weight: bold;
            color: var(--text-muted);
        }
        .form-row select, .form-row input {
            padding: 8px 12px;
            border: 1px solid var(--border);
            border-radius: 5px;
            font-size: 14px;
            background: var(--input-bg);
            color: var(--input-text);
        }
        .btn {
            padding: 10px 25px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            color: white;
        }
        .btn-primary { background: var(--accent); }
        .btn-primary:hover { background: var(--accent-hover); }
        .report-list {
            list-style: none;
            padding: 0;
        }
        .report-item {
            background: var(--bg-card);
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 10px;
            box-shadow: 0 1px 5px var(--shadow-sm);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .report-item a {
            color: var(--accent);
            text-decoration: none;
            font-weight: bold;
            font-size: 16px;
        }
        .report-item a:hover {
            text-decoration: underline;
        }
        .badge {
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .badge-simple { background: #e8f5e9; color: #2e7d32; }
        .badge-react { background: #e3f2fd; color: #1565c0; }
        .badge-map-reduce { background: #fff3e0; color: #e65100; }
        .badge-triage { background: #f3e5f5; color: #6a1b9a; }
        .badge-hybrid { background: #e0f7fa; color: #00695c; }
        .badge-progressive { background: #fce4ec; color: #b71c1c; }
        [data-theme="dark"] .badge-simple { background: #1b5e20; color: #a5d6a7; }
        [data-theme="dark"] .badge-react { background: #0d47a1; color: #90caf9; }
        [data-theme="dark"] .badge-map-reduce { background: #bf360c; color: #ffcc80; }
        [data-theme="dark"] .badge-triage { background: #4a148c; color: #ce93d8; }
        [data-theme="dark"] .badge-hybrid { background: #004d40; color: #80cbc4; }
        [data-theme="dark"] .badge-progressive { background: #880e4f; color: #f48fb1; }
        .empty-state {
            text-align: center;
            padding: 40px;
            color: var(--text-dim);
            font-style: italic;
        }
        .status-msg {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .status-success { background: #e8f5e9; border-left: 4px solid #4caf50; }
        .status-error { background: #ffebee; border-left: 4px solid #f44336; }
        .status-info { background: #e3f2fd; border-left: 4px solid #2196f3; }
        [data-theme="dark"] .status-success { background: #1b5e20; color: #c8e6c9; }
        [data-theme="dark"] .status-error { background: #b71c1c; color: #ffcdd2; }
        [data-theme="dark"] .status-info { background: #0d47a1; color: #bbdefb; }
        .hint { margin-top: 8px; font-size: 12px; color: var(--text-dim); }
    </style>
</head>
<body>
    <button class="theme-toggle" onclick="toggleTheme()" title="Toggle dark mode">🌓</button>

    <h1>🌍 Tourism Intelligence Reports</h1>

    {% if status_message %}
    <div class="status-msg status-{{ status_type or 'info' }}">
        {{ status_message }}
    </div>
    {% endif %}

    <div class="generate-form">
        <h2>Generate New Report</h2>
        <form method="POST" action="/generate">
            <div class="form-row">
                <label>Mode:</label>
                <select name="mode">
                    <option value="simple">Simple (single-pass)</option>
                    <option value="react">ReAct (iterative with RAG)</option>
                </select>
                <label>Strategy:</label>
                <select name="strategy">
                    <option value="basic">Basic (capped articles + RAG)</option>
                    <option value="map-reduce">Map-Reduce (batch summaries)</option>
                    <option value="triage">Triage (LLM picks articles)</option>
                    <option value="hybrid">Hybrid (score + deep dive)</option>
                    <option value="progressive">Progressive (rolling draft)</option>
                </select>
                <label>Hours:</label>
                <input type="number" name="hours" value="24" min="1" max="720" style="width:60px">
                <label>Max Iterations:</label>
                <input type="number" name="max_iterations" value="3" min="1" max="10" style="width:60px">
                <button type="submit" class="btn btn-primary">Generate Report</button>
            </div>
            <div class="hint">Strategy only applies to ReAct mode. Simple mode ignores it.</div>
        </form>
    </div>

    <h2>📄 Existing Reports</h2>
    {% if reports %}
    <ul class="report-list">
        {% for report in reports %}
        <li class="report-item">
            <a href="/report/{{ report.filename }}">{{ report.filename }}</a>
            <span class="badge badge-{{ report.strategy or report.mode }}">{{ report.label }}</span>
        </li>
        {% endfor %}
    </ul>
    {% else %}
    <div class="empty-state">
        No reports generated yet. Use the form above to create one!
    </div>
    {% endif %}

    <script>
    function toggleTheme() {
        var html = document.documentElement;
        var current = html.getAttribute('data-theme');
        var next = current === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
    }
    (function() {
        var saved = localStorage.getItem('theme');
        if (saved === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else if (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute('data-theme', 'dark');
        }
    })();
    </script>
</body>
</html>
"""


HTML_REPORT = r"""
<!DOCTYPE html>
<html>
<head>
    <title>{{ filename }} — Tourism Report</title>
    <style>
        :root {
            --bg: #f5f5f5;
            --bg-card: #ffffff;
            --text: #333333;
            --heading: #2c3e50;
            --heading-sub: #34495e;
            --accent: #3498db;
            --border: #eee;
            --shadow: rgba(0,0,0,0.1);
            --code-bg: #f0f0f0;
            --blockquote-border: #3498db;
            --blockquote-bg: rgba(52,152,219,0.05);
            --table-stripe: rgba(0,0,0,0.03);
            --hr-color: #ddd;
        }
        [data-theme="dark"] {
            --bg: #1a1a2e;
            --bg-card: #16213e;
            --text: #e0e0e0;
            --heading: #e0e0e0;
            --heading-sub: #b0bec5;
            --accent: #4fc3f7;
            --border: #2a2a4a;
            --shadow: rgba(0,0,0,0.3);
            --code-bg: #0f3460;
            --blockquote-border: #4fc3f7;
            --blockquote-bg: rgba(79,195,247,0.08);
            --table-stripe: rgba(255,255,255,0.04);
            --hr-color: #2a2a4a;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: var(--bg);
            color: var(--text);
            transition: background 0.3s, color 0.3s;
        }
        .nav {
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .nav a {
            color: var(--accent);
            text-decoration: none;
            font-size: 14px;
        }
        .nav a:hover {
            text-decoration: underline;
        }
        .theme-toggle {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 6px 14px;
            cursor: pointer;
            font-size: 18px;
            box-shadow: 0 2px 8px var(--shadow);
            transition: background 0.3s;
        }
        .theme-toggle:hover { opacity: 0.8; }
        .report-container {
            background: var(--bg-card);
            padding: 30px 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px var(--shadow);
            line-height: 1.7;
            font-size: 15px;
        }
        /* Rendered markdown typography */
        .report-container h1 {
            color: var(--heading);
            border-bottom: 3px solid var(--accent);
            padding-bottom: 10px;
            margin-top: 0;
        }
        .report-container h2 {
            color: var(--heading-sub);
            margin-top: 30px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 5px;
        }
        .report-container h3 {
            color: var(--heading-sub);
            margin-top: 24px;
        }
        .report-container p {
            margin: 12px 0;
        }
        .report-container ul, .report-container ol {
            padding-left: 24px;
            margin: 12px 0;
        }
        .report-container li {
            margin-bottom: 6px;
        }
        .report-container strong {
            color: var(--heading);
        }
        .report-container a {
            color: var(--accent);
            text-decoration: none;
        }
        .report-container a:hover {
            text-decoration: underline;
        }
        .report-container blockquote {
            border-left: 4px solid var(--blockquote-border);
            background: var(--blockquote-bg);
            margin: 16px 0;
            padding: 12px 20px;
            border-radius: 0 6px 6px 0;
        }
        .report-container code {
            background: var(--code-bg);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 13px;
            font-family: 'SF Mono', Monaco, Menlo, Consolas, monospace;
        }
        .report-container pre {
            background: var(--code-bg);
            padding: 16px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 13px;
        }
        .report-container pre code {
            padding: 0;
            background: none;
        }
        .report-container table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
        }
        .report-container th, .report-container td {
            padding: 10px 14px;
            border: 1px solid var(--border);
            text-align: left;
        }
        .report-container th {
            background: var(--code-bg);
            font-weight: 600;
        }
        .report-container tr:nth-child(even) {
            background: var(--table-stripe);
        }
        .report-container hr {
            border: none;
            border-top: 1px solid var(--hr-color);
            margin: 24px 0;
        }
        .report-container img {
            max-width: 100%;
            border-radius: 8px;
        }
        /* Stats widget */
        .stats-widget {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 6px var(--shadow);
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
            font-size: 13px;
        }
        .stats-widget .stat-label {
            color: var(--text);
            opacity: 0.5;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .stats-widget .stat-pill {
            background: var(--code-bg);
            color: var(--text);
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        .stats-widget .stat-pill .stat-icon {
            font-size: 14px;
        }
        .stats-widget .stat-divider {
            width: 1px;
            height: 20px;
            background: var(--border);
        }
    </style>
</head>
<body>
    <div class="nav">
        <a href="/">← Back to all reports</a>
        <button class="theme-toggle" onclick="toggleTheme()" title="Toggle dark mode">🌓</button>
    </div>

    {% if meta and (meta.model or meta.provider) %}
    <div class="stats-widget">
        <span class="stat-label">Report Parameters</span>
        <span class="stat-divider"></span>
        {% if meta.mode %}
        <span class="stat-pill"><span class="stat-icon">📋</span> {{ meta.mode }}{% if meta.strategy %} ({{ meta.strategy }}){% endif %}</span>
        {% endif %}
        {% if meta.model %}
        <span class="stat-pill"><span class="stat-icon">🤖</span> {{ meta.model }}</span>
        {% endif %}
        {% if meta.provider %}
        <span class="stat-pill"><span class="stat-icon">☁️</span> {{ meta.provider }}</span>
        {% endif %}
        {% if meta.hours %}
        <span class="stat-pill"><span class="stat-icon">🕐</span> {{ meta.hours }}h window</span>
        {% endif %}
        {% if meta.iterations %}
        <span class="stat-pill"><span class="stat-icon">🔄</span> {{ meta.iterations }} iterations</span>
        {% endif %}
        {% if meta.date %}
        <span class="stat-pill"><span class="stat-icon">📅</span> {{ meta.date }}</span>
        {% endif %}
    </div>
    {% endif %}

    <div class="report-container" id="report-output">
        <p style="color: var(--text); opacity: 0.5;">Rendering report...</p>
    </div>

    <!-- Raw markdown stored here, rendered by marked.js -->
    <script id="raw-markdown" type="text/plain">{{ content }}</script>

    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
    // Render markdown
    (function() {
        var raw = document.getElementById('raw-markdown').textContent;
        var output = document.getElementById('report-output');
        if (typeof marked !== 'undefined') {
            output.innerHTML = marked.parse(raw);
        } else {
            // Fallback if CDN fails: show raw text
            output.innerHTML = '<pre>' + raw + '</pre>';
        }

        // Post-process: show only cited sources in the rendered Sources section.
        // The full list stays in the .md file for reproducibility.
        try {
            // 1. Find all [Source N] citations in the report body
            var citedNums = new Set();
            var bodyText = output.innerHTML;
            var citationPattern = /\[Source[s]?\s*([^\]]+)\]/gi;
            var match;
            while ((match = citationPattern.exec(bodyText)) !== null) {
                var nums = match[1].match(/\d+/g);
                if (nums) { nums.forEach(function(n) { citedNums.add(parseInt(n)); }); }
            }

            // 2. Find the Sources <h2> and its following <ol>
            var headings = output.querySelectorAll('h2');
            var sourcesHeading = null;
            for (var i = 0; i < headings.length; i++) {
                if (headings[i].textContent.trim() === 'Sources') {
                    sourcesHeading = headings[i];
                    break;
                }
            }

            if (sourcesHeading && citedNums.size > 0) {
                var ol = sourcesHeading.nextElementSibling;
                if (ol && ol.tagName === 'OL') {
                    var items = ol.querySelectorAll('li');
                    var totalSources = items.length;
                    var startNum = parseInt(ol.getAttribute('start')) || 1;

                    // Build a new container with only the cited sources
                    var newContainer = document.createElement('div');
                    newContainer.className = 'filtered-sources';

                    // Add a count label
                    var countLabel = document.createElement('p');
                    countLabel.style.cssText = 'font-size:13px;color:var(--text);opacity:0.5;margin-bottom:12px;';
                    countLabel.textContent = citedNums.size + ' of ' + totalSources + ' sources cited in this report';
                    newContainer.appendChild(countLabel);

                    // Keep only cited items, with their original source number
                    for (var j = 0; j < items.length; j++) {
                        var sourceNum = startNum + j;
                        if (citedNums.has(sourceNum)) {
                            var entry = document.createElement('p');
                            entry.style.margin = '6px 0';
                            entry.innerHTML = '<strong>' + sourceNum + '.</strong> ' + items[j].innerHTML;
                            newContainer.appendChild(entry);
                        }
                    }

                    // Replace the original <ol> with the filtered container
                    ol.parentNode.replaceChild(newContainer, ol);
                }
            }
        } catch(e) {
            // If post-processing fails, just show the full list
            console.warn('Source filtering failed:', e);
        }
    })();

    // Dark mode toggle
    function toggleTheme() {
        var html = document.documentElement;
        var current = html.getAttribute('data-theme');
        var next = current === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
    }
    (function() {
        var saved = localStorage.getItem('theme');
        if (saved === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else if (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute('data-theme', 'dark');
        }
    })();
    </script>
</body>
</html>
"""


# =============================================================================
# WEB INTERFACE — FLASK APP
# =============================================================================

# Create Flask app
app = Flask(__name__)

# Initialize clients (done once at startup)
openai_client = None
chroma_collection = None


def list_reports():
    """
    List all report files in data/reports/, sorted newest first.

    Parses metadata from filename. Supports both new format:
        2026-02-19_react-triage_gpt5_azure_24h3i_001304.md
    and legacy format:
        2026-02-18_simple_103000.md
        2026-02-18_react-triage_103000.md

    RETURNS:
    - A list of dicts with filename, mode, strategy, model, provider, etc.
    """
    if not os.path.exists(REPORTS_DIR):
        return []

    report_files = glob.glob(os.path.join(REPORTS_DIR, "*.md"))
    reports = []

    for filepath in report_files:
        filename = os.path.basename(filepath)
        name_no_ext = filename.rsplit(".", 1)[0]

        # Split by underscore — parts vary by format
        parts = name_no_ext.split("_")

        mode = "unknown"
        strategy = ""
        model = ""
        provider = ""
        hours = ""
        iterations = ""

        if len(parts) >= 2:
            # parts[0] = date, parts[1] = mode(-strategy)
            mode_strategy = parts[1]

            if mode_strategy.startswith("react-"):
                mode = "react"
                strategy = mode_strategy.replace("react-", "")
            elif mode_strategy == "react":
                mode = "react"
                strategy = "basic"
            elif mode_strategy == "simple":
                mode = "simple"

        # New format has 6 parts: date, mode-strategy, model, provider, NhNi, HHMMSS
        if len(parts) >= 6:
            model = parts[2]
            provider = parts[3]
            params_part = parts[4]  # e.g. "24h3i"
            # Parse hours and iterations
            m = re.match(r"(\d+)h(\d+)i", params_part)
            if m:
                hours = m.group(1)
                iterations = m.group(2)

        # Build a display label
        if strategy:
            label = f"{mode} ({strategy})"
        else:
            label = mode

        reports.append({
            "filename": filename,
            "mode": mode,
            "strategy": strategy,
            "model": model,
            "provider": provider,
            "hours": hours,
            "iterations": iterations,
            "label": label,
        })

    # Sort by filename (which starts with date), newest first
    reports.sort(key=lambda r: r["filename"], reverse=True)

    return reports


@app.route("/", methods=["GET"])
def index():
    """
    Index page: lists all reports and shows the generate form.
    """
    reports = list_reports()

    # Check for status messages from redirects
    status_message = request.args.get("msg", None)
    status_type = request.args.get("type", "info")

    return render_template_string(
        HTML_INDEX,
        reports=reports,
        status_message=status_message,
        status_type=status_type,
    )


@app.route("/report/<filename>", methods=["GET"])
def view_report(filename):
    """
    View a single report rendered from its markdown file.
    Parses metadata from the filename for the stats widget.
    """
    filepath = os.path.join(REPORTS_DIR, filename)

    if not os.path.exists(filepath):
        return "Report not found", 404

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse metadata from filename
    name_no_ext = filename.rsplit(".", 1)[0]
    parts = name_no_ext.split("_")

    meta = {
        "date": parts[0] if len(parts) >= 1 else "",
        "mode": "",
        "strategy": "",
        "model": "",
        "provider": "",
        "hours": "",
        "iterations": "",
    }

    if len(parts) >= 2:
        ms = parts[1]
        if ms.startswith("react-"):
            meta["mode"] = "react"
            meta["strategy"] = ms.replace("react-", "")
        elif ms == "react":
            meta["mode"] = "react"
            meta["strategy"] = "basic"
        else:
            meta["mode"] = ms

    if len(parts) >= 6:
        meta["model"] = parts[2]
        meta["provider"] = parts[3]
        m = re.match(r"(\d+)h(\d+)i", parts[4])
        if m:
            meta["hours"] = m.group(1)
            meta["iterations"] = m.group(2)

    return render_template_string(
        HTML_REPORT,
        filename=filename,
        content=content,
        meta=meta,
    )


@app.route("/generate", methods=["POST"])
def generate():
    """
    Generate a new report from the web interface.
    """
    global openai_client, chroma_collection

    mode = request.form.get("mode", "simple")
    strategy = request.form.get("strategy", "basic")
    hours = int(request.form.get("hours", 24))
    max_iterations = int(request.form.get("max_iterations", 3))

    request_id = build_request_id()

    print()
    print("=" * 60)
    print(f"[REQ {request_id}] [WEB] Generate report: mode={mode}, strategy={strategy}, hours={hours}")
    print("=" * 60)

    # Step 1: Load articles
    articles = load_recent_articles(hours=hours)

    if not articles:
        msg = f"No articles found in the last {hours} hours. Try increasing the hours parameter."
        return redirect(f"/?msg={msg}&type=error")

    # Step 2: Generate report
    report = None

    if mode == "react":
        # Load ChromaDB if not already loaded
        if chroma_collection is None:
            try:
                chroma_collection = get_chromadb_collection()
            except SystemExit:
                msg = "Vector database not found. Run the embedder first, or use simple mode."
                return redirect(f"/?msg={msg}&type=error")

        # Dispatch to the right strategy
        if strategy == "map-reduce":
            report = generate_map_reduce_report(openai_client, articles, chroma_collection, max_iterations, request_id)
        elif strategy == "triage":
            report = generate_triage_report(openai_client, articles, chroma_collection, max_iterations, request_id)
        elif strategy == "hybrid":
            report = generate_hybrid_report(openai_client, articles, chroma_collection, max_iterations, request_id)
        elif strategy == "progressive":
            report = generate_progressive_report(openai_client, articles, chroma_collection, max_iterations, request_id)
        else:
            # basic strategy
            report = generate_react_report(openai_client, articles, chroma_collection, max_iterations, request_id)
    else:
        report = generate_simple_report(openai_client, articles, request_id)

    if not report:
        msg = "Report generation failed. Check the server logs for details."
        return redirect(f"/?msg={msg}&type=error")

    # Step 3: Save
    filename = save_report(
        report, mode,
        strategy=strategy if mode == "react" else "",
        model=APP_CONFIG.get("llm_model", ""),
        provider=APP_CONFIG.get("provider", ""),
        hours=hours,
        max_iterations=max_iterations,
    )

    msg = f"Report generated successfully: {filename}"
    return redirect(f"/?msg={msg}&type=success")


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """
    Main function that runs the report generator.
    """
    global openai_client, chroma_collection, APP_CONFIG

    # Step 1: Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Portuguese Tourism - Daily Report Generator"
    )

    parser.add_argument(
        "--mode",
        choices=["simple", "react"],
        default="simple",
        help="Generation mode: simple (single-pass) or react (iterative with RAG)"
    )

    parser.add_argument(
        "--strategy",
        choices=["basic", "map-reduce", "triage", "hybrid", "progressive"],
        default="basic",
        help="ReAct strategy (only used with --mode react)"
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Max iterations for ReAct mode (default: 3)"
    )

    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Look-back window for recent articles in hours (default: 24)"
    )

    parser.add_argument(
        "--provider",
        choices=["auto", "openai", "azure"],
        default=None,
        help="Provider selection (default: LLM_PROVIDER/auto)"
    )

    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start web viewer after generating a report"
    )

    parser.add_argument(
        "--web-only",
        action="store_true",
        help="Only start the web viewer, skip report generation"
    )

    parser.add_argument(
        "--cap",
        type=int,
        default=None,
        help="Cap the number of articles to process (default: no limit, use all)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("TOURISM REPORT GENERATOR - Starting")
    print("=" * 60)
    print()

    # Step 2: Resolve provider and build client
    provider = resolve_provider(args.provider)
    llm_model, embedding_model = get_model_names(provider)

    print(f"[INFO] Provider: {provider}")
    print(f"[INFO] LLM model: {llm_model}")
    print(f"[INFO] Embedding model: {embedding_model}")

    print("[INFO] Initializing LLM client...")
    openai_client, endpoint_host, api_version, raw_api_key = build_llm_client(provider)

    APP_CONFIG = {
        "provider": provider,
        "llm_model": llm_model,
        "embedding_model": embedding_model,
        "endpoint_host": endpoint_host,
        "api_key_prefix": mask_api_key(raw_api_key),
    }

    print(f"[INFO] Endpoint: {endpoint_host}")
    print(f"[INFO] API key: {APP_CONFIG['api_key_prefix']}")
    print()

    # Step 3: If web-only, skip generation
    if args.web_only:
        print("[INFO] Web-only mode — skipping report generation")
        print()

        # Load ChromaDB collection if available (for generate via web form)
        try:
            chroma_collection = get_chromadb_collection()
            print("[INFO] Vector database loaded (ReAct mode available via web form)")
        except SystemExit:
            print("[INFO] Vector database not found (ReAct mode unavailable via web form)")
            chroma_collection = None

        print()
        print("[INFO] Starting web server...")
        print()
        print("=" * 60)
        print("Open in your browser: http://localhost:9998")
        print("=" * 60)
        print()
        print("Press Ctrl+C to stop the server")
        print()

        app.run(host="0.0.0.0", port=9998, debug=False)
        return

    # Step 4: Load recent articles
    print()
    articles = load_recent_articles(hours=args.hours)

    # Apply optional cap for testing
    if args.cap and len(articles) > args.cap:
        print(f"[INFO] Capping articles from {len(articles)} to {args.cap} (--cap)")
        articles = articles[:args.cap]

    print()

    if not articles:
        print(f"[WARNING] No articles found in the last {args.hours} hours.")
        print("[WARNING] Try increasing --hours or check if data/articles/ has recent files.")
        print()

        if args.serve:
            print("[INFO] Starting web viewer anyway...")
            print()
            print("=" * 60)
            print("Open in your browser: http://localhost:9998")
            print("=" * 60)
            print()
            app.run(host="0.0.0.0", port=9998, debug=False)
        return

    # Log some article titles
    print("[INFO] Sample articles loaded:")
    for i, article in enumerate(articles[:5], start=1):
        meta = article.get("metadata", {})
        title = meta.get("title", "Untitled")
        source = meta.get("source", "Unknown")
        print(f"  [{i}] [{source}] {title[:70]}")
    if len(articles) > 5:
        print(f"  ... and {len(articles) - 5} more")
    print()

    # Step 5: Generate the report
    request_id = build_request_id()
    strategy = args.strategy

    if args.mode == "react":
        print(f"[INFO] Mode: REACT (strategy: {strategy})")
        print(f"[INFO] Max iterations: {args.max_iterations}")
        print()

        # Load ChromaDB for ReAct mode. For map-reduce/progressive we can
        # continue without RAG if the vector DB is unavailable.
        try:
            chroma_collection = get_chromadb_collection()
            print(f"[INFO] Vector database loaded from {CHROMA_DIR}")
            print()
        except SystemExit:
            if strategy in {"map-reduce", "progressive"}:
                print(f"[WARNING] Vector database unavailable at {CHROMA_DIR}; continuing without RAG enrichment.")
                print()
                chroma_collection = None
            else:
                raise
        except Exception as e:
            if strategy in {"map-reduce", "progressive"}:
                print(f"[WARNING] Could not open vector database ({e}); continuing without RAG enrichment.")
                print()
                chroma_collection = None
            else:
                raise

        # Dispatch to the right strategy function
        if strategy == "map-reduce":
            report = generate_map_reduce_report(
                openai_client, articles, chroma_collection,
                args.max_iterations, request_id
            )
        elif strategy == "triage":
            report = generate_triage_report(
                openai_client, articles, chroma_collection,
                args.max_iterations, request_id
            )
        elif strategy == "hybrid":
            report = generate_hybrid_report(
                openai_client, articles, chroma_collection,
                args.max_iterations, request_id
            )
        elif strategy == "progressive":
            report = generate_progressive_report(
                openai_client, articles, chroma_collection,
                args.max_iterations, request_id
            )
        else:
            # basic strategy
            report = generate_react_report(
                openai_client, articles, chroma_collection,
                args.max_iterations, request_id
            )
    else:
        print("[INFO] Mode: SIMPLE (single-pass)")
        print()
        strategy = ""  # no strategy for simple mode

        report = generate_simple_report(openai_client, articles, request_id)

    # Step 6: Save the report
    print()
    if report:
        filename = save_report(
            report, args.mode, strategy,
            model=APP_CONFIG.get("llm_model", ""),
            provider=APP_CONFIG.get("provider", ""),
            hours=args.hours,
            max_iterations=args.max_iterations,
        )
        print()
        print("=" * 60)
        print(f"REPORT GENERATED: {filename}")
        print("=" * 60)
    else:
        print("[ERROR] Report generation failed!")
        print()

    # Step 7: Optionally start web viewer
    if args.serve:
        # Load ChromaDB for web form if not already loaded
        if chroma_collection is None:
            try:
                chroma_collection = get_chromadb_collection()
            except SystemExit:
                chroma_collection = None

        print()
        print("[INFO] Starting web server...")
        print()
        print("=" * 60)
        print("Open in your browser: http://localhost:9998")
        print("=" * 60)
        print()
        print("Press Ctrl+C to stop the server")
        print()

        app.run(host="0.0.0.0", port=9998, debug=False)


# =============================================================================
# RUN THE SCRIPT
# =============================================================================

if __name__ == "__main__":
    main()
