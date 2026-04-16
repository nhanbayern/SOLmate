import re

from app.core.loan_prompt_payload import build_loan_model_input_json
from app.core.prompts import LOAN_ADVISORY_PROMPT_TEMPLATE
from app.schemas.loan_models import AdvisoryReport, EnterpriseCICMetrics, EnterpriseProfile, RiskAssessmentResult


_RECOMMENDATION_PATTERN = re.compile(r"(?im)^\s*(?:Quyết định|Quyet dinh):\s*(.+?)\s*$")


def _build_key_reasons(
    enterprise_profile: EnterpriseProfile,
    risk_assessment: RiskAssessmentResult,
) -> list[str]:
    reasons = [
        f"Credit score {risk_assessment.credit_score:.0f} được xếp mức {risk_assessment.matched_rule.level}.",
        (
            f"Mô hình cho khách hàng {enterprise_profile.customer_id} dự đoán nhóm rủi ro "
            f"{risk_assessment.risk_class} với xác suất {risk_assessment.risk_probability:.2f}."
        ),
    ]
    factors = risk_assessment.top_risk_factors or risk_assessment.metric_insights
    for factor in factors[:3]:
        reasons.append(f"{factor.name}={factor.value}: {factor.note}")
    return reasons


def _build_missing_information(enterprise_profile: EnterpriseProfile) -> list[str]:
    missing_information: list[str] = []
    if not enterprise_profile.merchant_id:
        missing_information.append("Thiếu merchant_id để đối chiếu giao dịch liên quan.")
    if not enterprise_profile.years_in_business:
        missing_information.append("Thiếu số năm hoạt động của doanh nghiệp.")
    return missing_information


def _build_suggested_actions(risk_assessment: RiskAssessmentResult) -> list[str]:
    suggested_actions = [
        "Đối chiếu dòng tiền POS với biến động vào tài khoản để kiểm tra tính xác thực của doanh thu.",
        "Kiểm tra tính đầy đủ, độ mới và bất thường của bộ dữ liệu giao dịch trước khi phê duyệt.",
        "Rà soát lại các chỉ số rủi ro nổi bật và lập kế hoạch giám sát sau giải ngân nếu hồ sơ đủ điều kiện.",
    ]
    if risk_assessment.recommendation == "MANUAL_REVIEW":
        suggested_actions.insert(0, "Chuyển hồ sơ sang thẩm định thủ công bổ sung.")
    return suggested_actions


def _build_summary(recommendation: str, risk_overview: str) -> str:
    if recommendation and len(recommendation.split()) > 4:
        return recommendation
    if recommendation and risk_overview:
        return f"{recommendation}. {risk_overview}"
    return recommendation or risk_overview


def _compose_report_text(
    enterprise_profile: EnterpriseProfile,
    risk_assessment: RiskAssessmentResult,
    missing_information: list[str],
    suggested_actions: list[str],
    recommendation: str,
) -> str:
    enterprise_overview = (
        f"Doanh nghiệp {enterprise_profile.name or enterprise_profile.customer_id} "
        f"thuộc ngành {enterprise_profile.industry or 'chưa rõ'}, "
        f"loại hình {enterprise_profile.business_type or 'chưa rõ'}, "
        f"hoạt động tại {enterprise_profile.location or 'chưa rõ'}."
    )
    risk_lines = [
        f"- Credit score: {risk_assessment.credit_score:.2f}",
        f"- Risk class: {risk_assessment.risk_class}",
        f"- Risk probability: {risk_assessment.risk_probability:.2f}",
    ]
    risk_lines.extend(
        f"- {factor.name}: {factor.value} ({factor.note})"
        for factor in (risk_assessment.top_risk_factors or risk_assessment.metric_insights)[:3]
    )

    missing_lines = (
        "\n".join(f"- {item}" for item in missing_information)
        if missing_information
        else "- Không có thông tin thiếu nổi bật."
    )
    action_lines = "\n".join(f"- {item}" for item in suggested_actions)

    return "\n".join(
        [
            "### 1. Tổng quan khách hàng",
            enterprise_overview,
            "",
            "### 2. Đánh giá rủi ro",
            "\n".join(risk_lines),
            "",
            "### 3. Thông tin còn thiếu",
            missing_lines,
            "",
            "### 4. Khuyến nghị cho nhân viên ngân hàng",
            f"Quyết định: {recommendation}",
            f"Lý do chính: {risk_assessment.summary}",
            "",
            "### 5. Đề xuất hành động",
            action_lines,
        ]
    )


def _extract_recommendation(text: str) -> str:
    match = _RECOMMENDATION_PATTERN.search(text)
    if not match:
        return ""
    return match.group(1).strip()


class MockLoanAdvisoryGenerator:
    def generate(
        self,
        enterprise_profile: EnterpriseProfile,
        enterprise_cic_metrics: EnterpriseCICMetrics,
        risk_assessment: RiskAssessmentResult,
    ) -> AdvisoryReport:
        key_reasons = _build_key_reasons(enterprise_profile, risk_assessment)
        missing_information = _build_missing_information(enterprise_profile)
        suggested_actions = _build_suggested_actions(risk_assessment)
        summary = _build_summary(risk_assessment.recommendation, risk_assessment.summary)
        report_text = _compose_report_text(
            enterprise_profile=enterprise_profile,
            risk_assessment=risk_assessment,
            missing_information=missing_information,
            suggested_actions=suggested_actions,
            recommendation=risk_assessment.recommendation,
        )

        return AdvisoryReport(
            recommendation=risk_assessment.recommendation,
            summary=summary,
            risk_overview=risk_assessment.summary,
            key_reasons=key_reasons,
            missing_information=missing_information,
            suggested_actions=suggested_actions,
            report_text=report_text,
        )


class QwenLoanAdvisoryGenerator:
    def __init__(self, llm_client) -> None:
        self.llm_client = llm_client

    def generate(
        self,
        enterprise_profile: EnterpriseProfile,
        enterprise_cic_metrics: EnterpriseCICMetrics,
        risk_assessment: RiskAssessmentResult,
    ) -> AdvisoryReport:
        prompt = LOAN_ADVISORY_PROMPT_TEMPLATE.format(
            loan_application_json=build_loan_model_input_json(
                enterprise_profile=enterprise_profile,
                enterprise_cic_metrics=enterprise_cic_metrics,
            ),
        )
        text = self.llm_client.generate(prompt, max_new_tokens=256).strip()

        recommendation = _extract_recommendation(text) or risk_assessment.recommendation
        risk_overview = risk_assessment.summary
        missing_information = _build_missing_information(enterprise_profile)
        suggested_actions = _build_suggested_actions(risk_assessment)
        summary = _build_summary(recommendation, risk_overview)
        key_reasons = _build_key_reasons(enterprise_profile, risk_assessment)
        report_text = text or _compose_report_text(
            enterprise_profile=enterprise_profile,
            risk_assessment=risk_assessment,
            missing_information=missing_information,
            suggested_actions=suggested_actions,
            recommendation=recommendation,
        )

        return AdvisoryReport(
            recommendation=recommendation,
            summary=summary,
            risk_overview=risk_overview,
            key_reasons=key_reasons,
            missing_information=missing_information,
            suggested_actions=suggested_actions,
            report_text=report_text,
        )
