from pathlib import Path

from app.config import AppConfig
from app.ingestion.json_loader import JSONDataLoader
from app.llm.advisory_generator import MockLoanAdvisoryGenerator, QwenLoanAdvisoryGenerator
from app.llm.qwen_client import QwenClient
from app.risk.loan_risk_engine import LoanRiskEngine
from app.services.loan_advisory_service import LoanAdvisoryService
from app.services.loan_risk_review_service import LoanRiskReviewService


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


def build_demo_loan_advisory_service() -> LoanAdvisoryService:
    return LoanAdvisoryService(
        risk_engine=LoanRiskEngine(),
        advisory_generator=MockLoanAdvisoryGenerator(),
    )


def build_demo_loan_advisory_pipeline(
    dataset_dir: str | Path = "dataset",
    customer_id: str | None = None,
) -> tuple[LoanAdvisoryService, dict[str, object]]:
    return (
        build_demo_loan_advisory_service(),
        load_loan_advisory_payload(dataset_dir=dataset_dir, customer_id=customer_id),
    )


def build_qwen_loan_advisory_service() -> LoanAdvisoryService:
    config = AppConfig()
    llm_client = QwenClient(model_name=config.models.llm_name)

    return LoanAdvisoryService(
        risk_engine=LoanRiskEngine(),
        advisory_generator=QwenLoanAdvisoryGenerator(llm_client=llm_client),
    )


def build_qwen_loan_advisory_pipeline(
    dataset_dir: str | Path = "dataset",
    customer_id: str | None = None,
) -> tuple[LoanAdvisoryService, dict[str, object]]:
    return (
        build_qwen_loan_advisory_service(),
        load_loan_advisory_payload(dataset_dir=dataset_dir, customer_id=customer_id),
    )
