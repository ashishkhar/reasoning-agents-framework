# =============================================================================
# MCP Tool 1 - Example Database Query Tool
# =============================================================================
"""
Example MCP Tool for database queries.

CUSTOMIZE THIS TOOL:
- Change the data source (DATA_PATH) to your data file
- Rename the tool functions to match your use case
- Update the docstrings with your schema/columns
- Modify the logger name and MCP server name

This tool uses DuckDB as an embedded SQL engine for fast queries.

Usage:
    python -m tools.tool_1
    
    The tool will start on port 11001 (configurable via TOOL_1_PORT env var)
"""

import os
import sys

# Add parent directory to path for imports when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from typing import Any, Dict

import duckdb
from fastmcp import FastMCP

from core.config import get_config
from core.logging_utils import log_event, setup_logging


# =============================================================================
# Configuration - CUSTOMIZE THESE
# =============================================================================

config = get_config()
config.ensure_directories()

# CUSTOMIZE: Change to your data file
DATA_PATH = config.data_dir / "contracts.csv"
RESULTS_PATH = config.data_dir / "query_results"
RESULTS_PATH.mkdir(exist_ok=True)

# CUSTOMIZE: Change logger and server names
logger = setup_logging("Tool1", log_level=config.log_level)
mcp = FastMCP("Database Query Tool")


# =============================================================================
# Helper Functions
# =============================================================================

def get_database_connection():
    """
    Create a DuckDB connection with data loaded.
    
    CUSTOMIZE: Change 'contracts' to your table name.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data not found at {DATA_PATH}")
    
    conn = duckdb.connect(':memory:')
    
    # CUSTOMIZE: Change table name 'data' to match your use case
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
    
    CUSTOMIZE: Update docstring with your actual columns.
    
    Args:
        sql_query: SQL query to execute. Table name is 'data'.
        output_filename: Filename to save results as CSV.
    
    Returns:
        Dictionary with success, row_count, columns, preview, all_results
    """
    try:
        log_event("Tool1", "QUERY_RECEIVED", {
            "query": sql_query,
            "filename": output_filename
        })
        
        conn = get_database_connection()
        result_df = conn.execute(sql_query).fetchdf()
        conn.close()
        
        # Save results
        save_path = RESULTS_PATH / output_filename
        result_df.to_csv(save_path, index=False)
        
        # Convert to JSON-serializable format
        all_results = result_df.to_dict('records')
        for row in all_results:
            for key, value in row.items():
                if hasattr(value, 'isoformat'):
                    row[key] = value.isoformat()
                elif hasattr(value, 'item'):
                    row[key] = value.item()
        
        log_event("Tool1", "QUERY_SUCCESS", {
            "query": sql_query,
            "row_count": len(result_df),
            "columns": list(result_df.columns),
            "results": all_results
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
    
    CUSTOMIZE: Change column name 'id' to your primary key column.
    
    Args:
        record_id: The record identifier
    
    Returns:
        Dictionary with success flag and record data
    """
    try:
        log_event("Tool1", "RECORD_LOOKUP", {"record_id": record_id})
        
        conn = get_database_connection()
        # CUSTOMIZE: Change 'id' to your actual ID column name
        result_df = conn.execute(f"""
            SELECT * FROM data WHERE contract_id = '{record_id}'
        """).fetchdf()
        conn.close()
        
        if result_df.empty:
            return {"success": False, "error": f"Record {record_id} not found"}
        
        record = result_df.iloc[0].to_dict()
        return {"success": True, "record": record}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_schema() -> Dict[str, Any]:
    """
    Get schema information for the data table.
    
    Returns:
        Dictionary with columns, types, and row count
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
    # CUSTOMIZE: Change env var and default port
    port = int(os.getenv("TOOL_1_PORT", "11001"))
    
    logger.info(f"🔧 Starting Tool 1 on port {port}")
    logger.info(f"📂 Data path: {DATA_PATH}")
    
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = port
    mcp.run(transport="streamable-http")
