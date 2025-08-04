# Ultimate MCP Documentation Server

> ﴿يُسَبِّحُ لِلَّهِ مَا فِي السَّمَاوَاتِ وَالْأَرْضِ ۖ لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ ۖ وَهُوَ عَلَىٰ كُلِّ شَيْءٍ قَدِيرٌ﴾  
> (سورة التغابن، الآية 1)

الحمد لله العليم الحكيم، المدبر الخبير، القوي القهار، الذي علَّم الإنسان ما لم يعلم، وسخّر له سُبل الفهم والمعرفة.

بعون الله وتوفيقه، وابتغاء وجهه الكريم، أنشأنا هذا المشروع:

## 🎯 **Ultimate MCP Documentation Server**

**خادم ذكي موحد، يمكّن المطورين والباحثين من التعامل مع أي موقع وثائق بشكل أوتوماتيكي، يفهم اللغة الطبيعية، ويدير عملية الزحف والفهرسة والبحث الدلالي باحترافية.**

✨🌱 **نسأل الله القبول والإخلاص، وأن يكون هذا العمل في ميزان كل من يستخدمه ويطوره ويستفيد منه.**

---

> **THE ONE** MCP server that handles ANY documentation website automatically with intelligent scraping and AI-powered search.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)
[![Free for All](https://img.shields.io/badge/Free-For%20All-brightgreen.svg)](https://github.com/your-username/ultimate-mcp-docs)

## 🚀 Features

### 🧠 **Ultimate AI Handler**
- **Natural Language Interface**: Just ask! "Scrape https://docs.python.org/", "Search for authentication methods"
- **Intent Detection**: Automatically understands what you want to do
- **Smart Request Routing**: Handles scraping, searching, and summarization intelligently

### 🕷️ **Intelligent Web Scraping**
- **Auto-Scaling**: Handles 10 pages to 10,000+ pages seamlessly
- **Smart Optimization**: Automatically detects site size and optimizes strategy
- **Respectful Crawling**: Follows robots.txt, implements intelligent delays
- **Content Extraction**: Uses multiple methods (trafilatura, BeautifulSoup) for maximum success
- **Resume Capability**: Auto-resume interrupted crawls

### 🔍 **AI-Powered Search**
- **Semantic Search**: Find content by meaning, not just keywords
- **Hybrid Search**: Combines semantic + keyword matching for best results
- **Real-time Results**: Search across all your scraped documentation instantly
- **Context Awareness**: Understands documentation structure and relationships

### ⚡ **Production Ready**
- **Memory Management**: Handles large datasets efficiently
- **Error Recovery**: Graceful error handling and detailed diagnostics
- **Security**: URL validation, SSRF protection, rate limiting
- **Performance**: Connection pooling, caching, optimized timeouts

## 📦 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-username/ultimate-mcp-docs
cd ultimate-mcp-docs

# Run the setup script
python setup.py
```

### 2. Configure Your MCP Client

#### For Cursor IDE:
Add to your `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "ultimate-docs": {
      "command": "/path/to/your/project/.venv/bin/python",
      "args": ["/path/to/your/project/ultimate_mcp_server.py"],
      "env": {
        "MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### For Other MCP Clients:
Use the paths shown after running `python setup.py`.

### 3. Start Using!

Once configured, you can use natural language commands in your MCP client:

```
🤖 "Scrape https://docs.python.org/"
🤖 "Search for authentication methods"
🤖 "What documentation do we have available?"
```

## 🎯 Usage Examples

### 🚀 **MCP Client Usage** 

#### **Cursor IDE**
```bash
# Natural language commands in Cursor:
"Scrape https://fastapi.tiangolo.com/"
"Download all pages from https://docs.github.com/"
"Search for authentication methods"
"What documentation do we have available?"
```

#### **Google Gemini CLI** 🤖
```bash
# Setup Gemini CLI with MCP server
gemini config add-mcp-server ultimate-docs \
  --command "/path/to/.venv/bin/python" \
  --args "/path/to/ultimate_mcp_server.py"

# Use with Gemini
gemini chat --mcp ultimate-docs "Scrape https://docs.python.org/ and search for decorators"
gemini ask --mcp ultimate-docs "What documentation do we have available?"
```

#### **Anthropic Claude CLI** 🧠
```bash
# Setup Claude CLI with MCP server
claude mcp add ultimate-docs \
  --command "/path/to/.venv/bin/python" \
  --args "/path/to/ultimate_mcp_server.py" \
  --description "Ultimate documentation scraping and search"

# Use with Claude
claude chat --mcp ultimate-docs "Please scrape https://fastapi.tiangolo.com/ documentation"
claude ask --mcp ultimate-docs "Search for authentication patterns in scraped docs"
```

#### **Any MCP-Compatible Client**
Add to your MCP configuration file:
```json
{
  "mcpServers": {
    "ultimate-docs": {
      "command": "/path/to/your/project/.venv/bin/python",
      "args": ["/path/to/your/project/ultimate_mcp_server.py"],
      "env": {
        "MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 💻 **Command Line Usage**

```bash
# Direct command line usage (no MCP client needed):

# Scrape a website
python ultimate_mcp_server.py --scrape https://docs.python.org/ --max-pages 50

# Search existing documentation  
python ultimate_mcp_server.py --search "authentication methods" --search-type hybrid

# List available datasets
python ultimate_mcp_server.py --list-data

# Interactive mode
python ultimate_mcp_server.py --interactive

# Get help
python ultimate_mcp_server.py --help
```

### 🐍 **Programmatic Usage**

```python
# Use as a Python library
import asyncio
from ultimate_mcp_server import UltimateWebScraper, UltimateConfig

async def scrape_docs():
    # Configure scraper
    config = UltimateConfig(
        max_pages=100,
        delay_seconds=0.5,
        concurrent_workers=8
    )
    
    # Scrape website
    scraper = UltimateWebScraper(config)
    stats = await scraper.scrape_website("https://docs.python.org/")
    
    print(f"Scraped {stats['pages_crawled']} pages!")
    
    # Access scraped data directly
    for page in scraper.scraped_pages:
        print(f"URL: {page['url']}")
        print(f"Content: {page['content'][:100]}...")

asyncio.run(scrape_docs())
```

### 📁 **Examples Script**

Run comprehensive examples:

```bash
# Run all usage examples
python examples.py

# Examples include:
# - Basic scraping
# - Advanced configuration  
# - AI-powered search
# - Complete workflows
# - Direct data access
```

### 🤖 **AI CLI Integration**

**Full integration with popular AI tools:**

- **🤖 Google Gemini CLI**: Complete setup and usage guide
- **🧠 Anthropic Claude CLI**: Advanced integration patterns  
- **🔧 Generic MCP Clients**: Universal configuration templates

📖 **Detailed Guide**: See [CLI_INTEGRATION.md](CLI_INTEGRATION.md) for complete instructions on using with Gemini CLI, Claude CLI, and other MCP-compatible tools.

## 🏗️ Architecture

### Core Components

- **🎯 RequestRouter**: Intelligent intent detection and request routing
- **🕷️ UltimateWebScraper**: Auto-scaling web scraper with smart optimization
- **🔍 UltimateQueryEngine**: AI-powered search with semantic understanding
- **⚙️ AutoScaler**: Automatic strategy optimization based on site size
- **🛡️ Security Layer**: URL validation, SSRF protection, rate limiting

### Data Flow

```
User Request → Intent Detection → Smart Routing → Execution → Results
                      ↓
              [Scrape|Search|Summary] Handler
                      ↓
              Optimized Processing → Data Storage/Retrieval
```

## 📊 Performance

- **Small Sites** (< 100 pages): Conservative approach, respectful delays
- **Medium Sites** (100-1000 pages): Balanced optimization
- **Large Sites** (1000+ pages): High-performance parallel processing
- **Memory Efficient**: Handles 10K+ pages with streaming and batching
- **Resume Support**: Automatic checkpoint and resume functionality

## 🔧 Configuration

### Environment Variables

```bash
# Optional customization
export MCP_LOG_LEVEL=INFO          # Logging level
export MCP_MAX_PAGES=10000         # Maximum pages per scrape
export MCP_DELAY_SECONDS=1.0       # Default delay between requests
export MCP_MAX_WORKERS=8           # Maximum concurrent workers
```

### Advanced Configuration

The server automatically optimizes settings, but you can customize via the `UltimateConfig` class:

```python
config = UltimateConfig(
    max_pages=5000,
    concurrent_workers=12,
    delay_seconds=0.5,
    chunk_size=512,
    similarity_threshold=0.7
)
```

## 📁 Project Structure

```
ultimate-mcp-docs/
├── ultimate_mcp_server.py    # Main MCP server
├── config.py                 # Configuration classes
├── setup.py                  # Easy setup script
├── requirements.txt          # Python dependencies
├── ultimate_config.json      # MCP configuration template
├── data/                     # Scraped documentation
│   ├── examples/             # Sample data
│   └── README.md            # Data format documentation
├── backups/                  # Backup directory
└── README.md                # This file
```

## 🛠️ Development

### Running Tests

```bash
# Test server startup
.venv/bin/python ultimate_mcp_server.py --test

# Test scraping
python -c "
import asyncio
from ultimate_mcp_server import UltimateMCPServer
async def test():
    server = UltimateMCPServer()
    result = await server._handle_scrape({'url': 'https://httpbin.org/html'})
asyncio.run(test())
"
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Submit a pull request

## 🔒 Security

- **URL Validation**: Prevents SSRF attacks and invalid URLs
- **Rate Limiting**: Respectful crawling with configurable delays
- **Robots.txt Compliance**: Automatic robots.txt checking
- **Input Sanitization**: Validates and sanitizes all inputs
- **Error Handling**: Secure error messages without information disclosure

## 🐛 Troubleshooting

### Common Issues

**Server Won't Start**
```bash
# Check Python version (3.8+ required)
python --version

# Reinstall dependencies
.venv/bin/pip install -r requirements.txt --force-reinstall
```

**No Data Saved**
- Check that the `data` directory exists and is writable
- Verify MCP client is using correct working directory
- Look for diagnostic files in the data directory

**Search Not Working**
- Ensure you have scraped some documentation first
- Check that the model dependencies are installed correctly
- Verify the data files are in the correct format

### Debug Mode

Set `MCP_LOG_LEVEL=DEBUG` for detailed logging:

```bash
export MCP_LOG_LEVEL=DEBUG
```

## 📈 Roadmap

- [ ] **Multi-format Support**: PDF, Word, and other document formats
- [ ] **Real-time Updates**: Monitor documentation for changes
- [ ] **Team Collaboration**: Shared datasets and search results
- [ ] **Custom Extractors**: Site-specific content extraction rules
- [ ] **Analytics Dashboard**: Usage statistics and insights
- [ ] **API Endpoints**: REST API for external integrations

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) for the fantastic protocol
- [Trafilatura](https://trafilatura.readthedocs.io/) for excellent content extraction
- [Sentence Transformers](https://www.sbert.net/) for semantic search capabilities
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/ultimate-mcp-docs/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/ultimate-mcp-docs/discussions)
- **Documentation**: [Wiki](https://github.com/your-username/ultimate-mcp-docs/wiki)

---

**Made with ❤️ for the developer community**

> Transform any documentation website into a searchable, AI-powered knowledge base with just one command!