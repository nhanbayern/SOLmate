from app.schemas.models import LegalArticle, RetrievalResult


class ArticleMapper:
    def __init__(self, articles: list[LegalArticle]) -> None:
        self.article_map = {article.article_id: article for article in articles}

    def map_chunks_to_articles(self, ranked_chunks: list[RetrievalResult], top_k_articles: int) -> list[LegalArticle]:
        ordered_article_ids: list[str] = []
        seen: set[str] = set()

        for chunk in ranked_chunks:
            if chunk.article_id not in seen:
                seen.add(chunk.article_id)
                ordered_article_ids.append(chunk.article_id)

        return [self.article_map[article_id] for article_id in ordered_article_ids[:top_k_articles]]
