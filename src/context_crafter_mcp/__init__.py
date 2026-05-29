"""context-crafter-mcp: Universal stdio MCP server for repository documentation."""

import warnings

from langchain_core._api.deprecation import LangChainPendingDeprecationWarning

warnings.filterwarnings("ignore", category=UserWarning, module="langgraph")
warnings.filterwarnings("ignore", category=PendingDeprecationWarning, module="langgraph")
warnings.filterwarnings("ignore", category=PendingDeprecationWarning, module="langchain_core")
warnings.simplefilter("ignore", LangChainPendingDeprecationWarning)

__version__ = "0.3.2"
