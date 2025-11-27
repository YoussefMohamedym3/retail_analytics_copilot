import logging

from agent.rag.retrieval import retriever
from agent.state import AgentState

logger = logging.getLogger("RAGNode")


def retrieve_node(state: AgentState) -> dict:
    """
    Searches the local knowledge base for relevant document chunks.
    Updates 'retrieved_docs' in the state.
    """
    question = state["question"]
    logger.info(f"🔎 Retrieving docs for: {question[:50]}...")

    try:
        results = retriever.retrieve(question)
        logger.info(f"✅ Found {len(results)} chunks.")
    except Exception as e:
        logger.error(f"❌ Retrieval failed: {e}")
        # Return empty list on failure so graph doesn't crash
        results = []

    return {"retrieved_docs": results}
