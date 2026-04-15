from app.schemas.loan_models import (
    CICMetricSpec,
    CreditScoreRule,
    EnterpriseCICMetrics,
    EnterpriseProfile,
    RiskReviewResult,
)


class LoanRiskReviewService:
    def __init__(self, risk_engine) -> None:
        self.risk_engine = risk_engine

    def run(
        self,
        credit_score_rules: list[CreditScoreRule],
        cic_metric_specs: list[CICMetricSpec],
        enterprise_cic_metrics: EnterpriseCICMetrics,
    ) -> RiskReviewResult:
        enterprise_profile = EnterpriseProfile(
            customer_id=enterprise_cic_metrics.customer_id,
            years_in_business=0,
        )
        risk_assessment = self.risk_engine.evaluate(
            enterprise_profile=enterprise_profile,
            credit_score_rules=credit_score_rules,
            cic_metric_specs=cic_metric_specs,
            enterprise_cic_metrics=enterprise_cic_metrics,
        )
        review = self.risk_engine.review_reasonableness(
            credit_score_rules=credit_score_rules,
            enterprise_cic_metrics=enterprise_cic_metrics,
            risk_assessment=risk_assessment,
        )
        report_text = self._compose_report_text(result=risk_assessment, review=review)
        return RiskReviewResult(
            risk_assessment=risk_assessment,
            review=review,
            report_text=report_text,
        )

    def _compose_report_text(self, result, review) -> str:
        class_judgement = "hop ly" if review.risk_class_is_reasonable else "chua hop ly"
        probability_judgement = "hop ly" if review.risk_probability_is_reasonable else "chua hop ly"
        top_factors = ", ".join(factor.name for factor in result.top_risk_factors[:4]) or "khong co"
        findings = "\n- ".join(review.findings)

        return (
            f"Ket luan nhanh: nhan rui ro {review.provided_risk_class} la {class_judgement}; "
            f"xac suat {review.provided_risk_probability:.4f} la {probability_judgement}.\n\n"
            f"Rule khop voi credit score: {result.matched_rule.level} ({result.matched_rule.decision}).\n"
            f"Risk class ky vong theo rule + metric: {review.expected_risk_class}.\n"
            f"Xac suat ky vong xap xi: {review.expected_risk_probability:.4f} "
            f"(vung {review.expected_probability_band}).\n"
            f"Cac metric rui ro noi bat: {top_factors}.\n"
            f"Recommendation theo engine: {result.recommendation}.\n\n"
            f"Nhan dinh chi tiet:\n- {findings}"
        )
