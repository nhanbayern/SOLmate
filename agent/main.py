import argparse
import json
import sys
from pathlib import Path

from app.pipeline import (
    build_demo_loan_advisory_pipeline,
    build_dense_milvus_loan_advisory_pipeline,
    build_risk_review_service,
    load_risk_review_payload,
)
from app.schemas.loan_models import EnterpriseCICMetrics


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run the loan advisory pipeline.")
    parser.add_argument(
        "--mode",
        choices=["demo", "milvus-dense", "risk-review"],
        default="risk-review",
        help="Pipeline mode to run.",
    )
    parser.add_argument(
        "--dataset-dir",
        default="dataset",
        help="Dataset directory containing enterprise and legal JSON files.",
    )
    parser.add_argument(
        "--customer-id",
        default=None,
        help="Optional customer_id to select a specific enterprise record.",
    )
    parser.add_argument(
        "--input-file",
        default=None,
        help="JSON file containing a direct EnterpriseCICMetrics payload for risk-review mode.",
    )
    args = parser.parse_args()

    if args.mode == "risk-review":
        if not args.input_file:
            raise ValueError("--input-file is required when --mode risk-review.")
        payload = json.loads(Path(args.input_file).read_text(encoding="utf-8"))
        service = build_risk_review_service()
        references = load_risk_review_payload(dataset_dir=args.dataset_dir)
        result = service.run(
            credit_score_rules=references["credit_score_rules"],
            cic_metric_specs=references["cic_metric_specs"],
            enterprise_cic_metrics=EnterpriseCICMetrics(**payload),
        )
        print(result.report_text)
        return

    if args.mode == "milvus-dense":
        service, payload = build_dense_milvus_loan_advisory_pipeline(
            dataset_dir=args.dataset_dir,
            customer_id=args.customer_id,
        )
    else:
        service, payload = build_demo_loan_advisory_pipeline(
            dataset_dir=args.dataset_dir,
            customer_id=args.customer_id,
        )

    result = service.run(
        enterprise_profile=payload["enterprise_profile"],
        credit_score_rules=payload["credit_score_rules"],
        cic_metric_specs=payload["cic_metric_specs"],
        enterprise_cic_metrics=payload["enterprise_cic_metrics"],
    )

    print(result.report.report_text)


if __name__ == "__main__":
    main()
