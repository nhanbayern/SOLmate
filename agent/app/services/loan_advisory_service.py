from app.config import AppConfig
from app.schemas.loan_models import (
    AdvisoryReport,
    CICMetricSpec,
    CreditScoreRule,
    EnterpriseCICMetrics,
    EnterpriseProfile,
    LoanAdvisoryResult,
)

#Là lớp điều phối toàn bộ pipeline. Đứng giữa để gọi đúng thành phần theo thứ tự
class LoanAdvisoryService:
    def __init__(
        self,
        config: AppConfig,
        query_rewriter,
        query_preprocessor,
        hybrid_retriever,
        article_mapper,
        risk_engine,
        advisory_generator,
    ) -> None:
        self.config = config
        self.query_rewriter = query_rewriter 
        self.query_preprocessor = query_preprocessor
        self.hybrid_retriever = hybrid_retriever
        self.article_mapper = article_mapper
        self.risk_engine = risk_engine
        self.advisory_generator = advisory_generator

    def run(
        self,
        enterprise_profile: EnterpriseProfile,
        credit_score_rules: list[CreditScoreRule],
        cic_metric_specs: list[CICMetricSpec],
        enterprise_cic_metrics: EnterpriseCICMetrics,
    ) -> LoanAdvisoryResult:
        
        risk_assessment = self.risk_engine.evaluate(
            enterprise_profile=enterprise_profile,
            credit_score_rules=credit_score_rules,
            cic_metric_specs=cic_metric_specs,
            enterprise_cic_metrics=enterprise_cic_metrics,
        )

        advisory_query = risk_assessment.advisory_query
        rewritten_query = self.query_rewriter.rewrite(advisory_query)
        query_variant = self.query_preprocessor.prepare_query(advisory_query, rewritten_query)

        retrieved_chunks = self.hybrid_retriever.retrieve(
            query_variant,
            top_k=self.config.retrieval.top_k_chunks,
        )
        legal_articles = self.article_mapper.map_chunks_to_articles(
            retrieved_chunks,
            top_k_articles=self.config.retrieval.top_k_articles,
        )

        report: AdvisoryReport = self.advisory_generator.generate(
            enterprise_profile=enterprise_profile,
            risk_assessment=risk_assessment,
            legal_articles=legal_articles,
        )

        return LoanAdvisoryResult(
            enterprise_profile=enterprise_profile,
            risk_assessment=risk_assessment,
            advisory_query=advisory_query,
            rewritten_query=rewritten_query,
            query_variant=query_variant,
            legal_references=retrieved_chunks,
            report=report,
        )
