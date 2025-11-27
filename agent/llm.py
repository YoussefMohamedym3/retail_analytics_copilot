import logging
import os

import dspy

# Setup professional logging (consistent with agent/rag/config.py)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("LLM")


def init_dspy():
    """
    Initializes and configures the global DSPy Language Model client.

    This function connects to a local Ollama instance running the
    Phi-3.5-mini-instruct model. It sets the temperature to 0.0 for
    deterministic outputs and configures a large context window (8192)
    to handle RAG context and database schemas.

    Returns:
        dspy.LM: The configured language model instance.
    """
    model_name = "ollama/phi3.5:3.8b-mini-instruct-q4_K_M"

    logger.info(f"🔌 Connecting to local Ollama model: {model_name}...")

    lm = dspy.LM(
        model=model_name,
        api_base="http://localhost:11434",
        temperature=0.0,
        num_ctx=8192,
    )

    dspy.configure(lm=lm)

    return lm
