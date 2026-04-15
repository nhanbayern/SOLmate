import argparse
import csv
import json
from pathlib import Path
from typing import Any


PROFILE_COLUMNS = (
    "customer_id",
    "merchant_id",
    "name",
    "age",
    "industry",
    "business_type",
    "years_in_business",
    "location",
    "created_at",
)

METRIC_COLUMNS = (
    "Revenue_mean_30d",
    "Revenue_mean_90d",
    "Txn_frequency", 
    "regime",
    "Growth_value",
    "Growth_score",
    "CV_value",
    "CV_score",
    "Spike_ratio",
    "Spike_score",
    "Txn_freq_score",
    "Years_score",
    "Industry_score",
)

def _parse_number(value: str) -> int | float | str:
    text = value.strip()
    if text == "":
        return ""
    try:
        number = float(text)
    except ValueError:
        return text
    if number.is_integer():
        return int(number)
    return number


def build_enterprise_profile_record(row: dict[str, str]) -> dict[str, Any]:
    return {
        "customer_id": row["customer_id"],
        "merchant_id": row["merchant_id"],
        "name": row["name"],
        "age": _parse_number(row["age"]),
        "industry": row["industry"],
        "business_type": row["business_type"],
        "years_in_business": _parse_number(row["years_in_business"]),
        "location": row["location"],
        "created_at": row["created_at"],
    }


def build_enterprise_cic_metrics_record(row: dict[str, str]) -> dict[str, Any]:
    metrics = {column: _parse_number(row[column]) for column in METRIC_COLUMNS}
    record = {
        "customer_id": row["customer_id"],
        "credit_score": float(row["CIC_SCORE"]),
        "metrics": metrics,
        "risk_class": row["label_cic_range"],
    }
    default_probability = row.get("default_probability", "").strip()
    if default_probability:
        record["risk_probability"] = float(default_probability)
    return record


def convert_csv_to_json(
    csv_path: str | Path,
    enterprise_profile_path: str | Path,
    enterprise_cic_metrics_path: str | Path,
) -> tuple[int, Path, Path]:
    csv_file = Path(csv_path)
    profile_file = Path(enterprise_profile_path)
    metrics_file = Path(enterprise_cic_metrics_path)

    with csv_file.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        profiles: list[dict[str, Any]] = []
        cic_metrics: list[dict[str, Any]] = []
        for row in reader:
            profiles.append(build_enterprise_profile_record(row))
            cic_metrics.append(build_enterprise_cic_metrics_record(row))

    profile_file.write_text(
        json.dumps(profiles, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    metrics_file.write_text(
        json.dumps(cic_metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(profiles), profile_file, metrics_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert SME customer CSV data into enterprise JSON datasets.",
    )
    parser.add_argument(
        "--csv",
        default="dataset/sme_loan_customers_30000_samples.csv",
        help="Path to the source CSV file.",
    )
    parser.add_argument(
        "--enterprise-profile",
        default="dataset/enterprise_profile.json",
        help="Path to the enterprise profile JSON output.",
    )
    parser.add_argument(
        "--enterprise-cic-metrics",
        default="dataset/enterprise_cic_metrics.json",
        help="Path to the enterprise CIC metrics JSON output.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    total_records, profile_file, metrics_file = convert_csv_to_json(
        csv_path=args.csv,
        enterprise_profile_path=args.enterprise_profile,
        enterprise_cic_metrics_path=args.enterprise_cic_metrics,
    )
    print(
        f"Converted {total_records} records to {profile_file.as_posix()} "
        f"and {metrics_file.as_posix()}."
    )


if __name__ == "__main__":
    main()
