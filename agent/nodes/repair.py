import logging

import dspy

from agent.dspy_signatures import RepairSQLSignature
from agent.state import AgentState
from tools.sqlite_tool import get_db_schema

logger = logging.getLogger("RepairNode")

# Initialize module
repair_module = dspy.ChainOfThought(RepairSQLSignature)


def repair_sql_node(state: AgentState) -> dict:
    """
    Attempts to fix a broken SQL query using the error message and schema.
    Increments 'repair_steps'.
    """
    question = state["question"]
    bad_query = state.get("sql_query", "")
    error_message = str(state.get("sql_result", "Unknown Error"))
    constraints = state.get("constraints", {})
    format_hint = state.get("format_hint", "str")

    steps = state.get("repair_steps", 0) + 1
    logger.info(f"🔧 Repairing SQL (Attempt {steps})...")
    logger.info(f"   Error: {error_message}")

    schema_str = get_db_schema()
    constraints_str = str(constraints) if constraints else "None"

    try:
        pred = repair_module(
            question=question,
            bad_query=bad_query,
            error_message=error_message,
            db_schema=schema_str,
            constraints=constraints_str,
            format_hint=format_hint,
        )

        if hasattr(pred, "reasoning"):
            logger.info(f"🧠 Repair Logic: {pred.reasoning}")

        raw_query = pred.fixed_sql
        logger.info(f"📝 Raw Fixed SQL: {raw_query}")

        # Clean SQL
        clean_query = raw_query.replace("```sql", "").replace("```", "").strip()
        if clean_query.lower().startswith("sql"):
            clean_query = clean_query[3:].strip()

        logger.info(f"✅ Fixed SQL: {clean_query}")

    except Exception as e:
        logger.error(f"❌ Repair failed: {e}")
        clean_query = bad_query  # Keep original if repair crashes

    return {"sql_query": clean_query, "repair_steps": steps}
