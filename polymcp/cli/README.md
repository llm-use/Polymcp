<p align="center">
  <img src="cli/polymcp-cli.png" alt="PolymCP-cli Logo" width="500"/>
</p>

Command-line interface for PolyMCP - Universal MCP Agent & Toolkit.

## Quick Start

```bash
# Initialize a new project
polymcp init my-project

# Add MCP servers
polymcp server add http://localhost:8000/mcp

# List configured servers
polymcp server list

# Run an agent
polymcp agent run

# Test a server
polymcp test server http://localhost:8000/mcp
```

---

## 🎯 Your First Custom Tool

Let's create a complete example from scratch:

```bash
# 1. Create project
polymcp init my-first-tool --with-examples
cd my-first-tool

# 2. Create your custom tool
cat > tools/weather_tool.py << 'EOF'
def get_weather(city: str, units: str = "celsius") -> dict:
    """
    Get weather information for a city.
    
    Args:
        city: City name
        units: Temperature units (celsius/fahrenheit)
        
    Returns:
        Weather information dictionary
    """
    import random
    temp = random.randint(15, 30) if units == "celsius" else random.randint(59, 86)
    
    return {
        "city": city,
        "temperature": temp,
        "units": units,
        "condition": random.choice(["sunny", "cloudy", "rainy"]),
        "humidity": random.randint(40, 80)
    }
EOF

# 3. Update server.py to use your tool
# Add to imports: from tools.weather_tool import get_weather
# Add to tools list: tools=[greet, calculate, get_weather]

# 4. Install and run
pip install -r requirements.txt
python server.py &

# 5. Test your tool
polymcp test tool http://localhost:8000/mcp get_weather \
  --params '{"city":"Rome","units":"celsius"}'

# 6. Use with agent
polymcp agent run
# > You: What's the weather in Rome?
# > Agent: [calls get_weather and responds]
```

**Output:**
```json
{
  "city": "Rome",
  "temperature": 24,
  "units": "celsius",
  "condition": "sunny",
  "humidity": 65
}
```

---

## Commands

### `polymcp init`

Initialize new PolyMCP projects.

```bash
# Basic project
polymcp init my-project

# HTTP server project
polymcp init my-server --type http-server

# Agent project
polymcp init my-agent --type agent

# With examples and authentication
polymcp init my-project --with-examples --with-auth
```

**Project Types:**
- `basic`: Complete project with server + tools
- `http-server`: HTTP MCP server
- `stdio-server`: Stdio MCP server
- `agent`: Interactive agent

### `polymcp server`

Manage MCP servers.

```bash
# Add HTTP server
polymcp server add http://localhost:8000/mcp --name my-server

# Add stdio server
polymcp server add stdio://playwright \
  --type stdio \
  --command npx \
  --args @playwright/mcp@latest

# List all servers
polymcp server list

# Remove server
polymcp server remove http://localhost:8000/mcp

# Test server
polymcp server test http://localhost:8000/mcp

# Get server info
polymcp server info http://localhost:8000/mcp
```

**Using Your Own MCP Servers:**

1. Start your MCP server:
   ```bash
   cd my-mcp-project
   python server.py
   ```

2. Add it to PolyMCP CLI:
   ```bash
   polymcp server add http://localhost:8000/mcp --name my-custom-server
   ```

3. Use it with agents:
   ```bash
   polymcp agent run
   # or
   polymcp agent run --servers http://localhost:8000/mcp
   ```

### `polymcp agent`

Run and manage agents.

```bash
# Run interactive agent (default: unified)
polymcp agent run

# Use specific agent type
polymcp agent run --type codemode
polymcp agent run --type basic

# Use specific LLM
polymcp agent run --llm openai --model gpt-4
polymcp agent run --llm anthropic --model claude-3-5-sonnet-20241022
polymcp agent run --llm ollama --model llama3.2

# Single query (non-interactive)
polymcp agent run --query "What is 2+2?"

# With specific servers
polymcp agent run --servers http://localhost:8000/mcp,http://localhost:8001/mcp

# Verbose mode
polymcp agent run --verbose

# Benchmark agents
polymcp agent benchmark --query "Add 2+2" --iterations 5
```

**Agent Types:**
- `unified`: Autonomous multi-step reasoning (best for complex tasks)
- `codemode`: Code generation for tool orchestration (fastest)
- `basic`: Simple tool selection and execution

### `polymcp test`

Test MCP servers and tools.

