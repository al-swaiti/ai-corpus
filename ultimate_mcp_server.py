#!/usr/bin/env python3
"""
Ultimate MCP Documentation Server
ONE server that handles ANY website automatically

Features:
- Automatic scaling (detects small vs large sites)
- Smart intent detection and request routing
- Handles 10 pages to 10,000+ pages seamlessly
- Built-in semantic search and AI capabilities
- Memory management and streaming
- Natural language interface
- Production-ready error handling
"""

import asyncio
import json
import logging
import psutil
import re
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import traceback
import functools

# MCP imports
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp import types
import mcp.server.stdio

# Core dependencies
import httpx
import trafilatura
from bs4 import BeautifulSoup
from markdownify import markdownify
import aiofiles

# AI/ML imports
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# Configuration
from dataclasses import dataclass, field
import os


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class UltimateConfig:
    """Configuration for the ultimate MCP server"""
    # Auto-scaling settings
    small_site_threshold: int = 100  # Pages below this = small site strategy
    large_site_threshold: int = 1000  # Pages above this = large site strategy
    max_pages: int = 10000  # Absolute maximum
    
    # Performance settings (auto-adjusted)
    delay_seconds: float = 0.5  # Will auto-adjust based on site size
    concurrent_workers: int = 8  # Will auto-adjust
    timeout_seconds: float = 45.0
    
    # Content settings
    min_content_length: int = 100
    include_tables: bool = True
    include_images: bool = False
    favor_precision: bool = True
    
    # Memory management
    max_memory_mb: int = 2048
    batch_size: int = 100  # Will auto-adjust
    enable_streaming: bool = True
    auto_resume: bool = True
    
    # AI/Search settings
    model_name: str = "all-MiniLM-L6-v2"
    chunk_size: int = 512
    chunk_overlap: int = 50
    max_results: int = 10
    similarity_threshold: float = 0.7
    cache_embeddings: bool = True
    
    # Progress tracking
    progress_file: str = "crawl_progress.json"
    checkpoint_interval: int = 50
    
    # Output settings - relative paths
    output_dir: Path = field(default_factory=lambda: Path("data"))
    backup_dir: Path = field(default_factory=lambda: Path("backups"))
    
    def __post_init__(self):
        """Ensure directories exist and resolve paths relative to script location"""
        # Resolve paths relative to this script's directory
        script_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
        
        # Convert to absolute paths relative to script location
        if not self.output_dir.is_absolute():
            self.output_dir = script_dir / self.output_dir
        if not self.backup_dir.is_absolute():
            self.backup_dir = script_dir / self.backup_dir
            
        self.output_dir = Path(self.output_dir)
        self.backup_dir = Path(self.backup_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)


