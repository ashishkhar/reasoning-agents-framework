# Reasoning Agents Framework

A **modular framework** for building multi-agent reasoning systems using the [A2A protocol](https://github.com/google/a2a) and [MCP tools](https://modelcontextprotocol.io/).

## 🧠 What It Does

**Give it your data → It reasons and analyzes → Returns verifiable results**

```
┌─────────────────────────────────────────────────────────────────────┐
│                         YOUR DATA                                   │
│              (CSV, JSON, Database, API, anything)                   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    🧠 A2A AGENTS (The Brain)                        │
│                                                                     │
│  • THINK about what to do                                           │
│  • PLAN execution steps                                             │
│  • REASON about results                                             │
│  • SYNTHESIZE answers                                               │
│                                                                     │
│  (LLM-powered, using A2A protocol for agent-to-agent communication) │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    🔧 MCP TOOLS (The Hands)                         │
│                                                                     │
│  • EXECUTE deterministic operations                                 │
│  • QUERY databases with SQL                                         │
│  • VALIDATE against rules                                           │
│  • CALCULATE metrics                                                │
│                                                                     │
│  (No LLM - pure logic, 100% reproducible, fully auditable)          │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    📊 VERIFIED RESULTS                              │
│                                                                     │
│  • Every step logged                                                │
│  • Every tool call traceable                                        │
│  • Every decision explainable                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

| Component | Role | Analogy |
|-----------|------|---------|
| **A2A Agents** | Think, plan, reason | 🧠 Brain |
| **MCP Tools** | Execute, query, validate | 🔧 Hands |
| **Manager** | Orchestrate, delegate, synthesize | 👔 Manager |
| **Workers** | Specialize in specific domains | 👷 Specialists |

**Result**: An AI system that can *think* about your data while producing *deterministic*, *auditable* results.

---

## 🤖 Customize with AI (Cursor/Antigravity)

The fastest way to adapt this framework is to open it in an AI-powered editor and ask it to customize for you.

### Step 1: Open in Your AI Editor

```bash
# Clone and open in Cursor
git clone https://github.com/ashishkhar/reasoning-agents-framework.git
cursor reasoning-agents-framework

# Or use VS Code with Antigravity/Copilot
code reasoning-agents-framework
```

### Step 2: Ask AI to Customize

Copy one of these prompts to your AI assistant:

#### 🎯 Full Customization Prompt

```
I want to customize this Reasoning Agents Framework for my use case: [YOUR DOMAIN].

Please help me:
1. Rename worker_agent_1.py to handle [YOUR FIRST TASK] - update the class name, prompts, and registry
2. Rename worker_agent_2.py to handle [YOUR SECOND TASK] - update the class name, prompts, and registry
3. Update tool_1.py to query my data file [YOUR DATA FILE] with columns [YOUR COLUMNS]
4. Update tool_2.py to validate against my rules [YOUR RULES]
5. Update prompts/ files with domain-specific instructions
6. Update config/registry.yaml with the new names
7. Update run.sh to use the new file names

My data looks like: [PASTE SAMPLE OF YOUR DATA]
My validation rules are: [DESCRIBE YOUR RULES]
```

#### � Quick Examples

**For a Customer Support System:**
```
Customize this framework for a customer support ticket analyzer:
- Worker 1: Ticket Classification Agent (categorize tickets by urgency/type)
- Worker 2: Response Suggestion Agent (suggest responses based on knowledge base)
- Tool 1: Query tickets database (columns: ticket_id, customer, issue, priority, status)
- Tool 2: Search knowledge base for relevant articles
```

**For a Financial Analysis System:**
```
Customize this framework for financial portfolio analysis:
- Worker 1: Market Data Agent (fetch and analyze stock data)
- Worker 2: Risk Assessment Agent (evaluate portfolio risk)
- Tool 1: Query market data API
- Tool 2: Calculate risk metrics (VaR, Sharpe ratio, etc.)
```

**For a Content Moderation System:**
```
Customize this framework for content moderation:
- Worker 1: Content Analysis Agent (analyze text/images for policy violations)
- Worker 2: Appeal Review Agent (review flagged content appeals)
- Tool 1: Query content database
- Tool 2: Check against moderation rules
```

### Step 3: Test Your Customization

```bash
# Start the system
./run.sh

# Test your custom query
curl -X POST http://localhost:8100/task \
  -H "Content-Type: application/json" \
  -d '{"message": {"content": {"text": "Your custom query here"}}}'
```

---

## �🚀 Manual Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/ashishkhar/reasoning-agents-framework.git
cd reasoning-agents-framework

# 2. Copy environment file and add your API key
cp .env.example .env
# Edit .env with your LLM API credentials

# 3. Run everything
./run.sh
```

That's it! The system will:
1. Install dependencies via `uv`
2. Start MCP tools
3. Start worker agents
4. Start the manager agent

---

## 📁 Project Structure

```
reasoning-agents-framework/
├── core/                    # Framework base classes (don't modify)
│   ├── base_agent.py        # Abstract agent class
│   ├── config.py            # Configuration management
│   └── logging_utils.py     # Structured logging
│
├── agents/                  # 🎯 CUSTOMIZE THESE
│   ├── manager/
│   │   └── manager_agent.py # Orchestrator (modify routing logic)
│   └── workers/
│       ├── worker_agent_1.py  # Rename & customize
│       └── worker_agent_2.py  # Rename & customize
│
├── tools/                   # 🎯 CUSTOMIZE THESE
│   ├── tool_1.py            # Rename & customize (database queries)
│   └── tool_2.py            # Rename & customize (rule evaluation)
│
├── prompts/                 # 🎯 CUSTOMIZE THESE
│   ├── worker_agent_1.txt   # System prompt for worker 1
│   ├── worker_agent_2.txt   # System prompt for worker 2
│   └── manager_agent.txt    # System prompt for manager
│
├── data/                    # 🎯 REPLACE WITH YOUR DATA
│   ├── contracts.csv        # Example data (replace with yours)
│   └── compliance_rules.json # Example rules (replace with yours)
│
├── config/
│   └── registry.yaml        # 🎯 UPDATE with your component names
│
├── scripts/                 # Helper scripts
├── logs/                    # Runtime logs
├── run.sh                   # One-command startup
└── .env                     # API keys (create from .env.example)
```

### What to Customize (Look for `# CUSTOMIZE` comments)

| File | What to Change |
|------|---------------|
| `agents/workers/worker_agent_1.py` | Class name, port, tools list, prompt file |
| `agents/workers/worker_agent_2.py` | Class name, port, tools list, prompt file |
| `tools/tool_1.py` | Data file path, table name, tool functions |
| `tools/tool_2.py` | Rules file path, validation logic |
| `prompts/*.txt` | Agent behavior instructions |
| `config/registry.yaml` | Component names, ports, dependencies |
| `data/*.csv`, `data/*.json` | Your actual data files |

---

## 🏗️ Architecture

### Level 1: High-Level Overview

![Component Architecture](public/Component%20Architecture.svg)

### Level 2: Component Details

![Component Diagram](public/Component%20Diagram.svg)

### Level 3: Query Flow

![Detailed Query Flow](public/Detailed%20Query%20Flow.svg)


---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Required
API_KEY="your-llm-api-key"

# Optional
MODEL="openai/gpt-oss-20b"           # or any OpenAI-compatible model
TEMPERATURE=0                  # 0 for deterministic responses
BASE_URL=""                    # Custom endpoint (e.g., OpenRouter, Azure)
```

### Using OpenRouter (Recommended for Cost)

```bash
API_KEY="sk-or-v1-your-openrouter-key"
BASE_URL="https://openrouter.ai/api/v1"
MODEL="openai/gpt-oss-20b"  # or anthropic/claude-3-haiku
```

---

## 📖 Usage

### Test the Manager Agent

```bash
curl -X POST http://localhost:8100/task \
  -H "Content-Type: application/json" \
  -d '{"message": {"content": {"text": "Your query here"}}}'
```

### Query Specific Workers

```bash
# Worker Agent 1
curl -X POST http://localhost:8101/task \
  -H "Content-Type: application/json" \
  -d '{"message": {"content": {"text": "Your query for worker 1"}}}'
```

### Health Check & Stop

```bash
./scripts/health_check.sh   # Check all services
./scripts/stop_all.sh       # Stop all services
```

---

## 📊 Logs & Audit Trail

All activity is logged to `logs/`:
- `*.log` - Standard logs
- `*_events.jsonl` - Structured events (for audit)

```bash
# Watch real-time logs
tail -f logs/manager_agent.log

# Parse structured events
cat logs/manageragent_events.jsonl | jq .
```

---

## 🔧 Adding More Agents/Tools

See detailed guides:
- [Adding New Agents](docs/ADDING_AGENTS.md)
- [Adding New Tools](docs/ADDING_TOOLS.md)
- [Architecture Overview](docs/ARCHITECTURE.md)

---

## 🛠️ Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- LLM API access (OpenAI, Azure, OpenRouter, or compatible)

---

## 📄 License

MIT License - see [LICENSE](LICENSE)
