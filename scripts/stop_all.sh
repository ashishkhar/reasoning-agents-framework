#!/bin/bash
# =============================================================================
# Stop All Services Script
# =============================================================================
# Stops all running tools and agents.
#
# Usage:
#   ./scripts/stop_all.sh
# =============================================================================

echo "Stopping all Reasoning Agents Framework services..."
echo ""

# Kill by script name
pkill -f "tools/tool_1.py" 2>/dev/null && echo "✓ Stopped Tool 1" || echo "• Tool 1 not running"
pkill -f "tools/tool_2.py" 2>/dev/null && echo "✓ Stopped Tool 2" || echo "• Tool 2 not running"
pkill -f "agents/workers/worker_agent_1.py" 2>/dev/null && echo "✓ Stopped Worker Agent 1" || echo "• Worker Agent 1 not running"
pkill -f "agents/workers/worker_agent_2.py" 2>/dev/null && echo "✓ Stopped Worker Agent 2" || echo "• Worker Agent 2 not running"
pkill -f "agents/manager/manager_agent.py" 2>/dev/null && echo "✓ Stopped Manager Agent" || echo "• Manager Agent not running"

# Remove PID file if exists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
rm -f "$SCRIPT_DIR/.running_pids"

echo ""
echo "All services stopped."
