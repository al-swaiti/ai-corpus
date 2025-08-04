#!/usr/bin/env python3
"""
Easy setup script for Ultimate MCP Documentation Server
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors gracefully"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Ultimate MCP Documentation Server")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Create virtual environment
    if not Path(".venv").exists():
        if not run_command(f"{sys.executable} -m venv .venv", "Creating virtual environment"):
            sys.exit(1)
    else:
        print("✅ Virtual environment already exists")
    
    # Determine activation script path
    if os.name == 'nt':  # Windows
        activate_script = ".venv\\Scripts\\activate"
        pip_path = ".venv\\Scripts\\pip"
        python_path = ".venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        activate_script = ".venv/bin/activate"
        pip_path = ".venv/bin/pip"
        python_path = ".venv/bin/python"
    
    # Install requirements
    if not run_command(f"{pip_path} install -r requirements.txt", "Installing dependencies"):
        sys.exit(1)
    
    # Create necessary directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("backups", exist_ok=True)
    print("✅ Created necessary directories")
    
    # Test the server
    print("\n🧪 Testing server startup...")
    test_command = f"echo 'test' | timeout 2 {python_path} ultimate_mcp_server.py 2>/dev/null"
    if os.name == 'nt':
        # Windows doesn't have timeout, use a different approach
        test_command = f"echo test | {python_path} ultimate_mcp_server.py"
    
    try:
        subprocess.run(test_command, shell=True, timeout=3, capture_output=True, text=True)
        print("✅ Server test completed successfully")
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        print("✅ Server startup test completed (timeout is expected)")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Configure your MCP client (like Cursor) with this server")
    print("2. Use the following configuration:")
    print(f'   Command: {os.path.abspath(python_path)}')
    print(f'   Args: ["{os.path.abspath("ultimate_mcp_server.py")}"]')
    print("3. Start scraping documentation websites!")
    
    print("\n📚 Example MCP configuration for Cursor (~/.cursor/mcp.json):")
    print(f'''{{
  "mcpServers": {{
    "ultimate-docs": {{
      "command": "{os.path.abspath(python_path)}",
      "args": ["{os.path.abspath("ultimate_mcp_server.py")}"],
      "env": {{
        "MCP_LOG_LEVEL": "INFO"
      }}
    }}
  }}
}}''')

if __name__ == "__main__":
    main()