```bash
# Test server connectivity
polymcp test server http://localhost:8000/mcp

# Test with authentication
polymcp test server http://localhost:8000/mcp --auth-key sk-...

# Test specific tool
polymcp test tool http://localhost:8000/mcp greet --params '{"name":"World"}'

# Test authentication
polymcp test auth http://localhost:8000

# Test stdio server
polymcp test stdio npx @playwright/mcp@latest

# Test all configured servers
polymcp test all
```

### `polymcp config`

Manage configuration.

```bash
# Show configuration
polymcp config show

# Set values
polymcp config set llm.provider openai
polymcp config set llm.model gpt-4
polymcp config set agent.verbose true

# Get value
polymcp config get llm.provider

# Delete value
polymcp config delete llm.model

# Initialize with defaults
polymcp config init

# Edit in editor
polymcp config edit

# Show config path
polymcp config path

# Reset to defaults
polymcp config reset
```

**Global vs Local Config:**

```bash
# Local config (project-specific)
polymcp config set llm.provider openai

# Global config (user-wide)
polymcp config set llm.provider openai --global
```

---

## Configuration

The CLI uses two configuration files:

1. **Global Config**: `~/.polymcp/polymcp_config.json`
   - User-wide settings
   - LLM provider defaults
   - Agent preferences

2. **Local Config**: `./polymcp_config.json`
   - Project-specific settings
   - Overrides global config

**Example Configuration:**

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7
  },
  "agent": {
    "type": "unified",
    "verbose": false,
    "max_steps": 10
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000
  }
}
```

## Server Registry

The CLI maintains a registry of MCP servers:

**Registry File**: `./polymcp_registry.json`

```json
{
  "version": "1.0.0",
  "description": "PolyMCP server registry",
  "servers": {
    "http://localhost:8000/mcp": {
      "url": "http://localhost:8000/mcp",
      "type": "http",
      "name": "my-server"
    }
  },
  "stdio_servers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": {},
      "type": "stdio"
    }
  }
}
```

## Environment Variables

The CLI respects standard environment variables:

```bash
# LLM Providers
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export OLLAMA_BASE_URL=http://localhost:11434

# Windows Encoding Fix
export PYTHONIOENCODING=utf-8

# Editor for config editing
export EDITOR=vim

# Debug mode
export POLYMCP_DEBUG=true
```

---

## 💡 Real-World Examples

### Example 1: Complete Workflow

```bash
# 1. Create new project
polymcp init my-project --with-examples
cd my-project

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start your MCP server
python server.py &

# 4. Add server to CLI
polymcp server add http://localhost:8000/mcp --name my-server

# 5. Test the server
polymcp test server http://localhost:8000/mcp

# 6. Run interactive agent
polymcp agent run
```

### Example 2: Multi-Tool Financial Assistant

```bash
# Create financial tools server
polymcp init finance-server --type http-server
cd finance-server

# Create financial tools
cat > tools/finance_tools.py << 'EOF'
def calculate_mortgage(principal: float, rate: float, years: int) -> dict:
    """Calculate monthly mortgage payment."""
    monthly_rate = rate / 100 / 12
    num_payments = years * 12
    payment = principal * (monthly_rate * (1 + monthly_rate)**num_payments) / \
              ((1 + monthly_rate)**num_payments - 1)
    
    return {
        "monthly_payment": round(payment, 2),
        "total_paid": round(payment * num_payments, 2),
        "total_interest": round((payment * num_payments) - principal, 2)
    }

def calculate_roi(initial: float, final: float, years: int) -> dict:
    """Calculate return on investment."""
    total_return = ((final - initial) / initial) * 100
    annual_return = ((final / initial) ** (1 / years) - 1) * 100
    
    return {
        "total_return_percent": round(total_return, 2),
        "annual_return_percent": round(annual_return, 2),
        "profit": round(final - initial, 2)
    }
EOF

# Update server.py to include new tools
# Start and register
python server.py &
polymcp server add http://localhost:8000/mcp --name finance-tools

# Use with agent
polymcp agent run --query "Calculate mortgage for 300000 at 3.5% for 30 years"
```

### Example 3: Using Multiple Servers

```bash
# Add multiple servers
polymcp server add http://localhost:8000/mcp --name text-tools
polymcp server add http://localhost:8001/mcp --name data-tools

# List all servers
polymcp server list

# Run agent with all configured servers
polymcp agent run

# Or specify servers explicitly
polymcp agent run --servers http://localhost:8000/mcp,http://localhost:8001/mcp
```

### Example 4: Web Automation with Playwright

```bash
# Setup browser automation
polymcp init web-automation --type agent

