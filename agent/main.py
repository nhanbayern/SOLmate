import argparse
import sys

from app.report_runner import run_loan_advisory, run_risk_review_from_file


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run the loan advisory pipeline.")
    parser.add_argument(
        "--mode",
        choices=["demo", "qwen", "risk-review"],
        default="risk-review",
        help="Pipeline mode to run.",
    )
    parser.add_argument(
        "--dataset-dir",
        default="dataset",
        help="Dataset directory containing enterprise and CIC JSON files.",
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
        result = run_risk_review_from_file(
            input_file=args.input_file,
            dataset_dir=args.dataset_dir,
        )
        print(result.report_text)
        return

    result = run_loan_advisory(
        mode=args.mode,
        dataset_dir=args.dataset_dir,
        customer_id=args.customer_id,
    )

    print(result.report.report_text)


if __name__ == "__main__":
    main()
