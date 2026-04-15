from pydantic import BaseModel, Field

from app.schemas.models import QueryVariant, RetrievalResult


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

# Kết quả đầu ra của LoanRiskEngine sau khi đánh giá rủi ro dựa trên profile doanh nghiệp, điểm tín dụng và các chỉ số CIC khác.
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
    advisory_query: str #Đây là truy vấn được tạo ra từ kết quả đánh giá rủi ro để đi tìm căn cứ pháp lý và nội dung tư vấn tiếp theo

# Là báo cáo tư vấn được viết ra sau khi hệ thống tra cứu tài liệu pháp lý
class AdvisoryReport(BaseModel):
    recommendation: str
    summary: str
    risk_overview: str
    legal_basis: list[str] = Field(default_factory=list)
    key_reasons: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    report_text: str

# Là object tổng hợp cuối cùng của toàn bộ quy trình.
class LoanAdvisoryResult(BaseModel):
    enterprise_profile: EnterpriseProfile
    risk_assessment: RiskAssessmentResult
    advisory_query: str
    rewritten_query: str
    query_variant: QueryVariant
    legal_references: list[RetrievalResult] = Field(default_factory=list)
    report: AdvisoryReport
