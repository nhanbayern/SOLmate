from abc import ABC, abstractmethod

from app.schemas.models import LegalChunk


class WordSegmenter(ABC):
    @abstractmethod
    def segment(self, text: str) -> str:
        raise NotImplementedError


class ChunkPreprocessor(ABC):
    @abstractmethod
    def prepare_chunk(self, chunk: LegalChunk) -> LegalChunk:
        raise NotImplementedError
