import pandas as pd

from app.core.prompts import RISK_REVIEW_REPORT_TEMPLATE, RISK_REVIEW_USER_REPORT_TEMPLATE
from app.schemas.loan_models import (
    CICMetricSpec,
    CreditScoreRule,
    EnterpriseCICMetrics,
    EnterpriseProfile,
    RiskReviewResult,
)
from app.services.credit_limits import calculate_credit_limit, get_coefficient_note


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
        risk_class_review = self._build_risk_class_review(
            risk_assessment=risk_assessment,
            review=review,
        )
        user_enterprise_overview = self._build_user_enterprise_overview(profile)
        business_status = self._build_user_business_status(
            risk_assessment=risk_assessment,
            review=review,
        )
        loan_eligibility = self._build_user_loan_eligibility(review.reviewed_recommendation)
        bank_advice = self._build_bank_advice(
            risk_assessment=risk_assessment,
            review=review,
            enterprise_cic_metrics=enterprise_cic_metrics,
        )
        user_advice = self._build_user_advice(
            enterprise_profile=profile,
            risk_assessment=risk_assessment,
            review=review,
        )
        next_actions = self._build_next_actions(
            enterprise_profile=profile,
            review_recommendation=review.reviewed_recommendation,
            risk_class_is_reasonable=review.risk_class_is_reasonable,
        )
        report_text_bank = self._compose_bank_report_text(
            enterprise_overview=enterprise_overview,
            risk_class_review=risk_class_review,
            current_overview=current_overview,
            bank_advice=bank_advice,
            next_actions=next_actions,
        )
        report_text_user = self._compose_user_report_text(
            enterprise_overview=user_enterprise_overview,
            business_status=business_status,
            loan_eligibility=loan_eligibility,
            user_advice=user_advice,
        )
        return RiskReviewResult(
            enterprise_profile=profile,
            risk_assessment=risk_assessment,
            review=review,
            enterprise_overview=enterprise_overview,
            current_overview=current_overview,
            bank_advice=bank_advice,
            user_advice=user_advice,
            next_actions=next_actions,
            report_text=report_text_bank,
            report_text_user=report_text_user,
            report_text_bank=report_text_bank,
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

    def _build_user_enterprise_overview(self, enterprise_profile: EnterpriseProfile) -> str:
        details: list[str] = []
        if enterprise_profile.name:
            details.append(f"doanh nghiệp/chủ hộ {enterprise_profile.name}")
        if enterprise_profile.industry:
            details.append(f"ngành nghề {enterprise_profile.industry}")
        if enterprise_profile.business_type:
            details.append(f"loại hình {enterprise_profile.business_type}")
        if enterprise_profile.location:
            details.append(f"khu vực hoạt động {enterprise_profile.location}")
        if enterprise_profile.years_in_business:
            details.append(f"thời gian hoạt động khoảng {enterprise_profile.years_in_business:.2f} năm")
        if not details:
            return "Ngân hàng đã tiếp nhận thông tin cơ bản của doanh nghiệp để phục vụ đánh giá hồ sơ vay."
        return "Thông tin ghi nhận cho thấy " + ", ".join(details) + "."

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
        if review.risk_class_is_reasonable:
            alignment_text = "Nhãn đầu vào nhìn chung phù hợp với nhóm tín hiệu hiện tại. "
        else:
            alignment_text = "Nhãn đầu vào đang có xu hướng thấp hơn mức rủi ro phản ánh từ tín hiệu hiện tại. "
        return (
            f"Tín hiệu hiện tại cho thấy doanh nghiệp đang nằm ở nhóm {review.expected_risk_class}. "
            f"{alignment_text}Credit score khớp rule {risk_assessment.matched_rule.level}, "
            f"trong khi các metric nổi bật gồm {factor_summary} cho thấy khả năng biến động dòng tiền "
            f"và độ ổn định hoạt động đang là điểm cần theo dõi sát."
        )

    def _build_user_business_status(self, risk_assessment, review) -> str:
        risk_class = review.expected_risk_class.upper()
        level_map = {
            "VERY_LOW": "mức rủi ro rất thấp",
            "LOW": "mức rủi ro thấp",
            "MEDIUM": "mức rủi ro trung bình",
            "HIGH": "mức rủi ro cao",
            "VERY_HIGH": "mức rủi ro rất cao",
        }
        level_text = level_map.get(risk_class, "mức độ cần theo dõi thêm")

        recommendation = review.reviewed_recommendation
        if recommendation == "APPROVE":
            return (
                f"Hồ sơ hiện cho thấy doanh nghiệp đang ở trạng thái tương đối ổn định và được đánh giá ở {level_text}. "
                "Một số chỉ số chính nhìn chung đang hỗ trợ cho việc xem xét tín dụng."
            )
        if recommendation == "APPROVE_WITH_CONDITIONS":
            return (
                f"Hồ sơ cho thấy doanh nghiệp vẫn có cơ sở để được xem xét vay, nhưng hiện còn một số điểm cần làm rõ và đang được đánh giá ở {level_text}. "
                "Ngân hàng sẽ cần thêm xác nhận để bảo đảm việc cấp tín dụng an toàn hơn."
            )
        if recommendation == "MANUAL_REVIEW":
            return (
                f"Hồ sơ hiện chưa đủ rõ để kết luận ngay và doanh nghiệp đang được đánh giá ở {level_text}. "
                "Ngân hàng cần xem xét thêm một số thông tin trước khi đưa ra quyết định cuối cùng."
            )
        return (
            f"Hồ sơ hiện cho thấy doanh nghiệp đang có nhiều yếu tố cần thận trọng và được đánh giá ở {level_text}. "
            "Tại thời điểm này, tình trạng hồ sơ chưa thuận lợi cho việc cấp tín dụng."
        )

    def _build_bank_advice(self, risk_assessment, review, enterprise_cic_metrics: EnterpriseCICMetrics) -> str:
        recommendation = review.reviewed_recommendation
        advice_map = {
            "APPROVE": "Có thể xem xét cho vay theo quy trình thông thường, nhưng vẫn cần kiểm tra tính đầy đủ của hồ sơ.",
            "APPROVE_WITH_CONDITIONS": "Có thể xem xét cho vay nhưng nên áp điều kiện bổ sung hồ sơ, giới hạn mức vay và tăng cường điều kiện kiểm soát sau giải ngân.",
            "MANUAL_REVIEW": "Chưa nên phê duyệt ngay. Nên chuyển thẩm định thủ công, bổ sung tài liệu tài chính và kiểm tra thêm khả năng trả nợ trước khi quyết định cho vay.",
            "REJECT": "Không nên phê duyệt cho vay ở thời điểm hiện tại, trừ khi doanh nghiệp bổ sung được các bằng chứng rất mạnh để đảo ngược các tín hiệu rủi ro.",
        }
        credit_limit_text = self._build_credit_limit_text(
            risk_assessment=risk_assessment,
            review=review,
            enterprise_cic_metrics=enterprise_cic_metrics,
        )
        reason = (
            f"Khuyến nghị sau khi review là **{recommendation}**. "
            f"Lý do chính: credit score thuộc mức {risk_assessment.matched_rule.level}, "
            f"risk class hợp lý hơn là {review.expected_risk_class}, "
            f"và xác suất rủi ro kỳ vọng ở mức {review.expected_risk_probability:.4f}."
        )
        return "\n".join(
            [
                reason + " " + advice_map.get(recommendation, ""),
                credit_limit_text,
            ]
        )

    def _build_credit_limit_text(
        self,
        risk_assessment,
        review,
        enterprise_cic_metrics: EnterpriseCICMetrics,
    ) -> str:
        coefficient_set_name = self._select_credit_limit_coefficient_set(review.reviewed_recommendation)
        customer_data = pd.Series(
            {
                **enterprise_cic_metrics.metrics,
                "default_probability": review.expected_risk_probability,
                "CIC_SCORE": risk_assessment.credit_score,
                "label_cic_range": self._map_credit_level_to_cic_range(risk_assessment.matched_rule.level),
            }
        )
        credit_limit = calculate_credit_limit(
            customer_data=customer_data,
            coefficient_set_name=coefficient_set_name,
        )
        limit_note = get_coefficient_note(coefficient_set_name)
        return (
            f"Hạn mức cho vay đề xuất: **{self._format_currency_vnd(credit_limit)}**.\n"
            f"Ghi chú hạn mức: Tính theo bộ hệ số **{coefficient_set_name}**; {limit_note} "
            "Kết quả đã được làm tròn xuống đến 100.000.000 VND gần nhất."
        )

    def _select_credit_limit_coefficient_set(self, recommendation: str) -> str:
        coefficient_map = {
            "APPROVE": "Growth-driven",
            "APPROVE_WITH_CONDITIONS": "Balanced",
            "MANUAL_REVIEW": "Conservative",
            "REJECT": "Risk-based",
        }
        return coefficient_map.get(recommendation, "Balanced")

    def _map_credit_level_to_cic_range(self, credit_level: str) -> str:
        level_map = {
            "VERY_GOOD": "EXCELLENT",
            "GOOD": "GOOD",
            "AVERAGE": "FAIR",
            "LOW": "LOW",
            "VERY_LOW": "LOW",
        }
        return level_map.get(credit_level.upper().strip(), "LOW")

    def _format_currency_vnd(self, amount: int) -> str:
        return f"{amount:,.0f} VND"

    def _build_user_advice(self, enterprise_profile: EnterpriseProfile, risk_assessment, review) -> str:
        recommendation = review.reviewed_recommendation
        advice_map = {
            "APPROVE": (
                "Doanh nghiệp có thể tiếp tục làm việc với ngân hàng để hoàn tất bước xác nhận thông tin, "
                "duy trì dòng tiền ổn định và chuẩn bị kế hoạch sử dụng vốn rõ ràng."
            ),
            "APPROVE_WITH_CONDITIONS": (
                "Doanh nghiệp nên chuẩn bị thêm thông tin về dòng tiền, doanh thu, nghĩa vụ trả nợ hiện tại "
                "và mục đích sử dụng vốn để đáp ứng các điều kiện phê duyệt bổ sung từ ngân hàng."
            ),
            "MANUAL_REVIEW": (
                "Doanh nghiệp nên chủ động bổ sung chứng từ vận hành, thông tin giao dịch thực tế "
                "và giải trình những biến động đáng chú ý trong hoạt động kinh doanh để hỗ trợ quá trình thẩm định."
            ),
            "REJECT": (
                "Doanh nghiệp nên ưu tiên cải thiện tính ổn định dòng tiền, kiểm soát tốt hơn hiệu quả kinh doanh "
                "và chuẩn bị lại hồ sơ khi đã có thêm bằng chứng tích cực hơn."
            ),
        }
        guidance = advice_map.get(
            recommendation,
            "Doanh nghiệp nên bổ sung thêm thông tin để ngân hàng có cơ sở đánh giá đầy đủ hơn.",
        )
        if not enterprise_profile.industry or not enterprise_profile.business_type:
            guidance += " Đồng thời, doanh nghiệp nên cập nhật đầy đủ thông tin ngành nghề và loại hình kinh doanh trong hồ sơ."
        if risk_assessment.credit_score < 500:
            guidance += " Việc cải thiện lịch sử tín dụng và tính đều đặn của dòng tiền cũng sẽ giúp hồ sơ thuận lợi hơn."
        return guidance

    def _build_user_loan_eligibility(self, recommendation: str) -> str:
        eligibility_map = {
            "APPROVE": "Khả năng vay vốn hiện tại ở mức tích cực. Hồ sơ có thể được tiếp tục xử lý theo quy trình thông thường nếu thông tin cung cấp nhất quán.",
            "APPROVE_WITH_CONDITIONS": "Doanh nghiệp vẫn có khả năng được vay, nhưng việc phê duyệt nhiều khả năng sẽ đi kèm thêm điều kiện hoặc yêu cầu bổ sung thông tin.",
            "MANUAL_REVIEW": "Khả năng vay vốn hiện chưa thể kết luận ngay. Hồ sơ cần được đánh giá thủ công thêm trước khi ngân hàng ra quyết định.",
            "REJECT": "Khả năng được phê duyệt vay ở thời điểm hiện tại là thấp. Doanh nghiệp nên cải thiện hồ sơ trước khi nộp lại hoặc đề nghị xem xét lại.",
        }
        return eligibility_map.get(
            recommendation,
            "Ngân hàng cần thêm thông tin trước khi có thể đánh giá rõ khả năng vay vốn của doanh nghiệp.",
        )

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

    def _compose_bank_report_text(
        self,
        enterprise_overview: str,
        risk_class_review: str,
        current_overview: str,
        bank_advice: str,
        next_actions: list[str],
    ) -> str:
        next_actions_text = "\n".join(f"- {action}" for action in next_actions)
        return RISK_REVIEW_REPORT_TEMPLATE.format(
            enterprise_overview=enterprise_overview,
            risk_class_review=risk_class_review,
            current_overview=current_overview,
            bank_advice=bank_advice,
            next_actions=next_actions_text,
        )

    def _compose_user_report_text(
        self,
        enterprise_overview: str,
        business_status: str,
        loan_eligibility: str,
        user_advice: str,
    ) -> str:
        return RISK_REVIEW_USER_REPORT_TEMPLATE.format(
            enterprise_overview=enterprise_overview,
            business_status=business_status,
            loan_eligibility=loan_eligibility,
            user_advice=user_advice,
        )
