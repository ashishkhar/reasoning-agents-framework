# =============================================================================
# Reasoning Agents Framework - Core Module
# =============================================================================
"""
Core module providing base classes and utilities for the reasoning agents framework.

This module exports:
- BaseAgent: Abstract base class for all A2A agents
- BaseTool: Helper class for MCP tool creation
- Config: Centralized configuration management
- setup_logging: Logging configuration utility
- log_event: Structured event logging
"""

from core.base_agent import BaseAgent
from core.base_tool import BaseTool
from core.config import Config
from core.logging_utils import setup_logging, log_event

__all__ = [
    "BaseAgent",
    "BaseTool", 
    "Config",
    "setup_logging",
    "log_event",
]

__version__ = "1.0.0"
