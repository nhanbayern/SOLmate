from pathlib import Path

from app.ingestion.json_loader import JSONDataLoader
from app.risk.loan_risk_engine import LoanRiskEngine
from app.schemas.loan_models import EnterpriseCICMetrics
from app.services.loan_risk_review_service import LoanRiskReviewService


def test_risk_review_flags_low_label_as_unreasonable_for_high_risk_signals():
    loader = JSONDataLoader()
    dataset_dir = Path("dataset")
    credit_score_rules = loader.load_credit_score_rules(dataset_dir / "credit_score_rules.json")
    cic_metric_specs = loader.load_cic_metric_specs(dataset_dir / "cic_metrics_spec.json")

    sample = EnterpriseCICMetrics(
        customer_id="CUST_70314034",
        credit_score=342.61,
        metrics={
            "Revenue_mean_30d": 2939981.5951350383,
            "Revenue_mean_90d": 4120090.034469776,
            "Txn_frequency": 16.86872411150142,
            "regime": "HIGH_RISK",
            "Growth_value": -0.2864278279022144,
            "Growth_score": 0.3567860860488928,
            "CV_value": 0.5901900337623234,
            "CV_score": 0,
            "Spike_ratio": 2.202300634970376,
            "Spike_score": 0,
            "Txn_freq_score": 0.6560667393791124,
            "Years_score": 0.2426819015442752,
            "Industry_score": 0.7711962577582611,
        },
        risk_class="LOW",
        risk_probability=0.3584073061206929,
    )

    service = LoanRiskReviewService(risk_engine=LoanRiskEngine())
    result = service.run(
        credit_score_rules=credit_score_rules,
        cic_metric_specs=cic_metric_specs,
        enterprise_cic_metrics=sample,
    )

    assert result.review.expected_risk_class == "POOR"
    assert result.review.risk_class_is_reasonable is False
    assert result.review.risk_probability_is_reasonable is False
    assert result.risk_assessment.matched_rule.level == "POOR"
    assert result.review.reviewed_recommendation == "REJECT"
    assert "### 1. Thông Tin Cơ Bản Doanh Nghiệp" in result.report_text
    assert "### 2. Kiểm Tra Lại Phân Loại Risk Class" in result.report_text
    assert "### 4. Khuyến Nghị Cho Nhân Viên Ngân Hàng" in result.report_text
