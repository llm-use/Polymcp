"""
MCP Tool Exposure Module
Production-ready framework for exposing Python functions as MCP tools.
"""

import inspect
import asyncio
from typing import Callable, List, Dict, Any, get_type_hints, Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, create_model, Field
from docstring_parser import parse


def _extract_function_metadata(func: Callable) -> Dict[str, Any]:
    """Extract metadata from a function using type hints and docstring."""
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    docstring = parse(func.__doc__ or "")
    description = docstring.short_description or func.__name__
    
    input_fields = {}
    for param_name, param in sig.parameters.items():
        param_type = type_hints.get(param_name, str)
        param_doc = next(
            (p.description for p in docstring.params if p.arg_name == param_name),
            ""
        )
        
        if param.default != inspect.Parameter.empty:
            input_fields[param_name] = (param_type, Field(default=param.default, description=param_doc))
        else:
            input_fields[param_name] = (param_type, Field(description=param_doc))
    
    return_type = type_hints.get('return', str)
    
    return {
        "name": func.__name__,
        "description": description,
        "input_fields": input_fields,
        "return_type": return_type,
        "is_async": asyncio.iscoroutinefunction(func)
    }


def _create_input_model(func_name: str, input_fields: Dict) -> type:
    """Create a Pydantic model for function input validation."""
    if not input_fields:
        return create_model(f"{func_name}_Input")
    return create_model(f"{func_name}_Input", **input_fields)


def _create_output_model(func_name: str, return_type: type) -> type:
    """Create a Pydantic model for function output."""
    return create_model(
        f"{func_name}_Output",
        result=(return_type, Field(description="Function result"))
    )


def expose_tools(
    tools: Union[Callable, List[Callable]],
    title: str = "MCP Tool Server",
    description: str = "FastAPI server exposing Python functions as MCP tools",
    version: str = "1.0.0"
) -> FastAPI:
    """
    Expose Python functions as MCP tools via FastAPI.
    
    Creates a FastAPI application with MCP-compliant endpoints:
    - GET /mcp/list_tools: List all available tools
    - POST /mcp/invoke/{tool_name}: Invoke a specific tool
    
    Args:
        tools: Single function or list of functions to expose
        title: API title
        description: API description
        version: API version
        
    Returns:
        FastAPI application instance
    
    Example:
        >>> def add(a: int, b: int) -> int:
        ...     '''Add two numbers.'''
        ...     return a + b
        >>> 
        >>> app = expose_tools(add)
        >>> # Run with: uvicorn main:app
    """
    if not isinstance(tools, list):
        tools = [tools]
    
    app = FastAPI(title=title, description=description, version=version)
    
    tool_registry = {}
    
    for func in tools:
        metadata = _extract_function_metadata(func)
        input_model = _create_input_model(metadata["name"], metadata["input_fields"])
        output_model = _create_output_model(metadata["name"], metadata["return_type"])
        
        input_schema = input_model.model_json_schema()
        output_schema = output_model.model_json_schema()
        
        tool_registry[metadata["name"]] = {
            "metadata": {
                "name": metadata["name"],
                "description": metadata["description"],
                "input_schema": input_schema,
                "output_schema": output_schema
            },
            "function": func,
            "input_model": input_model,
            "is_async": metadata["is_async"]
        }
    
    @app.get("/mcp/list_tools")
    async def list_tools():
        """List all available MCP tools."""
        return {
            "tools": [tool["metadata"] for tool in tool_registry.values()]
        }
    
    @app.post("/mcp/invoke/{tool_name}")
    async def invoke_tool(tool_name: str, payload: Dict[str, Any] = None):
        """Invoke a specific MCP tool."""
        if tool_name not in tool_registry:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found. Available: {list(tool_registry.keys())}"
            )
        
        tool = tool_registry[tool_name]
        
        try:
            validated_input = tool["input_model"](**(payload or {}))
            params = validated_input.model_dump()
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid input parameters: {str(e)}"
            )
        
        try:
            if tool["is_async"]:
                result = await tool["function"](**params)
            else:
                result = tool["function"](**params)
            
            return {"result": result, "status": "success"}
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Tool execution failed: {str(e)}"
            )
    
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": title,
            "description": description,
            "version": version,
            "endpoints": {
                "list_tools": "/mcp/list_tools",
                "invoke_tool": "/mcp/invoke/{tool_name}"
            },
            "available_tools": list(tool_registry.keys())
        }
    
    return app