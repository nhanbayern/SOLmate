from app.core.interfaces import ChunkRetriever
from app.schemas.models import LegalChunk, QueryVariant, RetrievalResult


class MockBM25Retriever(ChunkRetriever):
    def __init__(self, chunks: list[LegalChunk]) -> None:
        self.chunks = chunks

    def score_text(self, query: str, text: str) -> float:
        query_terms = set(query.lower().split())
        text_terms = text.lower().split()
        if not text_terms:
            return 0.0
        overlap = sum(1 for term in text_terms if term in query_terms)
        return overlap / len(text_terms)

    def retrieve(self, query: QueryVariant, top_k: int) -> list[RetrievalResult]:
        ranked = sorted(
            (
                RetrievalResult(
                    chunk_id=chunk.chunk_id,
                    article_id=chunk.article_id,
                    text=chunk.text,
                    bm25_score=self.score_text(query.bm25_text, chunk.bm25_text or chunk.text),
                    metadata=chunk.metadata,
                )
                for chunk in self.chunks
            ),
            key=lambda item: item.bm25_score,
            reverse=True,
        )
        return ranked[:top_k]