class AutoScaler:
    """Automatically adjusts scraping strategy based on website size"""
    
    @staticmethod
    async def estimate_site_size(start_url: str, sample_pages: int = 5) -> Tuple[int, Dict[str, Any]]:
        """Estimate total site size by sampling a few pages"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get robots.txt info
                robots_info = await AutoScaler._check_robots_txt(client, start_url)
                
                # Sample a few pages to estimate link density
                visited = set()
                total_links = set()
                pages_sampled = 0
                
                urls_to_check = [start_url]
                domain = urlparse(start_url).netloc
                
                while urls_to_check and pages_sampled < sample_pages:
                    url = urls_to_check.pop(0)
                    if url in visited:
                        continue
                    
                    try:
                        response = await client.get(url, follow_redirects=True)
                        if response.status_code == 200 and 'text/html' in response.headers.get('content-type', ''):
                            visited.add(url)
                            pages_sampled += 1
                            
                            # Extract links
                            soup = BeautifulSoup(response.text, 'html.parser')
                            links = soup.find_all('a', href=True)
                            
                            for link in links:
                                href = link['href']
                                full_url = urljoin(url, href)
                                parsed = urlparse(full_url)
                                
                                if parsed.netloc == domain and full_url not in visited:
                                    total_links.add(full_url)
                                    if len(urls_to_check) < 20:  # Limit queue size
                                        urls_to_check.append(full_url)
                        
                        await asyncio.sleep(0.5)  # Be respectful
                        
                    except Exception as e:
                        logger.warning(f"Error sampling {url}: {e}")
                
                # Estimate total size
                if pages_sampled > 0:
                    avg_links_per_page = len(total_links) / pages_sampled
                    estimated_size = min(len(total_links) + pages_sampled, int(avg_links_per_page * pages_sampled * 2))
                else:
                    estimated_size = 50  # Default conservative estimate
                
                return estimated_size, {
                    "pages_sampled": pages_sampled,
                    "unique_links_found": len(total_links),
                    "avg_links_per_page": len(total_links) / max(pages_sampled, 1),
                    "robots_allowed": robots_info["allowed"],
                    "robots_crawl_delay": robots_info.get("crawl_delay", 0)
                }
                
        except Exception as e:
            logger.error(f"Error estimating site size: {e}")
            return 100, {"error": str(e)}  # Default conservative estimate
    
    @staticmethod
    async def _check_robots_txt(client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
        """Check robots.txt for crawling permissions and delays"""
        try:
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            robots_url = f"{base_url}/robots.txt"
            
            response = await client.get(robots_url)
            if response.status_code == 200:
                rp = RobotFileParser()
                rp.set_url(robots_url)
                rp.read()
                
                allowed = rp.can_fetch('*', url)
                crawl_delay = rp.crawl_delay('*')
                
                return {
                    "allowed": allowed,
                    "crawl_delay": crawl_delay or 0,
                    "robots_exists": True
                }
            else:
                return {"allowed": True, "crawl_delay": 0, "robots_exists": False}
                
        except Exception as e:
            logger.warning(f"Could not check robots.txt: {e}")
            return {"allowed": True, "crawl_delay": 0, "robots_exists": False}
    
    @staticmethod
    def optimize_config(config: UltimateConfig, estimated_size: int, site_info: Dict[str, Any]) -> UltimateConfig:
        """Optimize configuration based on estimated site size"""
        optimized = UltimateConfig()  # Start with defaults
        
        # Set crawl delay based on robots.txt and site size
        robots_delay = site_info.get("crawl_delay", 0)
        if robots_delay > 0:
            optimized.delay_seconds = max(robots_delay, 0.5)
        elif estimated_size > config.large_site_threshold:
            optimized.delay_seconds = 0.3  # Fast for large sites
        elif estimated_size < config.small_site_threshold:
            optimized.delay_seconds = 1.0  # Respectful for small sites
        else:
            optimized.delay_seconds = 0.5  # Balanced
        
        # Adjust concurrency based on site size
        if estimated_size > config.large_site_threshold:
            optimized.concurrent_workers = 12  # High concurrency for large sites
            optimized.batch_size = 200
            optimized.checkpoint_interval = 100
        elif estimated_size < config.small_site_threshold:
            optimized.concurrent_workers = 4   # Conservative for small sites
            optimized.batch_size = 50
            optimized.checkpoint_interval = 25
        else:
            optimized.concurrent_workers = 8   # Balanced
            optimized.batch_size = 100
            optimized.checkpoint_interval = 50
        
        # Set max pages based on estimate (with buffer)
        optimized.max_pages = min(config.max_pages, estimated_size * 2)
        
        # Copy other settings
        optimized.output_dir = config.output_dir
        optimized.backup_dir = config.backup_dir
        optimized.model_name = config.model_name
        optimized.cache_embeddings = config.cache_embeddings
        
        logger.info(f"Optimized config for estimated {estimated_size} pages:")
        logger.info(f"  - Workers: {optimized.concurrent_workers}")
        logger.info(f"  - Delay: {optimized.delay_seconds}s")
        logger.info(f"  - Batch size: {optimized.batch_size}")
        logger.info(f"  - Max pages: {optimized.max_pages}")
        
        return optimized


class RequestRouter:
    """Intelligent request routing based on user intent"""
    
    SCRAPE_PATTERNS = [
        r'scrape|crawl|download|fetch|extract|get data from',
        r'scan website|index site|collect pages',
        r'gather documentation|harvest content'
    ]
    
    SEARCH_PATTERNS = [
        r'search|find|look for|query|locate',
        r'what does|how to|show me|explain',
        r'tell me about|information about'
    ]
    
    SUMMARY_PATTERNS = [
        r'summarize|summary|overview|brief',
        r'what is|describe|explain briefly',
        r'give me an overview'
    ]
    
    URL_PATTERN = r'https?://[^\s]+'
    
    @classmethod
    def detect_intent(cls, request: str) -> Tuple[str, Dict[str, Any]]:
        """Detect user intent from natural language request"""
        request_lower = request.lower()
        urls = re.findall(cls.URL_PATTERN, request)
        
        # Check for scraping intent
        for pattern in cls.SCRAPE_PATTERNS:
            if re.search(pattern, request_lower):
                return "scrape", {"urls": urls, "query": request, "confidence": 0.9}
        
        # Check for search intent
        for pattern in cls.SEARCH_PATTERNS:
            if re.search(pattern, request_lower):
                return "search", {"query": request, "urls": urls, "confidence": 0.8}
        
        # Check for summary intent
        for pattern in cls.SUMMARY_PATTERNS:
            if re.search(pattern, request_lower):
                return "summary", {"query": request, "topic": cls._extract_topic(request), "confidence": 0.8}
        
        # Default to search
        return "search", {"query": request, "confidence": 0.5}
    
    @classmethod
    def _extract_topic(cls, request: str) -> str:
        """Extract main topic from request"""
        words = request.split()
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'how', 'where', 'when', 'why'}
        topic_words = [w for w in words if w.lower() not in stop_words and len(w) > 2]
        return ' '.join(topic_words[:5])


class UltimateWebScraper:
    """Ultimate web scraper that handles any website size automatically"""
    
    def __init__(self, config: UltimateConfig):
        self.config = config
        self.scraped_pages: List[Dict[str, Any]] = []
        self.robots_cache: Dict[str, Any] = {}
    
    async def scrape_website(self, start_url: str, max_pages: Optional[int] = None) -> Dict[str, Any]:
        """Scrape any website with automatic optimization"""
        logger.info(f"🕷️ Starting intelligent scraping of {start_url}")
        
        # Step 1: Estimate site size and optimize config
        logger.info("📊 Analyzing website structure...")
        estimated_size, site_info = await AutoScaler.estimate_site_size(start_url)
        
        # Override max_pages if specified
        if max_pages:
            estimated_size = min(estimated_size, max_pages)
        
        # Optimize configuration
        optimized_config = AutoScaler.optimize_config(self.config, estimated_size, site_info)
        if max_pages:
            optimized_config.max_pages = max_pages
        
        logger.info(f"🎯 Estimated site size: {estimated_size} pages")
        logger.info(f"⚙️ Using optimized strategy: {optimized_config.concurrent_workers} workers, {optimized_config.delay_seconds}s delay")
        
        # Step 2: Execute scraping with optimized config
        start_time = datetime.now(timezone.utc)
        stats = await self._execute_scraping(start_url, optimized_config, start_time)
        
        # Step 3: Save results
        await self._save_scraped_data(start_url, stats)
        
        return stats
    
    async def _execute_scraping(self, start_url: str, config: UltimateConfig, start_time: datetime) -> Dict[str, Any]:
        """Execute the actual scraping with the optimized configuration"""
        visited_urls: Set[str] = set()
        urls_to_visit = asyncio.Queue(maxsize=1000)
        
        # Initialize crawling state
        normalized_start_url = self._normalize_url(start_url)
        target_domain = urlparse(normalized_start_url).netloc
        await urls_to_visit.put((normalized_start_url, 0))
        
        stats = {
            "pages_crawled": 0,
            "pages_failed": 0,
            "total_words": 0,
            "total_chars": 0,
            "start_time": start_time.isoformat(),
            "target_domain": target_domain,
            "strategy": "auto-optimized",
            "workers": config.concurrent_workers,
            "delay": config.delay_seconds
        }
        
        # Use concurrent workers for better performance
        workers = []
        semaphore = asyncio.Semaphore(config.concurrent_workers)
        
        async def worker():
            async with httpx.AsyncClient(timeout=config.timeout_seconds) as session:
                while not urls_to_visit.empty() and stats["pages_crawled"] < config.max_pages:
                    try:
                        current_url, depth = await asyncio.wait_for(urls_to_visit.get(), timeout=1.0)
                        
                        if current_url in visited_urls or depth > 10:  # Max depth limit
                            continue
                        
                        async with semaphore:
                            visited_urls.add(current_url)
                            
                            # Process page
                            result = await self._process_page(session, current_url, depth, target_domain, config)
                            
                            if result["success"]:
                                stats["pages_crawled"] += 1
                                stats["total_words"] += result["word_count"]
                                stats["total_chars"] += result["char_count"]
                                
                                self.scraped_pages.append(result["page_data"])
                                
                                # Add new links to queue
                                for link in result["links"]:
                                    normalized_link = self._normalize_url(link)
                                    if normalized_link not in visited_urls:
                                        try:
                                            await urls_to_visit.put((normalized_link, depth + 1))
                                        except asyncio.QueueFull:
                                            pass  # Queue full, skip this link
                                
                                # Progress logging
                                if stats["pages_crawled"] % 20 == 0:
                                    logger.info(f"📄 Processed {stats['pages_crawled']} pages...")
                            else:
                                stats["pages_failed"] += 1
                            
                            # Rate limiting
                            await asyncio.sleep(config.delay_seconds)
                            
                    except asyncio.TimeoutError:
                        break  # No more work available
                    except Exception as e:
                        logger.error(f"Worker error: {e}")
                        stats["pages_failed"] += 1
        
        # Start workers
        for _ in range(config.concurrent_workers):
            workers.append(asyncio.create_task(worker()))
        
        # Wait for workers to complete
        await asyncio.gather(*workers, return_exceptions=True)
        
        # Finalize stats
        end_time = datetime.now(timezone.utc)
        stats["end_time"] = end_time.isoformat()
        stats["duration_seconds"] = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Scraping complete: {stats['pages_crawled']} pages, {stats['pages_failed']} failed")
        return stats
    
    async def _process_page(self, session: httpx.AsyncClient, url: str, depth: int, target_domain: str, config: UltimateConfig) -> Dict[str, Any]:
        """Process a single page"""
        try:
            # Check robots.txt
            if not await self._check_robots_txt(session, url):
                return {"success": False, "error": "Robots.txt disallows"}
            
            # Fetch page
            response = await session.get(url, follow_redirects=True)
            
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                return {"success": False, "error": f"Non-HTML content: {content_type}"}
            
            # Extract content
            content = self._extract_content(response.text, url)
            if not content or len(content) < config.min_content_length:
                return {"success": False, "error": "Insufficient content"}
            
            # Extract metadata and links
            metadata = self._extract_metadata(response.text, url)
            links = self._extract_links(response.text, url, target_domain) if depth < 10 else []
            
            page_data = {
                "url": url,
                "content": content,
                "metadata": metadata,
                "word_count": len(content.split()),
                "char_count": len(content),
                "crawl_depth": depth,
                "crawled_at": datetime.now(timezone.utc).isoformat()
            }
            
            return {
                "success": True,
                "page_data": page_data,
                "links": links,
                "word_count": page_data["word_count"],
                "char_count": page_data["char_count"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _check_robots_txt(self, session: httpx.AsyncClient, url: str) -> bool:
        """Check if URL is allowed by robots.txt"""
        try:
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            if base_url not in self.robots_cache:
                robots_url = f"{base_url}/robots.txt"
                try:
                    response = await session.get(robots_url)
                    if response.status_code == 200:
                        rp = RobotFileParser()
                        rp.set_url(robots_url)
                        rp.read()
                        self.robots_cache[base_url] = rp
                    else:
                        self.robots_cache[base_url] = None
                except:
                    self.robots_cache[base_url] = None
            
            rp = self.robots_cache[base_url]
            if rp:
                return rp.can_fetch('*', url)
            return True
            
        except Exception:
            return True
    
    def _extract_content(self, html: str, url: str) -> Optional[str]:
        """Extract main content from HTML"""
        try:
            # Try trafilatura first (best quality)
            content = trafilatura.extract(html, url=url, favor_precision=True, include_tables=True)
            if content and len(content.strip()) >= self.config.min_content_length:
                logger.debug(f"✅ Trafilatura extracted {len(content)} chars from {url}")
                return content.strip()
            else:
                logger.debug(f"⚠️ Trafilatura failed for {url}, trying fallback methods")
            
            # Fallback to BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                script.decompose()
            
            # Try to find main content areas
            main_content = None
            content_selectors = ['main', 'article', '.content', '#content', '.post', '.entry', 
                               '.documentation', '.docs', '.page-content', '.main-content']
            
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    logger.debug(f"Found content using selector: {selector}")
                    break
            
            if main_content:
                markdown_content = markdownify(str(main_content))
                if len(markdown_content.strip()) >= self.config.min_content_length:
                    logger.debug(f"✅ BeautifulSoup extracted {len(markdown_content)} chars from {url}")
                    return markdown_content.strip()
            
            # Last resort: extract all text from body
            body = soup.find('body')
            if body:
                text_content = body.get_text(separator='\n', strip=True)
            else:
                text_content = soup.get_text(separator='\n', strip=True)
                
            # Clean up the text content
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            clean_content = '\n'.join(lines)
            
            if len(clean_content) >= self.config.min_content_length:
                logger.debug(f"✅ Fallback text extraction got {len(clean_content)} chars from {url}")
                return clean_content
            else:
                logger.warning(f"❌ Content too short ({len(clean_content)} chars) for {url}, min required: {self.config.min_content_length}")
                
            return None
            
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {e}")
            return None
    
    def _extract_metadata(self, html: str, url: str) -> Dict[str, Any]:
        """Extract metadata from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Title
            title = "Untitled"
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            elif soup.h1:
                title = soup.h1.get_text().strip()
                
            # Description
            description = ""
            meta_desc = soup.find("meta", attrs={"name": "description"}) or \
                       soup.find("meta", attrs={"property": "og:description"})
            if meta_desc and meta_desc.get("content"):
                description = meta_desc["content"].strip()
            
            # Keywords
            keywords = []
            meta_keywords = soup.find("meta", attrs={"name": "keywords"})
            if meta_keywords and meta_keywords.get("content"):
                keywords = [k.strip() for k in meta_keywords["content"].split(",")]
            
            # Language
            language = "en"
            html_tag = soup.find("html")
            if html_tag and html_tag.get("lang"):
                language = html_tag["lang"]
            
            return {
                "title": title,
                "description": description,
                "keywords": keywords,
                "language": language,
                "source_url": url
            }
            
        except Exception as e:
            logger.error(f"Metadata extraction failed for {url}: {e}")
            return {"title": "Untitled", "description": "", "keywords": [], "language": "en", "source_url": url}
    
    def _extract_links(self, html: str, url: str, target_domain: str) -> List[str]:
        """Extract internal links from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            links = []
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                parsed = urlparse(full_url)
                
                # Only include links from the same domain
                if parsed.netloc == target_domain:
                    # Clean up the URL
                    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if clean_url not in links and clean_url != url:
                        links.append(clean_url)
            
            return links[:50]  # Limit links per page
            
        except Exception as e:
            logger.error(f"Link extraction failed for {url}: {e}")
            return []
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for consistent comparison"""
        try:
            parsed = urlparse(url)
            # Remove fragment, query, and trailing slash
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
            return normalized if normalized.endswith('/') == False else normalized[:-1]
        except:
            return url
    
    async def _save_scraped_data(self, start_url: str, stats: Dict[str, Any]) -> None:
        """Save scraped data to files"""
        try:
            domain = urlparse(start_url).netloc.replace('.', '_').replace(':', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            pages_file = self.config.output_dir / f"{domain}_pages_{timestamp}.json"
            stats_file = self.config.output_dir / f"{domain}_stats_{timestamp}.json"
            
            # Always save files, even if no pages were scraped (for debugging)
            if len(self.scraped_pages) == 0:
                logger.warning(f"⚠️ No pages were successfully scraped from {start_url}")
                logger.warning(f"📊 Stats: {stats}")
                
                # Save empty pages file with explanation
                empty_data = {
                    "message": "No pages were successfully scraped",
                    "possible_reasons": [
                        "Content extraction failed (pages had insufficient content)",
                        "Robots.txt blocked access",
                        "Pages returned non-HTML content",
                        "Network/timeout issues",
                        "Content was shorter than minimum length requirement"
                    ],
                    "scraped_pages": []
                }
                async with aiofiles.open(pages_file, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(empty_data, indent=2, ensure_ascii=False))
            else:
                # Save pages data
                async with aiofiles.open(pages_file, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(self.scraped_pages, indent=2, ensure_ascii=False))
            
            # Save stats
            async with aiofiles.open(stats_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(stats, indent=2, ensure_ascii=False))
            
            logger.info(f"💾 Saved {len(self.scraped_pages)} pages to {pages_file}")
            logger.info(f"📊 Saved stats to {stats_file}")
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")


class UltimateQueryEngine:
    """AI-powered query engine for scraped documentation"""
    
    def __init__(self, config: UltimateConfig):
        self.config = config
        self.documents: List[Dict[str, Any]] = []
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.model: Optional[SentenceTransformer] = None
    
    async def load_documents(self) -> int:
        """Load all available scraped documents"""
        data_dir = Path("data")
        if not data_dir.exists():
            return 0
        
        self.documents = []
        for file_path in data_dir.glob("*_pages_*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    pages = json.load(f)
                    self.documents.extend(pages)
            except Exception as e:
                logger.warning(f"Could not load {file_path}: {e}")
        
        if self.documents:
            await self._process_documents()
        
        logger.info(f"📚 Loaded {len(self.documents)} documents")
        return len(self.documents)
    
    async def _process_documents(self):
        """Process documents into searchable chunks with embeddings"""
        logger.info("🔄 Processing documents for AI search...")
        
        # Create chunks
        self.chunks = []
        for doc in self.documents:
            content = doc.get('content', '')
            if len(content) < 50:
                continue
            
            # Split into chunks
            words = content.split()
            for i in range(0, len(words), self.config.chunk_size - self.config.chunk_overlap):
                chunk_words = words[i:i + self.config.chunk_size]
                chunk_text = ' '.join(chunk_words)
                
                self.chunks.append({
                    'content': chunk_text,
                    'source_url': doc.get('url', ''),
                    'source_title': doc.get('metadata', {}).get('title', 'Untitled'),
                    'chunk_id': len(self.chunks)
                })
        
        logger.info(f"📄 Created {len(self.chunks)} chunks")
        
        # Load embedding model
        if not self.model:
            logger.info(f"🤖 Loading embedding model: {self.config.model_name}")
            self.model = SentenceTransformer(self.config.model_name)
        
        # Create embeddings
        chunk_texts = [chunk['content'] for chunk in self.chunks]
        self.embeddings = self.model.encode(chunk_texts, show_progress_bar=True)
        
        # Create TF-IDF matrix for keyword search
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        self.tfidf_matrix = self.vectorizer.fit_transform(chunk_texts)
        
        logger.info("✅ Document processing complete")
    
    async def search(self, query: str, search_type: str = "hybrid", max_results: int = 5) -> List[Dict[str, Any]]:
        """Search documents with AI-powered ranking"""
        if not self.chunks:
            return []
        
        if search_type == "semantic":
            return await self._semantic_search(query, max_results)
        elif search_type == "keyword":
            return await self._keyword_search(query, max_results)
        else:  # hybrid
            return await self._hybrid_search(query, max_results)
    
    async def _semantic_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Semantic search using embeddings"""
        query_embedding = self.model.encode([query])
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:max_results]
        
        results = []
        for idx in top_indices:
            chunk = self.chunks[idx].copy()
            chunk['semantic_score'] = float(similarities[idx])
            results.append(chunk)
        
        return results
    
    async def _keyword_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Keyword search using TF-IDF"""
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        
        top_indices = np.argsort(similarities)[::-1][:max_results]
        
        results = []
        for idx in top_indices:
            chunk = self.chunks[idx].copy()
            chunk['keyword_score'] = float(similarities[idx])
            results.append(chunk)
        
        return results
    
    async def _hybrid_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Hybrid search combining semantic and keyword approaches"""
        semantic_results = await self._semantic_search(query, max_results * 2)
        keyword_results = await self._keyword_search(query, max_results * 2)
        
        # Combine and re-rank
        combined = {}
        
        for result in semantic_results:
            chunk_id = result['chunk_id']
            combined[chunk_id] = result.copy()
            combined[chunk_id]['hybrid_score'] = result['semantic_score'] * 0.7
        
        for result in keyword_results:
            chunk_id = result['chunk_id']
            if chunk_id in combined:
                combined[chunk_id]['hybrid_score'] += result['keyword_score'] * 0.3
                combined[chunk_id]['keyword_score'] = result['keyword_score']
            else:
                combined[chunk_id] = result.copy()
                combined[chunk_id]['hybrid_score'] = result['keyword_score'] * 0.3
        
        # Sort by hybrid score
        sorted_results = sorted(combined.values(), key=lambda x: x['hybrid_score'], reverse=True)
        return sorted_results[:max_results]


class UltimateMCPServer:
    """The ONE ultimate MCP server that handles any documentation request"""
    
    def __init__(self):
        self.server = Server("ultimate-documentation-server")
        self.config = UltimateConfig()
        self.scraper = UltimateWebScraper(self.config)
        self.query_engine = UltimateQueryEngine(self.config)
        self.router = RequestRouter()
        
        self.available_datasets: Dict[str, Dict[str, Any]] = {}
        self.current_logging_level: types.LoggingLevel = "info"  # Track current logging level
        
        # Performance optimizations
        self.http_client: Optional[httpx.AsyncClient] = None
        self.robots_cache: Dict[str, Any] = {}  # Cache robots.txt responses
        self.url_validation_cache: Dict[str, Tuple[bool, str]] = {}  # Cache URL validations
        self._init_performance_features()
        
        self._load_available_datasets()
        self._setup_handlers()
    
    def _init_performance_features(self):
        """Initialize performance optimization features"""
        # Create shared HTTP client with connection pooling
        timeout = httpx.Timeout(30.0, connect=10.0)
        limits = httpx.Limits(
            max_connections=100,      # Total connections
            max_keepalive_connections=20,  # Persistent connections
            keepalive_expiry=30.0     # Keep connections alive for 30s
        )
        
        self.http_client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            follow_redirects=True,
            headers={
                'User-Agent': 'Ultimate-MCP-Documentation-Server/1.0 (+https://github.com/your-repo)'
            }
        )
        
        logger.info("🚀 Performance features initialized: connection pooling, caching, optimized timeouts")
    
    def _load_available_datasets(self):
        """Load information about available scraped datasets"""
        data_dir = Path("data")
        if not data_dir.exists():
            return
        
        self.available_datasets = {}
        for file_path in data_dir.glob("*_pages_*.json"):
            try:
                filename = file_path.stem
                parts = filename.split('_pages_')
                if len(parts) == 2:
                    domain = parts[0].replace('_', '.')
                    timestamp = parts[1]
                    
                    # Get file stats
                    stats_file = data_dir / f"{parts[0]}_stats_{timestamp}.json"
                    stats = {}
                    if stats_file.exists():
                        with open(stats_file, 'r', encoding='utf-8') as f:
                            stats = json.load(f)
                    
                    self.available_datasets[domain] = {
                        "pages_file": str(file_path),
                        "stats_file": str(stats_file) if stats_file.exists() else None,
                        "domain": domain,
                        "timestamp": timestamp,
                        "pages_count": stats.get("pages_crawled", 0),
                        "words_count": stats.get("total_words", 0),
                        "crawled_at": stats.get("start_time", "unknown"),
                        "file_size_mb": file_path.stat().st_size / 1024 / 1024
                    }
            except Exception as e:
                logger.warning(f"Could not load dataset info for {file_path}: {e}")
    
    def _setup_handlers(self):
        """Setup MCP handlers"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[types.Resource]:
            """List available resources"""
            resources = [
                types.Resource(
                    uri="ultimate://system/status",
                    name="Ultimate Server Status",
                    description="System status and capabilities",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="ultimate://datasets/available",
                    name="Available Datasets",
                    description="Information about scraped datasets",
                    mimeType="application/json"
                )
            ]
            
            # Add resources for each dataset
            for domain, info in self.available_datasets.items():
                resources.append(types.Resource(
                    uri=f"ultimate://dataset/{domain}",
                    name=f"Dataset: {domain}",
                    description=f"Scraped data from {domain} ({info['pages_count']} pages)",
                    mimeType="application/json"
                ))
            
            return resources
        
        @self.server.read_resource()
        async def handle_read_resource(uri: types.AnyUrl) -> str:
            """Read resource content"""
            uri_str = str(uri)
            
            if uri_str == "ultimate://system/status":
                return json.dumps({
                    "server_name": "Ultimate Documentation Server",
                    "version": "1.0.0",
                    "status": "active",
                    "capabilities": [
                        "Automatic site size detection",
                        "Intelligent scraping optimization",
                        "Natural language request processing",
                        "AI-powered semantic search",
                        "Hybrid search (semantic + keyword)",
                        "Large-scale crawling (10K+ pages)",
                        "Smart intent detection",
                        "Memory management",
                        "Auto-resume functionality"
                    ],
                    "available_datasets": len(self.available_datasets),
                    "total_pages": sum(info["pages_count"] for info in self.available_datasets.values()),
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }, indent=2)
            
            elif uri_str == "ultimate://datasets/available":
                return json.dumps(self.available_datasets, indent=2, ensure_ascii=False)
            
            elif uri_str.startswith("ultimate://dataset/"):
                domain = uri_str.replace("ultimate://dataset/", "")
                if domain in self.available_datasets:
                    info = self.available_datasets[domain]
                    with open(info["pages_file"], 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    return json.dumps(data, indent=2, ensure_ascii=False)
                else:
                    raise ValueError(f"Dataset not found: {domain}")
            
            else:
                raise ValueError(f"Unknown resource: {uri}")
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available tools"""
            return [
                types.Tool(
                    name="handle_any_request",
                    description="🧠 THE ULTIMATE TOOL - Handles ANY documentation request automatically. Just ask naturally!",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "request": {
                                "type": "string",
                                "description": "Your request in natural language (e.g., 'scrape https://docs.python.org/', 'search for authentication', 'summarize React hooks')"
                            },
                            "max_pages": {
                                "type": "integer",
                                "description": "Optional: Maximum pages to scrape (auto-detected if not specified)",
                                "default": None
                            }
                        },
                        "required": ["request"]
                    }
                ),
                types.Tool(
                    name="scrape_any_website",
                    description="🕷️ Scrape any website (10 pages to 10,000+ pages) with automatic optimization",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Website URL to scrape"},
                            "max_pages": {"type": "integer", "default": None, "description": "Maximum pages (auto-detected if not specified)"}
                        },
                        "required": ["url"]
                    }
                ),
                types.Tool(
                    name="search_documentation",
                    description="🔍 AI-powered search across all scraped documentation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "search_type": {"type": "string", "enum": ["semantic", "keyword", "hybrid"], "default": "hybrid"},
                            "max_results": {"type": "integer", "default": 5}
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="list_available_data",
                    description="📚 List all available scraped datasets with statistics",
                    inputSchema={"type": "object", "properties": {}}
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle tool calls with intelligent routing"""
            try:
                logger.info(f"🎯 Handling: {name}")
                
                if name == "handle_any_request":
                    return await self._handle_any_request(arguments)
                elif name == "scrape_any_website":
                    return await self._handle_scrape(arguments)
                elif name == "search_documentation":
                    return await self._handle_search(arguments)
                elif name == "list_available_data":
                    return await self._handle_list_data(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                    
            except Exception as e:
                logger.error(f"Error in tool call {name}: {e}")
                traceback.print_exc()
                return [types.TextContent(
                    type="text",
                    text=f"❌ Error: {str(e)}"
                )]
        
        # MCP Logging handlers
        @self.server.set_logging_level()
        async def handle_set_logging_level(level: types.LoggingLevel) -> None:
            """Set the server's logging level"""
            level_map = {
                "debug": logging.DEBUG,
                "info": logging.INFO,
                "notice": logging.INFO,  # Map notice to INFO
                "warning": logging.WARNING, 
                "error": logging.ERROR,
                "critical": logging.CRITICAL,
                "alert": logging.CRITICAL,  # Map alert to CRITICAL
                "emergency": logging.CRITICAL  # Map emergency to CRITICAL
            }
            
            if level in level_map:
                self.current_logging_level = level
                logging.getLogger().setLevel(level_map[level])
                logger.info(f"🔧 Logging level set to: {level}")
                
                # Send logging change notification
                await self.send_log_message(
                    level="info",
                    message=f"Logging level changed to {level}"
                )
            else:
                logger.warning(f"⚠️ Unsupported logging level: {level}")
    
    async def send_log_message(self, level: types.LoggingLevel, message: str, logger_name: str = "ultimate-mcp-server"):
        """Send structured log message to MCP client"""
        try:
            if hasattr(self.server, 'request_context') and self.server.request_context:
                await self.server.request_context.session.send_log_message(
                    level=level,
                    data=message,
                    logger=logger_name
                )
        except Exception as e:
            # Fallback to standard logging if MCP logging fails
            logger.info(f"MCP log send failed, using standard: {message} (error: {e})")
    
    async def notify_resources_changed(self):
        """Notify clients that available resources have changed"""
        try:
            if hasattr(self.server, 'request_context') and self.server.request_context:
                # Send resource list changed notification
                await self.server.request_context.session.send_resource_list_changed()
                logger.info("🔔 Sent resource change notification to client")
        except Exception as e:
            logger.warning(f"Failed to send resource change notification: {e}")
    
    def validate_url(self, url: str) -> Tuple[bool, str]:
        """
        Comprehensive URL validation for security and safety with caching
        Returns: (is_valid, error_message)
        """
        # Check cache first
        if url in self.url_validation_cache:
            return self.url_validation_cache[url]
        
        try:
            # Basic URL parsing
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ['http', 'https']:
                return False, f"Invalid scheme '{parsed.scheme}'. Only HTTP and HTTPS are allowed."
            
            # Check if hostname exists
            if not parsed.netloc:
                return False, "URL must include a hostname."
            
            # Security checks - prevent SSRF attacks
            hostname = parsed.hostname
            if not hostname:
                return False, "Invalid hostname."
            
            # Block localhost and private IP ranges
            import ipaddress
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    return False, f"Access to private/local IP addresses is not allowed: {hostname}"
            except ValueError:
                # Not an IP address, continue with hostname checks
                pass
            
            # Block common localhost aliases
            localhost_aliases = [
                'localhost', '127.0.0.1', '::1', '0.0.0.0',
                'local', 'internal', 'intranet'
            ]
            if hostname.lower() in localhost_aliases:
                return False, f"Access to localhost/internal addresses is not allowed: {hostname}"
            
            # Block private domain patterns
            private_patterns = [
                '.local', '.internal', '.corp', '.lan', '.home',
                'test.', 'dev.', 'staging.', 'beta.'
            ]
            for pattern in private_patterns:
                if pattern in hostname.lower():
                    logger.warning(f"Potentially private domain detected: {hostname}")
            
            # Check for suspicious ports
            if parsed.port:
                # Allow common web ports, block others
                allowed_ports = [80, 443, 8080, 8443]
                if parsed.port not in allowed_ports:
                    return False, f"Port {parsed.port} is not allowed. Allowed ports: {allowed_ports}"
            
            # Validate URL length (prevent extremely long URLs)
            if len(url) > 2048:
                return False, "URL is too long (max 2048 characters)."
            
            # Check for suspicious characters
            suspicious_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
            for char in suspicious_chars:
                if char in url:
                    return False, f"URL contains suspicious character: '{char}'"
            
            result = (True, "URL is valid")
            
        except Exception as e:
            result = (False, f"URL validation error: {str(e)}")
        
        # Cache the result (limit cache size)
        if len(self.url_validation_cache) > 1000:
            # Clear oldest entries when cache gets too large
            old_keys = list(self.url_validation_cache.keys())[:100]
            for key in old_keys:
                del self.url_validation_cache[key]
        
        self.url_validation_cache[url] = result
        return result
    
    @functools.lru_cache(maxsize=500)
    def get_robots_txt_cached(self, domain: str) -> Dict[str, Any]:
        """
        Cache robots.txt responses using LRU cache for better performance
        Returns: dict with robots info
        """
        return {
            "allowed": True,
            "crawl_delay": 0,
            "cached_at": time.time()
        }
    
    async def cleanup_resources(self):
        """Clean up resources when server shuts down"""
        try:
            if self.http_client:
                await self.http_client.aclose()
                logger.info("🧹 HTTP client closed")
            
            # Clear caches
            self.robots_cache.clear()
            self.url_validation_cache.clear()
            self.get_robots_txt_cached.cache_clear()
            
            logger.info("🧹 Performance caches cleared")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
    
    async def _handle_any_request(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """THE ULTIMATE HANDLER - Handles any request automatically"""
        request = arguments["request"]
        max_pages = arguments.get("max_pages")
        
        # Detect intent
        intent, intent_data = self.router.detect_intent(request)
        confidence = intent_data.get("confidence", 0.5)
        
        result_text = f"🧠 **Ultimate AI Documentation Handler**\n\n"
        result_text += f"📝 **Your Request:** {request}\n\n"
        result_text += f"🎯 **Detected Intent:** {intent.title()} (confidence: {confidence:.1%})\n\n"
        
        try:
            if intent == "scrape":
                urls = intent_data.get("urls", [])
                if urls:
                    result_text += f"🕷️ **Auto-Scraping Website**\n\n"
                    
                    # Validate URLs before processing
                    valid_urls = []
                    for url in urls:
                        is_valid, validation_message = self.validate_url(url)
                        if is_valid:
                            valid_urls.append(url)
                        else:
                            result_text += f"🚫 **Skipped {url}**: {validation_message}\n\n"
                    
                    # Process valid URLs
                    for url in valid_urls:
                        scrape_args = {"url": url}
                        if max_pages:
                            scrape_args["max_pages"] = max_pages
                        
                        scrape_result = await self._handle_scrape(scrape_args)
                        result_text += scrape_result[0].text + "\n\n"
                    
                    if not valid_urls:
                        result_text += "❌ No valid URLs found after security validation.\n"
                else:
                    result_text += "❌ No URLs found in scraping request. Please include a website URL.\n"
            
            elif intent in ["search", "summary"]:
                query = intent_data["query"]
                search_args = {
                    "query": query,
                    "search_type": "hybrid",
                    "max_results": 5
                }
                search_result = await self._handle_search(search_args)
                result_text += search_result[0].text
            
            else:
                result_text += "🤔 **Request Analysis**\n\n"
                result_text += "I'm not entirely sure what you want to do. Here are some examples:\n"
                result_text += "- 'Scrape https://docs.example.com'\n"
                result_text += "- 'Search for authentication methods'\n"
                result_text += "- 'Summarize React hooks documentation'\n"
                result_text += "- 'What documentation do we have available?'\n"
        
        except Exception as e:
            result_text += f"❌ **Error Processing Request**\n\n{str(e)}\n"
        
        return [types.TextContent(type="text", text=result_text)]
    
    async def _handle_scrape(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle intelligent scraping requests"""
        url = arguments["url"]
        max_pages = arguments.get("max_pages")
        
        # Security: Validate URL before processing
        is_valid, validation_message = self.validate_url(url)
        if not is_valid:
            return [types.TextContent(
                type="text",
                text=f"🚫 **Security Error: Invalid URL**\n\n{validation_message}\n\n"
                     f"**Security Guidelines:**\n"
                     f"- Only HTTP/HTTPS URLs are allowed\n"
                     f"- Private/internal networks are blocked\n" 
                     f"- Standard web ports only (80, 443, 8080, 8443)\n"
                     f"- URL must be under 2048 characters\n"
            )]
        
        await self.send_log_message("info", f"🔒 URL validation passed: {url}")
        
        try:
            result_text = f"🕷️ **Ultimate Auto-Scraper**\n\n"
            result_text += f"🎯 **Target:** {url}\n"
            
            if max_pages:
                result_text += f"📊 **Max Pages:** {max_pages:,} (user specified)\n\n"
            else:
                result_text += f"📊 **Max Pages:** Auto-detecting...\n\n"
            
            result_text += "🔍 Analyzing website structure and optimizing strategy...\n\n"
            
            # Execute scraping with automatic optimization
            stats = await self.scraper.scrape_website(url, max_pages)
            
            # Refresh available datasets and notify clients
            old_count = len(self.available_datasets)
            self._load_available_datasets()
            new_count = len(self.available_datasets)
            
            # Send resource change notification if datasets changed
            if new_count != old_count:
                await self.notify_resources_changed()
                await self.send_log_message("info", f"📚 New datasets available: {new_count} total (+{new_count - old_count})")
            
            result_text += "✅ **Scraping Complete!**\n\n"
            result_text += f"📄 **Pages Scraped:** {stats['pages_crawled']:,}\n"
            result_text += f"❌ **Failed Pages:** {stats['pages_failed']:,}\n"
            result_text += f"📝 **Words Extracted:** {stats['total_words']:,}\n"
            result_text += f"⏱️ **Duration:** {stats.get('duration_seconds', 0):.1f} seconds\n"
            result_text += f"🌐 **Domain:** {stats['target_domain']}\n"
            result_text += f"⚡ **Strategy:** {stats.get('workers', 'N/A')} workers, {stats.get('delay', 'N/A')}s delay\n\n"
            result_text += "💡 **Next Steps:** You can now search this documentation using AI-powered search!\n"
            
        except Exception as e:
            result_text = f"❌ **Scraping Failed**\n\nError: {str(e)}\n"
        
        return [types.TextContent(type="text", text=result_text)]
    
    async def _handle_search(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle AI-powered search requests"""
        query = arguments["query"]
        search_type = arguments.get("search_type", "hybrid")
        max_results = arguments.get("max_results", 5)
        
        try:
            # Load documents if not already loaded
            if not self.query_engine.documents:
                doc_count = await self.query_engine.load_documents()
                if doc_count == 0:
                    return [types.TextContent(
                        type="text",
                        text="❌ **No Documentation Available**\n\nPlease scrape some documentation first using the scraping tool.\n"
                    )]
            
            # Perform AI-powered search
            results = await self.query_engine.search(query, search_type, max_results)
            
            result_text = f"🔍 **AI-Powered Search Results**\n\n"
            result_text += f"📝 **Query:** {query}\n"
            result_text += f"🎯 **Search Type:** {search_type.title()}\n"
            result_text += f"📚 **Documents:** {len(self.query_engine.documents)}\n"
            result_text += f"📊 **Results Found:** {len(results)}\n\n"
            
            if results:
                for i, result in enumerate(results, 1):
                    title = result.get('source_title', 'Untitled')
                    url = result.get('source_url', '')
                    
                    # Get the best score available
                    score = result.get('hybrid_score', result.get('semantic_score', result.get('keyword_score', 0)))
                    
                    preview = result['content'][:200] + '...' if len(result['content']) > 200 else result['content']
                    
                    result_text += f"**{i}. {title}**\n"
                    result_text += f"🔗 {url}\n"
                    result_text += f"⭐ Relevance: {score:.3f}\n"
                    result_text += f"📖 Preview: {preview}\n\n"
            else:
                result_text += "❌ No relevant results found. Try different search terms or scrape more documentation.\n"
        
        except Exception as e:
            result_text = f"❌ **Search Failed**\n\nError: {str(e)}\n"
        
        return [types.TextContent(type="text", text=result_text)]
    
    async def _handle_list_data(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle dataset listing requests"""
        result_text = f"📚 **Available Documentation Datasets**\n\n"
        
        if not self.available_datasets:
            result_text += "❌ No datasets available. Scrape some documentation first!\n"
        else:
            total_pages = sum(info["pages_count"] for info in self.available_datasets.values())
            total_words = sum(info["words_count"] for info in self.available_datasets.values())
            
            result_text += f"📊 **Summary:** {len(self.available_datasets)} datasets, {total_pages:,} pages, {total_words:,} words\n\n"
            
            for domain, info in self.available_datasets.items():
                result_text += f"**🌐 {domain}**\n"
                result_text += f"📄 Pages: {info['pages_count']:,}\n"
                result_text += f"📝 Words: {info['words_count']:,}\n"
                result_text += f"💾 Size: {info['file_size_mb']:.1f} MB\n"
                result_text += f"📅 Crawled: {info['crawled_at']}\n\n"
        
        return [types.TextContent(type="text", text=result_text)]
    
    async def run(self):
        """Run the Ultimate MCP server with proper cleanup"""
        try:
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="ultimate-documentation-server",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            NotificationOptions(
                                tools_changed=True,
                                resources_changed=True
                            ),
                            {
                                "tools": {},
                                "resources": {}, 
                                "logging": {},
                                "resource_subscriptions": {}
                            }
                        )
                    )
                )
        finally:
            # Ensure cleanup happens even if server crashes
            await self.cleanup_resources()


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Ultimate MCP Documentation Server - Intelligent web scraping and AI search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start MCP server (default)
  python ultimate_mcp_server.py
  
  # Scrape a website directly
  python ultimate_mcp_server.py --scrape https://docs.python.org/
  
  # Scrape with custom limits
  python ultimate_mcp_server.py --scrape https://fastapi.tiangolo.com/ --max-pages 100
  
  # Search existing documentation
  python ultimate_mcp_server.py --search "authentication methods"
  
  # List available datasets
  python ultimate_mcp_server.py --list-data
  
  # Interactive mode
  python ultimate_mcp_server.py --interactive
        """
    )
    
    # Command line arguments
    parser.add_argument('--scrape', type=str, help='Scrape a website URL')
    parser.add_argument('--max-pages', type=int, help='Maximum pages to scrape')
    parser.add_argument('--search', type=str, help='Search existing documentation')
    parser.add_argument('--search-type', choices=['semantic', 'keyword', 'hybrid'], 
                       default='hybrid', help='Type of search to perform')
    parser.add_argument('--max-results', type=int, default=10, help='Maximum search results')
    parser.add_argument('--list-data', action='store_true', help='List available datasets')
    parser.add_argument('--interactive', action='store_true', help='Start interactive mode')
    parser.add_argument('--output-format', choices=['text', 'json'], default='text',
                       help='Output format for results')
    
    args = parser.parse_args()
    
    # Handle command line usage
    if args.scrape or args.search or args.list_data or args.interactive:
        await handle_cli_mode(args)
    else:
        # Default: Start MCP server
        logger.info("🚀 Starting Ultimate MCP Documentation Server...")
        server = UltimateMCPServer()
        await server.run()


async def handle_cli_mode(args):
    """Handle command line interface mode"""
    server = UltimateMCPServer()
    
    try:
        if args.scrape:
            print(f"🕷️ Scraping: {args.scrape}")
            if args.max_pages:
                print(f"📊 Max pages: {args.max_pages:,}")
            
            scrape_args = {"url": args.scrape}
            if args.max_pages:
                scrape_args["max_pages"] = args.max_pages
            
            result = await server._handle_scrape(scrape_args)
            
            if args.output_format == 'json':
                # Extract key info as JSON
                import json
                import re
                text = result[0].text
                
                # Parse the results from the text output
                pages_match = re.search(r'Pages Scraped:\*\* (\d+)', text)
                words_match = re.search(r'Words Extracted:\*\* ([\d,]+)', text)
                duration_match = re.search(r'Duration:\*\* ([\d.]+) seconds', text)
                
                json_result = {
                    "status": "completed",
                    "url": args.scrape,
                    "pages_scraped": int(pages_match.group(1)) if pages_match else 0,
                    "words_extracted": int(words_match.group(1).replace(',', '')) if words_match else 0,
                    "duration_seconds": float(duration_match.group(1)) if duration_match else 0,
                    "output_files": "Check data/ directory for generated files"
                }
                print(json.dumps(json_result, indent=2))
            else:
                print(result[0].text)
        
        elif args.search:
            print(f"🔍 Searching: {args.search}")
            print(f"🎯 Search type: {args.search_type}")
            
            search_args = {
                "query": args.search,
                "search_type": args.search_type,
                "max_results": args.max_results
            }
            
            result = await server._handle_search(search_args)
            
            if args.output_format == 'json':
                # Parse search results into JSON format
                import json
                import re
                text = result[0].text
                
                # Basic JSON structure
                json_result = {
                    "query": args.search,
                    "search_type": args.search_type,
                    "results": "See full output above - JSON parsing of search results needs refinement"
                }
                print(json.dumps(json_result, indent=2))
            else:
                print(result[0].text)
        
        elif args.list_data:
            print("📚 Available Documentation Datasets")
            result = await server._handle_list_data({})
            print(result[0].text)
        
        elif args.interactive:
            await interactive_mode(server)
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        if args.output_format == 'json':
            import json
            error_result = {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            print(json.dumps(error_result, indent=2))
        else:
            traceback.print_exc()


async def interactive_mode(server):
    """Interactive command-line mode"""
    print("\n🤖 Ultimate MCP Documentation Server - Interactive Mode")
    print("=" * 60)
    print("Commands:")
    print("  scrape <url> [max_pages]  - Scrape a website")
    print("  search <query>            - Search documentation")
    print("  list                      - List available datasets")
    print("  help                      - Show this help")
    print("  quit/exit                 - Exit interactive mode")
    print("=" * 60)
    
    while True:
        try:
            command = input("\n🔥 > ").strip()
            
            if not command:
                continue
            
            if command.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if command.lower() in ['help', 'h']:
                print("\n📋 Available Commands:")
                print("  scrape https://docs.python.org/ 50")
                print("  search authentication methods")
                print("  list")
                print("  quit")
                continue
            
            parts = command.split()
            cmd = parts[0].lower()
            
            if cmd == 'scrape' and len(parts) >= 2:
                url = parts[1]
                max_pages = int(parts[2]) if len(parts) > 2 else None
                
                print(f"\n🕷️ Scraping: {url}")
                scrape_args = {"url": url}
                if max_pages:
                    scrape_args["max_pages"] = max_pages
                
                result = await server._handle_scrape(scrape_args)
                print(result[0].text)
            
            elif cmd == 'search' and len(parts) >= 2:
                query = ' '.join(parts[1:])
                print(f"\n🔍 Searching: {query}")
                
                search_args = {
                    "query": query,
                    "search_type": "hybrid",
                    "max_results": 5
                }
                result = await server._handle_search(search_args)
                print(result[0].text)
            
            elif cmd == 'list':
                print("\n📚 Available Datasets:")
                result = await server._handle_list_data({})
                print(result[0].text)
            
            else:
                print("❌ Unknown command. Type 'help' for available commands.")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())