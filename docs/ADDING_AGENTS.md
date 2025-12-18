# Adding New Agents

This guide explains how to add new worker agents to the Reasoning Agents Framework.

## Overview

Agents in this framework:
1. Extend the `BaseAgent` class
2. Implement the `process_query()` method  
3. Connect to MCP tools for execution
4. Communicate via A2A protocol

## Quick Start: Copy an Existing Agent

The easiest way is to copy an existing worker agent:

```bash
cp agents/workers/worker_agent_1.py agents/workers/worker_agent_3.py
```

Then customize it by searching for `CUSTOMIZE` comments.

## Step-by-Step Guide

### 1. Create the Agent File

Create `agents/workers/worker_agent_3.py`:

```python
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.base_agent import BaseAgent
from core.config import get_config


class WorkerAgent3(BaseAgent):
    """Your agent's purpose."""
    
    def __init__(self):
        config = get_config()
        agents = config.get_agent_registry()
        agent_config = agents.get("worker_3", {})
        
        super().__init__(
            name="WorkerAgent3",
            port=agent_config.get("port", 8103),
            mcp_tools=["tool_1", "tool_3"],  # Your tools
            config=config
        )
    
    def get_system_prompt(self) -> str:
        prompt = self.config.load_prompt("worker_agent_3")
        if prompt:
            return prompt
        return "Default prompt for your agent..."
    
    async def process_query(self, query: str) -> str:
        try:
            result = await self.run_react_agent(query)
            return result
        except Exception as e:
            self.logger.error(f"Error: {e}")
            return f"Error: {str(e)}"


if __name__ == "__main__":
    print("🚀 Starting Worker Agent 3...")
    agent = WorkerAgent3()
    agent.run()
```

### 2. Create System Prompt

Create `prompts/worker_agent_3.txt`:

```text
You are a specialized agent for [your domain].

## Your Capabilities
1. Capability one
2. Capability two

## Available Tools
- tool_1: What this tool does
- tool_3: What this tool does

## Workflow
1. First: Discover available data/resources
2. Then: Execute your query
3. Finally: Summarize results

## CRITICAL RULES
1. Always call get_schema() first
2. Use actual column names from schema
3. Never make up data
```

### 3. Add to Registry

Add to `config/registry.yaml`:

```yaml
agents:
  worker_3:
    host: localhost
    port: 8103
    enabled: true
    description: "What your agent does"
    script: agents/workers/worker_agent_3.py
    uses_tools:
      - tool_1
      - tool_3
```

### 4. Update Run Script

Add to `run.sh` in `start_agents()`:

```bash
print_step "Starting Worker Agent 3 (port 8103)..."
uv run python agents/workers/worker_agent_3.py > logs/worker_agent_3.log 2>&1 &
echo $! >> "$PID_FILE"

wait_for_service 8103 "Worker Agent 3" || exit 1
```

Add cleanup in `cleanup()`:

```bash
pkill -f "agents/workers/worker_agent_3.py" 2>/dev/null || true
```

### 5. Update Manager (Optional)

To route queries to your new agent, update `agents/manager/manager_agent.py`:

1. Add URL configuration in `__init__()`:
```python
worker_3_config = agents.get("worker_3", {})
self.worker_agent_3_url = (
    f"http://{worker_3_config.get('host', 'localhost')}:"
    f"{worker_3_config.get('port', 8103)}"
)
```

2. Update `agent_map` in `_execute_plan()`:
```python
agent_map = {
    "worker_agent_1": self.worker_agent_1_url,
    "worker_agent_2": self.worker_agent_2_url,
    "worker_agent_3": self.worker_agent_3_url,
}
```

3. Update `prompts/manager_agent.txt` with the new agent.

## Testing Your Agent

```bash
# Start your agent
uv run python agents/workers/worker_agent_3.py

# Test it
curl -X POST http://localhost:8103/task \
  -H "Content-Type: application/json" \
  -d '{"message": {"content": {"text": "Your test query"}}}'
```

## Best Practices

1. **Single Responsibility**: Each agent handles one domain
2. **Descriptive Names**: Clear names for agent and skills
3. **Error Handling**: Catch and log errors gracefully
4. **Logging**: Use `self.logger` for debug info
5. **Event Logging**: Use `log_event()` for audit trails
