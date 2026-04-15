from pathlib import Path

from app.config import AppConfig
from app.embeddings.bkai_biencoder import BKAIBiEncoderEmbedder
from app.ingestion.json_loader import JSONDataLoader
from app.llm.advisory_generator import MockLoanAdvisoryGenerator, QwenLoanAdvisoryGenerator
from app.llm.query_rewriter import MockQueryRewriter
from app.llm.query_rewriter import QwenQueryRewriter
from app.llm.qwen_client import QwenClient
from app.preprocessing.chunk_preprocessor import VietnameseChunkPreprocessor
from app.preprocessing.query_preprocessor import VietnameseQueryPreprocessor
from app.preprocessing.segmenter import RDRSegmenterAdapter, WhitespaceFallbackSegmenter
from app.risk.loan_risk_engine import LoanRiskEngine
from app.retrieval.article_mapper import ArticleMapper
from app.retrieval.bm25_retriever import MockBM25Retriever
from app.retrieval.dense_retriever import MockDenseRetriever
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.milvus_hybrid_retriever import MilvusHybridRetriever
from app.schemas.models import LegalArticle, LegalChunk
from app.services.loan_advisory_service import LoanAdvisoryService
from app.services.loan_risk_review_service import LoanRiskReviewService
from app.vectorstores.milvus_store import MilvusVectorStore


def load_loan_advisory_payload(
    dataset_dir: str | Path = "dataset",
    customer_id: str | None = None,
) -> dict[str, object]:
    loader = JSONDataLoader()
    dataset_path = Path(dataset_dir)

    return {
        "enterprise_profile": loader.load_enterprise_profile(
            dataset_path / "enterprise_profile.json",
            customer_id=customer_id,
        ),
        "credit_score_rules": loader.load_credit_score_rules(dataset_path / "credit_score_rules.json"),
        "cic_metric_specs": loader.load_cic_metric_specs(dataset_path / "cic_metrics_spec.json"),
        "enterprise_cic_metrics": loader.load_enterprise_cic_metrics(
            dataset_path / "enterprise_cic_metrics.json",
            customer_id=customer_id,
        ),
    }


def load_risk_review_payload(
    dataset_dir: str | Path = "dataset",
) -> dict[str, object]:
    loader = JSONDataLoader()
    dataset_path = Path(dataset_dir)
    return {
        "credit_score_rules": loader.load_credit_score_rules(dataset_path / "credit_score_rules.json"),
        "cic_metric_specs": loader.load_cic_metric_specs(dataset_path / "cic_metrics_spec.json"),
    }


def build_risk_review_service() -> LoanRiskReviewService:
    return LoanRiskReviewService(risk_engine=LoanRiskEngine())


def build_demo_loan_advisory_service(
    dataset_dir: str | Path = "dataset",
) -> LoanAdvisoryService:
    config = AppConfig()
    loader = JSONDataLoader()
    dataset_path = Path(dataset_dir)
    legal_records = loader.load_legal_articles(dataset_path / "vietnamese-bank-legal.json")

    segmenter = WhitespaceFallbackSegmenter()
    chunk_preprocessor = VietnameseChunkPreprocessor(config=config, segmenter=segmenter)
    query_preprocessor = VietnameseQueryPreprocessor(config=config, segmenter=segmenter)

    chunks: list[LegalChunk] = []
    articles: list[LegalArticle] = []
    for article in legal_records:
        chunk = chunk_preprocessor.prepare_chunk(
            LegalChunk(
                chunk_id=f"{article.article_id}:chunk_1",
                article_id=article.article_id,
                text=article.content,
            )
        )
        chunks.append(chunk)
        articles.append(article.model_copy(update={"chunk_ids": [chunk.chunk_id]}))

    bm25 = MockBM25Retriever(chunks=chunks)
    dense = MockDenseRetriever(chunks=chunks)
    hybrid = HybridRetriever(
        bm25_retriever=bm25,
        dense_retriever=dense,
        weights=config.retrieval.weights,
    )
    article_mapper = ArticleMapper(articles=articles)

    return LoanAdvisoryService(
        config=config,
        query_rewriter=MockQueryRewriter(),
        query_preprocessor=query_preprocessor,
        hybrid_retriever=hybrid,
        article_mapper=article_mapper,
        risk_engine=LoanRiskEngine(),
        advisory_generator=MockLoanAdvisoryGenerator(),
    )


def build_demo_loan_advisory_pipeline(
    dataset_dir: str | Path = "dataset",
    customer_id: str | None = None,
) -> tuple[LoanAdvisoryService, dict[str, object]]:
    return (
        build_demo_loan_advisory_service(dataset_dir=dataset_dir),
        load_loan_advisory_payload(dataset_dir=dataset_dir, customer_id=customer_id),
    )


def build_production_loan_advisory_blueprint(rdr_segmenter=None) -> dict[str, object]:
    config = AppConfig()
    segmenter = RDRSegmenterAdapter(segmenter=rdr_segmenter)
    query_preprocessor = VietnameseQueryPreprocessor(config=config, segmenter=segmenter)

    llm_client = QwenClient(model_name=config.models.llm_name)
    query_rewriter = QwenQueryRewriter(llm_client=llm_client)
    advisory_generator = QwenLoanAdvisoryGenerator(llm_client=llm_client)
    risk_engine = LoanRiskEngine()

    embedder = BKAIBiEncoderEmbedder(model_name=config.models.embedding_name)
    vector_store = MilvusVectorStore(config=config.milvus)
    hybrid = MilvusHybridRetriever(
        vector_store=vector_store,
        embedder=embedder,
        weights=config.retrieval.weights,
    )

    return {
        "config": config,
        "segmenter": segmenter,
        "query_preprocessor": query_preprocessor,
        "llm_client": llm_client,
        "query_rewriter": query_rewriter,
        "advisory_generator": advisory_generator,
        "risk_engine": risk_engine,
        "embedder": embedder,
        "vector_store": vector_store,
        "hybrid_retriever": hybrid,
    }


def build_dense_milvus_loan_advisory_pipeline(
    dataset_dir: str | Path = "dataset",
    customer_id: str | None = None,
    rdr_segmenter=None,
) -> tuple[LoanAdvisoryService, dict[str, object]]:
    return (
        build_dense_milvus_loan_advisory_service(
            dataset_dir=dataset_dir,
            rdr_segmenter=rdr_segmenter,
        ),
        load_loan_advisory_payload(dataset_dir=dataset_dir, customer_id=customer_id),
    )


def build_dense_milvus_loan_advisory_service(
    dataset_dir: str | Path = "dataset",
    rdr_segmenter=None,
) -> LoanAdvisoryService:
    loader = JSONDataLoader()
    dataset_path = Path(dataset_dir)
    components = build_production_loan_advisory_blueprint(rdr_segmenter=rdr_segmenter)
    legal_articles = loader.load_legal_articles(dataset_path / "vietnamese-bank-legal.json")
    article_mapper = ArticleMapper(articles=legal_articles)

    return LoanAdvisoryService(
        config=components["config"],
        query_rewriter=components["query_rewriter"],
        query_preprocessor=components["query_preprocessor"],
        hybrid_retriever=components["hybrid_retriever"],
        article_mapper=article_mapper,
        risk_engine=components["risk_engine"],
        advisory_generator=components["advisory_generator"],
    )
