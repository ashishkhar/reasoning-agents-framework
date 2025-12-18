# =============================================================================
# Reasoning Agents Framework - Base Agent Class
# =============================================================================
"""
Abstract base class for all A2A agents in the framework.

This module provides BaseAgent, which:
- Handles common A2A protocol boilerplate
- Provides MCP client initialization
- Implements standard task handling
- Sets up logging automatically

To create a new agent:
1. Subclass BaseAgent
2. Implement process_query() method
3. Optionally override get_system_prompt()

Example:
    from core.base_agent import BaseAgent
    
    class MyAgent(BaseAgent):
        def __init__(self):
            super().__init__(
                name="MyAgent",
                port=8103,
                mcp_tools=["my_tool"]  # Tools from registry.yaml
            )
        
        async def process_query(self, query: str) -> str:
            # Your implementation here
            return "Result"
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from python_a2a.models import Task, TaskState, TaskStatus

from core.config import Config, get_config
from core.logging_utils import log_event, setup_logging


class BaseAgent(ABC):
    """
    Abstract base class for A2A agents.
    
    Provides common functionality:
    - Configuration loading
    - Logging setup
    - MCP client management
    - Standard task handling
    - LLM initialization
    
    Subclasses must implement:
    - process_query(query: str) -> str
    
    Subclasses may optionally override:
    - get_system_prompt() -> str
    - get_mcp_config() -> dict
    
    Attributes:
        name: Agent name for logging and identification
        port: Port number the agent runs on
        config: Configuration instance
        logger: Configured logger
        mcp_client: MCP client (initialized on first use)
        tools: List of MCP tools (populated after MCP init)
    """
    
    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------
    
    def __init__(
        self,
        name: str,
        port: int,
        mcp_tools: Optional[List[str]] = None,
        config: Optional[Config] = None
    ):
        """
        Initialize the base agent.
        
        Args:
            name: Human-readable name for the agent
            port: Port number to run on
            mcp_tools: List of tool names from registry to connect to
            config: Optional Config instance (uses default if not provided)
        """
        # Store configuration
        
        # Store configuration
        self.name = name
        self.port = port
        self.config = config or get_config()
        self._mcp_tool_names = mcp_tools or []
        
        # Setup logging
        self.logger = setup_logging(
            name,
            log_level=self.config.log_level,
            log_to_file=True
        )
        
        # MCP client (lazy initialization)
        self._mcp_client: Optional[MultiServerMCPClient] = None
        self._tools: List = []
        
        # Ensure log directory exists
        self.config.ensure_directories()
        
        self.logger.info(f"Initialized {name} on port {port}")
    
    # -------------------------------------------------------------------------
    # Abstract Methods (must be implemented by subclasses)
    # -------------------------------------------------------------------------
    
    @abstractmethod
    async def process_query(self, query: str) -> str:
        """
        Process a query and return a response.
        
        This is the main method that subclasses must implement.
        It receives the user's query and should return a string response.
        
        Args:
            query: The user's query text
        
        Returns:
            Response string to send back to the caller
        
        Example:
            async def process_query(self, query: str) -> str:
                # Use MCP tools via self.tools
                # Use LLM via self.create_llm()
                result = await self._run_react_agent(query)
                return result
        """
        pass
    
    # -------------------------------------------------------------------------
    # Overridable Methods
    # -------------------------------------------------------------------------
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        
        Override this to provide a custom system prompt.
        Default implementation loads from prompts/<name>.txt file.
        
        Returns:
            System prompt string
        """
        # Try to load from prompts directory
        prompt = self.config.load_prompt(self.name.lower().replace(" ", "_"))
        if prompt:
            return prompt
        
        # Default generic prompt
        return f"You are {self.name}, an AI assistant. Help the user with their request."
    
    def get_mcp_config(self) -> Dict[str, Any]:
        """
        Get MCP client configuration.
        
        Override this to customize which MCP tools to connect to.
        Default implementation uses tools specified in __init__.
        
        Returns:
            Dictionary mapping tool names to their configurations
        
        Example:
            def get_mcp_config(self):
                return {
                    "ContractDB": {
                        "url": "http://localhost:11001/mcp",
                        "transport": "streamable_http"
                    }
                }
        """
        mcp_config = {}
        for tool_name in self._mcp_tool_names:
            url = self.config.get_tool_url(tool_name)
            if url:
                mcp_config[tool_name] = {
                    "url": url,
                    "transport": "streamable_http"
                }
        return mcp_config
    
    # -------------------------------------------------------------------------
    # MCP Client Management
    # -------------------------------------------------------------------------
    
    async def ensure_mcp_initialized(self) -> bool:
        """
        Ensure MCP client is initialized.
        
        Lazily initializes the MCP client on first call.
        Subsequent calls return immediately if already initialized.
        
        Returns:
            True if MCP is ready, False if initialization failed
        """
        if self._mcp_client is not None:
            return True
        
        mcp_config = self.get_mcp_config()
        if not mcp_config:
            self.logger.warning("No MCP tools configured")
            return True  # Not an error, just no tools
        
        try:
            self.logger.info(f"Initializing MCP client with tools: {list(mcp_config.keys())}")
            self._mcp_client = MultiServerMCPClient(mcp_config)
            self._tools = await self._mcp_client.get_tools()
            self.logger.info(f"MCP initialized with {len(self._tools)} tools")
            return True
        except Exception as e:
            self.logger.error(f"MCP initialization failed: {e}")
            return False
    
    @property
    def mcp_client(self) -> Optional[MultiServerMCPClient]:
        """Get the MCP client (may be None if not initialized)."""
        return self._mcp_client
    
    @property
    def tools(self) -> List:
        """Get the list of available MCP tools."""
        return self._tools
    
    # -------------------------------------------------------------------------
    # LLM Helper Methods
    # -------------------------------------------------------------------------
    
    def create_llm(
        self,
        temperature: Optional[float] = None,
        max_tokens: int = 4000
    ) -> ChatOpenAI:
        """
        Create a configured LLM instance.
        
        Args:
            temperature: Optional temperature override
            max_tokens: Maximum tokens in response
        
        Returns:
            Configured ChatOpenAI instance
        """
        params = {
            "model": self.config.model,
            "api_key": self.config.api_key,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "max_tokens": max_tokens
        }
        if self.config.base_url:
            params["base_url"] = self.config.base_url
        
        return ChatOpenAI(**params)
    
    async def run_react_agent(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        recursion_limit: int = 25
    ) -> str:
        """
        Run a ReAct agent with the configured tools.
        
        Convenience method that creates a ReAct agent with the
        system prompt and available tools, then runs the query.
        
        Args:
            query: User query to process
            system_prompt: Optional override for system prompt
            recursion_limit: Max reasoning steps
        
        Returns:
            Agent response string
        """
        if not await self.ensure_mcp_initialized():
            return "Error: Failed to initialize MCP tools"
        
        if not self._tools:
            return "Error: No tools available"
        
        llm = self.create_llm()
        agent = create_react_agent(llm, self._tools)
        
        prompt = system_prompt or self.get_system_prompt()
        
        response = await agent.ainvoke(
            {
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query}
                ]
            },
            config={"recursion_limit": recursion_limit}
        )
        
        return response["messages"][-1].content
    
    # -------------------------------------------------------------------------
    # A2A Task Handling
    # -------------------------------------------------------------------------
    
    async def handle_task(self, task: Task) -> Task:
        """
        Handle an incoming A2A task.
        
        This method implements the standard A2A task handling flow:
        1. Extract query from task message
        2. Call process_query() (implemented by subclass)
        3. Package response as task artifacts
        4. Set appropriate task status
        
        Subclasses typically don't need to override this.
        
        Args:
            task: Incoming A2A Task object
        
        Returns:
            Updated Task with response or error
        """
        try:
            # Set processing status
            task.status = TaskStatus(state=TaskState.PROCESSING)
            
            # Extract query from task message
            query = self._extract_query(task)
            
            if not query:
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={
                        "role": "agent",
                        "content": {"text": "Please provide a query"}
                    }
                )
                return task
            
            # Log incoming request
            log_event(self.name, "TASK_RECEIVED", {"query": query})
            
            # Process the query (implemented by subclass)
            result = await self.process_query(query)
            
            # Build response
            task.artifacts = [{"parts": [{"type": "text", "text": result}]}]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
            # Log completion - full result in file, preview in console
            log_event(self.name, "TASK_COMPLETED", {
                "preview": result[:200] if len(result) > 200 else result,
                "full_result": result
            })
            
        except Exception as e:
            self.logger.error(f"Task handling error: {e}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={
                    "role": "agent",
                    "content": {"text": f"Error: {str(e)}"}
                }
            )
            log_event(self.name, "TASK_ERROR", {"error": str(e)})
        
        return task
    
    def _extract_query(self, task: Task) -> str:
        """
        Extract query text from an A2A task.
        
        Args:
            task: The incoming Task object
        
        Returns:
            Extracted query string, or empty string if not found
        """
        message = task.message or {}
        content = message.get("content", {})
        
        if isinstance(content, dict):
            return content.get("text", "")
        return str(content)
    
    # -------------------------------------------------------------------------
    # Lifecycle Methods
    # -------------------------------------------------------------------------
    
    def run(self, host: str = "0.0.0.0"):
        """
        Start the agent server.
        
        Args:
            host: Host address to bind to
        """
        # Import here to avoid circular imports
        from flask import Flask, jsonify, request
        import asyncio
        
        self.logger.info(f"🚀 Starting {self.name} on {host}:{self.port}")
        
        # Create Flask app
        app = Flask(self.name)
        
        # Store reference to self for route handlers
        agent_instance = self
        
        @app.route('/.well-known/agent.json', methods=['GET'])
        def agent_card():
            """Return agent card for A2A discovery."""
            return jsonify({
                "name": agent_instance.name,
                "description": f"A2A Agent: {agent_instance.name}",
                "version": "1.0.0",
                "url": f"http://{host}:{agent_instance.port}",
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
                            "parts": [{"type": "text", "text": "Please provide a query"}]
                        }]
                    })
                
                # Log the request
                agent_instance.logger.info(f"Received query: {query[:100]}")
                
                # Run async process_query directly
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(agent_instance.process_query(query))
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
            return jsonify({"status": "healthy", "agent": agent_instance.name})
        
        # Run Flask app
        app.run(host=host, port=self.port, debug=False, threaded=True)