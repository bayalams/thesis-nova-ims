"""
11__web_app.py - Step 11: Web Interface for RAG
================================================

This script runs a simple web interface for asking questions.

WHAT IT DOES:
1. Shows a web page with a question input
2. When you ask a question, it:
   - Searches the vector database for relevant documents
   - Sends the documents + question to OpenAI or Azure OpenAI
   - Shows the answer with citations

HOW TO RUN:
    # Option A: OpenAI
    export OPENAI_API_KEY="your-openai-key"
    export OPENAI_LLM_MODEL="gpt-4o-mini"
    export OPENAI_EMBEDDING_MODEL="text-embedding-3-large"

    # Option B: Azure OpenAI
    export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
    export AZURE_OPENAI_API_KEY="your-azure-key"
    export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
    export AZURE_LLM_DEPLOYMENT="gpt-5"
    export AZURE_EMBEDDING_DEPLOYMENT="text-embedding-3-large"

    # Then run the web app
    python 11__web_app.py

    # Optional provider selection:
    python 11__web_app.py --provider auto
    python 11__web_app.py --provider openai
    python 11__web_app.py --provider azure

    # Open in browser: http://localhost:9999

COMMAND LINE OPTIONS:
    --provider auto|openai|azure   Provider selection
    --use-wikipedia                Include Wikipedia articles in search
    --no-wikipedia                 Exclude Wikipedia articles, only use news

REQUIREMENTS:
    - Run 10__embedder.py first to create the vector database
"""

# =============================================================================
# IMPORTS
# =============================================================================

import argparse  # Built-in library to parse command line arguments
import os        # Built-in library to work with files and folders
import re        # Built-in library for regular expression parsing
import time      # Built-in library for timing operations
import traceback # Built-in library for stack traces
import uuid      # Built-in library to generate request IDs
from urllib.parse import urlparse  # Built-in library to parse URLs

# External libraries (install with pip)
import chromadb
from flask import Flask, request, render_template_string
from openai import OpenAI, AzureOpenAI, BadRequestError

# =============================================================================
# GLOBAL FLAGS / STATE
# =============================================================================

# This will be set by command line arguments
# True = include Wikipedia articles in search
# False = only use news articles (DEFAULT)
USE_WIKIPEDIA = False

# Runtime configuration is stored here after startup
APP_CONFIG = {}

# =============================================================================
# CONFIGURATION
# =============================================================================

# ChromaDB settings
CHROMA_DIR = "data/vectordb"
COLLECTION_NAME = "tourism_knowledge"

# How many documents to retrieve
TOP_K = 10

