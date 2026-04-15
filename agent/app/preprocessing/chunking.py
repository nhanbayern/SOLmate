import re

from app.config import AppConfig
from app.schemas.models import ChunkMetadata, LegalArticle, LegalChunk


class LegalTextChunker:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def chunk_article(self, article: LegalArticle) -> list[LegalChunk]:
        if self.config.preprocessing.enable_section_chunking:
            section_chunks = self._chunk_by_sections(article)
            if section_chunks:
                return section_chunks

        if self.config.preprocessing.enable_overlap_chunking:
            return self._chunk_with_overlap(article)

        return [
            LegalChunk(
                chunk_id=f"{article.article_id}_chunk_1",
                article_id=article.article_id,
                text=article.content,
            )
        ]

    def _chunk_by_sections(self, article: LegalArticle) -> list[LegalChunk]:
        pattern = re.compile(r"(?=Dieu\s+\d+|Khoan\s+\d+|Muc\s+\d+)", re.IGNORECASE)
        sections = [section.strip() for section in pattern.split(article.content) if section.strip()]
        if len(sections) <= 1:
            return []

        chunks: list[LegalChunk] = []
        for index, section_text in enumerate(sections, start=1):
            token_count = len(section_text.split())
            if token_count > self.config.preprocessing.max_tokens:
                return []

            chunks.append(
                LegalChunk(
                    chunk_id=f"{article.article_id}_section_{index}",
                    article_id=article.article_id,
                    text=section_text,
                    metadata=ChunkMetadata(
                        source_id=article.article_id,
                        token_count=token_count,
                        start_token=0,
                        end_token=token_count,
                        chunk_strategy="section",
                    ),
                )
            )

        return chunks

    def _chunk_with_overlap(self, article: LegalArticle) -> list[LegalChunk]:
        words = article.content.split()
        max_tokens = self.config.preprocessing.max_tokens
        overlap = self.config.preprocessing.overlap_tokens
        step = max(max_tokens - overlap, 1)

        chunks: list[LegalChunk] = []
        for start in range(0, len(words), step):
            window = words[start : start + max_tokens]
            if not window:
                continue

            end = start + len(window)
            chunks.append(
                LegalChunk(
                    chunk_id=f"{article.article_id}_chunk_{len(chunks) + 1}",
                    article_id=article.article_id,
                    text=" ".join(window),
                    metadata=ChunkMetadata(
                        source_id=article.article_id,
                        token_count=len(window),
                        start_token=start,
                        end_token=end,
                        chunk_strategy="overlap",
                    ),
                )
            )

            if end >= len(words):
                break

        return chunks
