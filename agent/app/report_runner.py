import json
from pathlib import Path
from typing import Literal

from app.pipeline import (
    build_demo_loan_advisory_service,
    build_qwen_loan_advisory_service,
    build_risk_review_service,
    load_loan_advisory_payload,
    load_risk_review_payload,
)
from app.schemas.loan_models import (
    EnterpriseCICMetrics,
    EnterpriseProfile,
    LoanAdvisoryResult,
    RiskReviewResult,
)

AdvisoryMode = Literal["demo", "qwen"]


def run_loan_advisory(
    mode: AdvisoryMode = "demo",
    dataset_dir: str | Path = "dataset",
    customer_id: str | None = None,
    service=None,
) -> LoanAdvisoryResult:
    advisory_service = service or _build_advisory_service(mode=mode)
    payload = load_loan_advisory_payload(
        dataset_dir=dataset_dir,
        customer_id=customer_id,
    )
    return advisory_service.run(
        enterprise_profile=payload["enterprise_profile"],
        credit_score_rules=payload["credit_score_rules"],
        cic_metric_specs=payload["cic_metric_specs"],
        enterprise_cic_metrics=payload["enterprise_cic_metrics"],
    )


def run_risk_review(
    payload: dict[str, object],
    dataset_dir: str | Path = "dataset",
    service=None,
) -> RiskReviewResult:
    review_payload = dict(payload)
    enterprise_profile_payload = review_payload.pop("enterprise_profile", None)
    enterprise_profile = None
    if enterprise_profile_payload is not None:
        enterprise_profile = EnterpriseProfile(**enterprise_profile_payload)

    review_service = service or build_risk_review_service()
    references = load_risk_review_payload(dataset_dir=dataset_dir)
    return review_service.run(
        credit_score_rules=references["credit_score_rules"],
        cic_metric_specs=references["cic_metric_specs"],
        enterprise_cic_metrics=EnterpriseCICMetrics(**review_payload),
        enterprise_profile=enterprise_profile,
    )


def run_risk_review_from_file(
    input_file: str | Path,
    dataset_dir: str | Path = "dataset",
    service=None,
) -> RiskReviewResult:
    payload = json.loads(Path(input_file).read_text(encoding="utf-8"))
    return run_risk_review(
        payload=payload,
        dataset_dir=dataset_dir,
        service=service,
    )


def _build_advisory_service(mode: AdvisoryMode):
    if mode == "qwen":
        return build_qwen_loan_advisory_service()
    if mode == "demo":
        return build_demo_loan_advisory_service()
    raise ValueError(f"Unsupported mode '{mode}'.")
