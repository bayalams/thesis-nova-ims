# Simple Flying Cleaning Overview

## Source Characteristics

**Website**: [simpleflying.com](https://simpleflying.com)  
**Content Type**: Aviation news, airline coverage, aircraft analysis  
**Language**: English

### Raw Content Issues

1. **Header Noise**: Menu, Follow/Like buttons, author bios, "Sign in" prompts
2. **AI Summary Prompts**: "Here is a fact-based summary...", "Explain it like I'm 5"
3. **Footer Noise**: "Trending Now", related article links, "Copy link"
4. **Inline Links**: Markdown-style links `[text](/url/)` throughout articles
5. **Tag Links**: `TagName](/tag/tag-name/ "TagName")` patterns
6. **Image Credits**: "Credit: Shutterstock", "Photo: Getty Images"
7. **Newsletter Prompts**: "Soar through captivating aviation stories..."

---

## Cleaning Steps

### 1. Date Extraction
- Extracts "Published X hours/days ago" from raw content
- Converts to actual date using `scraped_at` timestamp as base
- Stores in `meta['pubDate']` as `YYYY-MM-DD` format

### 2. Header Trimming
- Title-based header trim using `trim_header_by_title()`
- Removes: Close, Menu, Follow, Like, Thread counts, Author bios

### 3. AI Summary Removal
- Removes interactive prompts that appear before article content
- Triggers: "Here is a fact-based summary", "Show me the facts", etc.

### 4. Footer Trimming
- Cuts at "Trending Now", related article links
- Uses `rfind()` to find last occurrence in article

### 5. Link Removal
- Converts markdown links `[text](/url)` → `text`
- Removes orphaned brackets from partial link patterns
- Removes tag links and inline image markdown

### 6. Image Credit Removal
- Patterns: "Credit:", "Photo:", "Image:", "Source:", "(Photo by...)"

---

## Key Implementation Details

**File**: `cleaners/clean_simple_flying.py`

```python
# Date extraction with scraped_at support
def extract_simple_flying_date(text, scraped_at=None):
    # Uses scraped_at as base time for accurate date calculation
    match = re.search(r'Published (\d+) (hours?|days?) ago', text)
    if match:
        pub_date = base_time - timedelta(...)
        return pub_date.strftime('%Y-%m-%d')

# Main cleaner accepts scraped_at parameter
def clean_simple_flying(text, meta, scraped_at=None):
    # 1. Extract date (using scraped_at)
    # 2. Header trimming
    # 3. AI summary removal  
    # 4. Footer trimming
    # 5. Link removal (markdown → plain text)
    # 6. Image credit removal
```

---

## Dispatcher Integration

```python
# In dispatcher.py
elif 'SIMPLE_FLYING' in source and clean_simple_flying:
    cleaned_body = clean_simple_flying(text, meta)
```

---

## Known Limitations

1. **Date Accuracy**: Relative dates ("2 hours ago") are approximate; accuracy depends on `scraped_at` timestamp being captured at scrape time
2. **Image Captions**: Some contextual captions may be removed if they match credit patterns
3. **Tables**: Markdown tables are preserved correctly
