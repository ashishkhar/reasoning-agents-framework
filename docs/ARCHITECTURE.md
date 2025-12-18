# Architecture Overview

This document describes the architecture of the Reasoning Agents Framework.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER REQUEST                               │
│                    (Natural Language Query)                          │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      MANAGER AGENT (Port 8100)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐   │
│  │   Classify   │→ │     Plan     │→ │   Execute & Synthesize  │   │
│  │  Complexity  │  │  Execution   │  │        Results          │   │
│  └──────────────┘  └──────────────┘  └─────────────────────────┘   │
└───────────────┬─────────────────────────────────┬───────────────────┘
                │                                 │
                │    A2A Protocol (HTTP/JSON)     │
                │                                 │
    ┌───────────▼────────────┐       ┌───────────▼────────────┐
    │   WORKER AGENT 1       │       │   WORKER AGENT 2       │
    │   (Port 8101)          │       │   (Port 8102)          │
    │   CUSTOMIZE            │       │   CUSTOMIZE            │
    └───────────┬────────────┘       └───────────┬────────────┘
                │                                 │
                │    MCP Protocol (HTTP/JSON)     │
                │                                 │
    ┌───────────▼────────────┐       ┌───────────▼────────────┐
    │   MCP TOOL 1           │       │   MCP TOOL 2           │
    │   (Port 11001)         │       │   (Port 11002)         │
    │                        │       │                        │
    │   - query_data()       │       │   - validate_record()  │
    │   - get_record_by_id() │       │   - list_rules()       │
    │   - get_schema()       │       │   - evaluate_rule()    │
    └───────────┬────────────┘       └───────────┬────────────┘
                │                                 │
    ┌───────────▼────────────┐       ┌───────────▼────────────┐
    │   YOUR DATA FILE       │       │   YOUR RULES FILE      │
    │   (Knowledge Base)     │       │   (Rule Definitions)   │
    └────────────────────────┘       └────────────────────────┘
```

## Component Roles

### Manager Agent

The **brain** of the system. Responsibilities:
- Receive user queries
- Classify complexity (SIMPLE/COMPLEX)
- Plan execution strategy
- Delegate to workers
- Synthesize results

**Does NOT** connect to MCP tools directly.

### Worker Agents

**Specialized experts** for specific domains:
- Connect to MCP tools
- Use ReAct agent pattern with LLM
- Return structured results

**CUSTOMIZE**: Rename and specialize these for your use case.

### MCP Tools

**Deterministic execution layer**:
- Database queries
- Rule evaluation
- Calculations
- No LLM calls - pure logic

**CUSTOMIZE**: Add your own tools for your domain.

## Communication Protocols

### A2A (Agent to Agent)

Used between Manager and Workers.

**Request:**
```json
{
  "message": {
    "content": {
      "type": "text",
      "text": "The query"
    }
  }
}
```

**Response:**
```json
{
  "status": {
    "state": "COMPLETED"
  },
  "artifacts": [{
    "parts": [{
      "type": "text",
      "text": "The response"
    }]
  }]
}
```

### MCP (Model Context Protocol)

Used between Agents and Tools.

**Tool Call:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "query_data",
    "arguments": {
      "sql_query": "SELECT * FROM data",
      "output_filename": "results.csv"
    }
  }
}
```

## Query Flow

### Simple Query

```
User: "Your simple query"
          │
          ▼
   Manager classifies: SIMPLE
          │
          ▼
   Plan: [worker_agent_1], parallel=false
          │
          ▼
   Worker Agent 1 calls Tool 1
          │
          ▼
   Returns data
          │
          ▼
   Manager returns (no synthesis needed)
```

### Complex Query

```
User: "Your complex query requiring multiple agents"
          │
          ▼
   Manager classifies: COMPLEX
          │
          ▼
   Plan: [worker_agent_1, worker_agent_2], parallel=true
          │
          ├──────────────────┬──────────────────┐
          ▼                  ▼                  │
   Worker Agent 1      Worker Agent 2          │
   (fetches data)      (validates data)        │
          │                  │                  │
          └────────┬─────────┘                  │
                   ▼                            │
            Manager synthesizes                 │
            combined results                    │
                   │                            │
                   ▼                            │
            Final comprehensive                 │
            analysis returned                   │
```

## Data Flow

### Database Tool (Tool 1)

```
data/your_data.csv
       │
       ▼
 ┌───────────────┐
 │    DuckDB     │
 │ (in-memory)   │
 └───────────────┘
       │
       ▼
 SQL Query Results
       │
       ▼
 Saved to data/query_results/
```

### Validation Tool (Tool 2)

```
data/your_rules.json
       │
       ▼
 Load rules at startup
       │
       ▼
 Record data in
       │
       ▼
 Evaluate each rule condition
       │
       ▼
 Return: {violations, passed}
```

## Logging & Audit Trail

```
logs/
├── manager_agent.log           # Manager stdout
├── manageragent_events.jsonl   # Structured events
├── worker_agent_1.log
├── workeragent1_events.jsonl
├── worker_agent_2.log
├── workeragent2_events.jsonl
├── tool_1.log
├── tool1_events.jsonl
└── tool_2.log
```

Event log format (JSONL):
```json
{"timestamp": "2024-01-15T10:30:00", "source": "ManagerAgent", "type": "QUERY_RECEIVED", "data": {"query": "..."}}
{"timestamp": "2024-01-15T10:30:01", "source": "ManagerAgent", "type": "PLAN_CREATED", "data": {"agents": ["worker_agent_1"]}}
```

## Configuration Hierarchy

```
.env                    # Secrets (API keys)
       │
       ▼
config/registry.yaml    # Service definitions
       │
       ▼
core/config.py          # Config loader
       │
       ▼
Agents/Tools read       # At startup
```

## Extension Points

1. **Add Worker Agent**: New domain expert
2. **Add MCP Tool**: New deterministic operation
3. **Modify Manager**: New routing logic
4. **Add Data Source**: New knowledge base
5. **Custom Rules**: New validation checks
