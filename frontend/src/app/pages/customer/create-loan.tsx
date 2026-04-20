import { useNavigate } from "react-router";
import { useEffect, useState } from "react";
import CustomerLayout from "../../components/customer-layout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { CheckCircle, Loader2 } from "lucide-react";
import { createCustomerLoan } from "../../lib/api";

// Loan types accepted by server (from Swagger CreateLoanRequest example + apidocs.yaml)
const LOAN_TYPES = [
  "Khoản vay SME nhỏ",
  "Hạn mức tín dụng quay vòng",
  "Tài trợ hóa đơn đơn giản",
  "Ứng tiền theo doanh thu (MCA)",
];

export default function CustomerCreateLoan() {
  const navigate = useNavigate();

  const [loanType, setLoanType] = useState("");
  const [requestedAmount, setRequestedAmount] = useState("");
  const [merchantId, setMerchantId] = useState("");
  const [merchantName, setMerchantName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("customerLoggedIn");
    if (!token) {
      navigate("/customer/login");
      return;
    }

    try {
      const profileStr = localStorage.getItem("customerProfile");
      if (profileStr) {
        const profile = JSON.parse(profileStr);
        if (profile?.merchant?.id) {
          setMerchantId(profile.merchant.id);
          setMerchantName(profile.merchant.name || profile.merchant.owner_name || profile.merchant.id);
        }
      }
    } catch (e) {
      console.error("Failed to parse customer profile");
    }
  }, [navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!loanType || !requestedAmount || !merchantId) {
      setError("Vui lòng điền đầy đủ thông tin");
      return;
    }

    try {
      setSubmitting(true);
      // POST /api/customer/loans
      await createCustomerLoan({
        merchant_id: merchantId,
        loan_type: loanType,
        requested_amount: parseFloat(requestedAmount),
      });
      setSubmitted(true);
      setTimeout(() => navigate("/customer/loans"), 2000);
    } catch (err: any) {
      setError(err.message || "Gửi yêu cầu thất bại");
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <CustomerLayout>
        <div className="p-6 flex items-center justify-center min-h-[calc(100vh-4rem)]">
          <Card className="w-full max-w-md text-center">
            <CardContent className="pt-12 pb-12">
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2">Gửi yêu cầu thành công!</h2>
              <p className="text-muted-foreground mb-4">
                Yêu cầu vay của bạn đã được gửi. Chúng tôi sẽ xem xét và phản hồi trong thời gian sớm nhất.
              </p>
              <p className="text-sm text-muted-foreground">Đang chuyển hướng...</p>
            </CardContent>
          </Card>
        </div>
      </CustomerLayout>
    );
  }

  return (
    <CustomerLayout>
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Tạo yêu cầu vay</h1>
          <p className="text-muted-foreground">Điền thông tin để gửi yêu cầu vay mới</p>
        </div>

        <div className="max-w-2xl">
          <Card>
            <CardHeader>
              <CardTitle>Thông tin yêu cầu vay</CardTitle>
              <CardDescription>Vui lòng điền đầy đủ thông tin dưới đây</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Merchant info (read-only) */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">
                    Merchant / Cơ sở kinh doanh
                  </label>
                  <div className="flex h-10 w-full rounded-md border border-input bg-muted px-3 py-2 text-sm text-muted-foreground opacity-100 items-center">
                    {merchantName ? `${merchantName} (${merchantId})` : "Không tìm thấy thông tin merchant"}
                  </div>
                  <p className="text-xs text-muted-foreground">Thông tin cơ sở kinh doanh được tự động điền từ hồ sơ của bạn.</p>
                </div>

                {/* Loan type */}
                <div className="space-y-2">
                  <label htmlFor="loanType" className="text-sm font-medium">
                    Loại vay <span className="text-destructive">*</span>
                  </label>
                  <select
                    id="loanType"
                    className="flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={loanType}
                    onChange={(e) => setLoanType(e.target.value)}
                    required
                  >
                    <option value="">Chọn loại vay</option>
                    {LOAN_TYPES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>

                {/* Requested amount */}
                <div className="space-y-2">
                  <label htmlFor="amount" className="text-sm font-medium">
                    Số tiền đề nghị vay (VND) <span className="text-destructive">*</span>
                  </label>
                  <Input
                    id="amount"
                    type="number"
                    placeholder="Ví dụ: 50000000"
                    value={requestedAmount}
                    onChange={(e) => setRequestedAmount(e.target.value)}
                    required
                    min="1000000"
                    step="1000000"
                  />
                  <p className="text-xs text-muted-foreground">Số tiền tối thiểu: 1,000,000 VND</p>
                </div>

                {error && <p className="text-sm text-destructive">{error}</p>}

                <div className="flex gap-4">
                  <Button type="submit" size="lg" className="flex-1" disabled={submitting}>
                    {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Gửi yêu cầu vay
                  </Button>
                  <Button
                    type="button"
                    size="lg"
                    variant="outline"
                    onClick={() => navigate("/customer/loans")}
                  >
                    Hủy
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          <Card className="mt-6 bg-amber-50 border-amber-200">
            <CardHeader>
              <CardTitle className="text-amber-900">Lưu ý quan trọng</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-amber-800 space-y-2">
              <p>• Yêu cầu vay sẽ được xem xét dựa trên điểm tín dụng và lịch sử giao dịch của bạn.</p>
              <p>• Thời gian xét duyệt thường từ 1-3 ngày làm việc.</p>
              <p>• Bạn có thể theo dõi trạng thái yêu cầu trong mục "Danh sách yêu cầu vay".</p>
              <p>• Hệ thống AI sẽ tự động phân tích và đưa ra khuyến nghị cho ngân hàng.</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </CustomerLayout>
  );
}
