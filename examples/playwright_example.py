#!/usr/bin/env python3
"""
Playwright MCP Example with PolyMCP
Real example using Anthropic's @playwright/mcp server via stdio.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from polymcp.polyagent import UnifiedPolyAgent, OllamaProvider


async def main():
    """Main example function."""
    
    print("\n" + "="*60)
    print("🎭 Playwright MCP Example with PolyMCP + Ollama")
    print("="*60 + "\n")
    
    # Create Ollama LLM provider
    print("Initializing Ollama...")
    llm = OllamaProvider(
        model="llama2",
        base_url="http://localhost:11434"
    )
    
    # Configure Playwright stdio server
    stdio_servers = [
        {
            "command": "npx",
            "args": ["@playwright/mcp@latest"],
            "env": {
                "DISPLAY": ":1"  # For Linux, remove on Windows/Mac
            }
        }
    ]
    
    # Create unified agent with stdio support
    print("Starting Playwright MCP server...")
    agent = UnifiedPolyAgent(
        llm_provider=llm,
        stdio_servers=stdio_servers,
        verbose=True
    )
    
    async with agent:
        # Example queries
        queries = [
            "Go to google.com",
            "Search for 'best restaurants in San Francisco'",
            "Take a screenshot of the page",
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n{'='*60}")
            print(f"Query {i}/{len(queries)}: {query}")
            print(f"{'='*60}\n")
            
            try:
                result = await agent.run_async(query)
                print(f"\nResult: {result}\n")
            except Exception as e:
                print(f"\nError: {e}\n")
            
            await asyncio.sleep(1)
        
        # Interactive mode
        print("\n" + "="*60)
        print("Interactive Mode - Type 'quit' to exit")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye!")
                    break
                
                if not user_input:
                    continue
                
                result = await agent.run_async(user_input)
                print(f"\nAgent: {result}\n")
            
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}\n")


if __name__ == "__main__":
    print("\n📋 Prerequisites:")
    print("  1. Ollama running: ollama serve")
    print("  2. Playwright MCP: npm install -g @playwright/mcp")
    print("  3. Model pulled: ollama pull llama2")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)