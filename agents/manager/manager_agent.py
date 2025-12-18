# =============================================================================
# Legal Reasoning Manager Agent - A2A Implementation
# =============================================================================
"""
Manager agent that orchestrates worker agents for legal document analysis.

This agent acts as the brain of the system:
- Receives user queries
- Classifies query complexity
- Plans which workers to call (and in what order)
- Executes the plan (parallel or sequential)
- Synthesizes results into comprehensive answers

The manager does NOT connect to MCP tools directly. Instead, it
delegates work to specialized worker agents via A2A protocol.

Usage:
    # As standalone server:
    python -m agents.manager.manager_agent
    
    # The agent will start on port 8100 (configurable in registry.yaml)

A2A Endpoint:
    POST http://localhost:8100/task
    
Skills:
    - analyze_legal_query: Full legal analysis with orchestration
"""

import asyncio
import json
import os
import re
import sys
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from python_a2a import A2AServer, agent, skill
from python_a2a.models import Task, TaskState, TaskStatus

# Add parent directory to path for imports when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.config import get_config
from core.logging_utils import log_event, setup_logging


# =============================================================================
# Enums and Types
# =============================================================================

class QueryComplexity(Enum):
    """Classification of query complexity."""
    SIMPLE = "simple"    # Single agent call
    COMPLEX = "complex"  # Multiple agents or reasoning steps


# =============================================================================
# Agent Definition
# =============================================================================

