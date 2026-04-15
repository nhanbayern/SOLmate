import csv
import json
import shutil
import unittest
from pathlib import Path

from app.ingestion.csv_to_enterprise_json import convert_csv_to_json


class CsvToEnterpriseJsonTest(unittest.TestCase):
    def test_convert_csv_to_json_outputs_expected_structure(self) -> None:
        temp_path = Path("tests/_tmp_csv_to_json")
        shutil.rmtree(temp_path, ignore_errors=True)
        temp_path.mkdir(parents=True, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(temp_path, ignore_errors=True))

        csv_path = temp_path / "sample.csv"
        profile_path = temp_path / "enterprise_profile.json"
        metrics_path = temp_path / "enterprise_cic_metrics.json"

        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "customer_id",
                    "merchant_id",
                    "name",
                    "age",
                    "industry",
                    "business_type",
                    "years_in_business",
                    "location",
                    "created_at",
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
                    "CIC_SCORE",
                    "label",
                    "label_quantile",
                    "label_cic_range",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "customer_id": "CUST_1",
                    "merchant_id": "MER_1",
                    "name": "Nguyen Van A",
                    "age": "35",
                    "industry": "Retail",
                    "business_type": "Micro_SME",
                    "years_in_business": "5.5",
                    "location": "Ha Noi",
                    "created_at": "2024-01-01",
                    "Revenue_mean_30d": "12345.6",
                    "Revenue_mean_90d": "34567.8",
                    "Txn_frequency": "18",
                    "regime": "NORMAL",
                    "Growth_value": "0.25",
                    "Growth_score": "0.7",
                    "CV_value": "0.4",
                    "CV_score": "0.8",
                    "Spike_ratio": "1.2",
                    "Spike_score": "0.3",
                    "Txn_freq_score": "0.9",
                    "Years_score": "0.6",
                    "Industry_score": "0.5",
                    "CIC_SCORE": "512.25",
                    "label": "MEDIUM",
                    "label_quantile": "MEDIUM",
                    "label_cic_range": "MEDIUM",
                }
            )

        total_records, _, _ = convert_csv_to_json(csv_path, profile_path, metrics_path)

        self.assertEqual(total_records, 1)

        profiles = json.loads(profile_path.read_text(encoding="utf-8"))
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

        self.assertEqual(
            profiles,
            [
                {
                    "customer_id": "CUST_1",
                    "merchant_id": "MER_1",
                    "name": "Nguyen Van A",
                    "age": 35,
                    "industry": "Retail",
                    "business_type": "Micro_SME",
                    "years_in_business": 5.5,
                    "location": "Ha Noi",
                    "created_at": "2024-01-01",
                }
            ],
        )
        self.assertEqual(
            metrics,
            [
                {
                    "customer_id": "CUST_1",
                    "credit_score": 512.25,
                    "metrics": {
                        "Revenue_mean_30d": 12345.6,
                        "Revenue_mean_90d": 34567.8,
                        "Txn_frequency": 18,
                        "regime": "NORMAL",
                        "Growth_value": 0.25,
                        "Growth_score": 0.7,
                        "CV_value": 0.4,
                        "CV_score": 0.8,
                        "Spike_ratio": 1.2,
                        "Spike_score": 0.3,
                        "Txn_freq_score": 0.9,
                        "Years_score": 0.6,
                        "Industry_score": 0.5,
                    },
                    "risk_class": "MEDIUM",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
