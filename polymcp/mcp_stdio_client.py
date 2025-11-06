"""
MCP Stdio Client - Production Implementation
Handles communication with stdio-based MCP servers (like Anthropic's official servers).
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP stdio server."""
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None


class MCPStdioClient:
    """
    Client for stdio-based MCP servers.
    
    Communicates with MCP servers that use JSON-RPC over stdin/stdout,
    such as @playwright/mcp, @modelcontextprotocol/server-filesystem, etc.
    """
    
    def __init__(self, config: MCPServerConfig):
        """
        Initialize stdio client.
        
        Args:
            config: Server configuration (command, args, env)
        """
        self.config = config
        self.process: Optional[asyncio.subprocess.Process] = None
        self.request_id = 0
        self._lock = asyncio.Lock()
        self._running = False
    
    async def start(self) -> None:
        """Start the MCP server process."""
        if self._running:
            return
        
        try:
            import os
            import sys
            import shutil
            
            env = os.environ.copy()
            if self.config.env:
                env.update(self.config.env)
            
            # Gestione automatica cross-platform INTERNA
            command = self.config.command
            args = list(self.config.args)
            
            # Se è npx su Windows, usa cmd /c automaticamente
            if sys.platform == "win32" and command == "npx":
                # Trova npx
                npx_path = shutil.which("npx") or shutil.which("npx.cmd")
                if npx_path:
                    command = "cmd"
                    args = ["/c", npx_path] + args
            
            # Crea il processo
            self.process = await asyncio.create_subprocess_exec(
                command,
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            self._running = True
            logger.info(f"Started MCP server: {self.config.command} {' '.join(self.config.args)}")
            
            await asyncio.sleep(2)
            await self._initialize()
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise RuntimeError(f"Failed to start MCP server: {e}")
    
    async def _initialize(self) -> None:
        """Initialize the MCP connection."""
        try:
            response = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "polymcp",
                    "version": "1.0.0"
                }
            })
            
            if "error" in response:
                raise RuntimeError(f"Initialization failed: {response['error']}")
            
            logger.info("MCP connection initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize MCP connection: {e}")
            raise
    
    async def _send_request(self, method: str, params: Optional[Dict] = None, timeout: float = 60.0) -> Dict[str, Any]:
        """Send JSON-RPC request to server."""
        async with self._lock:
            if not self.process or not self._running:
                raise RuntimeError("MCP server not running")
            
            self.request_id += 1
            request = {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "method": method
            }
            
            if params is not None:
                request["params"] = params
            
            try:
                # Send request
                request_json = json.dumps(request) + "\n"
                self.process.stdin.write(request_json.encode('utf-8'))
                await self.process.stdin.drain()
                
                logger.debug(f"Sent request: {method}")
                
                # Leggi risposta in modo più robusto
                response_data = b""
                start_time = asyncio.get_event_loop().time()
                
                while True:
                    if asyncio.get_event_loop().time() - start_time > timeout:
                        raise asyncio.TimeoutError()
                    
                    try:
                        chunk = await asyncio.wait_for(
                            self.process.stdout.read(1024), 
                            timeout=1.0
                        )
                        if not chunk:
                            break
                        
                        response_data += chunk
                        
                        # Cerca una risposta JSON completa
                        if b'\n' in response_data:
                            lines = response_data.split(b'\n')
                            for line in lines[:-1]:  # Tutte tranne l'ultima (potrebbe essere incompleta)
                                try:
                                    response = json.loads(line.decode('utf-8'))
                                    if response.get('id') == self.request_id:
                                        logger.debug(f"Received response for: {method}")
                                        return response
                                except json.JSONDecodeError:
                                    continue
                            # Mantieni solo l'ultima linea incompleta
                            response_data = lines[-1]
                            
                    except asyncio.TimeoutError:
                        continue
                
                raise RuntimeError("No valid response received")
                
            except asyncio.TimeoutError:
                logger.error(f"Timeout waiting for response to {method}")
                raise RuntimeError(f"Timeout waiting for response to {method}")
            
            except Exception as e:
                logger.error(f"Error sending request: {e}")
                raise
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the MCP server.
        
        Returns:
            List of tool definitions
        """
        try:
            response = await self._send_request("tools/list")
            
            if "error" in response:
                raise RuntimeError(f"Error listing tools: {response['error']}")
            
            tools = response.get("result", {}).get("tools", [])
            logger.info(f"Listed {len(tools)} tools")
            
            return tools
        
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the MCP server.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        try:
            response = await self._send_request("tools/call", {
                "name": name,
                "arguments": arguments
            })
            
            if "error" in response:
                error_msg = response["error"].get("message", str(response["error"]))
                raise RuntimeError(f"Tool execution failed: {error_msg}")
            
            result = response.get("result", {})
            print(f"🔍 RAW TOOL RESULT: {json.dumps(result, indent=2)}")
            logger.info(f"Tool {name} executed successfully")
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to call tool {name}: {e}")
            raise
    
    async def stop(self) -> None:
        import sys
        """Stop the MCP server process."""
        if not self._running:
            return
        
        self._running = False
        
        try:
            # Cancella il reader task se esiste
            if hasattr(self, '_reader_task') and self._reader_task and not self._reader_task.done():
                self._reader_task.cancel()
                try:
                    await self._reader_task
                except asyncio.CancelledError:
                    pass
            
            if self.process:
                # Chiudi i transport in modo pulito su Windows
                if sys.platform == "win32":
                    # Su Windows, chiudi prima i pipe transport
                    for stream in [self.process.stdin, self.process.stdout, self.process.stderr]:
                        if stream and hasattr(stream, 'close'):
                            try:
                                stream.close()
                            except:
                                pass
                    
                    # Aspetta un attimo per la chiusura dei transport
                    await asyncio.sleep(0.1)
                
                # Termina il processo
                try:
                    self.process.terminate()
                    await asyncio.wait_for(self.process.wait(), timeout=3.0)
                    logger.info("MCP server stopped gracefully")
                except asyncio.TimeoutError:
                    # Forza la chiusura
                    try:
                        self.process.kill()
                        await self.process.wait()
                    except:
                        pass
                    logger.warning("MCP server killed (timeout)")
                
                # Su Windows, aspetta che i transport si chiudano
                if sys.platform == "win32":
                    await asyncio.sleep(0.5)
        
        except Exception as e:
            logger.error(f"Error stopping MCP server: {e}")
        
        finally:
            self.process = None
            if hasattr(self, '_responses'):
                self._responses.clear()
            if hasattr(self, '_events'):
                self._events.clear()

    async def __aenter__(self):
        """Context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        import sys
        """Context manager exit."""
        try:
            await self.stop()
            # Dai tempo ad asyncio di pulire su Windows
            if sys.platform == "win32":
                await asyncio.sleep(0.5)
        except:
            pass  # Ignora errori durante la chiusura


