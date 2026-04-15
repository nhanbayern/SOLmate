import argparse
import sys

from app.pipeline import (
    build_demo_loan_advisory_pipeline,
    build_dense_milvus_loan_advisory_pipeline,
)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run the loan advisory pipeline.")
    parser.add_argument(
        "--mode",
        choices=["demo", "milvus-dense"],
        default="demo",
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
    args = parser.parse_args()

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