@agent(
    name="Legal Reasoning Manager",
    description="Orchestrates legal analysis by coordinating clause extraction and compliance checking",
    version="1.0.0"
)
class LegalManagerAgent(A2AServer):
    """
    Manager agent for legal document reasoning.
    
    This agent does NOT extend BaseAgent because it has special
    orchestration logic instead of MCP tool connections.
    
    Workflow:
    1. Classify query complexity (SIMPLE/COMPLEX)
    2. Plan execution (which agents, parallel/sequential)
    3. Execute plan by calling worker agents
    4. Synthesize results into final answer
    
    Example queries:
    - "What's the termination clause for CTR-001?" (SIMPLE → Clause)
    - "Is CTR-003 compliant?" (SIMPLE → Compliance)
    - "Analyze all contracts and find violations" (COMPLEX → Both)
    """
    
    def __init__(self):
        """Initialize the Manager Agent."""
        # Load configuration
        self.config = get_config()
        agents = self.config.get_agent_registry()
        manager_config = agents.get("manager", {})
        
        # Set port
        self.port = manager_config.get("port", 8100)
        
        # Initialize A2A server
        super().__init__(url=f"http://localhost:{self.port}")
        
        # Setup logging
        self.logger = setup_logging(
            "ManagerAgent",
            log_level=self.config.log_level
        )
        
        # Worker agent URLs - CUSTOMIZE: Change these to match your registry.yaml
        worker_1_config = agents.get("worker_1", {})
        worker_2_config = agents.get("worker_2", {})
        
        self.worker_agent_1_url = (
            f"http://{worker_1_config.get('host', 'localhost')}:"
            f"{worker_1_config.get('port', 8101)}"
        )
        self.worker_agent_2_url = (
            f"http://{worker_2_config.get('host', 'localhost')}:"
            f"{worker_2_config.get('port', 8102)}"
        )
        
        # Ensure directories exist
        self.config.ensure_directories()
        
        self.logger.info(f"Initialized Manager Agent on port {self.port}")
        self.logger.info(f"  Worker Agent 1: {self.worker_agent_1_url}")
        self.logger.info(f"  Worker Agent 2: {self.worker_agent_2_url}")
    
    # -------------------------------------------------------------------------
    # LLM Helpers
    # -------------------------------------------------------------------------
    
    def _create_llm(
        self,
        temperature: float = 0.0,
        max_tokens: int = 4000
    ) -> ChatOpenAI:
        """Create a configured LLM instance."""
        params = {
            "model": self.config.model,
            "api_key": self.config.api_key,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if self.config.base_url:
            params["base_url"] = self.config.base_url
        return ChatOpenAI(**params)
    
    # -------------------------------------------------------------------------
    # Query Classification
    # -------------------------------------------------------------------------
    
    async def _classify_complexity(self, query: str) -> QueryComplexity:
        """
        Classify query complexity using LLM.
        
        Args:
            query: User's query
        
        Returns:
            SIMPLE if one agent needed, COMPLEX if multiple
        """
        try:
            llm = self._create_llm(temperature=0.0, max_tokens=100)
            
            prompt = f"""Classify this legal query:

Query: {query}

Is this SIMPLE (needs one agent) or COMPLEX (needs multiple agents or steps)?

Reply with only: SIMPLE or COMPLEX"""
            
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            classification = response.content.strip().upper()
            
            if "COMPLEX" in classification:
                return QueryComplexity.COMPLEX
            return QueryComplexity.SIMPLE
            
        except Exception as e:
            self.logger.warning(f"Classification error: {e}, defaulting to SIMPLE")
            return QueryComplexity.SIMPLE
    
    # -------------------------------------------------------------------------
    # Execution Planning
    # -------------------------------------------------------------------------
    
    async def _plan_execution(self, query: str) -> Dict[str, Any]:
        """
        Plan which agents to call and in what order.
        
        Args:
            query: User's query
        
        Returns:
            Plan dict with agents, parallel flag, and reasoning
        """
        try:
            llm = self._create_llm(temperature=0.0, max_tokens=500)
            
            prompt = f"""Plan the execution for this legal query:

Query: {query}

Available agents:
- worker_agent_1: Extract and analyze data (Worker Agent 1)
- worker_agent_2: Validate data against rules (Worker Agent 2)

Decide the execution plan. Return JSON:
{{
    "agents": ["agent1", "agent2"],
    "parallel": true/false,
    "reasoning": "why this plan"
}}

If parallel=true, queries run simultaneously. If false, run sequentially."""
            
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            # Parse JSON from response
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                plan = json.loads(match.group())
                return plan
            
            # Default plan
            return {
                "agents": ["worker_agent_1"],
                "parallel": False,
                "reasoning": "Default to data extraction"
            }
            
        except Exception as e:
            self.logger.error(f"Planning error: {e}")
            return {"agents": ["worker_agent_1"], "parallel": False}
    
    # -------------------------------------------------------------------------
    # Worker Agent Communication
    # -------------------------------------------------------------------------
    
    async def _call_worker(
        self,
        agent_url: str,
        query: str,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Call a worker agent via A2A protocol.
        
        Args:
            agent_url: Base URL of the worker agent
            query: Query to send
            timeout: Request timeout in seconds
        
        Returns:
            Response dict with success flag and result
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{agent_url}/task",
                    json={
                        "message": {
                            "content": {"text": query}
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "result": result,
                            "agent_url": agent_url
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "agent_url": agent_url
                        }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Timeout", "agent_url": agent_url}
        except Exception as e:
            return {"success": False, "error": str(e), "agent_url": agent_url}
    
    async def _execute_plan(
        self,
        query: str,
        plan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Execute the planned agent calls.
        
        Args:
            query: User's query
            plan: Execution plan from _plan_execution
        
        Returns:
            List of results from each agent
        """
        agent_map = {
            "worker_agent_1": self.worker_agent_1_url,
            "worker_agent_2": self.worker_agent_2_url,
            # Keep backward compatibility - CUSTOMIZE: Remove if not needed
            "clause_agent": self.worker_agent_1_url,
            "compliance_agent": self.worker_agent_2_url
        }
        
        agents_to_call = plan.get("agents", [])
        is_parallel = plan.get("parallel", False)
        
        if is_parallel:
            # Execute in parallel using asyncio.gather
            tasks = [
                self._call_worker(agent_map[a], query)
                for a in agents_to_call if a in agent_map
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [
                r if not isinstance(r, Exception) 
                else {"success": False, "error": str(r)}
                for r in results
            ]
        else:
            # Execute sequentially
            results = []
            for agent_name in agents_to_call:
                if agent_name in agent_map:
                    result = await self._call_worker(agent_map[agent_name], query)
                    results.append(result)
            return results
    
    # -------------------------------------------------------------------------
    # Result Synthesis
    # -------------------------------------------------------------------------
    
    async def _synthesize_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Synthesize results from multiple agents into final answer.
        
        Args:
            query: Original user query
            results: List of agent results
        
        Returns:
            Synthesized response string
        """
        try:
            llm = self._create_llm(temperature=0.0, max_tokens=2000)
            
            # Extract text from results
            result_texts = []
            for i, r in enumerate(results):
                if r.get("success"):
                    artifacts = r.get("result", {}).get("artifacts", [])
                    if artifacts:
                        parts = artifacts[0].get("parts", [])
                        if parts:
                            text = parts[0].get("text", "")
                            result_texts.append(f"Agent {i+1} Result:\n{text}")
            
            if not result_texts:
                return "No results obtained from worker agents."
            
            synthesis_prompt = f"""Synthesize these results into a comprehensive answer.

ORIGINAL QUERY: {query}

AGENT RESULTS:
{chr(10).join(result_texts)}

Create a unified response that:
1. Answers the original query directly
2. Integrates insights from all sources
3. Highlights key findings and recommendations
4. Notes any conflicts or uncertainties"""
            
            response = await llm.ainvoke([HumanMessage(content=synthesis_prompt)])
            return response.content.strip()
            
        except Exception as e:
            return f"Synthesis error: {str(e)}"
    
    # -------------------------------------------------------------------------
    # Main Analysis Skill
    # -------------------------------------------------------------------------
    
    @skill(
        name="Legal Document Analysis",
        description="Analyze legal documents by coordinating clause extraction and compliance checking",
        tags=["legal", "contracts", "analysis", "compliance"]
    )
    async def analyze_legal_query(self, query: str) -> str:
        """
        Process a legal query through the reasoning pipeline.
        
        Args:
            query: Natural language question about contracts
        
        Returns:
            Comprehensive analysis combining all relevant insights
        """
        try:
            log_event("ManagerAgent", "QUERY_RECEIVED", {"query": query})
            
            # Step 1: Classify complexity
            complexity = await self._classify_complexity(query)
            log_event("ManagerAgent", "COMPLEXITY_CLASSIFIED", {
                "complexity": complexity.value
            })
            
            # Step 2: Plan execution
            plan = await self._plan_execution(query)
            log_event("ManagerAgent", "PLAN_CREATED", plan)
            
            # Step 3: Execute plan
            results = await self._execute_plan(query, plan)
            log_event("ManagerAgent", "EXECUTION_COMPLETE", {
                "result_count": len(results),
                "worker_results": results  # Log full worker responses
            })
            
            # Step 4: Synthesize results
            final_answer = await self._synthesize_results(query, results)
            log_event("ManagerAgent", "SYNTHESIS_COMPLETE", {
                "preview": final_answer[:200] if len(final_answer) > 200 else final_answer,
                "full_result": final_answer
            })
            
            return final_answer
            
        except Exception as e:
            error_msg = f"Analysis error: {str(e)}"
            log_event("ManagerAgent", "ERROR", {"error": error_msg})
            return error_msg
    
    # -------------------------------------------------------------------------
    # A2A Task Handling
    # -------------------------------------------------------------------------
    
    async def handle_task(self, task: Task) -> Task:
        """Handle incoming A2A tasks."""
        try:
            task.status = TaskStatus(state=TaskState.PROCESSING)
            
            # Extract query
            message = task.message or {}
            content = message.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else str(content)
            
            if not text:
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={
                        "role": "agent",
                        "content": {"text": "Please provide a legal query"}
                    }
                )
                return task
            
            # Process the query
            result = await self.analyze_legal_query(text)
            
            # Build response
            task.artifacts = [{"parts": [{"type": "text", "text": result}]}]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
        except Exception as e:
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={
                    "role": "agent",
                    "content": {"text": f"Error: {str(e)}"}
                }
            )
        
        return task


# =============================================================================
# Entry Point
# =============================================================================

def run_manager_server(agent_instance, host: str = "0.0.0.0", port: int = 8100):
    """
    Run the manager agent with Flask on the correct port.
    
    This function replaces python_a2a's run_server to ensure
    the port parameter is actually respected.
    """
    from flask import Flask, jsonify, request
    import asyncio
    
    app = Flask("ManagerAgent")
    
    @app.route('/.well-known/agent.json', methods=['GET'])
    def agent_card():
        """Return agent card for A2A discovery."""
        return jsonify({
            "name": "Legal Reasoning Manager",
            "description": "Orchestrates legal analysis by coordinating clause extraction and compliance checking",
            "version": "1.0.0",
            "url": f"http://{host}:{port}",
            "capabilities": {
                "streaming": False,
                "pushNotifications": False
            }
        })
    
    @app.route('/task', methods=['POST'])
    def handle_task_endpoint():
        """Handle incoming A2A task requests."""
        try:
            data = request.get_json()
            
            # Extract query from request
            message = data.get('message', {})
            content = message.get('content', {})
            
            if isinstance(content, dict):
                query = content.get('text', '')
            else:
                query = str(content)
            
            if not query:
                return jsonify({
                    "id": data.get('id', ''),
                    "status": {"state": "input_required"},
                    "artifacts": [{
                        "parts": [{"type": "text", "text": "Please provide a legal query"}]
                    }]
                })
            
            # Log the request
            agent_instance.logger.info(f"Received query: {query[:100]}")
            
            # Run async analyze_legal_query directly
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(agent_instance.analyze_legal_query(query))
            finally:
                loop.close()
            
            # Build response
            return jsonify({
                "id": data.get('id', ''),
                "status": {"state": "completed"},
                "artifacts": [{
                    "parts": [{"type": "text", "text": result}]
                }]
            })
            
        except Exception as e:
            agent_instance.logger.error(f"Task endpoint error: {e}", exc_info=True)
            return jsonify({
                "id": "",
                "status": {"state": "failed"},
                "artifacts": [{
                    "parts": [{"type": "text", "text": f"Error: {str(e)}"}]
                }]
            })
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        return jsonify({"status": "healthy", "agent": "ManagerAgent"})
    
    agent_instance.logger.info(f"🚀 Starting Manager Agent on {host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    print("🚀 Starting Legal Reasoning Manager Agent...")
    agent_instance = LegalManagerAgent()
    run_manager_server(agent_instance, host="0.0.0.0", port=agent_instance.port)

