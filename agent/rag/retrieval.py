"""
Public Facade for RAG functionality.
Initializes the retrieval engine and exposes standard methods.
"""

from typing import Any, Dict, List

from .config import DOCS_DIR, validate_paths
from .engine import SearchEngine
from .loader import CorpusLoader

# Validation on import
validate_paths()

# We load the data once when this module is imported.
_chunks = CorpusLoader.load_chunks(DOCS_DIR)
_engine = SearchEngine(_chunks)


class LocalRetriever:
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        return _engine.search(query, k=k)


retriever = LocalRetriever()


def retrieve_docs(query: str, k: int = 5) -> str:
    """
    Format retrieval results as a string for the LLM context.
    """
    results = retriever.retrieve(query, k=k)
    formatted_results = []

    for res in results:
        formatted_results.append(f"Source: {res['id']}\nContent: {res['content']}")

    return "\n\n".join(formatted_results)
