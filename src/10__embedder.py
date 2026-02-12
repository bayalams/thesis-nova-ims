"""
10__embedder.py - Step 10: Document Embedder
=============================================

This script processes all our collected documents and creates embeddings.

WHAT IT DOES:
1. Loads all documents from data/articles/ and data/wiki/
2. Chunks long documents into smaller pieces
3. Creates embeddings using OpenAI API
4. Stores everything in ChromaDB (local vector database)

HOW TO RUN:
    # First, set your OpenAI API key
    export OPENAI_API_KEY="your_api_key_here"
    
    # Then run the embedder
    python 10__embedder.py

WHAT IS AN EMBEDDING?
    - An embedding is a list of numbers that represents the "meaning" of text
    - Similar texts have similar embeddings
    - We use embeddings to find documents related to a question

WHAT IS CHROMADB?
    - ChromaDB is a simple local vector database
    - It stores embeddings and lets us search for similar ones
    - No external server needed - everything is stored in a folder
"""

# =============================================================================
# IMPORTS
# =============================================================================

import json        # Built-in library to work with JSON data
import os          # Built-in library to work with files and folders
from datetime import datetime  # Built-in library to work with dates and times
from pathlib import Path       # Built-in library for file path handling
import re

# External libraries (install with pip)
import chromadb                # Vector database (pip install chromadb)
from openai import OpenAI, AzureOpenAI

# =============================================================================
# CONFIGURATION
# =============================================================================

# Input directories (where our documents are)
NEWS_DIR = "data/articles"
WIKI_DIR = "data/wiki"

# Output directory for ChromaDB
CHROMA_DIR = os.environ.get("CHROMA_DIR", "data/vectordb")

# Collection name in ChromaDB
COLLECTION_NAME = "tourism_knowledge"

# Runtime-selected provider/model (set in main)
PROVIDER = None
EMBEDDING_MODEL = None
EMBEDDING_DIMS = None  # Optional dimension override (e.g. 1536 for reduced 3-large)

# Maximum chunk size (in characters)
# OpenAI recommends chunks of ~500-1000 tokens
# We use 2000 characters which is roughly 500 tokens
MAX_CHUNK_SIZE = 2000

# Overlap between chunks (to keep context)
CHUNK_OVERLAP = 200

# Maximum content length (in characters)
# Documents larger than this will be skipped (likely spam or scraping errors)
# 200,000 chars ≈ 50,000 tokens ≈ 100 chunks
MAX_CONTENT_LENGTH = 200000

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def mask_api_key(api_key):
    """
    Return a masked API key prefix for logs.
    """
    if not api_key:
        return "<missing>"
    return f"{api_key[:8]}..."


def resolve_provider(cli_provider):
    """
    Resolve which provider to use for embeddings.

    Priority:
    1) --provider
    2) EMBEDDING_PROVIDER environment variable
    3) LLM_PROVIDER environment variable
    4) auto-detection
    """
    provider = cli_provider
    if not provider:
        provider = os.environ.get("EMBEDDING_PROVIDER")
    if not provider:
        provider = os.environ.get("LLM_PROVIDER", "auto")

    provider = provider.strip().lower()
    valid = {"auto", "openai", "azure"}
    if provider not in valid:
        print(f"[ERROR] Invalid provider '{provider}'.")
        print("[ERROR] Valid options: auto, openai, azure")
        raise SystemExit(1)

    openai_key = os.environ.get("OPENAI_API_KEY")
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_key = os.environ.get("AZURE_OPENAI_API_KEY")

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

    # Auto mode: prefer OpenAI if available (more stable default)
    if openai_key:
        return "openai"
    if azure_endpoint and azure_key:
        return "azure"

    print("[ERROR] Could not auto-detect provider.")
    print("Provide one of:")
    print("  - OPENAI_API_KEY")
    print("  - AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY")
    raise SystemExit(1)


