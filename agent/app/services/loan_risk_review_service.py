from app.core.prompts import RISK_REVIEW_REPORT_TEMPLATE
from app.schemas.loan_models import (
    CICMetricSpec,
    CreditScoreRule,
    EnterpriseCICMetrics,
    EnterpriseProfile,
    RiskReviewResult,
)


class LoanRiskReviewService:
    def __init__(self, risk_engine) -> None:
        self.risk_engine = risk_engine

    def run(
        self,
        credit_score_rules: list[CreditScoreRule],
        cic_metric_specs: list[CICMetricSpec],
        enterprise_cic_metrics: EnterpriseCICMetrics,
        enterprise_profile: EnterpriseProfile | None = None,
    ) -> RiskReviewResult:
        profile = enterprise_profile or EnterpriseProfile(
            customer_id=enterprise_cic_metrics.customer_id,
            years_in_business=0,
        )
        risk_assessment = self.risk_engine.evaluate(
            enterprise_profile=profile,
            credit_score_rules=credit_score_rules,
            cic_metric_specs=cic_metric_specs,
            enterprise_cic_metrics=enterprise_cic_metrics,
        )
        review = self.risk_engine.review_reasonableness(
            credit_score_rules=credit_score_rules,
            enterprise_cic_metrics=enterprise_cic_metrics,
            risk_assessment=risk_assessment,
        )
        enterprise_overview = self._build_enterprise_overview(
            enterprise_profile=profile,
            risk_assessment=risk_assessment,
        )
        current_overview = self._build_current_overview(
            risk_assessment=risk_assessment,
            review=review,
        )
        bank_advice = self._build_bank_advice(
            risk_assessment=risk_assessment,
            review=review,
        )
        next_actions = self._build_next_actions(
            enterprise_profile=profile,
            review_recommendation=review.reviewed_recommendation,
            risk_class_is_reasonable=review.risk_class_is_reasonable,
        )
        report_text = self._compose_report_text(
            enterprise_overview=enterprise_overview,
            risk_class_review=self._build_risk_class_review(risk_assessment, review),
            current_overview=current_overview,
            bank_advice=bank_advice,
            next_actions=next_actions,
        )
        return RiskReviewResult(
            enterprise_profile=profile,
            risk_assessment=risk_assessment,
            review=review,
            enterprise_overview=enterprise_overview,
            current_overview=current_overview,
            bank_advice=bank_advice,
            next_actions=next_actions,
            report_text=report_text,
        )

    def _build_enterprise_overview(
        self,
        enterprise_profile: EnterpriseProfile,
        risk_assessment,
    ) -> str:
        details: list[str] = [f"Mã khách hàng {enterprise_profile.customer_id}"]
        if enterprise_profile.name:
            details.append(f"tên doanh nghiệp/chủ hộ {enterprise_profile.name}")
        if enterprise_profile.industry:
            details.append(f"ngành {enterprise_profile.industry}")
        if enterprise_profile.business_type:
            details.append(f"loại hình {enterprise_profile.business_type}")
        if enterprise_profile.location:
            details.append(f"địa bàn {enterprise_profile.location}")
        if enterprise_profile.years_in_business:
            details.append(f"thời gian hoạt động {enterprise_profile.years_in_business:.2f} năm")
        details.append(f"credit score hiện tại {risk_assessment.credit_score:.2f}")
        return "Doanh nghiệp có " + ", ".join(details) + "."

    def _build_risk_class_review(self, risk_assessment, review) -> str:
        status = "hợp lý" if review.risk_class_is_reasonable else "chưa hợp lý"
        probability_status = "hợp lý" if review.risk_probability_is_reasonable else "chưa hợp lý"
        highlighted_findings = "\n".join(f"- {item}" for item in review.findings[:5])
        return (
            f"Nhãn risk class đầu vào là **{review.provided_risk_class}** và được đánh giá là **{status}**.\n"
            f"Risk class kỳ vọng sau khi đối chiếu credit score rule và metrics là **{review.expected_risk_class}**.\n"
            f"Xác suất đầu vào **{review.provided_risk_probability:.4f}** được xem là **{probability_status}**; "
            f"mức kỳ vọng xấp xỉ là **{review.expected_risk_probability:.4f}** trong vùng **{review.expected_probability_band}**.\n"
            f"Các căn cứ chính:\n{highlighted_findings}"
        )

    def _build_current_overview(self, risk_assessment, review) -> str:
        factor_summary = ", ".join(
            f"{factor.name}={factor.value}" for factor in risk_assessment.top_risk_factors[:4]
        ) or "chưa xác định được metric nổi bật"
        return (
            f"Tín hiệu hiện tại cho thấy doanh nghiệp đang nằm ở nhóm {review.expected_risk_class}, "
            f"nghiêng về mức rủi ro cao hơn nhãn đầu vào. Credit score khớp rule {risk_assessment.matched_rule.level}, "
            f"trong khi các metric nổi bật gồm {factor_summary} cho thấy khả năng biến động dòng tiền "
            f"và độ ổn định hoạt động đang là điểm cần theo dõi sát."
        )

    def _build_bank_advice(self, risk_assessment, review) -> str:
        recommendation = review.reviewed_recommendation
        advice_map = {
            "APPROVE": "Có thể xem xét cho vay theo quy trình thông thường, nhưng vẫn cần kiểm tra tính đầy đủ của hồ sơ.",
            "APPROVE_WITH_CONDITIONS": "Có thể xem xét cho vay nhưng nên áp điều kiện bổ sung hồ sơ, giới hạn mức vay và tăng cường điều kiện kiểm soát sau giải ngân.",
            "MANUAL_REVIEW": "Chưa nên phê duyệt ngay. Nên chuyển thẩm định thủ công, bổ sung tài liệu tài chính và kiểm tra thêm khả năng trả nợ trước khi quyết định cho vay.",
            "REJECT": "Không nên phê duyệt cho vay ở thời điểm hiện tại, trừ khi doanh nghiệp bổ sung được các bằng chứng rất mạnh để đảo ngược các tín hiệu rủi ro.",
        }
        reason = (
            f"Khuyến nghị sau khi review là **{recommendation}**. "
            f"Lý do chính: credit score thuộc mức {risk_assessment.matched_rule.level}, "
            f"risk class hợp lý hơn là {review.expected_risk_class}, "
            f"và xác suất rủi ro kỳ vọng ở mức {review.expected_risk_probability:.4f}."
        )
        return reason + " " + advice_map.get(recommendation, "")

    def _build_next_actions(
        self,
        enterprise_profile: EnterpriseProfile,
        review_recommendation: str,
        risk_class_is_reasonable: bool,
    ) -> list[str]:
        actions = [
            "Yêu cầu bổ sung báo cáo tài chính, sao kê dòng tiền và thông tin dư nợ hiện tại.",
            "Kiểm tra lại nguồn gốc biến động doanh thu và mức độ phụ thuộc vào doanh thu đột biến.",
            "Đối chiếu thêm lịch sử trả nợ, tài sản bảo đảm và mục đích sử dụng vốn.",
        ]
        if not risk_class_is_reasonable:
            actions.insert(0, "Rà soát lại mô hình gán nhãn risk_class vì nhãn đầu vào đang có dấu hiệu đánh giá thấp hơn mức rủi ro thực tế.")
        if review_recommendation == "REJECT":
            actions.insert(0, "Tạm dừng phê duyệt và chỉ mở lại hồ sơ nếu doanh nghiệp cung cấp được bằng chứng cải thiện chất lượng tín dụng.")
        if review_recommendation == "APPROVE_WITH_CONDITIONS":
            actions.append("Nếu cấp tín dụng, cần hạn mức thận trọng và điều kiện giám sát sau giải ngân rõ ràng.")
        if not enterprise_profile.industry or not enterprise_profile.business_type:
            actions.append("Bổ sung thông tin nền tảng về ngành nghề và loại hình kinh doanh để đánh giá bối cảnh doanh nghiệp đầy đủ hơn.")
        return actions

    def _compose_report_text(
        self,
        enterprise_overview: str,
        risk_class_review: str,
        current_overview: str,
        bank_advice: str,
        next_actions: list[str],
    ) -> str:
        formatted_actions = "\n".join(f"- {item}" for item in next_actions)
        return RISK_REVIEW_REPORT_TEMPLATE.format(
            enterprise_overview=enterprise_overview,
            risk_class_review=risk_class_review,
            current_overview=current_overview,
            bank_advice=bank_advice,
            next_actions=formatted_actions,
        )
