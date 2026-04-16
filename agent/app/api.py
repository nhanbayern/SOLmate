from functools import lru_cache
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.pipeline import build_demo_loan_advisory_service, build_qwen_loan_advisory_service
from app.report_runner import run_loan_advisory, run_risk_review
from app.schemas.loan_models import EnterpriseCICMetrics, EnterpriseProfile, RiskReviewResult


class AdvisoryRequest(BaseModel):
    customer_id: str | None = Field(
        default=None,
        description="Customer ID to evaluate. If omitted, the first record in the dataset is used.",
    )
    mode: Literal["demo", "qwen"] = Field(
        default="qwen",
        description="Advisory generation mode.",
    )
    dataset_dir: str = Field(
        default="dataset",
        description="Directory containing enterprise and CIC JSON files.",
    )


class AdvisoryResponse(BaseModel):
    customer_id: str
    mode: str
    report_text: str
    recommendation: str
    summary: str


class RiskReviewRequest(EnterpriseCICMetrics):
    dataset_dir: str = Field(
        default="dataset",
        description="Directory containing credit_score_rules.json and cic_metrics_spec.json.",
    )
    enterprise_profile: EnterpriseProfile | None = Field(
        default=None,
        description="Optional basic enterprise profile used to enrich the final report.",
    )


class RiskReviewResponse(BaseModel):
    customer_id: str
    enterprise_overview: str
    provided_risk_class: str
    expected_risk_class: str
    provided_risk_probability: float
    expected_risk_probability: float
    expected_probability_band: str
    risk_class_is_reasonable: bool
    risk_probability_is_reasonable: bool
    recommendation: str
    summary: str
    current_overview: str
    bank_advice: str
    findings: list[str]
    next_actions: list[str]
    report_text: str


class ReportTextResponse(BaseModel):
    customer_id: str
    report_text: str


def _make_service(mode: str):
    if mode == "qwen":
        return build_qwen_loan_advisory_service()
    if mode == "demo":
        return build_demo_loan_advisory_service()
    raise ValueError(f"Unsupported mode '{mode}'.")


@lru_cache(maxsize=4)
def get_service(mode: str):
    return _make_service(mode=mode)


app = FastAPI(
    title="Loan Advisory API",
    version="1.0.0",
    description="API for generating Vietnamese loan advisory reports.",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/risk-review", response_model=RiskReviewResponse)
def review_risk_input(request: RiskReviewRequest) -> RiskReviewResponse:
    try:
        result: RiskReviewResult = run_risk_review(
            payload=request.model_dump(exclude={"dataset_dir"}),
            dataset_dir=request.dataset_dir,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return RiskReviewResponse(
        customer_id=result.risk_assessment.customer_id,
        enterprise_overview=result.enterprise_overview,
        provided_risk_class=result.review.provided_risk_class,
        expected_risk_class=result.review.expected_risk_class,
        provided_risk_probability=result.review.provided_risk_probability,
        expected_risk_probability=result.review.expected_risk_probability,
        expected_probability_band=result.review.expected_probability_band,
        risk_class_is_reasonable=result.review.risk_class_is_reasonable,
        risk_probability_is_reasonable=result.review.risk_probability_is_reasonable,
        recommendation=result.review.reviewed_recommendation,
        summary=result.risk_assessment.summary,
        current_overview=result.current_overview,
        bank_advice=result.bank_advice,
        findings=result.review.findings,
        next_actions=result.next_actions,
        report_text=result.report_text,
    )


@app.post("/risk-review/report-text", response_model=ReportTextResponse)
def review_risk_input_report_text(request: RiskReviewRequest) -> ReportTextResponse:
    try:
        result: RiskReviewResult = run_risk_review(
            payload=request.model_dump(exclude={"dataset_dir"}),
            dataset_dir=request.dataset_dir,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ReportTextResponse(
        customer_id=result.risk_assessment.customer_id,
        report_text=result.report_text,
    )
