import re

from app.core.prompts import LOAN_ADVISORY_PROMPT_TEMPLATE
from app.schemas.loan_models import AdvisoryReport, EnterpriseProfile, RiskAssessmentResult
from app.schemas.models import LegalArticle


_SECTION_LABELS = {
    "Risk Overview": "risk_overview",
    "Legal Basis": "legal_basis",
    "Missing Information": "missing_information",
    "Recommendation": "recommendation",
    "Suggested Next Actions": "suggested_actions",
}
_SECTION_PATTERN = re.compile(
    r"(?ims)^\s*(?P<label>Risk Overview|Legal Basis|Missing Information|Recommendation|Suggested Next Actions)\s*:\s*(?P<content>.*?)(?=^\s*(?:Risk Overview|Legal Basis|Missing Information|Recommendation|Suggested Next Actions)\s*:|\Z)"
)


def _build_legal_basis_refs(legal_articles: list[LegalArticle]) -> list[str]:
    return [
        f"{article.metadata.get('document_id', article.article_id)} - {article.metadata.get('section_path', article.title)}"
        for article in legal_articles
    ]


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
        "Đối chiếu thêm hồ sơ tài chính và tài sản bảo đảm trước khi phê duyệt.",
        "Kiểm tra lại lịch sử trả nợ CIC và các nghĩa vụ hiện tại của doanh nghiệp.",
    ]
    if risk_assessment.recommendation == "MANUAL_REVIEW":
        suggested_actions.insert(0, "Chuyen ho so sang tham dinh thu cong bo sung.")
    return suggested_actions


def _extract_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    for match in _SECTION_PATTERN.finditer(text):
        label = match.group("label").strip()
        sections[_SECTION_LABELS[label]] = match.group("content").strip()
    return sections


def _parse_list_section(text: str) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []

    normalized = cleaned.lower().strip(". ")
    if normalized in {"khong co", "khong", "none", "n/a", "khong co thong tin bo sung"}:
        return []

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    items: list[str] = []
    for line in lines:
        line = re.sub(r"^[-*]\s*", "", line)
        line = re.sub(r"^\d+[.)]\s*", "", line)
        if line:
            items.append(line.strip())

    if len(items) > 1:
        return items

    if ";" in cleaned:
        return [part.strip() for part in cleaned.split(";") if part.strip()]

    return items or [cleaned]


def _build_summary(recommendation: str, risk_overview: str) -> str:
    if recommendation and len(recommendation.split()) > 4:
        return recommendation
    if recommendation and risk_overview:
        return f"{recommendation}. {risk_overview}"
    return recommendation or risk_overview


def _compose_report_text(
    risk_overview: str,
    legal_basis: list[str],
    missing_information: list[str],
    recommendation: str,
    suggested_actions: list[str],
) -> str:
    sections = [
        f"Risk Overview: {risk_overview}" if risk_overview else "",
        (
            "Legal Basis:\n- " + "\n- ".join(legal_basis)
            if legal_basis
            else "Legal Basis: Khong co can cu phap ly phu hop."
        ),
        (
            "Missing Information:\n- " + "\n- ".join(missing_information)
            if missing_information
            else "Missing Information: Khong co thong tin thieu noi bat."
        ),
        f"Recommendation: {recommendation}" if recommendation else "",
        (
            "Suggested Next Actions:\n- " + "\n- ".join(suggested_actions)
            if suggested_actions
            else "Suggested Next Actions: Chua co de xuat bo sung."
        ),
    ]
    return "\n\n".join(section for section in sections if section)


class MockLoanAdvisoryGenerator:
    def generate(
        self,
        enterprise_profile: EnterpriseProfile,
        risk_assessment: RiskAssessmentResult,
        legal_articles: list[LegalArticle],
    ) -> AdvisoryReport:
        legal_basis = _build_legal_basis_refs(legal_articles)
        key_reasons = _build_key_reasons(enterprise_profile, risk_assessment)
        missing_information = _build_missing_information(enterprise_profile)
        suggested_actions = _build_suggested_actions(risk_assessment)
        summary = _build_summary(risk_assessment.recommendation, risk_assessment.summary)
        report_text = _compose_report_text(
            risk_overview=risk_assessment.summary,
            legal_basis=legal_basis,
            missing_information=missing_information,
            recommendation=risk_assessment.recommendation,
            suggested_actions=suggested_actions,
        )

        return AdvisoryReport(
            recommendation=risk_assessment.recommendation,
            summary=summary,
            risk_overview=risk_assessment.summary,
            legal_basis=legal_basis,
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
        legal_articles: list[LegalArticle],
    ) -> AdvisoryReport:
        legal_context = "\n\n".join(
            f"{article.title}\n{article.content}" for article in legal_articles
        )
        metric_summary = "\n".join(
            f"- {item.name}: {item.value} ({item.note})" for item in risk_assessment.metric_insights
        )
        prompt = LOAN_ADVISORY_PROMPT_TEMPLATE.format(
            enterprise_profile=enterprise_profile.model_dump_json(indent=2),
            risk_assessment=risk_assessment.model_dump_json(indent=2),
            metric_summary=metric_summary or "- Khong co metric insight.",
            legal_context=legal_context or "Khong co van ban phap ly phu hop.",
        )
        text = self.llm_client.generate(prompt, max_new_tokens=256).strip()
        sections = _extract_sections(text)

        legal_basis = _parse_list_section(sections.get("legal_basis", "")) or _build_legal_basis_refs(
            legal_articles
        )
        missing_information = _parse_list_section(
            sections.get("missing_information", "")
        ) or _build_missing_information(enterprise_profile)
        recommendation = sections.get("recommendation", "").strip() or risk_assessment.recommendation
        risk_overview = sections.get("risk_overview", "").strip() or risk_assessment.summary
        suggested_actions = _parse_list_section(
            sections.get("suggested_actions", "")
        ) or _build_suggested_actions(risk_assessment)
        summary = _build_summary(recommendation, risk_overview)
        key_reasons = _build_key_reasons(enterprise_profile, risk_assessment)
        report_text = (
            text
            if len(sections) == len(_SECTION_LABELS)
            else _compose_report_text(
                risk_overview=risk_overview,
                legal_basis=legal_basis,
                missing_information=missing_information,
                recommendation=recommendation,
                suggested_actions=suggested_actions,
            )
        )

        return AdvisoryReport(
            recommendation=recommendation,
            summary=summary,
            risk_overview=risk_overview,
            legal_basis=legal_basis,
            key_reasons=key_reasons,
            missing_information=missing_information,
            suggested_actions=suggested_actions,
            report_text=report_text,
        )
