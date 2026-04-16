import re

from app.core.prompts import LOAN_ADVISORY_PROMPT_TEMPLATE
from app.schemas.loan_models import AdvisoryReport, EnterpriseProfile, RiskAssessmentResult


_RECOMMENDATION_PATTERN = re.compile(r"(?im)^\s*Quy[ếe]t định:\s*(.+?)\s*$")


def _build_key_reasons(
    enterprise_profile: EnterpriseProfile,
    risk_assessment: RiskAssessmentResult,
) -> list[str]:
    reasons = [
        f"Credit score {risk_assessment.credit_score:.0f} duoc xep muc {risk_assessment.matched_rule.level}.",
        (
            f"Mo hinh {enterprise_profile.customer_id} du doan nhom rui ro "
            f"{risk_assessment.risk_class} voi xac suat {risk_assessment.risk_probability:.2f}."
        ),
    ]
    factors = risk_assessment.top_risk_factors or risk_assessment.metric_insights
    for factor in factors[:3]:
        reasons.append(f"{factor.name}={factor.value}: {factor.note}")
    return reasons


def _build_missing_information(enterprise_profile: EnterpriseProfile) -> list[str]:
    missing_information: list[str] = []
    if not enterprise_profile.merchant_id:
        missing_information.append("Thieu merchant_id de doi chieu giao dich lien quan.")
    if not enterprise_profile.years_in_business:
        missing_information.append("Thieu so nam hoat dong cua doanh nghiep.")
    return missing_information


def _build_suggested_actions(risk_assessment: RiskAssessmentResult) -> list[str]:
    suggested_actions = [
        "Doi chieu dong tien POS voi bien dong vao tai khoan de kiem tra tinh xac thuc cua doanh thu.",
        "Kiem tra tinh day du, do moi va bat thuong cua bo du lieu giao dich truoc khi phe duyet.",
        "Ra soat lai cac chi so rui ro noi bat va lap ke hoach giam sat sau giai ngan neu ho so du dieu kien.",
    ]
    if risk_assessment.recommendation == "MANUAL_REVIEW":
        suggested_actions.insert(0, "Chuyen ho so sang tham dinh thu cong bo sung.")
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
        f"Doanh nghiep {enterprise_profile.name or enterprise_profile.customer_id} "
        f"thuoc nganh {enterprise_profile.industry or 'chua ro'}, "
        f"loai hinh {enterprise_profile.business_type or 'chua ro'}, "
        f"hoat dong tai {enterprise_profile.location or 'chua ro'}."
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
        else "- Khong co thong tin thieu noi bat."
    )
    action_lines = "\n".join(f"- {item}" for item in suggested_actions)

    return "\n".join(
        [
            "### 1. Tong quan khach hang",
            enterprise_overview,
            "",
            "### 2. Danh gia rui ro",
            "\n".join(risk_lines),
            "",
            "### 4. Thong tin con thieu",
            missing_lines,
            "",
            "### 5. Khuyen nghi",
            f"Quyet dinh: {recommendation}",
            f"Ly do chinh: {risk_assessment.summary}",
            "",
            "### 6. De xuat hanh dong",
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
        risk_assessment: RiskAssessmentResult,
    ) -> AdvisoryReport:
        metric_summary = "\n".join(
            f"- {item.name}: {item.value} ({item.note})" for item in risk_assessment.metric_insights
        )
        prompt = LOAN_ADVISORY_PROMPT_TEMPLATE.format(
            enterprise_profile=enterprise_profile.model_dump_json(indent=2),
            risk_assessment=risk_assessment.model_dump_json(indent=2),
            metric_summary=metric_summary or "- Khong co metric insight.",
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
