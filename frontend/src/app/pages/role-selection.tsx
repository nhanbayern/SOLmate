import { Link } from "react-router";
import { Building2, User } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";

export default function RoleSelection() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex items-center justify-center p-4">
      <div className="w-full max-w-4xl">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-primary mb-3">SOLmate SOLUTIONS</h1>
          <p className="text-muted-foreground text-lg">Hệ thống quản lý vay thông minh</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <Card className="hover:shadow-lg transition-shadow border-2 hover:border-primary">
            <CardHeader className="text-center pb-4">
              <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                <Building2 className="w-8 h-8 text-primary" />
              </div>
              <CardTitle className="text-2xl">BANKER</CardTitle>
              <CardDescription className="text-base">
                Quản lý nghiệp vụ vay và đánh giá rủi ro tín dụng
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <Link to="/banker/login">
                <Button size="lg" className="w-full">
                  Đăng nhập Banker
                </Button>
              </Link>
              <ul className="mt-4 text-sm text-muted-foreground text-left space-y-2">
                <li>• Xem Credit Risk Dashboard</li>
                <li>• Phân tích dữ liệu giao dịch</li>
                <li>• Quản lý yêu cầu vay</li>
                <li>• AI Recommendations</li>
              </ul>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow border-2 hover:border-primary">
            <CardHeader className="text-center pb-4">
              <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                <User className="w-8 h-8 text-primary" />
              </div>
              <CardTitle className="text-2xl">CUSTOMER</CardTitle>
              <CardDescription className="text-base">
                Người vay - Quản lý hồ sơ và yêu cầu vay
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <Link to="/customer/login">
                <Button size="lg" variant="outline" className="w-full">
                  Đăng nhập Customer
                </Button>
              </Link>
              <ul className="mt-4 text-sm text-muted-foreground text-left space-y-2">
                <li>• Xem hồ sơ doanh nghiệp</li>
                <li>• Tạo yêu cầu vay mới</li>
                <li>• Theo dõi trạng thái vay</li>
                <li>• Nhận khuyến nghị AI</li>
              </ul>
            </CardContent>
          </Card>
        </div>

        <div className="mt-8 text-center text-sm text-muted-foreground">
          <p>Demo Version 1.0 - Mock Data Environment</p>
        </div>
      </div>
    </div>
  );
}
