import ast
import json
import logging

import dspy

from agent.dspy_signatures import PlannerSignature
from agent.state import AgentState

logger = logging.getLogger("PlannerNode")

# Initialize the DSPy module once
planner_module = dspy.ChainOfThought(PlannerSignature)


def plan_query(state: AgentState) -> dict:
    """
    1. Read 'retrieved_docs' from state.
    2. Planning: Uses LLM to extract structured constraints.
    3. Update: Saves result to state['constraints'].
    """
    question = state["question"]
    docs = state.get("retrieved_docs", [])

    logger.info(f"🗓️ Planning for: {question[:50]}...")

    # Format Context
    if docs:
        context_str = "\n\n".join(
            [
                f"Source: {r.get('id', 'unknown')}\nContent: {r.get('content', '')}"
                for r in docs
            ]
        )
    else:
        logger.warning("⚠️ No docs found in state. Planner might fail.")
        context_str = ""

    # Extract Constraints (DSPy)
    constraints = {}
    try:
        pred = planner_module(question=question, context=context_str)

        if hasattr(pred, "reasoning"):
            logger.info(f"🧠 Planner Thought: {pred.reasoning}")
        raw_constraints = pred.constraints
        logger.info(f"📝 Raw Constraints Output: {raw_constraints}")

        # Parse Logic
        # 1. Strip Markdown
        # Validates variable name: cleaned_str used everywhere below
        cleaned_str = raw_constraints.replace("```json", "").replace("```", "").strip()

        # 2. Try Standard JSON
        try:
            constraints = json.loads(cleaned_str)
        except json.JSONDecodeError:
            # 3. Try Python Literal Eval (Handles single quotes: {'key': 'val'})
            try:
                logger.info("⚠️ JSON failed, trying Python literal_eval...")
                constraints = ast.literal_eval(cleaned_str)
            except Exception:
                logger.error(f"❌ Failed to parse constraints: {cleaned_str}")
                constraints = {}

        logger.info(f"✅ Extracted Constraints: {constraints}")

    except Exception as e:
        logger.error(f"❌ Planner Critical Error: {e}")
        constraints = {}

    return {"constraints": constraints}
