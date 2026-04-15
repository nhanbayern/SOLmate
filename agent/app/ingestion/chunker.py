from app.preprocessing.chunking import LegalTextChunker
from app.schemas.models import LegalArticle, LegalChunk


class SimpleChunker:
    """Backward-compatible wrapper around the legal chunking strategy."""

    def __init__(self, legal_chunker: LegalTextChunker) -> None:
        self.legal_chunker = legal_chunker

    def split_article(self, article_id: str, text: str, chunk_size: int = 300) -> list[LegalChunk]:
        article = LegalArticle(
            article_id=article_id,
            title=article_id,
            content=text,
            metadata={"legacy_chunk_size": str(chunk_size)},
        )
        return self.legal_chunker.chunk_article(article)
