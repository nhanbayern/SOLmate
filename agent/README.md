# Vietnamese Loan Risk Review

This project supports loan advisory and risk review flows for Vietnamese business loan screening.

The current flow:

1. Receive a direct `EnterpriseCICMetrics` payload from the client.
2. Load reference rules from:
   - `dataset/credit_score_rules.json`
   - `dataset/cic_metrics_spec.json`
3. Evaluate the case with `LoanRiskEngine`.
4. Review whether the provided `risk_class` and `risk_probability` are reasonable.
5. Return a compact explanation with the main risk signals.

## Input shape

The API accepts a payload like this:

```json
{
  "customer_id": "CUST_70314034",
  "credit_score": 342.61,
  "metrics": {
    "Revenue_mean_30d": 2939981.5951350383,
    "Revenue_mean_90d": 4120090.034469776,
    "Txn_frequency": 16.86872411150142,
    "regime": "HIGH_RISK",
    "Growth_value": -0.2864278279022144,
    "Growth_score": 0.3567860860488928,
    "CV_value": 0.5901900337623234,
    "CV_score": 0,
    "Spike_ratio": 2.202300634970376,
    "Spike_score": 0,
    "Txn_freq_score": 0.6560667393791124,
    "Years_score": 0.2426819015442752,
    "Industry_score": 0.7711962577582611
  },
  "risk_class": "LOW",
  "risk_probability": 0.3584073061206929
}
```

You can optionally include:

```json
{
  "dataset_dir": "dataset"
}
```

## API

Start the API:

```bash
uvicorn app.api:app --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Risk review:

```bash
curl -X POST http://localhost:8000/risk-review \
  -H "Content-Type: application/json" \
  -d "{\"customer_id\":\"CUST_70314034\",\"credit_score\":342.61,\"metrics\":{\"Revenue_mean_30d\":2939981.5951350383,\"Revenue_mean_90d\":4120090.034469776,\"Txn_frequency\":16.86872411150142,\"regime\":\"HIGH_RISK\",\"Growth_value\":-0.2864278279022144,\"Growth_score\":0.3567860860488928,\"CV_value\":0.5901900337623234,\"CV_score\":0,\"Spike_ratio\":2.202300634970376,\"Spike_score\":0,\"Txn_freq_score\":0.6560667393791124,\"Years_score\":0.2426819015442752,\"Industry_score\":0.7711962577582611},\"risk_class\":\"LOW\",\"risk_probability\":0.3584073061206929}"
```

Example response shape:

```json
{
  "customer_id": "CUST_70314034",
  "provided_risk_class": "LOW",
  "expected_risk_class": "POOR",
  "provided_risk_probability": 0.3584,
  "expected_risk_probability": 0.8045,
  "expected_probability_band": "0.60-0.85",
  "risk_class_is_reasonable": false,
  "risk_probability_is_reasonable": false,
  "recommendation": "MANUAL_REVIEW",
  "summary": "...",
  "findings": ["..."],
  "report_text": "..."
}
```

Get only `report_text_user` and `report_text_bank` from risk review:

```bash
curl -X POST http://localhost:8000/risk-review/report-text \
  -H "Content-Type: application/json" \
  -d "{\"customer_id\":\"CUST_70314034\",\"credit_score\":342.61,\"metrics\":{\"Revenue_mean_30d\":2939981.5951350383,\"Revenue_mean_90d\":4120090.034469776,\"Txn_frequency\":16.86872411150142,\"regime\":\"HIGH_RISK\",\"Growth_value\":-0.2864278279022144,\"Growth_score\":0.3567860860488928,\"CV_value\":0.5901900337623234,\"CV_score\":0,\"Spike_ratio\":2.202300634970376,\"Spike_score\":0,\"Txn_freq_score\":0.6560667393791124,\"Years_score\":0.2426819015442752,\"Industry_score\":0.7711962577582611},\"risk_class\":\"LOW\",\"risk_probability\":0.3584073061206929}"
```

Example response shape:

```json
{
  "customer_id": "CUST_70314034",
  "report_text_user": "...",
  "report_text_bank": "..."
}
```

Get only `report_text` from advisory:

```bash
curl -X POST http://localhost:8000/advisory/report-text \
  -H "Content-Type: application/json" \
  -d "{\"mode\":\"demo\",\"customer_id\":\"CUST_70314034\",\"dataset_dir\":\"dataset\"}"
```

## CLI

Run the same review from the command line:

```bash
python main.py --mode risk-review --input-file sample.json
```

Where `sample.json` contains the same direct CIC payload as above.

## Notes

- The risk review path does not depend on `enterprise_cic_metrics.json`.
- The review compares the provided label/probability against:
  - the matched credit score rule
  - the severity of the CIC metrics
  - the `regime` signal when present
- The current advisory flow does not depend on legal-text retrieval.
