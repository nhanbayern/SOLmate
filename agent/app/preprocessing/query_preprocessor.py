from app.config import AppConfig
from app.core.interfaces import QueryPreprocessor, WordSegmenter
from app.preprocessing.stopwords import remove_stopwords
from app.schemas.models import QueryVariant


class VietnameseQueryPreprocessor(QueryPreprocessor):
    def __init__(self, config: AppConfig, segmenter: WordSegmenter) -> None:
        self.config = config
        self.segmenter = segmenter

    def prepare_query(self, query: str, rewritten_query: str) -> QueryVariant:
        segmented = self.segmenter.segment(rewritten_query)
        retrieval_units = self._build_retrieval_units(segmented)

        dense_text = self._trim_to_tail(segmented, self.config.preprocessing.query_tail_tokens)
        bm25_text = dense_text
        if self.config.preprocessing.remove_stopwords_for_bm25:
            bm25_text = remove_stopwords(dense_text)

        return QueryVariant(
            original_text=query,
            rewritten_text=rewritten_query,
            segmented_text=segmented,
            bm25_text=bm25_text,
            dense_text=dense_text,
            retrieval_units=retrieval_units,
        )

    def _trim_to_tail(self, text: str, max_tokens: int) -> str:
        tokens = text.split()
        if len(tokens) <= max_tokens:
            return text
        return " ".join(tokens[-max_tokens:])

    def _build_retrieval_units(self, text: str) -> list[str]:
        tokens = text.split()
        max_tokens = self.config.preprocessing.max_tokens
        if len(tokens) <= max_tokens:
            return [text]

        units: list[str] = []
        for start in range(0, len(tokens), max_tokens):
            units.append(" ".join(tokens[start : start + max_tokens]))

        return units
