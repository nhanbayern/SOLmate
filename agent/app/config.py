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


class MilvusConfig(BaseModel):
    uri: str = Field(default_factory=lambda: os.getenv("MILVUS_URI", "http://localhost:19530"))
    token: str | None = Field(default_factory=lambda: os.getenv("MILVUS_TOKEN"))
    database: str = Field(default_factory=lambda: os.getenv("MILVUS_DB_NAME", "legal_rag"))
    collection_name: str = Field(default_factory=lambda: os.getenv("MILVUS_COLLECTION_NAME", "legal_chunks"))
    vector_field: str = Field(default_factory=lambda: os.getenv("MILVUS_VECTOR_FIELD", "dense_vector"))
    sparse_field: str = Field(default_factory=lambda: os.getenv("MILVUS_SPARSE_FIELD", "sparse_vector"))
    text_field: str = Field(default_factory=lambda: os.getenv("MILVUS_TEXT_FIELD", "dense_text"))
    metadata_field: str = Field(default_factory=lambda: os.getenv("MILVUS_METADATA_FIELD", "metadata"))
    metric_type: str = Field(default_factory=lambda: os.getenv("MILVUS_METRIC_TYPE", "COSINE"))
    index_type: str = Field(default_factory=lambda: os.getenv("MILVUS_INDEX_TYPE", "HNSW"))


class PreprocessingConfig(BaseModel):
    max_tokens: int = 256
    overlap_tokens: int = 32
    query_tail_tokens: int = 256
    enable_section_chunking: bool = True
    enable_overlap_chunking: bool = True
    use_rdr_segmenter: bool = True
    remove_stopwords_for_bm25: bool = True
    preserve_stopwords_for_dense: bool = True


class RetrievalConfig(BaseModel):
    top_k_chunks: int = 8
    top_k_articles: int = 3
    max_active_rounds: int = 2
    article_batch_size: int = 2
    weights: RetrievalWeights = Field(default_factory=RetrievalWeights)


class AppConfig(BaseModel):
    models: ModelConfig = Field(default_factory=ModelConfig)
    milvus: MilvusConfig = Field(default_factory=MilvusConfig)
    preprocessing: PreprocessingConfig = Field(default_factory=PreprocessingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
