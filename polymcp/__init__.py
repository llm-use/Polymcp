"""
PolyMCP - Universal MCP Agent & Toolkit
"""

from .polyagent.agent import PolyAgent
from .polyagent.llm_providers import (
    LLMProvider,
    OpenAIProvider,
    AnthropicProvider,
    OllamaProvider,
    KimiProvider,
    DeepSeekProvider
)
from .polymcp_toolkit.expose import expose_tools

# Importa la versione da version.py invece di definirla qui
try:
    from .version import __version__
except ImportError:
    __version__ = "0.0.0.dev0"

__all__ = [
    'PolyAgent',
    'LLMProvider',
    'OpenAIProvider',
    'AnthropicProvider',
    'OllamaProvider',
    'KimiProvider',
    'DeepSeekProvider',
    'expose_tools',
    '__version__',
]
