#!/bin/bash
# =============================================================================
# Health Check Script
# =============================================================================
# Checks if all services are running and responding.
#
# Usage:
#   ./scripts/health_check.sh
#
# Exit codes:
#   0 - All services healthy
#   1 - One or more services unhealthy
# =============================================================================

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

all_healthy=true

check_service() {
    local name=$1
    local url=$2
    local timeout=5
    
    if curl -sf --connect-timeout $timeout "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is healthy"
        return 0
    else
        echo -e "${RED}✗${NC} $name is not responding at $url"
        all_healthy=false
        return 1
    fi
}

echo ""
echo "Checking service health..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "MCP Tools:"
check_service "Tool 1" "http://localhost:11001/mcp"
check_service "Tool 2" "http://localhost:11002/mcp"

echo ""
echo "A2A Agents:"
check_service "Worker Agent 1" "http://localhost:8101/health"
check_service "Worker Agent 2" "http://localhost:8102/health"
check_service "Manager Agent" "http://localhost:8100/health"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if $all_healthy; then
    echo -e "${GREEN}All services are healthy!${NC}"
    exit 0
else
    echo -e "${RED}Some services are not responding.${NC}"
    echo ""
    echo "Check logs in ./logs/ for details."
    exit 1
fi
