import json
import logging

from agent.state import AgentState
from tools.sqlite_tool import execute_sql

logger = logging.getLogger("ExecutorNode")


def execute_sql_node(state: AgentState) -> dict:
    """
    Executes the SQL query found in the state.
    Updates 'sql_result' and sets 'is_sql_error' flag.
    """
    query = state.get("sql_query", "")
    logger.info(f"⚡ Executing SQL...")

    result_str = execute_sql(query)

    logger.info(f"🔌 Tool Raw Output: {result_str}")

    # Default values
    sql_result = []
    is_error = False

    try:
        response = json.loads(result_str)
        status = response.get("status")
        message = response.get("message", "")

        if status == "success":
            # We save DATA to state (for the AI to read)
            sql_result = response.get("data", [])
            is_error = False
            # We log the MESSAGE (for you to read)
            logger.info(f"✅ Success: {message}")
        else:
            # On error, the result IS the message (so the AI knows what broke)
            sql_result = message
            is_error = True
            logger.warning(f"⚠️ SQL Execution Error: {sql_result}")

    except json.JSONDecodeError:
        sql_result = "System Error: Failed to parse execution response."
        is_error = True
        logger.error(f"❌ JSON Parse Error on: {result_str}")
    except Exception as e:
        sql_result = f"System Error: {str(e)}"
        is_error = True
        logger.error(f"❌ Execution Exception: {e}")

    return {"sql_result": sql_result, "is_sql_error": is_error}
