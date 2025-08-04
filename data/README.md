# Data Directory

This directory contains scraped documentation data from various websites.

## Structure

- `examples/` - Sample scraped data for demonstration
- Main directory will contain your scraped datasets (ignored by git)

## File Format

### Pages Files (`*_pages_*.json`)
Contains an array of scraped pages with the following structure:
```json
[
  {
    "url": "https://example.com/page",
    "content": "Extracted page content...",
    "metadata": {
      "title": "Page Title",
      "description": "Page description",
      "keywords": ["keyword1", "keyword2"],
      "language": "en"
    },
    "word_count": 150,
    "char_count": 850,
    "crawl_depth": 1,
    "crawled_at": "2025-01-01T12:00:00Z"
  }
]
```

### Stats Files (`*_stats_*.json`)
Contains scraping statistics:
```json
{
  "pages_crawled": 50,
  "pages_failed": 2,
  "total_words": 15000,
  "total_chars": 95000,
  "start_time": "2025-01-01T12:00:00Z",
  "end_time": "2025-01-01T12:05:00Z",
  "duration_seconds": 300,
  "target_domain": "example.com",
  "strategy": "auto-optimized",
  "workers": 4,
  "delay": 1.0
}
```

## Usage

When you scrape documentation using the MCP server, files will be automatically saved here with timestamped names like:
- `domain_com_pages_20250101_120000.json`
- `domain_com_stats_20250101_120000.json`

These files can then be searched using the AI-powered query capabilities of the MCP server.