from app.schemas.loan_models import (
    CICMetricSpec,
    CreditScoreRule,
    EnterpriseCICMetrics,
    EnterpriseProfile,
    RiskAssessmentResult,
    RiskFactor,
    RiskReasonablenessReview,
)


class LoanRiskEngine:
    def evaluate(
        self,
        enterprise_profile: EnterpriseProfile,
        credit_score_rules: list[CreditScoreRule],
        cic_metric_specs: list[CICMetricSpec],
        enterprise_cic_metrics: EnterpriseCICMetrics,
    ) -> RiskAssessmentResult:
        normalized_risk_class = self._normalize_risk_class(enterprise_cic_metrics.risk_class)
        matched_rule = self._match_credit_rule(
            enterprise_cic_metrics.credit_score,
            credit_score_rules,
        )
        metric_insights = self._build_metric_insights(
            enterprise_cic_metrics.metrics,
            cic_metric_specs,
        )
        risk_probability = self._derive_risk_probability(
            normalized_risk_class,
            enterprise_cic_metrics.risk_probability,
        )
        top_risk_factors = self._derive_top_risk_factors(
            enterprise_cic_metrics=enterprise_cic_metrics,
            metric_insights=metric_insights,
        )
        recommendation = self._decide_recommendation(
            matched_rule=matched_rule,
            risk_class=normalized_risk_class,
            risk_probability=risk_probability,
        )
        summary = (
            f"Doanh nghiep {enterprise_profile.customer_id} hoat dong trong nganh "
            f"{enterprise_profile.industry or 'chua ro'}, credit score "
            f"{enterprise_cic_metrics.credit_score:.2f}, thuoc muc {matched_rule.level}, "
            f"rui ro mo hinh {normalized_risk_class} ({risk_probability:.2f})."
        )
        advisory_query = self._build_advisory_query(
            enterprise_profile=enterprise_profile,
            matched_rule=matched_rule,
            risk_class=normalized_risk_class,
            metric_insights=metric_insights,
            top_risk_factors=top_risk_factors,
        )

        return RiskAssessmentResult(
            customer_id=enterprise_profile.customer_id,
            credit_score=enterprise_cic_metrics.credit_score,
            matched_rule=matched_rule,
            risk_class=normalized_risk_class,
            risk_probability=risk_probability,
            recommendation=recommendation,
            summary=summary,
            metric_insights=metric_insights,
            top_risk_factors=top_risk_factors,
            advisory_query=advisory_query,
        )

    def review_reasonableness(
        self,
        credit_score_rules: list[CreditScoreRule],
        enterprise_cic_metrics: EnterpriseCICMetrics,
        risk_assessment: RiskAssessmentResult,
    ) -> RiskReasonablenessReview:
        provided_risk_class = self._normalize_risk_class(enterprise_cic_metrics.risk_class)
        regime = str(enterprise_cic_metrics.metrics.get("regime", "")).upper().strip()
        top_severities = sorted(
            [
                self._metric_severity(metric_name, metric_value)
                for metric_name, metric_value in enterprise_cic_metrics.metrics.items()
                if self._metric_severity(metric_name, metric_value) > 0
            ],
            reverse=True,
        )[:5]

        if regime == "HIGH_RISK":
            top_severities.append(1.0)
        elif regime == "NORMAL":
            top_severities.append(0.4)
        elif regime == "LOW_RISK":
            top_severities.append(0.0)

        metric_signal = (sum(top_severities) / len(top_severities)) if top_severities else 0.0
        matched_rule = self._match_credit_rule(
            enterprise_cic_metrics.credit_score,
            credit_score_rules,
        )
        credit_anchor = self._credit_rule_probability_anchor(matched_rule.level)
        metric_anchor = 0.15 + (0.75 * metric_signal)

        if regime == "HIGH_RISK":
            metric_anchor = max(metric_anchor, 0.75)
        elif regime == "LOW_RISK":
            metric_anchor = min(metric_anchor, 0.35)

        expected_probability = round((0.65 * credit_anchor) + (0.35 * metric_anchor), 4)
        expected_risk_class = self._probability_to_risk_class(expected_probability)
        probability_band = self._probability_band(expected_risk_class)
        probability_is_reasonable = (
            probability_band[0] <= enterprise_cic_metrics.risk_probability <= probability_band[1]
        )

        findings = [
            (
                f"Credit score {enterprise_cic_metrics.credit_score:.2f} nam trong rule "
                f"{matched_rule.level} ({matched_rule.decision})."
            )
        ]
        if regime:
            findings.append(f"Metric 'regime' dang o muc {regime}.")

        for factor in risk_assessment.top_risk_factors[:4]:
            findings.append(f"{factor.name}={factor.value}: {factor.note}")

        if provided_risk_class != expected_risk_class:
            findings.append(
                f"Nhan dau vao la {provided_risk_class} nhung tong hop tin hieu nghieng ve {expected_risk_class}."
            )
        if not probability_is_reasonable:
            findings.append(
                f"Xac suat {enterprise_cic_metrics.risk_probability:.4f} lech vung ky vong "
                f"{probability_band[0]:.2f}-{probability_band[1]:.2f}."
            )

        return RiskReasonablenessReview(
            provided_risk_class=provided_risk_class,
            expected_risk_class=expected_risk_class,
            provided_risk_probability=round(enterprise_cic_metrics.risk_probability, 4),
            expected_risk_probability=expected_probability,
            expected_probability_band=self._format_probability_band(probability_band),
            risk_class_is_reasonable=provided_risk_class == expected_risk_class,
            risk_probability_is_reasonable=probability_is_reasonable,
            findings=findings,
        )

    def _normalize_risk_class(self, risk_class: str) -> str:
        normalized = risk_class.upper().strip()
        if normalized.endswith("_RISK"):
            normalized = normalized.removesuffix("_RISK")
        if normalized == "AVERAGE":
            return "MEDIUM"
        return normalized

    def _derive_risk_probability(
        self,
        risk_class: str,
        provided_probability: float,
    ) -> float:
        if provided_probability > 0:
            return provided_probability

        fallback_map = {
            "VERY_GOOD": 0.15,
            "VERY_LOW": 0.18,
            "GOOD": 0.28,
            "LOW": 0.32,
            "MEDIUM": 0.55,
            "POOR": 0.78,
            "VERY_POOR": 0.92,
        }
        return fallback_map.get(risk_class, 0.50)

    def _match_credit_rule(
        self,
        credit_score: float,
        credit_score_rules: list[CreditScoreRule],
    ) -> CreditScoreRule:
        for rule in credit_score_rules:
            if rule.min_score <= credit_score <= rule.max_score:
                return rule

        return CreditScoreRule(
            min_score=0,
            max_score=0,
            level="UNKNOWN",
            risk="UNKNOWN",
            decision="REVIEW_REQUIRED",
            note="Credit score does not match any configured rule.",
        )

    def _build_metric_insights(
        self,
        metrics: dict[str, str | float],
        cic_metric_specs: list[CICMetricSpec],
    ) -> list[RiskFactor]:
        spec_map = {item.metrics: item for item in cic_metric_specs}
        insights: list[RiskFactor] = []
        for metric_name, metric_value in metrics.items():
            spec = spec_map.get(metric_name)
            note = "Khong co mo ta metrics."
            if spec is not None:
                note_parts = [part for part in [spec.note, spec.value] if part]
                note = " ".join(note_parts).strip()
            insights.append(
                RiskFactor(
                    name=metric_name,
                    value=str(metric_value),
                    note=note,
                )
            )

        return insights

    def _derive_top_risk_factors(
        self,
        enterprise_cic_metrics: EnterpriseCICMetrics,
        metric_insights: list[RiskFactor],
    ) -> list[RiskFactor]:
        if enterprise_cic_metrics.top_risk_factors:
            return enterprise_cic_metrics.top_risk_factors

        scored_factors: list[tuple[float, RiskFactor]] = []
        metrics = enterprise_cic_metrics.metrics
        insight_map = {item.name: item for item in metric_insights}
        for metric_name, metric_value in metrics.items():
            severity = self._metric_severity(metric_name, metric_value)
            if severity <= 0:
                continue
            scored_factors.append(
                (
                    severity,
                    RiskFactor(
                        name=metric_name,
                        value=str(metric_value),
                        note=insight_map.get(
                            metric_name,
                            RiskFactor(name=metric_name, value=str(metric_value)),
                        ).note,
                    ),
                )
            )

        scored_factors.sort(key=lambda item: item[0], reverse=True)
        return [factor for _, factor in scored_factors[:5]]

    def _metric_severity(self, metric_name: str, metric_value: str | int | float | bool) -> float:
        if isinstance(metric_value, bool):
            numeric_value = 1.0 if metric_value else 0.0
        else:
            try:
                numeric_value = float(metric_value)
            except (TypeError, ValueError):
                return 0.0

        higher_is_worse = {
            "CV_value": (0.30, 0.45),
            "Spike_ratio": (1.30, 1.70),
        }
        lower_is_worse = {
            "Growth_score": (0.45, 0.30),
            "CV_score": (0.45, 0.25),
            "Spike_score": (0.45, 0.25),
            "Txn_freq_score": (0.55, 0.35),
            "Years_score": (0.35, 0.15),
            "Industry_score": (0.65, 0.45),
        }

        if metric_name in higher_is_worse:
            warning, critical = higher_is_worse[metric_name]
            if numeric_value >= critical:
                return 1.0
            if numeric_value >= warning:
                return 0.6
            return 0.0

        if metric_name in lower_is_worse:
            warning, critical = lower_is_worse[metric_name]
            if numeric_value <= critical:
                return 1.0
            if numeric_value <= warning:
                return 0.6
            return 0.0

        if metric_name == "Growth_value":
            if numeric_value <= -0.30:
                return 0.9
            if numeric_value < 0:
                return 0.5
            return 0.0

        if metric_name in {"Revenue_mean_30d", "Revenue_mean_90d"}:
            if numeric_value < 1_000_000:
                return 0.4
            return 0.0

        if metric_name == "Txn_frequency":
            if numeric_value < 12:
                return 0.7
            if numeric_value < 20:
                return 0.4
            return 0.0

        return 0.0

    def _decide_recommendation(
        self,
        matched_rule: CreditScoreRule,
        risk_class: str,
        risk_probability: float,
    ) -> str:
        safe_classes = {"VERY_LOW", "LOW", "GOOD", "VERY_GOOD"}

        if matched_rule.decision == "REJECT" or risk_class == "VERY_POOR":
            return "REJECT"
        if matched_rule.decision == "LIKELY_REJECT":
            if risk_class in safe_classes:
                return "MANUAL_REVIEW"
            return "REJECT"
        if risk_class == "POOR" and risk_probability >= 0.70:
            return "REJECT"
        if matched_rule.decision == "REVIEW_REQUIRED":
            if risk_class in safe_classes and risk_probability < 0.40:
                return "APPROVE_WITH_CONDITIONS"
            return "MANUAL_REVIEW"
        if risk_class in {"POOR", "MEDIUM"}:
            return "MANUAL_REVIEW"
        if matched_rule.decision == "APPROVE_EASILY" and risk_class in safe_classes and risk_probability < 0.35:
            return "APPROVE"
        if matched_rule.decision == "APPROVE" and risk_class in safe_classes and risk_probability < 0.50:
            return "APPROVE_WITH_CONDITIONS"
        return "MANUAL_REVIEW"

    def _build_advisory_query(
        self,
        enterprise_profile: EnterpriseProfile,
        matched_rule: CreditScoreRule,
        risk_class: str,
        metric_insights: list[RiskFactor],
        top_risk_factors: list[RiskFactor],
    ) -> str:
        years_text = str(enterprise_profile.years_in_business or "khong ro")
        focus_metrics = ", ".join(item.name for item in top_risk_factors[:4]) or ", ".join(
            item.name for item in metric_insights[:4]
        )
        return (
            "quy dinh cap tin dung cho doanh nghiep, dieu kien tham dinh ho so vay, "
            f"doanh nghiep nganh {enterprise_profile.industry or 'khong ro'}, "
            f"loai hinh {enterprise_profile.business_type or 'khong ro'}, "
            f"so nam hoat dong la {years_text}, "
            f"credit score muc {matched_rule.level}, "
            f"risk class {risk_class}, "
            f"cac chi so CIC can luu y la: {focus_metrics}"
        )

    def _credit_rule_probability_anchor(self, matched_level: str) -> float:
        anchors = {
            "VERY_GOOD": 0.15,
            "GOOD": 0.30,
            "AVERAGE": 0.55,
            "POOR": 0.78,
            "VERY_POOR": 0.92,
            "UNKNOWN": 0.50,
        }
        return anchors.get(matched_level.upper().strip(), 0.50)

    def _probability_to_risk_class(self, probability: float) -> str:
        if probability < 0.20:
            return "VERY_LOW"
        if probability < 0.40:
            return "LOW"
        if probability < 0.60:
            return "MEDIUM"
        if probability < 0.85:
            return "POOR"
        return "VERY_POOR"

    def _probability_band(self, risk_class: str) -> tuple[float, float]:
        bands = {
            "VERY_LOW": (0.00, 0.20),
            "LOW": (0.20, 0.40),
            "MEDIUM": (0.40, 0.60),
            "POOR": (0.60, 0.85),
            "VERY_POOR": (0.85, 1.00),
        }
        return bands.get(risk_class, (0.00, 1.00))

    def _format_probability_band(self, band: tuple[float, float]) -> str:
        return f"{band[0]:.2f}-{band[1]:.2f}"
