# Build Your Own Reasoning Model

**A practical guide to building a multi-agent reasoning system using A2A agents (the brain) and MCP tools (the hands).**

> This framework lets you bring your own data, define your own rules, and build an AI system that reasons about it—with every step logged and explainable.

---

## Table of Contents

1. [What You're Building](#what-youre-building)
2. [Architecture Overview](#architecture-overview)
3. [Project Structure](#project-structure)
4. [Step 1: Core Framework](#step-1-core-framework)
5. [Step 2: Create MCP Tools](#step-2-create-mcp-tools)
6. [Step 3: Build Worker Agents](#step-3-build-worker-agents)
7. [Step 4: Build the Manager Agent](#step-4-build-the-manager-agent)
8. [Step 5: Configure the System](#step-5-configure-the-system)
9. [Step 6: Create the Orchestration Script](#step-6-create-the-orchestration-script)
10. [Step 7: Testing](#step-7-testing)
11. [Customizing for Your Domain](#customizing-for-your-domain)
12. [Conclusion](#conclusion)

---

## What You're Building

A **multi-agent reasoning system** with two key components:

| Component | What It Does | How It Works |
|-----------|-------------|--------------|
| 🧠 **A2A Agents** (Brain) | Think, plan, reason, synthesize | LLM-powered, communicate via A2A protocol |
| 🔧 **MCP Tools** (Hands) | Execute, query, validate, calculate | Deterministic, no LLM, fully auditable |

```
┌─────────────────────────────────────────────────────────────────────┐
│                         YOUR DATA                                    │
│              (CSV, JSON, Database, API, anything)                    │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    🧠 A2A AGENTS (The Brain)                         │
│                                                                      │
│  MANAGER AGENT (:8100)                                              │
│  └── Classifies complexity, routes to workers, synthesizes          │
│                                                                      │
│  WORKER AGENT 1 (:8101)        WORKER AGENT 2 (:8102)               │
│  └── Specializes in Task A     └── Specializes in Task B           │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    🔧 MCP TOOLS (The Hands)                          │
│                                                                      │
│  TOOL 1 (:11001)               TOOL 2 (:11002)                      │
│  └── Database queries          └── Rule validation                  │
│  └── SQL execution             └── Compliance checks                │
└─────────────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

| Feature | ML-Based Systems | This Framework |
|---------|------------------|----------------|
| Explainability | Black box | Every step traced |
| Determinism | Probabilistic | Guaranteed identical results |
| Auditability | Difficult | JSONL event logs |
| Rule changes | Retrain model | Edit JSON/config |

---

## Architecture Overview

### The Flow

1. **User sends query** → Manager Agent
2. **Manager classifies** → SIMPLE (one worker) or COMPLEX (multiple workers)
3. **Manager plans** → Which workers, parallel or sequential
4. **Workers execute** → Each worker calls its MCP tools
5. **Manager synthesizes** → Combines results into final answer

### Component Responsibilities

| Component | Port | Responsibility |
|-----------|------|----------------|
| **Manager Agent** | 8100 | Orchestration, routing, synthesis |
| **Worker Agent 1** | 8101 | Domain task A (e.g., data extraction) |
| **Worker Agent 2** | 8102 | Domain task B (e.g., validation) |
| **Tool 1** | 11001 | Database queries (deterministic) |
| **Tool 2** | 11002 | Rule evaluation (deterministic) |

---

## Project Structure

```
reasoning-agents-framework/
│
├── core/                        # Framework internals (don't modify)
│   ├── base_agent.py            # BaseAgent class (agents inherit this)
│   ├── config.py                # Configuration loader
│   └── logging_utils.py         # Structured logging
│
├── agents/
│   ├── manager/
│   │   └── manager_agent.py     # Orchestrator agent
│   └── workers/
│       ├── worker_agent_1.py    # CUSTOMIZE: First worker
│       └── worker_agent_2.py    # CUSTOMIZE: Second worker
│
├── tools/
│   ├── tool_1.py                # CUSTOMIZE: First MCP tool
│   └── tool_2.py                # CUSTOMIZE: Second MCP tool
│
├── prompts/
│   ├── manager_agent.txt        # Manager's system prompt
│   ├── worker_agent_1.txt       # Worker 1's system prompt
│   └── worker_agent_2.txt       # Worker 2's system prompt
│
├── data/
│   ├── contracts.csv            # Example data (replace with yours)
│   └── compliance_rules.json    # Example rules (replace with yours)
│
├── config/
│   └── registry.yaml            # Service configuration
│
├── logs/                        # Runtime logs (gitignored)
├── run.sh                       # One-command startup
├── .env                         # API keys (gitignored)
└── pyproject.toml               # Dependencies
```

---

## Step 1: Core Framework

The core framework provides the foundation. These files are in `core/` and you typically don't modify them.

### core/base_agent.py

This is the abstract base class that all worker agents inherit from.

```python
"""
BaseAgent - The foundation for all worker agents.

Provides:
- MCP tool connection management
- ReAct agent pattern with LangGraph
- Structured logging
- A2A protocol handling
"""

class BaseAgent(A2AServer):
    """
    Base class for all worker agents.
    
    Inherit from this class and implement:
    - __init__(): Configure port, tools, and name
    - get_system_prompt(): Return the agent's system prompt
    - process_query(): Main query processing logic
    """
    
    def __init__(
        self,
        name: str,
        port: int,
        mcp_tools: List[str],
        config: Config
    ):
        """
        Initialize a worker agent.
        
        Args:
            name: Agent name for logging (e.g., "WorkerAgent1")
            port: Port to run on (e.g., 8101)
            mcp_tools: List of tool names from registry to connect to
            config: Configuration object
        """
        self.name = name
        self.port = port
        self.mcp_tool_names = mcp_tools
        self.config = config
        # ... initialization logic
    
    async def run_react_agent(self, query: str) -> str:
        """
        Run the ReAct agent pattern.
        
        1. Creates LLM with system prompt
        2. Connects to MCP tools
        3. Runs LangGraph ReAct agent
        4. Returns final answer
        """
        # ... implementation
    
    def run(self):
        """Start the Flask server for A2A communication."""
        # ... Flask server with /task and /health endpoints
```

### core/config.py

Loads configuration from `.env` and `config/registry.yaml`.

```python
class Config:
    """
    Configuration management.
    
    Loads from:
    - .env: API keys, model settings
    - config/registry.yaml: Service definitions
    """
    
    def __init__(self):
        self.api_key = os.getenv("API_KEY", "")
        self.model = os.getenv("MODEL", "gpt-4o-mini")
        self.temperature = float(os.getenv("TEMPERATURE", "0"))
        self.base_url = os.getenv("BASE_URL", "")
    
    def get_tool_url(self, tool_name: str) -> str:
        """Get the MCP URL for a tool from registry."""
        
    def get_agent_registry(self) -> Dict:
        """Get all agent configurations from registry."""
        
    def load_prompt(self, prompt_name: str) -> str:
        """Load a system prompt from prompts/ directory."""
```

### core/logging_utils.py

Provides structured logging for audit trails.

```python
def log_event(source: str, event_type: str, data: Dict):
    """
    Log a structured event to JSONL file.
    
    Args:
        source: Component name (e.g., "WorkerAgent1")
        event_type: Event type (e.g., "QUERY_RECEIVED")
        data: Event data dictionary
    
    Creates entries like:
    {"timestamp": "2024-01-15T10:30:00", "source": "WorkerAgent1", 
     "type": "QUERY_RECEIVED", "data": {"query": "..."}}
    """
```

---

## Step 2: Create MCP Tools

MCP tools are the **deterministic hands** of your system. They execute operations like database queries and rule evaluation **without any LLM involvement**.

### tools/tool_1.py - Database Query Tool

```python
"""
MCP Tool 1 - Database Query Tool

CUSTOMIZE:
- Change DATA_PATH to your data file
- Rename tool functions to match your use case
- Update the table name in SQL queries
"""

import os
import sys
from typing import Any, Dict

import duckdb
from fastmcp import FastMCP

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_config
from core.logging_utils import log_event, setup_logging

# =============================================================================
# Configuration - CUSTOMIZE THESE
# =============================================================================

config = get_config()

# CUSTOMIZE: Path to your data file
DATA_PATH = config.data_dir / "contracts.csv"
RESULTS_PATH = config.data_dir / "query_results"
RESULTS_PATH.mkdir(exist_ok=True)

# CUSTOMIZE: Logger and server names
logger = setup_logging("Tool1", log_level=config.log_level)
mcp = FastMCP("Database Query Tool")


# =============================================================================
# Helper Functions
# =============================================================================

def get_database_connection():
    """
    Create a DuckDB connection with data loaded.
    
    DuckDB is an embedded SQL engine - no server needed.
    It loads your CSV/JSON into memory and lets you query with SQL.
    """
    conn = duckdb.connect(':memory:')
    
    # Load CSV and register as table named 'data'
    # CUSTOMIZE: Change table name if needed
    data_df = conn.execute(f"""
        SELECT * FROM read_csv_auto('{DATA_PATH}', header=true)
    """).fetchdf()
    
    conn.register('data', data_df)
    return conn


# =============================================================================
# MCP Tools - CUSTOMIZE THESE
# =============================================================================

@mcp.tool()
def query_data(sql_query: str, output_filename: str) -> Dict[str, Any]:
    """
    Execute SQL query against the data.
    
    This is what agents call to fetch data. The agent provides:
    - sql_query: The SQL to execute (table name is 'data')
    - output_filename: Where to save results as CSV
    
    Returns a dictionary with results (success, row_count, preview, etc.)
    """
    try:
        log_event("Tool1", "QUERY_RECEIVED", {
            "query": sql_query,
            "filename": output_filename
        })
        
        conn = get_database_connection()
        result_df = conn.execute(sql_query).fetchdf()
        conn.close()
        
        # Save results to CSV
        save_path = RESULTS_PATH / output_filename
        result_df.to_csv(save_path, index=False)
        
        # Convert to JSON-serializable format
        all_results = result_df.to_dict('records')
        
        log_event("Tool1", "QUERY_SUCCESS", {
            "row_count": len(result_df),
            "columns": list(result_df.columns)
        })
        
        return {
            "success": True,
            "row_count": len(result_df),
            "columns": list(result_df.columns),
            "preview": all_results[:10],
            "all_results": all_results,
            "saved_file": output_filename
        }
        
    except Exception as e:
        log_event("Tool1", "QUERY_ERROR", {"error": str(e)})
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_record_by_id(record_id: str) -> Dict[str, Any]:
    """
    Retrieve a specific record by its ID.
    
    CUSTOMIZE: Change 'contract_id' to your actual ID column name.
    """
    try:
        conn = get_database_connection()
        # CUSTOMIZE: Change column name
        result_df = conn.execute(f"""
            SELECT * FROM data WHERE contract_id = '{record_id}'
        """).fetchdf()
        conn.close()
        
        if result_df.empty:
            return {"success": False, "error": f"Record {record_id} not found"}
        
        return {"success": True, "record": result_df.iloc[0].to_dict()}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_schema() -> Dict[str, Any]:
    """
    Get schema information for the data table.
    
    Agents should call this FIRST to discover available columns.
    This enables data-agnostic prompts.
    """
    try:
        conn = get_database_connection()
        schema_df = conn.execute("DESCRIBE data").fetchdf()
        count = conn.execute("SELECT COUNT(*) FROM data").fetchone()[0]
        conn.close()
        
        columns = [
            {"name": row["column_name"], "type": row["column_type"]}
            for _, row in schema_df.iterrows()
        ]
        
        return {"success": True, "columns": columns, "row_count": count}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    port = int(os.getenv("TOOL_1_PORT", "11001"))
    
    logger.info(f"🔧 Starting Tool 1 on port {port}")
    logger.info(f"📂 Data path: {DATA_PATH}")
    
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = port
    mcp.run(transport="streamable-http")
```

### tools/tool_2.py - Rules/Validation Tool

```python
"""
MCP Tool 2 - Rules/Validation Engine

CUSTOMIZE:
- Change RULES_PATH to your rules file
- Update evaluate_condition() for your rule format
- Add new validation functions as needed
"""

import json
import os
import re
import sys
from typing import Any, Dict, List

from fastmcp import FastMCP

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_config
from core.logging_utils import log_event, setup_logging

# =============================================================================
# Configuration - CUSTOMIZE THESE
# =============================================================================

config = get_config()

# CUSTOMIZE: Path to your rules file
RULES_PATH = config.data_dir / "compliance_rules.json"

logger = setup_logging("Tool2", log_level=config.log_level)
mcp = FastMCP("Validation Engine Tool")


# =============================================================================
# Helper Functions
# =============================================================================

def load_rules() -> List[Dict]:
    """Load rules from JSON file."""
    with open(RULES_PATH, 'r') as f:
        return json.load(f).get("rules", [])


def evaluate_condition(condition: str, record: Dict) -> bool:
    """
    Evaluate a rule condition against record data.
    
    CUSTOMIZE: Update context variables to match your data schema.
    
    This uses safe eval with restricted builtins.
    For production, consider a proper rule engine library.
    """
    # Build context from record data
    # CUSTOMIZE: Map your column names to rule variables
    context = {
        "termination_notice_days": parse_days(str(record.get("termination_clause", ""))),
        "liability_cap": float(record.get("liability_cap", 0)),
        "auto_renewal": str(record.get("auto_renewal", "")).lower() == "true",
        "governing_law": str(record.get("governing_law", "")),
    }
    
    try:
        eval_str = condition
        for key, value in context.items():
            if isinstance(value, str):
                eval_str = eval_str.replace(key, f"'{value}'")
            elif isinstance(value, bool):
                eval_str = eval_str.replace(key, str(value))
            else:
                eval_str = eval_str.replace(key, str(value))
        
        # Restricted eval for safety
        return eval(eval_str, {"__builtins__": {}}, {})
        
    except Exception as e:
        logger.warning(f"Condition evaluation error: {e}")
        return False


def parse_days(text: str) -> int:
    """Extract numeric days from text like '30 days notice'."""
    match = re.search(r'(\d+)', str(text))
    return int(match.group(1)) if match else 0


# =============================================================================
# MCP Tools
# =============================================================================

@mcp.tool()
def validate_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a record against all rules.
    
    The agent calls this with a record dictionary.
    Returns which rules passed and which were violated.
    """
    try:
        record_id = record.get("contract_id", "UNKNOWN")
        log_event("Tool2", "VALIDATION_CHECK", {"record_id": record_id})
        
        rules = load_rules()
        violations = []
        passed = []
        
        for rule in rules:
            is_violated = evaluate_condition(rule["condition"], record)
            
            result = {
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "severity": rule["severity"],
                "message": rule["message"]
            }
            
            if is_violated:
                violations.append(result)
            else:
                passed.append(result)
        
        return {
            "success": True,
            "record_id": record_id,
            "is_valid": len(violations) == 0,
            "violation_count": len(violations),
            "violations": violations,
            "passed_rules": passed,
            "summary": f"Checked {len(rules)} rules: {len(violations)} violations"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_rules() -> Dict[str, Any]:
    """
    List all available validation rules.
    
    Agents should call this FIRST to discover what rules exist.
    """
    try:
        rules = load_rules()
        return {"success": True, "rule_count": len(rules), "rules": rules}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def evaluate_rule(rule_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a specific rule against a record."""
    try:
        rules = load_rules()
        rule = next((r for r in rules if r["id"] == rule_id), None)
        
        if not rule:
            return {"success": False, "error": f"Rule {rule_id} not found"}
        
        is_violated = evaluate_condition(rule["condition"], record)
        
        return {
            "success": True,
            "rule_id": rule_id,
            "is_violated": is_violated,
            "rule_details": rule
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    port = int(os.getenv("TOOL_2_PORT", "11002"))
    
    logger.info(f"🔧 Starting Tool 2 on port {port}")
    logger.info(f"📋 Rules path: {RULES_PATH}")
    
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = port
    mcp.run(transport="streamable-http")
```

---

## Step 3: Build Worker Agents

Worker agents are the **LLM-powered specialists**. They receive queries, use MCP tools to get data, and return analyzed results.

### agents/workers/worker_agent_1.py

```python
"""
Worker Agent 1 - Data Extraction Specialist

CUSTOMIZE:
- Rename the class to match your use case
- Update mcp_tools list to connect to your tools
- Modify get_system_prompt() to define agent behavior
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.base_agent import BaseAgent
from core.config import get_config


class WorkerAgent1(BaseAgent):
    """
    Worker agent for data extraction and analysis.
    
    CUSTOMIZE: Rename this class and update for your use case.
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
        
        The prompt tells the agent:
        - What tools are available
        - What workflow to follow
        - What format to use for responses
        """
        prompt = self.config.load_prompt("worker_agent_1")
        if prompt:
            return prompt
        
        # Fallback default prompt
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
        
        This is the main entry point. It:
        1. Creates a ReAct agent with the system prompt
        2. Gives it access to MCP tools
        3. Runs the agent loop until completion
        4. Returns the final answer
        """
        try:
            result = await self.run_react_agent(query)
            return result
        except Exception as e:
            self.logger.error(f"Query processing error: {e}")
            return f"Error processing query: {str(e)}"


if __name__ == "__main__":
    print("🚀 Starting Worker Agent 1...")
    agent = WorkerAgent1()
    agent.run()
```

### agents/workers/worker_agent_2.py

```python
"""
Worker Agent 2 - Validation Specialist

CUSTOMIZE:
- Rename for your use case (e.g., ComplianceAgent, QAAgent)
- Update mcp_tools to include the tools this agent needs
- Modify the system prompt
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.base_agent import BaseAgent
from core.config import get_config


class WorkerAgent2(BaseAgent):
    """
    Worker agent for validation and compliance.
    
    This agent has access to BOTH tools:
    - tool_1: To fetch data
    - tool_2: To validate against rules
    """
    
    def __init__(self):
        config = get_config()
        agents = config.get_agent_registry()
        agent_config = agents.get("worker_2", {})
        
        super().__init__(
            name="WorkerAgent2",
            port=agent_config.get("port", 8102),
            # This agent uses both tools
            mcp_tools=["tool_1", "tool_2"],
            config=config
        )
    
    def get_system_prompt(self) -> str:
        prompt = self.config.load_prompt("worker_agent_2")
        if prompt:
            return prompt
        
        return """You are a validation and compliance specialist.

## Workflow
1. Call list_rules() first to discover available rules
2. Retrieve the data you need to validate
3. Run validation checks and report findings

## Rules
- Always use tools to check compliance - never assume rules
- Report findings with severity levels
- Provide actionable recommendations
"""
    
    async def process_query(self, query: str) -> str:
        try:
            result = await self.run_react_agent(query)
            return result
        except Exception as e:
            self.logger.error(f"Query processing error: {e}")
            return f"Error processing query: {str(e)}"


if __name__ == "__main__":
    print("🚀 Starting Worker Agent 2...")
    agent = WorkerAgent2()
    agent.run()
```

### System Prompts

The system prompt is critical—it tells the agent what tools are available and how to use them.

**prompts/worker_agent_1.txt:**

```text
You are a data extraction and analysis specialist.

## Available Tools

### get_schema()
**ALWAYS call this first** to discover available columns and data types.
Returns: column names, types, and row count.

### query_data(sql_query, output_filename)
Execute SQL queries on the data. 
Arguments:
- sql_query: Valid SQL using columns from get_schema()
- output_filename: Name for output CSV file

### get_record_by_id(record_id)
Get a specific record by its ID.

## Workflow
1. **First**: Call `get_schema()` to see available columns
2. **Then**: Construct SQL using actual column names from schema
3. **Finally**: Summarize results for the user

## CRITICAL RULES
1. ALWAYS call get_schema() first - never assume column names
2. Use actual column names from schema in your SQL queries
3. When you receive tool results, summarize them - don't re-call with response fields
4. Never make up data - only report what tools return

## Response Format
- Start with a summary of findings
- Present data in tables when helpful
- Highlight notable items
- Provide actionable recommendations
```

**prompts/worker_agent_2.txt:**

```text
You are a validation and compliance specialist.

## Available Tools

### list_rules()
**ALWAYS call this first** to discover available validation rules.
Returns: All rule IDs, descriptions, conditions, and severity levels.

### validate_record(record)
Check a record against all rules.
Argument: dictionary with record fields.

### evaluate_rule(rule_id, record)
Check a specific rule against a record.

## Workflow
1. **First**: Call `list_rules()` to see available rules
2. **Then**: Retrieve the data you need to validate
3. **Finally**: Run validation checks and report findings

## CRITICAL RULES
1. ALWAYS call list_rules() first - never assume rule IDs
2. Use actual rule conditions from the rules engine
3. When you receive tool results, summarize them

## Response Format

### Validation Report

**Summary**: [Overall status]

**Violations Found**:
| Rule | Severity | Issue | Action |
|------|----------|-------|--------|
| ... | ... | ... | ... |

**Passed Rules**: [List]

**Recommendations**: [Next steps]
```

---

## Step 4: Build the Manager Agent

The Manager Agent is the **orchestrator**. It doesn't connect to MCP tools directly—instead, it routes queries to the right workers and synthesizes their results.

### agents/manager/manager_agent.py (Key Parts)

```python
"""
Manager Agent - The Orchestrator

This agent:
1. Receives user queries
2. Classifies complexity (SIMPLE/COMPLEX)
3. Plans execution (which workers, parallel/sequential)
4. Calls worker agents via A2A protocol
5. Synthesizes results into final answer
"""

class ManagerAgent(A2AServer):
    """
    Manager agent for orchestrating worker agents.
    
    Key difference from workers:
    - Does NOT connect to MCP tools
    - DOES call other agents via HTTP (A2A protocol)
    """
    
    def __init__(self):
        config = get_config()
        agents = config.get_agent_registry()
        
        # Get worker URLs from registry
        worker_1_config = agents.get("worker_1", {})
        worker_2_config = agents.get("worker_2", {})
        
        self.worker_agent_1_url = f"http://localhost:{worker_1_config.get('port', 8101)}"
        self.worker_agent_2_url = f"http://localhost:{worker_2_config.get('port', 8102)}"
    
    async def analyze_query(self, query: str) -> str:
        """
        Main entry point for query processing.
        
        Steps:
        1. Classify complexity
        2. Plan execution
        3. Execute plan (call workers)
        4. Synthesize results
        """
        # Step 1: Classify
        complexity = await self._classify_complexity(query)
        
        # Step 2: Plan
        plan = await self._plan_execution(query)
        
        # Step 3: Execute
        results = await self._execute_plan(query, plan)
        
        # Step 4: Synthesize
        final_answer = await self._synthesize_results(query, results)
        
        return final_answer
    
    async def _classify_complexity(self, query: str) -> str:
        """
        Use LLM to classify query as SIMPLE or COMPLEX.
        
        SIMPLE: One worker can handle it
        COMPLEX: Needs multiple workers or steps
        """
        prompt = f"""Classify this query:
        
Query: {query}

Is this SIMPLE (one worker) or COMPLEX (multiple workers)?
Reply with only: SIMPLE or COMPLEX"""
        
        # Call LLM and return classification
        ...
    
    async def _plan_execution(self, query: str) -> Dict:
        """
        Plan which workers to call and in what order.
        
        Returns:
            {
                "agents": ["worker_agent_1", "worker_agent_2"],
                "parallel": True,
                "reasoning": "Need both data and validation"
            }
        """
        prompt = f"""Plan execution for this query:

Query: {query}

Available agents:
- worker_agent_1: Data extraction and analysis
- worker_agent_2: Validation and compliance checking

Return JSON:
{{
    "agents": ["agent1", "agent2"],
    "parallel": true/false,
    "reasoning": "why this plan"
}}"""
        
        # Call LLM and parse JSON response
        ...
    
    async def _call_worker(self, agent_url: str, query: str) -> Dict:
        """
        Call a worker agent via A2A protocol.
        
        Sends POST to {agent_url}/task with the query.
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{agent_url}/task",
                json={"message": {"content": {"text": query}}}
            ) as response:
                return await response.json()
    
    async def _execute_plan(self, query: str, plan: Dict) -> List[Dict]:
        """
        Execute the plan by calling workers.
        
        If parallel=True, use asyncio.gather for concurrent execution.
        """
        agent_map = {
            "worker_agent_1": self.worker_agent_1_url,
            "worker_agent_2": self.worker_agent_2_url
        }
        
        if plan.get("parallel"):
            # Run in parallel
            tasks = [
                self._call_worker(agent_map[agent], query)
                for agent in plan["agents"]
            ]
            results = await asyncio.gather(*tasks)
        else:
            # Run sequentially
            results = []
            for agent in plan["agents"]:
                result = await self._call_worker(agent_map[agent], query)
                results.append(result)
        
        return results
    
    async def _synthesize_results(self, query: str, results: List[Dict]) -> str:
        """
        Combine results from multiple workers into final answer.
        """
        prompt = f"""Synthesize these results into a comprehensive answer:

Original Query: {query}

Results from agents:
{json.dumps(results, indent=2)}

Provide a unified answer that:
1. Directly answers the query
2. Highlights key findings from each agent
3. Notes any conflicts between agent outputs
4. Provides recommendations"""
        
        # Call LLM to synthesize
        ...
```

---

## Step 5: Configure the System

### config/registry.yaml

This file defines all your services and their relationships.

```yaml
# =============================================================================
# Service Registry - CUSTOMIZE ALL NAMES AND PORTS
# =============================================================================

# MCP Tools (deterministic, no LLM)
tools:
  tool_1:
    host: localhost
    port: 11001
    enabled: true
    description: "Database query tool"
    script: tools/tool_1.py
    
  tool_2:
    host: localhost
    port: 11002
    enabled: true
    description: "Rules/validation engine"
    script: tools/tool_2.py

# A2A Agents (LLM-powered)
agents:
  manager:
    host: localhost
    port: 8100
    enabled: true
    description: "Orchestrator"
    script: agents/manager/manager_agent.py
    depends_on:
      - worker_1
      - worker_2
      
  worker_1:
    host: localhost
    port: 8101
    enabled: true
    description: "Data extraction worker"
    script: agents/workers/worker_agent_1.py
    uses_tools:
      - tool_1
      
  worker_2:
    host: localhost
    port: 8102
    enabled: true
    description: "Validation worker"
    script: agents/workers/worker_agent_2.py
    uses_tools:
      - tool_1
      - tool_2

# Service discovery settings
discovery:
  auto_discover: false
  health_check_interval: 30
```

### .env

```bash
# LLM Configuration
API_KEY=your-api-key-here
MODEL=openai/gpt-oss-20b
TEMPERATURE=0
BASE_URL=              # Leave empty for OpenAI, or use OpenRouter URL

# For OpenRouter (cheaper alternative):
# API_KEY=sk-or-v1-your-key
# BASE_URL=https://openrouter.ai/api/v1
# MODEL=openai/gpt-oss-20b
```

---

## Step 6: Create the Orchestration Script

### run.sh

The one-command startup script that brings everything up in the right order.

```bash
#!/bin/bash
# =============================================================================
# Reasoning Agents Framework - Startup Script
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Reasoning Agents Framework - Starting Up              ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"

# Install dependencies
echo -e "${GREEN}▸${NC} Installing dependencies..."
uv sync --quiet

# Create directories
mkdir -p logs data/query_results

# Start MCP Tools (The Hands)
echo -e "${GREEN}▸${NC} Starting Tool 1 (port 11001)..."
uv run python tools/tool_1.py > logs/tool_1.log 2>&1 &

echo -e "${GREEN}▸${NC} Starting Tool 2 (port 11002)..."
uv run python tools/tool_2.py > logs/tool_2.log 2>&1 &

sleep 3

# Start Worker Agents (The Brain - Specialists)
echo -e "${GREEN}▸${NC} Starting Worker Agent 1 (port 8101)..."
uv run python agents/workers/worker_agent_1.py > logs/worker_agent_1.log 2>&1 &

echo -e "${GREEN}▸${NC} Starting Worker Agent 2 (port 8102)..."
uv run python agents/workers/worker_agent_2.py > logs/worker_agent_2.log 2>&1 &

sleep 3

# Start Manager Agent (The Brain - Orchestrator)
echo -e "${GREEN}▸${NC} Starting Manager Agent (port 8100)..."
uv run python agents/manager/manager_agent.py > logs/manager_agent.log 2>&1 &

sleep 2

echo ""
echo -e "${GREEN}✓${NC} All services started!"
echo ""
echo "MCP Tools:"
echo "  • Tool 1:  http://localhost:11001"
echo "  • Tool 2:  http://localhost:11002"
echo ""
echo "A2A Agents:"
echo "  • Worker 1: http://localhost:8101"
echo "  • Worker 2: http://localhost:8102"
echo "  • Manager:  http://localhost:8100"
echo ""
echo "Test with:"
echo "  curl -X POST http://localhost:8100/task \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"message\": {\"content\": {\"text\": \"Your query here\"}}}'"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "pkill -f 'tools/tool_'; pkill -f 'agents/'" SIGINT SIGTERM
wait
```

---

## Step 7: Testing

### Start the System

```bash
./run.sh
```

### Test Individual Components

```bash
# Test Worker Agent 1 directly
curl -X POST http://localhost:8101/task \
  -H "Content-Type: application/json" \
  -d '{"message": {"content": {"text": "What columns are available?"}}}'

# Test Worker Agent 2 directly
curl -X POST http://localhost:8102/task \
  -H "Content-Type: application/json" \
  -d '{"message": {"content": {"text": "What rules can you check?"}}}'
```

### Test the Full System

```bash
# Send query to Manager
curl -X POST http://localhost:8100/task \
  -H "Content-Type: application/json" \
  -d '{"message": {"content": {"text": "Analyze the data and find any issues"}}}'
```

### Check Logs

```bash
# Real-time logs
tail -f logs/manager_agent.log

# Structured events (audit trail)
cat logs/manageragent_events.jsonl | jq .
```

---

## Customizing for Your Domain

### Step 1: Replace the Data

```bash
# Replace sample data with yours
cp your_data.csv data/
cp your_rules.json data/
```

### Step 2: Update Tool 1

Edit `tools/tool_1.py`:
- Change `DATA_PATH` to your file
- Update `get_record_by_id()` with your ID column
- Add any custom query functions

### Step 3: Update Tool 2

Edit `tools/tool_2.py`:
- Change `RULES_PATH` to your rules file
- Update `evaluate_condition()` for your schema
- Add custom validation functions

### Step 4: Update Prompts

Edit `prompts/worker_agent_1.txt` and `prompts/worker_agent_2.txt`:
- Describe your domain
- List your tools and what they do
- Define the expected response format

### Step 5: Rename Components (Optional)

If you want clearer names:
1. Rename files (`worker_agent_1.py` → `data_analyst.py`)
2. Update class names
3. Update `config/registry.yaml`
4. Update `run.sh`

---

## Conclusion

You now have a complete reasoning system with:

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Manager Agent** | Orchestration, planning, synthesis | LangChain + A2A |
| **Worker Agents** | Specialized reasoning | LangGraph ReAct + MCP |
| **MCP Tools** | Deterministic execution | FastMCP + DuckDB |
| **Configuration** | Service discovery | YAML + dotenv |
| **Logging** | Audit trail | JSONL structured events |

### Key Concepts

1. **Brain vs Hands**: Agents think (LLM), tools execute (deterministic)
2. **Manager-Worker Pattern**: Manager routes, workers specialize
3. **ReAct Pattern**: Reason → Act → Observe → Repeat
4. **Data-Agnostic Prompts**: Use `get_schema()` to discover data dynamically
5. **Full Audit Trail**: Every step logged to JSONL

### Next Steps

1. **Add more workers** for additional specializations
2. **Add more tools** for new capabilities
3. **Customize prompts** for your domain
4. **Deploy** with Docker or your preferred platform

---

*This framework is designed to be customized. Look for `CUSTOMIZE` comments throughout the code to find what to change for your use case.*