class MCPStdioAdapter:
    """
    Adapter to expose stdio MCP server as HTTP-compatible interface.
    
    This allows stdio servers to work seamlessly with PolyAgent.
    """
    
    def __init__(self, client: MCPStdioClient):
        """
        Initialize adapter.
        
        Args:
            client: Stdio client instance
        """
        self.client = client
        self._tools_cache: Optional[List[Dict]] = None
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get tools in PolyMCP HTTP format.
        
        Returns:
            List of tools in HTTP format
        """
        if self._tools_cache is not None:
            return self._tools_cache
        
        stdio_tools = await self.client.list_tools()
        
        # Convert to PolyMCP format
        http_tools = []
        for tool in stdio_tools:
            http_tool = {
                "name": tool.get("name"),
                "description": tool.get("description", ""),
                "input_schema": tool.get("inputSchema", {})
            }
            http_tools.append(http_tool)
        
        self._tools_cache = http_tools
        return http_tools
    
    async def invoke_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke tool in HTTP-compatible format.
        
        Args:
            tool_name: Name of tool to invoke
            parameters: Tool parameters
            
        Returns:
            Result in HTTP format
        """
        try:
            result = await self.client.call_tool(tool_name, parameters)
            print(f"📦 WRAPPED RESULT: {json.dumps({'result': result, 'status': 'success'}, indent=2)}")
            return {
                "result": result,
                "status": "success"
            }
        
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }