# =============================================================================
# MCP Tool 2 - Example Rules/Validation Engine
# =============================================================================
"""
Example MCP Tool for rule-based validation.

CUSTOMIZE THIS TOOL:
- Change RULES_PATH to point to your rules JSON file
- Update rule evaluation logic in evaluate_condition()
- Rename tool functions to match your use case
- Modify the logger name and MCP server name

This tool provides deterministic rule evaluation for auditable validation.

Usage:
    python -m tools.tool_2
    
    The tool will start on port 11002 (configurable via TOOL_2_PORT env var)
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path for imports when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP

from core.config import get_config
from core.logging_utils import log_event, setup_logging


# =============================================================================
# Configuration - CUSTOMIZE THESE
# =============================================================================

config = get_config()
config.ensure_directories()

# CUSTOMIZE: Change to your rules file
RULES_PATH = config.data_dir / "compliance_rules.json"

# CUSTOMIZE: Change logger and server names
logger = setup_logging("Tool2", log_level=config.log_level)
mcp = FastMCP("Validation Engine Tool")


# =============================================================================
# Helper Functions - CUSTOMIZE AS NEEDED
# =============================================================================

def load_rules() -> List[Dict]:
    """Load rules from the JSON file."""
    if not RULES_PATH.exists():
        raise FileNotFoundError(f"Rules file not found at {RULES_PATH}")
    
    with open(RULES_PATH, 'r') as f:
        data = json.load(f)
    
    return data.get("rules", [])


def parse_numeric_value(text: str) -> int:
    """Extract numeric value from text. CUSTOMIZE for your use case."""
    match = re.search(r'(\d+)', str(text))
    return int(match.group(1)) if match else 0


def evaluate_condition(condition: str, record: Dict) -> bool:
    """
    Safely evaluate a rule condition against record data.
    
    CUSTOMIZE: Update context variables to match your data schema.
    """
    # Build evaluation context from record data
    context = {
        "termination_notice_days": parse_numeric_value(
            str(record.get("termination_clause", ""))
        ),
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


# =============================================================================
# MCP Tools - CUSTOMIZE THESE
# =============================================================================

@mcp.tool()
def validate_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a record against all rules.
    
    CUSTOMIZE: Update docstring with your actual record fields.
    
    Args:
        record: Dictionary containing record details
    
    Returns:
        Dictionary with validation results
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
                logger.info(f"VIOLATION: {rule['id']} - {rule['name']}")
            else:
                passed.append(result)
        
        log_event("Tool2", "VALIDATION_RESULT", {
            "record_id": record_id,
            "violations": len(violations),
            "passed": len(passed)
        })
        
        return {
            "success": True,
            "record_id": record_id,
            "is_valid": len(violations) == 0,
            "violation_count": len(violations),
            "violations": violations,
            "passed_rules": passed,
            "summary": (
                f"Record {record_id} checked against {len(rules)} rules: "
                f"{len(violations)} violations, {len(passed)} passed"
            )
        }
        
    except Exception as e:
        log_event("Tool2", "VALIDATION_ERROR", {"error": str(e)})
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_rules() -> Dict[str, Any]:
    """
    List all available validation rules.
    
    Returns:
        Dictionary with rule_count and rules list
    """
    try:
        rules = load_rules()
        return {"success": True, "rule_count": len(rules), "rules": rules}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def evaluate_rule(rule_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate a specific rule against a record.
    
    Args:
        rule_id: ID of the rule to evaluate
        record: Record data dictionary
    
    Returns:
        Dictionary with rule evaluation result
    """
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
    # CUSTOMIZE: Change env var and default port
    port = int(os.getenv("TOOL_2_PORT", "11002"))
    
    logger.info(f"🔧 Starting Tool 2 on port {port}")
    logger.info(f"📋 Rules path: {RULES_PATH}")
    
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = port
    mcp.run(transport="streamable-http")
