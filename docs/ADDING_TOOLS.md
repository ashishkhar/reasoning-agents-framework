# Adding New Tools

This guide explains how to add new MCP tools to the Reasoning Agents Framework.

## Overview

MCP tools are the "hands" of the system. They execute deterministic operations:
- Database queries
- API calls
- File operations
- Rule evaluation
- Calculations

## Quick Start: Copy an Existing Tool

The easiest way to add a new tool is to copy `tools/tool_1.py` or `tools/tool_2.py`:

```bash
cp tools/tool_1.py tools/tool_3.py
```

Then customize it by searching for `CUSTOMIZE` comments.

## Step-by-Step Guide

### 1. Create the Tool File

Create `tools/tool_3.py`:

```python
import os
import sys
from typing import Any, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP
from core.config import get_config
from core.logging_utils import log_event, setup_logging

# CUSTOMIZE: Change these
config = get_config()
logger = setup_logging("Tool3", log_level=config.log_level)
mcp = FastMCP("Your Tool Name")


@mcp.tool()
def your_function(arg1: str, arg2: int) -> Dict[str, Any]:
    """
    Clear description of what this tool does.
    
    Args:
        arg1: Description of first argument
        arg2: Description of second argument
    
    Returns:
        Dictionary with success flag and result
    """
    try:
        log_event("Tool3", "FUNCTION_CALLED", {"arg1": arg1, "arg2": arg2})
        
        # Your implementation here
        result = f"{arg1} - {arg2}"
        
        return {"success": True, "result": result}
        
    except Exception as e:
        log_event("Tool3", "ERROR", {"error": str(e)})
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    port = int(os.getenv("TOOL_3_PORT", "11003"))
    logger.info(f"Starting Tool 3 on port {port}")
    
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = port
    mcp.run(transport="streamable-http")
```

### 2. Add to Registry

Add to `config/registry.yaml`:

```yaml
tools:
  tool_3:
    host: localhost
    port: 11003
    enabled: true
    description: "What your tool does"
    script: tools/tool_3.py
```

### 3. Update Run Script

Add to `run.sh` in the `start_tools()` function:

```bash
print_step "Starting Tool 3 (port 11003)..."
uv run python tools/tool_3.py > logs/tool_3.log 2>&1 &
echo $! >> "$PID_FILE"

wait_for_service 11003 "Tool 3" || exit 1
```

### 4. Connect Agent to Tool

Update the agent's `__init__()`:

```python
super().__init__(
    name="YourAgent",
    port=8101,
    mcp_tools=["tool_1", "tool_3"],  # Add tool_3
    config=config
)
```

## Tool Design Patterns

### Database Tool

```python
import duckdb

@mcp.tool()
def query_data(sql: str, output_file: str) -> Dict[str, Any]:
    """Execute SQL query and save results."""
    conn = duckdb.connect(':memory:')
    result = conn.execute(sql).fetchdf()
    result.to_csv(f"data/query_results/{output_file}")
    return {"success": True, "row_count": len(result)}
```

### API Tool

```python
import httpx

@mcp.tool()
def call_api(endpoint: str, params: dict) -> Dict[str, Any]:
    """Call external API."""
    response = httpx.get(endpoint, params=params)
    return {"success": True, "data": response.json()}
```

### File Tool

```python
from pathlib import Path

@mcp.tool()
def read_file(filename: str) -> Dict[str, Any]:
    """Read file contents."""
    path = Path("data") / filename
    if not path.exists():
        return {"success": False, "error": "File not found"}
    return {"success": True, "content": path.read_text()}
```

## Testing Your Tool

```bash
# Start your tool
uv run python tools/tool_3.py

# In another terminal, check it's running
curl http://localhost:11003/
```

## Best Practices

1. **Return Consistent Structure**: Always return `{"success": bool, ...}`
2. **Handle Errors**: Catch exceptions, return error messages
3. **Log Events**: Use `log_event()` for audit trails
4. **Document Tools**: Docstrings become MCP tool descriptions
5. **Type Hints**: Use proper typing for parameters
