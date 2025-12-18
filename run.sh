#!/bin/bash
# =============================================================================
# Reasoning Agents Framework - Main Run Script
# =============================================================================
# 
# This script starts the complete reasoning system with one command.
#
# Usage:
#   ./run.sh          # Start all services
#   ./run.sh --tools  # Start only MCP tools
#   ./run.sh --agents # Start only agents (tools must be running)
#
# Requirements:
#   - uv (https://github.com/astral-sh/uv)
#   - Python 3.11+
#   - .env file with API credentials
#
# =============================================================================

set -e  # Exit on error

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# PID file to track running processes
PID_FILE="$SCRIPT_DIR/.running_pids"

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_step() {
    echo -e "${GREEN}▸${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Check if a port is in use
check_port() {
    nc -z localhost $1 2>/dev/null
    return $?
}

# Wait for a service to be ready
wait_for_service() {
    local port=$1
    local name=$2
    local timeout=30
    local count=0
    
    while ! check_port $port; do
        sleep 1
        count=$((count + 1))
        if [ $count -ge $timeout ]; then
            print_error "$name failed to start on port $port"
            return 1
        fi
    done
    print_success "$name is ready on port $port"
    return 0
}

# Cleanup function for graceful shutdown
cleanup() {
    echo ""
    print_header "Stopping all services..."
    
    if [ -f "$PID_FILE" ]; then
        while read pid; do
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
            fi
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    
    # Also kill by name as fallback
    pkill -f "tools/tool_1.py" 2>/dev/null || true
    pkill -f "tools/tool_2.py" 2>/dev/null || true
    pkill -f "agents/workers/worker_agent_1.py" 2>/dev/null || true
    pkill -f "agents/workers/worker_agent_2.py" 2>/dev/null || true
    pkill -f "agents/manager/manager_agent.py" 2>/dev/null || true
    
    print_success "All services stopped"
    exit 0
}

# -----------------------------------------------------------------------------
# Pre-flight Checks
# -----------------------------------------------------------------------------

preflight_checks() {
    print_header "Pre-flight Checks"
    
    # Check for uv
    if ! command -v uv &> /dev/null; then
        print_error "uv is not installed!"
        echo ""
        echo "Install uv with:"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo ""
        exit 1
    fi
    print_success "uv is installed"
    
    # Check for .env file
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_warning ".env file not found. Copying from .env.example"
            cp .env.example .env
            print_warning "Please edit .env with your API credentials"
        else
            print_error ".env file not found!"
            exit 1
        fi
    fi
    print_success ".env file exists"
    
    # Check for data files
    if [ ! -f "data/contracts.csv" ]; then
        print_error "data/contracts.csv not found!"
        exit 1
    fi
    print_success "Data files exist"
}

# -----------------------------------------------------------------------------
# Environment Setup
# -----------------------------------------------------------------------------

setup_environment() {
    print_header "Setting up Python environment"
    
    # Sync dependencies with uv
    print_step "Installing dependencies with uv..."
    uv sync --quiet
    
    print_success "Dependencies installed"
    
    # Create logs directory
    mkdir -p logs
    mkdir -p data/query_results
    
    print_success "Directories ready"
}

# -----------------------------------------------------------------------------
# Start MCP Tools
# -----------------------------------------------------------------------------

start_tools() {
    print_header "Starting MCP Tools"
    
    # Clear PID file
    > "$PID_FILE"
    
    # Stop any existing instances
    pkill -f "tools/tool_1.py" 2>/dev/null || true
    pkill -f "tools/tool_2.py" 2>/dev/null || true
    sleep 1
    
    # Start Tool 1
    print_step "Starting Tool 1 (port 11001)..."
    uv run python tools/tool_1.py > logs/tool_1.log 2>&1 &
    echo $! >> "$PID_FILE"
    
    # Start Tool 2
    print_step "Starting Tool 2 (port 11002)..."
    uv run python tools/tool_2.py > logs/tool_2.log 2>&1 &
    echo $! >> "$PID_FILE"
    
    # Wait for tools to be ready
    sleep 2
    wait_for_service 11001 "Tool 1" || exit 1
    wait_for_service 11002 "Tool 2" || exit 1
}

# -----------------------------------------------------------------------------
# Start Agents
# -----------------------------------------------------------------------------

start_agents() {
    print_header "Starting A2A Agents"
    
    # Stop any existing instances
    pkill -f "agents/workers/worker_agent_1.py" 2>/dev/null || true
    pkill -f "agents/workers/worker_agent_2.py" 2>/dev/null || true
    pkill -f "agents/manager/manager_agent.py" 2>/dev/null || true
    sleep 1
    
    # Start Worker Agents
    print_step "Starting Worker Agent 1 (port 8101)..."
    uv run python agents/workers/worker_agent_1.py > logs/worker_agent_1.log 2>&1 &
    echo $! >> "$PID_FILE"
    
    print_step "Starting Worker Agent 2 (port 8102)..."
    uv run python agents/workers/worker_agent_2.py > logs/worker_agent_2.log 2>&1 &
    echo $! >> "$PID_FILE"
    
    # Wait for workers
    sleep 3
    wait_for_service 8101 "Worker Agent 1" || exit 1
    wait_for_service 8102 "Worker Agent 2" || exit 1
    
    # Start Manager Agent
    print_step "Starting Manager Agent (port 8100)..."
    uv run python agents/manager/manager_agent.py > logs/manager_agent.log 2>&1 &
    echo $! >> "$PID_FILE"
    
    wait_for_service 8100 "Manager Agent" || exit 1
}

# -----------------------------------------------------------------------------
# Print Status
# -----------------------------------------------------------------------------

print_status() {
    print_header "System Status"
    
    echo ""
    echo -e "${BLUE}MCP Tools:${NC}"
    echo "  • Tool 1:  http://localhost:11001/mcp"
    echo "  • Tool 2:  http://localhost:11002/mcp"
    echo ""
    echo -e "${BLUE}Worker Agents:${NC}"
    echo "  • Worker Agent 1:   http://localhost:8101"
    echo "  • Worker Agent 2:   http://localhost:8102"
    echo ""
    echo -e "${BLUE}Manager Agent:${NC}"
    echo "  • Manager:          http://localhost:8100"
    echo ""
    echo -e "${BLUE}Logs:${NC} ./logs/"
    echo ""
    print_header "Quick Test"
    echo ""
    echo "curl -X POST http://localhost:8100/task \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"message\": {\"content\": {\"text\": \"Find contracts with liability over \$1M\"}}}'"
    echo ""
    echo -e "${GREEN}Press Ctrl+C to stop all services${NC}"
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

main() {
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║         Reasoning Agents Framework - Ready to Customize       ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
    
    # Handle arguments
    case "${1:-all}" in
        --tools)
            preflight_checks
            setup_environment
            start_tools
            ;;
        --agents)
            start_agents
            ;;
        all|*)
            preflight_checks
            setup_environment
            start_tools
            start_agents
            ;;
    esac
    
    print_status
    
    # Set up signal handler for cleanup
    trap cleanup SIGINT SIGTERM
    
    # Keep script running
    wait
}

main "$@"
