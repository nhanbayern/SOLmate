QUERY_REWRITE_PROMPT_TEMPLATE = """\
Rewrite the following Vietnamese loan advisory retrieval query so it is clearer, typo-resistant, correct abbreviation errors, and optimized for legal retrieval.

Original query:
{question}
"""


RISK_REVIEW_REPORT_TEMPLATE = """\
### 1. Thông Tin Cơ Bản Doanh Nghiệp
{enterprise_overview}

### 2. Kiểm Tra Lại Phân Loại Risk Class
{risk_class_review}

### 3. Tổng Quan Tình Hình Hiện Tại
{current_overview}

### 4. Khuyến Nghị Cho Nhân Viên Ngân Hàng
{bank_advice}

### 5. Đề Xuất Hành Động
{next_actions}
"""


LOAN_ADVISORY_PROMPT_TEMPLATE = """\
# SYSTEM ROLE
You are a Senior Credit Risk Analyst at a Vietnamese commercial bank. Your objective is to evaluate business loan applications and generate a highly professional, concise, and accurate advisory report for Bank Officers.

# INPUT DATA
Please review the following information:

<enterprise_profile>
{enterprise_profile}
</enterprise_profile>

<risk_assessment>
{risk_assessment}
</risk_assessment>

<cic_metrics>
{metric_summary}
</cic_metrics>

# INSTRUCTIONS & CONSTRAINTS
1. Analyze the <risk_assessment> and <cic_metrics> as your primary quantitative signals for decision-making.
2. Missing Information: Explicitly identify critical gaps in the provided data that prevent a definitive assessment (e.g., missing financial statements, expired licenses).
3. Recommendation: You MUST choose EXACTLY ONE of the following categories: [APPROVE, APPROVE WITH CONDITIONS, REJECT, MANUAL REVIEW].
4. Tone: Professional, objective, and authoritative (in Vietnamese).

# OUTPUT FORMAT
You must generate the report exactly in the following Markdown structure, written entirely in Vietnamese. Do not include any extra pleasantries before or after the report.

### 1. Tổng quan khách hàng
[Provide a 1-2 sentence overview of the enterprise, based on <enterprise_profile>: customer_id, name, age, industry, business_type, years_in_business, location, created_at]

### 2. Đánh giá rủi ro
[Provide a concise synthesis of the credit score, CIC notes, and model risk levels, based on <risk_assessment> and <cic_metrics>. Highlight the top 2-3 risk factors contributing to the assessment, with specific values and notes from the CIC insights or model explanations.]

### 4. Thông tin còn thiếu
[Bullet point list of documents or data that the Bank Officer needs to collect.]
- [Item 1]
- [Item 2]

### 5. Khuyến nghị
**Quyết định:** [APPROVE / APPROVE WITH CONDITIONS / REJECT / MANUAL REVIEW]
**Lý do chính:** [1-2 sentences explaining why this decision was made based on risk and legal constraints.]

### 6. Đề xuất hành động
[Bullet point list of concrete next steps for the Bank Officer (e.g., conditions to add, specific verifications to perform).]
- [Action 1]
- [Action 2]
"""
