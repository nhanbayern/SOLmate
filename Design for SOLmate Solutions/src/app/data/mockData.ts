// Mock data for SOLmate SOLUTIONS

import customerMetricsCsv from '@mockdata/sme_loan_customers_10_from_random_transaction.csv?raw';
import transactionCsv from '@mockdata/random_transaction_10_firms.csv?raw';
import loanSamplesCsv from '@mockdata/sme_loan_customers_30000_samples_with_loan_type.csv?raw';

export const mockLoanSamplesCsvRaw = loanSamplesCsv;

export interface CustomerMetrics {
  customer_id: string;
  merchant_id: string;
  name: string;
  age: number;
  industry: string;
  business_type: string;
  years_in_business: number;
  location: string;
  created_at: string;
  Revenue_mean_30d: number;
  Revenue_mean_90d: number;
  Txn_frequency: number;
  regime: string;
  Growth_value: number;
  Growth_score: number;
  CV_value: number;
  CV_score: number;
  Spike_ratio: number;
  Spike_score: number;
  Txn_freq_score: number;
  Years_score: number;
  Industry_score: number;
  CIC_SCORE: number;
  label: string;
  label_quantile: string;
  label_cic_range: string;
  default_probability: number;
  loan_type?: string;
}

export interface Transaction {
  customer_id: string;
  merchant_id: string;
  name: string;
  age: number;
  industry: string;
  business_type: string;
  years_in_business: number;
  location: string;
  created_at: string;
  Status: string;
  Amount: number;
  Time: string;
  Date: string;
  'Beneficiary Account': string;
  'Beneficiary Name': string;
  'Beneficiary Bank': string;
  'Transfer Content': string;
  'Reference Code': string;
  'Transaction Code': string;
  'ID hóa đơn': string;
  'Tổng giá': number;
}

export interface LoanPurpose {
  code: string;
  name: string;
  description: string;
}

export interface LoanRequest {
  request_id: string;
  customer_id: string;
  merchant_id: string;
  purpose: string;
  requested_amount: number;
  currency: string;
  status: 'SUBMITTED' | 'IN_REVIEW' | 'APPROVED' | 'REJECTED';
  created_at: string;
  updated_at: string;
  decision_note?: string;
}

export interface AIRecommendation {
  customer_id: string;
  report_text_user: string;
  report_text_bank: string;
}

const legacyLoanPurposeCatalog: LoanPurpose[] = [
  {
    code: 'working_capital',
    name: 'Vay vốn lưu động',
    description: 'Khoản vay ngắn hạn phục vụ hoạt động kinh doanh hàng ngày',
  },
  {
    code: 'merchant_cash_advance',
    name: 'Ứng tiền theo doanh thu (MCA)',
    description: 'Ứng trước tiền dựa trên doanh thu POS tương lai',
  },
  {
    code: 'revolving_credit',
    name: 'Hạn mức tín dụng quay vòng',
    description: 'Cấp hạn mức dựa trên dòng tiền ổn định',
  },
  {
    code: 'revenue_based_financing',
    name: 'Tài trợ theo doanh thu',
    description: 'Khoản vay được hoàn trả theo tỷ lệ % trên doanh thu',
  },
  {
    code: 'micro_sme_loan',
    name: 'Khoản vay SME nhỏ',
    description: 'Khoản vay quy mô nhỏ cho hộ kinh doanh',
  },
];

const legacyLoanTypeOverrides: Record<string, string> = {
  CUST_20331909: 'Vay vốn lưu động',
  CUST_33291822: 'Hạn mức tín dụng quay vòng',
  CUST_41001495: 'Ứng tiền theo doanh thu (MCA)',
  CUST_49058415: 'Khoản vay SME nhỏ',
  CUST_70314034: 'Hạn mức tín dụng quay vòng',
};

