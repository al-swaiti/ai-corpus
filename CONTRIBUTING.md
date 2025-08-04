# Contributing to Ultimate MCP Documentation Server

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/ultimate-mcp-docs.git
   cd ultimate-mcp-docs
   ```
3. **Set up the development environment**:
   ```bash
   python setup.py
   ```

## 🔄 Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and test thoroughly

3. **Test your changes**:
   ```bash
   # Test server startup
   .venv/bin/python ultimate_mcp_server.py
   
   # Test with a small website
   echo '{"url": "https://httpbin.org/html"}' | .venv/bin/python -c "
   import asyncio, json, sys
   from ultimate_mcp_server import UltimateMCPServer
   async def test():
       server = UltimateMCPServer()
       data = json.loads(sys.stdin.read())
       result = await server._handle_scrape(data)
       print(result[0].text)
   asyncio.run(test())
   "
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push to your fork** and **create a Pull Request**

## 📋 Code Guidelines

### Python Style
- Follow PEP 8 style guidelines
- Use type hints where possible
- Add docstrings to all functions and classes
- Keep functions focused and small

### Commit Messages
Use conventional commits format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `refactor:` for code refactoring
- `test:` for adding tests

### Code Structure
- **Server Logic**: Keep in `ultimate_mcp_server.py`
- **Configuration**: Add to `config.py`
- **Utilities**: Create separate modules if needed
- **Tests**: Add test files in a `tests/` directory

## 🐛 Bug Reports

When reporting bugs, please include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS, etc.)
- Error messages and logs

## 💡 Feature Requests

For new features:
- Describe the use case and benefit
- Provide examples of how it would work
- Consider implementation complexity
- Discuss potential breaking changes

## 🧪 Testing

- Test your changes with multiple websites
- Verify that existing functionality still works
- Include both success and failure scenarios
- Test with different MCP clients if possible

## 📖 Documentation

- Update README.md for user-facing changes
- Add docstrings for new code
- Update configuration examples
- Include usage examples for new features

## 🤝 Community

- Be respectful and inclusive
- Help others learn and contribute
- Share knowledge and best practices
- Participate in discussions and code reviews

Thank you for contributing to make documentation scraping better for everyone! 🎉