# =============================================================================
# HTML TEMPLATE
# =============================================================================
# We keep the HTML simple and inline for beginner-friendliness

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Portuguese Tourism Assistant</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #2c3e50;
        }
        .question-form {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        input[type="text"] {
            width: 100%;
            padding: 15px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
            box-sizing: border-box;
        }
        input[type="text"]:focus {
            border-color: #3498db;
            outline: none;
        }
        button {
            background: #3498db;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover {
            background: #2980b9;
        }
        .answer {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .answer h2 {
            color: #27ae60;
            margin-top: 0;
        }
        .answer-text {
            line-height: 1.6;
            white-space: pre-wrap;
        }
        .error-banner {
            background: #ffe7e7;
            border-left: 4px solid #e74c3c;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            color: #7f1d1d;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }
        .error-banner h3 {
            margin-top: 0;
            margin-bottom: 8px;
            color: #c0392b;
        }
        .sources {
            background: #ecf0f1;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        .sources h3 {
            margin-top: 0;
            color: #7f8c8d;
        }
        .source-item {
            background: white;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 3px solid #3498db;
        }
        .source-item a {
            color: #3498db;
            text-decoration: none;
        }
        .source-item a:hover {
            text-decoration: underline;
        }
        .source-type {
            font-size: 12px;
            color: #95a5a6;
            text-transform: uppercase;
        }
        .chunks {
            background: #fff3cd;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            margin-bottom: 20px;
            border-left: 3px solid #ffc107;
        }
        .chunks h3 {
            margin-top: 0;
            color: #856404;
        }
        .chunk-item {
            background: white;
            padding: 12px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #ddd;
            transition: all 0.2s;
        }
        .chunk-item.used {
            border-left-color: #27ae60;
            background-color: #f0fff4;
            box-shadow: 0 2px 5px rgba(39, 174, 96, 0.1);
        }
        .chunk-header {
            font-weight: bold;
            color: #555;
            margin-bottom: 8px;
        }
        .badge {
            font-size: 10px;
            padding: 3px 6px;
            border-radius: 4px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .badge.used {
            background: #27ae60;
            color: white;
        }
        .badge.unused {
            background: #95a5a6;
            color: white;
        }
        .chunk-content {
            font-size: 14px;
            line-height: 1.5;
            color: #333;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
            border-top: 1px solid #eee;
            margin-top: 8px;
            padding-top: 8px;
        }
        .chunk-meta {
            font-size: 12px;
            color: #6c757d;
            margin-top: 8px;
        }
        .run-info {
            font-size: 12px;
            color: #6c757d;
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <h1>Portuguese Tourism Assistant</h1>
    <p>Ask me anything about travel, tourism, and culture in Portugal and Europe.</p>

    <div class="question-form">
        <form method="POST">
            <input type="text" name="question" placeholder="What are the best places to visit in Lisbon?"
                   value="{{ question or '' }}" autofocus>
            <button type="submit">Ask Question</button>
        </form>
        <div class="run-info">
            Provider: {{ provider }} | LLM: {{ llm_model }} | Embeddings: {{ embedding_model }}
        </div>
    </div>

    {% if error_message %}
    <div class="error-banner">
        <h3>Generation Error</h3>
        <div>{{ error_message }}</div>
        {% if request_id %}
        <div style="margin-top: 8px; font-size: 12px;">Request ID: {{ request_id }}</div>
        {% endif %}
    </div>
    {% endif %}

    {% if answer %}
    <div class="answer">
        <h2>Answer</h2>
        <div class="answer-text">{{ answer }}</div>

        {% if reasoning %}
        <div class="sources" style="border-left: 3px solid #9b59b6; margin-top: 15px;">
            <h3>Reasoning</h3>
            <div style="line-height: 1.6; white-space: pre-wrap;">{{ reasoning }}</div>
        </div>
        {% endif %}
    </div>
    {% endif %}

    {% if chunks %}
    <div class="chunks">
        <h3>Retrieved Chunks (Evaluation)</h3>
        <p style="font-size: 14px; color: #856404; margin-bottom: 15px;">
            Retrieved {{ chunks|length }} chunks.
            <br>
            <strong>Precision:</strong> {{ chunks|selectattr('is_used')|list|length }} used / {{ chunks|length }} retrieved.
        </p>
        {% for chunk in chunks %}
        <div class="chunk-item {{ 'used' if chunk.is_used else 'unused' }}">
            <div class="chunk-header">
                <span>
                    Chunk #{{ chunk.display_index }} - {{ chunk.title }}
                </span>
                {% if chunk.is_used %}
                    <span class="badge used">USED [Source {{ chunk.display_index }}]</span>
                {% else %}
                    <span class="badge unused">UNUSED</span>
                {% endif %}
            </div>

            <div class="chunk-content">{{ chunk.content }}</div>

            <div class="chunk-meta">
                <strong>Source:</strong> {{ chunk.source }} |
                <strong>Type:</strong> {{ chunk.type }} |
                <strong>Chunk Part:</strong> {{ chunk.chunk_index + 1 }}/{{ chunk.total_chunks }}
            </div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% if sources %}
    <div class="sources">
        <h3>Sources Retrieved</h3>
        {% for source in sources %}
        <div class="source-item">
            <span class="source-type">{{ source.type }}</span>
            <strong>{{ source.title }}</strong>
            {% if source.url %}
            <br><a href="{{ source.url }}" target="_blank">{{ source.url }}</a>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% endif %}
</body>
</html>
"""


# =============================================================================
# HELPER FUNCTIONS - PROVIDER / CONFIG
# =============================================================================

def build_request_id():
    """
    Build a short request ID so we can correlate logs for one query.
    """
    return uuid.uuid4().hex[:8]


def mask_api_key(api_key):
    """
    Return a masked API key prefix for logs.
    """
    if not api_key:
        return "<missing>"
    return f"{api_key[:8]}..."


def get_host_from_url(url):
    """
    Extract the host from a URL for cleaner logs.
    """
    if not url:
        return "<default>"
    try:
        return urlparse(url).netloc or url
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

    # Auto mode: prefer OpenAI if available (more stable default),
    # otherwise use Azure if configured.
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


def log_startup_config(config):
    """
    Print startup configuration in a readable way.
    """
    print("[CONFIG] Provider:", config["provider"])
    print("[CONFIG] LLM model:", config["llm_model"])
    print("[CONFIG] Embedding model:", config["embedding_model"])
    print("[CONFIG] Endpoint host:", config["endpoint_host"])
    print("[CONFIG] API version:", config["api_version"])
    print("[CONFIG] API key prefix:", config["api_key_prefix"])
    print("[CONFIG] TOP_K:", TOP_K)
    if USE_WIKIPEDIA:
        print("[CONFIG] Wikipedia articles: ENABLED")
    else:
        print("[CONFIG] Wikipedia articles: DISABLED (news only)")


# =============================================================================
# HELPER FUNCTIONS - CHROMADB / STATS
# =============================================================================

def get_chromadb_collection():
    """
    Get the ChromaDB collection.
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


def infer_collection_dimension(collection):
    """
    Infer collection embedding dimension from one stored embedding.
    """
    try:
        sample = collection.get(limit=1, include=["embeddings"])
        embeddings = sample.get("embeddings")
        if embeddings is None:
            embeddings = []
        if embeddings is not None and len(embeddings) > 0:
            first_embedding = embeddings[0]
            if first_embedding is not None:
                return len(first_embedding)
    except Exception as e:
        print(f"[WARNING] Could not infer collection dimension: {e}")

    return None


def safe_count_by_type(collection, doc_type):
    """
    Try to count documents by metadata type.

    This may be expensive for very large collections.
    """
    try:
        result = collection.get(where={"type": doc_type}, include=[])
        return len(result.get("ids") or [])
    except Exception as e:
        print(f"[WARNING] Could not count type '{doc_type}': {e}")
        return None


def log_collection_stats(collection):
    """
    Log collection size and useful diagnostics.
    """
    stats = {
        "count": None,
        "dimension": None,
        "news_count": None,
        "wiki_count": None,
    }

    try:
        stats["count"] = collection.count()
        print(f"[INFO] Collection loaded: {COLLECTION_NAME}")
        print(f"[INFO] Collection chunk count: {stats['count']}")
    except Exception as e:
        print(f"[WARNING] Could not read collection count: {e}")

    stats["dimension"] = infer_collection_dimension(collection)
    if stats["dimension"]:
        print(f"[INFO] Collection embedding dimension: {stats['dimension']}")

    # Optional counts by type
    stats["news_count"] = safe_count_by_type(collection, "news")
    stats["wiki_count"] = safe_count_by_type(collection, "wiki")

    if stats["news_count"] is not None:
        print(f"[INFO] News chunks: {stats['news_count']}")
    if stats["wiki_count"] is not None:
        print(f"[INFO] Wiki chunks: {stats['wiki_count']}")

    return stats


# =============================================================================
# HELPER FUNCTIONS - LLM REQUEST BUILDERS / PARSING
# =============================================================================

def is_reasoning_model(model_name):
    """
    Return True for model families that often require max_completion_tokens
    and default temperature behavior.
    """
    name = (model_name or "").strip().lower()

    # Keep this simple and explicit
    if name.startswith("gpt-5"):
        return True
    if name.startswith("o1") or name.startswith("o3") or name.startswith("o4"):
        return True
    if "reasoning" in name:
        return True

    return False


def build_chat_params(model_name, token_limit=1500):
    """
    Build chat completion parameters in a provider/model-safe way.
    """
    params = {}

    if is_reasoning_model(model_name):
        params["max_completion_tokens"] = token_limit
        params["reasoning_effort"] = "minimal"
    else:
        params["temperature"] = 0.7
        params["max_tokens"] = token_limit

    return params


def call_chat_completion_with_retries(client, request_kwargs, request_id):
    """
    Call chat.completions.create and retry once/twice if parameters are
    rejected by the endpoint.
    """
    current_kwargs = dict(request_kwargs)

    for attempt in range(1, 4):
        print(f"[REQ {request_id}] [INFO] LLM call attempt {attempt} with params: {sorted(current_kwargs.keys())}")

        try:
            response = client.chat.completions.create(**current_kwargs)
            return response, current_kwargs
        except BadRequestError as e:
            error_text = str(e)
            adjusted = False

            if "temperature" in error_text and "default (1)" in error_text and "temperature" in current_kwargs:
                print(f"[REQ {request_id}] [WARNING] Removing unsupported 'temperature' and retrying")
                current_kwargs.pop("temperature", None)
                adjusted = True

            if "max_tokens" in error_text and "max_completion_tokens" in error_text and "max_tokens" in current_kwargs:
                print(f"[REQ {request_id}] [WARNING] Switching max_tokens -> max_completion_tokens and retrying")
                current_kwargs["max_completion_tokens"] = current_kwargs.pop("max_tokens")
                adjusted = True

            if "max_completion_tokens" in error_text and "max_tokens" in error_text and "max_completion_tokens" in current_kwargs:
                print(f"[REQ {request_id}] [WARNING] Switching max_completion_tokens -> max_tokens and retrying")
                current_kwargs["max_tokens"] = current_kwargs.pop("max_completion_tokens")
                adjusted = True

            if "reasoning_effort" in error_text and "reasoning_effort" in current_kwargs:
                print(f"[REQ {request_id}] [WARNING] Removing unsupported 'reasoning_effort' and retrying")
                current_kwargs.pop("reasoning_effort", None)
                adjusted = True

            if adjusted and attempt < 3:
                continue

            print(f"[REQ {request_id}] [ERROR] BadRequestError: {e}")
            raise


def parse_model_output(full_response, refusal_text):
    """
    Parse answer/reasoning and enforce explicit error behavior for empty output.

    RETURNS:
    - answer (str or None)
    - reasoning (str or None)
    - error_message (str or None)
    """
    text = (full_response or "").strip()
    answer = text
    reasoning = None

    if text and "REASONING:" in text:
        parts = text.split("REASONING:", 1)
        answer = parts[0].strip()
        reasoning = parts[1].strip()

    if answer:
        return answer, reasoning, None

    if refusal_text:
        return None, None, f"Model refused to answer: {refusal_text}"

    if reasoning:
        return None, None, "Model returned reasoning but no answer text. Please retry or change the model."

    if not text:
        return None, None, "Model returned an empty response. Check provider, model, and API credentials."

    return None, None, "Model response did not include usable answer text."


def extract_usage_fields(response):
    """
    Extract token usage fields safely.
    """
    usage = getattr(response, "usage", None)
    if not usage:
        return None, None, None

    prompt_tokens = getattr(usage, "prompt_tokens", None)
    completion_tokens = getattr(usage, "completion_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)

    return prompt_tokens, completion_tokens, total_tokens


def extract_response_details(response):
    """
    Extract common response fields used in logs and parsing.
    """
    details = {
        "response_id": getattr(response, "id", None),
        "finish_reason": None,
        "content": "",
        "refusal_text": None,
        "tool_calls_present": False,
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
    }

    choices = getattr(response, "choices", []) or []
    if not choices:
        return details

    choice = choices[0]
    details["finish_reason"] = getattr(choice, "finish_reason", None)

    message = getattr(choice, "message", None)
    if message:
        details["content"] = getattr(message, "content", None) or ""
        details["refusal_text"] = getattr(message, "refusal", None)
        tool_calls = getattr(message, "tool_calls", None)
        details["tool_calls_present"] = bool(tool_calls)

    prompt_tokens, completion_tokens, total_tokens = extract_usage_fields(response)
    details["prompt_tokens"] = prompt_tokens
    details["completion_tokens"] = completion_tokens
    details["total_tokens"] = total_tokens

    return details


# =============================================================================
# CORE APP FUNCTIONS
# =============================================================================

def search_documents(collection, client, question, top_k, request_id):
    """
    Search for documents relevant to the question.

    PARAMETERS:
    - collection: ChromaDB collection
    - client: OpenAI/Azure client
    - question: The user's question
    - top_k: Number of results to return
    - request_id: Correlation ID for logs

    RETURNS:
    - A list of relevant document chunks with metadata
    """
    print(f"[REQ {request_id}] [INFO] Searching documents")
    print(f"[REQ {request_id}] [INFO] Question length: {len(question)} chars")
    print(f"[REQ {request_id}] [INFO] TOP_K: {top_k}")
    print(f"[REQ {request_id}] [INFO] Embedding model: {APP_CONFIG['embedding_model']}")

    if USE_WIKIPEDIA:
        print(f"[REQ {request_id}] [INFO] Wikipedia articles: ENABLED")
    else:
        print(f"[REQ {request_id}] [INFO] Wikipedia articles: DISABLED (only news)")

    # Step 1: Create embedding for the question
    response = client.embeddings.create(
        model=APP_CONFIG["embedding_model"],
        input=question,
    )
    question_embedding = response.data[0].embedding
    print(f"[REQ {request_id}] [INFO] Query embedding dimension: {len(question_embedding)}")

    # Step 2: Search ChromaDB
    if USE_WIKIPEDIA:
        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=top_k,
        )
    else:
        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=top_k,
            where={"type": "news"},
        )

    # Step 3: Format results
    documents = []

    ids = results.get("ids") or [[]]
    docs = results.get("documents") or [[]]
    metas = results.get("metadatas") or [[]]

    if ids and ids[0]:
        for i in range(len(ids[0])):
            documents.append({
                "content": docs[0][i],
                "metadata": metas[0][i],
            })

    # Step 4: Log retrieval stats
    chunk_lengths = [len((doc.get("content") or "")) for doc in documents]
    unique_sources = set()
    for doc in documents:
        meta = doc.get("metadata") or {}
        unique_sources.add(meta.get("source", "unknown"))

    print(f"[REQ {request_id}] [INFO] Retrieved chunks: {len(documents)}")
    print(f"[REQ {request_id}] [INFO] Unique sources: {len(unique_sources)}")

    if chunk_lengths:
        avg_len = sum(chunk_lengths) / len(chunk_lengths)
        print(f"[REQ {request_id}] [INFO] Chunk length min/avg/max: {min(chunk_lengths)}/{avg_len:.1f}/{max(chunk_lengths)}")

    return documents


def generate_answer(client, question, documents, request_id):
    """
    Generate an answer using the retrieved documents.

    RETURNS:
    - answer (str or None)
    - reasoning (str or None)
    - error_message (str or None)
    """
    print(f"[REQ {request_id}] [INFO] Generating answer with provider={APP_CONFIG['provider']} model={APP_CONFIG['llm_model']}")

    if not documents:
        return None, None, "No documents were retrieved from the vector database for this question."

    model_is_reasoning = is_reasoning_model(APP_CONFIG["llm_model"])

    # Build the context from documents
    # For reasoning-heavy models we reduce prompt size to lower empty-output risk.
    documents_for_prompt = documents
    chunk_char_limit = None
    if model_is_reasoning:
        documents_for_prompt = documents[:5]
        chunk_char_limit = 1200
        print(f"[REQ {request_id}] [INFO] Using top {len(documents_for_prompt)} chunks for prompt (reasoning-model context cap).")

    context_parts = []
    for i, doc in enumerate(documents_for_prompt, start=1):
        meta = doc["metadata"]
        chunk_text = doc.get("content", "")
        if chunk_char_limit:
            chunk_text = chunk_text[:chunk_char_limit]
        context_parts.append(f"[Source {i}: {meta.get('title', 'Untitled')}]\n{chunk_text}\n")

    context = "\n---\n".join(context_parts)

    # Build prompts

    system_prompt = """You are a helpful assistant specializing in Portuguese and European tourism.

Answer the user's question based on the provided sources. Be informative and helpful.

IMPORTANT - CITATION RULES:
1. You MUST cite the source for EVERY piece of information you provide
2. Use inline citations in the format [Source N] after each fact or claim
3. Example: "Lisbon is the capital of Portugal [Source 1] and has a population of around 500,000 [Source 2]."
4. If multiple sources confirm the same fact, cite all of them: [Source 1, 3]
5. NEVER state a fact without a citation - this is critical for verification

If the sources don't contain enough information to fully answer the question, say so clearly and only provide information that IS supported by the sources.
"""

    # Reasoning models (for example gpt-5) may consume many completion tokens
    # internally. We make reasoning optional to reduce empty-output risk.
    if model_is_reasoning:
        system_prompt += """
FORMAT YOUR RESPONSE LIKE THIS:
[Your answer with citations here]

You may add a short REASONING section only if there is enough space.
Do not leave the answer blank."""
    else:
        system_prompt += """
FORMAT YOUR RESPONSE LIKE THIS:
[Your answer with citations here]

REASONING:
[Explain your reasoning process here - which sources you found most relevant, how you combined information, any gaps you noticed, and why you structured the answer the way you did]"""

    if model_is_reasoning:
        response_format_instruction = (
            "Please provide a helpful answer based on the sources above. "
            "Remember to cite [Source N] after EVERY piece of information. "
            "Prioritize returning a complete final answer."
        )
    else:
        response_format_instruction = (
            "Please provide a helpful answer based on the sources above. "
            "Remember to cite [Source N] after EVERY piece of information. "
            "Then explain your reasoning after the REASONING: marker."
        )

    user_prompt = f"""Here are relevant sources from our knowledge base:

{context}

---

User Question: {question}

{response_format_instruction}"""

    print(f"[REQ {request_id}] [INFO] Context size: {len(context)} chars")
    print(f"[REQ {request_id}] [INFO] User prompt size: {len(user_prompt)} chars")

    # Build request
    request_kwargs = {
        "model": APP_CONFIG["llm_model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    token_limit = 2200 if model_is_reasoning else 1500
    request_kwargs.update(build_chat_params(APP_CONFIG["llm_model"], token_limit=token_limit))

    # Call model with compatibility retries
    started = time.time()
    response, final_request_kwargs = call_chat_completion_with_retries(client, request_kwargs, request_id)
    elapsed_ms = (time.time() - started) * 1000

    # Parse response metadata
    choices = getattr(response, "choices", []) or []
    if not choices:
        print(f"[REQ {request_id}] [ERROR] Model returned no choices")
        return None, None, "Model returned no completion choices."

    details = extract_response_details(response)
    response_id = details["response_id"]
    finish_reason = details["finish_reason"]
    content = details["content"]
    refusal_text = details["refusal_text"]
    tool_calls_present = details["tool_calls_present"]
    prompt_tokens = details["prompt_tokens"]
    completion_tokens = details["completion_tokens"]
    total_tokens = details["total_tokens"]

    print(f"[REQ {request_id}] [INFO] Response ID: {response_id}")
    print(f"[REQ {request_id}] [INFO] Finish reason: {finish_reason}")
    print(f"[REQ {request_id}] [INFO] Latency: {elapsed_ms:.1f} ms")
    print(f"[REQ {request_id}] [INFO] Prompt/Completion/Total tokens: {prompt_tokens}/{completion_tokens}/{total_tokens}")
    print(f"[REQ {request_id}] [INFO] Message content length: {len(content)}")
    print(f"[REQ {request_id}] [INFO] Refusal present: {bool(refusal_text)}")
    print(f"[REQ {request_id}] [INFO] Tool calls present: {tool_calls_present}")
    print(f"[REQ {request_id}] [INFO] Final request params: {sorted(final_request_kwargs.keys())}")

    # If we got no visible content and token limit was exhausted, retry once with
    # a larger completion limit and stronger instruction to produce final output.
    if not (content or "").strip() and finish_reason == "length" and "max_completion_tokens" in final_request_kwargs:
        print(f"[REQ {request_id}] [WARNING] Empty output with finish_reason=length. Retrying once with higher max_completion_tokens.")
        retry_kwargs = dict(final_request_kwargs)
        retry_kwargs["max_completion_tokens"] = min(int(retry_kwargs.get("max_completion_tokens", token_limit)) + 1000, 4000)
        retry_messages = list(retry_kwargs.get("messages", []))
        retry_messages.append({
            "role": "user",
            "content": "Return only the final answer with citations. Do not output an empty response."
        })
        retry_kwargs["messages"] = retry_messages

        retry_started = time.time()
        response, final_request_kwargs = call_chat_completion_with_retries(client, retry_kwargs, request_id)
        elapsed_ms = (time.time() - retry_started) * 1000

        choices = getattr(response, "choices", []) or []
        if not choices:
            print(f"[REQ {request_id}] [ERROR] Retry returned no choices")
            return None, None, "Model returned no completion choices (after retry)."

        details = extract_response_details(response)
        response_id = details["response_id"]
        finish_reason = details["finish_reason"]
        content = details["content"]
        refusal_text = details["refusal_text"]
        tool_calls_present = details["tool_calls_present"]
        prompt_tokens = details["prompt_tokens"]
        completion_tokens = details["completion_tokens"]
        total_tokens = details["total_tokens"]

        print(f"[REQ {request_id}] [INFO] Retry response ID: {response_id}")
        print(f"[REQ {request_id}] [INFO] Retry finish reason: {finish_reason}")
        print(f"[REQ {request_id}] [INFO] Retry latency: {elapsed_ms:.1f} ms")
        print(f"[REQ {request_id}] [INFO] Retry Prompt/Completion/Total tokens: {prompt_tokens}/{completion_tokens}/{total_tokens}")
        print(f"[REQ {request_id}] [INFO] Retry content length: {len(content)}")
        print(f"[REQ {request_id}] [INFO] Retry refusal present: {bool(refusal_text)}")
        print(f"[REQ {request_id}] [INFO] Retry tool calls present: {tool_calls_present}")
        print(f"[REQ {request_id}] [INFO] Retry final request params: {sorted(final_request_kwargs.keys())}")

    answer, reasoning, error_message = parse_model_output(content, refusal_text)

    # Final fallback for stubborn empty-output behavior in reasoning models:
    # use fewer chunks and a shorter prompt to force a visible answer.
    if error_message and model_is_reasoning and "empty response" in error_message.lower():
        print(f"[REQ {request_id}] [WARNING] Triggering short-context fallback request.")

        fallback_docs = documents[:3]
        fallback_context_parts = []
        for i, doc in enumerate(fallback_docs, start=1):
            meta = doc.get("metadata") or {}
            trimmed_content = (doc.get("content") or "")[:1200]
            fallback_context_parts.append(
                f"[Source {i}: {meta.get('title', 'Untitled')}]\n{trimmed_content}\n"
            )
        fallback_context = "\n---\n".join(fallback_context_parts)

        fallback_messages = [
            {
                "role": "system",
                "content": (
                    "Answer using only the provided sources. "
                    "Cite every factual statement as [Source N]. "
                    "Return final answer text only."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Sources:\n{fallback_context}\n\n"
                    "Provide a concise answer with citations."
                ),
            },
        ]

        fallback_kwargs = {
            "model": APP_CONFIG["llm_model"],
            "messages": fallback_messages,
            "max_completion_tokens": 800,
        }

        fallback_started = time.time()
        response, final_request_kwargs = call_chat_completion_with_retries(client, fallback_kwargs, request_id)
        fallback_elapsed_ms = (time.time() - fallback_started) * 1000

        choices = getattr(response, "choices", []) or []
        if not choices:
            print(f"[REQ {request_id}] [ERROR] Fallback returned no choices")
            return None, None, "Model returned no completion choices (fallback)."

        details = extract_response_details(response)
        response_id = details["response_id"]
        finish_reason = details["finish_reason"]
        content = details["content"]
        refusal_text = details["refusal_text"]
        tool_calls_present = details["tool_calls_present"]
        prompt_tokens = details["prompt_tokens"]
        completion_tokens = details["completion_tokens"]
        total_tokens = details["total_tokens"]

        print(f"[REQ {request_id}] [INFO] Fallback response ID: {response_id}")
        print(f"[REQ {request_id}] [INFO] Fallback finish reason: {finish_reason}")
        print(f"[REQ {request_id}] [INFO] Fallback latency: {fallback_elapsed_ms:.1f} ms")
        print(f"[REQ {request_id}] [INFO] Fallback Prompt/Completion/Total tokens: {prompt_tokens}/{completion_tokens}/{total_tokens}")
        print(f"[REQ {request_id}] [INFO] Fallback content length: {len(content)}")
        print(f"[REQ {request_id}] [INFO] Fallback refusal present: {bool(refusal_text)}")
        print(f"[REQ {request_id}] [INFO] Fallback tool calls present: {tool_calls_present}")
        print(f"[REQ {request_id}] [INFO] Fallback final request params: {sorted(final_request_kwargs.keys())}")

        answer, reasoning, error_message = parse_model_output(content, refusal_text)

    if error_message:
        print(f"[REQ {request_id}] [ERROR] {error_message}")

    return answer, reasoning, error_message


def run_startup_sanity_check(client, collection):
    """
    Run a startup sanity check for embeddings + chat completion.

    This runs on every startup to fail fast when credentials/model wiring is wrong.
    """
    print("[SANITY] Running startup sanity check...")

    try:
        # Step 1: Embedding sanity
        embedding_response = client.embeddings.create(
            model=APP_CONFIG["embedding_model"],
            input="sanity check ping",
        )
        sanity_embedding = embedding_response.data[0].embedding
        sanity_dim = len(sanity_embedding)
        print(f"[SANITY] Embedding dimension from API: {sanity_dim}")

        collection_dim = APP_CONFIG.get("collection_dimension")
        if collection_dim:
            print(f"[SANITY] Collection dimension: {collection_dim}")
            if sanity_dim != collection_dim:
                print("[SANITY] [ERROR] Embedding dimension mismatch!")
                print("[SANITY] [ERROR] Your embedder and web app are using incompatible embedding models.")
                print("[SANITY] [ERROR] Re-run embedding with the same embedding model configured for web app.")
                raise SystemExit(1)

        # Step 2: Chat sanity
        sanity_kwargs = {
            "model": APP_CONFIG["llm_model"],
            "messages": [
                {"role": "system", "content": "Reply with exactly SANITY_OK"},
                {"role": "user", "content": "Return SANITY_OK"},
            ],
        }
        sanity_kwargs.update(build_chat_params(APP_CONFIG["llm_model"], token_limit=200))

        response, final_request_kwargs = call_chat_completion_with_retries(client, sanity_kwargs, "startup")

        response_id = getattr(response, "id", None)
        choices = getattr(response, "choices", []) or []

        if not choices:
            print("[SANITY] [ERROR] Sanity chat returned no choices")
            raise SystemExit(1)

        choice = choices[0]
        finish_reason = getattr(choice, "finish_reason", None)
        message = getattr(choice, "message", None)
        content = ""
        if message:
            content = getattr(message, "content", None) or ""

        prompt_tokens, completion_tokens, total_tokens = extract_usage_fields(response)

        print(f"[SANITY] Response ID: {response_id}")
        print(f"[SANITY] Finish reason: {finish_reason}")
        print(f"[SANITY] Prompt/Completion/Total tokens: {prompt_tokens}/{completion_tokens}/{total_tokens}")
        print(f"[SANITY] Final request params: {sorted(final_request_kwargs.keys())}")
        print(f"[SANITY] Response preview: {content[:80]!r}")

        if "SANITY_OK" not in content.upper():
            print("[SANITY] [ERROR] Sanity response did not contain SANITY_OK")
            raise SystemExit(1)

        print("[SANITY] Startup sanity check passed")

    except SystemExit:
        raise
    except Exception as e:
        print(f"[SANITY] [ERROR] Startup sanity check failed: {type(e).__name__}: {e}")
        if APP_CONFIG.get("provider") == "azure":
            print("[SANITY] [HINT] Verify AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_LLM_DEPLOYMENT, and AZURE_EMBEDDING_DEPLOYMENT.")
        else:
            print("[SANITY] [HINT] Verify OPENAI_API_KEY, OPENAI_LLM_MODEL, and OPENAI_EMBEDDING_MODEL.")
        raise SystemExit(1)


# =============================================================================
# FLASK APP
# =============================================================================

# Create Flask app
app = Flask(__name__)

# Initialize clients (done once at startup)
openai_client = None
chroma_collection = None


@app.route("/", methods=["GET", "POST"])
def home():
    """
    Main page handler.
    Shows the question form and handles submissions.
    """
    global openai_client, chroma_collection

    question = None
    answer = None
    sources = None
    reasoning = None
    error_message = None
    request_id = None
    chunks = None

    if request.method == "POST":
        question = request.form.get("question", "").strip()

        if question:
            request_id = build_request_id()
            print()
            print("=" * 60)
            print(f"[REQ {request_id}] [QUESTION] {question}")
            print("=" * 60)

            documents = []

            try:
                # Search for relevant documents
                documents = search_documents(
                    chroma_collection,
                    openai_client,
                    question,
                    TOP_K,
                    request_id,
                )

                # Generate answer
                answer, reasoning, error_message = generate_answer(
                    openai_client,
                    question,
                    documents,
                    request_id,
                )

            except Exception as e:
                error_message = f"Request failed: {type(e).__name__}: {e}"
                print(f"[REQ {request_id}] [ERROR] {error_message}")
                traceback.print_exc()

            # Identify which chunks were actually used based on citations
            used_indices = set()
            if answer:
                source_blocks = re.findall(r"\[Source[s]?\s*([^\]]+)\]", answer, re.IGNORECASE)
                for block in source_blocks:
                    numbers = re.findall(r"(\d+)", block)
                    for num in numbers:
                        try:
                            idx = int(num) - 1
                            if 0 <= idx < len(documents):
                                used_indices.add(idx)
                        except Exception:
                            pass

            # Prepare chunks for evaluation display
            chunks = []
            for i, doc in enumerate(documents):
                meta = doc.get("metadata") or {}
                is_used = i in used_indices

                chunks.append({
                    "content": doc.get("content", ""),
                    "title": meta.get("title", "Untitled"),
                    "source": meta.get("source", "unknown"),
                    "type": meta.get("type", "unknown"),
                    "chunk_index": meta.get("chunk_index", 0),
                    "total_chunks": meta.get("total_chunks", 1),
                    "is_used": is_used,
                    "display_index": i + 1,
                })

            # Extract unique sources for display
            seen_titles = set()
            sources = []
            for i, doc in enumerate(documents):
                meta = doc.get("metadata") or {}
                title = meta.get("title", "Untitled")
                if title not in seen_titles:
                    seen_titles.add(title)
                    is_used = i in used_indices
                    sources.append({
                        "title": title,
                        "type": meta.get("type", "unknown"),
                        "source": meta.get("source", "unknown"),
                        "url": meta.get("url", ""),
                        "is_used": is_used,
                    })

            print()

    return render_template_string(
        HTML_TEMPLATE,
        question=question,
        answer=answer,
        chunks=chunks,
        sources=sources,
        reasoning=reasoning,
        error_message=error_message,
        request_id=request_id,
        provider=APP_CONFIG.get("provider", "unknown"),
        llm_model=APP_CONFIG.get("llm_model", "unknown"),
        embedding_model=APP_CONFIG.get("embedding_model", "unknown"),
    )


# =============================================================================
# MAIN
# =============================================================================

def main():
    """
    Main function that runs the web app.
    """
    global openai_client, chroma_collection, USE_WIKIPEDIA, APP_CONFIG

    # Step 1: Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Portuguese Tourism Assistant - RAG Web App"
    )

    parser.add_argument(
        "--provider",
        choices=["auto", "openai", "azure"],
        default=None,
        help="Provider selection (default: LLM_PROVIDER/auto)",
    )

    # Create mutually exclusive group for wikipedia flag
    wiki_group = parser.add_mutually_exclusive_group()
    wiki_group.add_argument(
        "--use-wikipedia",
        action="store_true",
        help="Include Wikipedia articles in search results"
    )
    wiki_group.add_argument(
        "--no-wikipedia",
        action="store_true",
        help="Exclude Wikipedia articles, only use news articles (default)"
    )

    # Parse the arguments
    args = parser.parse_args()

    # Set wikipedia mode
    if args.use_wikipedia:
        USE_WIKIPEDIA = True
    else:
        USE_WIKIPEDIA = False

    print("=" * 60)
    print("PORTUGUESE TOURISM ASSISTANT - Starting")
    print("=" * 60)
    print()

    # Step 2: Resolve provider and build client
    provider = resolve_provider(args.provider)
    llm_model, embedding_model = get_model_names(provider)

    print("[INFO] Initializing LLM client...")
    openai_client, endpoint_host, api_version, raw_api_key = build_llm_client(provider)

    APP_CONFIG = {
        "provider": provider,
        "llm_model": llm_model,
        "embedding_model": embedding_model,
        "endpoint_host": endpoint_host,
        "api_version": api_version,
        "api_key_prefix": mask_api_key(raw_api_key),
        "collection_dimension": None,
    }

    print()
    log_startup_config(APP_CONFIG)
    print()

    # Step 3: Initialize ChromaDB
    print("[INFO] Loading vector database...")
    chroma_collection = get_chromadb_collection()
    collection_stats = log_collection_stats(chroma_collection)
    APP_CONFIG["collection_dimension"] = collection_stats.get("dimension")
    print()

    # Step 4: Run startup sanity checks
    run_startup_sanity_check(openai_client, chroma_collection)
    print()

    # Step 5: Start the web server
    print("[INFO] Starting web server...")
    print()
    print("=" * 60)
    print("Open in your browser: http://localhost:9999")
    print("=" * 60)
    print()
    print("Press Ctrl+C to stop the server")
    print()

    app.run(host="0.0.0.0", port=9999, debug=False)


if __name__ == "__main__":
    main()