def get_embedding_model(provider):
    """
    Get embedding model/deployment name for chosen provider.
    """
    if provider == "azure":
        return os.environ.get("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
    return os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")


def get_openai_client(provider):
    """
    Create an OpenAI or Azure OpenAI client.
    
    The credentials are read from environment variables.
    """
    if provider == "azure":
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

        if not endpoint or not api_key:
            print("[ERROR] Azure OpenAI credentials not found!")
            print("Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY.")
            raise SystemExit(1)

        print("[INFO] Provider: azure")
        print(f"[INFO] Azure endpoint: {endpoint}")
        print(f"[INFO] Azure API key prefix: {mask_api_key(api_key)}")
        print(f"[INFO] Azure API version: {api_version}")
        return AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )

    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "").strip()
    if not api_key:
        print("[ERROR] OpenAI API key not found!")
        print("Set OPENAI_API_KEY.")
        raise SystemExit(1)

    print("[INFO] Provider: openai")
    print(f"[INFO] OpenAI API key prefix: {mask_api_key(api_key)}")
    if base_url:
        print(f"[INFO] OpenAI base URL: {base_url}")
        return OpenAI(api_key=api_key, base_url=base_url)

    print("[INFO] OpenAI base URL: https://api.openai.com/v1")
    return OpenAI(api_key=api_key)


def normalize_tags_for_metadata(tags):
    """
    Convert tags to a stable string for vector DB metadata.
    """
    if isinstance(tags, list):
        cleaned = [str(t).strip() for t in tags if str(t).strip()]
        return ", ".join(cleaned)
    if isinstance(tags, str):
        return tags.strip()
    return ""


def normalize_date_for_metadata(meta):
    """
    Pick a compact date (YYYY-MM-DD when possible) from article metadata.
    """
    candidates = [
        meta.get("date"),
        meta.get("published"),
        meta.get("updated"),
    ]
    for raw in candidates:
        if not raw:
            continue
        s = str(raw).strip()
        if not s:
            continue
        # Fast path for ISO-like date prefix.
        if re.match(r"^\d{4}-\d{2}-\d{2}", s):
            return s[:10]
        # RFC-like dates often contain day/month/year tokens.
        # Try datetime parser for strings already normalized by Python.
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass
        # Last fallback: return raw string so metadata is never empty if present.
        return s
    return ""


def load_documents(source_filter=None):
    """
    Load all documents from our data directories.
    
    PARAMETERS:
    - source_filter: If provided, only load documents from this source
    
    RETURNS:
    - A list of dictionaries, each containing document data
    """
    documents = []
    
    # Load news articles
    if os.path.exists(NEWS_DIR):
        print(f"[INFO] Loading news articles from {NEWS_DIR}...")
        news_files = list(Path(NEWS_DIR).glob("*.json"))
        
        for filepath in news_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    doc = json.load(f)
                
                # Filter by source if requested
                doc_source = doc.get("source")
                if source_filter and doc_source != source_filter:
                    continue
                
                # Extract the content we need
                # ONLY use cleaned text from 03__cleaner.py - no fallback to raw
                content = doc.get("text", "")
                
                if content and len(content) > 100:
                    meta = doc.get("metadata", {}) or {}
                    documents.append({
                        "id": doc.get("id"),
                        "type": "news",
                        "source": doc.get("source"),
                        "title": doc.get("metadata", {}).get("title", ""),
                        "url": doc.get("link"),
                        "content": content,
                        "date": normalize_date_for_metadata(meta),
                        "tags": normalize_tags_for_metadata(meta.get("tags")),
                    })
            except Exception as e:
                print(f"[WARNING] Failed to load {filepath}: {e}")
        
        print(f"[INFO]   Loaded {len([d for d in documents if d['type'] == 'news'])} news articles")
    
    # Load Wikipedia articles
    if os.path.exists(WIKI_DIR):
        print(f"[INFO] Loading Wikipedia articles from {WIKI_DIR}...")
        wiki_files = list(Path(WIKI_DIR).glob("*.json"))
        
        for filepath in wiki_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    doc = json.load(f)
                
                content = doc.get("content", "")
                
                if content and len(content) > 100:
                    documents.append({
                        "id": doc.get("id"),
                        "type": "wiki",
                        "source": "wikipedia",
                        "title": doc.get("title", ""),
                        "url": doc.get("url"),
                        "content": content,
                    })
            except Exception as e:
                print(f"[WARNING] Failed to load {filepath}: {e}")
        
        print(f"[INFO]   Loaded {len([d for d in documents if d['type'] == 'wiki'])} Wikipedia articles")
    
    print(f"[INFO] Total documents loaded: {len(documents)}")
    return documents


