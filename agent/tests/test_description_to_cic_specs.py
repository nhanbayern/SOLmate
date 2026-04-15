import json
import shutil
import unittest
from pathlib import Path

from app.ingestion.description_to_cic_specs import convert_description_to_cic_specs


class DescriptionToCicSpecsTest(unittest.TestCase):
    def test_convert_description_to_cic_specs_outputs_metric_spec_json(self) -> None:
        temp_path = Path("tests/_tmp_description_to_specs")
        shutil.rmtree(temp_path, ignore_errors=True)
        temp_path.mkdir(parents=True, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(temp_path, ignore_errors=True))

        input_path = temp_path / "description.txt"
        output_path = temp_path / "cic_metrics_spec.json"

        input_path.write_text(
            "\n".join(
                [
                    "### 10. Revenue_mean_30d",
                    "- Generation: short-term revenue snapshot.",
                    "- Nature: short-term 30-day mean revenue.",
                    "",
                    "### 11. Revenue_mean_90d",
                    "- Generation: baseline revenue snapshot.",
                    "- Nature: longer-horizon baseline mean revenue.",
                    "",
                    "### 12. Txn_frequency",
                    "- By regime:",
                    "  - HIGH_RISK: uniform(5, 30)",
                    "- Nature: transaction activity signal.",
                    "",
                    "### 13. regime",
                    "- Probabilities: NORMAL 0.70, HIGH_RISK 0.15, LOW_RISK 0.15.",
                    "- Nature: latent business regime.",
                    "",
                    "### 14. Growth_value",
                    "- Formula: (Revenue_mean_30d - Revenue_mean_90d) / Revenue_mean_90d.",
                    "- Nature: growth signal.",
                    "",
                    "### 15. Growth_score",
                    "- Formula: Growth_score = (Growth_value + 1) / 2.",
                    "- Nature: normalized growth score.",
                    "",
                    "### 16. CV_value",
                    "- Generation: volatility proxy.",
                    "- Nature: core risk signal.",
                    "",
                    "### 17. CV_score",
                    "- Main formula: CV_score = 1 - min(CV_value / 0.45, 1.0).",
                    "- Nature: cash-flow stability score.",
                    "",
                    "### 18. Spike_ratio",
                    "- By regime: [1.0, 1.8].",
                    "- Nature: dependence on revenue spikes.",
                    "",
                    "### 19. Spike_score",
                    "- Formula: Spike_score = max(0, 1 - (Spike_ratio - 1.0) / 1.2).",
                    "- Nature: spike-stability score.",
                    "",
                    "### 20. Txn_freq_score",
                    "- Formula: log(1 + Txn_frequency) / log(81).",
                    "- Nature: transaction frequency score.",
                    "",
                    "### 21. Years_score",
                    "- Formula: Years_score = min(years_in_business / 15, 1.0).",
                    "- Nature: operational maturity score.",
                    "",
                    "### 22. Industry_score",
                    "- Base score by group: LOW_RISK: 0.93.",
                    "- Nature: structural industry risk score.",
                ]
            ),
            encoding="utf-8",
        )

        total_specs, _ = convert_description_to_cic_specs(input_path, output_path)

        self.assertEqual(total_specs, 13)
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(payload[0]["metrics"], "Revenue_mean_30d")
        self.assertEqual(payload[3]["metrics"], "regime")
        self.assertEqual(
            payload[3]["value"],
            "NORMAL 0.70, HIGH_RISK 0.15, LOW_RISK 0.15.",
        )
        self.assertIn("Growth_score = (Growth_value + 1) / 2.", payload[5]["note"])


if __name__ == "__main__":
    unittest.main()
