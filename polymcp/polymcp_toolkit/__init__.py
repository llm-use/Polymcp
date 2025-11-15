"""PolyMCP Toolkit - Expose Python functions as MCP tools"""

from .expose import (
    expose_tools,           # Legacy, backward compatibility
    expose_tools_http,      # HTTP server mode
    expose_tools_inprocess, # In-process mode
    InProcessMCPServer,     # In-process server class
)

__all__ = [
    'expose_tools',
    'expose_tools_http', 
    'expose_tools_inprocess',
    'InProcessMCPServer',
]
