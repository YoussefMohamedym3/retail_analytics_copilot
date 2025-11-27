from typing import Any, Dict, List

from rank_bm25 import BM25Okapi

from .loader import CorpusLoader
from .schema import DocumentChunk


class SearchEngine:
    def __init__(self, chunks: List[DocumentChunk]):
        self.chunks = chunks
        self.bm25 = self._build_index()

    def _build_index(self) -> BM25Okapi:
        """
        Builds the BM25 index from the loaded chunks.
        """
        tokenized_corpus = [
            CorpusLoader.clean_tokenize(chunk.content) for chunk in self.chunks
        ]
        return BM25Okapi(tokenized_corpus)

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Returns top-k chunks sorted by relevance score.
        Returns Dicts to ensure compatibility with existing evaluation scripts.
        """
        query_tokens = CorpusLoader.clean_tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        scored_results = []
        for chunk, score in zip(self.chunks, scores):
            # Create a copy to avoid mutating the original index
            result_dict = chunk.model_dump(by_alias=True)
            result_dict["score"] = float(score)  # Ensure native float
            scored_results.append(result_dict)

        # Sort by score descending
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:k]
