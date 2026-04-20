/**
 * Term mapping: English technical terms from agent output → Vietnamese display labels
 * Apply via applyTermMapping(text) before rendering agent report text.
 */

// ─── Business type mapping ────────────────────────────────────────────────────
export const BUSINESS_TYPE_VI_MAP: Record<string, string> = {
  Household_Business: "Hộ kinh doanh nhỏ (mới thành lập)",
  Sole_Proprietor: "Hộ kinh doanh cá thể",
  Micro_SME: "Doanh nghiệp siêu nhỏ",
};

// ─── Industry mapping ─────────────────────────────────────────────────────────
export const INDUSTRY_VI_MAP: Record<string, string> = {
  // LOW_RISK
  Food_and_Beverage: "Ẩm thực - ăn uống",
  Street_Food: "Đồ ăn đường phố",
  Coffee_Shop: "Quán cà phê",
  Grocery_Store: "Cửa hàng tạp hóa",
  Convenience_Store: "Cửa hàng tiện lợi",
  Pharmacy: "Nhà thuốc",
  // MEDIUM_RISK
  Clothing_Retail: "Bán lẻ quần áo",
  Cosmetics_Retail: "Bán lẻ mỹ phẩm",
  Phone_Accessories: "Phụ kiện điện thoại",
  Stationery_Shop: "Cửa hàng văn phòng phẩm",
  Pet_Service: "Dịch vụ thú cưng",
  // SERVICE_RISK
  Hair_Salon: "Tiệm cắt tóc",
  Beauty_Spa: "Spa làm đẹp",
  Laundry_Service: "Giặt ủi",
  Printing_Service: "In ấn",
  // TECHNICAL_RISK
  Electronics_Repair: "Sửa chữa điện tử",
  Motorbike_Repair: "Sửa xe máy",
  // HIGH_RISK
  Transportation_Service: "Vận tải",
  Construction_Service: "Xây dựng",
  Agriculture_Trading: "Buôn bán nông sản",
  Livestock_Trading: "Buôn bán chăn nuôi",
  // TRADE_RISK
  Wholesale_Trading: "Bán buôn",
  Fresh_Market_Trading: "Kinh doanh chợ tươi",
  Online_Selling: "Bán hàng online",
  // ASSET_BASED
  Home_Rental: "Cho thuê nhà",
};

/** Translate a business_type value from server → Vietnamese */
export function translateBusinessType(value: string): string {
  return BUSINESS_TYPE_VI_MAP[value] ?? value.replace(/_/g, " ");
}

/** Translate an industry value from server → Vietnamese */
export function translateIndustry(value: string): string {
  return INDUSTRY_VI_MAP[value] ?? value.replace(/_/g, " ");
}

const TERM_MAP: Record<string, string> = {
  // ── Enterprise Profile ───────────────────────────────────────────────────
  customer_id: "Mã khách hàng",
  owner_name: "Tên doanh nghiệp/chủ hộ",
  industry: "Ngành",
  business_type: "Loại hình kinh doanh",
  years_in_business: "Thời gian hoạt động",
  credit_score: "Điểm tín dụng",

  // Business types (from BUSINESS_TYPE_VI_MAP)
  ...BUSINESS_TYPE_VI_MAP,

  // Industries (from INDUSTRY_VI_MAP)
  ...INDUSTRY_VI_MAP,

  // ── Risk Class & Validation ──────────────────────────────────────────────
  risk_class: "Nhóm rủi ro",
  input_risk_class: "Nhãn rủi ro đầu vào",
  VERY_HIGH: "Rất cao",
  MEDIUM: "Trung bình",
  expected_risk_class: "Nhóm rủi ro kỳ vọng",
  not_reasonable: "Không hợp lý",

  // ── Probability ──────────────────────────────────────────────────────────
  probability: "Xác suất",
  input_probability: "Xác suất đầu vào",
  expected_probability: "Xác suất kỳ vọng",
  probability_range: "Khoảng xác suất",
  default_probability: "Xác suất vỡ nợ",

  // ── Rules ────────────────────────────────────────────────────────────────
  credit_score_rule: "Quy tắc điểm tín dụng",
  UNKNOWN: "Không xác định",
  REVIEW_REQUIRED: "Cần thẩm định",

  // ── Metrics (POS behavior) ───────────────────────────────────────────────
  regime: "Trạng thái vận hành",
  VERY_POOR: "Rất yếu",
  Txn_frequency: "Tần suất giao dịch",
  Spike_ratio: "Tỷ lệ đột biến doanh thu",
  Industry_score: "Điểm rủi ro ngành",
  Revenue_mean_30d: "Doanh thu trung bình 30 ngày",

  // ── Risk Analysis ────────────────────────────────────────────────────────
  risk_signal: "Tín hiệu rủi ro",
  risk_level: "Mức rủi ro",
  underestimated_risk: "Đánh giá thấp rủi ro",
  cash_flow_volatility: "Biến động dòng tiền",
  business_stability: "Độ ổn định hoạt động",
  monitoring_required: "Cần theo dõi sát",

  // ── Credit Decision ──────────────────────────────────────────────────────
  recommendation: "Khuyến nghị",
  MANUAL_REVIEW: "Thẩm định thủ công",
  credit_approval: "Phê duyệt tín dụng",
  reject: "Từ chối",
  conditional_approval: "Phê duyệt có điều kiện",
  repayment_capacity: "Khả năng trả nợ",

  // ── Loan Terms ───────────────────────────────────────────────────────────
  loan_limit: "Hạn mức tín dụng",
  proposed_loan_amount: "Hạn mức đề xuất",
  conservative: "Thận trọng",
  Conservative: "Thận trọng",
  risk_penalty: "Phạt rủi ro",
  rounding: "Làm tròn",
  nearest_threshold: "Ngưỡng gần nhất",

  // ── Actions ──────────────────────────────────────────────────────────────
  next_steps: "Hành động tiếp theo",
  review_model: "Rà soát mô hình",
  risk_labeling: "Gán nhãn rủi ro",
  financial_statements: "Báo cáo tài chính",
  bank_statement: "Sao kê ngân hàng",
  outstanding_debt: "Dư nợ hiện tại",
  revenue_verification: "Xác minh doanh thu",
  collateral: "Tài sản bảo đảm",
  loan_purpose: "Mục đích vay",
  credit_history: "Lịch sử tín dụng",
};

// Sort longest-key-first so longer terms match before shorter substrings
const SORTED_KEYS = Object.keys(TERM_MAP).sort((a, b) => b.length - a.length);


/**
 * Replace all known technical English terms in the agent output text with
 * their Vietnamese equivalents. Matches whole-word occurrences only to
 * avoid partial replacements (e.g. "regime" inside "regime_score").
 */
export function applyTermMapping(text: string): string {
  let result = text;
  for (const key of SORTED_KEYS) {
    // Match the key as a whole word (boundary: non-alphanumeric/underscore on each side)
    const escaped = key.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const regex = new RegExp(`(?<![\\w_])${escaped}(?![\\w_])`, "g");
    result = result.replace(regex, TERM_MAP[key]);
  }
  return result;
}