const legacyLoanRequestsByCustomerId: Record<string, LoanRequest> = {
  CUST_20331909: {
    request_id: 'REQ_001',
    customer_id: 'CUST_20331909',
    merchant_id: 'MER_77698148',
    purpose: 'working_capital',
    requested_amount: 50000000,
    currency: 'VND',
    status: 'IN_REVIEW',
    created_at: '2026-04-10T10:30:00Z',
    updated_at: '2026-04-10T10:30:00Z',
  },
  CUST_33291822: {
    request_id: 'REQ_002',
    customer_id: 'CUST_33291822',
    merchant_id: 'MER_25509610',
    purpose: 'revolving_credit',
    requested_amount: 80000000,
    currency: 'VND',
    status: 'SUBMITTED',
    created_at: '2026-04-12T14:20:00Z',
    updated_at: '2026-04-12T14:20:00Z',
  },
  CUST_41001495: {
    request_id: 'REQ_003',
    customer_id: 'CUST_41001495',
    merchant_id: 'MER_68620564',
    purpose: 'merchant_cash_advance',
    requested_amount: 100000000,
    currency: 'VND',
    status: 'APPROVED',
    created_at: '2026-04-08T09:15:00Z',
    updated_at: '2026-04-09T16:45:00Z',
    decision_note: 'Hồ sơ tốt, doanh thu ổn định, phê duyệt hạn mức 100,000,000 VND',
  },
};

const legacyAIRecommendations: Record<string, AIRecommendation> = {
  CUST_20331909: {
    customer_id: 'CUST_20331909',
    report_text_user:
      '### 1. Thông tin cơ bản về doanh nghiệp\nDoanh nghiệp Lê Đức Đức, ngành Pet_Service, loại hình Sole_Proprietor, khu vực Bắc Ninh, thời gian hoạt động 2.8 năm.\n\n### 2. Tình trạng hiện tại của doanh nghiệp\nHồ sơ hiện tại cho thấy doanh nghiệp đang ở mức rủi ro trung bình (MEDIUM). Dòng tiền tương đối ổn định với doanh thu trung bình 30 ngày là 2,431,519 VND.\n\n### 3. Khả năng vay vốn hiện tại\nKhả năng được phê duyệt vay ở mức khá. Doanh nghiệp có thể xem xét vay với hạn mức phù hợp.\n\n### 4. Khuyến nghị cho doanh nghiệp\nNên duy trì tính ổn định của dòng tiền và cải thiện tần suất giao dịch để nâng cao điểm tín dụng.',
    report_text_bank:
      '### 1. Thông tin cơ bản về doanh nghiệp\nMã khách hàng CUST_20331909, tên Lê Đức Đức, ngành Pet_Service, loại hình Sole_Proprietor, Bắc Ninh, 2.8 năm hoạt động, CIC Score 565.05.\n\n### 2. Kiểm tra lại phân loại của Risk Class\nNhãn risk class là MEDIUM và được đánh giá là hợp lý. Xác suất vỡ nợ 29.3% nằm trong khoảng chấp nhận được cho nhóm MEDIUM.\n\n### 3. Tổng quan tình hình hiện tại\nDoanh nghiệp có dòng tiền ổn định với CV_score 0.478, cho thấy mức biến động chấp nhận được. Revenue trung bình 30 ngày đạt 2.43 triệu VND.\n\n### 4. Khuyến nghị cho nhân viên ngân hàng\nKhuyến nghị APPROVE với điều kiện. Hạn mức đề xuất: 50,000,000 VND. Doanh nghiệp có tiềm năng tốt nhưng cần theo dõi sát.\n\n### 5. Đề xuất hành động tiếp theo\n- Phê duyệt hạn mức 50 triệu VND\n- Yêu cầu bổ sung báo cáo tài chính định kỳ\n- Theo dõi dòng tiền hàng tháng',
  },
  CUST_33291822: {
    customer_id: 'CUST_33291822',
    report_text_user:
      '### 1. Thông tin cơ bản về doanh nghiệp\nDoanh nghiệp Đặng Quang Huy Nam, ngành Fresh_Market_Trading, loại hình Sole_Proprietor, khu vực Cần Thơ, thời gian hoạt động 1.4 năm.\n\n### 2. Tình trạng hiện tại của doanh nghiệp\nHồ sơ hiện tại cho thấy doanh nghiệp đang ở mức rủi ro cao (POOR). Cần cải thiện các chỉ số tài chính.\n\n### 3. Khả năng vay vốn hiện tại\nKhả năng được phê duyệt vay hiện tại thấp. Đề nghị cải thiện hồ sơ trước khi nộp lại.\n\n### 4. Khuyến nghị cho doanh nghiệp\nCần tập trung cải thiện tính ổn định dòng tiền và giảm biến động doanh thu.',
    report_text_bank:
      '### 1. Thông tin cơ bản về doanh nghiệp\nMã khách hàng CUST_33291822, tên Đặng Quang Huy Nam, ngành Fresh_Market_Trading, Cần Thơ, 1.4 năm hoạt động, CIC Score 420.61.\n\n### 2. Kiểm tra lại phân loại của Risk Class\nNhãn risk class là POOR. Xác suất vỡ nợ 52% là mức rủi ro cao.\n\n### 3. Tổng quan tình hình hiện tại\nRegime HIGH_RISK. CV_value cao cho thấy biến động dòng tiền đáng lo ngại.\n\n### 4. Khuyến nghị cho nhân viên ngân hàng\nKhuyến nghị REJECT hoặc yêu cầu bổ sung tài sản đảm bảo. Nếu phê duyệt, hạn mức tối đa 30,000,000 VND với lãi suất điều chỉnh theo rủi ro.\n\n### 5. Đề xuất hành động tiếp theo\n- Yêu cầu bổ sung tài sản đảm bảo\n- Rà soát lịch sử thanh toán\n- Đề nghị khách hàng cải thiện hồ sơ trong 3-6 tháng',
  },
};

