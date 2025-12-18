# =============================================================================
# Worker Agent 2 - A2A Implementation (Example: Validation/Compliance)
# =============================================================================
"""
Example worker agent specialized in validation and rule checking.

CUSTOMIZE THIS AGENT:
- Rename the class to match your use case
- Update mcp_tools list to connect to your tools
- Modify get_system_prompt() to define agent behavior
- Update process_query() with custom logic if needed

This agent connects to multiple MCP tools for validation tasks.

Usage:
    python -m agents.workers.worker_agent_2
    
    The agent will start on port 8102 (configurable in registry.yaml)
"""

import os
import sys

# Add parent directory to path for imports when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.base_agent import BaseAgent
from core.config import get_config


# =============================================================================
# Agent Definition
# =============================================================================

class WorkerAgent2(BaseAgent):
    """
    Example worker agent for validation and compliance.
    
    CUSTOMIZE: Rename this class and update the docstring
    to match your specific use case.
    """
    
    def __init__(self):
        """Initialize Worker Agent 2."""
        config = get_config()
        agents = config.get_agent_registry()
        
        # CUSTOMIZE: Change 'worker_2' to match your registry.yaml key
        agent_config = agents.get("worker_2", {})
        
        super().__init__(
            # CUSTOMIZE: Change the name
            name="WorkerAgent2",
            port=agent_config.get("port", 8102),
            # CUSTOMIZE: List the MCP tools this agent uses
            mcp_tools=["tool_1", "tool_2"],
            config=config
        )
    
    def get_system_prompt(self) -> str:
        """
        Load the system prompt that defines this agent's behavior.
        
        CUSTOMIZE: Create prompts/worker_agent_2.txt with your prompt
        or modify the fallback below.
        """
        prompt = self.config.load_prompt("worker_agent_2")
        if prompt:
            return prompt
        
        # Fallback default prompt - CUSTOMIZE this for your use case
        return """You are a validation and compliance specialist.

## Workflow
1. Call list_rules() first to discover available rules
2. Retrieve the data you need to validate
3. Run compliance checks and report findings

## Rules
- Always use tools to check compliance - never assume rules
- Report findings with severity levels
- Provide actionable recommendations
"""
    
    async def process_query(self, query: str) -> str:
        """
        Process a query using the ReAct agent pattern.
        
        CUSTOMIZE: Add preprocessing, postprocessing, or
        custom logic as needed.
        """
        try:
            result = await self.run_react_agent(query)
            return result
        except Exception as e:
            self.logger.error(f"Query processing error: {e}")
            return f"Error processing query: {str(e)}"


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    print("🚀 Starting Worker Agent 2...")
    agent_instance = WorkerAgent2()
    agent_instance.run()
