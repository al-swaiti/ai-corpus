# Ultimate MCP Documentation Server - Usage Guide

This guide shows all the different ways you can use the Ultimate MCP Documentation Server to scrape and search documentation.

## 🚀 Quick Start

Choose your preferred method:

### Method 1: MCP Client (Cursor IDE)
```bash
# Configure in ~/.cursor/mcp.json then use natural language:
"Scrape https://docs.python.org/"
"Search for authentication methods"
```

### Method 2: Command Line
```bash
# Direct command line usage:
.venv/bin/python ultimate_mcp_server.py --scrape https://docs.python.org/ --max-pages 50
```

### Method 3: Python Programming
```python
# Use as a Python library:
import asyncio
from ultimate_mcp_server import UltimateWebScraper, UltimateConfig

async def main():
    config = UltimateConfig(max_pages=10)
    scraper = UltimateWebScraper(config)
    stats = await scraper.scrape_website("https://httpbin.org/html")
    print(f"Scraped {stats['pages_crawled']} pages!")

asyncio.run(main())
```

## 💻 Command Line Reference

### Scraping Commands

```bash
# Basic scraping
.venv/bin/python ultimate_mcp_server.py --scrape https://docs.example.com/

# Limit pages
.venv/bin/python ultimate_mcp_server.py --scrape https://docs.example.com/ --max-pages 50

# JSON output
.venv/bin/python ultimate_mcp_server.py --scrape https://docs.example.com/ --output-format json
```

### Search Commands

```bash
# Basic search
.venv/bin/python ultimate_mcp_server.py --search "authentication methods"

# Semantic search
.venv/bin/python ultimate_mcp_server.py --search "user login" --search-type semantic

# Keyword search with more results
.venv/bin/python ultimate_mcp_server.py --search "API" --search-type keyword --max-results 20
```

### Information Commands

```bash
# List all scraped datasets
.venv/bin/python ultimate_mcp_server.py --list-data

# Interactive mode
.venv/bin/python ultimate_mcp_server.py --interactive

# Help
.venv/bin/python ultimate_mcp_server.py --help
```

## 🔧 Interactive Mode

The interactive mode provides a command-line interface:

```bash
.venv/bin/python ultimate_mcp_server.py --interactive
```

Commands in interactive mode:
- `scrape <url> [max_pages]` - Scrape a website
- `search <query>` - Search documentation
- `list` - List available datasets
- `help` - Show help
- `quit` - Exit

Example session:
```
🔥 > scrape https://httpbin.org/html 5
🔥 > search HTTP methods
🔥 > list
🔥 > quit
```

## 🐍 Programmatic Usage

### Basic Scraping

```python
import asyncio
from ultimate_mcp_server import UltimateWebScraper, UltimateConfig

async def scrape_website():
    # Create configuration
    config = UltimateConfig(
        max_pages=100,
        delay_seconds=0.5,
        concurrent_workers=8
    )
    
    # Create scraper
    scraper = UltimateWebScraper(config)
    
    # Scrape website
    stats = await scraper.scrape_website("https://docs.python.org/")
    
    print(f"Pages scraped: {stats['pages_crawled']}")
    print(f"Words extracted: {stats['total_words']:,}")
    
    # Access scraped pages
    for page in scraper.scraped_pages:
        print(f"URL: {page['url']}")
        print(f"Title: {page['metadata']['title']}")
        print(f"Content: {page['content'][:100]}...")

asyncio.run(scrape_website())
```

### Advanced Configuration

```python
from ultimate_mcp_server import UltimateConfig
from pathlib import Path

# Custom configuration
config = UltimateConfig(
    # Scraping settings
    max_pages=5000,
    delay_seconds=0.3,
    concurrent_workers=12,
    timeout_seconds=60.0,
    
    # Content settings
    min_content_length=50,
    include_tables=True,
    include_images=False,
    favor_precision=True,
    
    # AI/Search settings
    model_name="all-MiniLM-L6-v2",
    chunk_size=512,
    chunk_overlap=50,
    similarity_threshold=0.7,
    
    # Output settings
    output_dir=Path("custom_data"),
    backup_dir=Path("custom_backups")
)
```

### AI-Powered Search

