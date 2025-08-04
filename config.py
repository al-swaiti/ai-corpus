"""
Configuration classes for MCP Documentation Intelligence System
Following production-ready patterns from MCP rules
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import os


@dataclass
class ScraperConfig:
    """Configuration for documentation scraper server"""
    base_url: str
    max_pages: int = 10000  # Increased for large-scale scraping
    delay_seconds: float = 0.5  # Faster for high-volume sites
    respect_robots_txt: bool = True
    max_depth: int = 10  # Deeper crawling
    timeout_seconds: float = 45.0  # Longer timeout for complex pages
    
    # Performance settings for large-scale scraping
    concurrent_workers: int = 8  # Parallel processing
    batch_size: int = 100  # Process in batches
    max_memory_mb: int = 2048  # Memory limit (2GB)
    enable_streaming: bool = True  # Stream large datasets
    auto_resume: bool = True  # Resume interrupted crawls
    
    # Content extraction settings
    min_content_length: int = 100
    include_tables: bool = True
    include_images: bool = False
    favor_precision: bool = True
    
    # Progress tracking
    progress_file: str = "crawl_progress.json"
    checkpoint_interval: int = 50  # Save progress every N pages
    
    # Output settings
    output_dir: Path = field(default_factory=lambda: Path("data"))
    backup_dir: Path = field(default_factory=lambda: Path("backups"))
    
    def __post_init__(self):
        """Ensure directories exist"""
        self.output_dir = Path(self.output_dir)
        self.backup_dir = Path(self.backup_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class QueryConfig:
    """Configuration for query server with semantic search"""
    data_dir: Path = field(default_factory=lambda: Path("data"))
    model_name: str = "all-MiniLM-L6-v2"
    chunk_size: int = 512
    chunk_overlap: int = 50
    max_results: int = 10
    similarity_threshold: float = 0.7
    
    # Cache settings
    cache_embeddings: bool = True
    cache_dir: Path = field(default_factory=lambda: Path("cache"))
    
    def __post_init__(self):
        """Ensure directories exist"""
        self.data_dir = Path(self.data_dir)
        self.cache_dir = Path(self.cache_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if self.cache_embeddings:
            self.cache_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class ServerConfig:
    """Base server configuration"""
    server_name: str
    version: str = "1.0.0"
    log_level: str = "INFO"
    log_file: Optional[Path] = None
    
    def __post_init__(self):
        """Setup logging configuration"""
        if self.log_file:
            self.log_file = Path(self.log_file)
            self.log_file.parent.mkdir(parents=True, exist_ok=True)


def load_scraper_config(base_url: str, **kwargs) -> ScraperConfig:
    """Load scraper configuration with environment variable overrides"""
    config_kwargs = {
        'base_url': base_url,
        'max_pages': int(os.getenv('MCP_MAX_PAGES', 1000)),
        'delay_seconds': float(os.getenv('MCP_DELAY_SECONDS', 1.0)),
        'respect_robots_txt': os.getenv('MCP_RESPECT_ROBOTS', 'true').lower() == 'true',
        'max_depth': int(os.getenv('MCP_MAX_DEPTH', 5)),
        'timeout_seconds': float(os.getenv('MCP_TIMEOUT', 30.0)),
        **kwargs
    }
    return ScraperConfig(**config_kwargs)


def load_query_config(**kwargs) -> QueryConfig:
    """Load query configuration with environment variable overrides"""
    config_kwargs = {
        'model_name': os.getenv('MCP_MODEL_NAME', 'all-MiniLM-L6-v2'),
        'chunk_size': int(os.getenv('MCP_CHUNK_SIZE', 512)),
        'max_results': int(os.getenv('MCP_MAX_RESULTS', 10)),
        'similarity_threshold': float(os.getenv('MCP_SIMILARITY_THRESHOLD', 0.7)),
        'cache_embeddings': os.getenv('MCP_CACHE_EMBEDDINGS', 'true').lower() == 'true',
        **kwargs
    }
    return QueryConfig(**config_kwargs)