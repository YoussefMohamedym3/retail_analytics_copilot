import logging

import dspy

from agent.dspy_signatures import RouterSignature
from agent.state import AgentState

# Setup logging
logger = logging.getLogger("RouterNode")

# Initialize the DSPy module once at module level
# This wraps our Signature with ChainOfThought reasoning
router_module = dspy.ChainOfThought(RouterSignature)


def route_query(state: AgentState) -> dict:
    """
    Decides the execution path (rag, sql, hybrid) for the user's question.
    """
    question = state["question"]
    logger.info(f"🤔 Routing Question: {question[:50]}...")

    try:
        pred = router_module(question=question)
        raw_classification = pred.classification

        # didn't happen when testing but just in case to not inc tokens by using pydantic
        # an update it happend
        decision = (
            raw_classification.strip()
            .lower()
            .replace(".", "")
            .replace("'", "")
            .replace('"', "")
        )

        valid_routes = ["rag", "sql", "hybrid"]
        if decision not in valid_routes:
            logger.warning(
                f"⚠️ Router produced invalid route: '{raw_classification}'. Defaulting to 'hybrid'."
            )
            decision = "hybrid"

    except Exception as e:
        logger.error(f"Router failed: {e}. Defaulting to 'hybrid'.")
        decision = "hybrid"

    logger.info(f"👉 Route Selected: {decision}")

    return {"route": decision}
