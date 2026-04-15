from abc import ABC, abstractmethod

from app.schemas.models import LegalChunk, QueryVariant, RetrievalResult


class QueryRewriter(ABC):
    @abstractmethod
    def rewrite(self, query: str) -> str:
        raise NotImplementedError


class QueryPreprocessor(ABC):
    @abstractmethod
    def prepare_query(self, query: str, rewritten_query: str) -> QueryVariant:
        raise NotImplementedError


class ChunkRetriever(ABC):
    @abstractmethod
    def retrieve(self, query: QueryVariant, top_k: int) -> list[RetrievalResult]:
        raise NotImplementedError


class EmbeddingModel(ABC):
    @abstractmethod
    def encode(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class WordSegmenter(ABC):
    @abstractmethod
    def segment(self, text: str) -> str:
        raise NotImplementedError


class ChunkPreprocessor(ABC):
    @abstractmethod
    def prepare_chunk(self, chunk: LegalChunk) -> LegalChunk:
        raise NotImplementedError