function parseCsvLine(line: string): string[] {
  const fields: string[] = [];
  let currentField = '';
  let insideQuotes = false;

  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];

    if (character === '"') {
      const nextCharacter = line[index + 1];
      if (insideQuotes && nextCharacter === '"') {
        currentField += '"';
        index += 1;
      } else {
        insideQuotes = !insideQuotes;
      }
      continue;
    }

    if (character === ',' && !insideQuotes) {
      fields.push(currentField);
      currentField = '';
      continue;
    }

    currentField += character;
  }

  fields.push(currentField);
  return fields.map((field) => field.trim());
}

function parseCsvRecords(csvText: string): Record<string, string>[] {
  const normalizedText = csvText.replace(/^\uFEFF/, '').trim();

  if (!normalizedText) {
    return [];
  }

  const [headerLine, ...dataLines] = normalizedText.split(/\r?\n/);
  const headers = parseCsvLine(headerLine);

  return dataLines
    .filter((line) => line.trim().length > 0)
    .map((line) => {
      const values = parseCsvLine(line);
      return headers.reduce<Record<string, string>>((record, header, index) => {
        record[header] = values[index] ?? '';
        return record;
      }, {});
    });
}

function toNumber(value: string | undefined): number {
  const parsedValue = Number.parseFloat(value ?? '0');
  return Number.isFinite(parsedValue) ? parsedValue : 0;
}

function normalizeScientificInteger(value: string | undefined): string {
  if (!value) {
    return '';
  }

  const parsedValue = Number(value);
  if (!Number.isFinite(parsedValue)) {
    return value;
  }

  return Math.trunc(parsedValue).toString();
}

function slugify(value: string): string {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .toLowerCase();
}

