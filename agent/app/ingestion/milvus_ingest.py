import argparse
import math
from pathlib import Path

from app.config import AppConfig
from app.embeddings.bkai_biencoder import BKAIBiEncoderEmbedder
from app.ingestion.json_loader import JSONDataLoader
from app.preprocessing.chunk_preprocessor import VietnameseChunkPreprocessor
from app.preprocessing.chunking import LegalTextChunker
from app.preprocessing.segmenter import WhitespaceFallbackSegmenter


def _build_chunk_records(dataset_path: Path, config: AppConfig) -> list[dict]:
    loader = JSONDataLoader()
    articles = loader.load_legal_articles(dataset_path)
    chunker = LegalTextChunker(config=config)
    preprocessor = VietnameseChunkPreprocessor(
        config=config,
        segmenter=WhitespaceFallbackSegmenter(),
    )

    records: list[dict] = []
    for article in articles:
        chunks = chunker.chunk_article(article)
        for chunk in chunks:
            prepared_chunk = preprocessor.prepare_chunk(chunk)
            records.append(
                {
                    "chunk_id": prepared_chunk.chunk_id,
                    "article_id": prepared_chunk.article_id,
                    "dense_text": prepared_chunk.dense_text or prepared_chunk.text,
                    "metadata": prepared_chunk.metadata.model_dump(),
                }
            )
    return records


def _attach_dense_vectors(
    records: list[dict],
    embedder: BKAIBiEncoderEmbedder,
    vector_field: str,
    batch_size: int,
) -> int:
    sample_vector: list[float] | None = None
    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        texts = [str(item["dense_text"]) for item in batch]
        vectors = embedder.encode(texts)
        for record, vector in zip(batch, vectors):
            record[vector_field] = vector
        if sample_vector is None and vectors:
            sample_vector = vectors[0]

    if not sample_vector:
        raise ValueError("No vectors were generated from the dataset.")
    return len(sample_vector)


def _ensure_database(client, db_name: str) -> None:
    if hasattr(client, "list_databases") and hasattr(client, "create_database"):
        databases = set(client.list_databases())
        if db_name not in databases:
            client.create_database(db_name)

    if hasattr(client, "using_database"):
        client.using_database(db_name)


def _create_collection(
    client,
    config: AppConfig,
    dim: int,
    drop_existing: bool,
) -> None:
    from pymilvus import DataType

    collection_name = config.milvus.collection_name

    if client.has_collection(collection_name=collection_name):
        if not drop_existing:
            raise ValueError(
                f"Collection '{collection_name}' already exists. "
                "Use --drop-existing to recreate it."
            )
        client.drop_collection(collection_name=collection_name)

    schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field(
        field_name="chunk_id",
        datatype=DataType.VARCHAR,
        is_primary=True,
        max_length=512,
    )
    schema.add_field(
        field_name="article_id",
        datatype=DataType.VARCHAR,
        max_length=512,
    )
    schema.add_field(
        field_name=config.milvus.text_field,
        datatype=DataType.VARCHAR,
        max_length=65535,
    )
    schema.add_field(
        field_name=config.milvus.vector_field,
        datatype=DataType.FLOAT_VECTOR,
        dim=dim,
    )
    schema.add_field(
        field_name=config.milvus.metadata_field,
        datatype=DataType.JSON,
    )

    index_params = client.prepare_index_params()
    dense_index_kwargs = {
        "field_name": config.milvus.vector_field,
        "index_type": config.milvus.index_type,
        "metric_type": config.milvus.metric_type,
    }
    if config.milvus.index_type.upper() == "HNSW":
        dense_index_kwargs["params"] = {"M": 16, "efConstruction": 200}
    index_params.add_index(**dense_index_kwargs)

    client.create_collection(
        collection_name=collection_name,
        schema=schema,
        index_params=index_params,
    )


def _insert_in_batches(client, collection_name: str, records: list[dict], batch_size: int) -> None:
    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        client.insert(collection_name=collection_name, data=batch)


def ingest_legal_json(
    dataset_path: Path,
    batch_size: int = 32,
    drop_existing: bool = False,
) -> None:
    try:
        from pymilvus import MilvusClient
    except ImportError as exc:
        raise ImportError(
            "pymilvus is required. Install dependencies with `pip install -r requirements.txt`."
        ) from exc

    config = AppConfig()
    records = _build_chunk_records(dataset_path, config)
    if not records:
        raise ValueError(f"No legal chunks were produced from '{dataset_path}'.")

    embedder = BKAIBiEncoderEmbedder(model_name=config.models.embedding_name)
    dim = _attach_dense_vectors(
        records=records,
        embedder=embedder,
        vector_field=config.milvus.vector_field,
        batch_size=batch_size,
    )

    client = MilvusClient(uri=config.milvus.uri, token=config.milvus.token)
    _ensure_database(client, config.milvus.database)
    _create_collection(
        client,
        config=config,
        dim=dim,
        drop_existing=drop_existing,
    )
    _insert_in_batches(
        client,
        collection_name=config.milvus.collection_name,
        records=records,
        batch_size=batch_size,
    )

    total_batches = math.ceil(len(records) / batch_size)
    print(f"Inserted {len(records)} chunks into Milvus collection '{config.milvus.collection_name}'.")
    print(f"Database: {config.milvus.database}")
    print(f"Batches: {total_batches}")
    print(f"Vector dimension: {dim}")
    print("Mode: dense-only")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest dataset/vietnamese-bank-legal.json into Milvus for dense-only RAG."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("dataset") / "vietnamese-bank-legal.json",
        help="Path to the legal JSON dataset.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Embedding and insert batch size.",
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop the existing collection before recreating it.",
    )
    args = parser.parse_args()

    ingest_legal_json(
        dataset_path=args.dataset,
        batch_size=args.batch_size,
        drop_existing=args.drop_existing,
    )


if __name__ == "__main__":
    main()
