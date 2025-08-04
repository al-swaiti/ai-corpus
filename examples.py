#!/usr/bin/env python3
"""
Examples showing how to use Ultimate MCP Documentation Server manually

This file demonstrates different ways to use the scraper programmatically
without going through the MCP protocol.
"""
import asyncio
import json
from pathlib import Path
from ultimate_mcp_server import (
    UltimateWebScraper, 
    UltimateQueryEngine,
    UltimateConfig,
    UltimateMCPServer
)


async def example_1_basic_scraping():
    """Example 1: Basic website scraping"""
    print("🔥 Example 1: Basic Website Scraping")
    print("=" * 50)
    
    # Create configuration
    config = UltimateConfig(
        max_pages=10,  # Limit for demonstration
        delay_seconds=1.0,
        concurrent_workers=2
    )
    
    # Create scraper
    scraper = UltimateWebScraper(config)
    
    # Scrape a website
    url = "https://httpbin.org/html"
    print(f"🕷️ Scraping: {url}")
    
    try:
        stats = await scraper.scrape_website(url)
        print(f"✅ Completed!")
        print(f"📄 Pages scraped: {stats['pages_crawled']}")
        print(f"❌ Pages failed: {stats['pages_failed']}")
        print(f"📝 Words extracted: {stats['total_words']:,}")
        print(f"⏱️ Duration: {stats.get('duration_seconds', 0):.1f} seconds")
        
        return stats
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


async def example_2_advanced_scraping():
    """Example 2: Advanced scraping with custom configuration"""
    print("\n🔥 Example 2: Advanced Scraping Configuration")
    print("=" * 50)
    
    # Custom configuration for larger sites
    config = UltimateConfig(
        max_pages=50,
        delay_seconds=0.5,
        concurrent_workers=8,
        min_content_length=50,  # Lower threshold for demo
        include_tables=True,
        chunk_size=256,  # Smaller chunks for demo
        similarity_threshold=0.6
    )
    
    scraper = UltimateWebScraper(config)
    
    # Example with a documentation site (replace with your preferred site)
    url = "https://httpbin.org/"
    print(f"🕷️ Advanced scraping: {url}")
    
    try:
        stats = await scraper.scrape_website(url, max_pages=5)
        
        print(f"✅ Advanced scraping completed!")
        print(f"📊 Strategy used: {stats.get('strategy', 'unknown')}")
        print(f"👥 Workers: {stats.get('workers', 'unknown')}")
        print(f"⏰ Delay: {stats.get('delay', 'unknown')}s")
        print(f"📄 Pages: {stats['pages_crawled']}/{stats['pages_crawled'] + stats['pages_failed']}")
        
        return stats
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