function parseCustomerMetricsRecords(csvText: string): CustomerMetrics[] {
  return parseCsvRecords(csvText).map((record) => ({
    customer_id: record.customer_id,
    merchant_id: record.merchant_id,
    name: record.name,
    age: toNumber(record.age),
    industry: record.industry,
    business_type: record.business_type,
    years_in_business: toNumber(record.years_in_business),
    location: record.location,
    created_at: record.created_at,
    Revenue_mean_30d: toNumber(record.Revenue_mean_30d),
    Revenue_mean_90d: toNumber(record.Revenue_mean_90d),
    Txn_frequency: toNumber(record.Txn_frequency),
    regime: record.regime,
    Growth_value: toNumber(record.Growth_value),
    Growth_score: toNumber(record.Growth_score),
    CV_value: toNumber(record.CV_value),
    CV_score: toNumber(record.CV_score),
    Spike_ratio: toNumber(record.Spike_ratio),
    Spike_score: toNumber(record.Spike_score),
    Txn_freq_score: toNumber(record.Txn_freq_score),
    Years_score: toNumber(record.Years_score),
    Industry_score: toNumber(record.Industry_score),
    CIC_SCORE: toNumber(record.CIC_SCORE),
    label: record.label,
    label_quantile: record.label_quantile,
    label_cic_range: record.label_cic_range,
    default_probability: toNumber(record.default_probability),
    loan_type: record.loan_type?.trim() || undefined,
  }));
}

function parseTransactionsRecords(csvText: string): Transaction[] {
  return parseCsvRecords(csvText).map((record) => ({
    customer_id: record.customer_id,
    merchant_id: record.merchant_id,
    name: record.name,
    age: toNumber(record.age),
    industry: record.industry,
    business_type: record.business_type,
    years_in_business: toNumber(record.years_in_business),
    location: record.location,
    created_at: record.created_at,
    Status: record.Status,
    Amount: toNumber(record.Amount),
    Time: record.Time,
    Date: record.Date,
    'Beneficiary Account': normalizeScientificInteger(record['Beneficiary Account']),
    'Beneficiary Name': record['Beneficiary Name'],
    'Beneficiary Bank': record['Beneficiary Bank'],
    'Transfer Content': record['Transfer Content'],
    'Reference Code': record['Reference Code'],
    'Transaction Code': record['Transaction Code'],
    'ID hóa đơn': record['ID hóa đơn'],
    'Tổng giá': toNumber(record['Tổng giá']),
  }));
}

function getLoanPurposeDescription(name: string): string {
  const descriptions: Record<string, string> = {
    'Vay vốn lưu động': 'Khoản vay ngắn hạn phục vụ hoạt động kinh doanh hàng ngày',
    'Ứng tiền theo doanh thu (MCA)': 'Ứng trước tiền dựa trên doanh thu POS tương lai',
    'Hạn mức tín dụng quay vòng': 'Cấp hạn mức dựa trên dòng tiền ổn định',
    'Tài trợ theo doanh thu': 'Khoản vay được hoàn trả theo tỷ lệ % trên doanh thu',
    'Khoản vay SME nhỏ': 'Khoản vay quy mô nhỏ cho hộ kinh doanh',
  };

  return descriptions[name] ?? 'Khoản vay được tạo từ dữ liệu mockdata';
}

function calculateRequestedAmount(customer: CustomerMetrics): number {
  const multiplierByRisk: Record<string, number> = {
    VERY_GOOD: 14,
    GOOD: 12,
    MEDIUM: 10,
    POOR: 8,
    VERY_POOR: 6,
  };

  const multiplier = multiplierByRisk[customer.label] ?? 10;
  const rawAmount = customer.Revenue_mean_30d * multiplier;
  const roundedAmount = Math.round(rawAmount / 5000000) * 5000000;
  return Math.max(10000000, roundedAmount);
}

function inferLoanStatus(customer: CustomerMetrics): LoanRequest['status'] {
  switch (customer.label) {
    case 'VERY_GOOD':
      return 'APPROVED';
    case 'GOOD':
    case 'MEDIUM':
      return 'IN_REVIEW';
    case 'POOR':
    case 'VERY_POOR':
      return 'REJECTED';
    default:
      return 'SUBMITTED';
  }
}

function buildDecisionNote(customer: CustomerMetrics, requestedAmount: number, status: LoanRequest['status']): string | undefined {
  if (status === 'APPROVED') {
    return `Hồ sơ đủ điều kiện theo dữ liệu mockdata, đề xuất hạn mức ${formatCurrency(requestedAmount)}`;
  }

  if (status === 'REJECTED') {
    return 'Dữ liệu mockdata cho thấy rủi ro cao, tạm thời chưa đề xuất phê duyệt';
  }

  if (customer.label === 'MEDIUM') {
    return 'Hồ sơ đang được theo dõi thêm trước khi ra quyết định cuối cùng';
  }

  return undefined;
}

