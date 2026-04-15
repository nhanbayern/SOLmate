from app.schemas.loan_models import (
    CICMetricSpec,
    CreditScoreRule,
    EnterpriseCICMetrics,
    EnterpriseProfile,
    RiskAssessmentResult,
    RiskFactor,
)

# Đánh giá rủi ro, kết luận risk ban đầu dựa trên profile doanh nghiệp, điểm tín dụng và các chỉ số CIC khác.
class LoanRiskEngine:
    def evaluate(
        self,
        enterprise_profile: EnterpriseProfile,
        credit_score_rules: list[CreditScoreRule],
        cic_metric_specs: list[CICMetricSpec],
        enterprise_cic_metrics: EnterpriseCICMetrics,
    ) -> RiskAssessmentResult:
        #Chuẩn hóa nhãn risk_class từ CIC để dễ dàng đối chiếu và đưa ra kết luận
        normalized_risk_class = self._normalize_risk_class(enterprise_cic_metrics.risk_class)
        # Đối chiếu credit_score với các rule của credit_score
        matched_rule = self._match_credit_rule(
            enterprise_cic_metrics.credit_score,
            credit_score_rules,
        )
        
        metric_insights = self._build_metric_insights(
            enterprise_cic_metrics.metrics,
            cic_metric_specs,
        )
        
        #Nếu có probability do CIC cung cấp thì dùng luôn, nếu không có thì suy ra từ risk_class
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
            f"Doanh nghiệp {enterprise_profile.customer_id} hoạt động trong ngành "
            f"{enterprise_profile.industry or 'chưa biết hoạt động trong ngành nào'}, credit score "
            f"{enterprise_cic_metrics.credit_score:.2f}, thuộc mục {matched_rule.level}, "
            f"rủi ro mô hình {normalized_risk_class} ({risk_probability:.2f})."
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
        metrics: dict[str, str |float],
        cic_metric_specs: list[CICMetricSpec],
    ) -> list[RiskFactor]:
        spec_map = {item.metrics: item for item in cic_metric_specs}
        insights: list[RiskFactor] = []
        for metric_name, metric_value in metrics.items():
            spec = spec_map.get(metric_name)
            note = "Không có mô tả metrics."
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
                        note=insight_map.get(metric_name, RiskFactor(name=metric_name, value=str(metric_value))).note,
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
        years_text = str(enterprise_profile.years_in_business or "không rõ")
        focus_metrics = ", ".join(item.name for item in top_risk_factors[:4]) or ", ".join(item.name for item in metric_insights[:4])
        return (
            "quy định cấp tín dụng cho doanh nghiệp, điều kiện thẩm định hồ sơ vay, "
            f"doanh nghiệp ngành {enterprise_profile.industry or 'không rõ'}, "
            f"loại hình {enterprise_profile.business_type or 'không rõ'}, "
            f"số năm hoạt động là {years_text}, "
            f"credit score mức {matched_rule.level}, "
            f"risk class {risk_class}, "
            f"các chỉ số CIC cần lưu ý là: {focus_metrics}"
        )
