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
        risk_engine,
        advisory_generator,
    ) -> None:
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

        report: AdvisoryReport = self.advisory_generator.generate(
            enterprise_profile=enterprise_profile,
            risk_assessment=risk_assessment,
        )

        return LoanAdvisoryResult(
            enterprise_profile=enterprise_profile,
            risk_assessment=risk_assessment,
            report=report,
        )
