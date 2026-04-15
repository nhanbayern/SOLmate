from app.core.interfaces import ChunkRetriever
from app.schemas.models import LegalChunk, QueryVariant, RetrievalResult


class MockDenseRetriever(ChunkRetriever):
    def __init__(self, chunks: list[LegalChunk]) -> None:
        self.chunks = chunks

    def score_text(self, query: str, text: str) -> float:
        query_terms = set(query.lower().split())
        text_terms = set(text.lower().split())
        if not query_terms or not text_terms:
            return 0.0
        intersection = len(query_terms & text_terms)
        union = len(query_terms | text_terms)
        return intersection / union

    def retrieve(self, query: QueryVariant, top_k: int) -> list[RetrievalResult]:
        ranked = sorted(
            (
                RetrievalResult(
                    chunk_id=chunk.chunk_id,
                    article_id=chunk.article_id,
                    text=chunk.text,
                    dense_score=self.score_text(query.dense_text, chunk.dense_text or chunk.text),
                    metadata=chunk.metadata,
                )
                for chunk in self.chunks
            ),
            key=lambda item: item.dense_score,
            reverse=True,
        )
        return ranked[:top_k]