const baseCustomerMetrics = parseCustomerMetricsRecords(customerMetricsCsv);
const loanSampleRows = parseCsvRecords(loanSamplesCsv);
const loanTypeByCustomerId = new Map<string, string>();
const loanPurposeNames = new Set<string>();

for (const purpose of legacyLoanPurposeCatalog) {
  loanPurposeNames.add(purpose.name);
}

for (const row of loanSampleRows) {
  const customerId = row.customer_id?.trim();
  const loanType = row.loan_type?.trim();

  if (customerId && loanType) {
    loanTypeByCustomerId.set(customerId, loanType);
    loanPurposeNames.add(loanType);
  }
}

export const mockCustomerMetrics: CustomerMetrics[] = baseCustomerMetrics.map((customer) => ({
  ...customer,
  loan_type:
    legacyLoanTypeOverrides[customer.customer_id] ?? loanTypeByCustomerId.get(customer.customer_id) ?? customer.loan_type,
}));

export const mockTransactions: Transaction[] = parseTransactionsRecords(transactionCsv);

export const mockLoanPurposes: LoanPurpose[] = Array.from(loanPurposeNames).map((name) => {
  const legacyPurpose = legacyLoanPurposeCatalog.find((purpose) => purpose.name === name);

  if (legacyPurpose) {
    return legacyPurpose;
  }

  return {
    code: slugify(name),
    name,
    description: getLoanPurposeDescription(name),
  };
});

const loanPurposeNameByCode = new Map(mockLoanPurposes.map((purpose) => [purpose.code, purpose.name]));

export function getLoanPurposeLabel(purpose: string): string {
  return loanPurposeNameByCode.get(purpose) ?? purpose.replace(/_/g, ' ');
}

const loanCustomers = mockCustomerMetrics.filter((customer) => customer.loan_type);
const generatedLoanRequests: LoanRequest[] = [];

for (const customer of loanCustomers) {
  const legacyRequest = legacyLoanRequestsByCustomerId[customer.customer_id];

  if (legacyRequest) {
    generatedLoanRequests.push(legacyRequest);
    continue;
  }

  const requestedAmount = calculateRequestedAmount(customer);
  const status = inferLoanStatus(customer);

  generatedLoanRequests.push({
    request_id: `REQ_${customer.customer_id}`,
    customer_id: customer.customer_id,
    merchant_id: customer.merchant_id,
    purpose: slugify(customer.loan_type ?? customer.customer_id),
    requested_amount: requestedAmount,
    currency: 'VND',
    status,
    created_at: customer.created_at,
    updated_at: customer.created_at,
    decision_note: buildDecisionNote(customer, requestedAmount, status),
  });
}

export const mockLoanRequests: LoanRequest[] = generatedLoanRequests;

export const mockAIRecommendations: Record<string, AIRecommendation> = legacyAIRecommendations;

// Helper function to get risk label color
export function getRiskLabelColor(label: string): string {
  switch (label) {
    case 'GOOD':
    case 'VERY_GOOD':
      return 'bg-green-100 text-green-800';
    case 'MEDIUM':
      return 'bg-yellow-100 text-yellow-800';
    case 'POOR':
      return 'bg-orange-100 text-orange-800';
    case 'VERY_POOR':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

// Helper function to get status color
export function getStatusColor(status: string): string {
  switch (status) {
    case 'SUBMITTED':
      return 'bg-blue-100 text-blue-800';
    case 'IN_REVIEW':
      return 'bg-yellow-100 text-yellow-800';
    case 'APPROVED':
      return 'bg-green-100 text-green-800';
    case 'REJECTED':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

// Format currency
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND'
  }).format(amount);
}

// Format percentage
export function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}
