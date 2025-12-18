# =============================================================================
# Reasoning Agents Framework - Configuration Management
# =============================================================================
"""
Centralized configuration management for the framework.

This module provides a Config class that:
- Loads settings from .env files
- Loads settings from YAML registry files
- Provides typed accessors for all configuration options
- Uses sensible defaults for optional settings

Usage:
    from core.config import Config
    
    config = Config()
    api_key = config.api_key
    model = config.model
    agents = config.get_agent_registry()
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv


class Config:
    """
    Centralized configuration manager for the framework.
    
    Loads configuration from:
    1. Environment variables (.env file)
    2. YAML registry files (config/registry.yaml)
    
    Attributes:
        api_key: LLM API key
        model: LLM model name
        temperature: Model temperature setting
        base_url: Optional custom API endpoint
        log_level: Logging level
    
    Example:
        >>> config = Config()
        >>> print(config.model)
        'gpt-4o-mini'
        >>> agents = config.get_agent_registry()
        >>> print(agents['manager']['port'])
        8100
    """
    
    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------
    
    def __init__(self, env_path: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            env_path: Optional path to .env file. If not provided,
                     searches for .env in the project root.
        """
        # Determine project root (parent of core/ directory)
        self._root = Path(__file__).parent.parent
        
        # Load .env file
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv(self._root / ".env")
        
        # Cache for registry data
        self._registry_cache: Optional[Dict[str, Any]] = None
    
    # -------------------------------------------------------------------------
    # LLM Configuration Properties
    # -------------------------------------------------------------------------
    
    @property
    def api_key(self) -> str:
        """Get the LLM API key."""
        return os.getenv("API_KEY", "")
    
    @property
    def model(self) -> str:
        """Get the LLM model name."""
        return os.getenv("MODEL", "gpt-4o-mini")
    
    @property
    def temperature(self) -> float:
        """Get the model temperature."""
        return float(os.getenv("TEMPERATURE", "0"))
    
    @property
    def base_url(self) -> Optional[str]:
        """Get the optional custom API endpoint."""
        url = os.getenv("BASE_URL", "").strip()
        return url if url else None
    
    # -------------------------------------------------------------------------
    # Logging Configuration
    # -------------------------------------------------------------------------
    
    @property
    def log_level(self) -> str:
        """Get the logging level."""
        return os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def log_dir(self) -> Path:
        """Get the logs directory path."""
        return self._root / "logs"
    
    # -------------------------------------------------------------------------
    # Directory Paths
    # -------------------------------------------------------------------------
    
    @property
    def root_dir(self) -> Path:
        """Get the project root directory."""
        return self._root
    
    @property
    def data_dir(self) -> Path:
        """Get the data directory path."""
        return self._root / "data"
    
    @property
    def prompts_dir(self) -> Path:
        """Get the prompts directory path."""
        return self._root / "prompts"
    
    @property
    def config_dir(self) -> Path:
        """Get the config directory path."""
        return self._root / "config"
    
    # -------------------------------------------------------------------------
    # Registry Methods
    # -------------------------------------------------------------------------
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load and cache the registry YAML file."""
        if self._registry_cache is not None:
            return self._registry_cache
        
        registry_path = self.config_dir / "registry.yaml"
        if registry_path.exists():
            with open(registry_path, 'r') as f:
                self._registry_cache = yaml.safe_load(f) or {}
        else:
            self._registry_cache = {}
        
        return self._registry_cache
    
    def get_agent_registry(self) -> Dict[str, Any]:
        """
        Get the agent registry configuration.
        
        Returns:
            Dictionary mapping agent names to their configurations.
            Each agent config includes: host, port, description, enabled.
        
        Example:
            >>> agents = config.get_agent_registry()
            >>> agents['manager']
            {'host': 'localhost', 'port': 8100, 'enabled': True}
        """
        registry = self._load_registry()
        return registry.get("agents", {})
    
    def get_tool_registry(self) -> Dict[str, Any]:
        """
        Get the MCP tool registry configuration.
        
        Returns:
            Dictionary mapping tool names to their configurations.
            Each tool config includes: host, port, description, enabled.
        
        Example:
            >>> tools = config.get_tool_registry()
            >>> tools['contract_query']
            {'host': 'localhost', 'port': 11001, 'enabled': True}
        """
        registry = self._load_registry()
        return registry.get("tools", {})
    
    def get_agent_url(self, agent_name: str) -> str:
        """
        Get the full URL for an agent.
        
        Args:
            agent_name: Name of the agent (e.g., 'manager', 'clause')
        
        Returns:
            Full URL string (e.g., 'http://localhost:8100')
        """
        agents = self.get_agent_registry()
        if agent_name in agents:
            agent = agents[agent_name]
            host = agent.get("host", "localhost")
            port = agent.get("port", 8000)
            return f"http://{host}:{port}"
        return ""
    
    def get_tool_url(self, tool_name: str) -> str:
        """
        Get the full MCP URL for a tool.
        
        Args:
            tool_name: Name of the tool (e.g., 'contract_query')
        
        Returns:
            Full MCP URL string (e.g., 'http://localhost:11001/mcp')
        """
        tools = self.get_tool_registry()
        if tool_name in tools:
            tool = tools[tool_name]
            host = tool.get("host", "localhost")
            port = tool.get("port", 11000)
            return f"http://{host}:{port}/mcp"
        return ""
    
    # -------------------------------------------------------------------------
    # Prompt Loading
    # -------------------------------------------------------------------------
    
    def load_prompt(self, prompt_name: str) -> str:
        """
        Load a system prompt from the prompts directory.
        
        Args:
            prompt_name: Name of the prompt file (without .txt extension)
        
        Returns:
            Contents of the prompt file, or empty string if not found.
        
        Example:
            >>> prompt = config.load_prompt("manager")
            >>> print(prompt[:50])
            'You are a Legal Reasoning Manager Agent...'
        """
        prompt_path = self.prompts_dir / f"{prompt_name}.txt"
        if prompt_path.exists():
            with open(prompt_path, 'r') as f:
                return f.read().strip()
        return ""
    
    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------
    
    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.log_dir.mkdir(exist_ok=True)
        (self.data_dir / "query_results").mkdir(parents=True, exist_ok=True)
    
    def __repr__(self) -> str:
        """String representation of config."""
        return (
            f"Config(model={self.model!r}, "
            f"temperature={self.temperature}, "
            f"log_level={self.log_level!r})"
        )


# =============================================================================
# Module-level convenience instance
# =============================================================================
# Create a default config instance for easy access
_default_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the default configuration instance.
    
    This creates a singleton Config instance for module-level access.
    
    Returns:
        The default Config instance.
    
    Example:
        >>> from core.config import get_config
        >>> config = get_config()
        >>> print(config.model)
    """
    global _default_config
    if _default_config is None:
        _default_config = Config()
    return _default_config
