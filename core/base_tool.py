# =============================================================================
# Reasoning Agents Framework - Base Tool Class
# =============================================================================
"""
Helper class for creating MCP tools in the framework.

This module provides utilities for creating MCP (Model Context Protocol) tools:
- BaseTool class for common initialization patterns
- Helper functions for tool creation

MCP tools are the "hands" of the system - they execute deterministic operations
like database queries, file operations, API calls, and rule evaluation.

Example using BaseTool:
    from core.base_tool import BaseTool
    from fastmcp import FastMCP
    
    class MyTool(BaseTool):
        def __init__(self):
            super().__init__(name="My Tool", port=11003)
        
        def register_tools(self, mcp: FastMCP):
            @mcp.tool()
            def my_function(arg: str) -> dict:
                return {"result": arg.upper()}

Example using create_mcp_server directly:
    from core.base_tool import create_mcp_server
    
    mcp = create_mcp_server("My Tool", port=11003)
    
    @mcp.tool()
    def my_function(arg: str) -> dict:
        return {"result": arg.upper()}
    
    mcp.run(transport="streamable-http")
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

from fastmcp import FastMCP

from core.config import Config, get_config
from core.logging_utils import log_event, setup_logging


class BaseTool(ABC):
    """
    Base class for MCP tools.
    
    Provides common functionality:
    - FastMCP server initialization
    - Logging setup
    - Configuration access
    - Standard startup procedure
    
    Subclasses must implement:
    - register_tools(mcp: FastMCP) - Register your @mcp.tool() functions
    
    Attributes:
        name: Tool name
        port: Port number
        config: Configuration instance
        logger: Configured logger
        mcp: FastMCP server instance
    
    Example:
        class ContractQueryTool(BaseTool):
            def __init__(self):
                super().__init__(name="Contract Query", port=11001)
            
            def register_tools(self, mcp: FastMCP):
                @mcp.tool()
                def query_contracts(sql: str) -> dict:
                    # Implementation
                    return {"results": [...]}
    """
    
    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------
    
    def __init__(
        self,
        name: str,
        port: int,
        config: Optional[Config] = None
    ):
        """
        Initialize the base tool.
        
        Args:
            name: Human-readable name for the tool
            port: Port number to run on
            config: Optional Config instance (uses default if not provided)
        """
        self.name = name
        self.port = port
        self.config = config or get_config()
        
        # Setup logging
        self.logger = setup_logging(
            name.replace(" ", ""),
            log_level=self.config.log_level,
            log_to_file=True
        )
        
        # Ensure directories exist
        self.config.ensure_directories()
        
        # Create FastMCP server
        self.mcp = FastMCP(name)
        
        # Register tools from subclass
        self.register_tools(self.mcp)
        
        self.logger.info(f"Initialized {name} on port {port}")
    
    # -------------------------------------------------------------------------
    # Abstract Methods (must be implemented by subclasses)
    # -------------------------------------------------------------------------
    
    @abstractmethod
    def register_tools(self, mcp: FastMCP) -> None:
        """
        Register MCP tools with the server.
        
        Subclasses must implement this to register their tools.
        Use the @mcp.tool() decorator to register functions.
        
        Args:
            mcp: The FastMCP server instance
        
        Example:
            def register_tools(self, mcp: FastMCP):
                @mcp.tool()
                def my_tool(arg: str) -> dict:
                    '''Tool docstring shown in MCP.'''
                    return {"result": arg}
        """
        pass
    
    # -------------------------------------------------------------------------
    # Logging Helpers
    # -------------------------------------------------------------------------
    
    def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Log a structured event.
        
        Args:
            event_type: Type of event (e.g., "QUERY_EXECUTED")
            data: Event data dictionary
        """
        log_event(self.name.replace(" ", ""), event_type, data)
    
    # -------------------------------------------------------------------------
    # Lifecycle Methods
    # -------------------------------------------------------------------------
    
    def run(self, host: str = "0.0.0.0"):
        """
        Start the MCP tool server.
        
        Args:
            host: Host address to bind to
        """
        self.logger.info(f"🔧 Starting {self.name} on {host}:{self.port}")
        self.mcp.settings.host = host
        self.mcp.settings.port = self.port
        self.mcp.run(transport="streamable-http")


# =============================================================================
# Standalone Helper Functions
# =============================================================================

def create_mcp_server(
    name: str,
    port: int,
    host: str = "0.0.0.0"
) -> FastMCP:
    """
    Create a configured FastMCP server.
    
    Use this for simple tools that don't need the full BaseTool class.
    
    Args:
        name: Server name
        port: Port to run on
        host: Host to bind to
    
    Returns:
        Configured FastMCP instance
    
    Example:
        mcp = create_mcp_server("My Tool", 11003)
        
        @mcp.tool()
        def my_function(arg: str) -> dict:
            return {"result": arg}
        
        # In __main__:
        mcp.run(transport="streamable-http")
    """
    mcp = FastMCP(name)
    mcp.settings.host = host
    mcp.settings.port = port
    return mcp


def get_data_path(filename: str) -> Path:
    """
    Get the full path to a file in the data directory.
    
    Args:
        filename: Name of the file in data/
    
    Returns:
        Full Path object
    
    Example:
        >>> path = get_data_path("contracts.csv")
        >>> df = pd.read_csv(path)
    """
    config = get_config()
    return config.data_dir / filename


def get_results_path(filename: str) -> Path:
    """
    Get the full path for saving query results.
    
    Creates the query_results directory if it doesn't exist.
    
    Args:
        filename: Name for the results file
    
    Returns:
        Full Path object
    
    Example:
        >>> path = get_results_path("high_liability.csv")
        >>> df.to_csv(path, index=False)
    """
    config = get_config()
    results_dir = config.data_dir / "query_results"
    results_dir.mkdir(exist_ok=True)
    return results_dir / filename
