# =============================================================================
# Reasoning Agents Framework - Logging Utilities
# =============================================================================
"""
Structured logging utilities for the framework.

This module provides:
- setup_logging: Configure logging for agents and tools
- log_event: Log structured events to JSONL files for audit trails
- LoggerAdapter: Custom adapter with agent context

Usage:
    from core.logging_utils import setup_logging, log_event
    
    # Setup logging for an agent
    logger = setup_logging("MyAgent", log_to_file=True)
    logger.info("Agent started")
    
    # Log a structured event
    log_event("MyAgent", "QUERY_RECEIVED", {"query": "test"})
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


# =============================================================================
# Logging Setup
# =============================================================================

def setup_logging(
    name: str,
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_dir: Optional[Path] = None
) -> logging.Logger:
    """
    Configure and return a logger for an agent or tool.
    
    Creates a logger with:
    - Console output (always)
    - File output (optional, to logs/<name>.log)
    
    Args:
        name: Name for the logger (e.g., "ClauseAgent")
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Whether to also log to a file
        log_dir: Custom log directory (defaults to project logs/)
    
    Returns:
        Configured logging.Logger instance
    
    Example:
        >>> logger = setup_logging("ClauseAgent", log_level="DEBUG")
        >>> logger.info("Agent started on port 8101")
        2024-01-15 10:30:00 - ClauseAgent - INFO - Agent started on port 8101
    """
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    # Set level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (always add)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_to_file:
        # Determine log directory
        if log_dir is None:
            # Default: project_root/logs/
            log_dir = Path(__file__).parent.parent / "logs"
        
        log_dir.mkdir(exist_ok=True)
        
        # Create file handler
        log_file = log_dir / f"{name.lower()}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# =============================================================================
# Structured Event Logging
# =============================================================================

def log_event(
    source: str,
    event_type: str,
    data: Dict[str, Any],
    log_dir: Optional[Path] = None
) -> None:
    """
    Log a structured event to a JSONL file for audit trails.
    
    Events are written as JSON Lines (one JSON object per line) to
    logs/<source>_events.jsonl. This enables:
    - Full audit trails of system activity
    - Easy parsing with tools like jq
    - Time-series analysis of agent behavior
    
    Args:
        source: Name of the component logging the event (e.g., "ClauseAgent")
        event_type: Type of event (e.g., "QUERY_RECEIVED", "TOOL_CALLED")
        data: Dictionary of event data (will be JSON serialized)
        log_dir: Custom log directory (defaults to project logs/)
    
    Example:
        >>> log_event("ClauseAgent", "QUERY_RECEIVED", {
        ...     "query": "Find contracts with high liability",
        ...     "timestamp": "2024-01-15T10:30:00"
        ... })
        
        # Output in logs/clauseagent_events.jsonl:
        {"timestamp": "2024-01-15T10:30:00.123", "source": "ClauseAgent", 
         "type": "QUERY_RECEIVED", "data": {"query": "Find contracts..."}}
    """
    # Determine log directory
    if log_dir is None:
        log_dir = Path(__file__).parent.parent / "logs"
    
    log_dir.mkdir(exist_ok=True)
    
    # Create event record
    event = {
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "type": event_type,
        "data": data
    }
    
    # Write to JSONL file
    events_file = log_dir / f"{source.lower()}_events.jsonl"
    with open(events_file, 'a') as f:
        f.write(json.dumps(event) + '\n')
    
    # Also log to standard logger at INFO level
    logger = logging.getLogger(source)
    if logger.handlers:  # Only log if logger is configured
        logger.info(f"[{event_type}] {json.dumps(data)}")


# =============================================================================
# Context Logger Adapter
# =============================================================================

class AgentLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds agent context to all log messages.
    
    Use this when you need to add consistent context (like request IDs)
    to all log messages from an agent.
    
    Example:
        >>> base_logger = setup_logging("ClauseAgent")
        >>> logger = AgentLoggerAdapter(base_logger, {"agent_id": "agent-001"})
        >>> logger.info("Processing query")
        2024-01-15 10:30:00 - ClauseAgent - INFO - [agent-001] Processing query
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add context prefix to the log message."""
        context_str = " ".join(f"[{v}]" for v in self.extra.values())
        return f"{context_str} {msg}", kwargs


# =============================================================================
# Utility Functions
# =============================================================================

def get_log_file_path(name: str, log_dir: Optional[Path] = None) -> Path:
    """
    Get the path to a log file.
    
    Args:
        name: Component name
        log_dir: Custom log directory
    
    Returns:
        Path to the log file
    """
    if log_dir is None:
        log_dir = Path(__file__).parent.parent / "logs"
    return log_dir / f"{name.lower()}.log"


def get_events_file_path(name: str, log_dir: Optional[Path] = None) -> Path:
    """
    Get the path to an events JSONL file.
    
    Args:
        name: Component name
        log_dir: Custom log directory
    
    Returns:
        Path to the events file
    """
    if log_dir is None:
        log_dir = Path(__file__).parent.parent / "logs"
    return log_dir / f"{name.lower()}_events.jsonl"
