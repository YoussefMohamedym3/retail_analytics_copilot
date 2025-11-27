import logging

import dspy

from agent.dspy_signatures import GenerateSQLSignature
from agent.state import AgentState
from tools.sqlite_tool import get_db_schema

logger = logging.getLogger("SQLGenNode")

# Initialize module
sql_module = dspy.ChainOfThought(GenerateSQLSignature)


def generate_sql_node(state: AgentState) -> dict:
    """
    Generates a SQL query based on the question and planner constraints.
    """
    question = state["question"]
    constraints = state.get("constraints", {})
    format_hint = state.get("format_hint", "str")

    logger.info(f"⚙️ Generating SQL for: {question[:50]}...")

    # Fetch Schema
    schema_str = get_db_schema()

    # Format Constraints
    constraints_str = str(constraints) if constraints else "None"

    try:
        # Call DSPy
        pred = sql_module(
            question=question,
            db_schema=schema_str,
            constraints=constraints_str,
            format_hint=format_hint,
        )

        if hasattr(pred, "reasoning"):
            logger.info(f"🧠 SQL Logic: {pred.reasoning}")

        raw_query = pred.sql_query

        logger.info(f"📝 Raw SQL Output: {raw_query}")

        # Clean SQL didn't need it but just in case
        clean_query = raw_query.replace("```sql", "").replace("```", "").strip()
        if clean_query.lower().startswith("sql"):
            clean_query = clean_query[3:].strip()

        logger.info(f"📜 Generated SQL: {clean_query}")

    except Exception as e:
        logger.error(f"❌ SQL Generation failed: {e}")
        clean_query = "-- Error generating SQL"

    return {"sql_query": clean_query}
