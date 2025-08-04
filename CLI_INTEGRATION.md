# CLI Integration Guide

> **تعليمات الاستخدام مع أدوات الذكاء الاصطناعي المختلفة**  
> **Instructions for using with various AI CLI tools**

This guide shows how to integrate the Ultimate MCP Documentation Server with popular AI CLI tools.

## 🤖 Google Gemini CLI Integration

### Installation
```bash
# Install Gemini CLI (if not already installed)
pip install google-generativeai-cli

# Or via npm
npm install -g @google/generative-ai-cli
```

### Setup
```bash
# Add our MCP server to Gemini CLI
gemini config add-mcp-server ultimate-docs \
  --command "/path/to/your/project/.venv/bin/python" \
  --args "/path/to/your/project/ultimate_mcp_server.py" \
  --description "Ultimate documentation scraping and AI search"

# Verify setup
gemini mcp list
```

### Usage Examples
```bash
# Scrape documentation
gemini chat --mcp ultimate-docs "Please scrape https://docs.python.org/3/ and extract all Python documentation"

# Search existing data
gemini ask --mcp ultimate-docs "Search for information about decorators in Python"

# Interactive session
gemini chat --mcp ultimate-docs
> "What documentation datasets do we have available?"
> "Scrape https://fastapi.tiangolo.com/ and then search for authentication examples"
```

## 🧠 Anthropic Claude CLI Integration

### Installation
```bash
# Install Claude CLI
pip install anthropic-cli

# Or download from GitHub releases
curl -L https://github.com/anthropics/claude-cli/releases/latest/download/claude-cli-linux -o claude
chmod +x claude
sudo mv claude /usr/local/bin/
```

### Setup
```bash
# Configure Claude CLI with our MCP server
claude mcp add ultimate-docs \
  --command "/path/to/your/project/.venv/bin/python" \
  --args "/path/to/your/project/ultimate_mcp_server.py" \
  --env MCP_LOG_LEVEL=INFO \
  --description "Intelligent documentation scraping and search"

# Test connection
claude mcp test ultimate-docs
```

### Usage Examples
```bash
# Comprehensive documentation scraping
claude chat --mcp ultimate-docs "I need you to scrape the entire React documentation from https://react.dev/learn and then help me find information about hooks"

# Advanced search and analysis
claude ask --mcp ultimate-docs "Search all available documentation for information about authentication patterns and security best practices"

# Multi-step workflow
claude chat --mcp ultimate-docs
> "First, scrape https://docs.crewai.com/en/ completely"
> "Then search for information about MCP integration"
> "Finally, create a summary of how to integrate MCP servers with CrewAI"
```

## 🔧 Generic MCP Configuration

For any MCP-compatible client, use this configuration template:

### JSON Configuration
```json
{
  "mcpServers": {
    "ultimate-docs": {
      "command": "/path/to/your/project/.venv/bin/python",
      "args": ["/path/to/your/project/ultimate_mcp_server.py"],
      "env": {
        "MCP_LOG_LEVEL": "INFO",
        "MCP_MAX_PAGES": "1000",
        "MCP_DELAY_SECONDS": "1.0"
      },
      "description": "Ultimate MCP Documentation Server - Intelligent scraping and AI search"
    }
  }
}
```

### YAML Configuration
```yaml
mcpServers:
  ultimate-docs:
    command: "/path/to/your/project/.venv/bin/python"
    args:
      - "/path/to/your/project/ultimate_mcp_server.py"
    env:
      MCP_LOG_LEVEL: "INFO"
      MCP_MAX_PAGES: "1000"
      MCP_DELAY_SECONDS: "1.0"
    description: "Ultimate MCP Documentation Server - Intelligent scraping and AI search"
```

## 🌟 Advanced Usage Patterns

### 1. Documentation Research Workflow
```bash
# With Gemini
gemini chat --mcp ultimate-docs "
1. Scrape https://docs.python.org/3/ focusing on async/await documentation
2. Also scrape https://fastapi.tiangolo.com/ for FastAPI async patterns
3. Search both datasets for async best practices
4. Create a comparison guide
"

# With Claude  
claude chat --mcp ultimate-docs "
I'm building an async Python application. Please:
1. Scrape relevant async documentation from multiple sources
2. Find examples of async/await patterns
3. Identify common pitfalls and best practices
4. Suggest an implementation approach
"
```

### 2. API Documentation Analysis
```bash
# Comprehensive API research
gemini ask --mcp ultimate-docs "
Scrape the following API documentation sites:
- https://docs.github.com/en/rest
- https://docs.gitlab.com/ee/api/
- https://docs.bitbucket.org/api/

Then analyze and compare their authentication methods
"
```

### 3. Framework Comparison Research
```bash
# Multi-framework analysis
claude chat --mcp ultimate-docs "
Please scrape documentation for these web frameworks:
- Django: https://docs.djangoproject.com/
- FastAPI: https://fastapi.tiangolo.com/
- Flask: https://flask.palletsprojects.com/

Then help me compare their approach to handling authentication and middleware
"
```

## 🚀 Tips for Effective Usage

### Best Practices
1. **Start with specific sites**: Begin with well-structured documentation sites
2. **Use reasonable limits**: Don't scrape more than you need initially
3. **Combine scraping with search**: Scrape first, then search for specific information
4. **Leverage natural language**: Ask conversational questions for better results

### Common Commands
```bash
# Check what's available
"What documentation do we have?"
"List all scraped datasets"

# Targeted scraping  
"Scrape https://docs.example.com/ but limit to 50 pages"
"Download only the API reference section from https://api-docs.com/"

# Smart searching
"Find examples of user authentication"
"Show me error handling patterns"
"Search for deployment instructions"
```

### Troubleshooting
```bash
# If MCP connection fails
claude mcp test ultimate-docs
gemini mcp list

# Check server logs
tail -f ~/.mcp/logs/ultimate-docs.log

# Restart server
claude mcp restart ultimate-docs
```

## 🔧 Environment Variables

Configure the server behavior:
```bash
export MCP_LOG_LEVEL=DEBUG          # Detailed logging
export MCP_MAX_PAGES=5000           # Increase page limit
export MCP_DELAY_SECONDS=0.5        # Faster scraping
export MCP_MAX_WORKERS=12           # More concurrent workers
```

## 🌍 Global Installation

For system-wide access:
```bash
# Create global symlink
sudo ln -s /path/to/your/project/.venv/bin/python /usr/local/bin/ultimate-mcp-python
sudo ln -s /path/to/your/project/ultimate_mcp_server.py /usr/local/bin/ultimate-mcp-server

# Then use in any MCP client
"command": "/usr/local/bin/ultimate-mcp-python",
"args": ["/usr/local/bin/ultimate-mcp-server"]
```

---

**Made with ❤️ for the global developer community**  
**صنع بالحب للمجتمع العالمي للمطورين**