def chunk_text(text, chunk_size, overlap):
    """
    Split text into smaller chunks with overlap.
    
    WHY CHUNK?
    - LLMs have limited context windows
    - Smaller chunks = more precise retrieval
    - Overlap = keeps context between chunks
    
    PARAMETERS:
    - text: The text to split
    - chunk_size: Maximum size of each chunk
    - overlap: Number of characters to overlap
    
    RETURNS:
    - A list of text chunks
    """
    chunks = []
    start = 0
    
    while start < len(text):
        # Get the chunk
        end = start + chunk_size
        chunk = text[start:end]
        
        # Only add non-empty chunks
        if chunk.strip():
            chunks.append(chunk)
        
        # Move to next chunk (with overlap)
        start = end - overlap
    
    return chunks


def chunk_text_recursive(text, chunk_size, overlap):
    """
    Split text into chunks using LangChain's RecursiveCharacterTextSplitter.
    
    Tries to split at natural boundaries in this priority order:
    1. Paragraph breaks ("\n\n")
    2. Line breaks ("\n")
    3. Sentence endings (". ")
    4. Word boundaries (" ")
    
    PARAMETERS:
    - text: The text to split
    - chunk_size: Maximum size of each chunk
    - overlap: Number of characters to overlap
    
    RETURNS:
    - A list of text chunks
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " "],
    )
    return splitter.split_text(text)


def create_embedding(client, text):
    """
    Create an embedding for a piece of text using OpenAI API.
    
    PARAMETERS:
    - client: OpenAI client
    - text: The text to embed
    
    RETURNS:
    - A list of numbers (the embedding vector)
    """
    kwargs = {
        "model": EMBEDDING_MODEL,
        "input": text,
    }
    if EMBEDDING_DIMS is not None:
        kwargs["dimensions"] = EMBEDDING_DIMS
    response = client.embeddings.create(**kwargs)
    
    return response.data[0].embedding


def setup_chromadb(reset=False, source_filter=None):
    """
    Set up ChromaDB and create/get our collection.
    
    PARAMETERS:
    - reset: If True, delete the entire collection and start fresh.
    - source_filter: If provided (and not reset), delete only chunks from this source.
    
    RETURNS:
    - The ChromaDB collection
    """
    print(f"[INFO] Setting up ChromaDB in {CHROMA_DIR}...")
    
    # Create the ChromaDB client (persistent storage)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    if reset:
        # Delete existing collection if it exists (fresh start)
        try:
            client.delete_collection(name=COLLECTION_NAME)
            print("[INFO]   Deleted existing collection (RESET)")
        except:
            pass
        
        # Create new collection
        collection = client.create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Portuguese Tourism Knowledge Base"}
        )
        print(f"[INFO]   Created NEW collection: {COLLECTION_NAME}")
    else:
        # Get or Create
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Portuguese Tourism Knowledge Base"}
        )
        print(f"[INFO]   Loaded existing collection: {COLLECTION_NAME}")
        
        if source_filter:
            # Delete existing chunks for this source so we can re-embed them
            try:
                print(f"[INFO]   Deleting existing chunks for source: {source_filter}")
                collection.delete(where={"source": source_filter})
                print(f"[INFO]   Deleted chunks for {source_filter}")
            except Exception as e:
                print(f"[WARNING] Failed to delete chunks for {source_filter}: {e}")
        
    return collection


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """
    Main function that runs the embedder.
    """
    global PROVIDER, EMBEDDING_MODEL, EMBEDDING_DIMS, CHROMA_DIR, MAX_CHUNK_SIZE, CHUNK_OVERLAP

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Embed documents into ChromaDB")
    parser.add_argument(
        "--provider",
        choices=["auto", "openai", "azure"],
        default=None,
        help="Embedding provider selection (default: EMBEDDING_PROVIDER/LLM_PROVIDER/auto)",
    )
    parser.add_argument(
        "--reset", 
        action="store_true", 
        help="Reset the database (delete everything) before starting"
    )
    parser.add_argument(
        "--source",
        type=str,
        help="Only process articles from this source (e.g. SKIFT). Will delete and re-embed them."
    )
    parser.add_argument(
        "--no-chunk",
        action="store_true",
        help="Embed full articles without chunking (each article = 1 embedding)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=None,
        help="Override chunk size in characters (default: 2000)"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=None,
        help="Override chunk overlap in characters (default: 200)"
    )
    parser.add_argument(
        "--chunk-strategy",
        choices=["char", "recursive"],
        default="char",
        help="Chunking strategy: 'char' (fixed character) or 'recursive' (smart boundaries)"
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default=None,
        help="Override embedding model name (e.g. text-embedding-3-small)"
    )
    parser.add_argument(
        "--embedding-dims",
        type=int,
        default=None,
        help="Request reduced embedding dimensions (e.g. 1536 for compressed 3-large)"
    )
    parser.add_argument(
        "--db-dir",
        type=str,
        default=None,
        help="Override ChromaDB output directory (default: from CHROMA_DIR env or data/vectordb)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("DOCUMENT EMBEDDER - Starting")
    print("=" * 60)
    print()

    # Step 0: Resolve provider + model + configuration overrides
    PROVIDER = resolve_provider(args.provider)
    EMBEDDING_MODEL = get_embedding_model(PROVIDER)
    
    # Apply CLI overrides
    if args.embedding_model:
        EMBEDDING_MODEL = args.embedding_model
    if args.embedding_dims:
        EMBEDDING_DIMS = args.embedding_dims
    if args.db_dir:
        global CHROMA_DIR
        CHROMA_DIR = args.db_dir
    if args.chunk_size is not None:
        global MAX_CHUNK_SIZE
        MAX_CHUNK_SIZE = args.chunk_size
    if args.chunk_overlap is not None:
        global CHUNK_OVERLAP
        CHUNK_OVERLAP = args.chunk_overlap
    
    print(f"[INFO] Selected provider: {PROVIDER}")
    print(f"[INFO] Embedding model/deployment: {EMBEDDING_MODEL}")
    if EMBEDDING_DIMS:
        print(f"[INFO] Embedding dimensions: {EMBEDDING_DIMS} (reduced)")
    print(f"[INFO] Chunk strategy: {'no chunking' if args.no_chunk else args.chunk_strategy}")
    if not args.no_chunk:
        print(f"[INFO] Chunk size: {MAX_CHUNK_SIZE} chars / Overlap: {CHUNK_OVERLAP} chars")
    print(f"[INFO] Database directory: {CHROMA_DIR}")
    print()
    
    # Step 1: Set up OpenAI client
    client = get_openai_client(PROVIDER)
    print()
    
    
    # Step 2: Load all documents
    documents = load_documents(source_filter=args.source)
    print()
    
    if len(documents) == 0:
        print("[ERROR] No documents found! Run the data collection scripts first.")
        return
    
    # Step 3: Set up ChromaDB
    collection = setup_chromadb(reset=args.reset, source_filter=args.source)
    print()
    
    # Step 4: Process each document
    print("[INFO] Processing documents...")
    print()
    
    # Get existing documents to skip duplicates
    existing_ids = set()
    if not args.reset:
        try:
            # We fetch all IDs currently in the collection
            # "ids" is lightweight compared to "documents" or "embeddings"
            result = collection.get(include=[])
            existing_ids = set(result["ids"])
            print(f"[INFO] Found {len(existing_ids)} existing chunks in database")
        except Exception as e:
            print(f"[WARNING] Could not fetch existing IDs: {e}")
    
    total_chunks = 0
    skipped_docs = 0
    
    for i, doc in enumerate(documents, start=1):
        # Check if document is already processed
        # We check if the first chunk ID exists (doc_id + "_chunk_0")
        # This assumes if chunk 0 exists, the whole doc exists
        test_chunk_id = f"{doc['id']}_chunk_0"
        
        if test_chunk_id in existing_ids:
             print(f"[{i}/{len(documents)}] [SKIP] Already indexed: {doc['title'][:40]}...")
             skipped_docs += 1
             continue

        print(f"[{i}/{len(documents)}] Processing: {doc['title'][:50]}...")
        
        # Skip very large documents (likely spam or scraping errors)
        content_length = len(doc["content"])
        if content_length > MAX_CONTENT_LENGTH:
            print(f"[SKIP]   Document too large ({content_length:,} chars > {MAX_CONTENT_LENGTH:,} max)")
            print()
            continue
        
        # Chunk the document (or use full article if --no-chunk)
        if args.no_chunk:
            chunks = [doc["content"]]  # Full article as single chunk
            print(f"[INFO]   Using full article (no chunking)")
        elif args.chunk_strategy == "recursive":
            chunks = chunk_text_recursive(doc["content"], MAX_CHUNK_SIZE, CHUNK_OVERLAP)
            print(f"[INFO]   Split into {len(chunks)} chunks (recursive)")
        else:
            chunks = chunk_text(doc["content"], MAX_CHUNK_SIZE, CHUNK_OVERLAP)
            print(f"[INFO]   Split into {len(chunks)} chunks")
        
        # Process each chunk
        try:
            for j, chunk in enumerate(chunks):
                # Create unique ID for this chunk
                chunk_id = f"{doc['id']}_chunk_{j}"
                
                # Create embedding
                embedding = create_embedding(client, chunk)
                
                # Store in ChromaDB
                collection.add(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        "doc_id": doc["id"],
                        "type": doc["type"],
                        "source": doc["source"],
                        "date": doc.get("date", ""),
                        "tags": doc.get("tags", ""),
                        "title": doc["title"],
                        "url": doc["url"] or "",
                        "chunk_index": j,
                        "total_chunks": len(chunks),
                    }]
                )
        except Exception as e:
            error_msg = str(e)
            if "maximum context length" in error_msg or "too many tokens" in error_msg.lower():
                print(f"[SKIP]   Article too long for embedding model ({len(doc['content']):,} chars)")
                print(f"[SKIP]   Consider using chunking for this article")
                skipped_docs += 1
                print()
                continue
            else:
                raise
        
        total_chunks += len(chunks)
        print(f"[INFO]   Added to database")
        print()
    
    # Step 5: Print summary
    print("-" * 60)
    print()
    print("=" * 60)
    print("DOCUMENT EMBEDDER - Finished")
    print("=" * 60)
    print()
    print(f"Documents processed: {len(documents)}")
    print(f"  - Newly embedded: {len(documents) - skipped_docs}")
    print(f"  - Skipped (already exists): {skipped_docs}")
    print(f"Total chunks created: {total_chunks}")
    print(f"Database location: {CHROMA_DIR}")
    print()


# =============================================================================
# RUN THE SCRIPT
# =============================================================================

if __name__ == "__main__":
    main()
