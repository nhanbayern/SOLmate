from functools import lru_cache
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.pipeline import (
    build_demo_loan_advisory_service,
    build_dense_milvus_loan_advisory_service,
    load_loan_advisory_payload,
)


class AdvisoryRequest(BaseModel):
    customer_id: str | None = Field(
        default=None,
        description="Customer ID to evaluate. If omitted, the first record in the dataset is used.",
    )
    mode: Literal["demo", "milvus-dense"] = Field(
        default="milvus-dense",
        description="Retrieval mode.",
    )
    dataset_dir: str = Field(
        default="dataset",
        description="Directory containing enterprise, CIC, and legal JSON files.",
    )


class AdvisoryResponse(BaseModel):
    customer_id: str
    mode: str
    report_text: str
    recommendation: str
    summary: str


def _make_service(mode: str, dataset_dir: str):
    if mode == "milvus-dense":
        return build_dense_milvus_loan_advisory_service(dataset_dir=dataset_dir)
    if mode == "demo":
        return build_demo_loan_advisory_service(dataset_dir=dataset_dir)
    raise ValueError(f"Unsupported mode '{mode}'.")


@lru_cache(maxsize=4)
def get_service(mode: str, dataset_dir: str):
    return _make_service(mode=mode, dataset_dir=dataset_dir)


app = FastAPI(
    title="Loan Advisory API",
    version="1.0.0",
    description="API for generating Vietnamese loan advisory reports.",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/advisory", response_model=AdvisoryResponse)
def generate_advisory(request: AdvisoryRequest) -> AdvisoryResponse:
    try:
        service = get_service(mode=request.mode, dataset_dir=request.dataset_dir)
        payload = load_loan_advisory_payload(
            dataset_dir=request.dataset_dir,
            customer_id=request.customer_id,
        )
        result = service.run(
            enterprise_profile=payload["enterprise_profile"],
            credit_score_rules=payload["credit_score_rules"],
            cic_metric_specs=payload["cic_metric_specs"],
            enterprise_cic_metrics=payload["enterprise_cic_metrics"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return AdvisoryResponse(
        customer_id=result.enterprise_profile.customer_id,
        mode=request.mode,
        report_text=result.report.report_text,
        recommendation=result.report.recommendation,
        summary=result.report.summary,
    )