# Add Playwright server
polymcp server add stdio://playwright \
  --type stdio \
  --command npx \
  --args @playwright/mcp@latest

# Add custom web tools
polymcp server add http://localhost:8000/mcp --name web-tools

# Test browser automation
polymcp agent run --query "
  Go to github.com/llm-use/polymcp,
  take a screenshot,
  count the stars
"
```

### Example 5: Data Processing Pipeline

```bash
# Setup multi-server pipeline
polymcp init data-pipeline --type agent

# Add multiple specialized servers
polymcp server add http://localhost:8000/mcp --name data-input
polymcp server add http://localhost:8001/mcp --name data-transform
polymcp server add http://localhost:8002/mcp --name data-output

# Configure agent for complex workflows
polymcp config set agent.type unified
polymcp config set agent.max_steps 20

# Run pipeline
polymcp agent run --query "
  Load data from CSV,
  clean missing values,
  calculate statistics,
  generate report
"
```

---

## 🔧 Advanced Usage

### Benchmark Different Approaches

```bash
# Compare agent performance
polymcp agent benchmark \
  --query "Calculate 10+20, multiply by 2, subtract 5" \
  --iterations 3

# Expected output:
# Basic Agent:     2.34s
# CodeMode Agent:  1.45s  ⚡ 38% faster
# Unified Agent:   3.12s
```

### Automated Server Discovery

Create `discover_servers.sh`:

```bash
#!/bin/bash
# Auto-discover MCP servers on local network

echo "Scanning for MCP servers..."

for port in {8000..8010}; do
    if timeout 1 curl -s http://localhost:$port/mcp/list_tools > /dev/null 2>&1; then
        echo "Found server on port $port"
        polymcp server add http://localhost:$port/mcp --name "auto-$port"
    fi
done

polymcp server list
```

### CI/CD Integration

Create `.github/workflows/test-mcp.yml`:

```yaml
name: Test MCP Servers
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install PolyMCP
        run: pip install polymcp
      
      - name: Start servers
        run: |
          python server1.py &
          python server2.py &
          sleep 5
      
      - name: Test all servers
        run: polymcp test all
      
      - name: Run agent tests
        run: |
          polymcp agent run --query "Test query" > output.txt
          grep -q "success" output.txt
```

---

## 🎓 Best Practices

### Choosing the Right Agent Type

| Task Type | Recommended Agent | Why |
|-----------|------------------|-----|
| Simple queries | `basic` | Fast, single tool call |
| Complex workflows | `unified` | Multi-step reasoning |
| Multiple tool orchestration | `codemode` | 60% faster, generates code |
| Browser automation | `unified` | Handles async operations |
| Data pipelines | `codemode` | Loops and conditions |

### Performance Tips

```bash
# 1. Use codemode for multiple operations
polymcp agent run --type codemode \
  --query "Process 100 records"  # ⚡ Much faster

# 2. Limit steps for complex tasks
polymcp config set agent.max_steps 15

# 3. Use verbose only for debugging
polymcp agent run --verbose  # Slower but detailed

# 4. Cache LLM provider in config
polymcp config set llm.provider ollama  # Avoid re-selection
```

### Security Considerations

```bash
# 1. Never commit API keys
echo "OPENAI_API_KEY=sk-..." >> .env
echo ".env" >> .gitignore

# 2. Use authentication for production
polymcp init my-server --with-auth

# 3. Validate tool inputs
# In your tools, always validate parameters!

# 4. Limit network access
# Configure firewall rules for MCP servers
```

---

## 🐛 Troubleshooting

### Windows Emoji Issue ⚠️

### Server Not Found

```bash
# Check registered servers
polymcp server list

# Test connectivity
polymcp test server http://localhost:8000/mcp

# Re-add server
polymcp server add http://localhost:8000/mcp
```

### Authentication Issues

```bash
# Test authentication
polymcp test auth http://localhost:8000

# Use API key
polymcp agent run --servers http://localhost:8000/mcp
# (Set X-API-Key in config or environment)
```

### LLM Provider Issues

```bash
# Check configuration
polymcp config get llm.provider

# Set explicitly
polymcp config set llm.provider ollama
polymcp config set llm.model llama3.2

# Or use command-line options
polymcp agent run --llm ollama --model llama3.2
```

### Ollama Connection Issues

**Problem:** "Connection refused to localhost:11434"

**Solutions:**
```bash
# 1. Check if Ollama is running
curl http://localhost:11434/api/tags

# 2. Start Ollama
ollama serve

