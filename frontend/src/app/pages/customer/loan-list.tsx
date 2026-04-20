import { useNavigate, Link } from "react-router";
import { useEffect, useState } from "react";
import CustomerLayout from "../../components/customer-layout";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../../components/ui/table";
import { formatCurrency, getStatusColor, getLoanPurposeLabel } from "../../data/mockData";
import { Eye, PlusCircle, Loader2 } from "lucide-react";
import { getCustomerLoans } from "../../lib/api";

export default function CustomerLoanList() {
  const navigate = useNavigate();
  const [loans, setLoans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("customerLoggedIn");
    if (!token) {
      navigate("/customer/login");
      return;
    }

    async function load() {
      try {
        setLoading(true);
        // GET /api/customer/loans — customer_id inferred from JWT
        const res = await getCustomerLoans();
        setLoans(res?.data ?? []);
      } catch (err) {
        console.error("Error loading customer loans:", err);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [navigate]);

  const statusLabel = (s: string) => {
    const map: Record<string, string> = {
      PENDING: "Chờ xét duyệt",
      SUBMITTED: "Đã gửi",
      IN_REVIEW: "Đang xét duyệt",
      EVALUATED: "Đã đánh giá AI",
      APPROVED: "Đã phê duyệt",
      REJECTED: "Đã từ chối",
    };
    return map[s] || s;
  };

  return (
    <CustomerLayout>
      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Danh sách yêu cầu vay</h1>
            <p className="text-muted-foreground">Theo dõi trạng thái các yêu cầu vay của bạn</p>
          </div>
          <Link to="/customer/create-loan">
            <Button size="lg" className="gap-2">
              <PlusCircle className="w-5 h-5" />
              Tạo yêu cầu mới
            </Button>
          </Link>
        </div>

        {loading ? (
          <div className="flex h-32 items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : loans.length > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>Yêu cầu vay của tôi</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Mã yêu cầu</TableHead>
                    <TableHead>Loại vay</TableHead>
                    <TableHead>Số tiền</TableHead>
                    <TableHead>AI Score</TableHead>
                    <TableHead>Risk</TableHead>
                    <TableHead>Trạng thái</TableHead>
                    <TableHead>Ngày tạo</TableHead>
                    <TableHead>Hành động</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loans.map((loan) => (
                    <TableRow key={loan.id}>
                      <TableCell className="font-mono text-xs">{loan.id}</TableCell>
                      <TableCell>{getLoanPurposeLabel(loan.loan_type)}</TableCell>
                      <TableCell className="font-semibold">{formatCurrency(loan.requested_amount ?? 0)}</TableCell>
                      <TableCell>{loan.ai_score ?? "—"}</TableCell>
                      <TableCell>
                        {loan.risk_label ? (
                          <Badge
                            className={
                              loan.risk_label === "VERY_GOOD" || loan.risk_label === "GOOD"
                                ? "bg-green-100 text-green-800"
                                : loan.risk_label === "MEDIUM"
                                ? "bg-yellow-100 text-yellow-800"
                                : "bg-red-100 text-red-800"
                            }
                          >
                            {loan.risk_label}
                          </Badge>
                        ) : (
                          "—"
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(loan.status)}>{statusLabel(loan.status)}</Badge>
                      </TableCell>
                      <TableCell>{new Date(loan.created_at).toLocaleDateString("vi-VN")}</TableCell>
                      <TableCell>
                        <Link to={`/customer/loans/${loan.id}`}>
                          <Button size="sm" variant="outline">
                            <Eye className="w-4 h-4 mr-1" />
                            Chi tiết
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="text-center py-12">
              <div className="mx-auto w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
                <PlusCircle className="w-8 h-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Chưa có yêu cầu vay nào</h3>
              <p className="text-muted-foreground mb-6">Bắt đầu bằng cách tạo yêu cầu vay đầu tiên của bạn</p>
              <Link to="/customer/create-loan">
                <Button size="lg">
                  <PlusCircle className="w-5 h-5 mr-2" />
                  Tạo yêu cầu vay
                </Button>
              </Link>
            </CardContent>
          </Card>
        )}

        <Card className="bg-slate-50">
          <CardHeader>
            <CardTitle className="text-base">Giải thích trạng thái</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div className="flex items-center gap-2">
                <Badge className="bg-yellow-100 text-yellow-800">Chờ xét duyệt</Badge>
                <span className="text-muted-foreground">Yêu cầu đã gửi, chờ ngân hàng xem xét</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge className="bg-blue-100 text-blue-800">Đã đánh giá AI</Badge>
                <span className="text-muted-foreground">AI đã phân tích, chờ quyết định cuối</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge className="bg-green-100 text-green-800">Đã phê duyệt</Badge>
                <span className="text-muted-foreground">Yêu cầu đã được chấp thuận</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge className="bg-red-100 text-red-800">Đã từ chối</Badge>
                <span className="text-muted-foreground">Yêu cầu không được chấp thuận</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </CustomerLayout>
  );
}