```python
import asyncio
from ultimate_mcp_server import UltimateQueryEngine, UltimateConfig

async def search_documentation():
    config = UltimateConfig()
    query_engine = UltimateQueryEngine(config)
    
    # Load existing scraped data
    doc_count = await query_engine.load_documents()
    print(f"Loaded {doc_count} documents")
    
    # Different search types
    queries = [
        ("user authentication", "semantic"),
        ("API endpoints", "keyword"), 
        ("error handling", "hybrid")
    ]
    
    for query, search_type in queries:
        print(f"\nSearching '{query}' ({search_type}):")
        results = await query_engine.search(query, search_type, max_results=5)
        
        for i, result in enumerate(results, 1):
            score = result.get(f'{search_type}_score', result.get('hybrid_score', 0))
            print(f"{i}. {result['source_title']} (score: {score:.3f})")
            print(f"   URL: {result['source_url']}")
            print(f"   Preview: {result['content'][:100]}...")

asyncio.run(search_documentation())
```

### Using the MCP Server Interface

```python
import asyncio
from ultimate_mcp_server import UltimateMCPServer

async def use_mcp_interface():
    server = UltimateMCPServer()
    
    # Scrape using the MCP interface
    scrape_result = await server._handle_scrape({
        "url": "https://docs.example.com/",
        "max_pages": 20
    })
    print(scrape_result[0].text)
    
    # Search using the MCP interface
    search_result = await server._handle_search({
        "query": "authentication",
        "search_type": "hybrid",
        "max_results": 5
    })
    print(search_result[0].text)
    
    # List data using the MCP interface
    list_result = await server._handle_list_data({})
    print(list_result[0].text)

asyncio.run(use_mcp_interface())
```

## 📁 Working with Scraped Data

### File Structure

After scraping, you'll find files in the `data/` directory:

```
data/
├── example_com_pages_20250104_120000.json  # Scraped content
├── example_com_stats_20250104_120000.json  # Scraping statistics
└── examples/                               # Sample data
```

### Reading Scraped Data

```python
import json
from pathlib import Path

# Find latest scraped data
data_dir = Path("data")
pages_files = list(data_dir.glob("*_pages_*.json"))

if pages_files:
    latest_file = max(pages_files, key=lambda f: f.stat().st_mtime)
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        pages = json.load(f)
    
    print(f"Found {len(pages)} pages")
    
    # Process each page
    for page in pages:
        print(f"URL: {page['url']}")
        print(f"Title: {page['metadata']['title']}")
        print(f"Words: {page['word_count']}")
        print(f"Content: {page['content'][:200]}...")
        print("-" * 50)
```

## 🔧 Configuration Options

### Environment Variables

```bash
export MCP_LOG_LEVEL=DEBUG           # Detailed logging
export MCP_MAX_PAGES=10000          # Global max pages
export MCP_DELAY_SECONDS=1.0        # Default crawl delay
export MCP_MAX_WORKERS=8            # Max concurrent workers
```

### Programmatic Configuration

```python
config = UltimateConfig(
    # Performance
    max_pages=1000,
    concurrent_workers=6,
    delay_seconds=0.8,
    timeout_seconds=45.0,
    batch_size=100,
    
    # Content
    min_content_length=100,
    include_tables=True,
    favor_precision=True,
    
    # AI/ML
    model_name="all-MiniLM-L6-v2",
    chunk_size=512,
    similarity_threshold=0.7,
    cache_embeddings=True
)
```

## 🚨 Troubleshooting

### Common Issues

**"No module named 'mcp'"**
```bash
# Make sure to use the virtual environment
.venv/bin/python ultimate_mcp_server.py --help
```

**"No scraped data found"**
```bash
# Check if scraping completed successfully
.venv/bin/python ultimate_mcp_server.py --list-data

# Try scraping a simple site first
.venv/bin/python ultimate_mcp_server.py --scrape https://httpbin.org/html --max-pages 1
```

**Scraping fails**
- Check your internet connection
- Verify the URL is accessible
- Check if the site blocks scrapers (robots.txt)
- Try with a smaller max-pages limit

### Debug Mode

```bash
# Enable detailed logging
export MCP_LOG_LEVEL=DEBUG
.venv/bin/python ultimate_mcp_server.py --scrape https://example.com/
```

## 💡 Tips and Best Practices

1. **Start Small**: Test with `--max-pages 5` first
2. **Respect Robots.txt**: The scraper automatically checks robots.txt
3. **Use Appropriate Delays**: Default delays are respectful, increase for sensitive sites
4. **Monitor Resources**: Large scrapes can use significant memory and bandwidth
5. **Regular Backups**: Scraped data is saved automatically with timestamps
6. **Search Types**: 
   - Use `semantic` for conceptual searches
   - Use `keyword` for exact term matching
   - Use `hybrid` (default) for best results

## 📚 Examples

See `examples.py` for comprehensive usage examples:

```bash
.venv/bin/python examples.py
```

This file demonstrates:
- Basic and advanced scraping
- Different search methods
- Data processing workflows
- Error handling
- Custom configurations