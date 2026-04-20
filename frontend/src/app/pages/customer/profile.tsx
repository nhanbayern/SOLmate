import { useNavigate, Link } from "react-router";
import { useEffect, useState } from "react";
import CustomerLayout from "../../components/customer-layout";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { PlusCircle, FileText, Loader2, CheckCircle, Clock } from "lucide-react";
import { authMe } from "../../lib/api";
import { translateIndustry, translateBusinessType } from "../../lib/termMapping";

const ROLE_VI: Record<string, string> = {
  MERCHANT: "Thương nhân / Hộ kinh doanh",
  ADMIN: "Quản trị viên",
  BANKER: "Nhân viên ngân hàng",
  CUSTOMER: "Khách hàng",
};


function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="py-2 border-b border-border last:border-0">
      <span className="text-xs text-muted-foreground block mb-0.5">{label}</span>
      <span className="font-medium text-sm">{value}</span>
    </div>
  );
}

export default function CustomerProfile() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<any>(() => {
    // Read cached profile from login response — instant, no spinner
    try {
      const cached = localStorage.getItem("customerProfile");
      return cached ? JSON.parse(cached) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(false); // no loading if cache hit

  useEffect(() => {
    const token = localStorage.getItem("customerLoggedIn");
    if (!token) {
      navigate("/customer/login");
      return;
    }

    // Silent background refresh from GET /api/auth/me
    authMe()
      .then((res) => {
        const inner = res?.data ?? res;
        setProfile(inner);
        // Update cache with fresh data
        localStorage.setItem("customerProfile", JSON.stringify(inner));
      })
      .catch((err) => console.error("[Profile] authMe error:", err));
  }, [navigate]);

  if (loading) {
    return (
      <CustomerLayout>
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </CustomerLayout>
    );
  }

  const merchant = profile?.merchant ?? {};
  const kycVerified = merchant.kyc_status === "VERIFIED";
  const accountActive = profile?.status === "ACTIVE";

  return (
    <CustomerLayout>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-foreground">Hồ sơ của tôi</h1>
          <p className="text-muted-foreground">Thông tin tài khoản và doanh nghiệp của bạn</p>
        </div>

        {/* Quick Actions */}
        <div className="flex gap-4 flex-wrap">
          <Link to="/customer/create-loan">
            <Button size="lg" className="gap-2">
              <PlusCircle className="w-5 h-5" />
              Tạo yêu cầu vay mới
            </Button>
          </Link>
          <Link to="/customer/loans">
            <Button size="lg" variant="outline" className="gap-2">
              <FileText className="w-5 h-5" />
              Xem danh sách yêu cầu vay
            </Button>
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Account Info */}
          <Card>
            <CardHeader>
              <CardTitle>Thông tin tài khoản</CardTitle>
            </CardHeader>
            <CardContent className="space-y-0">
              <InfoRow label="ID người dùng" value={
                <span className="font-mono">{profile?.user_id ?? "—"}</span>
              } />
              <InfoRow label="Mã khách hàng" value={
                <span className="font-mono">{profile?.customer_id ?? "—"}</span>
              } />
              <InfoRow label="Mã đơn vị kinh doanh" value={
                <span className="font-mono">{profile?.merchant_id ?? "—"}</span>
              } />
              <InfoRow label="Vai trò" value={ROLE_VI[profile?.role] ?? profile?.role ?? "—"} />
              <InfoRow label="Trạng thái tài khoản" value={
                <Badge className={accountActive
                  ? "bg-green-100 text-green-800"
                  : "bg-gray-100 text-gray-600"
                }>
                  {accountActive ? "Đang hoạt động" : (profile?.status ?? "—")}
                </Badge>
              } />
            </CardContent>
          </Card>

          {/* Merchant / Business Info */}
          <Card>
            <CardHeader>
              <CardTitle>Thông tin doanh nghiệp</CardTitle>
            </CardHeader>
            <CardContent className="space-y-0">
              <InfoRow label="Tên doanh nghiệp / cửa hàng" value={merchant.name ?? "—"} />
              <InfoRow label="Chủ doanh nghiệp" value={merchant.owner_name ?? "—"} />
              <InfoRow label="Ngành nghề" value={translateIndustry(merchant.industry ?? "")} />
              <InfoRow label="Loại hình kinh doanh" value={translateBusinessType(merchant.business_type ?? "")} />
              <InfoRow label="Số năm hoạt động" value={
                merchant.years_in_business != null
                  ? `${merchant.years_in_business} năm`
                  : "—"
              } />
              <InfoRow label="Trạng thái định danh (KYC)" value={
                <span className="inline-flex items-center gap-1">
                  {kycVerified
                    ? <><CheckCircle className="w-3.5 h-3.5 text-green-600" /> <span className="text-green-700 font-semibold">Đã xác minh</span></>
                    : <><Clock className="w-3.5 h-3.5 text-yellow-600" /> <span className="text-yellow-700">{merchant.kyc_status ?? "—"}</span></>
                  }
                </span>
              } />
            </CardContent>
          </Card>
        </div>

        {/* Info card */}
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-4 pb-4 text-sm text-blue-800 space-y-1">
            <p>• Thông tin doanh nghiệp được cập nhật từ hệ thống SOLmate sau khi hoàn tất xác minh KYC.</p>
            <p>• Để thay đổi thông tin, vui lòng liên hệ nhân viên ngân hàng hỗ trợ bạn.</p>
          </CardContent>
        </Card>
      </div>
    </CustomerLayout>
  );
}
