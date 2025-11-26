import json
import sqlite3
from typing import Any, Dict, List, Union

from pydantic import BaseModel, Field

from utils.db_client import NorthwindDB


# Input Schema for the LLM
class SqlQueryArgs(BaseModel):
    query: str = Field(
        description="The SQL query to execute. Must be a read-only statement (SELECT or WITH)."
    )


def execute_sql(query: str) -> str:
    """
    Executes a SQL query against the Northwind database.

    SECURITY:
    - STRICTLY READ-ONLY.
    - Allows 'SELECT' and 'WITH' (CTEs).
    - Rejects 'UPDATE', 'INSERT', 'DELETE', 'DROP', 'ALTER'.
    """
    conn = NorthwindDB.get_connection()
    if not conn:
        return json.dumps(
            {
                "status": "error",
                "data": None,
                "message": "System Error: Could not connect to database.",
            }
        )

    # --- SECURITY CHECKS ---
    clean_query = query.strip().upper()

    forbidden_keywords = [
        "UPDATE ",
        "INSERT ",
        "DELETE ",
        "DROP ",
        "ALTER ",
        "TRUNCATE ",
        "REPLACE ",
        "CREATE ",
    ]

    if any(keyword in clean_query for keyword in forbidden_keywords):
        return json.dumps(
            {
                "status": "error",
                "data": None,
                "message": "Security Error: Data modification commands are strictly forbidden.",
            }
        )

    if not (clean_query.startswith("SELECT") or clean_query.startswith("WITH")):
        return json.dumps(
            {
                "status": "error",
                "data": None,
                "message": "Security Error: Only SELECT or WITH queries are allowed.",
            }
        )

    try:
        cursor = conn.cursor()
        cursor.execute(query)

        # Fetch results
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]

        return json.dumps(
            {
                "status": "success",
                "data": results,
                "message": f"Successfully retrieved {len(results)} rows.",
            },
            default=str,
        )

    except Exception as e:
        # Return the error in a way the LLM can easily read to fix its own code
        return json.dumps(
            {"status": "error", "data": str(e), "message": f"SQL Error: {str(e)}"}
        )


def get_db_schema() -> str:
    """Helper for the agent to see the database structure."""
    return NorthwindDB.get_schema()
