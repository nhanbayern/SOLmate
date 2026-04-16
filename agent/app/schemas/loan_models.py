from pydantic import BaseModel, Field


class EnterpriseProfile(BaseModel):
    customer_id: str
    merchant_id: str = ""
    name: str = ""
    age: int = 0
    industry: str = ""
    business_type: str = ""
    years_in_business: float
    location: str = ""
    created_at: str = ""


class CreditScoreRule(BaseModel):
    min_score: int = 0
    max_score: int = 0
    level: str = ""
    risk: str = ""
    decision: str = ""
    note: str = ""


class CICMetricSpec(BaseModel):
    metrics: str = ""
    value: str = ""
    note: str = ""


class RiskFactor(BaseModel):
    name: str = ""
    value: str = ""
    note: str = ""


class EnterpriseCICMetrics(BaseModel):
    customer_id: str = ""
    credit_score: float = 0.0
    metrics: dict[str, str | float] = Field(default_factory=dict)
    risk_class: str
    risk_probability: float = 0.0
    top_risk_factors: list[RiskFactor] = Field(default_factory=list)


class RiskAssessmentResult(BaseModel):
    customer_id: str
    credit_score: float
    matched_rule: CreditScoreRule
    risk_class: str
    risk_probability: float
    recommendation: str
    summary: str
    metric_insights: list[RiskFactor] = Field(default_factory=list)
    top_risk_factors: list[RiskFactor] = Field(default_factory=list)


class RiskReasonablenessReview(BaseModel):
    provided_risk_class: str
    expected_risk_class: str
    provided_risk_probability: float
    expected_risk_probability: float
    expected_probability_band: str
    risk_class_is_reasonable: bool
    risk_probability_is_reasonable: bool
    reviewed_recommendation: str = ""
    findings: list[str] = Field(default_factory=list)


class RiskReviewResult(BaseModel):
    enterprise_profile: EnterpriseProfile
    risk_assessment: RiskAssessmentResult
    review: RiskReasonablenessReview
    enterprise_overview: str
    current_overview: str
    bank_advice: str
    next_actions: list[str] = Field(default_factory=list)
    report_text: str


class AdvisoryReport(BaseModel):
    recommendation: str
    summary: str
    risk_overview: str
    key_reasons: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    report_text: str


class LoanAdvisoryResult(BaseModel):
    enterprise_profile: EnterpriseProfile
    risk_assessment: RiskAssessmentResult
    report: AdvisoryReport
