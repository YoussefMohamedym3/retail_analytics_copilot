import logging
import os

import dspy

from agent.dspy_signatures import GenerateSQLSignature
from agent.state import AgentState
from tools.sqlite_tool import get_db_schema

logger = logging.getLogger("SQLGenNode")


class SQLModule(dspy.Module):
    """
    Wrapper for the SQL Generation Signature.
    Needed to match the structure used during optimization.
    """

    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(GenerateSQLSignature)

    def forward(self, question, constraints, format_hint, db_schema):
        return self.generate(
            question=question,
            constraints=constraints,
            format_hint=format_hint,
            db_schema=db_schema,
        )


sql_module = SQLModule()


current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level from nodes/ to agent/
opt_path = os.path.join(current_dir, "..", "optimized_sql_module.json")

if os.path.exists(opt_path):
    sql_module.load(opt_path)
    logger.info(f"✅ Loaded Optimized DSPy SQL Module from: {opt_path}")
else:
    logger.warning(
        f"⚠️ Optimization file not found at {opt_path}. Running un-optimized."
    )


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
    constraints_str = str(constraints) if constraints else "None"

    try:
        # CALL THE MODULE
        pred = sql_module(
            question=question,
            db_schema=schema_str,
            constraints=constraints_str,
            format_hint=format_hint,
        )

        if hasattr(pred, "reasoning"):
            logger.info(f"🧠 SQL Logic: {pred.reasoning}")

        raw_query = pred.sql_query

        # Clean SQL formatting
        clean_query = raw_query.replace("```sql", "").replace("```", "").strip()
        if clean_query.lower().startswith("sql"):
            clean_query = clean_query[3:].strip()

        logger.info(f"📜 Generated SQL: {clean_query}")

    except Exception as e:
        logger.error(f"❌ SQL Generation failed: {e}")
        clean_query = "-- Error generating SQL"

    return {"sql_query": clean_query}