async def example_3_search_existing_data():
    """Example 3: Search existing scraped data"""
    print("\n🔥 Example 3: AI-Powered Search")
    print("=" * 50)
    
    # Create query engine
    config = UltimateConfig()
    query_engine = UltimateQueryEngine(config)
    
    # Load existing data
    doc_count = await query_engine.load_documents()
    
    if doc_count == 0:
        print("❌ No scraped documents found. Run scraping examples first!")
        return
    
    print(f"📚 Loaded {doc_count} documents")
    
    # Perform different types of searches
    queries = [
        "HTTP methods",
        "JSON response",
        "API testing"
    ]
    
    for query in queries:
        print(f"\n🔍 Searching: '{query}'")
        
        # Semantic search
        results = await query_engine.search(query, "semantic", max_results=3)
        
        if results:
            print(f"   Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                score = result.get('semantic_score', 0)
                title = result.get('source_title', 'Untitled')
                preview = result['content'][:100] + '...' if len(result['content']) > 100 else result['content']
                print(f"   {i}. {title} (score: {score:.3f})")
                print(f"      {preview}")
        else:
            print("   No results found")


async def example_4_full_workflow():
    """Example 4: Complete workflow - Scrape then Search"""
    print("\n🔥 Example 4: Complete Workflow (Scrape → Search)")
    print("=" * 50)
    
    # Use the MCP server's high-level interface
    server = UltimateMCPServer()
    
    # Step 1: Scrape a website
    print("Step 1: Scraping documentation...")
    scrape_args = {
        "url": "https://httpbin.org/html",
        "max_pages": 3
    }
    
    try:
        scrape_result = await server._handle_scrape(scrape_args)
        print("✅ Scraping completed!")
        
        # Step 2: Search the scraped content
        print("\nStep 2: Searching scraped content...")
        search_args = {
            "query": "HTML form",
            "search_type": "hybrid",
            "max_results": 3
        }
        
        search_result = await server._handle_search(search_args)
        print("✅ Search completed!")
        
        # Step 3: List available data
        print("\nStep 3: Available datasets...")
        list_result = await server._handle_list_data({})
        print(list_result[0].text)
        
    except Exception as e:
        print(f"❌ Workflow error: {e}")


async def example_5_programmatic_usage():
    """Example 5: Direct programmatic access to scraped data"""
    print("\n🔥 Example 5: Direct Data Access")
    print("=" * 50)
    
    # Find and read scraped data files directly
    data_dir = Path("data")
    
    if not data_dir.exists():
        print("❌ No data directory found")
        return
    
    # List all scraped files
    pages_files = list(data_dir.glob("*_pages_*.json"))
    stats_files = list(data_dir.glob("*_stats_*.json"))
    
    print(f"📁 Found {len(pages_files)} pages files and {len(stats_files)} stats files")
    
    if pages_files:
        # Read the most recent pages file
        latest_pages_file = max(pages_files, key=lambda f: f.stat().st_mtime)
        print(f"📄 Reading: {latest_pages_file.name}")
        
        with open(latest_pages_file, 'r', encoding='utf-8') as f:
            pages_data = json.load(f)
        
        print(f"📊 Pages in file: {len(pages_data)}")
        
        # Show sample data
        if pages_data:
            sample_page = pages_data[0]
            print(f"🌐 Sample URL: {sample_page['url']}")
            print(f"📝 Word count: {sample_page['word_count']}")
            print(f"📅 Crawled at: {sample_page['crawled_at']}")
            
            # Show content preview
            content_preview = sample_page['content'][:200] + '...' if len(sample_page['content']) > 200 else sample_page['content']
            print(f"📖 Content preview: {content_preview}")


async def example_6_custom_content_extraction():
    """Example 6: Custom content extraction and processing"""
    print("\n🔥 Example 6: Custom Content Processing")
    print("=" * 50)
    
    config = UltimateConfig()
    scraper = UltimateWebScraper(config)
    
    # Example of accessing scraped pages data directly
    # (This would be after running a scrape operation)
    
    print("🔧 This example shows how to access scraped data programmatically")
    print("💡 After scraping, you can access scraper.scraped_pages list directly")
    print("📝 Each page contains: url, content, metadata, word_count, etc.")
    
    # Demonstrate data structure
    sample_page_structure = {
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
    
    print("📋 Sample page data structure:")
    print(json.dumps(sample_page_structure, indent=2))


async def main():
    """Run all examples"""
    print("🚀 Ultimate MCP Documentation Server - Usage Examples")
    print("=" * 60)
    print("This script demonstrates various ways to use the scraper manually")
    print("=" * 60)
    
    try:
        # Run examples
        await example_1_basic_scraping()
        await example_2_advanced_scraping()
        await example_3_search_existing_data()
        await example_4_full_workflow()
        await example_5_programmatic_usage()
        await example_6_custom_content_extraction()
        
        print("\n🎉 All examples completed!")
        print("\n💡 Tips:")
        print("  - Check the 'data/' folder for scraped files")
        print("  - Use different search types: semantic, keyword, hybrid")
        print("  - Adjust configuration parameters for different needs")
        print("  - Look at the generated JSON files to understand data structure")
        
    except KeyboardInterrupt:
        print("\n👋 Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())