import json

from app.schemas.loan_models import EnterpriseCICMetrics, EnterpriseProfile


def build_loan_model_input_payload(
    enterprise_profile: EnterpriseProfile,
    enterprise_cic_metrics: EnterpriseCICMetrics,
) -> dict[str, object]:
    payload = enterprise_profile.model_dump()
    payload.update(
        {
            "credit_score": enterprise_cic_metrics.credit_score,
            "metrics": enterprise_cic_metrics.metrics,
            "risk_class": enterprise_cic_metrics.risk_class,
            "risk_probability": enterprise_cic_metrics.risk_probability,
        }
    )
    return payload


def build_loan_model_input_json(
    enterprise_profile: EnterpriseProfile,
    enterprise_cic_metrics: EnterpriseCICMetrics,
) -> str:
    return json.dumps(
        build_loan_model_input_payload(
            enterprise_profile=enterprise_profile,
            enterprise_cic_metrics=enterprise_cic_metrics,
        ),
        ensure_ascii=False,
        indent=2,
    )
