import os

from pydantic import BaseModel, Field


class RetrievalWeights(BaseModel):
    bm25: float = 0.5
    dense: float = 0.5


class ModelConfig(BaseModel):
    llm_name: str = "Qwen/Qwen3-0.6B"
    embedding_name: str = "bkai-foundation-models/vietnamese-bi-encoder"
    embedding_max_tokens: int = 256
    llm_max_context_articles: int = 4


class PreprocessingConfig(BaseModel):
    max_tokens: int = 256
    overlap_tokens: int = 32
    query_tail_tokens: int = 256
    enable_section_chunking: bool = True
    enable_overlap_chunking: bool = True
    use_rdr_segmenter: bool = True
    remove_stopwords_for_bm25: bool = True
    preserve_stopwords_for_dense: bool = True



class AppConfig(BaseModel):
    models: ModelConfig = Field(default_factory=ModelConfig)
