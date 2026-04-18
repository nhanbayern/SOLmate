from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    source_id: str | None = None
    section_title: str | None = None
    section_path: list[str] = Field(default_factory=list)
    token_count: int = 0
    start_token: int = 0
    end_token: int = 0
    chunk_strategy: str = "section"


class LegalChunk(BaseModel):
    chunk_id: str
    article_id: str
    text: str
    dense_text: str | None = None
    bm25_text: str | None = None
    metadata: ChunkMetadata = Field(default_factory=ChunkMetadata)


class LegalArticle(BaseModel):
    article_id: str
    title: str
    content: str
    metadata: dict[str, str] = Field(default_factory=dict)
    chunk_ids: list[str] = Field(default_factory=list)
