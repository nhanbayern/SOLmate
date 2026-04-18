from app.config import AppConfig
from app.core.interfaces import ChunkPreprocessor, WordSegmenter
from app.preprocessing.stopwords import remove_stopwords
from app.schemas.models import LegalChunk


class VietnameseChunkPreprocessor(ChunkPreprocessor):
    def __init__(self, config: AppConfig, segmenter: WordSegmenter) -> None:
        self.config = config
        self.segmenter = segmenter

    def prepare_chunk(self, chunk: LegalChunk) -> LegalChunk:
        segmented = self.segmenter.segment(chunk.text)
        bm25_text = segmented
        if self.config.preprocessing.remove_stopwords_for_bm25:
            bm25_text = remove_stopwords(segmented)

        dense_text = segmented
        return chunk.model_copy(
            update={
                "bm25_text": bm25_text,
                "dense_text": dense_text,
            }
        )
