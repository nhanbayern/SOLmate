from app.schemas.models import LegalArticle, LegalChunk


class CorpusIndexer:
    def build_article_map(self, articles: list[LegalArticle]) -> dict[str, LegalArticle]:
        return {article.article_id: article for article in articles}

    def build_chunk_map(self, chunks: list[LegalChunk]) -> dict[str, LegalChunk]:
        return {chunk.chunk_id: chunk for chunk in chunks}