# 3. Check model is pulled
ollama list
ollama pull llama3.2

# 4. Test with explicit URL
export OLLAMA_BASE_URL=http://localhost:11434
polymcp agent run --llm ollama --model llama3.2
```

### Agent Not Finding Tools

**Problem:** "No suitable tool found"

**Solutions:**
```bash
# 1. Check server is registered
polymcp server list

# 2. Test server connectivity
polymcp test server http://localhost:8000/mcp

# 3. Verify tools are exposed
curl http://localhost:8000/mcp/list_tools

# 4. Check agent can see tools
polymcp agent run --verbose --query "list available tools"

# 5. Re-register server
polymcp server remove http://localhost:8000/mcp
polymcp server add http://localhost:8000/mcp --name my-server
```

### Import Errors

**Problem:** "ModuleNotFoundError: No module named 'polymcp'"

**Solutions:**
```bash
# 1. Install PolyMCP
pip install polymcp

# 2. Check installation
python -c "import polymcp; print(polymcp.__version__)"

# 3. Virtual environment issue
which python  # Should be in venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

# 4. Development install
cd polymcp
pip install -e .
```

### Server Won't Start

**Problem:** "Address already in use"

**Solutions:**
```bash
# Find process using port
# Linux/Mac
lsof -i :8000

# Windows
netstat -ano | findstr :8000

# Kill process
# Linux/Mac
kill -9 <PID>

# Windows
taskkill /PID <PID> /F

# Or use different port
# Edit server.py:
# uvicorn.run(app, host="0.0.0.0", port=8001)
```

---

## 🔍 Quick Reference

### Common Commands Cheatsheet

```bash
# Setup
polymcp init my-project              # New project
polymcp config init                  # Setup config

# Servers
polymcp server add <url>             # Add server
polymcp server list                  # List all
polymcp server test <url>            # Test connectivity

# Agent
polymcp agent run                    # Interactive mode
polymcp agent run --query "..."      # Single query
polymcp agent run --type codemode    # Specific type

# Testing
polymcp test all                     # Test everything
polymcp test server <url>            # Test one server
polymcp test tool <url> <name>       # Test tool

# Config
polymcp config set llm.provider openai
polymcp config get llm.provider
polymcp config show
```

### Environment Variables Reference

```bash
# LLM Providers
OPENAI_API_KEY=sk-...               # OpenAI
ANTHROPIC_API_KEY=sk-ant-...        # Anthropic
OLLAMA_BASE_URL=http://localhost:11434  # Ollama

# Encoding (Windows)
PYTHONIOENCODING=utf-8              # Fix emoji issues

# Editor
EDITOR=vim                          # Config editor

# Debug
POLYMCP_DEBUG=true                  # Enable debug mode
```

### File Locations

```bash
# Global config
~/.polymcp/polymcp_config.json

# Local config
./polymcp_config.json

# Server registry
./polymcp_registry.json

# Project structure
my-project/
├── server.py              # MCP server
├── tools/                 # Your tools
│   └── example_tools.py
├── .env                   # Environment vars
└── requirements.txt       # Dependencies
```

---

## 🎯 Next Steps

After reading this guide:

1. ✅ **Create your first project**: `polymcp init my-first-project`
2. ✅ **Add a custom tool**: Edit `tools/example_tools.py`
3. ✅ **Test your server**: `polymcp test server http://localhost:8000/mcp`
4. ✅ **Run an agent**: `polymcp agent run`

---

## ❓ FAQ

**Q: Which agent type should I use?**
A: Use `unified` for complex tasks, `codemode` for speed, `basic` for simple queries.

**Q: Can I use multiple LLM providers?**
A: Yes! Set different providers per project with local config.

**Q: How do I add authentication?**
A: Use `--with-auth` flag: `polymcp init my-server --with-auth`

**Q: Can I use PolyMCP without Python?**
A: Yes! Add TypeScript/Node.js MCP servers via stdio mode.

**Q: Is there a GUI?**
A: CLI only for now. GUI planned for future releases.

---

## License

MIT License - see LICENSE file for details.

## Links

- [PolyMCP Repository](https://github.com/llm-use/polymcp)
- [Report Issues](https://github.com/llm-use/polymcp/issues)
- [MCP Protocol](https://modelcontextprotocol.io/)

---

## 🙏 Credits

- **MCP Protocol**: [Anthropic](https://modelcontextprotocol.io/)
- **Playwright MCP**: [Microsoft](https://github.com/microsoft/playwright-mcp)

---

**Made with ❤️ by the PolyMCP community**
