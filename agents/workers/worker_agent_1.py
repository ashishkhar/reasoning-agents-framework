# =============================================================================
# Worker Agent 1 - A2A Implementation (Example: Data Extraction)
# =============================================================================
"""
Example worker agent specialized in data extraction and analysis.

CUSTOMIZE THIS AGENT:
- Rename the class to match your use case
- Update mcp_tools list to connect to your tools
- Modify get_system_prompt() to define agent behavior
- Update process_query() with custom logic if needed

This agent connects to MCP tools and uses an LLM to interpret queries.

Usage:
    python -m agents.workers.worker_agent_1
    
    The agent will start on port 8101 (configurable in registry.yaml)
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

class WorkerAgent1(BaseAgent):
    """
    Example worker agent for data extraction.
    
    CUSTOMIZE: Rename this class and update the docstring
    to match your specific use case.
    """
    
    def __init__(self):
        """Initialize Worker Agent 1."""
        config = get_config()
        agents = config.get_agent_registry()
        
        # CUSTOMIZE: Change 'worker_1' to match your registry.yaml key
        agent_config = agents.get("worker_1", {})
        
        super().__init__(
            # CUSTOMIZE: Change the name
            name="WorkerAgent1",
            port=agent_config.get("port", 8101),
            # CUSTOMIZE: List the MCP tools this agent uses
            mcp_tools=["tool_1"],
            config=config
        )
    
    def get_system_prompt(self) -> str:
        """
        Load the system prompt that defines this agent's behavior.
        
        CUSTOMIZE: Create prompts/worker_agent_1.txt with your prompt
        or modify the fallback below.
        """
        prompt = self.config.load_prompt("worker_agent_1")
        if prompt:
            return prompt
        
        # Fallback default prompt - CUSTOMIZE this for your use case
        return """You are a data extraction and analysis specialist.

## Workflow
1. Call get_schema() first to discover available data
2. Use the actual column names to construct queries
3. Summarize findings for the user

## Rules
- Always use tools to get data - never make up information
- When you receive results, summarize them clearly
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
    print("🚀 Starting Worker Agent 1...")
    agent_instance = WorkerAgent1()
    agent_instance.run()
