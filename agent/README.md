# Vietnamese Loan Risk Review

This project supports loan advisory and risk review flows for Vietnamese business loan screening.

The current flow:

1. Receive a nested payload from the client, including `enterprise_profile` and `enterprise_cic_metrics`.
2. Load reference rules from:
   - `dataset/credit_score_rules.json`
   - `dataset/cic_metrics_spec.json`
3. Evaluate the case with `LoanRiskEngine`.
4. Review whether the provided `risk_class` and `risk_probability` are reasonable.
5. Return a compact explanation with the main risk signals.


## API

Start the API:

```bash
uvicorn app.api:app --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

## Input

```json
{
  "enterprise_profile": {
    "customer_id": "CUST_25552451",
    "merchant_id": "MER_20471946",
    "name": "Tạ Gia Phúc",
    "age": 35,
    "industry": "Transportation_Service",
    "business_type": "Sole_Proprietor",
    "years_in_business": 3.795102879108812,
    "location": "Hưng Yên",
    "created_at": "2022-08-14"
  },
  "enterprise_cic_metrics": 
  {
    "credit_score": 359.71,
    "metrics": {
      "Revenue_mean_30d": 500000,
      "Revenue_mean_90d": 800413.56192567,
      "Txn_frequency": 29.042773069940303,
      "regime": "HIGH_RISK",
      "Growth_value": -0.3753229283158595,
      "Growth_score": 0.3123385358420703,
      "CV_value": 0.5974958975348206,
      "CV_score": 0,
      "Spike_ratio": 2.032744919995281,
      "Spike_score": 0.1393792333372658,
      "Txn_freq_score": 0.7743000352157346,
      "Years_score": 0.2530068586072541,
      "Industry_score": 0.3983918839203907
    },
    "risk_class": "LOW",
    "risk_probability": 0.518687260865519
  }
}
```

## Output

```json
{
  "customer_id": "CUST_25552451",
  "report_text_user": "...",
  "report_text_bank": "..."
}
```

## Notes

- The risk review path does not depend on `enterprise_cic_metrics.json`.
- The review compares the provided label/probability against:
  - the matched credit score rule
  - the severity of the CIC metrics
  - the `regime` signal when present
- The current advisory flow does not depend on legal-text retrieval.
